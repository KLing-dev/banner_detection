"""
横幅检测与追踪系统 - 完整流程整合
检测 → OCR → 违规检测

使用方法：
    # 实时模式（摄像头/RTSP流/视频）
    python main.py --realtime --camera --illegal-words illegal_words.txt
    python main.py --realtime --rtsp-url rtsp://... --illegal-words illegal_words.txt
    python main.py --realtime --video videodata/test3.mp4 --illegal-words illegal_words.txt
    
    # 批处理模式（视频文件）
    python main.py --input videodata/test3.mp4 --illegal-words illegal_words.txt
    
    # 测试模式（输出所有中间文件）
    python main.py --test --input videodata/test3.mp4 --illegal-words illegal_words.txt
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent


def parse_args():
    parser = argparse.ArgumentParser(description='Banner Detection and Alert System')
    
    # 输入源
    parser.add_argument('--input', type=str, help='Input video file path')
    parser.add_argument('--filename', type=str, help='Video filename in videodata folder')
    parser.add_argument('--camera', action='store_true', help='Use camera as input')
    parser.add_argument('--camera-id', type=int, default=0, help='Camera device ID')
    parser.add_argument('--rtsp-url', type=str, help='RTSP stream URL')
    parser.add_argument('--video', type=str, help='Video file path (for realtime mode)')
    
    # 模式
    parser.add_argument('--realtime', action='store_true', help='Real-time mode: process frame by frame')
    parser.add_argument('--test', action='store_true', help='Test mode: output all intermediate files')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    # 阶段参数
    parser.add_argument('--conf-thres', type=float, default=0.3, help='Detection confidence threshold')
    parser.add_argument('--ocr-conf', type=float, default=0.3, help='OCR confidence threshold')
    
    # 违规词
    parser.add_argument('--illegal-words', type=str, required=True, help='Illegal words file or comma-separated words')
    
    # 输出
    parser.add_argument('--output', type=str, default=None, help='Output directory')
    parser.add_argument('--output-video', type=str, default=None, help='Output video path (for realtime mode)')
    
    return parser.parse_args()


def run_realtime(args):
    """运行实时模式"""
    print("=" * 60)
    print("实时模式")
    print("=" * 60)
    
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / 'realtime' / 'main.py'),
        '--illegal-words', args.illegal_words,
        '--conf-thres', str(args.conf_thres),
        '--ocr-conf', str(args.ocr_conf)
    ]
    
    if args.camera:
        cmd.extend(['--camera'])
        if args.camera_id != 0:
            cmd.extend(['--camera-id', str(args.camera_id)])
    elif args.rtsp_url:
        cmd.extend(['--rtsp-url', args.rtsp_url])
    elif args.video:
        cmd.extend(['--video', args.video])
    elif args.input:
        cmd.extend(['--video', args.input])
    else:
        print("错误：实时模式需要指定输入源")
        return False
    
    if args.output_video:
        cmd.extend(['--output-video', args.output_video])
    
    print(f"执行命令：{' '.join(cmd)}")
    
    # 实时模式实时打印输出
    process = subprocess.Popen(cmd, cwd=str(PROJECT_ROOT),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
                           text=True,
                           encoding='utf-8',
                           errors='replace')
    
    for line in process.stdout:
        print(line.rstrip())
    
    process.wait()
    return process.returncode == 0


def get_output_dir():
    return PROJECT_ROOT / 'stage4_illegal_check' / 'output'


def print_verbose(args, msg):
    """只在 verbose 或测试模式下打印"""
    if args.verbose or args.test:
        print(msg)


def run_detect(args, detected_video, detect_log, output_dir, input_file):
    """运行检测"""
    print_verbose(args, "\n" + "=" * 60)
    print_verbose(args, "检测")
    print_verbose(args, "=" * 60)
    
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
        cmd.extend(['--filename', 'test3.mp4'])
    
    if args.output:
        cmd.extend(['--output', args.output])
    
    print_verbose(args, f"执行命令：{' '.join(cmd)}")
    
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), 
                          capture_output=not args.verbose,
                          text=not args.verbose)
    
    if args.verbose:
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    
    return result.returncode == 0


def run_ocr(args, detected_video, detect_log, ocr_result, ocr_video):
    """运行 OCR"""
    print_verbose(args, "\n" + "=" * 60)
    print_verbose(args, "OCR")
    print_verbose(args, "=" * 60)
    
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / 'stage3_ocr' / 'main.py'),
        '--input-video', str(detected_video),
        '--detect-log', str(detect_log),
        '--ocr-result', str(ocr_result),
        '--conf-thres', str(args.ocr_conf)
    ]
    
    print_verbose(args, f"执行命令：{' '.join(cmd)}")
    
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT),
                          capture_output=not args.verbose,
                          text=not args.verbose)
    
    if args.verbose:
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    
    return result.returncode == 0


def run_illegal_check(args, ocr_video, ocr_result, illegal_words, alert_json, alert_txt, final_video):
    """运行违规检测"""
    print_verbose(args, "\n" + "=" * 60)
    print_verbose(args, "违规检测")
    print_verbose(args, "=" * 60)
    
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / 'stage4_illegal_check' / 'main.py'),
        '--ocr-video', str(ocr_video),
        '--ocr-result', str(ocr_result),
        '--illegal-words', illegal_words,
        '--output-video', str(final_video),
        '--alert-log', str(alert_json)
    ]
    
    print_verbose(args, f"执行命令：{' '.join(cmd)}")
    
    # 捕获输出，但实时打印
    process = subprocess.Popen(cmd, cwd=str(PROJECT_ROOT), 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.STDOUT,
                              text=True,
                              encoding='utf-8',
                              errors='replace')
    
    # 实时打印输出
    for line in process.stdout:
        print(line.rstrip())
    
    process.wait()
    
    return process.returncode == 0


def cleanup_intermediate_files(args, output_dir, input_file):
    """删除中间文件（仅在非测试模式下）"""
    if args.test:
        return
    
    files_to_delete = [
        output_dir / f"{input_file}_detected.mp4",
        output_dir / f"{input_file}_detect_log.json",
        output_dir / f"{input_file}_ocr.mp4",
        output_dir / f"{input_file}_ocr_result.json"
    ]
    
    for f in files_to_delete:
        if f.exists():
            try:
                f.unlink()
                print_verbose(args, f"已删除中间文件: {f}")
            except Exception as e:
                print_verbose(args, f"删除失败 {f}: {e}")


def main():
    args = parse_args()
    
    # 实时模式
    if args.realtime:
        return 0 if run_realtime(args) else 1
    
    # 批处理模式
    if args.filename:
        input_file = Path(args.filename).stem
    elif args.input:
        input_file = Path(args.input).stem
    elif args.camera:
        input_file = f"camera_{args.camera_id}"
    elif args.rtsp_url:
        input_file = "rtsp_stream"
    else:
        input_file = "test3"
    
    output_dir = get_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 根据模式决定是否打印详细信息
    if not args.test:
        # 生产模式：只打印简洁信息
        print("横幅检测系统启动...")
    
    # 定义输出文件路径
    detected_video = output_dir / f"{input_file}_detected.mp4"
    detect_log = output_dir / f"{input_file}_detect_log.json"
    ocr_result = output_dir / f"{input_file}_ocr_result.json"
    ocr_video = output_dir / f"{input_file}_ocr.mp4"
    alert_json = output_dir / f"{input_file}_alert.json"
    alert_txt = output_dir / f"{input_file}_alert.txt"
    final_video = output_dir / f"{input_file}_final.mp4"
    
    # ========== 检测 ==========
    if not detect_log.exists():
        success = run_detect(args, detected_video, detect_log, output_dir, input_file)
        if not success:
            print("检测失败！")
            return 1
    else:
        print_verbose(args, f"[检测] 已有结果，跳过")
    
    # ========== OCR ==========
    if not ocr_result.exists():
        success = run_ocr(args, detected_video, detect_log, ocr_result, ocr_video)
        if not success:
            print("OCR失败！")
            return 1
    else:
        print_verbose(args, f"[OCR] 已有结果，跳过")
    
    # ========== 违规检测 ==========
    success = run_illegal_check(args, ocr_video, ocr_result, args.illegal_words, 
                               alert_json, alert_txt, final_video)
    if not success:
        print("违规检测失败！")
        return 1
    
    # ========== 清理中间文件 ==========
    if not args.test:
        cleanup_intermediate_files(args, output_dir, input_file)
    
    # ========== 完成 ==========
    if not args.test:
        print(f"\n完成！")
        print(f"  最终视频: {final_video}")
        print(f"  告警日志: {alert_txt}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
