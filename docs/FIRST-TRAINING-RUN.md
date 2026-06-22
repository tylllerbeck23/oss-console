# OSS — your first model training run

How to turn the frames you collect in the console into a working fish detector.
You don't need this until you have a few hundred labeled frames, but here's the
whole path so you can see where it's going.

## 0. What "good" looks like at the start
- **Narrow the target.** One thing first — e.g. "surface bait balls + tarpon
  strings, clear water, daylight, 200–350 ft." Win that before adding species.
- A few **hundred** labeled frames is enough to start seeing signal; a few
  **thousand** makes it useful. Negatives (glare/birds/empty water) matter as
  much as positives.

## 1. Export from the console
DATA / LAB → **Export YOLO Dataset (.zip)** → unzip. You get:
```
OSS_dataset/
  images/        the captured frames
  labels/        one YOLO .txt per image (class cx cy w h, normalized)
  data.yaml      class list + paths
  classes.txt
```

## 2. (Optional) clean it up in Roboflow or CVAT
Drag the folder into **Roboflow** (free tier) or **CVAT** to review boxes, fix
mistakes, add augmentation, and split train/val. Re-export as YOLO. This step
pays off — bad labels cap your accuracy.

## 3. Train (Python)
```bash
cd backend/ml
pip install -r requirements.txt           # ultralytics, opencv, requests
python train.py --data /path/to/OSS_dataset/data.yaml --epochs 120 --imgsz 1280
```
- `imgsz 1280` because aerial schools are small objects — don't shrink them away.
- Start from the pretrained `yolo11n.pt` (transfer learning) so little data goes far.
- Watch `runs/detect/oss-fish/` for `results.png` (loss curves) and
  `best.pt`. Aim to grow **recall** first (don't miss fish), then **precision**
  (stop false alarms on glare).
- Free GPUs: Google Colab, or RunPod/Modal/Replicate for a few dollars.

## 4. Use it
**Option A — drop it into the console (browser):** export to TF.js/ONNX and
swap the loader in the AI engine's `runModel()` (currently COCO-SSD). The whole
overlay + georeferencing + logging pipeline already works around it.

**Option B — run it at the edge (recommended for real flights):**
```bash
export OSS_API=http://your-hub:8000 OSS_API_KEY=... OSS_RTSP=rtsp://gateway:8554/oss
export OSS_MODEL=runs/detect/oss-fish/weights/best.pt
python backend/ml/edge_infer.py
```
It reads the drone stream, runs the model, georeferences each hit, and POSTs to
the Data Hub — which the console renders live. This is the production loop.

## 5. The flywheel
Every flight you keep marking/confirming fish → more labeled frames → retrain →
sharper model → it pre-flags more, you confirm faster. The product literally
trains itself the more you use it. The only thing that compounds is **your data**,
so collect relentlessly and label consistently.

## The one piece to build for real geo-accuracy
`backend/ml/edge_infer.py` has a `georeference()` placeholder (returns the
drone's nadir point). The browser already does a proper flat-sea projection
(`OSS.georeference`) — port that math to the edge node, feeding it real gimbal
pitch/yaw from DJI telemetry, and your detections will land dead-on the fish.
