"""Offline narration with Kokoro (Apache-2.0) -> voice.wav (48 kHz mono) + voice.json (word times).

    python3 voice.py script.json WORK

script.json fields used: voice (am_michael | am_fenrir | af_heart | ...), say {"AI": "A I"},
lead (s, default .45), end_tail (s, default 2.2), max_seconds (optional),
scenes[].lines ("It will *test* you."), scenes[].speed (0.8-1.15), scenes[].tail (s).
Per-line synthesis is cached in WORK/cache/, so re-runs after small script edits are fast.
"""
import hashlib, json, os, re, sys
import numpy as np, soundfile as sf
from scipy import signal

SR = 48000
CACHE = os.environ.get("VIDEO_KIT_CACHE", os.path.expanduser("~/.cache/video-kit"))
PAUSE = {",": .16, ";": .2, ":": .2, ".": .30, "!": .30, "?": .32, "-": .12}
_K = None


def kokoro():
    global _K
    if _K is None:
        from kokoro_onnx import Kokoro
        m = os.path.join(CACHE, "models")
        _K = Kokoro(os.path.join(m, "kokoro-v1.0.int8.onnx"), os.path.join(m, "voices-v1.0.bin"))
    return _K


def clean(line): return re.sub(r"\*", "", line).strip()


def spoken_text(line, say):
    t = clean(line)
    for k, v in (say or {}).items():
        t = re.sub(rf"(?<![A-Za-z]){re.escape(k)}(?![A-Za-z])", v, t)
    return t


def trim(x, db=-42, pad=.02):
    if not len(x): return x
    env = np.abs(x); thr = env.max() * 10 ** (db / 20)
    idx = np.where(env > thr)[0]
    if not len(idx): return x[:0]
    a = max(0, idx[0] - int(pad * SR)); b = min(len(x), idx[-1] + int(pad * SR)); return x[a:b]


def synth(text, voice, speed, cache_dir):
    key = hashlib.sha256(json.dumps([text, voice, round(speed, 3)]).encode()).hexdigest()[:20]
    p = os.path.join(cache_dir, key + ".wav")
    if os.path.exists(p): return sf.read(p, dtype="float32")[0]
    samples, sr = kokoro().create(text, voice=voice, speed=float(speed), lang="en-us")
    x = np.asarray(samples, dtype=np.float32)
    if sr != SR:
        g = np.gcd(SR, sr); x = signal.resample_poly(x, SR // g, sr // g).astype(np.float32)
    x = trim(x); sf.write(p, x, SR); return x


def word_times(line, start, dur, audio):
    """Spread words over the voiced span by syllable-ish weight, nudged toward detected pauses."""
    toks = clean(line).split()
    # keyword flags aligned with clean tokens (a *multi word* keyword spans several tokens)
    raw = line.split(); kflags = []
    inside = False
    for w in raw:
        k = inside or w.startswith("*")
        if w.startswith("*"): inside = True
        if w.rstrip(".,!?;:\"'").endswith("*"): inside = False
        kflags.append(k)
    def weight(w):
        core = re.sub(r"[^A-Za-z0-9]", "", w)
        return max(1.0, len(core) * .9 + 1.2) + (2.2 if re.search(r"[.,!?;:]$", w) else 0)
    ws = np.array([weight(w) for w in toks]); cum = np.concatenate([[0], np.cumsum(ws)]) / ws.sum()
    if os.environ.get("VIDEO_KIT_EXACT", "1") == "1":
        try:
            import align
            return align.exact_words(toks, kflags, start, dur, audio, list(ws), SR)
        except Exception as ex:
            print(f"[voice] exact timing unavailable ({type(ex).__name__}: {ex}); using estimate", file=sys.stderr)
    out = []
    for i, w in enumerate(toks):
        s = start + cum[i] * dur; e = start + cum[i + 1] * dur
        if re.search(r"[.,!?;:]$", w): e -= min(.18, (e - s) * .35)
        out.append({"w": w, "k": 1 if kflags[i] else 0, "s": round(s, 3), "e": round(max(e, s + .06), 3)})
    return out


def build(script, work):
    cache_dir = os.path.join(work, "cache"); os.makedirs(cache_dir, exist_ok=True)
    voice = script.get("voice", "am_michael"); say = script.get("say", {})
    lead = script.get("lead", .1 if script.get("hook") else .45); end_tail = script.get("end_tail", 2.2)
    scenes = script["scenes"]; last = len(scenes) - 1

    def render(speed_k=1.0, tail_k=1.0):
        segs, meta, t = [], [], lead
        for si, sc in enumerate(scenes):
            sp = min(1.25, sc.get("speed", .95) * speed_k); lines_meta = []
            for li, line in enumerate(sc["lines"]):
                x = synth(spoken_text(line, say), voice, sp, cache_dir) * sc.get("gain", 1.0)
                d = len(x) / SR
                segs.append((t, x)); lines_meta.append({"text": clean(line), "raw": line, "s": round(t, 3), "e": round(t + d, 3),
                                                        "words": word_times(line, t, d, x)})
                t += d
                p = PAUSE.get(clean(line)[-1:], .28)
                if li < len(sc["lines"]) - 1: t += p
            tail = sc.get("tail", .6) * tail_k
            meta.append({"lines": lines_meta, "voice_end": round(t, 3)})
            t += end_tail if si == last else max(.25, tail)
        return segs, meta, t

    segs, meta, total = render()
    mx = script.get("max_seconds")
    if mx and total > mx:   # shorten tails first, then speak faster (max +15%)
        segs, meta, total = render(1.0, .5)
        k = 1.0
        while total > mx and k < 1.15:
            k += .05; segs, meta, total = render(k, .5)
        if total > mx: print(f"[voice] still {total:.1f}s > max {mx}s: shorten the script", file=sys.stderr)
    out = np.zeros(int(total * SR) + 1, np.float32)
    for t, x in segs:
        i = int(t * SR); out[i:i + len(x)] += x
    pk = np.abs(out).max() or 1; out = out / pk * 10 ** (-3 / 20)
    sf.write(os.path.join(work, "voice.wav"), out, SR, subtype="FLOAT")
    info = {"duration": round(total, 3), "voice": voice, "scenes": meta}
    try:
        import align; info["align"] = align.STATS
    except Exception: pass
    json.dump(info, open(os.path.join(work, "voice.json"), "w"), indent=1)
    return info


if __name__ == "__main__":
    s = json.load(open(sys.argv[1])); w = sys.argv[2]; os.makedirs(w, exist_ok=True)
    import time; t0 = time.time(); info = build(s, w)
    print(f"voice: {info['duration']:.2f}s audio in {time.time() - t0:.1f}s")
