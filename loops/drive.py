#!/usr/bin/env python3
"""FredsDesk Loops - Google Drive helper (same OAuth secrets as the other FredsDesk workflows).

Env: GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET, GDRIVE_REFRESH_TOKEN
     GDRIVE_FOLDER_ID_LOOPS  (optional: upload into this folder id; if empty the folder named FOLDER_NAME is found or created)
Each day gets its own subfolder inside the main folder ("YYYY-MM-DD - Title") holding that day's 4 files.
"""
import mimetypes, os

FOLDER_NAME = "FredsDesk Loops"


def client():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials(token=None, refresh_token=os.environ["GDRIVE_REFRESH_TOKEN"], client_id=os.environ["GDRIVE_CLIENT_ID"],
                        client_secret=os.environ["GDRIVE_CLIENT_SECRET"], token_uri="https://oauth2.googleapis.com/token",
                        scopes=["https://www.googleapis.com/auth/drive"])
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def ensure_folder(drive, name=FOLDER_NAME):
    """id of the folder called `name` in My Drive root (created if missing; never creates a duplicate if one exists)."""
    explicit = os.environ.get("GDRIVE_FOLDER_ID_LOOPS", "").strip()
    if explicit: return explicit
    q = f"name = '{name}' and mimeType = 'application/vnd.google-apps.folder' and 'root' in parents and trashed = false"
    found = drive.files().list(q=q, fields="files(id,name)", pageSize=10, spaces="drive").execute().get("files", [])
    if found: return found[0]["id"]
    return drive.files().create(body={"name": name, "mimeType": "application/vnd.google-apps.folder"}, fields="id").execute()["id"]


def ensure_subfolder(drive, parent_id, name):
    """id of the subfolder `name` inside `parent_id` (found, or created; a re-run never makes a duplicate)."""
    safe = name.replace("\\", " ").replace("'", "")
    q = f"name = '{safe}' and mimeType = 'application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed = false"
    found = drive.files().list(q=q, fields="files(id,name)", pageSize=10).execute().get("files", [])
    if found: return found[0]["id"]
    return drive.files().create(body={"name": safe, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]}, fields="id").execute()["id"]


def existing_names(drive, folder_id):
    names, token = set(), None
    while True:
        r = drive.files().list(q=f"'{folder_id}' in parents and trashed = false", fields="nextPageToken, files(name)", pageSize=200, pageToken=token).execute()
        names |= {f["name"] for f in r.get("files", [])}; token = r.get("nextPageToken")
        if not token: return names


def upload(drive, folder_id, path, name):
    from googleapiclient.http import MediaFileUpload
    media = MediaFileUpload(path, mimetype=mimetypes.guess_type(path)[0] or "application/octet-stream", resumable=True)
    f = drive.files().create(body={"name": name, "parents": [folder_id]}, media_body=media, fields="id,webViewLink").execute()
    return f.get("webViewLink")
