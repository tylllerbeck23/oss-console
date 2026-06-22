"""OSS edge inference node.

Reads the drone's video (RTSP from the MediaMTX gateway), runs the trained YOLO
model, georeferences each detection, and POSTs it to the Data Hub — which is
exactly what the console renders. This is the "real" detector that replaces the
browser's beta AI once you have a trained model.

Runs on the ground-station laptop or a Jetson Orin Nano (the Mavic 3T can't
carry a companion computer, so inference is off-board on the stream).

Env: OSS_API, OSS_API_KEY, OSS_RTSP, OSS_MODEL
"""
import os
import time

import cv2
import requests
from ultralytics import YOLO

API = os.getenv("OSS_API", "http://localhost:8000")
KEY = os.getenv("OSS_API_KEY", "change-me")
RTSP = os.getenv("OSS_RTSP", "rtsp://localhost:8554/oss")
MODEL = os.getenv("OSS_MODEL", "runs/detect/oss-fish/weights/best.pt")
CONF = float(os.getenv("OSS_CONF", "0.40"))


def get_telemetry():
    """Latest drone pose. Replace with a DJI Cloud-API / MSDK bridge.
    Needs at minimum: lat, lng, rel_alt_m, yaw_deg, gimbal_pitch_deg."""
    return {"lat": 27.31, "lng": -82.62, "alt": 100.0,
            "yaw": 0.0, "gimbal_pitch": -90.0}


def georeference(box_xywhn, frame_w, frame_h, tele):
    """Project an image-space box center to ground lat/lng.

    Placeholder: returns the drone's nadir point (good enough when the gimbal
    looks straight down). The real version ray-casts the pixel through the
    camera model using yaw + gimbal pitch + altitude against a flat sea surface
    and offsets lat/lng by the ground intersection. Build it here — this is the
    function that turns a detection into a map pin.
    """
    return tele["lat"], tele["lng"]


def main():
    model = YOLO(MODEL)
    cap = cv2.VideoCapture(RTSP)
    print(f"edge: model={MODEL} rtsp={RTSP} -> {API}")
    last = 0.0
    while True:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.2)
            cap.open(RTSP)
            continue
        if time.time() - last < 0.2:   # ~5 fps inference
            continue
        last = time.time()
        h, w = frame.shape[:2]
        res = model(frame, verbose=False)[0]
        tele = get_telemetry()
        for b in res.boxes:
            conf = float(b.conf[0])
            if conf < CONF:
                continue
            cls = model.names[int(b.cls[0])]
            xywhn = b.xywhn[0].tolist()           # [cx,cy,w,h] normalized
            lat, lng = georeference(xywhn, w, h, tele)
            try:
                requests.post(
                    f"{API}/v1/detections",
                    headers={"X-API-Key": KEY},
                    json={
                        "lat": lat, "lng": lng, "species": cls,
                        "conf": round(conf * 100, 1), "source": "edge",
                        "alt": tele.get("alt"), "heading": tele.get("yaw"),
                        "box": [xywhn[0] - xywhn[2] / 2, xywhn[1] - xywhn[3] / 2,
                                xywhn[2], xywhn[3]],
                    },
                    timeout=2,
                )
            except requests.RequestException as e:
                print("post failed:", e)


if __name__ == "__main__":
    main()
