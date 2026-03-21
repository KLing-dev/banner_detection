"""
违规词检测与告警系统 - 阶段 4
基于阶段3的OCR结果进行违规词检测和告警
"""

import argparse
import json
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont


def parse_args():
    parser = argparse.ArgumentParser(description='Illegal Word Detection and Alert - Stage 4')
    parser.add_argument('--ocr-video', type=str, required=True, help='OCR annotated video path')
    parser.add_argument('--ocr-result', type=str, required=True, help='OCR result JSON path')
    parser.add_argument('--illegal-words', type=str, required=True, help='Illegal words file path or comma-separated words')
    parser.add_argument('--output', type=str, default=None, help='Output directory')
    parser.add_argument('--output-video', type=str, default=None, help='Output video filename')
    parser.add_argument('--alert-log', type=str, default=None, help='Alert log path')
    parser.add_argument('--conf-thres', type=float, default=0.3, help='OCR confidence threshold')
    return parser.parse_args()


def get_output_paths(ocr_video, output_dir=None):
    """根据输入视频生成输出路径"""
    input_path = Path(ocr_video)
    prefix = input_path.stem.replace('_ocr', '')
    
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / 'stage4_illegal_check' / 'output'
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_video = output_dir / f"{prefix}_final.mp4"
    alert_log = output_dir / f"{prefix}_alert.json"
    alert_txt = output_dir / f"{prefix}_alert.txt"
    
    return output_video, alert_log, alert_txt, output_dir


def load_illegal_words(file_path):
    """加载违规词列表"""
    words = []
    
    # 检查是否是逗号分隔的字符串
    if ',' in file_path or '，' in file_path:
        # 命令行直接输入的词，用逗号分隔
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
        # TXT 文件，每行一个词
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


def frame_to_timestamp(frame_id, fps):
    """帧号转换为时间戳"""
    total_seconds = frame_id / fps
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    milliseconds = int((total_seconds - int(total_seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def draw_text_with_background(frame, text, position, font_scale=0.8, text_color=(255, 255, 255), bg_color=None):
    """在帧上绘制文字（支持中文）"""
    x, y = position
    
    pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    
    font_size = int(30 * font_scale)
    
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


def save_alert_log(alert_log_path, alert_txt_path, alerts):
    """保存告警日志"""
    # JSON 格式
    with open(alert_log_path, 'w', encoding='utf-8') as f:
        json.dump(alerts, f, indent=2, ensure_ascii=False)
    
    # TXT 格式
    with open(alert_txt_path, 'w', encoding='utf-8') as f:
        for alert in alerts:
            f.write(f"[{alert['timestamp']}] 违规词: {alert['illegal_word']}, Banner ID: {alert['banner_id']}, 内容: {alert['text']}\n")


def main():
    args = parse_args()
    
    # 获取输出路径
    output_video, alert_log_path, alert_txt_path, output_dir = get_output_paths(args.ocr_video, args.output)
    
    # 如果用户指定了输出文件
    if args.output_video:
        output_video = Path(args.output_video)
    if args.alert_log:
        alert_log_path = Path(args.alert_log)
        alert_txt_path = alert_log_path.with_suffix('.txt')
    
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("违规词检测与告警系统 - 阶段 4")
    print("=" * 60)
    print(f"输入视频：{args.ocr_video}")
    print(f"OCR 结果：{args.ocr_result}")
    print(f"违规词文件：{args.illegal_words}")
    print(f"输出视频：{output_video}")
    print(f"告警日志：{alert_log_path}")
    print("=" * 60)
    
    # 加载违规词
    print("正在加载违规词...")
    illegal_words = load_illegal_words(args.illegal_words)
    print(f"✅ 加载了 {len(illegal_words)} 个违规词: {illegal_words[:5]}...")
    
    # 加载 OCR 结果
    print("正在加载 OCR 结果...")
    with open(args.ocr_result, 'r', encoding='utf-8') as f:
        ocr_results = json.load(f)
    
    # 按帧索引 OCR 结果
    ocr_results_by_frame = {}
    for result in ocr_results:
        # 过滤低置信度
        if result.get('text_conf', 0) < args.conf_thres:
            continue
        
        frame_id = result['frame_id']
        if frame_id not in ocr_results_by_frame:
            ocr_results_by_frame[frame_id] = []
        ocr_results_by_frame[frame_id].append(result)
    
    # 打开视频
    print(f"正在打开视频：{args.ocr_video}")
    cap = cv2.VideoCapture(args.ocr_video)
    if not cap.isOpened():
        raise ValueError(f"无法打开视频：{args.ocr_video}")
    
    # 获取视频属性
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FRAME_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"视频参数：{width}x{height}, {fps}fps, 总帧数：{total_frames}")
    
    # 创建视频写入器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_video), fourcc, fps, (width, height))
    
    if not out.isOpened():
        raise RuntimeError(f"无法创建输出视频：{output_video}")
    
    print(f"✅ 输出视频创建成功：{output_video}")
    print("开始违规词检测...")
    
    # 告警记录
    alerts = []
    alert_count = 0
    frame_id = 0
    
    # 主循环
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("视频读取完毕")
            break
        
        # 获取当前帧的 OCR 结果
        frame_results = ocr_results_by_frame.get(frame_id, [])
        
        for result in frame_results:
            text = result.get('text', '')
            is_illegal, illegal_word = check_illegal(text, illegal_words)
            
            if is_illegal:
                # 实时告警输出
                timestamp = frame_to_timestamp(frame_id, fps)
                alert_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] banner_warning 发现违规词: {text}"
                print(alert_msg)
                
                # 记录告警
                alerts.append({
                    'timestamp': timestamp,
                    'alert_time': datetime.now().isoformat(),
                    'illegal_word': illegal_word,
                    'banner_id': result.get('banner_id', 0),
                    'text': text,
                    'frame_id': frame_id,
                    'bbox': result.get('bbox', [])
                })
                
                alert_count += 1
                
                # 绘制红色边框和违规标记
                bbox = result.get('bbox', [])
                if len(bbox) >= 4:
                    x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                    
                    # 绘制违规标记
                    label = f"违规: {illegal_word}"
                    draw_text_with_background(frame, label, (x1, y1 - 25), 0.8, (255, 255, 255), (0, 0, 255))
        
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
    
    # 保存告警日志
    save_alert_log(alert_log_path, alert_txt_path, alerts)
    
    # 统计信息
    illegal_word_stats = {}
    for alert in alerts:
        word = alert['illegal_word']
        illegal_word_stats[word] = illegal_word_stats.get(word, 0) + 1
    
    print("=" * 60)
    print("✅ 违规词检测完成！")
    print(f"输出视频：{output_video}")
    print(f"告警日志：{alert_log_path}")
    print(f"总帧数：{frame_id}")
    print(f"发现违规次数：{alert_count}")
    print(f"涉及违规词种类：{len(illegal_word_stats)}")
    if illegal_word_stats:
        print("违规词统计：")
        for word, count in sorted(illegal_word_stats.items(), key=lambda x: -x[1]):
            print(f"  - {word}: {count}次")
    print("=" * 60)
    
    return {
        'output_video': str(output_video),
        'alert_log': str(alert_log_path),
        'total_frames': frame_id,
        'alert_count': alert_count,
        'illegal_word_stats': illegal_word_stats
    }


if __name__ == '__main__':
    main()
