#!/usr/bin/env python3
"""Pick today's loop recipe (no model): date -> seed -> scene / palette / material / camera / light / caption -> cfg.json.

    python3 loops/pick.py --out DIR [--date YYYY-MM-DD] [--scene domino|cubes] [--seed N] [--palette NAME] [--material KIND]

Variety = a slot machine over independent "reels" seeded by the date, with the last days' picks excluded so neighbours differ.
history.json (written by the daily build) holds the recipes of recent videos; a new recipe is re-rolled if it is too close to them.
"""
import argparse, hashlib, json, os, random
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
SCENES = ["domino", "cubes"]                       # P2 grows this list to ~10
MATERIALS = ["matte", "glossy", "metal", "toon"]
CAMERAS = ["orbit", "pushin", "sway", "rise"]
FPS, SECONDS = 30, 15


def load(name, default):
    p = os.path.join(HERE, name)
    return json.load(open(p)) if os.path.exists(p) else default


def seed_of(*parts):
    return int.from_bytes(hashlib.sha256("|".join(map(str, parts)).encode()).digest()[:4], "little")


def distance(a, b):   # how alike two recipes look (0 = identical look)
    return sum([a["scene"] != b["scene"], 2 * (a["palette_name"] != b["palette_name"]), a["material"] != b["material"], a["camera"]["move"] != b["camera"]["move"]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True); ap.add_argument("--date", default=str(date.today()))
    ap.add_argument("--scene"); ap.add_argument("--seed", type=int); ap.add_argument("--palette"); ap.add_argument("--material")
    ap.add_argument("--reroll", type=int, default=0, help="QA re-roll counter (changes the seed)")
    a = ap.parse_args()
    palettes = load("palettes.json", []); hooks = load("hooks.json", []); history = load("history.json", [])[-14:]
    seed = a.seed if a.seed is not None else seed_of(a.date, a.reroll)
    rng = random.Random(seed)
    best = None
    for attempt in range(40):                      # re-roll until it differs from the last 14 videos
        r = random.Random(seed + attempt * 7919)
        scene = a.scene or r.choice([s for s in SCENES if not history or s != history[-1]["scene"]] or SCENES)
        pal = next((p for p in palettes if p["name"] == a.palette), None) if a.palette else r.choice(palettes)
        rec = dict(scene=scene, palette_name=pal["name"], material=a.material or r.choice(MATERIALS),
                   camera=dict(move=r.choice(CAMERAS), amp=round(r.uniform(0.6, 1.0), 2)),
                   light=dict(az=r.randint(15, 60), el=r.randint(44, 62), swing=r.randint(10, 24)), sceneSeed=r.getrandbits(31))
        score = min([distance(rec, h) for h in history] or [99])
        if best is None or score > best[0]: best = (score, rec, pal)
        if score >= 3: break
    _, rec, pal = best
    hook = hooks[seed_of(a.date, "hook", a.reroll) % len(hooks)]
    cfg = dict(width=1080, height=1920, fps=FPS, frames=FPS * SECONDS, scene=rec["scene"], sceneSeed=rec["sceneSeed"], palette=pal,
               material=rec["material"], camera=rec["camera"], light=rec["light"], caption=hook["lines"], date=a.date, seed=seed, recipe=rec)
    os.makedirs(a.out, exist_ok=True)
    json.dump(cfg, open(os.path.join(a.out, "cfg.json"), "w"), indent=1)
    print(f"{a.date}: {rec['scene']} / {pal['name']} / {rec['material']} / cam {rec['camera']['move']} / hook '{' '.join(l['text'] for l in hook['lines'])}'")


if __name__ == "__main__":
    main()
