"""OSS Data Hub API — FastAPI + PostGIS.

Ingest and query fish detections (and training-sample metadata) for the OSS
console and the edge inference node. Auth is a single shared key via the
`X-API-Key` header — fine for a handful of vessels; swap for per-vessel keys /
JWT when you scale.

Run:  uvicorn main:app --host 0.0.0.0 --port 8000
Env:  DATABASE_URL, OSS_API_KEY
"""
import os
from datetime import datetime
from typing import Optional, List

import asyncpg
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

API_KEY = os.getenv("OSS_API_KEY", "change-me")
DSN = os.getenv("DATABASE_URL", "postgresql://oss:oss@localhost:5432/oss")

app = FastAPI(title="OSS Data Hub", version="1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
pool: Optional[asyncpg.Pool] = None


@app.on_event("startup")
async def _startup():
    global pool
    pool = await asyncpg.create_pool(DSN, min_size=1, max_size=8)


def _auth(key: Optional[str]):
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="invalid api key")


class Detection(BaseModel):
    lat: float
    lng: float
    species: Optional[str] = None
    count: Optional[int] = 0
    conf: Optional[float] = 0
    game: Optional[bool] = False
    alt: Optional[float] = None
    heading: Optional[float] = None
    note: Optional[str] = ""
    source: Optional[str] = "console"
    box: Optional[List[float]] = None
    vessel: Optional[str] = None  # license key


@app.get("/health")
async def health():
    return {"ok": True, "service": "oss-data-hub"}


@app.post("/v1/detections")
async def add_detection(d: Detection, x_api_key: str = Header(None)):
    _auth(x_api_key)
    async with pool.acquire() as c:
        row = await c.fetchrow(
            """
            INSERT INTO detections
              (species, fish_count, confidence, game, geom,
               altitude_m, heading_deg, note, source, bbox)
            VALUES ($1,$2,$3,$4,
               ST_SetSRID(ST_MakePoint($6,$5),4326)::geography,
               $7,$8,$9,$10,$11)
            RETURNING id, ts
            """,
            d.species, d.count, d.conf, d.game,
            d.lat, d.lng, d.alt, d.heading, d.note, d.source, d.box,
        )
    return {"id": str(row["id"]), "ts": row["ts"].isoformat()}


@app.get("/v1/detections")
async def list_detections(
    west: float = Query(None), south: float = Query(None),
    east: float = Query(None), north: float = Query(None),
    since_hours: int = Query(0, ge=0),
    limit: int = Query(500, le=5000),
    x_api_key: str = Header(None),
):
    _auth(x_api_key)
    cols = ("id, ts, species, fish_count, confidence, game, note, source, "
            "ST_Y(geom::geometry) AS lat, ST_X(geom::geometry) AS lng")
    clauses, args = [], []
    if None not in (west, south, east, north):
        args += [west, south, east, north]
        clauses.append(f"geom && ST_MakeEnvelope(${len(args)-3},${len(args)-2},"
                       f"${len(args)-1},${len(args)},4326)::geography")
    if since_hours:
        args.append(since_hours)
        clauses.append(f"ts > now() - (${len(args)} || ' hours')::interval")
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    args.append(limit)
    async with pool.acquire() as c:
        rows = await c.fetch(
            f"SELECT {cols} FROM detections{where} ORDER BY ts DESC LIMIT ${len(args)}",
            *args,
        )
    return [{**dict(r), "id": str(r["id"]), "ts": r["ts"].isoformat()} for r in rows]


class Sample(BaseModel):
    id: str
    species: Optional[str] = None
    conf: Optional[float] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    alt: Optional[float] = None
    heading: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    image_path: Optional[str] = None  # already uploaded to object storage
    boxes: Optional[list] = None


@app.post("/v1/samples")
async def add_sample(s: Sample, x_api_key: str = Header(None)):
    _auth(x_api_key)
    import json
    async with pool.acquire() as c:
        await c.execute(
            """
            INSERT INTO samples
              (id, species, confidence, geom, altitude_m, heading_deg,
               width, height, image_path, boxes)
            VALUES ($1,$2,$3,
               CASE WHEN $5 IS NULL THEN NULL
                    ELSE ST_SetSRID(ST_MakePoint($5,$4),4326)::geography END,
               $6,$7,$8,$9,$10,$11::jsonb)
            ON CONFLICT (id) DO UPDATE SET boxes = EXCLUDED.boxes,
               species = EXCLUDED.species
            """,
            s.id, s.species, s.conf, s.lat, s.lng, s.alt, s.heading,
            s.width, s.height, s.image_path, json.dumps(s.boxes or []),
        )
    return {"ok": True, "id": s.id}
