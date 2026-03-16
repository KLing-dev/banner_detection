"""
配置模块 - 统一管理所有配置参数
"""

from pathlib import Path


class Config:
    """项目配置类"""
    
    # ========== 路径配置 ==========
    # 项目根目录
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    
    # 阶段 2 目录
    STAGE2_DIR = PROJECT_ROOT / 'stage2_detect_track'
    
    # RTSP 流存储目录
    RTSP_STREAMS_DIR = STAGE2_DIR / 'rtsp_streams'
    
    # 输出目录（阶段 4）
    OUTPUT_DIR = PROJECT_ROOT / 'stage4_illegal_check' / 'output'
    
    # 日志目录
    LOGS_DIR = STAGE2_DIR / 'logs'
    
    # 视频数据目录
    VIDEO_DATA_DIR = PROJECT_ROOT / 'videodata'
    
    # 模型权重目录
    MODEL_WEIGHTS_DIR = PROJECT_ROOT / 'stage1_train' / 'runs' / 'train' / 'yolov12_banner_final5' / 'weights'
    
    # ========== 模型配置 ==========
    # 默认权重文件
    DEFAULT_WEIGHTS = MODEL_WEIGHTS_DIR / 'best.pt'
    
    # ========== 检测参数配置 ==========
    # 置信度阈值（已调整为 0.3）
    CONF_THRESHOLD = 0.3
    
    # NMS IoU 阈值
    IOU_THRESHOLD = 0.45
    
    # 追踪阈值
    TRACK_THRESHOLD = 0.5
    
    # 追踪缓冲区（帧数）
    TRACK_BUFFER = 30
    
    # 匹配阈值
    MATCH_THRESHOLD = 0.8
    
    # 图像尺寸
    IMG_SIZE = 640
    
    # ========== RTSP 流配置 ==========
    # RTSP 服务器地址
    RTSP_SERVER_HOST = 'localhost'
    
    # RTSP 服务器端口
    RTSP_SERVER_PORT = 8554
    
    # RTSP 流路径前缀
    RTSP_STREAM_PREFIX = 'stream'
    
    # FFmpeg 路径（如果不在系统 PATH 中，需要指定完整路径）
    FFMPEG_PATH = 'ffmpeg'
    
    # RTSP 流输出格式
    RTSP_OUTPUT_FORMAT = 'mp4'
    
    # ========== 显示配置 ==========
    # 是否显示实时预览窗口
    SHOW_PREVIEW = True
    
    # 是否显示标签
    SHOW_LABEL = True
    
    # 是否显示置信度
    SHOW_CONF = True
    
    # 检测框颜色（BGR：绿色）
    BOX_COLOR = (0, 255, 0)
    
    # 文本颜色（白色）
    TEXT_COLOR = (255, 255, 255)
    
    # 文本颜色（低置信度：灰色）
    LOW_CONF_TEXT_COLOR = (128, 128, 128)
    
    # 线宽
    LINE_WIDTH = 2
    
    # 字体大小
    FONT_SCALE = 0.6
    
    # ========== 输出配置 ==========
    # 输出视频文件名
    OUTPUT_VIDEO_NAME = 'detected_video.mp4'
    
    # 输出日志文件名
    OUTPUT_LOG_NAME = 'detect_log.json'
    
    # 是否保存检测日志
    SAVE_DETECT_LOG = True
    
    # ========== 性能配置 ==========
    # 每多少帧打印一次进度
    PROGRESS_INTERVAL = 30
    
    # 是否使用 GPU 加速
    USE_GPU = True
    
    # GPU 设备 ID
    GPU_DEVICE = '0'
    
    @classmethod
    def create_directories(cls):
        """创建所有必要的目录"""
        directories = [
            cls.RTSP_STREAMS_DIR,
            cls.OUTPUT_DIR,
            cls.LOGS_DIR,
        ]
        
        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        return directories
    
    @classmethod
    def get_rtsp_url(cls, stream_name='stream'):
        """生成 RTSP 流 URL"""
        return f'rtsp://{cls.RTSP_SERVER_HOST}:{cls.RTSP_SERVER_PORT}/{stream_name}'
    
    @classmethod
    def get_output_video_path(cls, filename=None):
        """获取输出视频路径"""
        if filename is None:
            filename = cls.OUTPUT_VIDEO_NAME
        return cls.OUTPUT_DIR / filename
    
    @classmethod
    def get_output_log_path(cls):
        """获取输出日志路径"""
        return cls.OUTPUT_DIR / cls.OUTPUT_LOG_NAME


# 创建默认配置实例
default_config = Config()
