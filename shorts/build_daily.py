#!/usr/bin/env python3
"""Build today's FredsDesk Short: validate -> render -> outro -> no-music version -> post text -> Drive upload -> covered.json.

    python3 shorts/build_daily.py [--file shorts/queue/2026-10-16-slug.json] [--date YYYY-MM-DD] [--out output/shorts]
                                  [--no-upload] [--no-log] [--force]

No model is used here. Needs: ffmpeg, node + playwright-core, kokoro models, sherpa-onnx ASR model, fluidsynth (see shorts.yml / kit/scripts/setup.sh).
Env for upload: GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET, GDRIVE_REFRESH_TOKEN, GDRIVE_FOLDER_ID_SHORTS.
Exit codes: 0 ok (or nothing to build), 1 failed (validation / render / QA).
"""
import glob, json, os, re, shutil, subprocess, sys
from datetime import datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
KIT = os.path.join(HERE, "kit", "scripts"); sys.path.insert(0, KIT)

CAPTION_PRESETS = {
    # bold phrase blocks (the "v2" look): size by importance, accent word
    "stack": {"caption": {"mode": "stack", "stack_y": 1330, "stack_size": 0.8},
              "fonts": {"display": "Archivo Black", "display_weight": 400, "text": "Share Tech Mono", "text_weight": 400}},
    # kinetic type-on: letters pop in, keyword label boxes, word swap
    "typeon": {"caption": {"mode": "typeon", "typeon_y": 1330, "typeon_size": 150, "typeon_w": 900},
               "fonts": {"display": "Anton", "display_weight": 400, "text": "Share Tech Mono", "text_weight": 400}},
    "off": {"caption": {"mode": "off"}, "fonts": {"display": "Archivo Black", "display_weight": 400, "text": "Share Tech Mono", "text_weight": 400}},
}


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode: raise RuntimeError(f"{' '.join(map(str, cmd[:3]))} failed (exit {r.returncode}):\n{r.stdout[-2500:]}\n{r.stderr[-2500:]}")
    return r.stdout


def deep_merge(a, b):
    o = dict(a)
    for k, v in b.items(): o[k] = deep_merge(o[k], v) if isinstance(v, dict) and isinstance(o.get(k), dict) else v
    return o


def probe(p):
    j = json.loads(sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate:format=duration", "-of", "json", p]))
    n, d = j["streams"][0]["r_frame_rate"].split("/")
    return {"w": j["streams"][0]["width"], "h": j["streams"][0]["height"], "fps": float(n) / float(d), "dur": float(j["format"]["duration"])}


def loudness(p):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", p, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    tail = r[r.rindex("Integrated loudness"):]
    return float(re.search(r"I:\s+(-?[\d.]+) LUFS", tail).group(1)), float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail).group(1))


def safe(s): return re.sub(r"[^A-Za-z0-9 ._()-]+", "", s).strip()[:80] or "video"


def post_text(meta, date, fmt_name):
    p = meta["post"]; srcs = "\n".join(f"- {s['name']}: {s['url']}" for s in p.get("sources", [])) or "- none (no factual claims)"
    return (f"# {p['title']}\n\n{date} | format {fmt_name}\n\n" +
            ("Files: '- YT+Reels.mp4' (voice + music) for YouTube Shorts and FB Reels; '- TikTok (add sound).mp4' (same picture, no music) for TikTok, add a trending sound there.\n\n"
             if fmt_name != "C" else "File: '- all platforms.mp4' (music + sound effects, no voice) for TikTok, YouTube Shorts and FB Reels.\n\n") +
            f"**TikTok caption:** {p['tiktok_caption']}\n\n**YouTube Shorts / Reels caption:** {p['yt_caption']}\n\n"
            f"**Pinned comment:** {p['pinned_comment']}\n\n**Hashtags:** {' '.join(p['hashtags'])}\n\n**Sources:**\n{srcs}\n")


def pronunciation_report(work, script):
    """ASR over the finished voice track; compare acronyms. Report only (never blocks)."""
    out = []
    try:
        import align, numpy as np, soundfile as sf
        pr = json.load(open(os.path.join(HERE, "pronounce.json"))); spelled = pr.get("spelled_check", {})
        text = " ".join(l.replace("*", "") for sc in script["scenes"] for l in sc.get("lines", []))
        x, sr = sf.read(os.path.join(work, "voice.wav"), dtype="float32"); x = x.mean(1) if x.ndim > 1 else x
        heard = " ".join(re.sub(r"[^a-z ]", "", w.lower()) for w, _ in align.asr_words(x, sr))
        for a, want in spelled.items():
            if re.search(rf"\b{a}\b", text) and want not in heard: out.append(f"{a}: expected '{want}' in the ASR text")
    except Exception as ex:
        out.append(f"pronunciation check skipped: {ex}")
    return out


def main():
    a = sys.argv[1:]; opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    date = opt("--date") or datetime.now(ZoneInfo("Asia/Manila")).strftime("%Y-%m-%d")
    cov_p = os.path.join(HERE, "covered.json"); cov = json.load(open(cov_p))
    f = opt("--file")
    if not f:
        c = sorted(glob.glob(os.path.join(HERE, "queue", f"{date}-*.json")))
        if not c: print(f"No script for {date} in shorts/queue: nothing to build."); return 0
        f = c[-1]
    f = os.path.abspath(f); base = os.path.basename(f)[:-5]; slug = base[11:]
    if any(e.get("slug") == slug for e in cov["entries"]) and "--force" not in a: print(f"{slug} already published: skipping."); return 0

    # 1. validate (rotation checks ignore entries on/after the script's own date)
    print(sh([sys.executable, os.path.join(HERE, "validate.py"), f, "--quiet"]).strip())

    S = json.load(open(f)); meta = S["meta"]; fmt = meta["format"]; voiced = fmt != "C"
    out = os.path.abspath(opt("--out", os.path.join(ROOT, "output", "shorts"))); shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
    # resolve preset + absolute scenes_custom into the script handed to the kit
    R = dict(S); R["style_overrides"] = deep_merge(CAPTION_PRESETS[meta["caption_preset"]], S.get("style_overrides") or {})
    R["scenes_custom"] = os.path.join(HERE, "kit", "scenes_fredsdesk.js"); R["say"] = S.get("say") or {}; R["silent"] = not voiced
    rs = os.path.join(out, "script_resolved.json"); json.dump(R, open(rs, "w"), indent=1)
    mdir = os.path.join(out, "main"); work = os.path.join(mdir, "work")
    log = sh([sys.executable, os.path.join(KIT, "make_video.py"), rs, "--out", mdir, "--keep-frames"]); print(log[-1200:])
    main_mp4 = [p for p in glob.glob(os.path.join(mdir, "*.mp4"))][0]
    tl = json.load(open(os.path.join(work, "timeline.json"))); mood = (R.get("music_mood") or tl.get("music", {}).get("mood") or "lofi")
    mood = mood if mood in ("lofi", "gentle", "upbeat", "synthwave", "epic", "trap") else "lofi"
    notes = pronunciation_report(work, R) if voiced else []

    # 2. no-music version (voiced formats): same frames, voice + sfx only
    nom_mp4 = None
    if voiced:
        shutil.copyfile(os.path.join(work, "mix.wav"), os.path.join(work, "mix_music.wav"))
        stash = os.path.join(work, "music_off"); os.makedirs(stash, exist_ok=True)
        for p in glob.glob(os.path.join(work, "music_*.wav")): shutil.move(p, stash)
        sh([sys.executable, os.path.join(KIT, "mix.py"), work])
        import make_video  # kit module: encode(work, out, preset)
        nom_mp4 = os.path.join(mdir, "nomusic.mp4"); make_video.encode(work, nom_mp4, "veryfast")
        shutil.copyfile(os.path.join(work, "mix_music.wav"), os.path.join(work, "mix.wav"))

    # 3. outro in this video's style, appended to both versions
    odir = os.path.join(out, "outro")
    sh([sys.executable, os.path.join(HERE, "outro", "outro_build.py"), "--style-work", work, "--out", odir, "--mood", mood])
    title = safe(meta["post"]["title"].split(":")[0] if len(meta["post"]["title"]) > 60 else meta["post"]["title"]); pre = f"{date} {title}"
    # clear platform names: the music version is for YouTube Shorts + FB Reels, the no-music one for TikTok (add a trending sound there)
    fin_main = os.path.join(out, f"{pre} - YT+Reels.mp4" if voiced else f"{pre} - all platforms.mp4"); fin_nom = os.path.join(out, f"{pre} - TikTok (add sound).mp4")
    sh([sys.executable, os.path.join(HERE, "outro", "append_outro.py"), main_mp4, os.path.join(odir, "outro.mp4"), fin_main])
    if nom_mp4: sh([sys.executable, os.path.join(HERE, "outro", "append_outro.py"), nom_mp4, os.path.join(odir, "outro.mp4"), fin_nom])
    if not shutil.which("ffmpeg"): raise RuntimeError("ffmpeg missing")

    # 4. QA gates (fail the run: nothing bad goes to Drive)
    problems = []; info = {}
    for p in [fin_main] + ([fin_nom] if nom_mp4 else []):
        v = probe(p); lufs, tp = loudness(p); info[os.path.basename(p)] = dict(dur=round(v["dur"], 2), lufs=lufs, tp=tp)
        if (v["w"], v["h"]) != (1080, 1920): problems.append(f"{p}: size {v['w']}x{v['h']}")
        if abs(v["fps"] - 30) > .1: problems.append(f"{p}: fps {v['fps']}")
        if not 26 <= v["dur"] <= 60: problems.append(f"{p}: duration {v['dur']:.1f}s")
        if p == fin_main or voiced:
            if not -17.5 <= lufs <= -13.0: problems.append(f"{p}: loudness {lufs} LUFS")
            if tp > -1.5: problems.append(f"{p}: true peak {tp} dBTP")
    print(json.dumps(info, indent=1)); [print("NOTE:", n) for n in notes]
    if problems: print("QA FAILED:\n" + "\n".join(problems)); return 1

    # 5. post text + preview
    pt = os.path.join(out, f"{pre} - post text.md"); open(pt, "w").write(post_text(meta, date, fmt))
    prev = os.path.join(out, f"{pre} - preview.jpg"); sh(["ffmpeg", "-v", "error", "-y", "-ss", "3", "-i", fin_main, "-frames:v", "1", "-q:v", "3", prev])
    shutil.copyfile(os.path.join(mdir, "contact.png"), os.path.join(out, "contact.png"))
    files = [fin_main] + ([fin_nom] if nom_mp4 else []) + [pt, prev]

    # 6. upload to Drive (new folder "FredsDesk Shorts")
    links = []
    if "--no-upload" not in a:
        if not os.environ.get("GDRIVE_FOLDER_ID_SHORTS"): print("GDRIVE_FOLDER_ID_SHORTS is not set: cannot upload"); return 1
        env = dict(os.environ, GDRIVE_FOLDER_ID=os.environ["GDRIVE_FOLDER_ID_SHORTS"])
        for p in files:
            r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "upload_drive.py"), p, os.path.basename(p)], env=env, capture_output=True, text=True)
            print(r.stdout.strip() or r.stderr[-500:]);
            if r.returncode: print("UPLOAD FAILED"); return 1
            links.append(r.stdout.strip())

    # 7. log as covered (the workflow commits it)
    if "--no-log" not in a:
        cov["entries"].append({"date": date, "slug": slug, "format": fmt, "topic": meta["topic"], "caption_preset": meta["caption_preset"], "title": meta["post"]["title"]})
        json.dump(cov, open(cov_p, "w"), indent=1, ensure_ascii=False); open(cov_p, "a").write("\n")
    print(f"DONE {date} {fmt} {slug}: {len(files)} files" + (" uploaded" if links else " (not uploaded)")); return 0


if __name__ == "__main__":
    try: sys.exit(main())
    except Exception as ex: print("BUILD FAILED:", ex); sys.exit(1)
