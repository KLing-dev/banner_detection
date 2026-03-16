"""
横幅文字识别模块 - 阶段 3
基于 PaddleOCR 实现横幅文字识别
"""

import argparse
import json
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
from paddleocr import PaddleOCR
from PIL import Image, ImageDraw, ImageFont


def parse_args():
    parser = argparse.ArgumentParser(description='Banner OCR Recognition - Stage 3')
    parser.add_argument('--input-video', type=str, required=True, help='Input video path')
    parser.add_argument('--detect-log', type=str, required=True, help='Detection log JSON path')
    parser.add_argument('--output', type=str, default=None, help='Output directory')
    parser.add_argument('--output-video', type=str, default=None, help='Output video filename')
    parser.add_argument('--ocr-result', type=str, default=None, help='OCR result JSON path')
    parser.add_argument('--conf-thres', type=float, default=0.5, help='OCR confidence threshold')
    parser.add_argument('--expand-ratio', type=float, default=0.05, help='ROI expansion ratio')
    return parser.parse_args()


def get_output_paths(input_video, output_dir=None):
    """根据输入视频生成输出路径"""
    input_path = Path(input_video)
    prefix = input_path.stem
    
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / 'stage4_illegal_check' / 'output'
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_video = output_dir / f"{prefix}_ocr.mp4"
    ocr_result = output_dir / f"{prefix}_ocr_result.json"
    
    return output_video, ocr_result, output_dir


def preprocess_roi(roi, expand_ratio=0.05):
    """预处理 ROI 图像"""
    height, width = roi.shape[:2]
    
    # 边缘扩展
    expand_h = int(height * expand_ratio)
    expand_w = int(width * expand_ratio)
    
    # 创建扩展后的图像
    expanded = np.zeros((height + 2*expand_h, width + 2*expand_w, 3), dtype=np.uint8)
    expanded[expand_h:expand_h+height, expand_w:expand_w+width] = roi
    
    # 灰度化
    gray = cv2.cvtColor(expanded, cv2.COLOR_BGR2GRAY)
    
    # 高斯降噪
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # 对比度增强
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(blur)
    
    # 转换为 BGR
    result = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
    
    # 缩放至合适大小
    h, w = result.shape[:2]
    scale = max(320 / h, 320 / w, 1.0)
    if scale > 1:
        result = cv2.resize(result, (int(w * scale), int(h * scale)))
    
    return result


def merge_duplicate_texts(ocr_results):
    """合并重复文字"""
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


def draw_text_with_background(frame, text, position, font_scale=0.5, text_color=(255, 255, 255), bg_color=None):
    """在帧上绘制文字（带背景）"""
    x, y = position
    
    # 获取文字大小
    (text_width, text_height), baseline = cv2.getTextSize(
        text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2
    )
    
    # 绘制背景
    if bg_color is not None:
        cv2.rectangle(
            frame,
            (x, y - text_height - 5),
            (x + text_width + 5, y + 5),
            bg_color,
            -1
        )
    
    # 绘制文字
    cv2.putText(
        frame,
        text,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        text_color,
        2
    )


def main():
    args = parse_args()
    
    # 获取输出路径
    output_video, ocr_result_path, output_dir = get_output_paths(args.input_video, args.output)
    
    # 如果用户指定了输出文件，使用用户指定的路径
    if args.output_video:
        output_video = Path(args.output_video)
    if args.ocr_result:
        ocr_result_path = Path(args.ocr_result)
    
    print("=" * 60)
    print("横幅文字识别系统 - 阶段 3")
    print("=" * 60)
    print(f"输入视频：{args.input_video}")
    print(f"检测日志：{args.detect_log}")
    print(f"输出视频：{output_video}")
    print(f"OCR 结果：{ocr_result_path}")
    print(f"置信度阈值：{args.conf_thres}")
    print("=" * 60)
    
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 加载检测日志
    print("正在加载检测日志...")
    with open(args.detect_log, 'r', encoding='utf-8') as f:
        detect_log = json.load(f)
    
    # 创建帧索引
    detect_log_by_frame = {item['frame_id']: item for item in detect_log}
    
    # 初始化 PaddleOCR
    print("正在初始化 PaddleOCR...")
    ocr = PaddleOCR(
        use_angle_cls=True,
        lang='ch',
        use_gpu=True,
        show_log=False
    )
    
    # 打开视频
    print(f"正在打开视频：{args.input_video}")
    cap = cv2.VideoCapture(args.input_video)
    if not cap.isOpened():
        raise ValueError(f"无法打开视频：{args.input_video}")
    
    # 获取视频属性
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"视频参数：{width}x{height}, {fps}fps, 总帧数：{total_frames}")
    
    # 创建视频写入器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_video), fourcc, fps, (width, height))
    
    if not out.isOpened():
        raise RuntimeError(f"无法创建输出视频：{output_video}")
    
    print(f"✅ 输出视频创建成功：{output_video}")
    print("开始 OCR 识别...")
    
    # OCR 结果存储
    ocr_results = []
    frame_id = 0
    
    # 主循环
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("视频读取完毕")
            break
        
        # 获取当前帧的检测结果
        frame_info = detect_log_by_frame.get(frame_id)
        
        if frame_info and frame_info.get('detections'):
            for det in frame_info['detections']:
                x1, y1, x2, y2 = int(det['x1']), int(det['y1']), int(det['x2']), int(det['y2'])
                
                # 裁剪 ROI
                roi = frame[y1:y2, x1:x2]
                
                if roi.size == 0:
                    continue
                
                # 预处理
                processed_roi = preprocess_roi(roi, args.expand_ratio)
                
                # OCR 识别
                ocr_result = ocr.ocr(processed_roi, cls=True)
                
                # 提取文字
                frame_texts = []
                if ocr_result and ocr_result[0]:
                    for line in ocr_result[0]:
                        if line and len(line) >= 2:
                            text = line[1][0]
                            text_conf = line[1][1]
                            if text_conf >= args.conf_thres:
                                frame_texts.append({
                                    'text': text,
                                    'text_conf': float(text_conf)
                                })
                
                # 合并重复文字
                frame_texts = merge_duplicate_texts(frame_texts)
                
                # 记录 OCR 结果
                if frame_texts:
                    for txt_info in frame_texts:
                        ocr_results.append({
                            'frame_id': frame_id,
                            'banner_id': det['track_id'],
                            'bbox': [x1, y1, x2, y2],
                            'text': txt_info['text'],
                            'text_conf': txt_info['text_conf']
                        })
                    
                    # 在帧上标注文字
                    for i, txt_info in enumerate(frame_texts):
                        label = f"{txt_info['text']} ({txt_info['text_conf']:.2f})"
                        
                        # 根据置信度选择颜色
                        if txt_info['text_conf'] >= 0.7:
                            text_color = (255, 255, 255)
                        else:
                            text_color = (128, 128, 128)
                        
                        # 绘制文字（带背景）
                        text_y = y2 + 20 + i * 25
                        draw_text_with_background(frame, label, (x1, text_y), 0.5, text_color)
        
        # 写入输出视频
        out.write(frame)
        
        frame_id += 1
        
        # 打印进度
        if frame_id % 30 == 0:
            progress = (frame_id / total_frames * 100) if total_frames > 0 else 0
            print(f"进度：{frame_id}/{total_frames} ({progress:.1f}%)")
    
    # 释放资源
    cap.release()
    out.release()
    
    # 保存 OCR 结果
    with open(ocr_result_path, 'w', encoding='utf-8') as f:
        json.dump(ocr_results, f, indent=2, ensure_ascii=False)
    
    print("=" * 60)
    print("✅ OCR 识别完成！")
    print(f"输出视频：{output_video}")
    print(f"OCR 结果：{ocr_result_path}")
    print(f"总帧数：{frame_id}")
    print(f"识别到文字的帧数：{len(set(r['frame_id'] for r in ocr_results))}")
    print("=" * 60)
    
    return {
        'output_video': str(output_video),
        'ocr_result': str(ocr_result_path),
        'total_frames': frame_id,
        'frames_with_text': len(set(r['frame_id'] for r in ocr_results))
    }


if __name__ == '__main__':
    main()
