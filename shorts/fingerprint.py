#!/usr/bin/env python3
"""Look-alike check: layout map (24x32 luminance grid) at frame 0 and 25/50/75% of the video, compared with the last videos.
python3 shorts/fingerprint.py <frames_dir> -> prints fingerprint JSON;  python3 shorts/fingerprint.py A_frames B_frames -> distance"""
import glob, json, os, sys
import numpy as np
from PIL import Image

POINTS = (0.0, .25, .5, .75)

def fp(frames_dir):
    fs = sorted(glob.glob(os.path.join(frames_dir, "*.jpg")) or glob.glob(os.path.join(frames_dir, "*.png"))); n = len(fs); out = []
    for p in POINTS:
        im = Image.open(fs[min(n - 1, int(p * (n - 1)))]).convert("L").resize((24, 32), Image.BILINEAR)
        a = np.asarray(im, dtype=float); a = (a - a.mean()) / (a.std() + 1e-6)   # colour-theme independent: structure only
        out.append(np.round(a, 2).tolist())
    return out

def dist(a, b):
    """Mean absolute structure difference (0 = identical layout). Typical: same layout ~0.35-0.6, different ~0.8+."""
    return float(np.mean([np.mean(np.abs(np.array(x) - np.array(y))) for x, y in zip(a, b)]))

if __name__ == "__main__":
    if len(sys.argv) == 2: print(json.dumps(fp(sys.argv[1])))
    else: print(round(dist(fp(sys.argv[1]), fp(sys.argv[2])), 3))
