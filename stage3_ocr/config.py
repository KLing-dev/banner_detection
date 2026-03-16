"""
OCR 模块配置
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


class Config:
    """OCR 配置类"""
    
    # 输出目录
    OUTPUT_DIR = PROJECT_ROOT / 'stage4_illegal_check' / 'output'
    
    # OCR 参数
    OCR_CONFIDENCE_THRESHOLD = 0.5
    ROI_EXPAND_RATIO = 0.05
    
    # 显示参数
    SHOW_LABEL = True
    SHOW_CONF = True
    
    # 文字颜色配置
    HIGH_CONF_COLOR = (255, 255, 255)  # 置信度 >= 0.7
    LOW_CONF_COLOR = (128, 128, 128)   # 置信度 < 0.7
    
    # 字体设置
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    FONT_SCALE = 0.5
    LINE_WIDTH = 2
    
    # PaddleOCR 配置
    PADDLEOCR_USE_GPU = True
    PADDLEOCR_LANG = 'ch'
    PADDLEOCR_USE_ANGLE_CLS = True
    
    @classmethod
    def get_output_paths(cls, input_video_name):
        """获取输出路径"""
        prefix = Path(input_video_name).stem
        return {
            'video': cls.OUTPUT_DIR / f"{prefix}_ocr.mp4",
            'result': cls.OUTPUT_DIR / f"{prefix}_ocr_result.json"
        }


import cv2
