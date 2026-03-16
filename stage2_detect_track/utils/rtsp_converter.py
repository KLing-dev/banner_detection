"""
RTSP 流转换模块 - 将本地 MP4 视频转换为 RTSP 流
功能：启动 RTSP 服务器、推送视频流、管理流生命周期
"""

import subprocess
import threading
import time
import signal
import os
from pathlib import Path
from .logger import get_logger
from .config import Config


class RTSPStreamManager:
    """RTSP 流管理器"""
    
    def __init__(self, config=None):
        """
        初始化 RTSP 流管理器
        
        参数：
            config: 配置对象（使用默认配置如果为 None）
        """
        self.config = config or Config()
        self.logger = get_logger()
        self.rtsp_process = None
        self.ffmpeg_process = None
        self.stream_name = None
        self.is_running = False
        
        # 创建必要的目录
        self.config.create_directories()
    
    def start_rtsp_server(self):
        """
        启动 RTSP 服务器（rtsp-simple-server）
        
        返回：
            bool: 是否成功启动
        """
        try:
            self.logger.info("正在启动 RTSP 服务器...")
            
            # 检查 rtsp-simple-server 是否存在
            server_path = self.config.STAGE2_DIR / 'rtsp-simple-server.exe'
            if not server_path.exists():
                # 尝试在系统 PATH 中查找
                server_path = 'rtsp-simple-server'
                self.logger.warning(f"未找到 rtsp-simple-server.exe，尝试使用系统命令：{server_path}")
            
            # 启动 RTSP 服务器
            self.rtsp_process = subprocess.Popen(
                [str(server_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.config.STAGE2_DIR)
            )
            
            # 等待服务器启动
            time.sleep(2)
            
            # 检查进程是否正常运行
            if self.rtsp_process.poll() is None:
                self.logger.info(f"✅ RTSP 服务器已启动")
                self.is_running = True
                return True
            else:
                stdout, stderr = self.rtsp_process.communicate()
                self.logger.error(f"❌ RTSP 服务器启动失败：{stderr.decode()}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 启动 RTSP 服务器时出错：{str(e)}")
            return False
    
    def push_video_to_rtsp(self, video_path, stream_name='stream'):
        """
        将本地视频推送到 RTSP 流
        
        参数：
            video_path: 本地视频文件路径
            stream_name: RTSP 流名称
        
        返回：
            str: RTSP 流 URL（成功时），None（失败时）
        """
        try:
            self.stream_name = stream_name
            rtsp_url = self.config.get_rtsp_url(stream_name)
            
            self.logger.info(f"正在推送视频到 RTSP 流：{video_path}")
            self.logger.info(f"RTSP 流地址：{rtsp_url}")
            
            # 检查视频文件是否存在
            if not Path(video_path).exists():
                raise FileNotFoundError(f"视频文件不存在：{video_path}")
            
            # 构建 FFmpeg 推流命令
            ffmpeg_cmd = [
                self.config.FFMPEG_PATH,
                '-re',  # 按帧率读取（模拟实时）
                '-i', str(video_path),  # 输入文件
                '-c', 'copy',  # 复制编码（不重新编码）
                '-f', 'rtsp',  # 输出格式
                rtsp_url
            ]
            
            self.logger.debug(f"FFmpeg 命令：{' '.join(ffmpeg_cmd)}")
            
            # 启动 FFmpeg 进程
            self.ffmpeg_process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 等待推流开始
            time.sleep(3)
            
            # 检查进程状态
            if self.ffmpeg_process.poll() is None:
                self.logger.info(f"✅ 视频推流已启动：{rtsp_url}")
                return rtsp_url
            else:
                stdout, stderr = self.ffmpeg_process.communicate()
                self.logger.error(f"❌ 视频推流失败：{stderr.decode()}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ 推送视频到 RTSP 流时出错：{str(e)}")
            return None
    
    def stop(self):
        """停止所有流和服务器"""
        self.logger.info("正在停止 RTSP 流服务...")
        
        # 停止 FFmpeg 推流
        if self.ffmpeg_process and self.ffmpeg_process.poll() is None:
            self.logger.info("停止 FFmpeg 推流...")
            self.ffmpeg_process.terminate()
            try:
                self.ffmpeg_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ffmpeg_process.kill()
        
        # 停止 RTSP 服务器
        if self.rtsp_process and self.rtsp_process.poll() is None:
            self.logger.info("停止 RTSP 服务器...")
            self.rtsp_process.terminate()
            try:
                self.rtsp_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.rtsp_process.kill()
        
        self.is_running = False
        self.logger.info("✅ RTSP 流服务已停止")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start_rtsp_server()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()


def convert_mp4_to_rtsp(video_path, stream_name='stream', config=None):
    """
    便捷函数：将 MP4 视频转换为 RTSP 流
    
    参数：
        video_path: MP4 视频文件路径
        stream_name: RTSP 流名称
        config: 配置对象
    
    返回：
        tuple: (rtsp_url, rtsp_manager) 成功时，(None, None) 失败时
    """
    logger = get_logger()
    
    try:
        # 创建 RTSP 管理器
        rtsp_manager = RTSPStreamManager(config)
        
        # 启动 RTSP 服务器
        if not rtsp_manager.start_rtsp_server():
            return None, None
        
        # 推送视频到 RTSP
        rtsp_url = rtsp_manager.push_video_to_rtsp(video_path, stream_name)
        
        if rtsp_url:
            logger.info(f"✅ RTSP 流转换成功：{rtsp_url}")
            return rtsp_url, rtsp_manager
        else:
            rtsp_manager.stop()
            return None, None
            
    except Exception as e:
        logger.error(f"❌ RTSP 流转换失败：{str(e)}")
        return None, None
