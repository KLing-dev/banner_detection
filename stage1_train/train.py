import argparse
import os
from pathlib import Path
from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(description='YOLO12 Banner Detection Training')
    parser.add_argument('--data', type=str, default='config.yaml', help='Path to data config')
    parser.add_argument('--epochs', type=int, default=100, help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=16, help='Batch size')
    parser.add_argument('--imgsz', type=int, default=640, help='Image size')
    parser.add_argument('--device', type=str, default='0', help='CUDA device (0, 1, ...) or cpu')
    parser.add_argument('--project', type=str, default='train_log', help='Project directory')
    parser.add_argument('--name', type=str, default='exp', help='Experiment name')
    parser.add_argument('--exist-ok', action='store_true', help='Allow overwriting existing experiment')
    return parser.parse_args()


def main():
    args = parse_args()

    if args.device.isdigit():
        device = f'cuda:{args.device}'
    else:
        device = args.device

    model = YOLO('yolo12n.pt')

    results = model.train(
        data=args.data,
        epochs=args.epochs,
        batch=args.batch_size,
        imgsz=args.imgsz,
        device=device,
        project=args.project,
        name=args.name,
        exist_ok=args.exist_ok,
        verbose=True,
        plots=True,
        val=True,
    )

    print(f"\nTraining completed! Weights saved to: {args.project}/{args.name}/weights/")


if __name__ == '__main__':
    main()
