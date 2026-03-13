import argparse
import json
import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO
from bytetrack import ByteTracker


def parse_args():
    parser = argparse.ArgumentParser(description='Banner Detection and Tracking')
    parser.add_argument('--weights', type=str, required=True, help='Path to YOLO weights')
    parser.add_argument('--rtsp-url', type=str, required=True, help='RTSP stream URL')
    parser.add_argument('--output', type=str, default='output/detected_video.mp4', help='Output video path')
    parser.add_argument('--conf-thres', type=float, default=0.5, help='Confidence threshold')
    parser.add_argument('--nms-thres', type=float, default=0.45, help='NMS threshold')
    parser.add_argument('--track-thres', type=float, default=0.5, help='Tracking threshold')
    parser.add_argument('--track-buffer', type=int, default=30, help='Track buffer')
    parser.add_argument('--match-thresh', type=float, default=0.8, help='Match threshold')
    return parser.parse_args()


def get_color(track_id):
    np.random.seed(track_id)
    return tuple(np.random.randint(0, 255, 3).tolist())


def draw_tracks(frame, tracks):
    for track in tracks:
        track_id = track.track_id
        tlbr = track.tlbr
        x1, y1, x2, y2 = map(int, tlbr)
        conf = track.score

        color = get_color(track_id)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        label = f"ID:{track_id}, Conf:{conf:.2f}"
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), color, -1)
        cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    return frame


def main():
    args = parse_args()

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    model = YOLO(args.weights)

    tracker = ByteTracker(
        track_thresh=args.track_thres,
        track_buffer=args.track_buffer,
        match_thresh=args.match_thresh,
        frame_rate=30
    )

    cap = cv2.VideoCapture(args.rtsp_url)
    if not cap.isOpened():
        raise ValueError(f"Cannot open RTSP stream: {args.rtsp_url}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(args.output, fourcc, fps, (width, height))

    detect_log = []
    frame_id = 0

    print("Starting detection and tracking...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame, conf=args.conf_thres, nms=args.nms_thres, verbose=False)

        detections = []
        if len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            for i in range(len(boxes)):
                box = boxes[i]
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                detections.append([x1, y1, x2, y2, conf])

        detections = np.array(detections) if detections else np.empty((0, 5))

        if detections.shape[1] == 5:
            online_targets = tracker.update(detections, frame)
        else:
            online_targets = []

        frame = draw_tracks(frame, online_targets)
        out.write(frame)

        frame_detections = []
        for target in online_targets:
            x1, y1, x2, y2 = target.tlbr
            frame_detections.append({
                'track_id': int(target.track_id),
                'x1': float(x1), 'y1': float(y1),
                'x2': float(x2), 'y2': float(y2),
                'conf': float(target.score)
            })

        detect_log.append({
            'frame_id': frame_id,
            'banner_ids': [d['track_id'] for d in frame_detections],
            'detections': frame_detections
        })

        frame_id += 1
        if frame_id % 30 == 0:
            print(f"Processed {frame_id} frames...")

    cap.release()
    out.release()

    log_path = Path(args.output).parent / 'detect_log.json'
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(detect_log, f, indent=2, ensure_ascii=False)

    print(f"Done! Output saved to: {args.output}")
    print(f"Detection log saved to: {log_path}")


if __name__ == '__main__':
    main()
