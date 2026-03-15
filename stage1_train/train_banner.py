from ultralytics import YOLO
import torch

def main():
    # 1. 严格限制GPU0显存占用至95%
    if torch.cuda.is_available():
        torch.cuda.set_per_process_memory_fraction(0.95, device=0)
        total_mem = torch.cuda.get_device_properties(0).total_memory / 1024 / 1024
        print(f"✅ GPU0显存限制：95%（总显存{total_mem:.0f}MB → 可用{total_mem*0.95:.0f}MB）")
        print(f"✅ 当前使用GPU：{torch.cuda.get_device_name(0)}")
    else:
        print("⚠️ 未检测到GPU，将使用CPU训练（速度极慢）")

    # 2. 加载YOLOv12预训练模型
    model = YOLO('yolov12n.pt')
    print("📌 成功加载YOLOv12n模型")

    # 3. 开始训练（固定batch=16，2的次方倍数+适配95%显存）
    try:
        data_path = r"F:\data\Projects\graduate\banner_detection\stage1_train\banner\banner.yaml"
        
        results = model.train(
            data=data_path,          
            epochs=200,
            imgsz=640,
            batch=16,                # 核心：2的次方倍数，最接近23且显存安全
            device='0',
            patience=15,             # 15轮无提升停止
            lr0=0.005,
            weight_decay=0.0005,
            fliplr=0.5,
            flipud=0.0,
            mosaic=1.0,
            pretrained=True,
            save=True,
            project='runs/train',
            name='yolov12_banner_final',
            val=True,
            cache=False              
        )

        # 打印训练结果
        print(f"\n✅ 训练完成！最优权重路径：runs/train/yolov12_banner_final/weights/best.pt")
        print(f"✅ 验证集mAP@0.5: {results.trainer.best_metrics['metrics/mAP50(B)']:.4f}")

    except Exception as e:
        print(f"❌ 训练出错：{e}")
        print(f"💡 检查数据集路径是否正确：{data_path}")
        print("💡 若显存溢出，将batch=16改为batch=8（2³）")

if __name__ == '__main__':
    main()