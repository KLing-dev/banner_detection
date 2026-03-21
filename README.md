# 横幅检测与追踪系统 - 完整流程

> 阶段2 → 阶段3 → 阶段4 完整流程

## 功能

- **阶段2**：YOLO12 检测 + ByteTrack 追踪
- **阶段3**：PaddleOCR 文字识别
- **阶段4**：违规词检测与告警

## 使用方法

### 方式一：使用整合版主程序（推荐）

```bash
# 激活环境
conda activate graduate_yolov12

# 进入项目目录
cd f:\data\Projects\graduate\banner_detection
```

```bash
# 视频文件
python main.py --input videodata/test3.mp4 --illegal-words stage4_illegal_check/illegal_words.txt

# 或使用 filename 参数
python main.py --filename test3.mp4 --illegal-words stage4_illegal_check/illegal_words.txt

# 摄像头模式
python main.py --camera --illegal-words stage4_illegal_check/illegal_words.txt

# RTSP 流
python main.py --rtsp-url rtsp://admin:password@192.168.1.100:554/stream --illegal-words stage4_illegal_check/illegal_words.txt
```

### 方式二：分阶段运行

```bash
# 阶段2：检测与追踪
cd stage2_detect_track
python main.py --filename test3.mp4

# 阶段3：OCR识别
cd ../stage3_ocr
python main.py --input-video ../stage4_illegal_check/output/test3_detected.mp4 --detect-log ../stage4_illegal_check/output/test3_detect_log.json

# 阶段4：违规词检测
cd ../stage4_illegal_check
python main.py --ocr-video ../stage4_illegal_check/output/test3_ocr.mp4 --ocr-result ../stage4_illegal_check/output/test3_ocr_result.json --illegal-words illegal_words.txt
```

## 输出文件

所有输出都在 `stage4_illegal_check/output/` 目录下：

```
stage4_illegal_check/output/
├── test3_detected.mp4          # 阶段2：检测追踪后的视频
├── test3_detect_log.json       # 阶段2：检测日志
├── test3_ocr.mp4               # 阶段3：OCR标注后的视频
├── test3_ocr_result.json       # 阶段3：OCR结果
├── test3_final.mp4             # 阶段4：最终视频（违规词标注）
├── test3_alert.json            # 阶段4：告警日志（JSON）
└── test3_alert.txt            # 阶段4：告警日志（TXT）
```

## 实时告警格式

检测到违规词时，会实时输出：

```
[2024-03-17 10:30:45] banner_warning 发现违规词: 赌博
```

## 命令行参数

### 整合版主程序参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--input` | 输入视频文件或 RTSP URL | 无 |
| `--filename` | videodata 文件夹中的视频名 | 无 |
| `--camera` | 使用摄像头 | False |
| `--camera-id` | 摄像头设备 ID | 0 |
| `--rtsp-url` | RTSP 流地址 | 无 |
| `--conf-thres` | 检测置信度阈值 | 0.3 |
| `--ocr-conf` | OCR 置信度阈值 | 0.3 |
| `--illegal-words` | 违规词文件或逗号分隔的词 | 必填 |
| `--output` | 输出目录 | stage4_illegal_check/output |

## 违规词管理

### 方式1：TXT 文件

```bash
--illegal-words stage4_illegal_check/illegal_words.txt
```

### 方式2：命令行直接输入

```bash
--illegal-words "赌博,诈骗,传销"
```

### 方式3：JSON 文件

```json
{
  "illegal_words": ["赌博", "诈骗", "传销"]
}
```

## 整合参数说明

- **阶段2**：只输出检测日志和标注视频，不输出最终视频
- **阶段3**：读取阶段2的检测日志，输出 OCR 结果和标注视频
- **阶段4**：读取阶段3的 OCR 结果，输出最终视频和告警

**最终输出**：
- 告警视频（标注违规词）
- 告警日志（JSON + TXT）
- 实时告警（控制台输出）

## 注意事项

1. 整合版会依次执行阶段2、3、4，适合批量处理
2. 实时流场景建议分阶段运行，便于问题排查
3. 确保各阶段的输入输出路径正确
