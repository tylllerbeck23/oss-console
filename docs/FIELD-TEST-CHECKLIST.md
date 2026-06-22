# OSS Console — field-test checklist

A practical run-through for your first on-the-water (or backyard) tests. The
goal of early testing is two things: (1) prove the workflow end-to-end, and
(2) start banking labeled training data. Don't chase a perfect AI yet.

## Before you leave the dock
- [ ] Open the **hosted** link (Netlify/HTTPS), not the local file — GPS, webcam,
      camera capture, and "add to home screen" only work fully on HTTPS.
- [ ] Activate with a license key (`~/Downloads/OSS-License-Keys.txt`).
- [ ] CONNECT → pick **DJI Mavic 3T**.
- [ ] CONNECT → **Start Vessel GPS** (or Set on Map / type coordinates).
- [ ] Phone fully charged; you'll be capturing a lot of frames.

## Prove the pipeline with NO drone (do this first, on land)
- [ ] CONNECT → **Use Webcam**, point it at moving water / a video.
- [ ] OPERATE → **▶ Start Live AI** → wave your hand or aim at chop → confirm it
      draws "disturbance" boxes. Slide **Sensitivity** to tune.
- [ ] OPERATE → **✎ Label Live Frame** → box a "school" → pick species → Save.
- [ ] DATA / LAB → confirm the frame is there → **Export YOLO Dataset (.zip)**.
- [ ] DATA HUB → **▶ Simulate Drone** → flip to OPERATE → watch the drone fly the
      mission, telemetry stream, and cards go green.
- [ ] PLAN FLIGHT → **Around Vessel** → Generate → **Simulate Flight & Battery** →
      **Download DJI Mission (.kmz)** → open it in **DJI Pilot 2** to confirm it
      imports. *(This is the single most important pre-flight check.)*

## On the water with the drone
- [ ] In **Pilot 2**: start the **RTMP livestream** to your gateway; paste the
      HLS/WebRTC URL into CONNECT → Connect Feed.
- [ ] Import the `.kmz` into Pilot 2 → Waypoint → fly the search grid.
- [ ] As you spot fish: **Mark Fish on Map** (auto-banks a frame) or **Label Live**.
- [ ] Capture **negatives** too: glare, birds, boats, empty water, whitecaps —
      hit **Capture Frame** over those. The model needs to learn what *isn't* fish.
- [ ] Keep an eye on **DATA HUB** — feed fps, telemetry age, AI candidates.

## After the trip
- [ ] DATA / LAB → label every captured frame (box the whole school/disturbance).
- [ ] **Export the dataset** and back it up (frames live only on the device until
      the cloud hub is running).
- [ ] LOGBOOK → review hotspots + best-bite-times.

## What to tell Claude afterward
- Anything clunky or confusing in the flow.
- Did the `.kmz` import + fly cleanly? (If Pilot 2 rejected it, note the exact
  error — likely the WPML drone enum needs a tweak for your aircraft.)
- Roughly how many labeled frames you collected, and of what.
- Did the AI flag real disturbance, or mostly glare/noise? At what sensitivity?
