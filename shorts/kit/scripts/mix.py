"""Mix & master: voice + music stems + SFX -> WORK/mix.wav at -14 LUFS, true peak <= -1 dBTP.

    python3 mix.py WORK [--music-db -20]

- Look-ahead ducking from the finished voice track; stem-aware depth (pads/keys full, drums half,
  bass light), relaxed for 150-300 ms on big keyword hits, near-silence before the turn.
- 2 kHz presence carve on mid stems while the voice talks.
- Master: glue + tanh soft clip + 4x-oversampled peak limit, then TWO-PASS ffmpeg loudnorm (keeps punch).
"""
import json, os, subprocess, sys
import numpy as np, soundfile as sf
from scipy import signal

SR = 48000


def load(p, n):
    if not os.path.exists(p): return None
    a, sr = sf.read(p, always_2d=True, dtype="float32"); a = a.T
    if a.shape[0] == 1: a = np.vstack([a, a])
    if sr != SR: a = signal.resample_poly(a, SR, sr, axis=1)
    out = np.zeros((2, n), np.float32); m = min(n, a.shape[1]); out[:, :m] = a[:, :m]; return out


def rms_db(x): return 10 * np.log10(np.mean(x ** 2) + 1e-12)


def duck_env(voice, look=.15, att=.05, rel=.4, hold=.35, cr=1000):
    """0..1 speech envelope, shifted EARLY by `look` so the duck starts before the first word."""
    hop = SR // cr; v = voice[:len(voice) // hop * hop].reshape(-1, hop)
    db = 10 * np.log10((v ** 2).mean(axis=1) + 1e-12); speech = (db > db.max() - 30).astype(float)
    speech = np.convolve(speech, np.ones(int(hold * cr)))[:len(speech)] > 0
    a, r = np.exp(-1 / (att * cr)), np.exp(-1 / (rel * cr)); env = np.empty(len(speech)); e = 0.
    for i, s in enumerate(speech): k = a if s > e else r; e = k * e + (1 - k) * s; env[i] = e
    sh = int(look * cr); env = np.concatenate([env[sh:], np.full(sh, env[-1])])
    return np.interp(np.arange(len(voice)) / hop, np.arange(len(env)), env)


def peaking(x, f0, gain_db, q=1.0):
    A = 10 ** (gain_db / 40); w = 2 * np.pi * f0 / SR; al = np.sin(w) / (2 * q)
    b = [1 + al * A, -2 * np.cos(w), 1 - al * A]; a = [1 + al / A, -2 * np.cos(w), 1 - al / A]
    return signal.lfilter(b, a, x, axis=-1)


def build(work, music_db=-20.0):
    tl = json.load(open(os.path.join(work, "timeline.json"))); n = int(tl["duration"] * SR)
    voice = load(os.path.join(work, "voice.wav"), n); vmono = voice.mean(axis=0)
    v_ref = rms_db(vmono[np.abs(vmono) > 1e-3]) if np.any(np.abs(vmono) > 1e-3) else -20
    env = duck_env(vmono)
    # relax the duck around big hits so they poke through; silence before the turn
    t = np.arange(n) / SR; relax = np.zeros(n); pre = np.ones(n)
    for s in tl["scenes"]:
        for k in s["keys"]:
            if k["str"] >= 1.0: relax = np.maximum(relax, np.exp(-((t - k["s"] - .1) / .12) ** 2))
        if s["act"] == "turn" and s["keys"]:
            k0 = s["keys"][0]["s"]; pre *= 1 - .9 * np.clip(1 - np.abs(t - (k0 - .22)) / .3, 0, 1) * (t < k0)
    depth = {"pad": 10, "keys": 10, "bass": 3, "drums": 5, "sting": 2}
    music = np.zeros((2, n), np.float32); have = False
    for stem, d in depth.items():
        a = load(os.path.join(work, f"music_{stem}.wav"), n)
        if a is None: continue
        have = True; e = env * (1 - .7 * relax)
        if stem in ("pad", "keys"):   # presence carve where the voice lives
            carved = peaking(a, 2000, -4.5, 1.0); a = a * (1 - e) + carved * e
        music += (a * 10 ** (-d * e / 20) * pre).astype(np.float32)
    if have:
        gaps = music[:, env < .1] if np.any(env < .1) else music
        music *= 10 ** ((v_ref + music_db + 6 - rms_db(gaps.mean(axis=0))) / 20)   # gaps ~14 dB under voice, talk ~24 dB under
    sfx = load(os.path.join(work, "sfx.wav"), n)
    if sfx is not None:
        pk = np.percentile(np.abs(sfx[np.abs(sfx) > 1e-4]), 99.9) if np.any(np.abs(sfx) > 1e-4) else 1
        sfx = sfx / (pk or 1) * 10 ** ((v_ref + 12) / 20) * .85
        sfx *= 10 ** (-3 * env / 20)                                                   # SFX duck 0-3 dB
    mix = np.stack([vmono, vmono]) + music + (sfx if sfx is not None else 0)
    # master: glue + soft clip + oversampled peak limit
    mix = mix / (np.percentile(np.abs(mix), 99.95) or 1) * .7
    mix = np.tanh(mix * 1.2) / np.tanh(1.2)
    up = signal.resample_poly(mix, 4, 1, axis=1); tp = np.abs(up).max()
    mix = mix / tp * 10 ** (-1.5 / 20)
    pre_p = os.path.join(work, "mix_pre.wav"); sf.write(pre_p, mix.T.astype(np.float32), SR, subtype="FLOAT")
    # two-pass loudnorm to -14 LUFS / -1 dBTP
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", pre_p, "-af", "loudnorm=I=-14:TP=-1:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    m = json.loads(r[r.rindex("{"): r.rindex("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true:print_format=summary")
    out = os.path.join(work, "mix.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", pre_p, "-af", af, "-ar", str(SR), "-c:a", "pcm_s24le", out], check=True)
    return out


if __name__ == "__main__":
    a = sys.argv[2:]; mdb = float(a[a.index("--music-db") + 1]) if "--music-db" in a else -20.0
    import time; t0 = time.time(); p = build(sys.argv[1], mdb); print(f"mix: {p} in {time.time() - t0:.1f}s")
