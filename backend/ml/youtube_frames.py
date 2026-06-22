"""Pull training frames from a YouTube (or any) video URL.

The browser can't grab frames from an embedded YouTube player (cross-origin),
so the console's footage library saves YouTube links for reference and uses this
script to actually extract frames for labeling.

Usage:
  pip install yt-dlp           # plus ffmpeg on PATH
  python youtube_frames.py "https://youtu.be/XXXXXXXXXXX" --every 2 --out frames/

Then drop the frames into Roboflow/CVAT (or the console can't import folders, so
label them in a tool), and fold them into your YOLO dataset for train.py.

Respect copyright/terms — use footage you have the right to use for training.
"""
import argparse
import os
import subprocess
import tempfile


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--every", type=float, default=2.0, help="seconds between frames")
    ap.add_argument("--out", default="frames")
    ap.add_argument("--max-h", type=int, default=1080)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        vid = os.path.join(tmp, "clip.mp4")
        print("downloading…")
        subprocess.run([
            "yt-dlp", "-f", f"bestvideo[height<={args.max_h}]+bestaudio/best",
            "--merge-output-format", "mp4", "-o", vid, args.url,
        ], check=True)
        print("extracting frames…")
        subprocess.run([
            "ffmpeg", "-i", vid, "-vf", f"fps=1/{args.every}",
            "-q:v", "2", os.path.join(args.out, "frame_%05d.jpg"),
        ], check=True)

    n = len([f for f in os.listdir(args.out) if f.endswith(".jpg")])
    print(f"done -> {n} frames in {args.out}/  (label them, then add to your YOLO dataset)")


if __name__ == "__main__":
    main()
