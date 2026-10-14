"""Render the FredsDesk outro (3 s) in the visual style of a given video, with synthesized SFX.

    python3 outro_build.py --style-work MAIN_WORK --out OUTDIR [--mood lofi] [--seconds 3.0]

MAIN_WORK is the work dir of the video the outro will follow (style.json + fonts.json + fonts/ are reused,
so the outro background, palette, fonts, post-FX and accent match that video exactly).
Outputs OUTDIR/outro.mp4 (video + sfx) and OUTDIR/outro.wav.
"""
import json, os, shutil, subprocess, sys
import numpy as np, soundfile as sf
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = "/root/.cache/video-kit/kit/scripts"
SR = 48000
KEY = {"lofi": 880.0, "gentle": 1046.5, "upbeat": 1046.5, "synthwave": 880.0, "epic": 1174.7, "trap": 1568.0}   # chime root (A5 / C6 / D6 / G6)


def sfx(dur, mood, seed=7):
    rng = np.random.default_rng(seed); n = int(dur * SR); out = np.zeros(n, np.float32)
    def add(t0, x, g=1.0):
        i = int(t0 * SR); j = min(n, i + len(x)); out[i:j] += (x[:j - i] * g).astype(np.float32)
    def tt(d): return np.arange(int(d * SR)) / SR
    def sine(f, d, dec, g=1.0):
        t = tt(d); return np.sin(2 * np.pi * f * t) * np.exp(-t * dec) * g
    # 0.00 whoosh: band-passed noise sweep (low -> high), 0.4 s
    d = .45; nz = rng.standard_normal(int(d * SR)); w = np.zeros_like(nz); L = len(nz); hop = L // 24
    for k in range(24):
        fc = 350 * (10 ** (k / 23 * 0.95)); b, a = signal.butter(2, [fc * .7 / (SR / 2), min(.99, fc * 1.4 / (SR / 2))], "band")
        seg = signal.lfilter(b, a, nz); win = np.zeros(L); lo = max(0, k * hop - hop); hi = min(L, k * hop + 2 * hop); win[lo:hi] = np.hanning(hi - lo); w += seg * win
    env = np.sin(np.linspace(0, np.pi, L)) ** 1.5; add(0.0, w / (np.abs(w).max() + 1e-9) * env, .55)
    # 0.30-1.0 shimmer while the desk draws: rising sparkles on a pentatonic scale
    scale = [0, 2, 4, 7, 9]; root = KEY.get(mood, 880.0) / 2
    for k in range(14):
        t0 = .32 + k * .05; f = root * 2 ** ((scale[k % 5] + 12 * (k // 5)) / 12); add(t0, sine(f, .22, 14), .16 * (.5 + k / 26))
    # 1.00 power-on blip
    t = tt(.12); f = 650 + 900 * (t / .12); add(1.0, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 22), .45)
    # 1.52 mouse click: down + up
    def click(g):
        t = tt(.06); n1 = rng.standard_normal(len(t)); b, a = signal.butter(2, 1800 / (SR / 2), "high"); c = signal.lfilter(b, a, n1) * np.exp(-t * 160)
        return c * g + sine(160, .06, 70, g * .9)
    add(1.52, click(.55)); add(1.585, click(.28))
    for k, g in enumerate((.26, .20, .15)):                       # ripple "bloops", one per ring
        t = tt(.30); f = (380 + 70 * k) + 260 * (t / .30); add(1.57 + k * .12, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11), g)
    # 1.70-2.24 letter ticks (rising pitch)
    for i in range(9): add(1.7 + i * .065, sine(1500 + i * 140, .05, 70), .30)
    # 2.30 logo chime (bell partials in the music's key) + soft tail
    f0 = KEY.get(mood, 880.0)
    for k, (r, g, dec) in enumerate([(1, 1.0, 2.2), (1.5, .55, 2.6), (2, .45, 3.2), (3, .22, 4.5)]): add(2.30, sine(f0 * r, 1.4, dec), .30 * g)
    add(2.42, sine(f0 * 1.5, 1.2, 2.8), .20)
    # 2.55 light sweep swish
    d = .35; nz = rng.standard_normal(int(d * SR)); b, a = signal.butter(2, [2500 / (SR / 2), 9000 / (SR / 2)], "band"); sw = signal.lfilter(b, a, nz) * np.sin(np.linspace(0, np.pi, len(nz))) ** 2
    add(2.55, sw / (np.abs(sw).max() + 1e-9), .12)
    out = np.tanh(out * 1.7); out *= 0.89 / (np.abs(out).max() + 1e-9)     # soft-clip drive: sparse SFX read as loud as the voiced body
    # gentle fade at the very end, then loudness ~ -16 LUFS short-term (SFX only, a bit lighter than speech videos)
    out[-int(.25 * SR):] *= np.linspace(1, 0, int(.25 * SR)) ** 1.5
    return np.stack([out, out], 1)


def main():
    a = sys.argv[1:]; opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    style_work = os.path.abspath(opt("--style-work")); out = os.path.abspath(opt("--out")); mood = opt("--mood", "lofi"); secs = float(opt("--seconds", 3.0))
    work = os.path.join(out, "work"); shutil.rmtree(work, ignore_errors=True); os.makedirs(work)
    shutil.copy(os.path.join(style_work, "style.json"), work); shutil.copy(os.path.join(style_work, "fonts.json"), work)
    shutil.copytree(os.path.join(style_work, "fonts"), os.path.join(work, "fonts"))
    brand = json.load(open(os.path.join(HERE, "brand", "brand.json")))
    for src, dst in (("icon_nocursor.png", "brand_icon.png"), ("cursor.png", "brand_cursor.png"), ("word.png", "brand_word.png")): shutil.copy(os.path.join(HERE, "brand", src), os.path.join(work, dst))
    js = open(os.path.join(HERE, "outro.js")).read(); open(os.path.join(work, "scenes_custom.js"), "w").write("const BRAND = " + json.dumps(brand) + ";\n" + js)
    st = json.load(open(os.path.join(work, "style.json"))); st["caption"] = dict(st.get("caption", {}), mode="off"); json.dump(st, open(os.path.join(work, "style.json"), "w"))
    frames = int(round(secs * 30))
    tl = {"title": "FredsDesk outro", "fps": 30, "W": 1080, "H": 1920, "duration": secs, "frames": frames, "seed": 7, "music": {},
          "scenes": [{"i": 0, "type": "outro", "act": "payoff", "start": 0.0, "end": secs, "bright": False, "params": {}, "keys": [], "lines": [], "transition": "none"}],
          "hits": [{"t": 1.55, "s": 0.06, "impact": 0}, {"t": 2.30, "s": 0.04, "impact": 0}]}
    json.dump(tl, open(os.path.join(work, "timeline.json"), "w"))
    if "--preview" in a:
        r = subprocess.run(["node", os.path.join(KIT, "render.js"), work, "preview", opt("--preview")], capture_output=True, text=True); print(r.stdout[-400:], r.stderr[-800:]); return
    r = subprocess.run(["node", os.path.join(KIT, "render.js"), work, "full", "--workers", "2"], capture_output=True, text=True); print(r.stdout[-300:]);
    if r.returncode: print(r.stderr[-1500:]); sys.exit(1)
    wav = os.path.join(out, "outro.wav"); sf.write(wav, sfx(secs, mood), SR, subtype="PCM_24")
    mp4 = os.path.join(out, "outro.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", os.path.join(work, "frames", "%05d.jpg"), "-i", wav, "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", mp4], check=True)
    print("OUTRO", mp4)


if __name__ == "__main__":
    main()
