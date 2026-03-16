"""
输入源选择模块 - 提供交互式输入源选择功能
功能：列出可用视频文件、选择输入源、验证输入
"""

import os
from pathlib import Path
from .logger import get_logger
from .config import Config


class InputSourceSelector:
    """输入源选择器"""
    
    def __init__(self, config=None):
        """
        初始化输入源选择器
        
        参数：
            config: 配置对象
        """
        self.config = config or Config()
        self.logger = get_logger()
        
        # 支持的视频格式
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.flv']
    
    def list_available_videos(self, video_dir=None):
        """
        列出指定目录中的所有可用视频文件
        
        参数：
            video_dir: 视频目录路径（默认使用配置的 VIDEO_DATA_DIR）
        
        返回：
            list: 视频文件路径列表
        """
        if video_dir is None:
            video_dir = self.config.VIDEO_DATA_DIR
        
        video_dir = Path(video_dir)
        
        if not video_dir.exists():
            self.logger.warning(f"视频目录不存在：{video_dir}")
            return []
        
        videos = []
        for ext in self.supported_formats:
            videos.extend(video_dir.glob(f'*{ext}'))
            videos.extend(video_dir.glob(f'*{ext.upper()}'))
        
        # 去重并排序
        videos = sorted(list(set(videos)))
        
        self.logger.info(f"在 {video_dir} 中找到 {len(videos)} 个视频文件")
        
        return videos
    
    def display_video_list(self, videos):
        """
        显示视频列表（带编号）
        
        参数：
            videos: 视频文件路径列表
        """
        if not videos:
            print("❌ 未找到可用的视频文件")
            return
        
        print("\n" + "="*60)
        print("可用的视频文件列表：")
        print("="*60)
        
        for i, video in enumerate(videos, 1):
            size_mb = video.stat().st_size / (1024 * 1024)
            print(f"  [{i:2d}] {video.name:<40} ({size_mb:8.2f} MB)")
        
        print("="*60)
    
    def select_interactive(self, video_dir=None):
        """
        交互式选择视频文件
        
        参数：
            video_dir: 视频目录路径
        
        返回：
            Path: 选中的视频文件路径，None（如果取消）
        """
        videos = self.list_available_videos(video_dir)
        
        if not videos:
            return None
        
        self.display_video_list(videos)
        
        while True:
            try:
                choice = input("\n请输入视频编号（或输入 'q' 退出）：").strip()
                
                if choice.lower() == 'q':
                    print("已取消选择")
                    return None
                
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(videos):
                    selected_video = videos[choice_num - 1]
                    print(f"✅ 已选择：{selected_video.name}")
                    return selected_video
                else:
                    print(f"❌ 无效的编号，请输入 1-{len(videos)} 之间的数字")
                    
            except ValueError:
                print("❌ 无效输入，请输入数字或 'q'")
    
    def select_by_index(self, index, video_dir=None):
        """
        通过索引选择视频文件（非交互式）
        
        参数：
            index: 视频索引（从 1 开始）
            video_dir: 视频目录路径
        
        返回：
            Path: 选中的视频文件路径，None（如果索引无效）
        """
        videos = self.list_available_videos(video_dir)
        
        if not videos:
            return None
        
        if 1 <= index <= len(videos):
            selected_video = videos[index - 1]
            self.logger.info(f"已选择视频：{selected_video.name}")
            return selected_video
        else:
            self.logger.error(f"无效的索引：{index}（有效范围：1-{len(videos)}）")
            return None
    
    def select_by_name(self, filename, video_dir=None):
        """
        通过文件名选择视频文件
        
        参数：
            filename: 视频文件名（可包含或不包含扩展名）
            video_dir: 视频目录路径
        
        返回：
            Path: 选中的视频文件路径，None（如果未找到）
        """
        videos = self.list_available_videos(video_dir)
        
        # 尝试精确匹配
        for video in videos:
            if video.name == filename or video.stem == filename:
                self.logger.info(f"已选择视频：{video.name}")
                return video
        
        # 尝试模糊匹配
        for video in videos:
            if filename in video.name:
                self.logger.info(f"模糊匹配到视频：{video.name}")
                return video
        
        self.logger.error(f"未找到匹配的视频文件：{filename}")
        return None
    
    def validate_input(self, input_source):
        """
        验证输入源是否有效
        
        参数：
            input_source: 输入源路径或 URL
        
        返回：
            bool: 是否有效
        """
        input_source = str(input_source)
        
        # 如果是 RTSP URL，直接返回 True
        if input_source.startswith('rtsp://'):
            self.logger.info(f"✅ 有效的 RTSP 流地址：{input_source}")
            return True
        
        # 如果是文件路径，检查文件是否存在
        input_path = Path(input_source)
        if input_path.exists():
            if input_path.suffix.lower() in self.supported_formats:
                self.logger.info(f"✅ 有效的视频文件：{input_path.name}")
                return True
            else:
                self.logger.warning(f"⚠️  不支持的视频格式：{input_path.suffix}")
                return False
        else:
            self.logger.error(f"❌ 文件不存在：{input_path}")
            return False


def quick_select_video(index=None, filename=None, video_dir=None, config=None):
    """
    便捷函数：快速选择视频
    
    参数：
        index: 视频索引（优先）
        filename: 视频文件名
        video_dir: 视频目录
        config: 配置对象
    
    返回：
        Path: 选中的视频文件，None（如果失败）
    """
    selector = InputSourceSelector(config)
    
    if index is not None:
        return selector.select_by_index(index, video_dir)
    elif filename is not None:
        return selector.select_by_name(filename, video_dir)
    else:
        return selector.select_interactive(video_dir)
