# FredsDesk daily AI lesson

A daily educational AI short (1080x1920, max 90s) generated entirely in code: animated canvas visuals, offline male voice (Kokoro `am_puck`), word-synced captions, synthesized sound effects, no music. Finished files land in Google Drive for manual upload.

## How it runs
- **Weekly (Claude scheduled task):** writes the next 7 lesson scripts into `queue/` following `WRITING_GUIDE.md`.
- **Daily 05:07 PH (GitHub Actions, `daily.yml`):** `engine/daily.py` picks the lowest-numbered uncovered script in `queue/`, validates it, renders MP4 + post text + preview, uploads all three to Drive as `Lesson NN - Title.*`, logs it in `curriculum/covered.json` and moves the script to `archive/`.
- **Watchdog 06:20 PH (Claude scheduled task):** if no lesson run happened today (GitHub sometimes skips scheduled runs), it starts one. `daily.py` refuses to publish twice on the same Manila date, so this is safe.
- A red run (invalid or missing script) means nothing was published that day; fix the script and re-run via Actions > Run workflow (optionally enter a lesson number).

## FredsDesk News (second daily video)
- **Daily 04:35 PH (Claude scheduled task "FredsDesk News script"):** finds one fresh AI story, checks it against 2+ sources, writes `news/queue/<date>-slug.json` per `news/WRITING_GUIDE.md`, validates it and pushes.
- **The push triggers `news.yml`** (backup cron 05:37 PH): `engine/news_daily.py` validates, renders (voice `af_heart`, 70-115 s), uploads `News YYYY-MM-DD - Title.*` to the same Drive folder, logs it in `news/covered.json` and moves the script to `news/archive/`. One news video per Manila day.
- No dates appear on screen (validator enforces it).

## Layout
`engine/` renderer, voice, audio, validator · `curriculum/lessons.json` the 100 lessons · `curriculum/covered.json` what's done · `queue/` scripts waiting · `archive/` used scripts · `samples/` extra example scripts.

## Secrets (already set from the old setup)
`GDRIVE_CLIENT_ID`, `GDRIVE_CLIENT_SECRET`, `GDRIVE_REFRESH_TOKEN`, `GDRIVE_FOLDER_ID`. (`PEXELS_API_KEY` is no longer used.)

## Go back to the old AI-news shorts
`git checkout legacy-ai-news` (branch holds the original pipeline untouched).

## Local test
`pip install -r requirements.txt && npm install`, download the Kokoro model files into `models/` (see `daily.yml`), then `python3 engine/build.py queue/002-*.json`.
