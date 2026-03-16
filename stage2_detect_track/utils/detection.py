"""
横幅检测与追踪主模块 - 阶段 2 核心功能
整合：输入源选择、YOLO 检测、ByteTrack 追踪、结果输出
"""

import cv2
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from ultralytics import YOLO

from .logger import get_logger
from .config import Config
from .input_selector import InputSourceSelector, quick_select_video
from .byte_tracker_wrapper import SimpleByteTracker


class BannerDetectionTracker:
    """横幅检测与追踪器"""
    
    def __init__(self, config=None):
        """
        初始化检测追踪器
        
        参数：
            config: 配置对象
        """
        self.config = config or Config()
        self.logger = get_logger()
        self.model = None
        self.tracker = None
        
        # 创建必要的目录
        self.config.create_directories()
    
    def _init_tracker(self):
        """初始化 ByteTrack 追踪器"""
        self.tracker = SimpleByteTracker(
            track_thresh=self.config.CONF_THRESHOLD,
            track_buffer=30,
            match_thresh=0.8,
            frame_rate=30
        )
    
    def load_model(self, weights_path=None):
        """
        加载 YOLO 模型
        
        参数：
            weights_path: 权重文件路径（默认使用配置的 DEFAULT_WEIGHTS）
        
        返回：
            bool: 是否成功加载
        """
        if weights_path is None:
            weights_path = self.config.DEFAULT_WEIGHTS
        
        weights_path = Path(weights_path)
        
        if not weights_path.exists():
            self.logger.error(f"❌ 权重文件不存在：{weights_path}")
            return False
        
        try:
            self.logger.info(f"正在加载 YOLO 模型：{weights_path}")
            self.model = YOLO(str(weights_path))
            self.logger.info(f"✅ 模型加载成功")
            return True
        except Exception as e:
            self.logger.error(f"❌ 模型加载失败：{str(e)}")
            return False
    
    def get_color(self, track_id):
        """
        根据追踪 ID 生成固定颜色
        
        参数：
            track_id: 追踪 ID
        
        返回：
            tuple: RGB 颜色元组
        """
        # 确保 track_id 是整数类型
        if hasattr(track_id, 'item'):
            track_id = int(track_id.item())
        else:
            track_id = int(track_id)
        
        np.random.seed(track_id)
        return tuple(np.random.randint(0, 255, 3).tolist())
    
    def draw_tracks(self, frame, online_targets):
        """
        在视频帧上绘制 ByteTrack 追踪结果
        
        参数：
            frame: 当前视频帧
            online_targets: ByteTrack 追踪结果列表 (STrack 对象)
        
        返回：
            frame: 绘制后的帧
        """
        if online_targets is None or len(online_targets) == 0:
            return frame
        
        # 处理 ByteTrack 的 STrack 对象
        for target in online_targets:
            # ByteTrack STrack 属性: tlbr (top-left, bottom-right), score, track_id
            x1, y1, x2, y2 = map(int, target.tlbr)
            conf = float(target.score)
            track_id = int(target.track_id)
            
            # 根据置信度选择颜色
            if conf < self.config.CONF_THRESHOLD + 0.1:
                text_color = self.config.LOW_CONF_TEXT_COLOR
            else:
                text_color = self.config.TEXT_COLOR
            
            # 获取颜色
            color = self.get_color(track_id)
            
            # 绘制边界框
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, self.config.LINE_WIDTH)
            
            # 绘制标签
            if self.config.SHOW_LABEL or self.config.SHOW_CONF:
                label_parts = []
                if self.config.SHOW_LABEL:
                    label_parts.append(f"Obj:{track_id}")
                if self.config.SHOW_CONF:
                    label_parts.append(f"Conf:{conf:.2f}")
                
                label = ", ".join(label_parts)
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, self.config.FONT_SCALE, self.config.LINE_WIDTH)
                
                # 绘制背景
                cv2.rectangle(
                    frame,
                    (x1, y1 - label_size[1] - 10),
                    (x1 + label_size[0], y1),
                    color,
                    -1
                )
                
                # 绘制文字
                cv2.putText(
                    frame,
                    label,
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    self.config.FONT_SCALE,
                    text_color,
                    self.config.LINE_WIDTH
                )
        
        return frame
    
    def process_video_file(self, video_path, output_path=None):
        """
        直接处理视频文件（无需 RTSP 转换）
        
        参数：
            video_path: 视频文件路径
            output_path: 输出视频路径
        
        返回：
            dict: 处理结果统计信息
        """
        # 从视频文件名构建输出文件名
        input_path = Path(video_path)
        output_prefix = input_path.stem  # 不含扩展名的文件名
        output_video_name = f"{output_prefix}_detected.mp4"
        output_log_name = f"{output_prefix}_detect_log.json"
        
        # 确定输出路径
        if output_path is None:
            output_path = self.config.OUTPUT_DIR / output_video_name
        elif isinstance(output_path, str):
            output_path = Path(output_path)
            if output_path.suffix == '':
                output_path = output_path / output_video_name
        
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"输出视频路径：{output_path}")
        
        try:
            # 直接打开视频文件
            self.logger.info(f"正在打开视频文件：{video_path}")
            cap = cv2.VideoCapture(str(video_path))
            
            if not cap.isOpened():
                raise RuntimeError(f"无法打开视频文件：{video_path}")
            
            # 获取视频属性
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            self.logger.info(f"视频参数：{width}x{height}, {fps}fps, 总帧数：{total_frames}")
            
            # 创建视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
            
            # 检查 VideoWriter 是否成功打开
            if not out.isOpened():
                self.logger.error(f"❌ 无法创建输出视频：{output_path}")
                self.logger.error(f"可能原因：编解码器 'mp4v' 不可用或输出路径无效")
                raise RuntimeError(f"无法创建输出视频文件：{output_path}")
            
            self.logger.info(f"✅ 输出视频创建成功：{output_path}")
            
            # 初始化统计信息
            detect_log = []
            frame_count = 0
            start_time = datetime.now()
            
            self.logger.info("开始横幅检测与追踪...")
            
            # 主循环
            while cap.isOpened():
                ret, frame = cap.read()
                
                if not ret:
                    self.logger.info("视频读取完毕")
                    break
                
                # YOLO 检测（先不使用 track 模式）
                results = self.model(
                    frame,
                    conf=self.config.CONF_THRESHOLD,
                    iou=self.config.IOU_THRESHOLD,
                    verbose=False
                )
                
                # 绘制追踪结果
                frame = self.draw_tracks(frame, results[0].boxes if results and results[0].boxes else None)
                
                # 写入输出视频
                out.write(frame)
                
                # 提取检测结果
                frame_detections = []
                if results and results[0].boxes is not None:
                    boxes = results[0].boxes.xyxy.cpu().numpy()
                    confs = results[0].boxes.conf.cpu().numpy()
                    
                    for i in range(len(boxes)):
                        frame_detections.append({
                            'detection_id': i,
                            'x1': float(boxes[i][0]),
                            'y1': float(boxes[i][1]),
                            'x2': float(boxes[i][2]),
                            'y2': float(boxes[i][3]),
                            'conf': float(confs[i])
                        })
                
                # 记录检测日志
                detect_log.append({
                    'frame_id': frame_count,
                    'banner_ids': [d['detection_id'] for d in frame_detections],
                    'detections': frame_detections
                })
                
                frame_count += 1
                
                # 打印进度
                if frame_count % self.config.PROGRESS_INTERVAL == 0:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    current_fps = frame_count / elapsed if elapsed > 0 else 0
                    progress = (frame_count / total_frames * 100) if total_frames > 0 else 0
                    self.logger.info(f"进度：{frame_count}/{total_frames} ({progress:.1f}%), FPS: {current_fps:.1f}")
            
            # 计算统计信息
            total_time = (datetime.now() - start_time).total_seconds()
            avg_fps = frame_count / total_time if total_time > 0 else 0
            
            stats = {
                'total_frames': frame_count,
                'total_time': total_time,
                'avg_fps': avg_fps,
                'output_video': str(output_path),
                'input_source': str(video_path)
            }
            
            # 保存检测日志
            if self.config.SAVE_DETECT_LOG:
                log_path = self.config.OUTPUT_DIR / output_log_name
                with open(log_path, 'w', encoding='utf-8') as f:
                    json.dump(detect_log, f, indent=2, ensure_ascii=False)
                self.logger.info(f"检测日志已保存：{log_path}")
            
            self.logger.info(f"\n✅ 处理完成！")
            self.logger.info(f"输出视频：{output_path}")
            self.logger.info(f"总帧数：{frame_count}, 总耗时：{total_time:.2f}s, 平均 FPS: {avg_fps:.1f}")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ 处理过程中出错：{str(e)}")
            raise
        
        finally:
            # 清理资源
            if 'cap' in locals() and cap.isOpened():
                cap.release()
            if 'out' in locals() and out.isOpened():
                out.release()
    
    def process_camera(self, camera_id=0, output_path=None):
        """
        处理摄像头实时视频流
        
        参数：
            camera_id: 摄像头设备 ID（默认 0）
            output_path: 输出视频路径（可选）
        
        返回：
            dict: 处理结果统计信息
        """
        # 构建输出文件名
        output_prefix = f"camera_{camera_id}"
        output_video_name = f"{output_prefix}_detected.mp4"
        output_log_name = f"{output_prefix}_detect_log.json"
        
        if output_path:
            output_path = Path(output_path)
            if output_path.suffix == '':
                output_path = output_path / output_video_name
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            output_path = self.config.OUTPUT_DIR / output_video_name
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # 打开摄像头
            self.logger.info(f"正在打开摄像头，设备 ID: {camera_id}")
            cap = cv2.VideoCapture(camera_id)
            
            if not cap.isOpened():
                raise RuntimeError(f"无法打开摄像头：{camera_id}")
            
            # 获取摄像头参数
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            
            # 如果 FPS 为 0 或无效，使用默认值
            if fps <= 0:
                fps = 30
                self.logger.warning(f"无法获取摄像头帧率，使用默认值：{fps}")
            
            self.logger.info(f"摄像头参数：{width}x{height}, {fps}fps")
            
            # 创建视频写入器（如果指定了输出路径）
            out = None
            if output_path:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
                self.logger.info(f"输出视频：{output_path}")
            
            # 初始化统计信息
            detect_log = []
            frame_count = 0
            start_time = datetime.now()
            
            # 初始化 ByteTrack 追踪器
            self._init_tracker()
            
            self.logger.info("开始实时检测（按 'q' 键退出）...")
            
            # 主循环
            while cap.isOpened():
                ret, frame = cap.read()
                
                if not ret:
                    self.logger.warning("无法读取摄像头画面")
                    break
                
                # 1. YOLO 检测
                results = self.model(
                    frame,
                    conf=self.config.CONF_THRESHOLD,
                    verbose=False
                )
                
                # 2. 提取检测结果并转换为 ByteTrack 格式
                detections = []
                if results and results[0].boxes is not None:
                    boxes = results[0].boxes.xyxy.cpu().numpy()
                    confs = results[0].boxes.conf.cpu().numpy()
                    
                    for i in range(len(boxes)):
                        detections.append([
                            boxes[i][0], boxes[i][1], boxes[i][2], boxes[i][3], confs[i]
                        ])
                
                # 3. ByteTrack 追踪
                if detections:
                    detections = np.array(detections)
                    online_targets = self.tracker.update(detections, frame)
                else:
                    online_targets = []
                
                # 4. 绘制追踪结果
                frame = self.draw_tracks(frame, online_targets)
                
                # 写入输出视频（如果指定）
                if out:
                    out.write(frame)
                
                # 显示实时预览
                if self.config.SHOW_PREVIEW:
                    cv2.imshow('Banner Detection - Camera Mode', frame)
                    
                    # 按 'q' 键退出
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.logger.info("用户按下 'q' 键，退出检测")
                        break
                
                # 5. 记录检测日志
                frame_detections = []
                for target in online_targets:
                    x1, y1, x2, y2 = target.tlbr
                    conf = target.score
                    track_id = target.track_id
                    
                    frame_detections.append({
                        'track_id': int(track_id),
                        'x1': float(x1),
                        'y1': float(y1),
                        'x2': float(x2),
                        'y2': float(y2),
                        'conf': float(conf)
                    })
                
                detect_log.append({
                    'frame_id': frame_count,
                    'banner_ids': [d['track_id'] for d in frame_detections],
                    'detections': frame_detections
                })
                
                frame_count += 1
                
                # 打印进度（每 30 帧）
                if frame_count % self.config.PROGRESS_INTERVAL == 0:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    current_fps = frame_count / elapsed if elapsed > 0 else 0
                    self.logger.info(f"已处理 {frame_count} 帧，实时 FPS: {current_fps:.1f}")
            
            # 计算统计信息
            total_time = (datetime.now() - start_time).total_seconds()
            avg_fps = frame_count / total_time if total_time > 0 else 0
            
            stats = {
                'total_frames': frame_count,
                'total_time': total_time,
                'avg_fps': avg_fps,
                'output_video': str(output_path) if output_path else None,
                'input_source': f'camera_{camera_id}'
            }
            
            # 保存检测日志
            if self.config.SAVE_DETECT_LOG and frame_count > 0:
                log_path = self.config.OUTPUT_DIR / output_log_name
                with open(log_path, 'w', encoding='utf-8') as f:
                    json.dump(detect_log, f, indent=2, ensure_ascii=False)
                self.logger.info(f"检测日志已保存：{log_path}")
            
            self.logger.info(f"\n✅ 摄像头检测完成！")
            if output_path:
                self.logger.info(f"输出视频：{output_path}")
            self.logger.info(f"总帧数：{frame_count}, 总耗时：{total_time:.2f}s, 平均 FPS: {avg_fps:.1f}")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ 处理过程中出错：{str(e)}")
            raise
        
        finally:
            # 清理资源
            if 'cap' in locals() and cap.isOpened():
                cap.release()
            if 'out' in locals() and out.isOpened():
                out.release()
            cv2.destroyAllWindows()
    
    def process_video(self, input_source, output_path=None, stream_name='stream'):
        """
        处理视频（支持文件路径或 RTSP URL）
        
        参数：
            input_source: 输入源（文件路径或 RTSP URL）
            output_path: 输出视频路径（默认使用配置的 OUTPUT_DIR）
            stream_name: RTSP 流名称（如果输入是文件）
        
        返回：
            dict: 处理结果统计信息
        """
        # 从输入源提取文件名作为输出文件名前缀
        input_path_str = str(input_source)
        if input_path_str.startswith('rtsp://'):
            # RTSP 流使用流名称
            output_prefix = stream_name
        else:
            # 视频文件使用文件名
            input_path = Path(input_path_str)
            output_prefix = input_path.stem  # 不含扩展名的文件名
        
        # 构建输出文件名
        output_video_name = f"{output_prefix}_detected.mp4"
        output_log_name = f"{output_prefix}_detect_log.json"
        
        if output_path is None:
            output_path = self.config.OUTPUT_DIR / output_video_name
        else:
            output_path = Path(output_path)
            # 如果是目录而非文件，添加文件名
            if output_path.suffix == '':
                output_path = output_path / output_video_name
        
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        is_rtsp_input = str(input_source).startswith('rtsp://')
        rtsp_url = None
        
        try:
            # 直接读取视频文件或 RTSP 流
            # 不再自动转换为 RTSP 流（需要 rtsp-simple-server）
            video_source = str(input_source)  # 确保是字符串类型
            
            if is_rtsp_input:
                self.logger.info(f"🌐 读取 RTSP 流：{video_source}")
            else:
                self.logger.info(f"📼 读取视频文件：{video_source}")
            
            # 打开视频源
            self.logger.info(f"正在打开视频源：{video_source}")
            cap = cv2.VideoCapture(video_source)
            
            if not cap.isOpened():
                raise RuntimeError(f"无法打开视频源：{video_source}")
            
            # 获取视频属性
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            self.logger.info(f"视频参数：{width}x{height}, {fps}fps, 总帧数：{total_frames}")
            
            # 初始化 ByteTrack 追踪器
            self._init_tracker()
            
            # 创建视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
            
            # 检查 VideoWriter 是否成功打开
            if not out.isOpened():
                self.logger.error(f"❌ 无法创建输出视频：{output_path}")
                raise RuntimeError(f"无法创建输出视频文件：{output_path}")
            
            self.logger.info(f"✅ 输出视频创建成功：{output_path}")
            
            # 初始化统计信息
            detect_log = []
            frame_count = 0
            start_time = datetime.now()
            
            self.logger.info("开始横幅检测与追踪...")
            
            # 主循环
            while cap.isOpened():
                ret, frame = cap.read()
                
                if not ret:
                    self.logger.info("视频读取完毕")
                    break
                
                # 1. YOLO 检测（不使用 track 模式）
                results = self.model(
                    frame,
                    conf=self.config.CONF_THRESHOLD,
                    verbose=False
                )
                
                # 2. 提取检测结果并转换为 ByteTrack 格式
                detections = []
                if results and results[0].boxes is not None:
                    boxes = results[0].boxes.xyxy.cpu().numpy()
                    confs = results[0].boxes.conf.cpu().numpy()
                    
                    for i in range(len(boxes)):
                        # ByteTrack 格式：[x1, y1, x2, y2, conf]
                        detections.append([
                            boxes[i][0], boxes[i][1], boxes[i][2], boxes[i][3], confs[i]
                        ])
                
                # 3. ByteTrack 追踪
                if detections:
                    detections = np.array(detections)
                    online_targets = self.tracker.update(detections, frame)
                else:
                    online_targets = []
                
                # 4. 绘制追踪结果
                frame = self.draw_tracks(frame, online_targets)
                
                # 写入输出视频
                out.write(frame)
                
                # 5. 记录检测日志
                frame_detections = []
                for target in online_targets:
                    x1, y1, x2, y2 = target.tlbr
                    conf = target.score
                    track_id = target.track_id
                    
                    frame_detections.append({
                        'track_id': int(track_id),
                        'x1': float(x1),
                        'y1': float(y1),
                        'x2': float(x2),
                        'y2': float(y2),
                        'conf': float(conf)
                    })
                
                detect_log.append({
                    'frame_id': frame_count,
                    'banner_ids': [d['track_id'] for d in frame_detections],
                    'detections': frame_detections
                })
                
                frame_count += 1
                
                # 打印进度
                if frame_count % self.config.PROGRESS_INTERVAL == 0:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    current_fps = frame_count / elapsed if elapsed > 0 else 0
                    progress = (frame_count / total_frames * 100) if total_frames > 0 else 0
                    self.logger.info(f"进度：{frame_count}/{total_frames} ({progress:.1f}%), FPS: {current_fps:.1f}")
            
            # 计算统计信息
            total_time = (datetime.now() - start_time).total_seconds()
            avg_fps = frame_count / total_time if total_time > 0 else 0
            
            stats = {
                'total_frames': frame_count,
                'total_time': total_time,
                'avg_fps': avg_fps,
                'output_video': str(output_path),
                'input_source': str(input_source),
                'rtsp_url': rtsp_url
            }
            
            # 保存检测日志
            if self.config.SAVE_DETECT_LOG:
                log_path = self.config.OUTPUT_DIR / output_log_name
                with open(log_path, 'w', encoding='utf-8') as f:
                    json.dump(detect_log, f, indent=2, ensure_ascii=False)
                self.logger.info(f"检测日志已保存：{log_path}")
            
            self.logger.info(f"\n✅ 处理完成！")
            self.logger.info(f"输出视频：{output_path}")
            self.logger.info(f"总帧数：{frame_count}, 总耗时：{total_time:.2f}s, 平均 FPS: {avg_fps:.1f}")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ 处理过程中出错：{str(e)}")
            raise
        
        finally:
            # 清理资源
            if 'cap' in locals() and cap.isOpened():
                cap.release()
            if 'out' in locals() and out.isOpened():
                out.release()
    
    def run_pipeline(self, video_index=None, video_filename=None, interactive=False):
        """
        运行完整处理流程
        
        参数：
            video_index: 视频索引（从 1 开始）
            video_filename: 视频文件名
            interactive: 是否交互式选择
        
        返回：
            dict: 处理结果统计信息
        """
        try:
            # 1. 加载模型
            if not self.load_model():
                return None
            
            # 2. 选择输入源
            selector = InputSourceSelector(self.config)
            
            if interactive:
                video_path = selector.select_interactive()
            elif video_index is not None:
                video_path = selector.select_by_index(video_index)
            elif video_filename is not None:
                video_path = selector.select_by_name(video_filename)
            else:
                # 默认使用 test3.mp4
                video_path = selector.select_by_name('test3')
            
            if video_path is None:
                self.logger.error("❌ 未选择视频文件")
                return None
            
            # 3. 处理视频
            stats = self.process_video(video_path)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ 流程执行失败：{str(e)}")
            return None


def run_detection(weights_path=None, video_path=None, output_path=None, config=None):
    """
    便捷函数：运行横幅检测
    
    参数：
        weights_path: 权重文件路径
        video_path: 视频文件路径
        output_path: 输出路径
        config: 配置对象
    
    返回：
        dict: 处理结果统计信息
    """
    if config is None:
        config = Config()
    
    tracker = BannerDetectionTracker(config)
    
    if weights_path:
        if not tracker.load_model(weights_path):
            return None
    else:
        if not tracker.load_model():
            return None
    
    if video_path is None:
        # 使用默认视频
        video_path = config.VIDEO_DATA_DIR / 'test3.mp4'
    
    return tracker.process_video(video_path, output_path)
