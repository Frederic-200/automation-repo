#!/usr/bin/env python3
"""Novelty (rejection) test for v2 videos: is today's video too close to any of the last 14?

    python3 shorts/v2/novelty.py check PREVIEW_DIR [--log shorts/v2/novelty_log.json] [--min 0.12] [--last 14]
    python3 shorts/v2/novelty.py add   PREVIEW_DIR --date YYYY-MM-DD --slug SLUG --world a --palette ember [--extra '{"hook_type":"pov","ending":"loop","voice":"af_heart","music":"gentle"}'] [--log ...]
    python3 shorts/v2/novelty.py pair  DIR_A DIR_B                       (print the distance between two preview sets)

PREVIEW_DIR = the PNGs written by `build.py --preview` (one frame per scene + the frame-0 hook). Cheap: no full render needed.
Each frame -> colour (4x4x4 histogram), layout (12x16 luminance map) and texture (6x8 edge-energy map). Two videos are compared frame to frame
(each frame matched to its nearest frame in the other video, both ways), so "same layout, different words" still counts as close.
Compares ONLY against the v2 log (never against old loops/shorts). Exit 0 = novel enough, 3 = too close (re-roll world/palette, see pick_world.py).
"""
import glob, json, os, sys
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); LOG = os.path.join(HERE, "novelty_log.json")
W_COL, W_LAY, W_TEX = .40, .35, .25


def feats(png):
    im = Image.open(png).convert("RGB").resize((108, 192), Image.BILINEAR); a = np.asarray(im, dtype=np.float32) / 255
    q = np.minimum((a * 4).astype(int), 3); idx = q[..., 0] * 16 + q[..., 1] * 4 + q[..., 2]
    col = np.bincount(idx.ravel(), minlength=64).astype(np.float32); col /= col.sum()
    lum = np.asarray(im.convert("L").filter(ImageFilter.GaussianBlur(3)), dtype=np.float32) / 255
    lay = np.asarray(Image.fromarray((lum * 255).astype(np.uint8)).resize((12, 16), Image.BOX), dtype=np.float32) / 255; lay = lay - lay.mean()
    g = np.asarray(im.convert("L"), dtype=np.float32) / 255; gx = np.abs(np.diff(g, axis=1))[:-1, :]; gy = np.abs(np.diff(g, axis=0))[:, :-1]; e = gx + gy
    tex = np.asarray(Image.fromarray((np.clip(e * 4, 0, 1) * 255).astype(np.uint8)).resize((6, 8), Image.BOX), dtype=np.float32) / 255
    return {"c": np.round(col, 4).tolist(), "l": np.round(lay, 3).ravel().tolist(), "t": np.round(tex, 3).ravel().tolist()}


def frame_dist(a, b):
    c = .5 * np.abs(np.array(a["c"]) - np.array(b["c"])).sum()                 # 0..1
    l = min(1.0, float(np.abs(np.array(a["l"]) - np.array(b["l"])).mean()) / .25)   # 0..1 (0.25 = very different layout)
    t = min(1.0, float(np.abs(np.array(a["t"]) - np.array(b["t"])).mean()) / .12)
    return W_COL * c + W_LAY * l + W_TEX * t, (c, l, t)


def video_dist(A, B):
    """symmetric nearest-frame distance: every frame of A matched to its closest frame in B and vice versa."""
    def one(X, Y): return float(np.mean([min(frame_dist(x, y)[0] for y in Y) for x in X]))
    return (one(A, B) + one(B, A)) / 2


def load_dir(d):
    fs = sorted(glob.glob(os.path.join(d, "preview_*.png")))
    if not fs: sys.exit(f"no preview_*.png in {d}")
    return [feats(f) for f in fs]


def log_load(p): return json.load(open(p)) if os.path.exists(p) else {"entries": []}


def main():
    a = sys.argv[1:]
    if len(a) < 2: print(__doc__); sys.exit(2)
    cmd = a[0]; opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    logp = opt("--log", LOG)
    if cmd == "pair":
        A, B = load_dir(a[1]), load_dir(a[2]); print(f"distance {video_dist(A, B):.3f}"); return
    F = load_dir(a[1])
    if cmd == "add":
        L = log_load(logp); L["entries"].append({"date": opt("--date"), "slug": opt("--slug"), "world": opt("--world"), "palette": opt("--palette"), "frames": F, **json.loads(opt("--extra", "{}"))})
        json.dump(L, open(logp, "w")); print(f"logged {opt('--slug')} ({len(L['entries'])} entries)"); return
    if cmd == "check":
        mn = float(opt("--min", .12)); last = int(opt("--last", 14)); E = log_load(logp)["entries"][-last:]
        if not E: print("no v2 history yet: novel by definition"); return
        rows = sorted(((video_dist(F, e["frames"]), e) for e in E), key=lambda r: r[0])
        for d, e in rows[:3]: print(f"  closest: {e.get('date')} {e.get('slug')} ({e.get('world')}/{e.get('palette')}) distance {d:.3f}")
        d0, e0 = rows[0]
        if d0 < mn: print(f"TOO CLOSE to {e0.get('slug')}: {d0:.3f} < {mn}. Re-roll the world/palette (pick_world.py --reroll N)."); sys.exit(3)
        print(f"NOVEL (closest {d0:.3f} >= {mn})"); return
    print(__doc__); sys.exit(2)


if __name__ == "__main__":
    main()
