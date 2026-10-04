# Daily AI Short Automation

Claude writes a script every day and commits it to `queue/YYYY-MM-DD.json`.
That push triggers GitHub Actions, which builds a vertical 1080x1920 video
(Edge TTS voice, AI images with motion or Pexels stock, burned-in captions)
and uploads it to Google Drive.

## Script format (`queue/*.json`)

```json
{
  "title": "Short title",
  "beats": [
    {"text": "Did you know ...?", "image_prompt": "...", "stock_query": "..."}
  ]
}
```

First beat opens with "Did you know...", last beat closes with
"For more videos like this, like and follow...".

## Repository secrets (Settings > Secrets and variables > Actions)

| Secret | What it is |
|---|---|
| `PEXELS_API_KEY` | Free key from pexels.com/api |
| `GDRIVE_CLIENT_ID` | Google OAuth client ID |
| `GDRIVE_CLIENT_SECRET` | Google OAuth client secret |
| `GDRIVE_REFRESH_TOKEN` | One-time OAuth refresh token (Drive scope) |
| `GDRIVE_FOLDER_ID` | ID of the Drive folder for finished videos |

Never commit keys to the repo.

## Run manually

Actions tab > "Render daily AI short" > Run workflow.
