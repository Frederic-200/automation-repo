"""Layered, deterministic sound effects keyed to the timeline -> WORK/sfx.wav (48 kHz stereo).

    python3 sfx.py WORK            (reads timeline.json + style.json)

Kits (style.sfx.kit): cinematic | glitch | soft | click | chip. Events:
  keyword  -> hit stack scaled by strength (big hits >= 1 get sub + debris + reverb)
  scene cut-> whoosh whose apex lands on the cut
  impact   -> riser ending 0.12 s before it (+ braam on cinematic)
  turn     -> reversed reverb swell ending exactly on the turn keyword
Every generator returns (stereo[2, n], anchor_sample); events are placed at time*SR - anchor.
"""
import hashlib, json, os, sys
import numpy as np, soundfile as sf
from scipy import signal

os.environ.setdefault("OMP_NUM_THREADS", "1")
SR = 48000


def rng_for(*key):  # stable across processes (never Python hash())
    d = hashlib.sha256(json.dumps(key).encode()).digest(); return np.random.default_rng(int.from_bytes(d[:8], "little"))


def sat(x, drive):  # 4x-oversampled tanh: harmonics make low end audible on phones
    up = signal.resample_poly(x, 4, 1); return signal.resample_poly(np.tanh(drive * up) / np.tanh(drive), 1, 4)[:len(x)]


def env_t(dur): return np.arange(int(dur * SR)) / SR


def drop(f0, f1, dur, tau):  # exponential pitch sweep with integrated phase
    t = env_t(dur); return np.sin(2 * np.pi * np.cumsum(f0 * (f1 / f0) ** (t / dur)) / SR) * np.exp(-t / tau)


def noise(rng, dur, tau, band):
    n = rng.standard_normal(int(dur * SR)) * np.exp(-np.arange(int(dur * SR)) / (tau * SR))
    kind = "high" if np.isscalar(band) else "band"
    return signal.sosfilt(signal.butter(4, band, kind, fs=SR, output="sos"), n)


def synth_ir(rng, rt60=2.2, dur=2.4):  # decorrelated L/R, darker tail, 20 ms pre-delay
    t = env_t(dur); ir = rng.standard_normal((2, t.size)) * np.exp(-6.91 * t / rt60)
    dark = signal.sosfilt(signal.butter(2, 5000, fs=SR, output="sos"), ir); ir = ir * (1 - t / dur) + dark * (t / dur)
    return np.pad(ir, ((0, 0), (int(.02 * SR), 0))) / np.sqrt((ir ** 2).sum())


def reverb(mono, rng, mix=.5, rt60=2.2):
    ir = synth_ir(rng, rt60); return mix * np.stack([signal.oaconvolve(mono, ch)[:len(mono)] for ch in ir])


def stereo(m): return np.stack([m, m])


def norm(x, db=-6): pk = np.abs(x).max() or 1; return x / pk * 10 ** (db / 20)


def pad_to(x, n): return x[..., :n] if x.shape[-1] >= n else np.pad(x, [(0, 0)] * (x.ndim - 1) + [(0, n - x.shape[-1])])


# ------------------------------------------------------------------ generators
def hit_cinematic(key, s, n_sec=3.2):
    r1, r2, r3 = rng_for(key, "hit").spawn(3); n = int(n_sec * SR); out = np.zeros((2, n))
    click = noise(r1, .03, .012, 3000); body = sat(drop(150, 48, .45, .12 + .05 * s), 4.0)
    sub = drop(55, 30, 1.5, .6) if s >= .95 else np.zeros(1)
    debris = noise(r2, .8, .12 + .08 * s, [1000, 6000]) if s >= .9 else np.zeros(1)
    for xx, g in ((click, .5), (body, .9), (sub, .8 * min(1.5, s))):
        out[:, :xx.size] += g * xx[:n]
    d = debris[:n - 240]; out[0, :d.size] += .25 * d; out[1, 240:240 + d.size] += .25 * d  # 5 ms Haas
    send = np.zeros(n); send[:body.size] += body; send[:min(n, debris.size)] += .3 * debris[:n]
    out += reverb(send, r3, .45 * min(1.3, s))
    out = np.stack([sat(ch, 1.5) for ch in out]); return norm(out, -6 + 6 * (min(s, 1.5) - 1.5) / 1.5 * .8), 0


def hit_glitch(key, s):
    base, a = hit_cinematic(key, min(s, 1.2), 2.0); rng = rng_for(key, "gl")
    n = base.shape[1]; out = base.copy()
    sl = int(.045 * SR); seg = base[:, :sl]  # stutter: shrinking repeats of the transient
    pos = int(.0 * SR)
    for k, ln in enumerate((sl, int(sl * .7), int(sl * .5), int(sl * .35))):
        pos += ln
        if pos + ln < n: out[:, pos:pos + ln] += seg[:, :ln] * (.6 - .1 * k)
    crush = np.round(out * 12) / 12  # bit-crush layer
    dec = np.repeat(crush[:, ::6], 6, axis=1)[:, :n]
    zap = np.sign(np.sin(2 * np.pi * np.cumsum(np.geomspace(1800, 120, int(.25 * SR))) / SR)) * np.exp(-env_t(.25) / .08) * .35
    out[:, :zap.size] += zap
    return norm(.7 * out + .3 * dec, -6), a


def fm_bell(f, dur, ratio=1.4, idx=3.0, tau=.9):
    t = env_t(dur); mod = idx * np.exp(-t / (tau * .35)) * np.sin(2 * np.pi * f * ratio * t)
    return np.sin(2 * np.pi * f * t + mod) * np.exp(-t / tau)


def hit_soft(key, s):
    rng = rng_for(key, "soft"); f = [523.25, 659.25, 783.99, 1046.5][int(rng.integers(4))]
    bell = fm_bell(f, 2.0, 1.4, 2.5) * .6; b2 = fm_bell(f * 2, 1.4, 3.5, 1.5, .5); bell[:b2.size] += b2 * .25
    thump = sat(drop(110, 55, .3, .09), 2.0) * .5 * s
    m = np.zeros(int(2.2 * SR)); m[:bell.size] += bell; m[:thump.size] += thump
    out = stereo(m) * .7 + reverb(m, rng, .55, 2.6); return norm(out, -8), 0


def modal(f0, ratios, dur, q=60, rng=None):
    n = int(dur * SR); exc = np.zeros(n); exc[:int(.003 * SR)] = (rng.standard_normal(int(.003 * SR)) if rng is not None else 1)
    out = np.zeros(n)
    for k, r in enumerate(ratios):
        f = f0 * r
        if f > SR / 2.2: break
        b, a = signal.iirpeak(f, q * (1 + k * .3), fs=SR); out += signal.lfilter(b, a, exc) / (1 + k)
    return out


def hit_click(key, s):
    rng = rng_for(key, "click"); wood = modal(880 + 220 * rng.random(), [1, 2.76, 5.40, 8.93], .4, 40, rng)
    tick = noise(rng, .01, .003, 4000) * .6; thump = sat(drop(140, 60, .2, .05), 2.5) * .7 * s
    m = np.zeros(int(1.0 * SR)); m[:wood.size] += norm(wood, 0); m[:tick.size] += tick; m[:thump.size] += thump
    out = stereo(m) + reverb(m, rng, .2, 1.0); return norm(out, -7), 0


def hit_chip(key, s):
    rng = rng_for(key, "chip"); notes = [523.25, 659.25, 783.99, 1046.5]; seg = int(.05 * SR); m = np.zeros(seg * 6)
    for k in range(4 if s < 1 else 6):
        f = notes[k % 4] * (2 if k >= 4 else 1); t = np.arange(seg) / SR
        m[k * seg:(k + 1) * seg] = np.sign(np.sin(2 * np.pi * f * t)) * .3 * np.exp(-t / .08)
    nz = np.sign(rng.standard_normal(int(.12 * SR))) * np.exp(-env_t(.12) / .03) * .25 * s; m[:nz.size] += nz
    return norm(stereo(m), -8), 0


def whoosh(key, dur=.7, apex=.68, gain=1.0):
    rng = rng_for(key, "wh"); n = int(dur * SR); src = np.cumsum(rng.standard_normal(n)); src -= signal.savgol_filter(src, 2001, 2)  # brown-ish
    t = env_t(dur); amp = np.exp(-((t - dur * apex) / (dur * .22)) ** 2)
    # time-varying band-pass via overlap-add blocks; center follows the motion
    hop = 1024; win = np.hanning(2 * hop); out = np.zeros(n + 2 * hop); padded = np.pad(src, (0, 2 * hop))
    for i in range(0, n, hop):
        c = 250 + 2600 * np.exp(-((i / SR - dur * apex) / (dur * .25)) ** 2)
        sos = signal.butter(2, [c * .6, min(c * 1.6, SR / 2.2)], "band", fs=SR, output="sos")
        out[i:i + 2 * hop] += signal.sosfilt(sos, padded[i:i + 2 * hop]) * win
    m = out[:n] * amp; pan = np.clip((t - dur * apex) / (dur * .5), -1, 1)  # equal-power pan as it passes
    L, Rr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    return norm(np.stack([m * L, m * Rr]), -12 + 6 * (gain - 1)), int(dur * apex * SR)


def riser(key, dur=1.6):
    rng = rng_for(key, "ris"); t = env_t(dur); n = t.size
    f = 110 * 2 ** (1.5 * (t / dur) ** 2); saw = np.zeros(n)
    for v in range(6):
        det = 1 + (v - 2.5) * .006; ph = np.cumsum(f * det) / SR; saw += 2 * (ph % 1) - 1
    nz = rng.standard_normal(n) * .5; sig = saw / 6 + nz
    hop = 1024; out = np.zeros(n + 2 * hop); padded = np.pad(sig, (0, 2 * hop)); win = np.hanning(2 * hop)
    for i in range(0, n, hop):
        c = 300 * (40 ** (i / n)); out[i:i + 2 * hop] += signal.sosfilt(signal.butter(2, min(c, 16000), fs=SR, output="sos"), padded[i:i + 2 * hop]) * win
    trem = .7 + .3 * np.sin(2 * np.pi * np.cumsum(4 + 18 * (t / dur) ** 2) / SR)
    m = out[:n] * (t / dur) ** 1.6 * trem
    return norm(np.stack([m, np.roll(m, 180)]), -10), n - 1


def braam(key, dur=2.6):
    t = env_t(dur); f = 65.4 * (1 - .03 * t / dur); m = np.zeros_like(t)
    for o, g in ((1, 1), (2, .6), (4, .3), (.5, .7)):
        ph = np.cumsum(f * o) / SR; m += g * (2 * (ph % 1) - 1)
    m = signal.sosfilt(signal.butter(2, 900, fs=SR, output="sos"), m) * np.minimum(1, t / .04) * np.exp(-t / 1.1)
    m = sat(m, 3.0); return norm(stereo(m) + reverb(m, rng_for(key, "br"), .4), -8), 0


def rev_swell(key, dur=1.0):
    rng = rng_for(key, "rs"); m = fm_bell(392, .3, 1.4, 2.0, .2); nz = noise(rng, .15, .05, [800, 5000]); m[:nz.size] += nz * .4
    wet = reverb(np.pad(m, (0, int(dur * SR))), rng, 1.0, 2.0)[:, :int(dur * SR)]
    return norm(wet[:, ::-1].copy(), -12), int(dur * SR) - 1


HIT = {"cinematic": hit_cinematic, "glitch": hit_glitch, "soft": hit_soft, "click": hit_click, "chip": hit_chip}


def build(work):
    tl = json.load(open(os.path.join(work, "timeline.json"))); st = json.load(open(os.path.join(work, "style.json")))
    kit = st.get("sfx", {}).get("kit", "cinematic"); gain = st.get("sfx", {}).get("gain", 1.0)
    n = int((tl["duration"] + 1) * SR); bus = np.zeros((2, n)); events = []
    cache = {}

    def place(t, gen, g=1.0, label=""):
        a, anchor = gen
        i = int(round(t * SR)) - anchor; j0 = max(0, -i); i = max(0, i)
        seg = a[:, j0:j0 + (n - i)]; bus[:, i:i + seg.shape[1]] += g * seg; events.append([round(t, 3), label])

    vid = tl.get("title", "") + str(tl["seed"])
    for s in tl["scenes"]:
        if s["i"] > 0 and s.get("transition") != "none":
            place(s["start"], whoosh((vid, "cut", s["i"]), .7 if kit != "soft" else 1.0), .8 * gain, "whoosh")
        for j, k in enumerate(s["keys"]):
            strength = k["str"]; gen = HIT.get(kit, hit_cinematic)((vid, s["i"], j), strength)
            place(k["s"], gen, gain * (.55 + .35 * min(strength, 1.5)), f"hit:{k['w']}")
            if k.get("impact"):
                if k["s"] - s["start"] > .4 or s["i"] > 0:
                    place(k["s"] - .12, riser((vid, "riser")), .9 * gain, "riser")
                if kit in ("cinematic", "glitch"): place(k["s"], braam((vid, "braam")), .7 * gain, "braam")
        if s["act"] == "turn" and s["keys"]:
            place(s["keys"][0]["s"], rev_swell((vid, "swell", s["i"])), .7 * gain, "swell")
    # SFX bus: mono below 120 Hz, glue (2:1-ish soft knee via tanh), headroom
    lo = signal.sosfiltfilt(signal.butter(2, 120, fs=SR, output="sos"), bus, axis=1); mono_lo = lo.mean(axis=0)
    bus = bus - lo + np.stack([mono_lo, mono_lo])
    pk = np.abs(bus).max() or 1; bus = np.tanh(bus / pk * 1.3) / np.tanh(1.3) * 10 ** (-3 / 20)
    sf.write(os.path.join(work, "sfx.wav"), bus.T.astype(np.float32), SR, subtype="FLOAT")
    json.dump(events, open(os.path.join(work, "sfx.json"), "w"))
    return events


if __name__ == "__main__":
    import time; t0 = time.time(); ev = build(sys.argv[1])
    print(f"sfx: {len(ev)} events in {time.time() - t0:.1f}s")
