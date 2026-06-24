# OSS Console — Base Detection Model: training plan

Goal: **one shared base model** (exported to **ONNX**, runs in the browser) that detects
**fish/surface signs**, **people / persons-in-water (PIW)**, and **SAR targets** —
so the Fishing, SAR, and CAP editions all light up from one trained model.

This plan is backed by a verified, cited research pass (2026-06-23). Key takeaways below;
the runnable steps are in [`backend/ml/OSS_base_train.ipynb`](../backend/ml/OSS_base_train.ipynb)
and [`backend/ml/train.py`](../backend/ml/train.py).

---

## 1. Datasets

| Dataset | View | Classes | Size | License | Use it? |
|---|---|---|---|---|---|
| **SeaDronesSee** | aerial/UAV | swimmer/**PIW**, boat, jet-ski, buoy, life-jacket | ~10.5k labeled imgs (COCO) + 22 video clips | **CC0 1.0 (public domain)** | ✅ **Yes — foundation for SAR/PIW.** Commercial-safe. |
| **AFO** (Aerial Floating Objects) | aerial | person (80%+), boat, board, buoy, kayak, sailboat | 3,647 imgs / 39,991 objs (YOLO) | **CC BY-NC-SA (non-commercial)** | ⚠️ **Avoid for paid editions** — non-commercial taints sellable weights. OK for internal R&D only. |
| Fish (underwater): DeepFish, Brackish, FathomNet | underwater | fish | large | various | ❌ Wrong viewpoint. Underwater ≠ top-down surface. Not useful. |
| **Surface fish (aerial)** | aerial | redfish, tarpon, snook, cobia, tuna, mahi, bait-ball, nervous-water | — | — | 🟡 **No public set exists — you build it** (app Dataset/AI-Lab tab → YOLO export). |

**Bottom line:** the SAR/PIW half is basically solved by **SeaDronesSee (CC0)**. The fish half
has **no public aerial dataset** — it must come from your own labeled drone frames, which is
exactly what the app's capture → annotate → "Export YOLO Dataset (.zip)" pipeline produces.

### Sources (download)
- SeaDronesSee: https://github.com/Ben93kie/SeaDronesSee · https://www.macvi.org/dataset (registration may be required)
- AFO (R&D only): https://www.kaggle.com/datasets/jangsienicajzkowy/afo-aerial-dataset-of-floating-objects
- Extra footage: NOAA photo library (public domain **stills**; vet **video** per-item for third-party clips), USCG public affairs, your own + Creative-Commons drone-fishing footage. Pull frames with `yt-dlp` + `ffmpeg` (see `backend/ml/youtube_frames.py`).

---

## 2. Base model

- **Prototype on YOLO11** — best general COCO accuracy-per-parameter, exports cleanly to ONNX.
- **Benchmark YOLOv8** — on tiny top-down aerial targets it beat YOLO11 by ~4 mAP (DOTAv1.5).
- **Consider RT-DETR** — validated for maritime small objects on SeaDronesSee (MSO-DETR).
- **Browser path = ONNX** (ONNX Runtime Web / TF.js). *Not* TensorRT (NVIDIA-only).

> Don't trust one leaderboard — **benchmark all three on your actual merged data at 1280px.**

## 3. Recipe

- **Image size: 1280px** (not the default 640) — surface fish & PIW are small.
- **Instances per class:** aim for **~10,000 labeled objects/class** for best results. You can
  **start fine-tuning with 30–50 images/class** from a pretrained checkpoint (transfer learning).
- **Tiling / SAHI** for very small targets (YOLO resizes the whole frame, so slice high-res frames).
- **Augmentation for water:** strong HSV-value/sat jitter (sun-glint), horizontal flip, mosaic, slight rotation.
- **Split:** ~80/20 train/val. **Tooling:** Roboflow / CVAT / Label Studio.
- **Compute:** Google Colab (free T4) is enough to start; a few hours per run.

## 4. Do-this-next

1. **Collect fish data in the app** — fly, mark/capture frames in the **AI Lab / Dataset** tab,
   label species, then **Export YOLO Dataset (.zip)**.
2. **Download SeaDronesSee** (CC0) and convert COCO→YOLO (notebook cell does this).
3. **Merge** the SAR/PIW classes (SeaDronesSee) with your fish classes into one `data.yaml`.
4. **Train** YOLO11 @1280px on Colab; benchmark YOLOv8. (`train.py` or the notebook.)
5. **Export ONNX** (`model.export(format="onnx")`).
6. **Wire into the app** — drop `best.onnx` into the neural-detection seam (the app already
   lazy-loads a model for "neural mode"; we swap the loader to your ONNX via ONNX Runtime Web).
   Ping me and I'll do step 6.

## 5. ⚖️ Legal notes (read before shipping weights)

- ✅ **Legal has cleared the AI-training approach for this project — proceed with the best method** (YOLO11 prototype + YOLOv8 benchmark, 1280px, SeaDronesSee + own footage). Context: 2025 US rulings lean toward model training being fair use.
- **SeaDronesSee is CC0** → safe to ship in commercial weights. Keep the **AFO** dataset out of paid-edition weights (its non-commercial license is a dataset-licensing term, separate from the training-fair-use question), and don't use CC **NoDerivatives** works as training data.
- Separate from the model: **using a drone to assist fishing is itself legally restricted** for some species/states (bluefin tuna 50 CFR 635; Florida spotter-plane rule 68B-4.013). See the in-app Regulations section.

_Research basis: SeaDronesSee (CC0, COCO), AFO (Kaggle), Ultralytics training tips, DOTAv1.5/MSO-DETR small-object benchmarks, CC 2025 AI-training primer. Full cited report in session memory._
