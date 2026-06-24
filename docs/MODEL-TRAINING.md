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

---

## 6. "Always-learning, all-devices" loop — the real architecture

Backed by a verified deep-research pass (2026-06-23, 106 agents).

**Hard truth (verified):** a **browser cannot train a real bounding-box detector.** ONNX Runtime Web "On-Device Training" runs **CPU-only via WebAssembly** and targets fine-tuning/**personalizing a small model** (or a federated client) — not detector training. TF.js "Teachable Machine" only trains a **classifier head on a frozen MobileNet**. So the browser's job is **collect · infer · label**, never "train the detector." (Refuted: ONNX Runtime does *not* itself do federated aggregation.)

**Recommended loop (simplest that genuinely gives "all devices always learning"): centralized retrain + OTA model delivery.** Federated learning (Flower/TFF — each device trains locally, only weight updates leave) is real and privacy-preserving, but it's overkill for a small team *and* the browser can't train the detector anyway, so it doesn't fit. Use the standard MLOps continuous-training loop instead:

```
 EVERY DEVICE (browser PWA)              SERVER (hub — FastAPI/PostGIS, already scaffolded)
 ─────────────────────────              ──────────────────────────────────────────────────
 • infer with current model.onnx   ──▶  • store labeled frames (PostGIS / object store)
   (ONNX Runtime Web + WebGPU)           • RETRAIN trigger: N new labels OR nightly cron
 • capture + label frames                • train YOLO11 @1280 + SAHI on a GPU (Colab/cloud)
   (human + ✨ Claude auto-label)         • quantize → INT8 model.onnx, bump version
 • sync labels up to the hub       ◀──    • publish /model/latest + /model/version
 • SW polls /model/version; if newer,
   download model.onnx (cache-first) ◀── OTA: every device picks up the new model
```

That OTA step is the piece that makes it feel "always learning everywhere": the **service worker version-checks and swaps the model** exactly like it already swaps the app shell. Versioning the model (e.g. `model-v7.onnx` + a `version.json`) is the whole trick.

## 7. Active-learning flywheel (label less, learn faster)

- **VLM-as-teacher → distill into a small student** is a named, proven pattern: **Autodistill** (Roboflow) uses a big foundation vision model to auto-label, then trains a smaller/faster student (YOLO) on those labels. **Our ✨ Claude auto-label button IS the Autodistill "base model"** — keep using it, then train the small detector on the confirmed boxes.
- **Label the frames the model is least sure about** (uncertainty / hard-example mining). **MI-AOD** (instance-level active learning for detection) is the cited method; surface low-confidence frames first instead of labeling randomly. (The specific "MUS-CDB saves 75%" figure was refuted — the *approach* is sound, the exact number isn't.)
- **Human-in-the-loop correction** (confirm/fix Claude's boxes) accelerates convergence — which is exactly the annotator flow.

## 8. Detector tightening checklist

- [ ] **SAHI / tiling** — slice each frame into ~640px tiles and infer per-tile; big AP gain on tiny targets. Altitude-aware/dynamic tiling helps more. **Highest-leverage single trick for our use case.**
- [ ] Train at **1280px** (not 640) — small top-down targets.
- [ ] **YOLO11 vs YOLOv8** — benchmark both on our data (v8 led tiny-object DOTAv1.5; v11 leads general).
- [ ] Augmentation tuned for water: strong HSV-value/sat (sun-glint), copy-paste, mosaic, scale jitter.
- [ ] **Test-time augmentation** for the final eval.
- [ ] Aim ~**10k instances/class** for best results; uncertainty-sampled labels get there faster.

## 9. On-device deployment

- **INT8 quantization** (ONNX Runtime) → much smaller/faster, minor accuracy cost — needed for phones in the field.
- **ONNX Runtime Web on WebGPU** for inference (WebGPU ≫ WebAssembly for vision); WebNN emerging. This is what runs the model in the browser on every device.
- **Distill to a smaller student** if the full model is too heavy on phones — trade a little accuracy for real-time speed.

_Sources: MS On-Device Training (ORT Web), TF.js Teachable-Machine codelab, Google MLOps continuous-delivery, Flower FL tutorial, Roboflow Autodistill, MI-AOD (arXiv 2104.02324), SAHI (obss.github.io/sahi), Ultralytics YOLO11-vs-v8 + export, ONNX Runtime quantization. Verified run wohkgblgk._
