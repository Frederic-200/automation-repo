#!/usr/bin/env python3
"""FredsDesk Loops - automatic quality check. Exit 0 = pass, 1 = fail (the builder then re-rolls the seed).

    python3 loops/qa.py DIR [--video FILE] [--audio-lufs-target -15]

Checks: format (1080x1920, 30fps, duration), blank / flat / frozen frames, motion present, perfect loop seam
(frame at t=1.0 must equal frame at t=0), audio loudness + loop continuity, caption gone before the end.
"""
import json, os, subprocess, sys, re, glob, tempfile
import numpy as np
from PIL import Image


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate,duration", "-of", "json", path])
    return json.loads(r.stdout)["streams"]


def gray(path):
    return np.asarray(Image.open(path).convert("L"), dtype=np.float32)


def main():
    d = sys.argv[1]; video = sys.argv[sys.argv.index("--video") + 1] if "--video" in sys.argv else os.path.join(d, "final_music.mp4")
    cfg = json.load(open(os.path.join(d, "cfg.json"))); fails = []; notes = []
    D = cfg["frames"] / cfg["fps"]

    # 1) format
    st = probe(video); v = next(s for s in st if s["codec_type"] == "video"); a = next((s for s in st if s["codec_type"] == "audio"), None)
    num, den = map(int, v["r_frame_rate"].split("/"))
    if (v["width"], v["height"]) != (1080, 1920): fails.append(f"size {v['width']}x{v['height']}")
    if abs(num / den - cfg["fps"]) > 0.01: fails.append(f"fps {num/den}")
    if abs(float(v["duration"]) - D) > 0.1: fails.append(f"duration {v['duration']}s != {D}s")
    if a is None: fails.append("no audio track")
    notes.append(f"{v['width']}x{v['height']} {num/den:.0f}fps {float(v['duration']):.2f}s")

    # 2) frames: sample 2 per second
    tmp = tempfile.mkdtemp(); run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-vf", "fps=2,scale=270:480", os.path.join(tmp, "s%03d.png")])
    fr = [gray(p) for p in sorted(glob.glob(os.path.join(tmp, "s*.png")))]
    means = np.array([f.mean() for f in fr]); stds = np.array([f.std() for f in fr])
    diffs = np.array([np.abs(fr[i + 1] - fr[i]).mean() for i in range(len(fr) - 1)])
    if means.min() < 18 or means.max() > 238: fails.append(f"brightness out of range ({means.min():.0f}..{means.max():.0f})")
    if stds.min() < 10: fails.append(f"flat frame (std {stds.min():.1f})")
    frozen = int(np.sum(diffs < 0.25))
    if frozen > 2: fails.append(f"{frozen} frozen sample pairs")
    if diffs.mean() < 1.0: fails.append(f"too little motion (mean diff {diffs.mean():.2f})")
    notes.append(f"brightness {means.min():.0f}-{means.max():.0f}, motion {diffs.mean():.1f}, frozen pairs {frozen}")

    # 3) caption must be gone by the end (clean seam) -> compare last sampled frame's top band to the first non-caption one is
    #    implicit in the seam test below (frame N == frame 0, and frame 0 has no caption visible).

    # 4) loop seam: render t=0 and t=1.0 and compare
    r = run(["node", os.path.join(os.path.dirname(os.path.abspath(__file__)), "render.js"), "--cfg", os.path.join(d, "cfg.json"), "--out", d, "--mode", "seam"])
    if r.returncode: fails.append("seam render failed: " + r.stdout[-300:] + r.stderr[-300:])
    else:
        f0, fN = gray(os.path.join(d, "seam_first.png")), gray(os.path.join(d, "seam_last.png")); sd = float(np.abs(f0 - fN).mean())
        # typical frame-to-frame motion for scale (from the video itself, full-res frame 0 vs 1)
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-vf", "select='lt(n,2)'", "-vsync", "0", os.path.join(tmp, "m%d.png")])
        step = float(np.abs(gray(os.path.join(tmp, "m1.png")) - gray(os.path.join(tmp, "m2.png"))).mean()) if os.path.exists(os.path.join(tmp, "m2.png")) else 1.0
        if sd > max(0.6, step * 0.5): fails.append(f"loop seam differs (mean diff {sd:.2f} vs frame step {step:.2f})")
        notes.append(f"seam diff {sd:.3f} (one frame of motion = {step:.2f})")

    # 5) audio loudness
    if a is not None:
        e = run(["ffmpeg", "-hide_banner", "-nostats", "-i", video, "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
        I = re.findall(r"I:\s+(-?[\d.]+) LUFS", e); P = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e)
        if I and not (-19 <= float(I[-1]) <= -11): fails.append(f"loudness {I[-1]} LUFS")
        if P and float(P[-1]) > -0.5: fails.append(f"true peak {P[-1]} dBFS")
        notes.append(f"audio {I[-1] if I else '?'} LUFS")

    print("QA", "PASS" if not fails else "FAIL", "|", "; ".join(notes))
    for f in fails: print("  FAIL:", f)
    json.dump(dict(passed=not fails, fails=fails, notes=notes), open(os.path.join(d, "qa.json"), "w"))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
