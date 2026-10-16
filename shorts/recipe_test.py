#!/usr/bin/env python3
"""Render a script with a given recipe (for previews / variety sheets).
python3 shorts/recipe_test.py <script.json> <outdir> '<recipe json or layout name>' [--preview]"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import pick_recipe as PR
def main():
    f, out, spec = sys.argv[1:4]; S = json.load(open(f))
    base = {"layout": "full", "caption_style": "stack", "caption_pos": "low", "hook_style": "pop", "hook_pos": "mid", "fonts": "archivo", "camera": "punchy",
            "finish": "grain", "transitions": "whippy", "anim": "snappy", "sfx": "cinematic", "progress": False}
    r = dict(base, **(json.loads(spec) if spec.startswith("{") else {"layout": spec}))
    if S["meta"]["format"] == "C": r["caption_style"] = "off"
    r["family"] = PR.family_of(S); r["sound"] = PR.sound_of(S, r["sfx"]); S["meta"]["recipe"] = r; S["meta"]["caption_preset"] = r["caption_style"]
    ov = PR.overrides(r); S["style_overrides"] = {**(S.get("style_overrides") or {}), **ov}
    S["scenes_custom"] = os.path.join(HERE, "kit", "scenes_fredsdesk.js"); S["say"] = S.get("say") or {}; S["silent"] = S["meta"]["format"] == "C"
    os.makedirs(out, exist_ok=True); rs = os.path.join(out, "script_resolved.json"); json.dump(S, open(rs, "w"), indent=1)
    cmd = [sys.executable, os.path.join(HERE, "kit", "scripts", "make_video.py"), rs, "--out", out, "--keep-frames"] + (["--preview"] if "--preview" in sys.argv else [])
    print(subprocess.run(cmd, capture_output=True, text=True).stdout[-800:])
main()
