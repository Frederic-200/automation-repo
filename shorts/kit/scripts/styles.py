"""Dynamic styles for video-kit.

A style is ONE dict that drives everything: palette, fonts, motion feel, camera, transitions,
post-FX, preferred scene worlds, caption mode, SFX kit and music mood.

    from styles import resolve_style
    st = resolve_style("calm warm paper, teal accent")          # free text cues
    st = resolve_style({"base": "neon", "accent": "#00e5ff"})   # preset + overrides
    st = resolve_style({"blend": ["liquid", "vhs"], "t": .4})   # mix two presets

CLI:  python3 styles.py "glitchy neon night, purple"  -> prints the resolved JSON
      python3 styles.py --list                         -> preset names + cue words
"""
import json, re, sys, copy

# ---------------------------------------------------------------- presets (seeds, not fixed looks)
BASE = {
    "name": "custom",
    "bg": ["#06070b", "#141826"],          # dark acts (problem/build), top -> bottom gradient
    "bg2": ["#f4f1ea", "#ffffff"],         # bright acts (payoff/button)
    "ink": "#ffffff", "ink2": "#0b0b0f",   # text on dark / on bright
    "accent": "#ff3b30",
    "palette": ["#ff3b30", "#ffb000", "#ffffff", "#7a7f8c"],
    "fonts": {"display": "Anton", "display_weight": 400, "text": "Inter", "text_weight": 800},
    "upper": True,
    "motion": {"zeta": 0.5, "w0": 14, "stagger": 0.07, "on_twos": False, "speed": 1.0},
    "camera": {"shake": 1.0, "push": 0.08, "zoom_hit": 1.0},
    "transitions": ["liquid", "iris", "whip", "flash"],
    "post": {"grain": 0.07, "vignette": 0.35, "scanlines": 0, "rgb": 1.0, "glitch": 0.6,
             "pixel": 0, "halftone": 0, "bloom": 0.4, "paper": 0},
    "worlds": ["liquid", "storm", "shapes", "tunnel", "particles", "burst"],
    "caption": {"mode": "slam", "slab": True, "y": 1390, "size": 86},
    "sfx": {"kit": "cinematic", "gain": 1.0},
    "music": {"mood": "epic", "bpm": [86, 100]},
}

PRESETS = {
    "liquid": dict(cues="liquid fluid goo blob abstract motivation resilience flow water melt organic default",
                   accent="#ff3b30", palette=["#ff3b30", "#ff8a00", "#ffffff", "#8a8f99"],
                   worlds=["liquid", "storm", "shapes", "tunnel", "particles", "burst"],
                   transitions=["liquid", "liquid", "iris", "flash"]),
    "neon": dict(cues="neon synthwave synth retrowave 80s night cyber cyberpunk grind ambition outrun glow arcade",
                 bg=["#0a0418", "#1a0633"], bg2=["#2a0a4a", "#ff2e88"], accent="#ff2e88",
                 palette=["#ff2e88", "#00e5ff", "#ffd400", "#7b2cff"],
                 fonts={"display": "Monoton", "display_weight": 400, "text": "Orbitron", "text_weight": 800},
                 worlds=["grid", "tunnel", "particles", "grid", "burst"],
                 transitions=["glitch", "whip", "flash", "iris"],
                 post={"grain": .05, "vignette": .45, "scanlines": .12, "rgb": 1.4, "glitch": 1.0, "bloom": .9},
                 sfx={"kit": "glitch"}, music={"mood": "synthwave", "bpm": [92, 108]}),
    "vhs": dict(cues="vhs crt tape retro rewind memory memories nostalgia 90s analog vintage tv glitchy glitch",
                bg=["#101418", "#1f2a30"], bg2=["#e8e1cf", "#f6efe0"], accent="#ff4d4d",
                palette=["#ff4d4d", "#4dd2ff", "#f6e05e", "#c8c8c8"],
                fonts={"display": "VT323", "display_weight": 400, "text": "Share Tech Mono", "text_weight": 400},
                upper=True, worlds=["shapes", "storm", "particles", "tunnel", "burst"],
                transitions=["glitch", "glitch", "flash", "pixel"],
                post={"grain": .12, "vignette": .5, "scanlines": .25, "rgb": 2.2, "glitch": 1.3, "bloom": .3},
                caption={"mode": "slam", "slab": True}, sfx={"kit": "glitch"}, music={"mood": "lofi", "bpm": [76, 88]}),
    "halftone": dict(cues="halftone risograph riso zine print comic pop poster creativity dots ink-print bold",
                     bg=["#f3ecd8", "#efe4c6"], bg2=["#ff4f64", "#ffd23f"], ink="#1a1a1a", ink2="#1a1a1a",
                     accent="#ff4f64", palette=["#ff4f64", "#0078bf", "#ffd23f", "#1a1a1a"],
                     fonts={"display": "Archivo Black", "display_weight": 400, "text": "Archivo Black", "text_weight": 400},
                     worlds=["shapes", "particles", "bars", "shapes", "burst"],
                     transitions=["whip", "iris", "flash"],
                     post={"grain": .1, "vignette": .1, "rgb": 0.0, "glitch": 0.2, "halftone": 1.0, "bloom": 0},
                     sfx={"kit": "click"}, music={"mood": "upbeat", "bpm": [108, 120]}),
    "onebit": dict(cues="1-bit 1bit gameboy game boy pixel 8bit 8-bit retro-game level up levelup habits coding chiptune",
                   bg=["#0f380f", "#306230"], bg2=["#8bac0f", "#9bbc0f"], ink="#9bbc0f", ink2="#0f380f",
                   accent="#9bbc0f", palette=["#0f380f", "#306230", "#8bac0f", "#9bbc0f"],
                   fonts={"display": "Press Start 2P", "display_weight": 400, "text": "Press Start 2P", "text_weight": 400},
                   motion={"zeta": .6, "on_twos": True}, worlds=["shapes", "grid", "bars", "particles", "burst"],
                   transitions=["pixel", "pixel", "iris"],
                   post={"grain": 0, "vignette": 0, "rgb": 0, "glitch": .3, "pixel": 1.0, "bloom": 0},
                   caption={"mode": "slam", "slab": True, "size": 54}, sfx={"kit": "chip"},
                   music={"mood": "upbeat", "bpm": [112, 124]}),
    "paper": dict(cues="paper cut cutout cut-out craft warm warmth family gratitude cozy handmade kids soft gentle love",
                  bg=["#2b2d42", "#3d405b"], bg2=["#f4e9d8", "#fff6e9"], ink="#fffaf0", ink2="#2b2d42",
                  accent="#e07a5f", palette=["#e07a5f", "#f2cc8f", "#81b29a", "#3d405b"],
                  fonts={"display": "Fredoka", "display_weight": 700, "text": "Baloo 2", "text_weight": 800},
                  upper=False, motion={"zeta": .45, "w0": 11, "on_twos": True, "speed": .85},
                  camera={"shake": .35, "push": .05}, worlds=["paper", "shapes", "particles", "paper", "burst"],
                  transitions=["iris", "whip", "flash"],
                  post={"grain": .06, "vignette": .25, "rgb": 0, "glitch": 0, "paper": 1.0, "bloom": 0},
                  caption={"mode": "clean", "slab": True}, sfx={"kit": "soft"}, music={"mood": "gentle", "bpm": [70, 80]}),
    "swiss": dict(cues="swiss bauhaus grid minimal minimalist rules framework productivity clean modern geometric corporate business",
                  bg=["#f2f2f2", "#e9e9e9"], bg2=["#111111", "#1d1d1d"], ink="#111111", ink2="#ffffff",
                  accent="#e10600", palette=["#e10600", "#111111", "#0047ab", "#ffcc00"],
                  fonts={"display": "Archivo Black", "display_weight": 400, "text": "Inter Tight", "text_weight": 800},
                  motion={"zeta": .75, "w0": 18}, camera={"shake": .3, "push": .03},
                  worlds=["shapes", "bars", "blueprint", "shapes", "burst"], transitions=["whip", "iris", "whip"],
                  post={"grain": .03, "vignette": .05, "rgb": 0, "glitch": 0, "bloom": 0},
                  caption={"mode": "clean", "slab": True}, sfx={"kit": "click"}, music={"mood": "upbeat", "bpm": [112, 122]}),
    "aurora": dict(cues="aurora calm hope hopeful affirmation affirmations peaceful dreamy gradient serene mindfulness breathe sleep",
                   bg=["#0b1026", "#1b1f4a"], bg2=["#ffd6e0", "#c9f2ff"], ink="#ffffff", ink2="#1b1f4a",
                   accent="#7cf2d0", palette=["#7cf2d0", "#a78bfa", "#ff9ec7", "#ffd58a"],
                   fonts={"display": "Fraunces", "display_weight": 800, "text": "Inter", "text_weight": 700},
                   upper=False, motion={"zeta": .8, "w0": 9, "speed": .8}, camera={"shake": .15, "push": .06},
                   worlds=["aurora", "particles", "aurora", "tunnel", "burst"], transitions=["flash", "iris", "liquid"],
                   post={"grain": .07, "vignette": .3, "rgb": 0, "glitch": 0, "bloom": .6},
                   caption={"mode": "clean", "slab": False}, sfx={"kit": "soft", "gain": .8},
                   music={"mood": "gentle", "bpm": [66, 76]}),
    "terminal": dict(cues="terminal ascii hacker code coder developer debug matrix console programmer tech dev",
                     bg=["#020604", "#04140a"], bg2=["#0d2b17", "#0a3d1f"], ink="#b6ffcc", ink2="#b6ffcc",
                     accent="#39ff88", palette=["#39ff88", "#1fa35a", "#b6ffcc", "#0f5c30"],
                     fonts={"display": "JetBrains Mono", "display_weight": 800, "text": "JetBrains Mono", "text_weight": 700},
                     worlds=["matrix", "grid", "bars", "particles", "burst"], transitions=["glitch", "pixel", "flash"],
                     post={"grain": .05, "vignette": .45, "scanlines": .2, "rgb": .8, "glitch": 1.0, "bloom": .7},
                     caption={"mode": "type", "slab": True}, sfx={"kit": "glitch"}, music={"mood": "lofi", "bpm": [80, 92]}),
    "blueprint": dict(cues="blueprint explainer explain how-it-works howitworks diagram technical engineering schematic line-art science education",
                      bg=["#0b3d91", "#0a2f70"], bg2=["#f6f8fb", "#e8eef8"], ink="#ffffff", ink2="#0a2f70",
                      accent="#ffd400", palette=["#ffd400", "#ffffff", "#7fb3ff", "#ff6b6b"],
                      fonts={"display": "League Gothic", "display_weight": 400, "text": "Space Mono", "text_weight": 700},
                      motion={"zeta": .7, "w0": 15}, camera={"shake": .3, "push": .04},
                      worlds=["blueprint", "shapes", "bars", "blueprint", "burst"], transitions=["whip", "iris", "flash"],
                      post={"grain": .04, "vignette": .25, "rgb": 0, "glitch": 0, "bloom": .2},
                      caption={"mode": "clean", "slab": True}, sfx={"kit": "click"}, music={"mood": "upbeat", "bpm": [104, 116]}),
    "storm": dict(cues="dark epic intense power powerful war fight battle struggle pressure heavy cinematic trailer dramatic",
                  bg=["#05070c", "#151b28"], bg2=["#fff4e0", "#ffd28a"], accent="#ffb000",
                  palette=["#ffb000", "#ff4d00", "#ffffff", "#5b6475"],
                  worlds=["storm", "tunnel", "liquid", "particles", "burst"], transitions=["flash", "liquid", "glitch"],
                  camera={"shake": 1.3, "push": .1}, post={"grain": .09, "vignette": .5, "rgb": 1.2, "glitch": .8, "bloom": .6},
                  music={"mood": "epic", "bpm": [84, 96]}),
}

COLOR_WORDS = {
    "red": "#ff3b30", "crimson": "#dc143c", "orange": "#ff8a00", "amber": "#ffb000", "gold": "#ffc94d",
    "yellow": "#ffd400", "lime": "#a3ff12", "green": "#22c55e", "mint": "#7cf2d0", "teal": "#14b8a6",
    "cyan": "#00e5ff", "blue": "#2f6bff", "navy": "#1e3a8a", "indigo": "#5b5bf7", "purple": "#8b5cf6",
    "violet": "#7b2cff", "magenta": "#ff00a8", "pink": "#ff6fb5", "rose": "#ff4f79", "white": "#ffffff",
    "silver": "#c0c6d0", "coral": "#ff7f6b", "peach": "#ffb38a", "sky": "#38bdf8", "emerald": "#10b981",
}
MOOD_WORDS = {  # word -> (music mood, motion tweaks, sfx kit or None)
    "calm": ("gentle", {"zeta": .8, "speed": .8}, "soft"), "gentle": ("gentle", {"zeta": .75, "speed": .85}, "soft"),
    "sad": ("gentle", {"zeta": .8, "speed": .8}, "soft"), "love": ("gentle", {"zeta": .6}, "soft"),
    "energetic": ("upbeat", {"zeta": .45, "speed": 1.15}, None), "fun": ("upbeat", {"zeta": .4}, None),
    "playful": ("upbeat", {"zeta": .35}, "click"), "epic": ("epic", {}, "cinematic"),
    "motivational": ("epic", {}, "cinematic"), "chill": ("lofi", {"speed": .9}, "soft"), "lofi": ("lofi", {}, "soft"),
    "hype": ("trap", {"zeta": .4, "speed": 1.15}, "cinematic"), "trap": ("trap", {}, "cinematic"),
    "upbeat": ("upbeat", {}, None), "dramatic": ("epic", {}, "cinematic"),
}
LIGHT_WORDS = {"light", "bright", "white", "airy", "pastel"}
DARK_WORDS = {"dark", "night", "moody", "black", "noir"}


def _hex(c):
    c = c.lstrip("#")
    if len(c) == 3: c = "".join(ch * 2 for ch in c)
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _to_hex(rgb): return "#%02x%02x%02x" % tuple(max(0, min(255, round(v))) for v in rgb)


def mix_hex(a, b, t):
    A, B = _hex(a), _hex(b); return _to_hex([A[i] + (B[i] - A[i]) * t for i in range(3)])


def luminance(c):
    def lin(v): v /= 255; return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
    r, g, b = (lin(v) for v in _hex(c)); return .2126 * r + .7152 * g + .0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True); return (la + .05) / (lb + .05)


def deep_merge(a, b):
    out = copy.deepcopy(a)
    for k, v in (b or {}).items():
        if k == "cues": continue
        out[k] = deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def preset(name):
    if name not in PRESETS: raise KeyError(f"unknown preset {name!r}; choose from {', '.join(PRESETS)}")
    st = deep_merge(BASE, PRESETS[name]); st["name"] = name; return st


def blend(a, b, t=0.5):
    """Mix two styles: colors interpolate, numbers interpolate, lists/strings come from the nearer side."""
    A = preset(a) if isinstance(a, str) else a
    B = preset(b) if isinstance(b, str) else b
    def mx(x, y):
        if isinstance(x, dict): return {k: mx(x[k], y.get(k, x[k])) for k in x}
        if isinstance(x, str) and x.startswith("#") and isinstance(y, str) and y.startswith("#"): return mix_hex(x, y, t)
        if isinstance(x, (int, float)) and not isinstance(x, bool) and isinstance(y, (int, float)): return x + (y - x) * t
        if isinstance(x, list) and isinstance(y, list) and x and isinstance(x[0], str) and x[0].startswith("#") and len(x) == len(y):
            return [mix_hex(p, q, t) for p, q in zip(x, y)]
        if isinstance(x, list) and isinstance(y, list) and x and not isinstance(x[0], (int, float)):
            # interleave worlds/transitions so both looks appear
            out = []; [out.extend(p) for p in zip(x, y)]; return list(dict.fromkeys(out)) or x
        return x if t < .5 else y
    st = mx(A, B); st["name"] = f"{A['name']}+{B['name']}"; return st


def _words(text): return re.findall(r"#[0-9a-fA-F]{3,6}\b|[a-z0-9][a-z0-9\-]*", text.lower())


def score_presets(text):
    words = set(_words(text)); low = text.lower(); scores = {}
    for name, p in PRESETS.items():
        s = 0.0
        for cue in p["cues"].split():
            if cue in words: s += 1.0
            elif len(cue) > 4 and cue in low: s += .6
        if name in words: s += 2.0
        scores[name] = s
    return scores


def style_from_cues(text):
    """Free-text cues -> style. Picks the best preset, blends a strong runner-up, then applies
    color, light/dark and mood words. Unknown words are ignored; empty text -> 'liquid'."""
    sc = sorted(score_presets(text).items(), key=lambda kv: -kv[1])
    (n1, s1), (n2, s2) = sc[0], sc[1]
    if s1 <= 0: st = preset("liquid")
    elif s2 >= .6 * s1 and s2 > 0: st = blend(n1, n2, .35)
    else: st = preset(n1)
    words = _words(text)
    # mood -> music/motion/sfx
    for w in words:
        if w in MOOD_WORDS:
            mood, mot, kit = MOOD_WORDS[w]
            if st["music"].get("mood") != mood: st["music"].pop("bpm", None)
            st["music"]["mood"] = mood; st["motion"].update(mot)
            if kit: st["sfx"]["kit"] = kit
    # colors: explicit hex wins, else color words (first = accent, second = palette[1])
    hexes = [w for w in words if w.startswith("#")]
    named = [COLOR_WORDS[w] for w in words if w in COLOR_WORDS]
    cols = hexes + named
    if cols:
        st["accent"] = cols[0]
        st["palette"] = [cols[0]] + [c for c in cols[1:3]] + [c for c in st["palette"] if c not in cols][: max(1, 4 - len(cols))]
    if set(words) & LIGHT_WORDS and luminance(st["bg"][0]) < .3:
        st["bg"], st["bg2"] = st["bg2"], st["bg"]; st["ink"], st["ink2"] = st["ink2"], st["ink"]
    if set(words) & DARK_WORDS and luminance(st["bg"][0]) > .5:
        st["bg"], st["bg2"] = st["bg2"], st["bg"]; st["ink"], st["ink2"] = st["ink2"], st["ink"]
    st["cues"] = text
    return finalize(st)


def finalize(st):
    """Guarantee legibility: ink vs bg contrast >= 4.5, accent visible on both backgrounds."""
    for bgk, ink in (("bg", "ink"), ("bg2", "ink2")):
        if contrast(st[ink], st[bgk][0]) < 4.5:
            st[ink] = "#ffffff" if luminance(st[bgk][0]) < .35 else "#111111"
    # slab text color: whichever of black/white reads better on the accent
    st["on_accent"] = "#111111" if contrast("#111111", st["accent"]) >= contrast("#ffffff", st["accent"]) else "#ffffff"
    st.setdefault("seed", 7)
    return st


def resolve_style(spec=None):
    """Accepts: None, a preset name, free-text cues, or a dict
    {"base": name | "cues": text | "blend": [a, b], "t": .5, ...any field overrides}."""
    if spec is None or spec == "": return finalize(preset("liquid"))
    if isinstance(spec, str):
        return finalize(preset(spec)) if spec in PRESETS else style_from_cues(spec)
    spec = dict(spec)
    if "blend" in spec: st = blend(spec["blend"][0], spec["blend"][1], spec.get("t", .5))
    elif "cues" in spec: st = style_from_cues(spec["cues"])
    else: st = preset(spec.get("base", "liquid"))
    over = {k: v for k, v in spec.items() if k not in ("base", "cues", "blend", "t")}
    st = deep_merge(st, over)
    return finalize(st)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        for n, p in PRESETS.items(): print(f"{n:10s} {p['cues']}")
        sys.exit()
    arg = " ".join(sys.argv[1:])
    try: spec = json.loads(arg)
    except Exception: spec = arg
    print(json.dumps(resolve_style(spec), indent=1))
