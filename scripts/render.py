#!/usr/bin/env python3
"""Render a vertical (1080x1920) voice-over short from a script JSON.

Usage: python scripts/render.py queue/2026-10-05.json [--out output/video.mp4]

Script JSON format:
{
  "title": "Short title",
  "voice": "en-US-AndrewMultilingualNeural",          (optional)
  "beats": [
    {"text": "Did you know ...?",
     "image_prompt": "cinematic futuristic AI robot, dramatic lighting",
     "stock_query": "robot technology"}
  ]
}

Visual strategy per beat: AI image (Pollinations, free) with a slow zoom ->
Pexels portrait stock video -> plain gradient. Voice: Edge TTS (free).
"""
import argparse
import asyncio
import json
import os
import random
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

import edge_tts
import requests

W, H, FPS = 1080, 1920, 30
# Odd day of the month -> female voice, even day -> male voice.
# A script can force a voice with a "voice" key.
FEMALE_VOICE = "en-US-AvaMultilingualNeural"
MALE_VOICE = "en-US-AndrewMultilingualNeural"


def pick_voice(script_path):
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", str(script_path))
    day = int(m.group(3)) if m else 1
    return FEMALE_VOICE if day % 2 == 1 else MALE_VOICE
PEXELS_KEY = os.environ.get("PEXELS_API_KEY", "")


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        check=True, capture_output=True, text=True).stdout
    return float(out.strip())


# ---------------------------------------------------------------- voice
# Pacing (seconds). Tweak these to taste.
SPEECH_RATE = "+2%"     # history: +8% too fast, -6% too slow
LEAD_IN = 1.0           # silence before the very first word
TAIL_OUT = 1.5          # silence after the very last word
SENTENCE_PAUSE = 0.35   # between sentences inside a beat
DRAMATIC_PAUSE = 0.7    # where the script writes "..."
BEAT_PAUSE = 0.45       # between beats


def split_segments(text):
    """Split a beat into speakable pieces, each with the pause that follows it.

    "..." marks a dramatic pause; . ! ? end a sentence.
    """
    pieces = []
    for part in re.split(r"(\.\.\.|…)", text):
        if part in ("...", "…"):
            if pieces:
                pieces[-1][1] = DRAMATIC_PAUSE
            continue
        for sent in re.split(r"(?<=[.!?])\s+", part.strip()):
            if re.search(r"\w", sent):
                pieces.append([sent.strip(), SENTENCE_PAUSE])
    if pieces:
        pieces[-1][1] = 0.0
    return pieces


def silence(secs, dest):
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
         "-t", f"{secs:.3f}", "-c:a", "pcm_s16le", str(dest)])


def beat_audio(text, voice, n, tmp, lead=0.0, tail=0.0):
    """Build one beat's audio with human-like pauses. Returns (wav, words)."""
    parts, words, t = [], [], 0.0
    if lead:
        silence(lead, tmp / f"b{n}_lead.wav")
        parts.append(tmp / f"b{n}_lead.wav")
        t += lead
    for k, (sent, pause) in enumerate(split_segments(text)):
        mp3 = tmp / f"b{n}_s{k}.mp3"
        wav = tmp / f"b{n}_s{k}.wav"
        sw = asyncio.run(synth(sent, voice, mp3))
        run(["ffmpeg", "-y", "-i", str(mp3), "-ar", "24000", "-ac", "1", str(wav)])
        words += [(w, s + t, e + t) for w, s, e in sw]
        parts.append(wav)
        t += duration(wav)
        if pause:
            silence(pause, tmp / f"b{n}_p{k}.wav")
            parts.append(tmp / f"b{n}_p{k}.wav")
            t += pause
    end_pad = tail or BEAT_PAUSE
    silence(end_pad, tmp / f"b{n}_end.wav")
    parts.append(tmp / f"b{n}_end.wav")
    lst = tmp / f"b{n}_parts.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in parts))
    out = tmp / f"beat_{n}.wav"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)])
    return out, words


async def synth(text, voice, mp3_path):
    """Synthesize one sentence; return word timings [(word, start_s, end_s)]."""
    comm = edge_tts.Communicate(text, voice, rate=SPEECH_RATE, boundary="WordBoundary")
    words = []
    with open(mp3_path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 1e7
                words.append((chunk["text"], start, start + chunk["duration"] / 1e7))
    return words


# ---------------------------------------------------------------- visuals
def ai_image(prompt, dest):
    seed = random.randint(1, 10**6)
    url = ("https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt)
           + f"?width={W}&height={H}&nologo=true&seed={seed}")
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    if not r.headers.get("content-type", "").startswith("image"):
        raise RuntimeError("not an image")
    dest.write_bytes(r.content)


def image_to_clip(img, secs, dest):
    frames = max(int(secs * FPS), 1)
    vf = (f"scale={W*2}:{H*2},zoompan=z='min(zoom+0.0007,1.25)':d={frames}"
          f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},format=yuv420p")
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(img), "-vf", vf,
         "-t", f"{secs:.3f}", "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", str(dest)])


USED_STOCK = set()  # Pexels video IDs already used in this video: never reuse


def pexels_search(query):
    vids = []
    for page in (1, 2):
        r = requests.get("https://api.pexels.com/videos/search",
                         headers={"Authorization": PEXELS_KEY},
                         params={"query": query, "orientation": "portrait",
                                 "per_page": 20, "page": page},
                         timeout=30)
        r.raise_for_status()
        vids += r.json().get("videos", [])
    return [v for v in vids if v["id"] not in USED_STOCK]


def pexels_clip(query, secs, dest, tmp):
    """Fill `secs` with stock footage that is never repeated or looped.

    Prefers one clip long enough for the whole beat; otherwise chains several
    different clips back to back.
    """
    if not PEXELS_KEY:
        raise RuntimeError("no PEXELS_API_KEY")
    vids = pexels_search(query)
    if len(vids) < 3:
        vids += [v for v in pexels_search("technology future")
                 if v["id"] not in {x["id"] for x in vids}]
    if not vids:
        raise RuntimeError("no unused stock results")
    random.shuffle(vids)
    long_enough = [v for v in vids if (v.get("duration") or 0) >= secs]
    picks, total = [], 0.0
    if long_enough:
        picks = [long_enough[0]]
    else:
        for v in sorted(vids, key=lambda v: -(v.get("duration") or 0)):
            picks.append(v)
            total += v.get("duration") or 0
            if total >= secs:
                break
        if total < secs:
            raise RuntimeError("not enough unique stock footage")
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"fps={FPS},format=yuv420p")
    parts, remaining = [], secs
    for k, v in enumerate(picks):
        USED_STOCK.add(v["id"])
        files = sorted(v["video_files"], key=lambda f: abs((f.get("height") or 0) - H))
        raw = tmp / f"stock_raw_{k}.mp4"
        raw.write_bytes(requests.get(files[0]["link"], timeout=120).content)
        part = tmp / f"stock_part_{k}.mp4"
        seg = remaining if k == len(picks) - 1 else min(remaining, v.get("duration") or remaining)
        run(["ffmpeg", "-y", "-i", str(raw), "-vf", vf, "-an", "-t", f"{seg:.3f}",
             "-c:v", "libx264", "-preset", "veryfast", str(part)])
        seg = duration(part)
        parts.append(part)
        remaining -= seg
        if remaining <= 0.05:
            break
    if remaining > 0.05:
        raise RuntimeError("stock footage came up short")
    if len(parts) == 1:
        parts[0].replace(dest)
    else:
        lst = tmp / "stock_parts.txt"
        lst.write_text("".join(f"file '{p.name}'\n" for p in parts))
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
             "-c", "copy", str(dest)])


def gradient_clip(secs, dest):
    run(["ffmpeg", "-y", "-f", "lavfi", "-i",
         f"gradients=s={W}x{H}:d={secs:.3f}:r={FPS}:speed=0.03,format=yuv420p",
         "-c:v", "libx264", "-preset", "veryfast", str(dest)])


def make_visual(beat, secs, dest, tmp, first=False):
    """First scene: real video first. Other scenes: AI image first, stock fallback."""
    errors = []

    def try_stock():
        try:
            pexels_clip(beat.get("stock_query") or "technology", secs, dest, tmp)
            return True
        except Exception as e:  # noqa: BLE001
            errors.append(f"stock: {e}")
            return False

    def try_ai():
        if not beat.get("image_prompt"):
            return False
        try:
            img = tmp / "ai.jpg"
            ai_image(beat["image_prompt"], img)
            image_to_clip(img, secs, dest)
            return True
        except Exception as e:  # noqa: BLE001
            errors.append(f"ai: {e}")
            return False

    order = [("stock", try_stock), ("ai", try_ai)] if first else \
            [("ai", try_ai), ("stock", try_stock)]
    for kind, fn in order:
        if fn():
            return kind
    print("  visual fallbacks failed:", errors, file=sys.stderr)
    gradient_clip(secs, dest)
    return "gradient"


# ---------------------------------------------------------------- captions
def ass_time(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def build_ass(word_events, path):
    header = (
        "[Script Info]\nScriptType: v4.00+\nWrapStyle: 2\nPlayResX: %d\nPlayResY: %d\n\n"
        "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,"
        "OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,"
        "Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
        "Style: Default,DejaVu Sans,96,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,"
        "1,0,0,0,100,100,0,0,1,7,2,2,60,60,520,1\n\n"
        "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"
        % (W, H))
    # Fixed anchor: text is centered on the same point every time, never wraps,
    # and each group stays short enough to fit the screen width.
    pos = r"{\an5\pos(%d,%d)}" % (W // 2, 1380)
    lines, i = [], 0
    while i < len(word_events):
        group = [word_events[i]]
        i += 1
        while (i < len(word_events) and len(group) < 3
               and len(" ".join(w[0] for w in group + [word_events[i]])) <= 15):
            group.append(word_events[i])
            i += 1
        text = " ".join(w[0] for w in group).upper()
        text = re.sub(r"[{}\\]", "", text)
        start = group[0][1]
        end = group[-1][2] + 0.05
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Default,,0,0,0,,{pos}{text}")
    path.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--out", default="output/video.mp4")
    ap.add_argument("--tmp", default="build")
    args = ap.parse_args()

    spec = json.loads(Path(args.script).read_text(encoding="utf-8"))
    voice = spec.get("voice") or pick_voice(args.script)
    print("voice:", voice)
    tmp = Path(args.tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    clips, audios, all_words, offset = [], [], [], 0.0
    beats = spec["beats"]
    for n, beat in enumerate(beats, 1):
        print(f"beat {n}/{len(beats)}: {beat['text'][:60]}")
        wav, words = beat_audio(beat["text"], voice, n, tmp,
                                lead=LEAD_IN if n == 1 else 0.0,
                                tail=TAIL_OUT if n == len(beats) else 0.0)
        secs = duration(wav)
        all_words += [(w, s + offset, e + offset) for w, s, e in words]
        mp3 = wav
        clip = tmp / f"clip_{n}.mp4"
        kind = make_visual(beat, secs, clip, tmp, first=(n == 1))
        print(f"  visual: {kind}, {secs:.1f}s")
        clips.append(clip)
        audios.append(mp3)
        offset += secs

    # concat video + audio
    (tmp / "clips.txt").write_text("".join(f"file '{c.name}'\n" for c in clips))
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "clips.txt"),
         "-c", "copy", str(tmp / "video_nosound.mp4")])

    # audio: pad every beat to its clip length so sound and picture stay aligned
    inputs, filters = [], []
    for i, (a, c) in enumerate(zip(audios, clips)):
        inputs += ["-i", str(a)]
        filters.append(f"[{i}:a]apad=whole_dur={duration(c):.3f}[a{i}]")
    concat_in = "".join(f"[a{i}]" for i in range(len(audios)))
    filters.append(f"{concat_in}concat=n={len(audios)}:v=0:a=1[aout]")
    run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters),
         "-map", "[aout]", str(tmp / "voice_all.m4a")])

    ass = tmp / "captions.ass"
    build_ass(all_words, ass)
    run(["ffmpeg", "-y", "-i", str(tmp / "video_nosound.mp4"), "-i", str(tmp / "voice_all.m4a"),
         "-vf", f"ass={ass}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
         "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(out)])
    total = duration(out)
    print(f"done: {out} ({total:.1f}s)")
    if not 60 <= total <= 180:
        print(f"WARNING: video is {total:.0f}s; target is 60-180s", file=sys.stderr)


if __name__ == "__main__":
    main()
