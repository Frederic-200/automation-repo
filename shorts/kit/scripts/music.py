"""Background music composed in code (mido) and played by real GM instruments (FluidSynth).

    python3 music.py WORK [--mood epic] [--off]

Reads timeline.json + style.json (style.music.mood / bpm range). Writes music_<stem>.wav
(pad, keys, bass, drums, sting) at 48 kHz stereo and stores bpm/beat0 back into timeline.json.
Tempo is fitted so keywords land on beats; intensity follows the acts (problem 1 -> build 2 ->
near-silence before the turn -> payoff 3 -> button chord). No FluidSynth -> numpy synth fallback.
"""
import json, os, shutil, subprocess, sys
import numpy as np, soundfile as sf
import mido

SR = 48000
CACHE = os.environ.get("VIDEO_KIT_CACHE", os.path.expanduser("~/.cache/video-kit"))
ACT_INT = {"problem": 1, "build": 2, "turn": 2, "payoff": 3, "button": 3}

# ---------------------------------------------------------------- harmony
NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}
NOTE.update({"Db": 1, "Eb": 3, "Gb": 6, "Ab": 8, "Bb": 10})
QUAL = {"": [0, 4, 7], "m": [0, 3, 7], "7": [0, 4, 7, 10], "m7": [0, 3, 7, 10], "maj7": [0, 4, 7, 11],
        "add9": [0, 4, 7, 14], "madd9": [0, 3, 7, 14], "sus2": [0, 2, 7]}


def chord(name):
    root = name[:2] if len(name) > 1 and name[1] in "#b" else name[:1]
    q = name[len(root):]; return NOTE[root], QUAL.get(q, QUAL[""])


MOODS = {
    # progressions per section: (act1 problem/build, act2 turn/build, act3 payoff/button), bars per chord
    "epic": dict(prog=(["Dm", "Dm", "Bb", "Bb"], ["Dm", "Bb", "F", "C"], ["Bb", "C", "D", "D"]), bpc=1, bpm=(84, 100),
                 pad=48, keys=0, lead=61, choir=52, bass=32, sting=47, swing=0),
    "gentle": dict(prog=(["Cadd9", "G", "Am", "F"], ["Cadd9", "G", "Am", "F"], ["F", "G", "Cadd9", "Cadd9"]), bpc=1, bpm=(64, 80),
                   pad=48, keys=0, lead=None, choir=None, bass=42, sting=None, swing=0),
    "upbeat": dict(prog=(["C", "G", "Am", "F"], ["Am", "F", "C", "G"], ["F", "G", "C", "C"]), bpc=1, bpm=(108, 124),
                   pad=89, keys=12, lead=0, choir=None, bass=33, sting=None, swing=0),
    "lofi": dict(prog=(["Dm7", "G7", "Cmaj7", "Am7"], ["Dm7", "G7", "Cmaj7", "Am7"], ["Fmaj7", "G7", "Cmaj7", "Cmaj7"]), bpc=1, bpm=(70, 90),
                 pad=89, keys=4, lead=None, choir=None, bass=33, sting=None, swing=.58),
    "synthwave": dict(prog=(["Am", "F", "C", "G"], ["Am", "F", "C", "G"], ["F", "G", "Am", "Am"]), bpc=1, bpm=(86, 110),
                      pad=89, keys=81, lead=81, choir=None, bass=38, sting=None, swing=0),
    "trap": dict(prog=(["Cm", "Ab", "Bb", "Cm"], ["Cm", "Ab", "Bb", "Bb"], ["Ab", "Bb", "Cm", "Cm"]), bpc=1, bpm=(130, 150),
                 pad=48, keys=10, lead=None, choir=None, bass=38, sting=None, swing=0),
}


def fit_bpm(kw, wts, lo, hi):
    """Tempo + first-beat offset that put weighted keywords closest to beats."""
    kw, wts = np.asarray(kw, float), np.asarray(wts, float); best = None
    if not len(kw): return (0, (lo + hi) / 2, 0.0)
    for bpm in np.arange(lo, hi + 1e-9, .1):
        T = 60 / bpm
        for phi in np.linspace(0, T, 48, endpoint=False):
            r = (kw - phi) / T; err = np.sum(wts * ((r - np.round(r)) * T) ** 2)
            if best is None or err < best[0]: best = (err, bpm, phi)
    return best


class Track:
    def __init__(s, ch, prog): s.ch, s.prog, s.ev = ch, prog, []
    def note(s, t, dur, n, v): s.ev.append((t, dur, int(np.clip(n, 0, 127)), int(np.clip(v, 1, 127))))


def compose(tl, mood, rng):
    M = MOODS[mood]; dur = tl["duration"]; scenes = tl["scenes"]
    keys = [k for s in tl["scenes"] for k in s["keys"]]
    lo, hi = tl.get("_bpm_range") or M["bpm"]
    err, bpm, phi = fit_bpm([k["s"] for k in keys], [k["str"] ** 6 for k in keys], lo, hi)
    T = 60 / bpm; bar = 4 * T
    turn = next((s for s in scenes if s["act"] == "turn" and s["keys"]), None)
    drop0, drop1 = (turn["keys"][0]["s"] - .45, turn["keys"][0]["s"]) if turn else (-1, -1)
    last_key = keys[-1]["s"] if keys else dur - 2
    act_at = lambda t: next((s["act"] for s in reversed(scenes) if t >= s["start"]), scenes[0]["act"])
    sec_of = lambda a: 0 if a in ("problem", "build") and not turn_passed(a) else (1 if a in ("build", "turn") else 2)
    def turn_passed(a): return False
    tr = {k: Track(*v) for k, v in dict(pad=(0, M["pad"]), keys=(1, M["keys"]), bass=(2, M["bass"]), drums=(9, 0),
                                        sting=(3, M["sting"] or 47), lead=(4, M["lead"] or M["keys"]), choir=(5, M["choir"] or 52)).items()}
    hum = lambda: rng.normal(0, .008)
    vel = lambda b: b + rng.integers(-8, 9)
    def ok(t, d=0): return not (t < drop1 and t + d > drop0)
    def clip_d(t, d): return min(d, drop0 - t) if t < drop0 < t + d else d

    t0 = phi - bar * np.ceil(phi / bar)    # first bar may start slightly before 0
    nb = int(np.ceil((dur + 1 - t0) / bar))
    ci = [0, 0, 0]
    end_t = min(dur - .2, last_key)
    for b in range(nb):
        bs = t0 + b * bar
        if bs > dur: break
        a = act_at(max(0, bs + .01)); I = ACT_INT[a]
        sec = 2 if a in ("payoff", "button") else (1 if a == "turn" or (a == "build" and b % 2) else 0)
        prog = M["prog"][sec]; name = prog[ci[sec] % len(prog)]; ci[sec] += 1
        if bs >= last_key + .01:   # button: hold the final chord
            name = M["prog"][2][-1]
        root, iv = chord(name); base = 48 + root                      # C3 octave
        final = bs >= last_key - bar + .01 and a == "button"
        # ---- pad: sustained voicing, swells with intensity
        for n in iv[:4]:
            st = max(0, bs); d = clip_d(st, bar * (2 if final else 1) + .05)
            if d > .05 and ok(st, .01): tr["pad"].note(st, d, base + 12 + n, 52 + 14 * I)
        if M["choir"] and I >= 2 and not final:
            for n in iv[:3]:
                d = clip_d(max(0, bs), bar)
                if d > .05: tr["choir"].note(max(0, bs), d, base + 12 + n, 40 + 12 * I)
        # ---- bass
        steps = {1: [0], 2: [0, 2], 3: [0, 1, 2, 3, 0.5, 1.5, 2.5, 3.5]}[I] if mood != "gentle" else [0, 2]
        if mood in ("upbeat", "synthwave", "lofi") and I >= 2: steps = [i / 2 for i in range(8)]
        if mood == "trap": steps = [0, 1.5, 2.75] if I >= 2 else [0]
        for s_ in steps:
            t = bs + s_ * T + hum()
            if t >= 0 and ok(t) and t < dur: tr["bass"].note(t, T * (.9 if len(steps) > 4 else 1.8), base - 12 + iv[0], vel(70 + 10 * I))
        # ---- keys: broken chords / arps / stabs
        pat = iv + [iv[0] + 12]
        if mood in ("gentle", "lofi") or I == 1:
            sub = 2 if I < 3 else 4
            for k in range(4 * sub):
                t = bs + k * T / sub + hum()
                if mood == "lofi" and k % 2: t += (M["swing"] - .5) * T / sub * 2
                if t >= 0 and ok(t) and t < dur: tr["keys"].note(t, T / sub * 1.6, base + 12 + pat[k % len(pat)] + (12 if k >= 4 * sub - 2 else 0), vel(52 + 10 * I))
        else:
            sub = 4 if mood in ("synthwave", "upbeat") or I == 3 else 2
            for k in range(4 * sub):
                t = bs + k * T / sub + hum()
                if t >= 0 and ok(t) and t < dur: tr["keys"].note(t, T / sub * .9, base + 12 + pat[k % len(pat)] + (12 if (k // len(pat)) % 2 else 0), vel(58 + 9 * I))
        if mood == "epic" and I >= 2:   # piano octaves on beat 1, brass in payoff
            if bs >= 0 and ok(bs): tr["keys"].note(bs, bar * .9, base + iv[0], 80); tr["keys"].note(bs, bar * .9, base + 12 + iv[0], 80)
            if I == 3:
                for n in iv[:3]: tr["lead"].note(max(0, bs), clip_d(max(0, bs), bar * .95), base + n, 76)
        if mood == "synthwave" and I == 3:
            for k, n in enumerate([iv[0] + 24, iv[1] + 24, iv[2] + 24, iv[1] + 24]):
                tr["lead"].note(bs + k * T, T * .9, base + n, 70)
        # ---- drums (channel 10): kick 36, snare 38, clap 39, closed hat 42, open hat 46, crash 49, toms 41/45/48, rim 37, shaker 70
        D = tr["drums"]
        def hit(t, n, v):
            if 0 <= t < dur and ok(t): D.note(t, .1, n, vel(v))
        if mood == "gentle":
            if I == 3: [hit(bs + k * T / 2, 70, 40) for k in range(8)]; hit(bs, 36, 55)
        elif mood == "epic":
            if I == 1: hit(bs, 41, 70); hit(bs + 2 * T, 41, 60)
            if I == 2: [hit(bs + k * T, 45 if k % 2 else 41, 80) for k in range(4)]
            if I == 3: hit(bs, 49, 95); [hit(bs + k * T, 36, 105) for k in range(4)]; [hit(bs + k * T, 41, 90) for k in (1, 3)]; [hit(bs + k * T / 2, 42, 55) for k in range(8)]
        else:
            if I >= 2 or mood in ("lofi", "upbeat"):
                kicks = [0, 1, 2, 3] if mood in ("upbeat", "synthwave") else ([0, 2.5] if mood == "lofi" else [0, 2.25])
                for k in kicks: hit(bs + k * T, 36, 95)
                sn = [2] if mood == "trap" else [1, 3]
                for k in sn: hit(bs + k * T, 39 if mood in ("upbeat", "trap") else (37 if mood == "lofi" else 38), 90)
                hs = 8 if mood != "trap" else 16
                for k in range(hs):
                    t = bs + k * 4 * T / hs + (((M["swing"] - .5) * 4 * T / hs * 2) if (mood == "lofi" and k % 2) else 0)
                    hit(t, 42, 45 + 15 * (k % 2 == 0))
            if I == 3 and mood != "lofi": hit(bs, 49, 85)
    # snare roll into the turn (epic/trap) and pre-turn riser handled by sfx
    if turn and mood in ("epic", "trap", "synthwave"):
        t1 = drop0; n = 16
        for k in range(n):
            t = t1 - 1.2 + 1.2 * (k / n) ** .8; tr["drums"].note(t, .05, 38, 40 + int(70 * k / n))
    # stingers on the strongest hits
    for k in keys:
        if k["str"] >= 1.2 and (M["sting"] or mood == "epic"):
            tr["sting"].note(k["s"], 1.6, 38 if mood == "epic" else 50, 120); tr["drums"].note(k["s"], .1, 49, 110)
        if k.get("impact"): tr["drums"].note(k["s"], .1, 57, 120)
    return tr, bpm, phi, T


def write_mid(path, track, bpm, drum=False):
    mid = mido.MidiFile(ticks_per_beat=480); tk = mido.MidiTrack(); mid.tracks.append(tk)
    tk.append(mido.MetaMessage("set_tempo", tempo=int(60e6 / bpm)))
    if not drum: tk.append(mido.Message("program_change", channel=track.ch, program=track.prog))
    tk.append(mido.Message("control_change", channel=track.ch, control=91, value=0))
    tk.append(mido.Message("control_change", channel=track.ch, control=93, value=0))
    ev = []
    for t, d, n, v in track.ev:
        t = max(0, t); ev.append((t, 1, n, v)); ev.append((t + max(.03, d), 0, n, 0))
    ev.sort(key=lambda e: (e[0], e[1]))
    tps = 480 * bpm / 60; last = 0
    for t, on, n, v in ev:
        tick = int(round(t * tps)); tk.append(mido.Message("note_on" if on else "note_off", channel=track.ch, note=n, velocity=v, time=tick - last)); last = tick
    mid.save(path)


def numpy_render(track, dur, drum=False):
    """Fallback synth when FluidSynth is missing: soft saw/sine voices, noise drums."""
    out = np.zeros(int((dur + 2) * SR)); rng = np.random.default_rng(1)
    for t, d, n, v in track.ev:
        i = int(t * SR); L = int((d + .3) * SR); tt = np.arange(L) / SR; a = v / 127
        if drum:
            sig = (rng.standard_normal(L) * np.exp(-tt / .05) if n != 36 else np.sin(2 * np.pi * 55 * tt) * np.exp(-tt / .15))
        else:
            f = 440 * 2 ** ((n - 69) / 12); sig = (np.sin(2 * np.pi * f * tt) + .3 * np.sin(4 * np.pi * f * tt)) * np.minimum(1, tt / .01) * np.exp(-tt / max(.2, d))
        seg = out[i:i + L]; seg += .25 * a * sig[:len(seg)]
    return np.stack([out, out])


def build(work, mood=None, off=False):
    tl = json.load(open(os.path.join(work, "timeline.json"))); st = json.load(open(os.path.join(work, "style.json")))
    for f in os.listdir(work):
        if f.startswith("music_") and f.endswith(".wav"): os.remove(os.path.join(work, f))
    if off: tl["music"] = {"bpm": 0, "beat0": 0, "off": True}; json.dump(tl, open(os.path.join(work, "timeline.json"), "w"), indent=1); return None
    mood = mood or st.get("music", {}).get("mood", "epic")
    if mood not in MOODS: mood = "epic"
    sm = st.get("music", {})
    tl["_bpm_range"] = sm.get("bpm") if sm.get("mood") == mood else None
    rng = np.random.default_rng(tl["seed"])
    tracks, bpm, phi, T = compose(tl, mood, rng); tl.pop("_bpm_range", None)
    sf2 = open(os.path.join(CACHE, "soundfont.txt")).read().strip() if os.path.exists(os.path.join(CACHE, "soundfont.txt")) else None
    fs = shutil.which("fluidsynth") if sf2 and os.path.exists(sf2) else None
    n = int(tl["duration"] * SR); stems = {"pad": ["pad", "choir"], "keys": ["keys", "lead"], "bass": ["bass"], "drums": ["drums"], "sting": ["sting"]}
    mdir = os.path.join(work, "midi"); os.makedirs(mdir, exist_ok=True)
    for stem, parts in stems.items():
        mix = np.zeros((2, n))
        for p in parts:
            tr = tracks[p]
            if not tr.ev: continue
            mp = os.path.join(mdir, p + ".mid"); write_mid(mp, tr, bpm, drum=(p == "drums"))
            if fs:
                wp = os.path.join(mdir, p + ".wav")
                subprocess.run([fs, "-ni", "-q", "-F", wp, "-r", str(SR), "-g", "0.6", "-R", "0", "-C", "0", sf2, mp], check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                a, sr = sf.read(wp, always_2d=True); a = a.T
            else: a = numpy_render(tr, tl["duration"], p == "drums")
            a = a[:, :n]; mix[:, :a.shape[1]] += a      # trims FluidSynth's ~7 s silent tail
        if np.abs(mix).max() > 0:
            fade = int(.6 * SR); mix[:, -fade:] *= np.linspace(1, 0, fade)
            sf.write(os.path.join(work, f"music_{stem}.wav"), mix.T.astype(np.float32), SR, subtype="FLOAT")
    tl["music"] = {"bpm": round(float(bpm), 2), "beat0": round(float(phi), 4), "mood": mood, "engine": "fluidsynth" if fs else "numpy"}
    json.dump(tl, open(os.path.join(work, "timeline.json"), "w"), indent=1)
    keys = [k["s"] for s in tl["scenes"] for k in s["keys"]]
    strong = [k["s"] for s in tl["scenes"] for k in s["keys"] if k["str"] >= 1.2] or keys
    off_ms = [abs(((k - phi) / T - round((k - phi) / T)) * T * 1000) for k in strong]
    return {"bpm": round(float(bpm), 1), "beat0": round(float(phi), 3), "mood": mood, "engine": tl["music"]["engine"],
            "strong_key_offset_ms": round(float(max(off_ms)), 1) if off_ms else 0}


if __name__ == "__main__":
    a = sys.argv[2:]; mood = a[a.index("--mood") + 1] if "--mood" in a else None
    import time; t0 = time.time(); r = build(sys.argv[1], mood, "--off" in a)
    print(f"music: {r} in {time.time() - t0:.1f}s")
