#!/usr/bin/env python3
"""Upload a finished v2 video (+ a post.txt with captions/sources) to Google Drive: "FredsDesk v2" / "YYYY-MM-DD - Title".

    python3 shorts/v2/upload_v2.py SCRIPT.json VIDEO.mp4 [--no-music-video VIDEO2.mp4]
Env: GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET, GDRIVE_REFRESH_TOKEN (same secrets as loops). The folder is found or created by name in My Drive.
"""
import json, os, re, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from loops import drive as D   # reuse the loops helpers (client, ensure_subfolder, upload)

def upload_retry(drive, folder_id, path, name, tries=5):
    """Chunked resumable upload that survives dropped connections (big files got SSL EOF with the one-shot helper)."""
    import mimetypes, time
    from googleapiclient.http import MediaFileUpload
    last = None
    for attempt in range(1, tries + 1):
        try:
            media = MediaFileUpload(path, mimetype=mimetypes.guess_type(path)[0] or "application/octet-stream",
                                    resumable=True, chunksize=4 * 1024 * 1024)
            req = drive.files().create(body={"name": name, "parents": [folder_id]}, media_body=media, fields="id,webViewLink")
            resp = None
            while resp is None:
                _, resp = req.next_chunk(num_retries=5)
            return resp.get("webViewLink")
        except Exception as e:
            last = e
            print(f"upload attempt {attempt}/{tries} failed for {name}: {e!r}", flush=True)
            time.sleep(5 * attempt)
            try: drive = D.client()
            except Exception: pass
    raise last


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
    for v in videos: print("uploaded:", os.path.basename(v), upload_retry(drive, sub, v, os.path.basename(v)))
    with tempfile.TemporaryDirectory() as t:
        f = os.path.join(t, "post.txt"); open(f, "w").write(post_text(script)); print("uploaded: post.txt", upload_retry(drive, sub, f, "post.txt"))


if __name__ == "__main__":
    main()
