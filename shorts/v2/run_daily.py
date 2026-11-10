#!/usr/bin/env python3
"""One command for a v2 daily video: validate -> preview + novelty check -> full render -> (optional) upload to Drive.

    python3 shorts/v2/run_daily.py shorts/v2/queue/YYYY-MM-DD-slug.json [--out DIR] [--no-upload] [--skip-novelty] [--date YYYY-MM-DD]
Exit codes: 0 ok, 2 validation failed, 3 too close to a recent video (re-roll world/palette with pick_world.py), 4 render/upload failed.
Never writes the novelty log: that happens only after Frederic accepts and posts the video (novelty.py add).
"""
import shutil, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); PY = sys.executable


def run(cmd, **kw):
    print("+", " ".join(cmd), flush=True); return subprocess.run(cmd, **kw).returncode


def main():
    a = sys.argv[1:]
    if not a or a[0].startswith("-"): print(__doc__); sys.exit(1)
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    script = os.path.abspath(a[0]); out = os.path.abspath(opt("--out", os.path.join("/tmp", "v2-" + os.path.basename(script)[:-5])))
    date = opt("--date") or os.path.basename(script)[:10]
    if run([PY, os.path.join(HERE, "validate_v2.py"), script, "--date", date]) != 0: sys.exit(2)
    if "--skip-novelty" not in a:
        prev = out + "-preview"
        if run([PY, os.path.join(HERE, "build.py"), script, "--out", prev, "--preview"]) != 0: sys.exit(4)
        rc = run([PY, os.path.join(HERE, "novelty.py"), "check", prev])
        if rc == 3: print("TOO CLOSE to a recent video: re-roll with pick_world.py --reroll N+1"); sys.exit(3)
        if rc != 0: sys.exit(4)
    if run([PY, os.path.join(HERE, "build.py"), script, "--out", out, "--keep-frames"]) != 0: sys.exit(4)
    mp4 = [f for f in os.listdir(out) if f.endswith(".mp4")]
    if not mp4: print("no mp4 produced"); sys.exit(4)
    mp4 = os.path.join(out, mp4[0]); print("VIDEO:", mp4)
    # second version without background music: same frames, only the audio is rebuilt (a failure here never blocks the main video)
    nm = None; out2 = out + "-nomusic"
    if run([PY, os.path.join(HERE, "build.py"), script, "--out", out2, "--no-music", "--reuse-frames", os.path.join(out, "work", "frames")]) == 0:
        f2 = [f for f in os.listdir(out2) if f.endswith(".mp4")]
        if f2:
            nm = mp4[:-4] + "-no-music.mp4"; shutil.copy(os.path.join(out2, f2[0]), nm); print("VIDEO (no music):", nm)
    else: print("WARNING: the no-music version failed; continuing with the main video only")
    shutil.rmtree(os.path.join(out, "work", "frames"), ignore_errors=True)
    if "--no-upload" not in a:
        if run([PY, os.path.join(HERE, "upload_v2.py"), script, mp4] + (["--no-music-video", nm] if nm else [])) != 0: sys.exit(4)
    print("RUN_DAILY OK")


if __name__ == "__main__":
    main()
