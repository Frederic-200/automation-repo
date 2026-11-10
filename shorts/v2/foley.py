"""v2 foley: sfx synthesized per visual event (no bells, no tonal hits) -> WORK/sfx.wav (48 kHz stereo) + sfx.json.

Events are derived from timeline.json (scene starts, scene kind, params) using the same timing the world draws with.
Every sound is randomized from a per-video seed (pitch, band, length, pan), and the same voicing is never used twice in a row.
Relative levels matter: mix.py scales the whole bus (style.sfx.level_db); slides are quiet, stamps medium, the finale thud is the peak.
"""
import json, os, sys
import numpy as np, soundfile as sf
from scipy import signal
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kit", "scripts"))
from sfx import SR, rng_for, sat, env_t, drop, noise, stereo, pad_to  # noqa: E402


def band(rng, dur, f0, f1, q=2.2, shape="bell", attack=.02):
    """band-passed noise whose centre sweeps f0 -> f1 (paper / ink / air movement)."""
    n = int(dur * SR); x = rng.standard_normal(n); t = np.arange(n) / n
    out = np.zeros(n); blocks = 24; edges = np.linspace(0, n, blocks + 1).astype(int)
    for b in range(blocks):
        c = f0 * (f1 / f0) ** ((edges[b] + edges[b + 1]) / 2 / n); bw = c / q
        sos = signal.butter(2, [max(60, c - bw / 2), min(SR / 2 - 100, c + bw / 2)], "band", fs=SR, output="sos")
        out[edges[b]:edges[b + 1]] = signal.sosfilt(sos, x)[edges[b]:edges[b + 1]]
    env = np.sin(np.pi * t) ** 1.5 if shape == "bell" else np.exp(-t * 4.5)
    a = int(attack * SR); env[:a] *= np.linspace(0, 1, a)
    return out * env / (np.abs(out * env).max() or 1)


PACKS = {   # world voicing: ranges the generators draw from (world A = dry/typographic, world B = paper)
    "a": {},
    "c": dict(line="stamp", slide=(450, 1000), tick=(1100, 2100), tick_tau=.012, stamp=(85, 125), stamp_slap=.55, swish=(150, 300, 1200, 2200), swish_q=(.8, 1.2)),
    "b": dict(slide=(700, 1500), slide_q=(.9, 1.4), tick=(650, 1300), tick_tau=.016, stamp=(110, 150), stamp_slap=.35, swish=(250, 500, 1800, 2800), swish_q=(.7, 1.0), rip=True),
}
PK = {}   # active pack (set in build)


def pan(m, p):
    l, r = np.cos((p + 1) * np.pi / 4), np.sin((p + 1) * np.pi / 4); return np.stack([m * l, m * r])


def slide(rng, g=1.0):   # paper / mask sliding: short airy scrape
    d = rng.uniform(.14, .26); f0 = rng.uniform(*PK.get('slide', (1400, 2600))); up = rng.random() < .5
    m = band(rng, d, f0, f0 * (rng.uniform(1.5, 2.2) if up else rng.uniform(.5, .7)), q=rng.uniform(*PK.get('slide_q', (1.6, 2.6)))) * .5 * g
    return pan(m, rng.uniform(-.35, .35)), 0


def ink(rng, g=1.0):   # underline / rule drawn: lower, longer, softer swipe
    d = rng.uniform(.22, .34); f0 = rng.uniform(500, 900)
    m = band(rng, d, f0, f0 * rng.uniform(2.2, 3.2), q=rng.uniform(1.2, 1.8), shape="bell", attack=.05) * .45 * g
    return pan(m, rng.uniform(-.2, .2)), 0


def tick(rng, g=1.0, f=None):   # ruler / bar tick: tiny dry click
    f = f or rng.uniform(*PK.get('tick', (1800, 3400))); t = env_t(.05); tau = PK.get('tick_tau', .006)
    m = (np.sin(2 * np.pi * f * t) * np.exp(-t / tau) + .5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / .003)) * .5
    m[:int(.002 * SR)] += rng.standard_normal(int(.002 * SR)) * .5
    return pan(m * g * .6, rng.uniform(-.3, .3)), 0


def stamp(rng, g=1.0):   # ink stamp: dull thump + paper slap, no pitch you could hum
    f0 = rng.uniform(*PK.get('stamp', (150, 210))); body = drop(f0, rng.uniform(48, 62), .22, rng.uniform(.06, .09)) * .8
    slap = noise(rng, .05, .012, [900, 4200]) * rng.uniform(.5, .8) * PK.get('stamp_slap', 1.0); m = np.zeros(int(.3 * SR)); m[:body.size] += body; m[:slap.size] += slap
    return pan(sat(m, 1.6) * .75 * g, rng.uniform(-.15, .15)), 0


def swish(rng, g=1.0):   # scene wipe: bar sweeping across, small knock where it lands
    d = .38; a0, a1, b0, b1 = PK.get('swish', (500, 800, 3500, 5500)); m = band(rng, d, rng.uniform(a0, a1), rng.uniform(b0, b1), q=rng.uniform(*PK.get('swish_q', (1.0, 1.6))), attack=.06) * .5
    if PK.get('rip'):   # torn paper: crackly amplitude-modulated grain on top of the slide
        mod = (rng.random(int(d * SR)) > .55).astype(float); mod = signal.sosfilt(signal.butter(1, 900, fs=SR, output='sos'), mod); m = m * (.35 + .9 * mod)
    k = drop(rng.uniform(120, 150), 55, .16, .05) * .45; m = np.pad(m, (0, int(.3 * SR))); m[int(d * SR) - int(.02 * SR):int(d * SR) - int(.02 * SR) + k.size] += k
    return pan(m * g, rng.uniform(-.3, .3)), 0


def snap(rng, g=1.0):   # the slash through the equals sign: quick zip + tick
    m = band(rng, .1, rng.uniform(3000, 4200), rng.uniform(7000, 9000), q=1.4, attack=.008) * .55
    return pan(np.pad(m, (0, 400)) * g, 0), 0


def thud(rng, g=1.0):   # finale panel: low body with a short air tail (the loudest sound in the video)
    body = sat(drop(rng.uniform(95, 115), 38, .6, .22), 2.2) * .9; air = band(rng, .35, 700, 220, q=.8, shape="decay", attack=.01) * .35
    m = np.zeros(int(.7 * SR)); m[:body.size] += body; m[:air.size] += air
    return pan(m * g, 0), 0


def events(tl):
    ev = []   # (time, kind, gain, label)
    for s in tl["scenes"]:
        t0 = s["start"]; P = s.get("params", {}); ty = s["type"]
        if s["i"] > 0: ev.append((t0, "swish", .9, "wipe"))
        at = lambda lt: t0 + max(lt, 0.02) + (.1 if s["i"] > 0 else 0)   # incoming scene is covered by the wipe for its first ~0.38 s
        if ty == "headline":
            for i, _ in enumerate(P.get("lines", [])):
                ev.append((at(-.2 + i * .14 + .08), PK.get("line", "slide"), (.55 if i else .7) * (.75 if PK.get("line") == "stamp" else 1), f"line{i}"))
            if P.get("underline") is not None: ev.append((at(.5 + P["underline"] * .14), "ink", .8, "underline"))
        elif ty == "bars":
            if P.get("title"): ev.append((at(0), "slide", .7, "title"))
            for i, r in enumerate(P.get("rows", [])):
                ev.append((at(.2 + i * .35), "tick", .8, f"row{i}"))
                t_s = .35 + i * .35; dur = 1.1 if r.get("wobble") else .5
                n = 7 if r.get("wobble") else 4
                for k in range(n): ev.append((at(t_s + dur * k / n), "tick", .35 + .05 * k, f"grow{i}.{k}"))
            g = P.get("gap")
            if g: ev.append((at(.35 + g["to"] * .35 + 1.3), "stamp", .8, "gap"))
        elif ty == "stat":
            if P.get("small"): ev.append((at(-.1), "tick", .8, "small"))
            ev.append((at(-.05), "stamp", .9, "big")); ev.append((at(.4), "ink", .6, "rule"))
            for i, _ in enumerate((P.get("sub") or "").split("\n")): ev.append((at(.5 + i * .15), "slide", .5, f"sub{i}"))
        elif ty == "list":
            if P.get("title"): ev.append((at(0), "slide", .7, "title"))
            for i, _ in enumerate(P.get("items", [])): ev.append((at(.25 + i * .45), "slide", .65, f"item{i}"))
        elif ty == "versus":
            ev.append((at(.2), "stamp", .75, "a")); ev.append((at(.5), "snap", .8, "vs")); ev.append((at(.6), "stamp", .85, "b"))
        elif ty == "counter":
            if P.get("label"): ev.append((at(-.1), "tick", .8, "label"))
            for k in range(8): ev.append((at(.1 + 1.3 * k / 8), "tick", .3 + .05 * k, f"count{k}"))
            ev.append((at(1.42), "stamp", .9, "done"))
            if P.get("sub"): ev.append((at(1.0), "slide", .5, "sub"))
        elif ty == "steps":
            if P.get("title"): ev.append((at(0), "slide", .7, "title"))
            for i, _ in enumerate(P.get("steps", [])):
                ev.append((at(.25 + i * .5), "stamp", .7, f"step{i}"))
                if i: ev.append((at(.25 + i * .5 - .15), "ink", .45, f"arrow{i}"))
        elif ty == "finale":
            ev.append((at(.05), "thud", 1.0, "panel"))
            if P.get("top"): ev.append((at(.3), "slide", .6, "top"))
            if P.get("accent"): ev.append((at(.45), "stamp", .8, "accent"))
            if P.get("mark"): ev.append((at(.9), "ink", .6, "bars")); ev.append((at(1.3), "snap", .9, "slash")) if P["mark"] == "neq" else None
            for i, _ in enumerate(P.get("bottom", [])): ev.append((at(1.5 + i * .15), "slide", .6, f"bottom{i}"))
    return [e for e in ev if e]


GEN = dict(slide=slide, ink=ink, tick=tick, stamp=stamp, swish=swish, snap=snap, thud=thud)


def build(work):
    tl = json.load(open(os.path.join(work, "timeline.json"))); PK.clear(); PK.update(PACKS.get(tl.get('v2', {}).get('world', 'a'), {})); vid = tl.get("title", "") + str(tl["seed"])
    n = int((tl["duration"] + 1) * SR); bus = np.zeros((2, n)); log = []; last = {}
    for j, (t, kind, g, label) in enumerate(sorted(events(tl))):
        rng = rng_for(vid, "foley", j, kind); a, _ = GEN[kind](rng, g)
        i = int(round(t * SR)); seg = a[:, :max(0, n - i)]; bus[:, i:i + seg.shape[1]] += seg * g; log.append([round(t, 3), kind, label])
    pk = np.abs(bus).max() or 1; bus = bus / pk * 10 ** (-3 / 20)   # peak = the loudest hit (finale thud); mix.py sets the level
    sf.write(os.path.join(work, "sfx.wav"), bus.T.astype(np.float32), SR, subtype="FLOAT"); json.dump(log, open(os.path.join(work, "sfx.json"), "w"))
    return log


if __name__ == "__main__":
    print(len(build(sys.argv[1])), "foley events")
