# OSS Data Hub — backend

The cloud/edge half of Ocean Surveillance Services. The single-file console
(`../index.html`) is the cockpit; this is the **data processing hub** + **ML
pipeline** it talks to. Everything here is real, runnable code — it is not
wired into the console by default (the console stays local-first and works with
zero backend). Point the console at it when you're ready: DATA / LAB tab →
Cloud Data Hub → paste the API URL + key.

```
backend/
  docker-compose.yml     postgis + api + mediamtx (one command to stand it all up)
  db/schema.sql          PostGIS schema (detections as geography points, samples, models)
  api/                   FastAPI service — ingest + query detections/samples
  ml/train.py            train YOLO on the dataset exported from the console
  ml/edge_infer.py       edge node: read RTSP, run the model, POST detections
```

## Languages / stack (why)
- **Python (FastAPI)** for the API and all ML — the ecosystem (Ultralytics
  YOLO, OpenCV, PyTorch) lives here.
- **PostgreSQL + PostGIS** for storage — geospatial queries ("every bluefin
  spotted in this box in the last 30 days") are one line; TimescaleDB can be
  layered on for telemetry time-series later.
- **MediaMTX** as the RTMP→RTSP/HLS/WebRTC gateway (the drone livestream bridge).
- **JS / Leaflet** stays the front end — it speaks to this over plain REST.

## Run it
```bash
cd backend
export OSS_API_KEY=$(openssl rand -hex 16)   # your hub key
docker compose up --build
# API:    http://localhost:8000/health
# Stream: rtmp://<host>:1935/oss  →  http://<host>:8888/oss/index.m3u8
```

## The data flow
1. Console (or `edge_infer.py`) POSTs detections to `/v1/detections`.
2. They land in PostGIS as geography points → instant hotspot queries.
3. Console pulls shared hotspots back via `GET /v1/detections?west=&south=&east=&north=`.
4. Labeled frames exported from the console (YOLO zip) train a model
   (`ml/train.py`); the model runs at the edge (`ml/edge_infer.py`) and feeds
   detections back in. That is the flywheel.

## The one hard piece: georeferencing
`edge_infer.py` ships with a placeholder that maps a detection to the drone's
current GPS. The real version projects the **image pixel → ground lat/lng**
using aircraft GPS + altitude + gimbal yaw/pitch/roll + camera intrinsics
against a flat-sea assumption. That math turns a bounding box into a map pin and
is what makes the whole product geospatial. Build it there.
