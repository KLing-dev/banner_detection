import argparse
import json
import cv2
import re
from pathlib import Path
from datetime import datetime


def parse_args():
    parser = argparse.ArgumentParser(description='Illegal Word Detection and Alert')
    parser.add_argument('--ocr-video', type=str, required=True, help='OCR annotated video path')
    parser.add_argument('--ocr-result', type=str, required=True, help='OCR result JSON path')
    parser.add_argument('--illegal-words', type=str, required=True, help='Illegal words file path')
    parser.add_argument('--output', type=str, default='output/final_video.mp4', help='Output video path')
    parser.add_argument('--alert-log', type=str, default='output/alert.log', help='Alert log path')
    return parser.parse_args()


def load_illegal_words(file_path):
    words = []
    if file_path.endswith('.json'):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            words = data.get('illegal_words', [])
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                if word:
                    words.append(word)
    return [w.lower() for w in words]


def check_illegal(text, illegal_words):
    text_lower = text.lower()
    for illegal_word in illegal_words:
        if illegal_word in text_lower:
            return True, illegal_word
    return False, None


def frame_to_timestamp(frame_id, fps):
    total_seconds = frame_id / fps
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    milliseconds = int((total_seconds - int(total_seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def main():
    args = parse_args()

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.alert_log).parent.mkdir(parents=True, exist_ok=True)

    illegal_words = load_illegal_words(args.illegal_words)
    print(f"Loaded {len(illegal_words)} illegal words")

    with open(args.ocr_result, 'r', encoding='utf-8') as f:
        ocr_results = json.load(f)

    ocr_results_by_frame = {}
    for result in ocr_results:
        frame_id = result['frame_id']
        if frame_id not in ocr_results_by_frame:
            ocr_results_by_frame[frame_id] = []
        ocr_results_by_frame[frame_id].append(result)

    cap = cv2.VideoCapture(args.ocr_video)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {args.ocr_video}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(args.output, fourcc, fps, (width, height))

    alert_log = []
    frame_id = 0

    print("Starting illegal word detection...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_results = ocr_results_by_frame.get(frame_id, [])

        illegal_banner_ids = []

        for result in frame_results:
            is_illegal, illegal_word = check_illegal(result['text'], illegal_words)

            if is_illegal:
                illegal_banner_ids.append(result['banner_id'])

                timestamp = frame_to_timestamp(frame_id, fps)
                alert_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 出现违规词：{result['text']}"
                print(alert_msg)

                alert_log.append({
                    'timestamp': timestamp,
                    'illegal_word': result['text'],
                    'banner_id': result['banner_id'],
                    'text': result['text']
                })

                x1, y1, x2, y2 = result['bbox']
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 3)

                cv2.putText(frame, f"违规:{result['text']}", (int(x1), int(y1) - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            else:
                x1, y1, x2, y2 = result['bbox']
                cv2.putText(frame, result['text'], (int(x1), int(y2) + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        out.write(frame)
        frame_id += 1

        if frame_id % 30 == 0:
            print(f"Processed {frame_id} frames...")

    cap.release()
    out.release()

    with open(args.alert_log, 'w', encoding='utf-8') as f:
        for alert in alert_log:
            f.write(f"[{alert['timestamp']}] 违规词: {alert['illegal_word']}, Banner ID: {alert['banner_id']}, 内容: {alert['text']}\n")

    print(f"\nDone! Final video saved to: {args.output}")
    print(f"Alert log saved to: {args.alert_log}")
    print(f"Total alerts: {len(alert_log)}")


if __name__ == '__main__':
    main()
