#!/usr/bin/env python3
"""Pick today's visual RECIPE (12 axes) so no two videos look alike.

    python3 shorts/pick_recipe.py shorts/queue/<file>.json [--date YYYY-MM-DD] [--dry]

Writes meta.recipe (and meta.caption_preset) into the script. build_daily.py turns the recipe into style_overrides.
Rules (also enforced by validate.py): the recipe differs from each of the last 7 videos on at least MIN_DIFF of the 12 axes,
and frame layout + caption style are never the same as yesterday.
Axes: layout, caption_style, caption_pos, hook_style, hook_pos, fonts, family, camera, finish, transitions, anim, sound.
`family` (palette/style preset from the script's free-text `style`) and `sound` (sfx kit x music mood) are partly writer-driven,
so they are measured but not chosen here.
"""
import json, os, random, sys, hashlib, copy
from datetime import datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "kit", "scripts"))
MIN_DIFF = 5
LOOKBACK = 7

LAYOUTS = ["full", "card", "top_stage", "text_first", "letterbox", "tilt_card"]
CAPTION_STYLES = ["stack", "typeon", "slam", "clean"]
CAPTION_POS = ["low", "mid"]
HOOK_STYLES = ["pop", "outline", "sticker", "terminal"]
HOOK_POS = {"top": 330, "mid": 600, "low": 920}
CAMERAS = {
    "calm": {"shake": .35, "push": .05, "zoom_hit": .6, "drift": 0},
    "punchy": {"shake": 1.3, "push": .1, "zoom_hit": 1.4, "drift": 0},
    "drift": {"shake": .3, "push": .06, "zoom_hit": .7, "drift": 1.0},
    "snap": {"shake": .6, "push": .02, "zoom_hit": 1.8, "drift": 0},
}
FINISHES = {
    "clean": {"grain": .02, "vignette": .12, "scanlines": 0, "rgb": .3, "glitch": 0, "bloom": .15, "halftone": 0, "paper": 0, "pixel": 0},
    "grain": {"grain": .14, "vignette": .4, "scanlines": 0, "rgb": .6, "glitch": .3, "bloom": .35, "halftone": 0, "paper": 0, "pixel": 0},
    "vhs": {"grain": .12, "vignette": .5, "scanlines": .25, "rgb": 2.2, "glitch": 1.2, "bloom": .3, "halftone": 0, "paper": 0, "pixel": 0},
    "halftone": {"grain": .1, "vignette": .1, "scanlines": 0, "rgb": 0, "glitch": .2, "bloom": 0, "halftone": 1.0, "paper": 0, "pixel": 0},
    "crt": {"grain": .05, "vignette": .5, "scanlines": .22, "rgb": .9, "glitch": .5, "bloom": .7, "halftone": 0, "paper": 0, "pixel": 0},
}
TRANSITIONS = {
    "whippy": ["whip", "flash", "glitch", "whip"],
    "liquidy": ["liquid", "iris", "liquid", "flash"],
    "glitchy": ["glitch", "pixel", "flash", "glitch"],
    "clean": ["iris", "whip", "iris", "flash"],
    "flashy": ["flash", "whip", "iris", "flash"],
}
ANIMS = {
    "springy": {"zeta": .38, "w0": 12, "stagger": .09, "speed": 1.1, "on_twos": False},
    "snappy": {"zeta": .7, "w0": 20, "stagger": .05, "speed": 1.15, "on_twos": False},
    "smooth": {"zeta": .85, "w0": 10, "stagger": .07, "speed": .92, "on_twos": False},
    "steppy": {"zeta": .55, "w0": 14, "stagger": .07, "speed": 1.0, "on_twos": True},
}
SFX_KITS = ["cinematic", "glitch", "soft", "click", "chip"]
# (display, display weight, text, text weight, condensed?)
FONTS = {
    "anton": ("Anton", 400, "Share Tech Mono", 400, True),
    "archivo": ("Archivo Black", 400, "Share Tech Mono", 400, False),
    "bebas": ("Bebas Neue", 400, "Inter", 800, True),
    "oswald": ("Oswald", 700, "IBM Plex Mono", 700, True),
    "grotesk": ("Space Grotesk", 700, "JetBrains Mono", 700, False),
    "syne": ("Syne", 800, "Inter", 800, False),
    "unbounded": ("Unbounded", 800, "Inter", 800, False),
    "bricolage": ("Bricolage Grotesque", 800, "IBM Plex Mono", 700, False),
}
AXES = ["layout", "caption_style", "caption_pos", "hook_style", "hook_pos", "fonts", "family", "camera", "finish", "transitions", "anim", "sound"]

# caption anchors per layout: y of the stack/typeon block centre, block height, stack scale, typeon size, y for slam/clean captions
ANCHOR = {
    "full": dict(y=1330, h=800, ss=.8, ts=150, c=1390),
    "card": dict(y=1560, h=520, ss=.62, ts=118, c=1620),
    "top_stage": dict(y=1520, h=560, ss=.66, ts=124, c=1620),
    "text_first": dict(y=1000, h=900, ss=.9, ts=160, c=1000),
    "letterbox": dict(y=1720, h=300, ss=.45, ts=92, c=1730),
    "tilt_card": dict(y=1600, h=480, ss=.58, ts=110, c=1650),
}
MID_OFFSET = {"full": -260, "text_first": -360, "top_stage": -120, "card": 0, "letterbox": 0, "tilt_card": 0}


def family_of(script):
    import styles
    spec = script.get("style")
    try:
        return styles.resolve_style(spec).get("name", "custom")
    except Exception:
        return "custom"


def sound_of(script, recipe_sfx=None):
    import styles
    try:
        st = styles.resolve_style(script.get("style"))
        kit = (script.get("style_overrides") or {}).get("sfx", {}).get("kit") or st["sfx"]["kit"]
    except Exception:
        kit = "cinematic"
    return f"{recipe_sfx or kit}|{script.get('music_mood') or 'auto'}"


def distance(a, b):
    """Number of the 12 axes on which two recipes differ."""
    return sum(1 for k in AXES if a.get(k) != b.get(k))


def overrides(r, script_look=None):
    """Recipe -> style_overrides dict for the kit (layout, captions, hook, fonts, camera, finish, transitions, motion, sfx)."""
    A = ANCHOR[r["layout"]]; off = MID_OFFSET[r["layout"]] if r["caption_pos"] == "mid" else 0
    y, c = A["y"] + off, A["c"] + off
    d, dw, t, tw, _ = FONTS[r["fonts"]]
    cap = {"off": {"mode": "off"},
           "stack": {"mode": "stack", "stack_y": y, "stack_h": A["h"], "stack_size": A["ss"]},
           "typeon": {"mode": "typeon", "typeon_y": y, "typeon_size": A["ts"] + (25 if r["fonts"] == "bebas" else 0), "typeon_w": 900 if r["layout"] != "letterbox" else 940},
           "slam": {"mode": "slam", "slab": True, "y": c, "size": 86 if r["layout"] in ("full", "text_first") else 70},
           "clean": {"mode": "clean", "slab": True, "y": c, "size": 78 if r["layout"] in ("full", "text_first") else 64}}[r["caption_style"]]
    o = {"layout": {"name": r["layout"]},
         "caption": cap,
         "hook": {"style": r["hook_style"], "y": HOOK_POS[r["hook_pos"]]},
         "fonts": {"display": d, "display_weight": dw, "text": t, "text_weight": tw},
         "camera": dict(CAMERAS[r["camera"]]),
         "post": dict(FINISHES[r["finish"]]),
         "transitions": list(TRANSITIONS[r["transitions"]]),
         "motion": dict(ANIMS[r["anim"]]),
         "extras": {"progress": bool(r.get("progress"))}}
    if r.get("sfx"): o["sfx"] = {"kit": r["sfx"]}
    return o


def valid(r, fmt):
    cond = FONTS[r["fonts"]][4]
    if r["caption_style"] == "typeon" and not cond: return False
    if r["caption_style"] == "stack" and cond and r["fonts"] != "anton": return False   # stack blocks need wide heavy faces (Anton keeps the v2 look)
    if fmt == "C" and r["caption_style"] != "off": return False
    if fmt != "C" and r["caption_style"] == "off": return False
    if r["layout"] == "letterbox" and r["caption_style"] == "typeon" and r["camera"] == "snap": return False  # too busy with the ticker bands
    if r["finish"] == "halftone" and r["hook_style"] == "terminal": return False
    return True


def history(cov, date):
    h = [e for e in cov.get("entries", []) if e.get("date", "") < date and isinstance(e.get("recipe"), dict)]
    h.sort(key=lambda e: e["date"])
    return h[-LOOKBACK:]


def pick(script, date, cov):
    fmt = script["meta"]["format"]
    fam = family_of(script)
    hist = history(cov, date)
    last = hist[-1]["recipe"] if hist else {}
    rng = random.Random(int(hashlib.sha256(date.encode()).hexdigest()[:12], 16))
    best, best_score = None, -1
    for _ in range(4000):
        r = {"layout": rng.choice(LAYOUTS), "caption_style": rng.choice(CAPTION_STYLES + ["stack", "typeon"]) if fmt != "C" else "off",
             "caption_pos": rng.choice(CAPTION_POS), "hook_style": rng.choice(HOOK_STYLES), "hook_pos": rng.choice(list(HOOK_POS)),
             "fonts": rng.choice(list(FONTS)), "camera": rng.choice(list(CAMERAS)), "finish": rng.choice(list(FINISHES)),
             "transitions": rng.choice(list(TRANSITIONS)), "anim": rng.choice(list(ANIMS)), "sfx": rng.choice(SFX_KITS),
             "progress": rng.random() < .35}
        if not valid(r, fmt): continue
        if last and (r["layout"] == last.get("layout") or r["caption_style"] == last.get("caption_style")): continue
        r["family"] = fam; r["sound"] = sound_of(script, r["sfx"])
        worst = min([distance(r, h["recipe"]) for h in hist] or [12])
        if worst >= MIN_DIFF: return r
        if worst > best_score: best, best_score = r, worst
    return best


def main():
    a = sys.argv[1:]
    if not a: print(__doc__); return 2
    f = a[0]; s = json.load(open(f))
    date = a[a.index("--date") + 1] if "--date" in a else os.path.basename(f)[:10]
    cov = json.load(open(os.path.join(HERE, "covered.json")))
    r = pick(s, date, cov)
    if r is None: print("no valid recipe found"); return 1
    print(json.dumps(r, indent=1))
    if "--dry" not in a:
        s["meta"]["recipe"] = r; s["meta"]["caption_preset"] = r["caption_style"]
        json.dump(s, open(f, "w"), indent=1, ensure_ascii=False)
        print("recipe written into", f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
