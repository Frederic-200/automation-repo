#!/usr/bin/env python3
"""FredsDesk Loops - build one video: pick recipe -> render -> audio -> mux (music + no-music) -> QA -> preview.

    python3 loops/build.py --out DIR [--date YYYY-MM-DD] [--scene S] [--palette P] [--material M] [--seed N] [--no-qa]

No model is used anywhere. If QA fails the seed is re-rolled (up to 3 times); if every attempt fails the last passing
sample recipe in loops/fallback.json is used so a day is never missed (added in phase 3).
Outputs in DIR: final_music.mp4, final_tiktok.mp4 (SFX only), preview.jpg, cfg.json, qa.json
"""
import argparse, json, os, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode: raise RuntimeError(f"{' '.join(map(str, cmd[:3]))} failed:\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")
    return r.stdout


def true_peak(path):
    import re
    e = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e); return float(m[-1]) if m else None


def mux(d, name, wav, ceiling=-1.2):
    """video copy + AAC audio; AAC can overshoot the WAV's peak, so measure the finished file and trim until true peak <= ceiling."""
    trim = 0.0
    for _ in range(4):
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(d, "silent.mp4"), "-i", os.path.join(d, wav), "-c:v", "copy"]
        if trim: cmd += ["-af", f"volume={trim:.2f}dB"]
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", os.path.join(d, name)]
        sh(cmd); tp = true_peak(os.path.join(d, name))
        if tp is None or tp <= ceiling: break
        trim -= (tp - ceiling) + 0.3
    print(f"{name}: true peak {tp} dBFS (audio trim {trim:.1f} dB)")


def attempt(a, reroll):
    d = a.out
    os.makedirs(d, exist_ok=True)
    pick = [sys.executable, os.path.join(HERE, "pick.py"), "--out", d, "--reroll", str(reroll)]
    for k in ("date", "scene", "palette", "material", "seed"):
        if getattr(a, k) is not None: pick += [f"--{k}", str(getattr(a, k))]
    if not a.reuse_video: print(sh(pick).strip())
    if not a.reuse_video: print(sh(["node", os.path.join(HERE, "render.js"), "--cfg", os.path.join(d, "cfg.json"), "--out", d, "--mode", "full"]).strip().splitlines()[-1])
    print(sh([sys.executable, os.path.join(HERE, "audio.py"), d]).strip())
    for name, wav in (("final_music.mp4", "audio_music.wav"), ("final_tiktok.mp4", "audio_sfx.wav")):
        mux(d, name, wav)
    sh(["ffmpeg", "-y", "-loglevel", "error", "-ss", "5", "-i", os.path.join(d, "final_music.mp4"), "-frames:v", "1", "-q:v", "2", os.path.join(d, "preview.jpg")])
    if a.no_qa: return True
    r = subprocess.run([sys.executable, os.path.join(HERE, "qa.py"), d, "--video", os.path.join(d, "final_music.mp4")], capture_output=True, text=True)
    print(r.stdout.strip()); return r.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    for k in ("date", "scene", "palette", "material", "seed"): ap.add_argument(f"--{k}")
    ap.add_argument("--no-qa", action="store_true"); ap.add_argument("--reuse-video", action="store_true", help="keep existing cfg + silent.mp4, redo audio/mux/QA only"); a = ap.parse_args()
    for reroll in range(3):
        if attempt(a, reroll): print("BUILD OK"); return 0
        print(f"QA failed, re-rolling ({reroll + 1}/3)")
        if a.seed is not None: break          # an explicit seed is never re-rolled
    print("BUILD FAILED"); return 1


if __name__ == "__main__":
    sys.exit(main())
