# 违规词检测与告警系统 - 阶段 4

> 基于阶段3的 OCR 结果进行违规词检测和告警

## 功能特性

- 违规词检测与识别
- 实时告警输出（控制台 + 日志）
- 中文显示支持
- 违规词统计
- 支持多种违规词导入方式

## 环境要求

- Python 3.11+
- conda 环境：graduate_yolov12
- OpenCV
- PIL (Pillow)

## 违规词导入方式

### 1. TXT 文件（每行一个词）

```txt
赌博
诈骗
传销
色情
```

### 2. JSON 文件

```json
{
  "illegal_words": ["赌博", "诈骗", "传销"]
}
```

### 3. 命令行直接输入

```bash
python main.py --illegal-words "赌博,诈骗,传销"
```

## 使用方法

### 基本命令

```bash
# 激活环境
conda activate graduate_yolov12

# 进入项目目录
cd f:\data\Projects\graduate\banner_detection\stage4_illegal_check
```

### 运行违规词检测

```bash
# 使用 TXT 文件
python main.py --ocr-video ../stage4_illegal_check/output/test4_ocr.mp4 --ocr-result ../stage4_illegal_check/output/test4_ocr_result.json --illegal-words illegal_words.txt

# 使用 JSON 文件
python main.py --ocr-video ../stage4_illegal_check/output/test4_ocr.mp4 --ocr-result ../stage4_illegal_check/output/test4_ocr_result.json --illegal-words illegal_words.json

# 命令行直接输入
python main.py --ocr-video ../stage4_illegal_check/output/test4_ocr.mp4 --ocr-result ../stage4_illegal_check/output/test4_ocr_result.json --illegal-words "赌博,诈骗"
```

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--ocr-video` | OCR 标注视频路径 | 必填 |
| `--ocr-result` | OCR 结果 JSON 路径 | 必填 |
| `--illegal-words` | 违规词文件路径或逗号分隔的词 | 必填 |
| `--output` | 输出目录 | stage4_illegal_check/output |
| `--output-video` | 输出视频文件名 | 自动生成 |
| `--alert-log` | 告警日志路径 | 自动生成 |
| `--conf-thres` | OCR 置信度阈值 | 0.3 |

## 输出说明

### 输出文件

```
stage4_illegal_check/output/
├── test4_final.mp4           # 标注违规词的最终视频
├── test4_alert.json          # 告警日志（JSON格式）
└── test4_alert.txt           # 告警日志（TXT格式）
```

### 告警日志格式

**JSON 格式**：
```json
[
  {
    "timestamp": "00:00:10.500",
    "alert_time": "2024-03-17T10:30:45",
    "illegal_word": "赌博",
    "banner_id": 1,
    "text": "赌博网站",
    "frame_id": 315,
    "bbox": [100, 50, 400, 150]
  }
]
```

**TXT 格式**：
```
[00:00:10.500] 违规词: 赌博, Banner ID: 1, 内容: 赌博网站
```

### 实时告警输出

检测到违规词时，会实时输出：

```
[2024-03-17 10:30:45] banner_warning 发现违规词: 赌博网站
```

## 与阶段2、3配合使用

```bash
# 1. 阶段2：检测+追踪
cd ../stage2_detect_track
python main.py --filename test4.mp4

# 2. 阶段3：OCR识别
cd ../stage3_ocr
python main.py --input-video ../stage4_illegal_check/output/test4_detected.mp4 --detect-log ../stage4_illegal_check/output/test4_detect_log.json

# 3. 阶段4：违规词检测
cd ../stage4_illegal_check
python main.py --ocr-video ../stage4_illegal_check/output/test4_ocr.mp4 --ocr-result ../stage4_illegal_check/output/test4_ocr_result.json --illegal-words illegal_words.txt
```

## 常见问题

### Q1: 中文显示为 ???

**解决方案**：确保系统安装了中文字体（微软雅黑或宋体）

### Q2: 违规词没有被检测到

**解决方案**：
- 检查违规词文件格式是否正确
- 降低置信度阈值：`--conf-thres 0.2`
- 检查 OCR 识别结果是否正确

### Q3: 输出视频无法播放

**解决方案**：使用 VLC 或 PotPlayer 播放

## 项目结构

```
stage4_illegal_check/
├── main.py              # 主程序入口
├── config.py           # 配置管理
├── check_alert.py     # 原版脚本（保留）
└── README.md          # 使用文档
```

## 未来扩展

- 对接数据库（MySQL/PostgreSQL）存储历史记录
- 对接 Redis 实现实时告警
- 自动清理超过7天的数据
- 统计分析功能
