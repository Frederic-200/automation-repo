#!/usr/bin/env python3
"""FredsDesk Loops - audio built entirely in code, perfectly loopable (no samples, no licences).

    python3 loops/audio.py DIR        (reads DIR/cfg.json + DIR/events.json -> DIR/audio_music.wav, DIR/audio_sfx.wav)

Loop rules: every tone is snapped to a whole number of cycles per loop, noise is generated in the frequency domain (periodic by
construction) and every sound's tail wraps around the end back to the start, so the join is inaudible.
music version = pad + soft arpeggio + scene SFX      sfx version = scene SFX only (for TikTok, which adds its own music)
"""
import json, os, subprocess, sys, hashlib, re
import numpy as np, soundfile as sf
from scipy import signal

SR = 48000
TARGET_LUFS = -15.0

def rng_for(*key):
    return np.random.default_rng(int.from_bytes(hashlib.sha256(json.dumps(key).encode()).digest()[:8], "little"))

def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)

def add_wrap(buf, start, sig, pan=0.0):
    """add stereo-panned mono sig into buf[2, N] starting at sample `start`, wrapping past the end."""
    N = buf.shape[1]; gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    start %= N; n = len(sig); first = min(n, N - start)
    for ch, g in ((0, gl), (1, gr)):
        buf[ch, start:start + first] += sig[:first] * g
        if first < n: buf[ch, :n - first] += sig[first:] * g

def loop_freq(f, D):  # nearest frequency with a whole number of cycles per loop
    return max(1, round(f * D)) / D

SCALES = {"major": [0, 2, 4, 7, 9], "minor": [0, 3, 5, 7, 10], "dorian": [0, 2, 3, 7, 9]}

def note(root, scale, idx, oct0=0):
    s = SCALES[scale]; return root + 12 * (idx // len(s) + oct0) + s[idx % len(s)]

def pluck(f, dur, bright=1.0, rng=None):
    t = np.arange(int(dur * SR)) / SR
    env = np.exp(-t * (7 + f / 220)) * (1 - np.exp(-t * 900))
    x = np.sin(2 * np.pi * f * t) + 0.35 * bright * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 18) + 0.12 * bright * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t * 30)
    return x * env

def click(f, vel, rng):
    dur = 0.16; t = np.arange(int(dur * SR)) / SR
    tone = np.sin(2 * np.pi * f * t) * np.exp(-t * 38) + 0.3 * np.sin(2 * np.pi * f * 2.01 * t) * np.exp(-t * 70)
    n = rng.standard_normal(len(t)); b, a = signal.butter(2, [1800 / (SR / 2), 7500 / (SR / 2)], "band")
    tick = signal.lfilter(b, a, n) * np.exp(-t * 420)
    return (tone * 0.55 + tick * 0.9) * vel * (1 - np.exp(-t * 3000))

def thud(f, vel, rng):
    dur = 0.38; t = np.arange(int(dur * SR)) / SR
    body = np.sin(2 * np.pi * (f * 0.5 * (1 + 0.6 * np.exp(-t * 28))) * t) * np.exp(-t * 11)
    tone = np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 14) * 0.45 + np.sin(2 * np.pi * f * 4.02 * t) * np.exp(-t * 40) * 0.16
    n = rng.standard_normal(len(t)); b, a = signal.butter(2, 900 / (SR / 2), "low")
    return (body * 0.8 + tone + signal.lfilter(b, a, n) * np.exp(-t * 90) * 0.3) * vel * (1 - np.exp(-t * 1800))

def chime(f, vel, rng):
    dur = 1.4; t = np.arange(int(dur * SR)) / SR
    x = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * d) for r, a, d in ((1, 1.0, 2.6), (2.76, 0.45, 4.2), (5.4, 0.2, 7.5), (8.9, 0.08, 11)))
    return x * 0.5 * vel * (1 - np.exp(-t * 1200))

def periodic_noise(N, lo, hi, rng):
    """band-limited noise that loops perfectly (random phases in the frequency domain)."""
    spec = np.zeros(N // 2 + 1, complex); fr = np.fft.rfftfreq(N, 1 / SR)
    m = (fr > lo) & (fr < hi); spec[m] = np.exp(1j * rng.uniform(0, 2 * np.pi, m.sum())) / np.sqrt(1 + fr[m] / 300)
    x = np.fft.irfft(spec, N); return x / (np.abs(x).max() + 1e-9)

def lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr); return float(m[-1]) if m else None

def main(d):
    cfg = json.load(open(os.path.join(d, "cfg.json"))); ev = json.load(open(os.path.join(d, "events.json")))
    D = ev["duration"]; N = int(D * SR); rng = rng_for("audio", cfg["date"], cfg["seed"])
    root = int(rng.integers(45, 53)); scale = str(rng.choice(list(SCALES)))
    # ---- SFX layer from scene events: each event kind has its own voice, thinned so it never turns into noise ----------
    VOICE = {"tick": (click, 0.06, 16), "thud": (thud, 0.11, 0), "ping": (None, 0.09, 12), "chime": (chime, 0.28, 24)}
    sfx = np.zeros((2, N)); last = {}
    for e in sorted(ev["events"], key=lambda e: e["t"]):
        fn, gap, oct0 = VOICE.get(e["kind"], VOICE["tick"])
        if e["t"] - last.get(e["kind"], -1.0) < gap: continue
        last[e["kind"]] = e["t"]; idx = int(e["pitch"] * 9) % 10
        f = mtof(note(root + 12, scale, idx + (4 if e["kind"] == "tick" else 0), 1 if e["kind"] in ("ping", "chime") else 0))
        v = e["vel"] * rng.uniform(0.8, 1.0)
        sig = pluck(f * 2, 0.9) * v * 0.5 if e["kind"] == "ping" else fn(f * (2 if e["kind"] == "chime" else 1), v, rng)
        add_wrap(sfx, int(e["t"] * SR), sig, pan=float(rng.uniform(-0.35, 0.35)))
    sfx *= 0.9

    # ---- music layer: pad + arpeggio ---------------------------------------------------------------------------------
    t = np.arange(N) / SR; pad = np.zeros((2, N))
    chord = [0, 4 if scale != "minor" else 3, 7, 12, 16 if scale != "minor" else 15]
    for k, off in enumerate(chord):
        for det, pan in ((-0.0, -0.5), (0.0, 0.5)):
            f = loop_freq(mtof(root + off + 12 * (k > 2)) * (1 + (0.002 if pan > 0 else -0.002)), D)
            lfo = 0.6 + 0.4 * np.sin(2 * np.pi * (1 + k % 2) * t / D + k)
            v = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)) * lfo * 0.05
            add_wrap(pad, 0, v, pan)
    add_wrap(pad, 0, np.sin(2 * np.pi * loop_freq(mtof(root - 12), D) * t) * 0.16)
    air = periodic_noise(N, 300, 5000, rng) * 0.012 * (0.7 + 0.3 * np.sin(2 * np.pi * t / D)); add_wrap(pad, 0, air)
    arp = np.zeros((2, N)); beats = 24; step = D / (beats * 2); patt = rng.integers(0, 8, size=16)
    for i in range(beats * 2):
        if i % 4 == 3 and rng.random() < 0.5: continue
        f = mtof(note(root + 12, scale, int(patt[i % 16]) + 5)); add_wrap(arp, int(i * step * SR), pluck(f, 1.1) * 0.05 * (1 if i % 2 == 0 else 0.6), pan=0.4 * np.sin(i))
    music = pad + arp * 1.0

    def softclip(y):  # transparent below 0.55, gentle limiter above, hard ceiling 0.84 (about -1.5 dBFS: leaves room for AAC / platform re-encodes)
        a = np.abs(y); return np.where(a < 0.55, y, np.sign(y) * (0.55 + 0.29 * np.tanh((a - 0.55) / 0.29)))

    def finish(x, name):
        x = x / (np.abs(x).max() + 1e-9) * 0.5; path = os.path.join(d, name); sf.write(path, x.T.astype(np.float32), SR)
        for _ in range(5):                        # measure -> adjust until within 0.7 LU of target
            L = lufs(path)
            if L is None or abs(L - TARGET_LUFS) < 0.7: break
            x = softclip(x * 10 ** ((TARGET_LUFS - L) / 20)); sf.write(path, x.T.astype(np.float32), SR)
        x = softclip(x); sf.write(path, x.T.astype(np.float32), SR)
        print(f"{name}: {lufs(path):.1f} LUFS, peak {np.abs(x).max():.2f}")
    finish(music + sfx, "audio_music.wav"); finish(sfx, "audio_sfx.wav")

if __name__ == "__main__":
    main(sys.argv[1])
