# 横幅检测与违规内容识别告警模块
基于 YOLO12 + ByteTrack + PaddleOCR 实现视频/RTSP流中横幅检测、文字识别及违规内容告警的轻量化 Demo 系统，适配 Python 3.11 + CUDA 11.8/12.6 + PyTorch 2.6.0 技术栈。

## 项目概述
### 核心功能
- 阶段1：训练 YOLO12 自定义权重，精准检测视频帧中的横幅目标；
- 阶段2：将本地视频转为 RTSP 流，基于训练权重实现横幅检测 + ByteTrack 目标追踪；
- 阶段3：对检测到的横幅 ROI 区域进行 PaddleOCR 文字识别，提取横幅内容；
- 阶段4：集成全流程，对比违规词库实现实时告警，输出标注违规信息的最终视频。

### 技术栈
| 组件         | 版本/规格                          | 核心作用                     |
|--------------|------------------------------------|------------------------------|
| Python       | 3.11.x                             | 基础运行环境                 |
| CUDA         | 11.8 / 12.6                        | GPU 加速（二选一，需匹配 Torch） |
| PyTorch      | 2.6.0                              | YOLO12 运行基础              |
| YOLO12       | ultralytics 官方版                 | 横幅目标检测                 |
| ByteTrack    | 适配 Python 3.11 的稳定版          | 横幅跨帧追踪                 |
| PaddleOCR    | 2.7+（CUDA 加速版）                | 横幅文字识别                 |
| rtsp-simple-server | 最新版                          | 本地视频转 RTSP 流           |
| ffmpeg       | 5.0+                               | 视频推流/格式转换            |

## 环境准备
### 1. 系统要求
- 操作系统：Linux (Ubuntu 20.04+/CentOS 7+) / Windows 10/11（推荐 Linux，GPU 兼容性更好）；
- 硬件：NVIDIA GPU（显存 ≥ 8GB，支持 CUDA 11.8/12.6），CPU ≥ 4 核，内存 ≥ 16GB；
- 依赖工具：Git、FFmpeg（需加入系统环境变量）。

### 2. 环境配置步骤
#### 步骤1：创建并激活虚拟环境
```bash
# 创建虚拟环境（建议使用 conda，也可使用 venv）
conda create -n banner-det python=3.11 -y
conda activate banner-det

# 若使用 venv
# python -m venv banner-det-venv
# # Linux/Mac 激活
# source banner-det-venv/bin/activate
# # Windows 激活
# banner-det-venv\Scripts\activate
```

#### 步骤2：安装 CUDA（可选，无 GPU 可跳过）
- 下载对应版本：CUDA 11.8 → [NVIDIA 官网](https://developer.nvidia.com/cuda-11-8-0-download-archive)；CUDA 12.6 → [NVIDIA 官网](https://developer.nvidia.com/cuda-12-6-0-download-archive)；
- 验证安装：`nvcc -V`（输出 CUDA 版本即成功）。

#### 步骤3：安装 PyTorch（匹配 CUDA 版本）
```bash
# CUDA 11.8 版本
pip3 install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.6 版本
pip3 install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu126

# 无 GPU（CPU 版本）
pip3 install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu
```

#### 步骤4：安装项目依赖
```bash
# 安装核心依赖
pip install -r requirements.txt

# 安装 PaddleOCR（含 CUDA 加速）
pip install paddlepaddle-gpu==2.6.0.post126 -f https://www.paddlepaddle.org.cn/whl/linux/mkl/avx/stable.html  # 适配 CUDA 12.6
# 若为 CUDA 11.8，替换为：
# pip install paddlepaddle-gpu==2.6.0.post118 -f https://www.paddlepaddle.org.cn/whl/linux/mkl/avx/stable.html

# 安装 rtsp-simple-server（Linux/Mac）
wget https://github.com/aler9/rtsp-simple-server/releases/latest/download/rtsp-simple-server_linux_amd64.tar.gz
tar -xvf rtsp-simple-server_linux_amd64.tar.gz
chmod +x rtsp-simple-server

# Windows 需手动下载：https://github.com/aler9/rtsp-simple-server/releases/latest/download/rtsp-simple-server_windows_amd64.zip
```

#### 步骤5：验证环境
```bash
# 验证 Python 版本
python --version  # 需输出 3.11.x

# 验证 Torch + CUDA
python -c "import torch; print(torch.cuda.is_available())"  # 输出 True 即 GPU 可用

# 验证 PaddleOCR
python -c "from paddleocr import PaddleOCR; ocr = PaddleOCR(use_angle_cls=True, lang='ch'); print('PaddleOCR 初始化成功')"

# 验证 FFmpeg
ffmpeg -version  # 输出版本信息即成功
```

## 分阶段使用指南
### 目录结构
```
banner_detection/
├── stage1_train/          # 阶段1：权重训练
│   ├── banner/            # 横幅数据集
│   │   ├── banner.yaml   # YOLO12 数据集配置
│   │   ├── classes.txt   # 类别定义
│   │   ├── images/       # 训练/验证集图像（不纳入Git）
│   │   └── labels/        # YOLO 格式标注文件（不纳入Git）
│   └── train_banner.py   # 训练主脚本
├── stage2_detect_track/   # 阶段2：检测+追踪
│   ├── rtsp_server/       # RTSP 服务配置
│   │   └── config.yml     # rtsp-simple-server 配置
│   └── detect_track.py    # 检测追踪主脚本
├── stage3_ocr/            # 阶段3：OCR 识别
│   └── ocr_recognize.py  # OCR 主脚本
├── stage4_illegal_check/  # 阶段4：违规检测+告警
│   ├── illegal_words.txt  # 违规词库（需自行编写/上传）
│   └── check_alert.py    # 违规比对+告警主脚本
├── yolov12/               # YOLO12 官方环境
│   ├── ultralytics/      # Ultralytics 官方库
│   ├── yolov12n.pt       # 预训练权重（不纳入Git）
│   └── train_banner.py   # 训练脚本
├── .gitignore            # Git 忽略配置
├── README.md             # 项目说明文档
└── requirements.txt      # 环境依赖清单
```

### 阶段1：YOLO12 横幅权重训练
#### 前置条件
- 准备横幅标注数据集（YOLO 格式，单类别 `banner`，class_id=0）；
- 确认 `stage1_train/config.yaml` 配置正确（nc=1，names=['banner']）。

#### 操作步骤
```bash
# 进入阶段1目录
cd stage1_train

# 运行训练脚本（指定 CUDA 设备，默认 cuda:0）
python train.py --data config.yaml --epochs 100 --batch-size 16 --imgsz 640 --device 0
```

#### 输入/输出
| 输入          | 说明                                  |
|---------------|---------------------------------------|
| dataset/      | 标注好的横幅数据集                    |
| config.yaml   | YOLO12 训练配置文件                   |

| 输出          | 说明                                  |
|---------------|---------------------------------------|
| train_log/weights/best.pt | 验证集最优权重（核心输出）       |
| train_log/results.csv     | 训练损失/指标日志                |
| train_log/eval_report.txt | 权重评估报告（精度/召回率/mAP） |

#### 验证方式
查看 `train_log/eval_report.txt`，确保 `mAP50 ≥ 0.85`。

### 阶段2：横幅检测+追踪（模拟 RTSP 流）
#### 前置条件
- 阶段1 生成的 `best.pt` 已复制到 `stage2_detect_track/` 目录；
- 准备测试视频（MP4/AVI 格式，放入 `stage2_detect_track/` 目录，命名为 `test.mp4`）。

#### 操作步骤
```bash
# 进入阶段2目录
cd stage2_detect_track

# 启动 RTSP 服务（后台运行）
# Linux/Mac
nohup ./rtsp-simple-server > rtsp_server.log 2>&1 &
# Windows（新开命令行）
# rtsp-simple-server.exe

# 推送本地视频到 RTSP 流
ffmpeg -re -i test.mp4 -c copy -f rtsp rtsp://localhost:8554/stream

# 运行检测追踪脚本
python detect_track.py --weights best.pt --rtsp-url rtsp://localhost:8554/stream --output output/detected_video.mp4
```

#### 输入/输出
| 输入          | 说明                                  |
|---------------|---------------------------------------|
| best.pt       | 阶段1 训练的横幅检测权重              |
| test.mp4      | 测试视频文件                          |
| rtsp-url      | 模拟 RTSP 流地址                      |

| 输出          | 说明                                  |
|---------------|---------------------------------------|
| output/detected_video.mp4 | 标注横幅边界框/追踪ID的视频       |
| output/detect_log.json    | 每帧检测结果日志（框坐标/置信度） |

#### 验证方式
1. 用 VLC 播放器打开 `rtsp://localhost:8554/stream`，确认 RTSP 流正常；
2. 播放 `detected_video.mp4`，确认横幅边界框/追踪ID标注清晰，无频繁跳变。

### 阶段3：横幅文字识别
#### 前置条件
- 阶段2 生成的 `detected_video.mp4` 和 `detect_log.json` 已复制到 `stage3_ocr/` 目录。

#### 操作步骤
```bash
# 进入阶段3目录
cd stage3_ocr

# 运行 OCR 识别脚本
python ocr_recognize.py --video input/detected_video.mp4 --detect-log detect_log.json --output output/ocr_video.mp4 --ocr-result output/ocr_result.json
```

#### 输入/输出
| 输入          | 说明                                  |
|---------------|---------------------------------------|
| detected_video.mp4 | 阶段2 标注的检测视频               |
| detect_log.json    | 阶段2 检测日志（横幅框坐标）      |

| 输出          | 说明                                  |
|---------------|---------------------------------------|
| output/ocr_video.mp4    | 标注横幅文字的视频（含置信度）    |
| output/ocr_result.json  | 每帧横幅文字识别结果（文字/置信度） |

#### 验证方式
播放 `ocr_video.mp4`，确认横幅文字标注清晰，无明显识别错误（准确率 ≥ 85%）。

### 阶段4：违规词检测+告警（全流程集成）
#### 前置条件
- 阶段3 生成的 `ocr_video.mp4` 和 `ocr_result.json` 已复制到 `stage4_illegal_check/` 目录；
- 准备违规词库：在 `illegal_words.txt` 中每行写入一个违规词（如 `违规词1`、`违规词2`）。

#### 操作步骤
```bash
# 进入阶段4目录
cd stage4_illegal_check

# 运行违规检测+告警脚本
python check_alert.py --ocr-video ocr_video.mp4 --ocr-result ocr_result.json --illegal-words illegal_words.txt --output output/final_video.mp4 --alert-log output/alert.log
```

#### 输入/输出
| 输入          | 说明                                  |
|---------------|---------------------------------------|
| ocr_video.mp4     | 阶段3 标注文字的视频                |
| ocr_result.json   | 阶段3 文字识别结果                  |
| illegal_words.txt | 违规词库（TXT 格式，每行一个词）    |

| 输出          | 说明                                  |
|---------------|---------------------------------------|
| output/final_video.mp4 | 违规词红色高亮的最终视频          |
| output/alert.log       | 违规告警日志（时间戳+违规词）     |

#### 验证方式
1. 控制台会实时打印告警信息：`[YYYY-MM-DD HH:MM:SS] 出现违规词：XXX`；
2. 播放 `final_video.mp4`，确认违规词红色高亮，横幅边界框标红；
3. 查看 `alert.log`，确认告警信息格式正确、无漏报/误报。

## 常见问题排查
### 1. CUDA 相关报错
- 现象：`torch.cuda.is_available()` 返回 False / PaddleOCR 报 CUDA 错误；
- 解决：
  1. 确认 CUDA 版本与 Torch/PaddleOCR 版本匹配；
  2. 重新安装对应版本的 Torch/PaddleOCR；
  3. 若无 GPU，修改脚本中 `device` 参数为 `cpu`。

### 2. RTSP 流无法访问
- 现象：`rtsp://localhost:8554/stream` 无法播放；
- 解决：
  1. 检查 `rtsp-simple-server` 是否正常运行（`ps -ef | grep rtsp-simple-server`）；
  2. 确认 FFmpeg 推流命令正确，测试视频路径无误；
  3. 关闭防火墙/端口占用（默认端口 8554）。

### 3. 横幅检测准确率低
- 现象：漏检/误检横幅；
- 解决：
  1. 扩充标注数据集（增加不同场景/角度的横幅样本）；
  2. 调整训练超参数（增加 epochs、调整学习率）；
  3. 降低检测置信度阈值（脚本中 `conf-thres` 改为 0.4）。

### 4. OCR 识别文字错误
- 现象：横幅文字识别错误/乱码；
- 解决：
  1. 对 ROI 区域增强预处理（调整对比度/降噪参数）；
  2. 使用 PaddleOCR 高精度模型（`use_gpu=True`，`lang='ch'`）；
  3. 过滤低置信度结果（`text_conf < 0.5` 的结果丢弃）。

## 总结
1. 项目分 4 个阶段迭代开发，前一阶段为后一阶段的前置条件，需按顺序执行；
2. 核心依赖需严格匹配版本（Python 3.11、CUDA 11.8/12.6、Torch 2.6.0），避免环境兼容问题；
3. 关键验收指标：权重 mAP50≥0.85、横幅检出率≥90%、文字识别准确率≥85%、违规告警无漏报/误报。

## 免责声明
本项目仅为技术验证 Demo，请勿用于生产环境或非法用途。使用前需确保视频/数据来源合规，违规词库的定义与使用需遵守相关法律法规。