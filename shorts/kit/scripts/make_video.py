"""One command: script.json -> MP4.

    python3 make_video.py script.json --out OUTDIR [--preview] [--no-music] [--workers 2] [--keep-frames] [--hq]

Steps: style -> fonts -> voice -> timeline -> music -> previews + contact sheet
       -> frames (background) while sfx + mix run -> encode (<=30 MB) -> QA.
--hq encodes with x264 preset medium (~6x slower on 2 CPUs, slightly smaller file).
--preview stops after the contact sheet (fast check of look + timing before the full render).
Re-runs reuse cached voice lines, so edits to visuals/style are cheap.
Outputs: OUTDIR/<slug>.mp4, OUTDIR/contact.png, OUTDIR/work/ (timeline.json, mix.wav, frames/...).
"""
import json, os, re, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import styles, fonts, voice, timeline, music, sfx, mix, qa  # noqa: E402

SR = 48000


def slug(s): return re.sub(r"[^a-z0-9]+", "-", (s or "video").lower()).strip("-")[:40] or "video"


def run(cmd, log=None, bg=False):
    if bg: return subprocess.Popen(cmd, stdout=open(log, "w"), stderr=subprocess.STDOUT)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: raise RuntimeError(f"{cmd[0]} failed:\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    return r.stdout


def encode(work, out, preset="veryfast"):
    base = ["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", os.path.join(work, "frames", "%05d.jpg"), "-i", os.path.join(work, "mix.wav")]
    run(base + ["-c:v", "libx264", "-preset", preset, "-crf", "19" if preset == "veryfast" else "18", "-pix_fmt", "yuv420p", "-profile:v", "high",
                "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out])
    if os.path.getsize(out) > 29.5e6:   # grain/glitch inflate size: cap for SendUserFile (30 MB)
        tmp = out + ".tmp.mp4"; os.replace(out, tmp)
        run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-c:v", "libx264", "-preset", "slow", "-b:v", "6500k", "-maxrate", "8000k",
             "-bufsize", "12000k", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", out]); os.remove(tmp)


def main():
    a = sys.argv[1:]
    if not a or a[0].startswith("-"): print(__doc__); sys.exit(1)
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    script_p = os.path.abspath(a[0]); script = json.load(open(script_p))
    out_dir = os.path.abspath(opt("--out", os.path.join(os.path.dirname(script_p), "out"))); work = os.path.join(out_dir, "work")
    os.makedirs(work, exist_ok=True); T = {}; t0 = time.time()
    def lap(k): T[k] = round(time.time() - t0 - sum(T.values()), 1)

    # 1. style (dynamic: preset name, free-text cues, or dict) + per-video overrides
    st = styles.resolve_style(script.get("style"))
    if script.get("style_overrides"): st = styles.finalize(styles.deep_merge(st, script["style_overrides"]))
    json.dump(st, open(os.path.join(work, "style.json"), "w"), indent=1)
    f = st["fonts"]; json.dump(fonts.ensure_fonts(work, [(f["display"], f["display_weight"]), (f["text"], f["text_weight"]), ("Inter", 800)]),
                               open(os.path.join(work, "fonts.json"), "w"))
    print(f"style: {st['name']}  accent {st['accent']}  fonts {f['display']}/{f['text']}  music {st['music']['mood']}  sfx {st['sfx']['kit']}"); lap("style")

    # 2. voice + timeline
    vinfo = voice.build(script, work); lap("voice")
    if script.get("silent"):   # pure-animation format: keep the timings (captions, hits, music fit) but mute the voice track
        import numpy as _np, soundfile as _sf
        _v, _sr = _sf.read(os.path.join(work, "voice.wav"), dtype="float32"); _sf.write(os.path.join(work, "voice.wav"), _np.zeros_like(_v), _sr, subtype="FLOAT")
    tl = timeline.build(script, st, vinfo); json.dump(tl, open(os.path.join(work, "timeline.json"), "w"), indent=1)
    for s in tl["scenes"]:
        print(f"  {s['i']} {s['act']:7s} {s['type']:10s} {s['start']:5.2f}-{s['end']:5.2f}s keys={[k['w'] for k in s['keys']]} -> {s['transition']}")
    print(f"duration {tl['duration']:.2f}s ({tl['frames']} frames)"); lap("timeline")

    # 3. music (fits tempo to keywords, writes bpm back into timeline.json)
    music_on = script.get("music", True) and "--no-music" not in a
    mres = music.build(work, script.get("music_mood"), off=not music_on); print(f"music: {mres}"); lap("music")

    # optional per-video custom worlds
    cust = script.get("scenes_custom")
    if cust:
        src = cust if os.path.isabs(cust) else os.path.join(os.path.dirname(script_p), cust); shutil.copyfile(src, os.path.join(work, "scenes_custom.js"))
    elif os.path.exists(os.path.join(work, "scenes_custom.js")): os.remove(os.path.join(work, "scenes_custom.js"))

    # 4. previews + contact sheet
    print(run(["node", os.path.join(HERE, "render.js"), work, "auto-preview"]).strip().splitlines()[-1])
    sheet = qa.sheet(work, cols=5, width=216); shutil.copyfile(sheet, os.path.join(out_dir, "contact.png")); lap("preview")
    if "--preview" in a:
        print(json.dumps({"preview": os.path.join(out_dir, "contact.png"), "timings_s": T})); return

    # 5. frames in the background while audio is built
    fdir = os.path.join(work, "frames"); shutil.rmtree(fdir, ignore_errors=True)
    rp = run(["node", os.path.join(HERE, "render.js"), work, "full", "--workers", opt("--workers", "2")], os.path.join(work, "render.log"), bg=True)
    ev = sfx.build(work); mix.build(work, float(opt("--music-db", -20))); lap("audio")
    rc = rp.wait(); log = open(os.path.join(work, "render.log")).read()
    if rc: raise RuntimeError("render failed:\n" + log[-3000:])
    print(log.strip().splitlines()[-2] if len(log.strip().splitlines()) > 1 else log); lap("frames")

    # 6. encode + QA
    out = os.path.join(out_dir, slug(script.get("title")) + ".mp4"); encode(work, out, "medium" if "--hq" in a else "veryfast"); lap("encode")
    v = qa.video(out, work); aq = qa.audio(os.path.join(work, "mix.wav"))
    if "--keep-frames" not in a: shutil.rmtree(fdir, ignore_errors=True)
    T["total"] = round(time.time() - t0, 1)
    print(json.dumps({"mp4": out, "contact": os.path.join(out_dir, "contact.png"), "duration": round(v["duration"], 2),
                      "mb": round(v["mb"], 1), "lufs": aq["lufs"], "true_peak": aq["true_peak"], "timings_s": T}, indent=1))


if __name__ == "__main__":
    main()
