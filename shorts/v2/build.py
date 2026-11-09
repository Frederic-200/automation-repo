#!/usr/bin/env python3
"""FredsDesk v2 builder: v2 script -> MP4. Voice, word timing, music, SFX and mixing reuse shorts/kit/scripts; frames come from the v2 engine.

    python3 shorts/v2/build.py SCRIPT.json --out DIR [--preview] [--no-music]

Script format (see shorts/v2/tests/test_a.json): v2{world,palette,number,kicker,footer}, hook, voice, audio{music,sfx}, say, scenes[{kind, lines[], params{}}].
Outputs: DIR/<slug>.mp4, DIR/preview_*.png (with --preview: previews only, no audio, fast).
"""
import json, os, shutil, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); KIT = os.path.join(HERE, "..", "kit", "scripts")
sys.path.insert(0, KIT)
import styles, voice, timeline, music, sfx, mix, qa          # noqa: E402  (shorts/kit/scripts)
import make_video as mv                                       # noqa: E402  (encode helper)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import foley                                                  # noqa: E402  (v2 foley sfx)


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode: raise RuntimeError(f"{cmd[0]} failed:\n{r.stdout[-2500:]}\n{r.stderr[-2500:]}")
    return r.stdout


def main():
    a = sys.argv[1:]
    if not a or a[0].startswith("-"): print(__doc__); sys.exit(1)
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    script = json.load(open(a[0])); out_dir = os.path.abspath(opt("--out", "out")); work = os.path.join(out_dir, "work"); os.makedirs(work, exist_ok=True)
    t0 = time.time(); T = {}
    def lap(k): T[k] = round(time.time() - t0 - sum(T.values()), 1)

    st = styles.resolve_style(script.get("style", "swiss"))
    au = script.get("audio", {})
    if au.get("music"): st["music"]["mood"] = au["music"]
    if au.get("sfx"): st["sfx"]["kit"] = au["sfx"]
    foley_on = au.get("sfx") == "foley"
    if foley_on: st["sfx"]["level_db"] = float(au.get("sfx_db", 7))
    json.dump(st, open(os.path.join(work, "style.json"), "w"), indent=1)
    s2 = json.loads(json.dumps(script))
    for sc in s2["scenes"]: sc["type"] = sc["kind"]                       # the kit's timeline reads "type"
    vinfo = voice.build(s2, work); lap("voice")
    tl = timeline.build(s2, st, vinfo); tl["v2"] = script["v2"]
    json.dump(tl, open(os.path.join(work, "timeline.json"), "w"), indent=1)
    for s in tl["scenes"]: print(f"  {s['i']} {s['type']:9s} {s['start']:6.2f}-{s['end']:6.2f}s keys={[k['w'] for k in s['keys']]}")
    print(f"duration {tl['duration']:.2f}s ({tl['frames']} frames)"); lap("timeline")
    music_on = script.get("music", True) and "--no-music" not in a
    print("music:", music.build(work, au.get("music") or st["music"]["mood"], off=not music_on)); lap("music")

    fdir = os.path.join(work, "frames"); shutil.rmtree(fdir, ignore_errors=True)
    node = ["node", os.path.join(HERE, "engine", "render.js"), "--tl", os.path.join(work, "timeline.json"), "--out"]
    if "--preview" in a:
        tl2 = json.load(open(os.path.join(work, "timeline.json"))); times = ",".join(str(round(s["start"] + min(1.2, s["dur"] if "dur" in s else (s["end"] - s["start"]) * .5), 2)) for s in tl2["scenes"])
        print(run(node + [out_dir, "--mode", "preview", "--times", "0.1," + times]).strip().splitlines()[-1]); lap("preview"); print(json.dumps({"timings_s": T})); return
    rp = subprocess.Popen(node + [fdir], stdout=open(os.path.join(work, "render.log"), "w"), stderr=subprocess.STDOUT)
    (foley.build if foley_on else sfx.build)(work); mix.build(work, float(opt("--music-db", -20))); lap("audio")
    rc = rp.wait(); log = open(os.path.join(work, "render.log")).read()
    if rc: raise RuntimeError("render failed:\n" + log[-3000:])
    print(log.strip().splitlines()[-1]); lap("frames")
    out = os.path.join(out_dir, mv.slug(script.get("title")) + ".mp4"); mv.encode(work, out); lap("encode")
    v = qa.video(out, work); aq = qa.audio(os.path.join(work, "mix.wav")); T["total"] = round(time.time() - t0, 1)
    if "--keep-frames" not in a: shutil.rmtree(fdir, ignore_errors=True)
    print(json.dumps({"mp4": out, "duration": round(v["duration"], 2), "mb": round(v["mb"], 1), "lufs": aq["lufs"], "true_peak": aq["true_peak"], "timings_s": T}, indent=1))


if __name__ == "__main__":
    main()
