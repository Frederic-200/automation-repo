"""Quality checks for video-kit.

    python3 qa.py sheet WORK [--cols 4] [--width 270]  -> WORK/contact.png from WORK/preview/*.png
    python3 qa.py audio FILE.wav|mp4                   -> integrated LUFS, true peak, mean/max volume
    python3 qa.py video OUT.mp4 WORK                    -> duration vs timeline, size, 4 frames -> WORK/check_*.jpg
"""
import glob, json, os, re, subprocess, sys
from PIL import Image, ImageDraw


def sheet(work, cols=4, width=270, src=None):
    files = sorted(glob.glob(os.path.join(src or os.path.join(work, "preview"), "*.png")))
    if not files: print("no preview frames"); return None
    h = int(width * 1920 / 1080); rows = (len(files) + cols - 1) // cols
    out = Image.new("RGB", (cols * width, rows * (h + 22)), "#222")
    d = ImageDraw.Draw(out)
    for i, f in enumerate(files):
        im = Image.open(f).convert("RGB").resize((width, h), Image.LANCZOS)
        X, Y = (i % cols) * width, (i // cols) * (h + 22); out.paste(im, (X, Y + 22))
        d.text((X + 6, Y + 5), os.path.basename(f)[1:-4] + " s", fill="#fff")
    p = os.path.join(work, "contact.png"); out.save(p); print(p, f"{len(files)} frames"); return p


def audio(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    r += subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "volumedetect", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    j = json.loads(r[r.index("{"): r.index("}") + 1])
    mean = re.search(r"mean_volume: (-?[\d.]+)", r); mx = re.search(r"max_volume: (-?[\d.]+)", r)
    res = {"lufs": float(j["input_i"]), "true_peak": float(j["input_tp"]), "lra": float(j["input_lra"]),
           "mean_db": float(mean.group(1)) if mean else None, "max_db": float(mx.group(1)) if mx else None}
    ok = -15.5 <= res["lufs"] <= -12.5 and res["true_peak"] <= -0.5
    print(json.dumps(res), "OK" if ok else "CHECK: target -14 LUFS, true peak <= -1 dBTP"); return res


def video(mp4, work):
    tl = json.load(open(os.path.join(work, "timeline.json")))
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4], capture_output=True, text=True).stdout)
    size = os.path.getsize(mp4) / 1e6
    for i, f in enumerate((.1, .35, .6, .92)):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(dur * f), "-i", mp4, "-frames:v", "1", "-vf", "scale=360:-1", os.path.join(work, f"check_{i}.jpg")])
    ok = abs(dur - tl["duration"]) < .25 and size < 30
    print(f"duration {dur:.2f}s (timeline {tl['duration']:.2f}s)  size {size:.1f} MB  {'OK' if ok else 'CHECK'}")
    return {"duration": dur, "mb": size}


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "sheet":
        a = sys.argv[3:]; cols = int(a[a.index("--cols") + 1]) if "--cols" in a else 4; wd = int(a[a.index("--width") + 1]) if "--width" in a else 270
        sheet(sys.argv[2], cols, wd)
    elif cmd == "audio": audio(sys.argv[2])
    elif cmd == "video": video(sys.argv[2], sys.argv[3])
