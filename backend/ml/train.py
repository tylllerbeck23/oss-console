"""Train the OSS fish detector on a dataset exported from the console.

1. In the console: DATA / LAB tab -> Export YOLO Dataset (.zip), unzip it.
2. pip install -r requirements.txt
3. python train.py --data path/to/OSS_dataset/data.yaml

Start small and narrow (one target, good conditions) — reliability comes from
data volume + a constrained problem, not a bigger model. Fine-tune from a
pretrained checkpoint (transfer learning) so a few hundred labeled frames go a
long way. Re-run as the dataset grows (active learning); each export is bigger
and the model gets sharper.
"""
import argparse
from ultralytics import YOLO


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="OSS_dataset/data.yaml")
    ap.add_argument("--model", default="yolo11n.pt", help="pretrained checkpoint")
    ap.add_argument("--epochs", type=int, default=120)
    ap.add_argument("--imgsz", type=int, default=1280, help="aerial schools are small -> large imgsz")
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--name", default="oss-fish")
    args = ap.parse_args()

    model = YOLO(args.model)
    model.train(
        data=args.data, epochs=args.epochs, imgsz=args.imgsz, batch=args.batch,
        name=args.name,
        # augmentation tuned for water/glare robustness
        hsv_h=0.015, hsv_s=0.7, hsv_v=0.5, fliplr=0.5, mosaic=1.0, degrees=10,
        patience=30,
    )
    # export for the edge node (ONNX runs fast on a Jetson / CPU)
    model.export(format="onnx", imgsz=args.imgsz, simplify=True)
    print("done -> runs/detect/%s/weights/best.pt (+ best.onnx)" % args.name)


if __name__ == "__main__":
    main()
