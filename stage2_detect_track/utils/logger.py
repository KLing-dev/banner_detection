"""
日志模块 - 提供统一的日志记录功能
功能：控制台输出 + 文件记录，支持不同日志级别
"""

import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logger(log_dir='logs', log_level=logging.INFO):
    """
    配置日志记录器
    
    参数：
        log_dir: 日志文件保存目录
        log_level: 日志级别（默认 INFO）
    
    返回：
        logger: 配置好的日志记录器
    """
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # 生成日志文件名（带时间戳）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_path / f'banner_detect_{timestamp}.log'
    
    # 创建 logger
    logger = logging.getLogger('BannerDetection')
    logger.setLevel(log_level)
    
    # 清除已有的 handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # 创建文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # 添加处理器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger, log_file


# 全局 logger 实例
logger = None
log_file_path = None


def get_logger():
    """获取全局 logger 实例"""
    global logger
    if logger is None:
        logger, log_file_path = setup_logger()
    return logger


def get_log_file_path():
    """获取日志文件路径"""
    return log_file_path
