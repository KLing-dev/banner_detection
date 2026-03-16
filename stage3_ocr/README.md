# 横幅文字识别系统 - 阶段 3

> 基于 PaddleOCR 实现横幅文字识别

## 功能特性

- 使用 PaddleOCR 进行中英文文字识别
- 支持视频中横幅 ROI 区域的文字提取
- 自动预处理图像（灰度化、降噪、对比度增强）
- 标注识别结果到视频

## 环境要求

- Python 3.11+
- CUDA（可选，推荐）
- conda 环境：graduate_yolov12
- PaddleOCR

## 安装依赖

```bash
# 激活环境
conda activate graduate_yolov12

# 安装 PaddleOCR
pip install paddleocr paddlepaddle-gpu
```

## 使用方法

### 基本命令

```bash
# 激活环境
conda activate graduate_yolov12

# 进入项目目录
cd f:\data\Projects\graduate\banner_detection\stage3_ocr
```

### 运行 OCR 识别

```bash
# 使用阶段2的输出进行OCR识别
python main.py --input-video ../stage4_illegal_check/output/test4_detected.mp4 --detect-log ../stage4_illegal_check/output/test4_detect_log.json
```

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--input-video` | 输入视频路径（阶段2的标注视频） | 必填 |
| `--detect-log` | 检测日志路径（阶段2的JSON） | 必填 |
| `--output` | 输出目录 | stage4_illegal_check/output |
| `--output-video` | 输出视频文件名 | 自动生成 |
| `--ocr-result` | OCR结果JSON路径 | 自动生成 |
| `--conf-thres` | OCR置信度阈值 | 0.5 |
| `--expand-ratio` | ROI扩展比例 | 0.05 |

## 输出说明

### 输出文件

```
stage4_illegal_check/output/
├── test4_ocr.mp4           # 标注文字的视频
└── test4_ocr_result.json   # OCR 识别结果
```

### OCR 结果格式

```json
[
  {
    "frame_id": 10,
    "banner_id": 1,
    "bbox": [100, 50, 400, 150],
    "text": "欢迎光临",
    "text_conf": 0.95
  },
  {
    "frame_id": 11,
    "banner_id": 1,
    "bbox": [100, 50, 400, 150],
    "text": "欢迎光临",
    "text_conf": 0.94
  }
]
```

## 项目结构

```
stage3_ocr/
├── main.py              # 主程序入口
├── config.py           # 配置管理
├── ocr_recognize.py    # 原版 OCR 脚本（保留）
└── README.md           # 使用文档
```

## 与阶段2配合使用

```bash
# 1. 先运行阶段2（检测+追踪）
cd ../stage2_detect_track
python main.py --filename test4.mp4

# 2. 再运行阶段3（OCR识别）
cd ../stage3_ocr
python main.py --input-video ../stage4_illegal_check/output/test4_detected.mp4 --detect-log ../stage4_illegal_check/output/test4_detect_log.json

# 3. 最后运行阶段4（违规检测）
cd ../stage4_illegal_check
python check_alert.py --ocr-video ../stage4_illegal_check/output/test4_ocr.mp4 --ocr-result ../stage4_illegal_check/output/test4_ocr_result.json --illegal-words illegal_words.txt
```

## 常见问题

### Q1: PaddleOCR 初始化失败

**检查**：
- 是否正确安装 paddlepaddle
- GPU 版本是否与 CUDA 匹配

**解决方案**：
```bash
# 使用 CPU 版本
pip install paddlepaddle

# 或使用 GPU 版本
pip install paddlepaddle-gpu
```

### Q2: OCR 识别效果不好

**解决方案**：
- 降低置信度阈值：`--conf-thres 0.3`
- 调整 ROI 扩展比例：`--expand-ratio 0.1`

### Q3: 识别速度慢

**解决方案**：
- 使用 GPU 加速
- 降低视频分辨率
