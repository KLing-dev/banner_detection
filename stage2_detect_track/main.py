"""
横幅检测与追踪系统 - 主程序入口
功能：整合输入源选择、RTSP 流读取、YOLO 检测、ByteTrack 追踪、结果输出
支持三种演示模式：
    1. 视频文件模式：读取本地 MP4 文件（模拟 RTSP 流测试）
    2. 摄像头模式：读取电脑摄像头进行实时检测
    3. RTSP 流模式：读取网络摄像头/监控摄像头的 RTSP 流

使用方法：
    1. 交互式模式：python main.py --interactive
    2. 视频文件模式：python main.py --index 3
    3. 摄像头模式：python main.py --camera
    4. RTSP 流模式：python main.py --rtsp-url rtsp://localhost:8554/stream
"""

import argparse
import sys
from pathlib import Path

from utils import (
    setup_logger,
    Config,
    BannerDetectionTracker,
    InputSourceSelector
)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='横幅检测与追踪系统 - 阶段 2',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 交互式选择视频
  python main.py
  
  # 使用指定索引的视频（test3.mp4）
  python main.py --index 3
  
  # 使用指定文件名的视频
  python main.py --filename test4.mp4
  
  # 直接使用 RTSP 流
  python main.py --rtsp-url rtsp://localhost:8554/stream
  
  # 指定输出路径
  python main.py --index 3 --output my_output.mp4
        """
    )
    
    parser.add_argument(
        '--index', '-i',
        type=int,
        help='视频文件索引（从 1 开始，默认使用 test3.mp4）'
    )
    
    parser.add_argument(
        '--filename', '-f',
        type=str,
        help='视频文件名（如：test3.mp4）'
    )
    
    parser.add_argument(
        '--rtsp-url',
        type=str,
        help='直接使用 RTSP 流地址（如：rtsp://192.168.1.100:554/stream）'
    )
    
    parser.add_argument(
        '--camera', '-c',
        type=int,
        nargs='?',
        const=0,
        default=None,
        help='使用摄像头（默认设备 0，可指定设备编号如 --camera 1）'
    )
    
    parser.add_argument(
        '--mode', '-m',
        type=str,
        choices=['video', 'camera', 'rtsp'],
        default='video',
        help='演示模式：video（视频文件）, camera（摄像头）, rtsp（RTSP 流）'
    )
    
    parser.add_argument(
        '--weights', '-w',
        type=str,
        help='YOLO 权重文件路径（默认使用阶段 1 训练的 best.pt）'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='输出视频路径（默认输出到 stage4_illegal_check/output/）'
    )
    
    parser.add_argument(
        '--conf-thres',
        type=float,
        default=0.3,
        help='检测置信度阈值（默认 0.3）'
    )
    
    parser.add_argument(
        '--no-preview',
        action='store_true',
        help='禁用实时预览窗口'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='启用交互式视频选择模式'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='启用详细日志输出'
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    # 解析参数
    args = parse_args()
    
    # 初始化配置
    config = Config()
    
    # 根据命令行参数覆盖配置
    if args.conf_thres is not None:
        config.CONF_THRESHOLD = args.conf_thres
    
    if args.no_preview:
        config.SHOW_PREVIEW = False
    
    # 设置日志
    import logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger, log_file = setup_logger(log_dir=str(config.LOGS_DIR), log_level=log_level)
    
    logger.info("="*60)
    logger.info("横幅检测与追踪系统 - 阶段 2")
    logger.info("="*60)
    logger.info(f"配置文件：{log_file}")
    logger.info(f"置信度阈值：{config.CONF_THRESHOLD}")
    logger.info(f"输出目录：{config.OUTPUT_DIR}")
    logger.info("="*60)
    
    try:
        # 创建检测追踪器
        tracker = BannerDetectionTracker(config)
        
        # 加载模型
        if args.weights:
            logger.info(f"使用自定义权重：{args.weights}")
            if not tracker.load_model(args.weights):
                logger.error("❌ 模型加载失败")
                return 1
        else:
            if not tracker.load_model():
                logger.error("❌ 模型加载失败")
                return 1
        
        # 确定输入源（优先级：命令行参数 > mode 参数）
        input_source = None
        source_type = 'video'  # 默认视频文件模式
        
        # 1. 首先检查命令行参数（最高优先级）
        if args.camera is not None:
            # 摄像头模式
            logger.info(f"使用摄像头模式，设备编号：{args.camera}")
            input_source = args.camera
            source_type = 'camera'
        
        elif args.rtsp_url:
            # RTSP 流模式
            logger.info(f"使用 RTSP 流模式：{args.rtsp_url}")
            input_source = args.rtsp_url
            source_type = 'rtsp'
        
        elif args.interactive:
            # 交互式选择
            logger.info("启用交互式选择模式")
            selector = InputSourceSelector(config)
            video_path = selector.select_interactive()
            if video_path:
                input_source = video_path
            else:
                logger.info("用户取消选择")
                return 0
        
        elif args.index:
            # 按索引选择
            logger.info(f"使用视频索引：{args.index}")
            selector = InputSourceSelector(config)
            video_path = selector.select_by_index(args.index)
            if video_path:
                input_source = video_path
        
        elif args.filename:
            # 按文件名选择
            logger.info(f"使用视频文件：{args.filename}")
            selector = InputSourceSelector(config)
            video_path = selector.select_by_name(args.filename)
            if video_path:
                input_source = video_path
        
        else:
            # 2. 根据 mode 参数选择
            if args.mode == 'camera':
                logger.info("使用摄像头模式")
                input_source = 0  # 默认摄像头
                source_type = 'camera'
            
            elif args.mode == 'rtsp':
                logger.warning("RTSP 模式需要指定 --rtsp-url 参数")
                logger.info("切换到视频文件模式（模拟 RTSP 测试）")
                logger.info("使用默认视频：test3.mp4")
                selector = InputSourceSelector(config)
                video_path = selector.select_by_name('test3')
                if video_path:
                    input_source = video_path
            
            else:  # video 模式
                logger.info("使用默认视频：test3.mp4")
                selector = InputSourceSelector(config)
                video_path = selector.select_by_name('test3')
                if video_path:
                    input_source = video_path
        
        if input_source is None:
            logger.error("❌ 未找到有效的输入源")
            return 1
        
        # 确定输出路径（让 process_video 根据输入自动生成文件名）
        # 用户可以通过 --output 参数指定输出目录或文件
        output_path = args.output if args.output else None
        
        # 根据输入源类型选择处理方式
        if source_type == 'camera':
            logger.info("📹 摄像头模式：实时检测")
            stats = tracker.process_camera(input_source, output_path)
        else:
            # 视频文件或 RTSP 流
            if source_type == 'video':
                logger.info(f"📼 视频文件模式：{input_source}")
            elif source_type == 'rtsp':
                logger.info(f"🌐 RTSP 流模式：{input_source}")
            stats = tracker.process_video(input_source, output_path)
        
        if stats:
            logger.info("\n" + "="*60)
            logger.info("处理完成统计信息：")
            logger.info("="*60)
            logger.info(f"输入源：{stats['input_source']}")
            logger.info(f"输出视频：{stats['output_video']}")
            logger.info(f"总帧数：{stats['total_frames']}")
            logger.info(f"总耗时：{stats['total_time']:.2f}秒")
            logger.info(f"平均 FPS: {stats['avg_fps']:.1f}")
            logger.info("="*60)
            return 0
        else:
            logger.error("❌ 处理失败")
            return 1
    
    except KeyboardInterrupt:
        logger.info("\n⚠️  用户中断")
        return 0
    
    except Exception as e:
        logger.error(f"❌ 程序异常退出：{str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
