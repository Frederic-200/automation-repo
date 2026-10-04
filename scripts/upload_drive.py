#!/usr/bin/env python3
"""Upload a video to a Google Drive folder using an OAuth refresh token.

Env: GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET, GDRIVE_REFRESH_TOKEN, GDRIVE_FOLDER_ID
Usage: python scripts/upload_drive.py output/video.mp4 "2026-10-05 - Title.mp4"
"""
import os
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def main():
    path, name = sys.argv[1], sys.argv[2]
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GDRIVE_REFRESH_TOKEN"],
        client_id=os.environ["GDRIVE_CLIENT_ID"],
        client_secret=os.environ["GDRIVE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/drive.file"],
    )
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)
    meta = {"name": name, "parents": [os.environ["GDRIVE_FOLDER_ID"]]}
    media = MediaFileUpload(path, mimetype="video/mp4", resumable=True)
    f = drive.files().create(body=meta, media_body=media, fields="id,webViewLink").execute()
    print("uploaded:", f.get("webViewLink"))


if __name__ == "__main__":
    main()
