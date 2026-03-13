import argparse
import json
import cv2
import numpy as np
from pathlib import Path
from paddleocr import PaddleOCR
from PIL import Image, ImageDraw, ImageFont


def parse_args():
    parser = argparse.ArgumentParser(description='Banner OCR Recognition')
    parser.add_argument('--video', type=str, required=True, help='Input video path')
    parser.add_argument('--detect-log', type=str, required=True, help='Detection log JSON path')
    parser.add_argument('--output', type=str, default='output/ocr_video.mp4', help='Output video path')
    parser.add_argument('--ocr-result', type=str, default='output/ocr_result.json', help='OCR result JSON path')
    return parser.parse_args()


def preprocess_roi(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(blur)

    h, w = enhanced.shape
    scale = max(320 / h, 320 / w)
    resized = cv2.resize(enhanced, (int(w * scale), int(h * scale)))

    return cv2.cvtColor(resized, cv2.COLOR_GRAY2BGR)


def merge_duplicate_texts(ocr_results, similarity_thresh=0.9):
    if not ocr_results:
        return ocr_results

    merged = []
    for new_result in ocr_results:
        is_duplicate = False
        for existing in merged:
            if new_result['text'] == existing['text']:
                existing['count'] = existing.get('count', 1) + 1
                existing['text_conf'] = max(existing['text_conf'], new_result['text_conf'])
                is_duplicate = True
                break
        if not is_duplicate:
            merged.append(new_result.copy())

    return merged


def main():
    args = parse_args()

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.ocr_result).parent.mkdir(parents=True, exist_ok=True)

    print("Initializing PaddleOCR...")
    ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=True, show_log=False)

    with open(args.detect_log, 'r', encoding='utf-8') as f:
        detect_log = json.load(f)

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {args.video}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(args.output, fourcc, fps, (width, height))

    ocr_results = []
    frame_id = 0

    print("Starting OCR recognition...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_info = next((f for f in detect_log if f['frame_id'] == frame_id), None)

        if frame_info and frame_info.get('detections'):
            for det in frame_info['detections']:
                x1, y1, x2, y2 = int(det['x1']), int(det['y1']), int(det['x2']), int(det['y2'])

                expand_h = int((y2 - y1) * 0.05)
                expand_w = int((x2 - x1) * 0.05)
                x1_exp = max(0, x1 - expand_w)
                y1_exp = max(0, y1 - expand_h)
                x2_exp = min(width, x2 + expand_w)
                y2_exp = min(height, y2 + expand_h)

                roi = frame[y1_exp:y2_exp, x1_exp:x2_exp]

                processed_roi = preprocess_roi(roi)

                ocr_result = ocr.ocr(processed_roi, cls=True)

                frame_texts = []
                if ocr_result and ocr_result[0]:
                    for line in ocr_result[0]:
                        if line and len(line) >= 2:
                            text = line[1][0]
                            text_conf = line[1][1]
                            if text_conf >= 0.5:
                                frame_texts.append({
                                    'text': text,
                                    'text_conf': float(text_conf)
                                })

                frame_texts = merge_duplicate_texts(frame_texts)

                if frame_texts:
                    for txt_info in frame_texts:
                        ocr_results.append({
                            'frame_id': frame_id,
                            'banner_id': det['track_id'],
                            'bbox': [x1, y1, x2, y2],
                            'text': txt_info['text'],
                            'text_conf': txt_info['text_conf']
                        })

                    text_labels = [t['text'] for t in frame_texts]
                    combined_text = ' | '.join(text_labels)

                    for i, txt_info in enumerate(frame_texts):
                        label = f"{txt_info['text']} ({txt_info['text_conf']:.2f})"
                        color = (255, 255, 255) if txt_info['text_conf'] >= 0.7 else (128, 128, 128)

                        text_y = y2 + 20 + i * 25
                        cv2.putText(frame, label, (x1, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        out.write(frame)
        frame_id += 1

        if frame_id % 30 == 0:
            print(f"Processed {frame_id} frames...")

    cap.release()
    out.release()

    with open(args.ocr_result, 'w', encoding='utf-8') as f:
        json.dump(ocr_results, f, indent=2, ensure_ascii=False)

    print(f"Done! Output video saved to: {args.output}")
    print(f"OCR result saved to: {args.ocr_result}")


if __name__ == '__main__':
    main()
