# 横幅检测与追踪系统

> 检测 → OCR → 违规检测 完整流程

## 功能

- **检测**：YOLO12 检测 + ByteTrack 追踪
- **OCR**：PaddleOCR 文字识别
- **违规检测**：违规词检测与实时告警

## 使用方法

### 1. 实时模式（推荐）

实时处理摄像头/RTSP流/视频，每帧实时检测+OCR+告警：

```bash
# 激活环境
conda activate graduate_yolov12

# 摄像头实时检测
python main.py --realtime --camera --illegal-words stage4_illegal_check/illegal_words.txt

# RTSP 流实时检测
python main.py --realtime --rtsp-url rtsp://admin:password@192.168.1.100:554/stream --illegal-words stage4_illegal_check/illegal_words.txt

# 视频文件实时检测（逐帧处理）
python main.py --realtime --video videodata/test3.mp4 --illegal-words stage4_illegal_check/illegal_words.txt
```

### 2. 批处理模式

离线处理视频文件：

```bash
python main.py --input videodata/test3.mp4 --illegal-words stage4_illegal_check/illegal_words.txt
```

### 3. 测试模式

输出所有中间文件，便于调试：

```bash
python main.py --test --input videodata/test3.mp4 --illegal-words stage4_illegal_check/illegal_words.txt
```

### 4. 分阶段运行

```bash
# 检测
cd stage2_detect_track
python main.py --filename test3.mp4

# OCR
cd ../stage3_ocr
python main.py --input-video ../stage4_illegal_check/output/test3_detected.mp4 --detect-log ../stage4_illegal_check/output/test3_detect_log.json

# 违规检测
cd ../stage4_illegal_check
python main.py --ocr-video ../stage4_illegal_check/output/test3_ocr.mp4 --ocr-result ../stage4_illegal_check/output/test3_ocr_result.json --illegal-words illegal_words.txt
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--realtime` | 实时模式 | False |
| `--camera` | 使用摄像头 | False |
| `--camera-id` | 摄像头设备 ID | 0 |
| `--rtsp-url` | RTSP 流地址 | 无 |
| `--video` | 视频文件路径（实时模式） | 无 |
| `--input` | 输入视频文件（批处理模式） | 无 |
| `--filename` | videodata 文件夹中的视频名 | 无 |
| `--illegal-words` | 违规词文件或逗号分隔的词 | 必填 |
| `--conf-thres` | 检测置信度阈值 | 0.3 |
| `--ocr-conf` | OCR 置信度阈值 | 0.3 |
| `--output-video` | 输出视频路径（实时模式） | 无 |
| `--test` | 测试模式（输出所有中间文件） | False |
| `--verbose` | 详细输出 | False |

## 模式说明

### 实时模式 `--realtime`

- 每帧同时完成 检测+OCR+违规检测
- 实时输出告警：`[时间] banner_warning 发现违规词: XXX`
- 实时显示检测框和违规标记
- 按 `q` 键退出
- 适合：摄像头、RTSP 流、实时监控

### 批处理模式

- 分阶段处理：检测 → OCR → 违规检测
- 自动跳过已完成的阶段
- 只输出最终视频和告警日志
- 自动清理中间文件
- 适合：视频文件离线处理

### 测试模式 `--test`

- 输出所有中间文件
- 完整日志输出
- 适合：调试和问题排查

## 输出文件

### 批处理模式输出

```
stage4_illegal_check/output/
├── test3_final.mp4       # 最终视频（违规标注）
└── test3_alert.txt      # 告警日志
```

### 测试模式输出

```
stage4_illegal_check/output/
├── test3_detected.mp4      # 检测视频
├── test3_detect_log.json  # 检测日志
├── test3_ocr.mp4          # OCR视频
├── test3_ocr_result.json  # OCR结果
├── test3_final.mp4        # 最终视频
├── test3_alert.json       # 告警日志(JSON)
└── test3_alert.txt       # 告警日志(TXT)
```

## 实时告警格式

```
[2024-03-17 10:30:45] banner_warning 发现违规词: 赌博
```

## 违规词管理

### TXT 文件
```
赌博
诈骗
传销
```

### 命令行
```bash
--illegal-words "赌博,诈骗,传销"
```

### JSON 文件
```json
{
  "illegal_words": ["赌博", "诈骗", "传销"]
}
```

## 注意事项

1. 实时模式需要 GPU 加速以保证处理速度
2. 批处理模式会自动清理中间文件（除测试模式外）
3. 确保违规词文件编码为 UTF-8

## 项目架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         main.py                                 │
│                    (统一入口 / 调度器)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐    ┌──────────────────┐                 │
│  │   realtime/      │    │   stage2_/       │                 │
│  │   main.py        │    │   main.py        │                 │
│  │                  │    │                  │                 │
│  │  实时模式        │    │  检测+追踪        │                 │
│  │  (帧级处理)      │    │  (Batch模式)     │                 │
│  └────────┬─────────┘    └────────┬─────────┘                 │
│           │                        │                             │
│           │  ┌─────────────────────┼─────────────────────┐       │
│           │  │                     │                     │       │
│           ▼  ▼                     ▼                     ▼       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              BannerDetectionTracker                     │   │
│  │              (YOLO12 + ByteTrack)                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            │                                    │
│                            ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              PaddleOCR (文字识别)                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            │                                    │
│                            ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              违规词检测 (正则匹配)                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            │                                    │
│                            ▼                                    │
│              ┌─────────────────────────────┐                    │
│              │     实时告警输出            │                    │
│              │     [时间] banner_warning  │                    │
│              │     发现违规词: XXX        │                    │
│              └─────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

## 运行逻辑

### 1. 实时模式 (`--realtime`)

```
┌──────────────────────────────────────────────────────────────┐
│                        实时模式流程                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   摄像头/RTSP/视频 ──▶  读取帧 ──▶  YOLO12检测              │
│                                              │                │
│                                              ▼                │
│                                    ByteTrack追踪              │
│                                              │                │
│                                              ▼                │
│                                    提取ROI区域                │
│                                              │                │
│                                              ▼                │
│                                    PaddleOCR文字识别          │
│                                              │                │
│                                              ▼                │
│                                    违规词匹配检测              │
│                                              │                │
│                    ┌─────────────────────────┘                │
│                    │                                           │
│                    ▼                                           │
│   ┌─────────────────────────────────────────┐                │
│   │  判断是否告警:                           │                │
│   │  1. 帧内去重：同一帧不重复告警相同文字   │                │
│   │  2. 时间去重：2秒内相同文字不重复告警   │                │
│   └─────────────────────────────────────────┘                │
│                    │                                           │
│                    ▼                                           │
│   ┌─────────────────────────────────────────┐                │
│   │  输出告警: [时间] banner_warning        │                │
│   │         发现违规词: XXX                 │                │
│   └─────────────────────────────────────────┘                │
│                    │                                           │
│                    ▼                                           │
│            绘制检测框 + 违规标记                                │
│                    │                                           │
│                    ▼                                           │
│            显示/保存视频 ──▶ 下一帧循环                        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**特点：**
- 每帧同时完成 检测+OCR+违规检测
- 实时输出告警（无缓冲）
- 适合：摄像头监控、RTSP流、实时处理

### 2. 批处理模式

```
┌──────────────────────────────────────────────────────────────┐
│                       批处理模式流程                           │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   输入视频 ──▶ Stage2: 检测+追踪 ──▶ detected.mp4           │
│                              │                               │
│                              ▼                               │
│                       detect_log.json                        │
│                              │                               │
│                              ▼                               │
│                   Stage3: OCR文字识别                        │
│                              │                               │
│                              ▼                               │
│                   ocr_result.json + ocr.mp4                 │
│                              │                               │
│                              ▼                               │
│               Stage4: 违规词检测 + 告警                       │
│                              │                               │
│                              ▼                               │
│                   final.mp4 + alert.txt                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**特点：**
- 分阶段处理，可跳过已完成的阶段
- 自动清理中间文件
- 适合：视频离线分析

## 模块接口

### 1. 统一入口 (main.py)

```python
# 实时模式
python main.py --realtime --camera --illegal-words illegal_words.txt

# 批处理模式  
python main.py --input videodata/test3.mp4 --illegal-words illegal_words.txt
```

### 2. 实时模块 (realtime/main.py)

```python
# 直接调用
from realtime.main import main as realtime_main
import argparse

# 构造参数
args = argparse.Namespace(
    camera=True,
    camera_id=0,
    rtsp_url=None,
    video=None,
    illegal_words='illegal_words.txt',
    conf_thres=0.3,
    ocr_conf=0.3,
    output_video=None,
    show=True
)

# 运行
realtime_main()
```

### 3. 检测模块 (stage2_detect_track/main.py)

```python
# 命令行调用
python stage2_detect_track/main.py --filename test3.mp4

# 输出文件
# - output/test3_detected.mp4: 带检测框的视频
# - output/test3_detect_log.json: 检测日志
```

### 4. OCR模块 (stage3_ocr/main.py)

```python
# 命令行调用
python stage3_ocr/main.py \
    --input-video stage4_illegal_check/output/test3_detected.mp4 \
    --detect-log stage4_illegal_check/output/test3_detect_log.json \
    --ocr-result stage4_illegal_check/output/test3_ocr_result.json

# 输出文件
# - output/test3_ocr.mp4: 带文字标注的视频
# - output/test3_ocr_result.json: OCR结果
```

### 5. 违规检测模块 (stage4_illegal_check/main.py)

```python
# 命令行调用
python stage4_illegal_check/main.py \
    --ocr-video output/test3_ocr.mp4 \
    --ocr-result output/test3_ocr_result.json \
    --illegal-words illegal_words.txt \
    --output-video output/test3_final.mp4

# 输出文件
# - output/test3_final.mp4: 最终视频（违规标注）
# - output/test3_alert.txt: 告警日志
```

## 违规词告警去重机制

实时模式使用双重去重机制防止告警刷屏：

### 帧内去重
- 同一帧内相同文字只告警一次
- 实现：`frame_alerted_texts` 集合

### 时间去重
- 相同 track_id + 相同文字，2秒内不重复告警
- 实现：`last_alert` 字典记录上次告警时间和内容

```python
# 配置
ALERT_COOLDOWN = 2  # 冷却时间（秒）

# 判断逻辑
if should_alert:
    print("[时间] banner_warning 发现违规词: XXX", flush=True)
    last_alert[track_id] = {'text': text, 'time': current_time}
```

## 性能优化

### 实时输出
- 设置 `PYTHONUNBUFFERED=1` 环境变量
- 使用 `sys.stdout.reconfigure(line_buffering=True)`
- 关键输出点使用 `flush=True`

### FPS优化
- 检测阈值：`--conf-thres` (默认 0.3)
- OCR阈值：`--ocr-conf` (默认 0.3)
- 可根据实际需求调整平衡速度和精度
