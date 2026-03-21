"""
横幅检测与追踪系统 - 完整流程整合
阶段2：检测与追踪 → 阶段3：OCR识别 → 阶段4：违规词检测

使用方法：
    python main.py --filename test3.mp4 --illegal-words stage4_illegal_check/illegal_words.txt
    python main.py --camera --illegal-words stage4_illegal_check/illegal_words.txt
"""

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent


def parse_args():
    parser = argparse.ArgumentParser(description='Banner Detection and Alert System')
    
    # 输入源
    parser.add_argument('--filename', type=str, help='Video filename in videodata folder')
    parser.add_argument('--input', type=str, help='Input video file path')
    parser.add_argument('--camera', action='store_true', help='Use camera as input')
    parser.add_argument('--camera-id', type=int, default=0, help='Camera device ID')
    parser.add_argument('--rtsp-url', type=str, help='RTSP stream URL')
    
    # 阶段参数
    parser.add_argument('--conf-thres', type=float, default=0.3, help='Detection confidence threshold')
    parser.add_argument('--ocr-conf', type=float, default=0.3, help='OCR confidence threshold')
    
    # 阶段4参数
    parser.add_argument('--illegal-words', type=str, required=True, help='Illegal words file or comma-separated words')
    
    # 输出
    parser.add_argument('--output', type=str, default=None, help='Output directory')
    
    return parser.parse_args()


def get_output_dir():
    return PROJECT_ROOT / 'stage4_illegal_check' / 'output'


def run_stage2(args):
    """运行阶段：检测"""
    print("\n" + "=" * 60)
    print("阶段：检测")
    print("=" * 60)
    
    # 构建命令
    cmd = [
        sys.executable, 
        str(PROJECT_ROOT / 'stage2_detect_track' / 'main.py')
    ]
    
    if args.filename:
        cmd.extend(['--filename', args.filename])
    elif args.input:
        cmd.extend(['--input', args.input])
    elif args.camera:
        cmd.extend(['--camera'])
        if args.camera_id != 0:
            cmd.extend([str(args.camera_id)])
    elif args.rtsp_url:
        cmd.extend(['--rtsp-url', args.rtsp_url])
    else:
        # 默认使用 test3.mp4
        cmd.extend(['--filename', 'test3.mp4'])
    
    if args.output:
        cmd.extend(['--output', args.output])
    
    print(f"执行命令：{' '.join(cmd)}")
    
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    return result.returncode == 0


def run_stage3(detected_video, detect_log):
    """运行阶段：OCR"""
    print("\n" + "=" * 60)
    print("阶段：OCR")
    print("=" * 60)
    
    ocr_video = str(Path(detected_video).with_suffix('')).replace('_detected', '_ocr') + '.mp4'
    ocr_result = str(Path(detected_video).with_suffix('')).replace('_detected', '_ocr_result') + '.json'
    
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / 'stage3_ocr' / 'main.py'),
        '--input-video', str(detected_video),
        '--detect-log', str(detect_log),
        '--ocr-result', str(ocr_result)
    ]
    
    print(f"执行命令：{' '.join(cmd)}")
    
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    return result.returncode == 0


def run_stage4(ocr_video, ocr_result, illegal_words):
    """运行阶段：违规检测"""
    print("\n" + "=" * 60)
    print("阶段：违规检测")
    print("=" * 60)
    
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / 'stage4_illegal_check' / 'main.py'),
        '--ocr-video', str(ocr_video),
        '--ocr-result', str(ocr_result),
        '--illegal-words', illegal_words
    ]
    
    print(f"执行命令：{' '.join(cmd)}")
    
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    return result.returncode == 0


def main():
    args = parse_args()
    
    # 获取输入文件名作为前缀
    if args.filename:
        prefix = Path(args.filename).stem
    elif args.input:
        prefix = Path(args.input).stem
    elif args.camera:
        prefix = f"camera_{args.camera_id}"
    elif args.rtsp_url:
        prefix = "rtsp_stream"
    else:
        prefix = "test3"
    
    output_dir = get_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("横幅检测与追踪系统 - 完整流程")
    print("=" * 60)
    print(f"输入：{args.filename or args.input or ('camera ' + str(args.camera_id)) or args.rtsp_url}")
    print(f"违规词：{args.illegal_words}")
    print(f"输出目录：{output_dir}")
    print("=" * 60)
    
    # 阶段2输出路径
    if args.filename:
        input_file = args.filename
    elif args.input:
        input_file = Path(args.input).name
    elif args.camera:
        input_file = f"camera_{args.camera_id}"
    elif args.rtsp_url:
        input_file = "rtsp_stream"
    else:
        input_file = "test3"
    
    detected_video = output_dir / f"{input_file}_detected.mp4"
    detect_log = output_dir / f"{input_file}_detect_log.json"
    
    # 阶段1: 检测
    if not detect_log.exists():
        print("\n[检测] 开始...")
        success = run_stage2(args)
        if not success:
            print("检测执行失败！")
            return 1
    else:
        print(f"\n[检测] 已完成，跳过")
    
    # 阶段2: OCR
    ocr_result = output_dir / f"{input_file}_ocr_result.json"
    ocr_video = output_dir / f"{input_file}_ocr.mp4"
    
    if not ocr_result.exists():
        print("\n[OCR] 开始...")
        success = run_stage3(detected_video, detect_log)
        if not success:
            print("OCR执行失败！")
            return 1
    else:
        print(f"\n[OCR] 已完成，跳过")
    
    # 阶段3: 违规检测
    print("\n[违规检测] 开始...")
    success = run_stage4(ocr_video, ocr_result, args.illegal_words)
    if not success:
        print("阶段4执行失败！")
        return 1
    
    print("\n" + "=" * 60)
    print("✅ 完整流程执行完成！")
    print("=" * 60)
    print(f"最终输出：")
    print(f"  - 告警视频：{output_dir / f'{input_file}_final.mp4'}")
    print(f"  - 告警日志：{output_dir / f'{input_file}_alert.txt'}")
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
