"""Synthesized music bed + sound effects + narration, mixed with voice-activated ducking.
Usage: python3 audio.py <buildDir>   (needs voice.wav, events.json, timeline.json) -> mix.wav"""
import json, sys, os, wave
import numpy as np
from scipy.signal import butter, sosfilt, resample_poly

SR = 44100
d = sys.argv[1]
MUSIC = '--music' in sys.argv      # background music is OFF by default (add your own sound in TikTok); sound effects always stay
tl = json.load(open(os.path.join(d, 'timeline.json'))); events = json.load(open(os.path.join(d, 'events.json')))
DUR = tl['duration']; N = int(SR * DUR)
rng = np.random.default_rng(11)
M = np.zeros((N, 2)); X = np.zeros((N, 2))      # music, sfx buses

def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], btype='band', fs=SR, output='sos'), x)
def lp(x, f, o=2): return sosfilt(butter(o, f, btype='low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, btype='high', fs=SR, output='sos'), x)
def add(bus, sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N or i < 0: return
    s = sig[: N - i]
    bus[i:i + len(s), 0] += s * gain * (1 - max(0, pan)); bus[i:i + len(s), 1] += s * gain * (1 + min(0, pan))
def tt(sec): return np.arange(int(sec * SR)) / SR
def midi(n): return 440 * 2 ** ((n - 69) / 12)

# ---------------- music bed: Am - F - C - G, soft pad + pluck arpeggio + bass ----------------
BPM = 92; beat = 60 / BPM; bar = 4 * beat
prog = [([57, 60, 64], 45), ([53, 57, 60], 41), ([48, 52, 55], 36), ([55, 59, 62], 43)]   # (triad, bass)
def pad(notes, dur):
    t = tt(dur + .6); s = np.zeros(len(t))
    for n in notes:
        for det in (-.4, .4): s += np.sin(2 * np.pi * (midi(n) + det) * t) + .3 * np.sin(2 * np.pi * 2 * (midi(n) + det) * t)
    e = np.minimum(1, t / .5) * np.minimum(1, (dur + .6 - t) / .6)
    return lp(s * e, 1500) / 8
def pluck(f, dur=.5):
    t = tt(dur); return (np.sin(2 * np.pi * f * t) + .35 * np.sin(2 * np.pi * 2 * f * t) + .15 * np.sin(2 * np.pi * 3 * f * t)) * np.exp(-t / .16) * np.minimum(1, t / .003)
def bass(f):
    t = tt(.8); return np.sin(2 * np.pi * f * t) * np.exp(-t / .35) * np.minimum(1, t / .01)
nb = int(DUR / bar) + 2 if MUSIC else 0
pat = [0, 1, 2, 1, 2, 1, 0, 1]
for b in range(nb):
    triad, bn = prog[b % 4]; t0 = b * bar
    add(M, pad(triad, bar), t0, .55, 0)
    add(M, bass(midi(bn)), t0, .9); add(M, bass(midi(bn)), t0 + 2 * beat, .6)
    for k in range(8):
        n = triad[pat[k]] + (12 if k % 4 == 3 else 24)
        add(M, pluck(midi(n)), t0 + k * beat / 2, .16, np.sin(b * 8 + k) * .5)
    for k in range(8):
        add(M, hp(rng.standard_normal(int(.03 * SR)), 6000) * np.exp(-tt(.03) / .008), t0 + k * beat / 2 + (beat / 4 if False else 0), .012 if k % 2 else .006)
M *= np.clip(np.minimum(1, np.arange(N) / SR / 1.2) * np.minimum(1, (DUR - np.arange(N) / SR) / 1.6), 0, 1)[:, None]

# ---------------- sound effects ----------------
def whoosh(dur=.4, lo=300, hi=4500, up=False):
    t = tt(dur); w = bp(rng.standard_normal(len(t)), lo, hi); e = np.sin(np.pi * (t / dur) ** (.6 if up else 1.4)) ** 2; return w * e
def pop(f0=520, f1=880):
    t = tt(.14); fr = f0 + (f1 - f0) * np.minimum(1, t / .05); return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t / .045) * np.minimum(1, t / .002)
def key():
    t = tt(.03); return bp(rng.standard_normal(len(t)), 1800, 5000) * np.exp(-t / .006)
def click():
    t = tt(.09); a = bp(rng.standard_normal(len(t)), 1000, 6000) * np.exp(-t / .006); return a + .6 * np.sin(2 * np.pi * 900 * t) * np.exp(-t / .012)
def thud():
    t = tt(.3); return np.sin(2 * np.pi * np.cumsum(60 + 120 * np.exp(-t * 30)) / SR) * np.exp(-t / .09) + .3 * bp(rng.standard_normal(len(t)), 400, 2500) * np.exp(-t / .015)
def draw():
    t = tt(1.1); fr = 380 + 1500 * (t / 1.1) ** 1.6; s = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.sin(np.pi * (t / 1.1) ** .8) ** 2
    return .5 * s + .25 * np.sin(2 * np.pi * np.cumsum(fr * 1.5) / SR) * np.sin(np.pi * (t / 1.1)) ** 2
def glitch():
    t = tt(.28); n = rng.standard_normal(len(t)); n = np.round(n * 3) / 3; return bp(n, 700, 7000) * np.exp(-t / .1) * (np.sign(np.sin(2 * np.pi * 38 * t)) * .5 + .5)
def split():
    t = tt(.3); return hp(rng.standard_normal(len(t)), 1500) * np.exp(-t / .05) * .8 + np.sin(2 * np.pi * 180 * t) * np.exp(-t / .08) * .5
def flip():
    t = tt(.07); return np.sin(2 * np.pi * (1500 + 800 * t / .07) * t) * np.exp(-t / .02)
def tick(n=0):
    t = tt(.12); f = 900 * 2 ** (n / 6); return (np.sin(2 * np.pi * f * t) + .4 * np.sin(2 * np.pi * 2.5 * f * t)) * np.exp(-t / .03)
def ding():
    t = tt(1.0); return (np.sin(2 * np.pi * 1568 * t) + .5 * np.sin(2 * np.pi * 2093 * t) + .25 * np.sin(2 * np.pi * 3136 * t)) * np.exp(-t / .22) * np.minimum(1, t / .002)

tickn = 0
for e in sorted(events, key=lambda e: e['t']):
    k, t = e['kind'], e['t']
    if k == 'whoosh': add(X, whoosh(.45, 250, 3800), max(0, t - .12), .5)
    elif k == 'swoosh': add(X, whoosh(.5, 400, 6000, True), max(0, t - .1), .45)
    elif k == 'whoosh2': add(X, whoosh(.25, 600, 5000), max(0, t - .05), .3)
    elif k == 'pop': add(X, pop(), t, .55)
    elif k == 'key': add(X, key(), t, .35 + .15 * rng.random(), rng.uniform(-.2, .2))
    elif k == 'click': add(X, click(), t, .7)
    elif k == 'brick': add(X, thud(), t, .75)
    elif k == 'draw': add(X, draw(), t, .45)
    elif k == 'glitch': add(X, glitch(), t, .6)
    elif k == 'split': add(X, split(), t, .6)
    elif k == 'flip': add(X, flip(), t, .45)
    elif k == 'tick': add(X, tick(tickn % 3), t, .6); tickn += 1
    elif k == 'ding': add(X, ding(), t, .4)

# ---------------- narration + ducking ----------------
import soundfile as sf
v, vsr = sf.read(os.path.join(d, 'voice.wav')); v = v if v.ndim == 1 else v[:, 0]
v = resample_poly(v, SR // 300, vsr // 300) if vsr != SR else v
v = np.pad(v, (0, max(0, N - len(v))))[:N]
v = lp(hp(v, 70), 14000)            # gentle clean-up
v = np.tanh(v * 1.6 / max(1e-6, np.abs(v).max())) / np.tanh(1.6)       # soft-compress dynamics
v *= .9 / max(1e-6, np.abs(v).max())
env = np.abs(v); k = int(.12 * SR); env = np.convolve(env, np.ones(k) / k, 'same'); env = np.clip(env / (env.max() * .35 + 1e-9), 0, 1)
duck = 1 - .6 * lp(env, 6, 1)       # music + sfx dip while the voice talks
duck = np.clip(duck, .3, 1)
mix = np.zeros((N, 2))
mix += M * duck[:, None] * .55
mix += X * (.55 + .45 * duck[:, None]) * .5
mix[:, 0] += v * .95; mix[:, 1] += v * .95
mix = np.tanh(mix * 1.2) / np.tanh(1.2)
mix *= .93 / np.abs(mix).max()
pcm = (np.clip(mix, -1, 1) * 32767).astype('<i2')
with wave.open(os.path.join(d, 'mix.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print(f'mix.wav {DUR:.1f}s, {len(events)} sfx events')
