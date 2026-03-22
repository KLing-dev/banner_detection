"""
实时横幅检测与告警系统
摄像头/RTSP流 → 实时检测 → 实时OCR → 实时告警
"""

import argparse
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
from paddleocr import PaddleOCR
from PIL import Image, ImageDraw, ImageFont

# 添加项目路径
import sys
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'stage2_detect_track'))
sys.path.insert(0, str(PROJECT_ROOT / 'stage1_train'))

from utils.detection import BannerDetectionTracker
from utils.config import Config as Stage2Config


def parse_args():
    parser = argparse.ArgumentParser(description='Real-time Banner Detection and Alert')
    
    # 输入源
    parser.add_argument('--camera', action='store_true', help='Use camera as input')
    parser.add_argument('--camera-id', type=int, default=0, help='Camera device ID')
    parser.add_argument('--rtsp-url', type=str, help='RTSP stream URL')
    parser.add_argument('--video', type=str, help='Video file path')
    
    # 检测参数
    parser.add_argument('--conf-thres', type=float, default=0.3, help='Detection confidence threshold')
    parser.add_argument('--ocr-conf', type=float, default=0.3, help='OCR confidence threshold')
    
    # 违规词
    parser.add_argument('--illegal-words', type=str, required=True, help='Illegal words file or comma-separated words')
    
    # 输出
    parser.add_argument('--output-video', type=str, default=None, help='Output video path')
    parser.add_argument('--show', action='store_true', default=True, help='Show preview window')
    
    return parser.parse_args()


def load_illegal_words(file_path):
    """加载违规词列表"""
    words = []
    
    # 检查是否是逗号分隔的字符串
    if ',' in file_path or '，' in file_path:
        words = file_path.replace('，', ',').split(',')
        words = [w.strip().lower() for w in words if w.strip()]
        return words
    
    # 文件路径
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Illegal words file not found: {file_path}")
    
    if file_path.suffix == '.json':
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                words = data.get('illegal_words', [])
            elif isinstance(data, list):
                words = data
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                if word:
                    words.append(word)
    
    return [w.lower() for w in words]


def check_illegal(text, illegal_words):
    """检查文字是否包含违规词"""
    text_lower = text.lower()
    for illegal_word in illegal_words:
        if illegal_word in text_lower:
            return True, illegal_word
    return False, None


def preprocess_roi(roi, max_side=1000):
    """预处理 ROI 图像"""
    height, width = roi.shape[:2]
    
    if height < 10 or width < 10:
        return roi
    
    if height > max_side or width > max_side:
        scale = max_side / max(height, width)
        roi = cv2.resize(roi, (int(width * scale), int(height * scale)))
    
    return roi


def draw_chinese_text(frame, text, position, font_scale=0.7, text_color=(255, 255, 255), bg_color=None):
    """绘制中文文字"""
    x, y = position
    
    pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    
    font_size = int(25 * font_scale)
    
    try:
        font = ImageFont.truetype("msyh.ttc", font_size)
    except:
        try:
            font = ImageFont.truetype("simsun.ttc", font_size)
        except:
            font = ImageFont.load_default()
    
    bbox = draw.textbbox((x, y), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    if bg_color is not None:
        draw.rectangle(
            [x, y - text_height - 2, x + text_width + 2, y + 2],
            fill=bg_color
        )
    
    draw.text((x, y - text_height), text, fill=text_color, font=font)
    
    frame[:, :, :] = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    
    return frame


def main():
    args = parse_args()
    
    print("=" * 60)
    print("实时横幅检测与告警系统")
    print("=" * 60)
    
    # 加载违规词
    print(f"加载违规词: {args.illegal_words}")
    illegal_words = load_illegal_words(args.illegal_words)
    print(f"违规词列表: {illegal_words[:5]}...")
    
    # 初始化检测器
    print("初始化检测模型...")
    model_path = PROJECT_ROOT / 'stage1_train' / 'runs' / 'train' / 'yolov12_banner_final5' / 'weights' / 'best.pt'
    detector = BannerDetectionTracker()
    detector.load_model(str(model_path))
    
    # 初始化 OCR
    print("初始化 OCR...")
    ocr = PaddleOCR(lang='ch')
    
    # 打开视频源
    if args.camera:
        print(f"打开摄像头: {args.camera_id}")
        cap = cv2.VideoCapture(args.camera_id)
    elif args.rtsp_url:
        print(f"打开 RTSP 流: {args.rtsp_url}")
        cap = cv2.VideoCapture(args.rtsp_url)
    elif args.video:
        print(f"打开视频: {args.video}")
        cap = cv2.VideoCapture(args.video)
    else:
        print("错误：未指定输入源")
        return 1
    
    if not cap.isOpened():
        print(f"错误：无法打开视频源")
        return 1
    
    # 获取视频属性
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    print(f"视频属性: {width}x{height}, {fps}fps")
    
    # 创建视频写入器
    out = None
    if args.output_video:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(args.output_video, fourcc, fps, (width, height))
        print(f"输出视频: {args.output_video}")
    
    print("\n开始实时检测，按 'q' 键退出...")
    print("-" * 60)
    
    frame_count = 0
    alert_count = 0
    fps_start_time = datetime.now()
    fps_frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            if args.camera or args.rtsp_url:
                print("视频流断开")
                break
            # 视频文件循环播放
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        
        frame_count += 1
        fps_frame_count += 1
        
        # 1. YOLO 检测
        results = detector.model(frame, conf=detector.config.CONF_THRESHOLD, verbose=False)
        
        # 提取检测结果
        detections = []
        if results and results[0].boxes is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            confs = results[0].boxes.conf.cpu().numpy()
            
            for i in range(len(boxes)):
                detections.append([
                    boxes[i][0], boxes[i][1], boxes[i][2], boxes[i][3], confs[i]
                ])
        
        # 2. ByteTrack 追踪
        tracked_objects = []
        if detections:
            import numpy as np
            detections_array = np.array(detections)
            tracked_objects = detector.tracker.update(detections_array, frame)
        
        # 3. 对每个追踪目标进行 OCR 和违规检测
        frame_alerts = []
        
        for obj in tracked_objects:
            x1, y1, x2, y2 = int(obj.tlbr[0]), int(obj.tlbr[1]), int(obj.tlbr[2]), int(obj.tlbr[3])
            
            # 裁剪 ROI
            roi = frame[y1:y2, x1:x2]
            if roi.size == 0:
                continue
            
            # 预处理
            processed_roi = preprocess_roi(roi)
            
            # OCR 识别
            try:
                ocr_result = ocr.predict(processed_roi)
            except:
                continue
            
            # 提取文字
            if ocr_result and isinstance(ocr_result, list):
                for item in ocr_result:
                    if item is None or not isinstance(item, dict):
                        continue
                    
                    rec_texts = item.get('rec_texts', [])
                    rec_scores = item.get('rec_scores', [])
                    
                    for text, text_conf in zip(rec_texts, rec_scores):
                        if text_conf < args.ocr_conf or not text.strip():
                            continue
                        
                        # 检查违规
                        is_illegal, illegal_word = check_illegal(text, illegal_words)
                        
                        if is_illegal:
                            # 实时告警输出
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            alert_msg = f"[{timestamp}] banner_warning 发现违规词: {text}"
                            print(alert_msg)
                            alert_count += 1
                            
                            frame_alerts.append({
                                'bbox': [x1, y1, x2, y2],
                                'text': text,
                                'illegal_word': illegal_word,
                                'track_id': obj.track_id
                            })
        
        # 4. 绘制检测结果
        for obj in tracked_objects:
            x1, y1, x2, y2 = int(obj.tlbr[0]), int(obj.tlbr[1]), int(obj.tlbr[2]), int(obj.tlbr[3])
            
            # 绘制追踪框
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # 绘制追踪ID
            label = f"ID:{obj.track_id}"
            cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # 5. 绘制违规标记
        for alert in frame_alerts:
            x1, y1, x2, y2 = alert['bbox']
            
            # 红色边框
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
            
            # 违规文字
            label = f"违规: {alert['illegal_word']}"
            draw_chinese_text(frame, label, (x1, y1 - 30), 0.7, (255, 255, 255), (0, 0, 255))
        
        # 显示
        if args.show:
            cv2.imshow('Real-time Banner Detection', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\n用户退出")
                break
        
        # 写入输出视频
        if out:
            out.write(frame)
        
        # 计算 FPS
        elapsed = (datetime.now() - fps_start_time).total_seconds()
        if elapsed >= 5:
            current_fps = fps_frame_count / elapsed
            print(f"已处理 {frame_count} 帧, 当前 FPS: {current_fps:.1f}, 告警次数: {alert_count}")
            fps_start_time = datetime.now()
            fps_frame_count = 0
    
    # 清理
    cap.release()
    if out:
        out.release()
    if args.show:
        cv2.destroyAllWindows()
    
    print("-" * 60)
    print(f"完成！共处理 {frame_count} 帧，发现 {alert_count} 次违规")
    
    return 0


if __name__ == '__main__':
    import json
    sys.exit(main())
