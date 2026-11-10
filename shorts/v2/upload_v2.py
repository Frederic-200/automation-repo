#!/usr/bin/env python3
"""Upload a finished v2 video (+ a post.txt with captions/sources) to Google Drive: "FredsDesk v2" / "YYYY-MM-DD - Title".

    python3 shorts/v2/upload_v2.py SCRIPT.json VIDEO.mp4 [--no-music-video VIDEO2.mp4]
Env: GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET, GDRIVE_REFRESH_TOKEN (same secrets as loops). The folder is found or created by name in My Drive.
"""
import json, os, re, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from loops import drive as D   # reuse the loops helpers (client, ensure_subfolder, upload)

FOLDER = "FredsDesk v2"


def post_text(s):
    p = (s.get("meta") or {}).get("post") or {}
    out = [s.get("title", ""), "", "TikTok caption:", p.get("tiktok_caption", ""), "", "YouTube caption:", p.get("yt_caption", ""), "",
           "Pinned comment:", p.get("pinned_comment", ""), "", "Hashtags: " + " ".join(p.get("hashtags", [])), "", "Sources:"]
    out += [f"- {x.get('name')}: {x.get('url')}" for x in p.get("sources", [])]
    v = s.get("v2", {}); m = s.get("meta", {}); a = s.get("audio", {})
    out += ["", f"World {v.get('world')} / palette {v.get('palette')} / voice {s.get('voice')} / music {a.get('music')} / hook {m.get('hook_type')} / ending {m.get('ending')}"]
    return "\n".join(out) + "\n"


def main():
    if len(sys.argv) < 3: print(__doc__); sys.exit(1)
    script = json.load(open(sys.argv[1])); videos = [sys.argv[2]]
    if "--no-music-video" in sys.argv: videos.append(sys.argv[sys.argv.index("--no-music-video") + 1])
    date = re.match(r"(\d{4}-\d{2}-\d{2})", os.path.basename(sys.argv[1]))
    day = date.group(1) if date else __import__("datetime").date.today().isoformat()
    drive = D.client()
    root = D.ensure_folder(drive, FOLDER) if not os.environ.get("GDRIVE_FOLDER_ID_V2") else os.environ["GDRIVE_FOLDER_ID_V2"]
    sub = D.ensure_subfolder(drive, root, f"{day} - {script.get('title', 'video')}")
    for v in videos: print("uploaded:", os.path.basename(v), D.upload(drive, sub, v, os.path.basename(v)))
    with tempfile.TemporaryDirectory() as t:
        f = os.path.join(t, "post.txt"); open(f, "w").write(post_text(script)); print("uploaded: post.txt", D.upload(drive, sub, f, "post.txt"))


if __name__ == "__main__":
    main()
