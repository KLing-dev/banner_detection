# 横幅检测与追踪系统 - 阶段 2

> 基于 YOLO12 + ByteTrack 实现视频横幅的自动检测与追踪

## 功能特性

- 支持三种输入源：视频文件、摄像头、RTSP 流
- 使用 YOLO12 进行目标检测
- 使用 ByteTrack 进行目标追踪
- 输出标注视频和检测日志（JSON 格式）

## 环境要求

- Python 3.11+
- CUDA（可选，推荐）
- conda 环境：graduate_yolov12

## 安装依赖

```bash
# 激活 conda 环境
conda activate graduate_yolov12

# 安装 Python 依赖
pip install -r ../requirements.txt

# 安装 FFmpeg（手动安装）
# 1. 下载 FFmpeg: https://www.gyan.dev/ffmpeg/builds/
# 2. 解压后复制 ffmpeg.exe 到 conda 环境的 Library/bin 目录
```

## 使用方法

### 基本命令

```bash
# 激活环境
conda activate graduate_yolov12

# 进入项目目录
cd f:\data\Projects\graduate\banner_detection\stage2_detect_track
```

### 1. 视频文件模式

```bash
# 使用默认视频（test3.mp4）
python main.py

# 使用指定视频文件
python main.py --filename test3.mp4
python main.py --filename test4.mp4

# 使用视频索引
python main.py --index 0

# 指定置信度阈值
python main.py --filename test3.mp4 --conf-thres 0.25

# 指定输出路径
python main.py --filename test3.mp4 --output ./output/
```

### 2. 摄像头模式

```bash
# 使用默认摄像头（设备 0）
python main.py --camera

# 使用指定摄像头
python main.py --camera 1
python main.py --camera 2

# 退出：按 'q' 键
```

### 3. RTSP 流模式

```bash
# 使用 RTSP 流地址
python main.py --rtsp-url rtsp://admin:password@192.168.1.100:554/stream
```

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--filename` | 视频文件名 | test3.mp4 |
| `--index` | 视频索引（0-13） | 0 |
| `--camera` | 摄像头设备编号 | 0 |
| `--rtsp-url` | RTSP 流地址 | None |
| `--mode` | 演示模式：video/camera/rtsp | video |
| `--conf-thres` | 置信度阈值 | 0.3 |
| `--output` | 输出目录 | stage4_illegal_check/output |

## 输出说明

### 输出文件

程序运行完成后，会在 `stage4_illegal_check/output` 目录下生成以下文件：

```
stage4_illegal_check/output/
├── test3_detected.mp4      # 标注后的视频
├── test3_detect_log.json   # 检测日志
├── test4_detected.mp4      # 标注后的视频
└── test4_detect_log.json   # 检测日志
```

### 输出文件命名规则

- 视频文件：`{输入文件名}_detected.mp4`
- 检测日志：`{输入文件名}_detect_log.json`

例如：
- 输入：`test3.mp4` → 输出：`test3_detected.mp4`, `test3_detect_log.json`
- 输入：`rtsp://...` → 输出：`stream_detected.mp4`, `stream_detect_log.json`

### 检测日志格式

```json
[
  {
    "frame_id": 0,
    "banner_ids": [1],
    "detections": [
      {
        "track_id": 1,
        "x1": 100.0,
        "y1": 50.0,
        "x2": 400.0,
        "y2": 150.0,
        "conf": 0.85
      }
    ]
  },
  {
    "frame_id": 1,
    "banner_ids": [1],
    "detections": [...]
  }
]
```

## 性能统计

程序运行完成后，会输出以下统计信息：

```
============================================================
处理完成统计信息：
============================================================
输入源：videodata/test3.mp4
输出视频：stage4_illegal_check/output/test3_detected.mp4
总帧数：323
总耗时：12.50秒
平均 FPS: 25.8
============================================================
```

## 项目结构

```
stage2_detect_track/
├── main.py                      # 主程序入口
├── rtsp_server/
│   └── config.yml              # RTSP 服务器配置（备用）
└── utils/
    ├── __init__.py
    ├── byte_tracker_wrapper.py  # ByteTrack 追踪器封装
    ├── config.py               # 配置管理
    ├── detection.py            # 检测追踪核心模块
    ├── input_selector.py       # 输入源选择
    ├── logger.py               # 日志模块
    └── rtsp_converter.py       # RTSP 转换（备用）
```

## 配置文件

配置文件位于 `utils/config.py`，主要参数：

```python
# 检测参数
CONF_THRESHOLD = 0.3          # 置信度阈值
IOU_THRESHOLD = 0.45          # IOU 阈值

# 显示参数
SHOW_PREVIEW = True            # 显示实时预览
SHOW_LABEL = True              # 显示标签
SHOW_CONF = True              # 显示置信度
LINE_WIDTH = 2                # 边界框线条宽度
FONT_SCALE = 0.5             # 字体大小

# 输出参数
SAVE_DETECT_LOG = True        # 保存检测日志
SAVE_OUTPUT_VIDEO = True      # 保存输出视频
```

## 常见问题

### Q1: 视频文件无法打开

**检查**：
- 视频文件路径是否正确
- FFmpeg 是否正确安装

**验证 FFmpeg**：
```bash
ffmpeg -version
```

### Q2: 检测效果不好

**解决方案**：
- 降低置信度阈值：`--conf-thre 0.25`
- 检查视频质量

### Q3: 输出视频无法播放

**原因**：OpenCV 的 mp4v 编解码器可能不兼容

**解决方案**：使用 VLC 或 PotPlayer 播放

### Q4: 摄像头无法打开

**检查**：
- 摄像头是否被其他程序占用
- 尝试不同的设备编号：`--camera 1`

## 技术支持

- 项目仓库：https://github.com/KLing-dev/banner_detection
- 环境名称：graduate_yolov12
