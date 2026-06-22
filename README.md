# OSS Console — Ocean Surveillance

Aerial drone fish-spotting console for sport fishing crews. Live drone feed, in-browser
AI vision for surfacing fish schools, mission planning with DJI Pilot 2 waypoint export,
and a hotspot logbook — all in a single installable web app (PWA) that works offline at sea.

## Run it

It's a static app — no build step.

- **Quick look:** open `index.html` in a browser.
- **As a real installable app:** it must be served over HTTPS (the offline/install/update
  features need a secure origin). See *Deploy* below. `localhost` also counts as secure
  for testing: `python3 -m http.server 8777` then open http://localhost:8777.

## Deploy (and how updates reach users)

This repo is the deploy unit. Host it on any static host:

- **Netlify (recommended):** connect this GitHub repo → every `git push` auto-deploys.
  Build command: *(none)*. Publish directory: `.`
- **Manual:** drag this folder onto https://app.netlify.com/drop for an instant HTTPS URL.

**Updates:** the app HTML is served network-first, so a normal reload always pulls the
latest build. Installed/home-screen users see an in-app **"Update now"** banner when a new
version is deployed (service worker + on-demand `skipWaiting`). Bump `APP_VERSION` in
`index.html` and the `oss-v#` cache name in `sw.js` per release.

## Layout

| Path | What it is |
|------|------------|
| `index.html` | The entire front-end app (UI, Leaflet map, AI vision, mission planner, logbook) |
| `sw.js` | Service worker — offline shell + network-first update flow |
| `manifest.webmanifest` | PWA install metadata |
| `icon.svg` | App icon (maskable) |
| `backend/` | Python FastAPI + PostGIS + YOLO training/inference scaffold (optional cloud side) |
| `docs/` | Field-test checklist + first-training-run guide |

## Hardware

Built around the **DJI Mavic 3T** (thermal/IR, Enterprise) — Pilot 2 WPML waypoint missions
+ RTMP live feed. See `docs/` for the field workflow.
