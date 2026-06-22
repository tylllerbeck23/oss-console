-- OSS Data Hub — PostGIS schema
-- Detections are stored as geography points so hotspot / bbox / radius queries
-- are one line. Runs automatically on first `docker compose up`.

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- gen_random_uuid()

-- one row per customer boat (ties to the console license key)
CREATE TABLE IF NOT EXISTS vessels (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name        text,
  license_key text UNIQUE,
  created_at  timestamptz NOT NULL DEFAULT now()
);

-- every confirmed / auto detection
CREATE TABLE IF NOT EXISTS detections (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  vessel_id    uuid REFERENCES vessels(id),
  ts           timestamptz NOT NULL DEFAULT now(),
  species      text,
  fish_count   int,
  confidence   real,                       -- 0..100
  game         boolean DEFAULT false,
  geom         geography(Point,4326) NOT NULL,
  altitude_m   real,
  heading_deg  real,
  note         text,
  source       text,                       -- 'console' | 'edge' | 'ai'
  bbox         real[]                       -- [x,y,w,h] normalized 0..1 (optional)
);
CREATE INDEX IF NOT EXISTS detections_geom_idx ON detections USING GIST (geom);
CREATE INDEX IF NOT EXISTS detections_ts_idx   ON detections (ts DESC);

-- captured training frames (images go to object storage; this is the index)
CREATE TABLE IF NOT EXISTS samples (
  id          text PRIMARY KEY,            -- console-generated id
  vessel_id   uuid REFERENCES vessels(id),
  ts          timestamptz NOT NULL DEFAULT now(),
  species     text,
  confidence  real,
  geom        geography(Point,4326),
  altitude_m  real,
  heading_deg real,
  width       int,
  height      int,
  image_path  text,                        -- s3://... or /data/...
  boxes       jsonb                        -- [{species,x,y,w,h}, ...]
);
CREATE INDEX IF NOT EXISTS samples_ts_idx ON samples (ts DESC);

-- trained model registry
CREATE TABLE IF NOT EXISTS models (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name       text,
  version    text,
  path       text,
  metrics    jsonb,                        -- {map50, precision, recall, ...}
  created_at timestamptz NOT NULL DEFAULT now()
);

-- example hotspot query (grid-binned counts in a bbox over the last 30 days):
--   SELECT ST_SnapToGrid(geom::geometry, 0.01) AS cell, count(*), avg(confidence)
--   FROM detections
--   WHERE ts > now() - interval '30 days'
--     AND geom && ST_MakeEnvelope(:w,:s,:e,:n,4326)::geography
--   GROUP BY cell ORDER BY count DESC;
