#!/usr/bin/env python3
"""FredsDesk Loops - the daily job: build today's loop -> name files -> upload to Drive -> log in history.json.

    python3 loops/daily.py [--date YYYY-MM-DD] [--out output/loops] [--scene S] [--no-upload] [--no-log] [--force] [--drive-folder-id ID]

No model is used anywhere. Date defaults to today in Manila. Exit 0 = video published (or already done today), 1 = failed (the workflow goes red -> GitHub emails you).
Safety net: build.py re-rolls the seed up to 3x when the quality gate fails; if all fail, the known-good recipe in fallback.json is built instead
(flagged "fallback" in history.json and in the post text) so a day is never missed. A failing fallback fails the job.
"""
import argparse, json, os, shutil, subprocess, sys
from datetime import datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
HIST = os.path.join(HERE, "history.json")

NOUN = {"domino": "Domino Spiral", "cubes": "Cube Cascade", "pendulum": "Pendulum Wave", "rings": "Gyroscope Rings", "bounce": "Bouncing Grid",
        "morph": "Particle Morph", "ribbons": "Bead Ribbons", "gears": "Gear Train", "helix": "Helix Staircase", "wave": "Wave Field"}
TAGS = {"domino": "#dominoes", "cubes": "#cubes", "pendulum": "#pendulum", "rings": "#gyroscope", "bounce": "#bounce", "morph": "#particles",
        "ribbons": "#flow", "gears": "#gears", "helix": "#spiral", "wave": "#waves"}


def run(cmd, **kw):
    return subprocess.run(cmd, text=True, **kw)


def build(out, args, fallback=False):
    cmd = [sys.executable, os.path.join(HERE, "build.py"), "--out", out, "--date", args.date]
    if fallback:
        fb = json.load(open(os.path.join(HERE, "fallback.json")))
        for k in ("scene", "palette", "material", "seed"): cmd += [f"--{k}", str(fb[k])]
    elif args.scene: cmd += ["--scene", args.scene]
    shutil.rmtree(out, ignore_errors=True)
    return run(cmd).returncode == 0


def post_text(cfg, fallback):
    scene = cfg["scene"]; hook = " ".join(l["text"] for l in cfg["caption"]).strip()
    title = f"{NOUN.get(scene, 'Satisfying')} Loop - {hook}"
    tags = f"#satisfying #oddlysatisfying #loop #3d #asmr #relaxing #madebycode #shorts #fyp {TAGS.get(scene, '')}".strip()
    note = "\nNOTE: fallback recipe used today (the normal build failed its quality check twice or more).\n" if fallback else ""
    return (f"TITLE: {title}\n\nCAPTION: {hook}. A seamless loop, 100% made by code. Follow FredsDesk for a new one every day.\n\nHASHTAGS: {tags}\n\n"
            f"FILES: use the 'YT-FB' file (with music) on YouTube Shorts and Facebook Reels, and the 'TikTok no music' file on TikTok.\n"
            f"RECIPE: {scene} / {cfg['palette']['name']} / {cfg['material']} / camera {cfg['camera']['move']}{note}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.now(ZoneInfo("Asia/Manila")).strftime("%Y-%m-%d"))
    ap.add_argument("--out", default=os.path.join(ROOT, "output", "loops")); ap.add_argument("--scene")
    ap.add_argument("--no-upload", action="store_true"); ap.add_argument("--no-log", action="store_true"); ap.add_argument("--force", action="store_true")
    ap.add_argument("--drive-folder-id"); args = ap.parse_args()
    hist = json.load(open(HIST)) if os.path.exists(HIST) else []
    if not args.force and any(h["date"] == args.date for h in hist): print(f"{args.date} already built - nothing to do"); return 0

    fallback = False
    if not build(args.out, args):
        print("::warning title=Loop build failed its quality gate::using the fallback recipe")
        fallback = True
        if not build(args.out, args, fallback=True):
            print("::error title=Loop build failed::normal build AND fallback both failed"); return 1
    cfg = json.load(open(os.path.join(args.out, "cfg.json")))

    base = f"{args.date} Loop - {NOUN.get(cfg['scene'], cfg['scene'])}"
    files = {os.path.join(args.out, "final_music.mp4"): f"{base} (YT-FB).mp4", os.path.join(args.out, "final_tiktok.mp4"): f"{base} (TikTok no music).mp4",
             os.path.join(args.out, "preview.jpg"): f"{base} preview.jpg"}
    post = os.path.join(args.out, "post.txt"); open(post, "w").write(post_text(cfg, fallback)); files[post] = f"{base} post.txt"

    if not args.no_upload:
        for k in ("GDRIVE_CLIENT_ID", "GDRIVE_CLIENT_SECRET", "GDRIVE_REFRESH_TOKEN"):
            if not os.environ.get(k): print(f"::error title=Drive secrets missing::{k} is not set"); return 1
        if args.drive_folder_id: os.environ["GDRIVE_FOLDER_ID_LOOPS"] = args.drive_folder_id
        sys.path.insert(0, HERE); import drive as D
        try:
            dr = D.client(); folder = D.ensure_subfolder(dr, D.ensure_folder(dr), f"{args.date} - {NOUN.get(cfg['scene'], cfg['scene'])}"); have = D.existing_names(dr, folder)
            for path, name in files.items():
                if name in have: print("already in Drive, skipping:", name); continue
                print("uploaded:", name, D.upload(dr, folder, path, name))
        except Exception as e:
            print(f"::error title=Drive upload failed::{type(e).__name__}: {str(e)[:300]}"); return 1

    if not args.no_log:
        hist = [h for h in hist if h["date"] != args.date]
        hist.append(dict(date=args.date, scene=cfg["scene"], palette_name=cfg["palette"]["name"], material=cfg["material"], camera=cfg["camera"],
                         hook=" ".join(l["text"] for l in cfg["caption"]), fallback=fallback, qa=json.load(open(os.path.join(args.out, "qa.json"))).get("notes")))
        json.dump(hist[-60:], open(HIST, "w"), indent=1)
    print(f"DONE {args.date}: {cfg['scene']} / {cfg['palette']['name']} / {cfg['material']}{' (FALLBACK)' if fallback else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
