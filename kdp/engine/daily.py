#!/usr/bin/env python3
"""Daily KDP book run: pick the next theme in kdp/themes/queue -> validate -> build -> upload to
Google Drive -> add a row to the Catalog Tracker sheet -> move the theme to kdp/themes/done and log it.

Usage: python3 kdp/engine/daily.py [--theme FILE] [--no-upload] [--no-log] [--force]
Without --theme/--force it does nothing if a book was already made today (Manila date), so a
late scheduled run plus a manual re-run never make two books in one day.
Exit 1 (red run, GitHub emails you) if the queue is empty or the theme is invalid.

Env for upload: GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET, GDRIVE_REFRESH_TOKEN (same as the lesson video),
KDP_DAILY_FOLDER_ID (Drive folder "Tiny Comet Prints/01 Amazon KDP/Daily Books"),
KDP_TRACKER_ID (Google Sheet "Catalog Tracker"; optional).
"""
import csv
import datetime
import glob
import io
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KDP = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from build import build          # noqa: E402
from validate import validate    # noqa: E402

LOG = os.path.join(KDP, "catalog.json")
DEFAULT_DAILY_FOLDER = "1B3xZz0qPyqIu8Fv0IHksQrfLAWMMAoG_"
DEFAULT_TRACKER = "1mn26b1179fvBYYUFcTV-CW-YSdj4MW_fuuABnYoTy5Y"


def summary(text):
    s = os.environ.get("GITHUB_STEP_SUMMARY")
    if s:
        with open(s, "a") as f:
            f.write(text + "\n")


def fail(msg):
    print("::error::" + msg)
    summary("### Book skipped\n" + msg)
    sys.exit(1)


def manila_today():
    return (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).date().isoformat()


def drive_service():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build as gbuild
    creds = Credentials(token=None, refresh_token=os.environ["GDRIVE_REFRESH_TOKEN"],
                        client_id=os.environ["GDRIVE_CLIENT_ID"], client_secret=os.environ["GDRIVE_CLIENT_SECRET"],
                        token_uri="https://oauth2.googleapis.com/token",
                        scopes=["https://www.googleapis.com/auth/drive"])
    return gbuild("drive", "v3", credentials=creds, cache_discovery=False)


def mkfolder(drive, name, parent):
    meta = {"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent]}
    return drive.files().create(body=meta, fields="id,webViewLink").execute()


def upload(drive, path, parent, name=None, convert_to=None, mime=None):
    from googleapiclient.http import MediaFileUpload
    import mimetypes
    meta = {"name": name or os.path.basename(path), "parents": [parent]}
    if convert_to:
        meta["mimeType"] = convert_to
    m = mime or mimetypes.guess_type(path)[0] or "application/octet-stream"
    media = MediaFileUpload(path, mimetype=m, resumable=True)
    return drive.files().create(body=meta, media_body=media, fields="id,webViewLink").execute()


def update_tracker(drive, sheet_id, row):
    """Append a row to the Google Sheet tracker using Drive export/update (no Sheets API needed).
    Keeps whatever the user typed in the sheet (e.g. Status = Uploaded)."""
    from googleapiclient.http import MediaIoBaseUpload
    data = drive.files().export(fileId=sheet_id, mimeType="text/csv").execute().decode("utf-8")
    rows = list(csv.reader(io.StringIO(data)))
    rows = [r for r in rows if any(c.strip() for c in r)]
    if any(len(r) > 1 and r[1] == row[1] and r[0] == row[0] for r in rows):
        return
    rows.append(row)
    buf = io.StringIO()
    csv.writer(buf).writerows(rows)
    media = MediaIoBaseUpload(io.BytesIO(buf.getvalue().encode("utf-8")), mimetype="text/csv", resumable=False)
    drive.files().update(fileId=sheet_id, media_body=media).execute()


def upload_book(theme, today, out, facts, full_title):
    drive = drive_service()
    parent = os.environ.get("KDP_DAILY_FOLDER_ID") or DEFAULT_DAILY_FOLDER
    top = mkfolder(drive, f"{today} - {theme['title']}", parent)
    folder_url = top["webViewLink"]
    sub = {k: mkfolder(drive, k, top["id"])["id"] for k in
           ("1 Interior Pages", "2 Cover", "3 Final KDP Files", "4 Listing Kit")}
    for png in sorted(glob.glob(os.path.join(out, "pages", "*.png"))):
        upload(drive, png, sub["1 Interior Pages"])
    upload(drive, os.path.join(out, "contact_sheet.png"), sub["2 Cover"], "All pages - preview.png")
    upload(drive, os.path.join(out, "cover_front.png"), sub["2 Cover"], f"{theme['title']} - front cover preview.png")
    upload(drive, os.path.join(out, "interior.pdf"), sub["3 Final KDP Files"], f"{theme['title']} - interior.pdf")
    upload(drive, os.path.join(out, "cover.pdf"), sub["3 Final KDP Files"], f"{theme['title']} - cover.pdf")
    upload(drive, os.path.join(out, "listing.md"), sub["4 Listing Kit"], f"Listing Kit - {theme['title']}",
           convert_to="application/vnd.google-apps.document", mime="text/plain")
    tracker = os.environ.get("KDP_TRACKER_ID") or DEFAULT_TRACKER
    if tracker:
        try:
            update_tracker(drive, tracker, [today, full_title, "KDP paperback", "Ready to upload",
                                            str(facts["interior_pages"]), theme.get("price", "$7.99"), folder_url, ""])
        except Exception as e:   # tracker problems must not lose the book
            print("::warning::Tracker not updated: " + str(e))
    print("Uploaded to Drive:", folder_url)
    return folder_url


def main():
    args = sys.argv[1:]
    log = json.load(open(LOG)) if os.path.exists(LOG) else {"books": []}
    today = manila_today()
    if "--theme" not in args and "--force" not in args:
        done_today = [b for b in log["books"] if b.get("date") == today]
        if done_today:
            msg = f"A book was already made today ({today}): {done_today[-1]['title']}. Nothing to do."
            print(msg)
            summary("### Already done today\n" + msg)
            return
    if "--theme" in args:
        path = args[args.index("--theme") + 1]
    else:
        queue = sorted(glob.glob(os.path.join(KDP, "themes", "queue", "*.json")))
        if not queue:
            fail("No theme is queued. The weekly theme task must add kdp/themes/queue/NNN-slug.json files.")
        path = queue[0]
    theme = json.load(open(path))
    errs = validate(theme)
    if errs:
        fail(f"Theme {os.path.basename(path)} is invalid:\n- " + "\n- ".join(errs))
    if any(b["slug"] == theme["slug"] for b in log["books"]) and "--force" not in args:
        fail(f"Theme slug '{theme['slug']}' was already published. Give the theme a new slug.")

    out = os.path.join(KDP, "output", theme["slug"])
    shutil.rmtree(out, ignore_errors=True)
    print(f"Building: {theme['title']}", flush=True)
    facts = build(path, out)
    full_title = f"{theme['title']} {theme.get('cover_line', 'Coloring & Activity Book')}"
    folder_url = ""
    if "--no-upload" not in args:
        try:
            folder_url = upload_book(theme, today, out, facts, full_title)
        except Exception as e:
            msg = f"Drive upload failed: {type(e).__name__}: {str(e)[:600]}"
            print("::error::" + msg.replace("\n", " "))
            fail(msg + "\nThe book was built; download it from the run's kdp-book artifact.")

    if "--no-log" not in args:
        log["books"].append({"date": today, "slug": theme["slug"], "title": full_title,
                             "pages": facts["interior_pages"], "drive": folder_url, "status": "ready to upload"})
        with open(LOG, "w") as f:
            json.dump(log, f, indent=2)
        if os.path.dirname(os.path.abspath(path)) == os.path.join(KDP, "themes", "queue"):
            os.makedirs(os.path.join(KDP, "themes", "done"), exist_ok=True)
            shutil.move(path, os.path.join(KDP, "themes", "done", os.path.basename(path)))
    summary(f"### Book made: {full_title}\n- Pages: {facts['interior_pages']}\n- Drive: {folder_url or '(not uploaded)'}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        import traceback
        tb = traceback.format_exc().strip().splitlines()
        print("::error::Crash: " + " | ".join(tb[-6:]))
        raise
