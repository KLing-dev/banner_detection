"""
违规词检测配置
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


class Config:
    """违规词检测配置"""
    
    # 输出目录
    OUTPUT_DIR = PROJECT_ROOT / 'stage4_illegal_check' / 'output'
    
    # 默认参数
    DEFAULT_CONFIDENCE_THRESHOLD = 0.3
    
    # 告警参数
    ALERT_FORMAT = "[{time}] banner_warning 发现违规词: {text}"
    
    # 数据保留天数
    RETENTION_DAYS = 7
    
    @classmethod
    def get_output_paths(cls, input_video_name):
        """获取输出路径"""
        prefix = Path(input_video_name).stem.replace('_ocr', '')
        return {
            'video': cls.OUTPUT_DIR / f"{prefix}_final.mp4",
            'alert_json': cls.OUTPUT_DIR / f"{prefix}_alert.json",
            'alert_txt': cls.OUTPUT_DIR / f"{prefix}_alert.txt"
        }
