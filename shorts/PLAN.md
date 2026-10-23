# FredsDesk Shorts: approved plan (written by Opus, executed by Sonnet)

Status: APPROVED by the user on 2026-10-15. Follow this file step by step. If anything here is unclear, impossible, or contradicted by what you find in the repo, STOP and ask the user. Do not improvise, do not change scope.

Repo: Frederic-200/automation-repo. Backup of the old setup: branch `legacy-v1` (also `legacy-ai-news`). Old workflows `news.yml` and `daily.yml` are DISABLED in GitHub (state disabled_manually). `kdp-daily.yml` is paused on purpose: do not touch it.

## 1. Goal
One AI-related vertical short per day, built from what is trending now, fully automatic, posted manually by the user to TikTok, YouTube Shorts and FB Reels. Output may be wild and engaging as long as it is truthful, based on the current trend, and within the content rules.

## 2. Content rules (the validator must enforce what can be checked mechanically)
- Topic must be AI-related and current (news or trend from the last ~48 h). Format E (PLAN_V5.md): a common, evergreen AI question is fine.
- Every factual claim verified in at least 2 independent sources (the company's own post/paper + a reputable outlet, or two outlets). If sources disagree, use only the cautious common part or leave it out. Never invent facts, numbers or quotes. Attribute claims ("Google says", "Anthropic estimates").
- Companies, products and public figures may be named in factual statements only. No insults, speculation about people, or anything we could not defend as true.
- No politics, no election content, no mocking or disparaging companies, no private individuals, no logos or copyrighted characters, no lyrics.
- Skits and memes must be labeled as skits in the pinned comment and may only use real facts for any statistic.
- No dates on screen. Numbers in narration written as words ("thirty two thousand").
- Voice: am_fenrir, always. Narration is plain English words. NEVER respell "AI", "UK", "TV", "API" etc. (see section 6).

## 3. Formats (rotate; never the same format 3 days in a row; at least one C per week)
| Id | Format | Length | Audio | Notes |
|---|---|---|---|---|
| A | Explainer: explain the trending thing simply | 35-45 s | voice, stack captions, light music | hook, concept, caveat, takeaway |
| B | Breaking hit: big factual news | 25-35 s | voice, fast cuts, punchy music | numbers on screen, "X says" attribution |
| C | Pure animation | 15-25 s | music + SFX, voice track muted (`"silent": true`) | text lands on beats; no factual claims; tied to a visual/vibe trend |
| D | Skit/meme | 25-35 s | voice, chat bubbles, comedic SFX | based on a real current trend or survey |
Hard cap 60 s including the 3 s outro. Retention rules: hook in the first second, change the picture every 3-5 s, payoff by 10-15 s.

## 4. Pipeline (all code, no model after the script is pushed)
1. 02:35 PHT: scheduled Claude task (model `claude-opus-5-5`, one task, fresh session) researches, verifies, writes `shorts/queue/<date>-<slug>.json`, runs the validator, pushes to `main`.
2. Push of `shorts/queue/*.json` triggers `.github/workflows/shorts.yml` which renders (about 10-12 min) and uploads to Google Drive folder "FredsDesk Shorts" (new folder, secret `GDRIVE_FOLDER_ID_SHORTS`). Target: files in Drive by about 03:05 PHT.
3. Backup trigger inside the same workflow: GitHub `schedule` at 19:20 UTC (03:20 PHT, off the hour). It builds today's script only if it exists and has not been published (check `shorts/covered.json`). No Claude watchdog (it used usage for nothing).
4. Outputs per day (one Drive folder, flat): `<date> <title> - YT+Reels.mp4` (voice + music), `<date> <title> - TikTok (add sound).mp4` (voiced formats only, no music), `<date> <title> - post text.md`, `<date> <title> - preview.jpg`. Format C has one video only: `<date> <title> - all platforms.mp4`.
5. `shorts/covered.json` is updated by the workflow (date, format, topic, slug) so rotation and no-repeat work. The daily task reads it first.
Pin runners: `ubuntu-24.04`, Node 22 (GitHub retires `ubuntu-latest` -> 26 on 2026-10-19 and Node 20). Reuse the Chromium/ffmpeg/Kokoro-cache steps from `.github/workflows/news.yml`; add `fluidsynth` and `fluid-soundfont-gm` (apt) for music. `scripts/upload_drive.py` is reused unchanged except the folder id env var.

## 5. Engine (vendor into `shorts/`, do not rely on the session cache)
Copy these working files from the dev branch `shorts-dev` (they are the tested versions):
- `shorts/kit/`: the video-kit (scripts + engine) with three patches: (a) caption mode `stack` (phrase-sized blocks, size by importance, accent word, color flip, clears at phrase end; config `caption.stack_y`, `stack_h`, `stack_size`), (b) caption mode `off`, (c) `"silent": true` in make_video.py (mute voice but keep timings).
- `shorts/kit/scenes_fredsdesk.js`: custom worlds `neural`, `fleet`, `chat`, `tokens`, `stat` (counter with decimals), `haunt`, `echo` (giant outlined keyword, optional `params.scramble`). Reference it with `"scenes_custom": "scenes_fredsdesk.js"` (build_daily.py swaps in the absolute path).
- Text toolkit (user-approved 2026-10-15, chosen per video by `meta.caption_preset`, mixed across days; never the same preset 3 videos in a row): `stack` (Archivo Black phrase blocks, the v2 look; best for A/B), `typeon` (Anton, letters pop in, keyword label boxes, word swap; best for D and punchy hooks), `off` (C). Extras used by content: `stat` counter, `echo` + `scramble` payoff word, `card` transition (1-2 per video max, on a hard pivot). Quote marks around type-on text were NOT implemented.
- `shorts/brand/`: `brand.json` (colors navy #0f4866, teal #32a788, geometry, CTA text, outro length), `icon_nocursor.png`, `cursor.png`, `word.png`, `logo_original.png`.
- `shorts/outro/outro.js`, `outro_build.py`, `append_outro.py`.
Style for videos: the preset (`caption_preset`) expands to `style_overrides` in `build_daily.py`; per day only free-text style cues are written (neon, blueprint, swiss, vhs, terminal, aurora...). Never end a video with the diamond `burst` world: the last scene must be a non-diamond world (`type`, `particles`, `aurora`, `neural`...). Set `"end_tail": 0.5` because the outro follows.
Music moods: lofi, gentle, upbeat, synthwave, epic, trap. Pass the same mood to the outro (`--mood`) so the chime is in key.

## 6. Pronunciation (the "AI" bug)
Cause: respelling "AI" as "A I" in `say` made Kokoro read it as the word "a" + "eye". Plain "AI" is read correctly (ay-eye). Verified with speech recognition. Rules:
- `say` is empty by default. Only add entries listed in `shorts/pronounce.json` (tested ones). Initially: nothing needed; "UK", "TV", "API", "GPT", "LLM", "AGI", "OpenAI" are fine as written.
- Validator: for each narration line, phonemize with Kokoro (`kokoro().tokenizer.phonemize(text,'en-us')`) and fail if an uppercase acronym is spoken as a word-like sound or if a `say` value is not in `pronounce.json`.
- After voice generation run the aligner ASR on lines containing acronyms; report mismatches in the run summary.

## 7. Outro (3 s, SFX only, appended automatically to every video)
Built from the user's logo (masks extracted from the original image). Background and palette come from the video's own style (`style.json`); logo colors adapt (dark bg: light teal icon, white "Freds", teal "Desk"; light bg: original navy/teal). APPROVED by the user as final, reuse on every video. No glows, no diamond. Timeline: 0.0 whoosh; 0.3-1.0 desk draws on (solid teal pen dot) with shimmer; 1.0-1.3 monitor boots (flicker, blip); 1.2-1.55 cursor curves in (teal), clicks at 1.55 with three expanding teal wave rings (brand teal, identical on every video) and three ripple bloops; 1.7-2.3 "FredsDesk" letters rise with ticks; 2.3 chime; 2.3-2.7 "Follow for daily AI" types in with blinking cursor; 2.55-3.0 light sweep; holds clean. Joined to the video with a 0.3 s slide transition (`append_outro.py`); audio balanced to the video body (about -16 LUFS, true peak below -2 dBTP).
Run: `outro_build.py --style-work <video work dir> --out <dir> --mood <mood>` then `append_outro.py main.mp4 outro.mp4 final.mp4`.

## 8. Daily task spec (create with the scheduler, then verify it appears enabled)
- Name "FredsDesk Shorts daily script", cron `CRON_TZ=Asia/Manila 35 2 * * *`, model `claude-opus-5-5`, environment as the existing tasks.
- Prompt must: attach+clone the repo once (push access); get today's date in Asia/Manila; stop if today's script or covered entry exists; read `shorts/WRITING_GUIDE.md`, `shorts/covered.json`, last 7 entries (pick the format by the rotation rules); research 6-10 searches (extended where useful) for AI news/trends of the last 48 h and which AI formats are working on TikTok/Shorts/Reels now; choose one topic; verify every fact with 2 sources; write the script; run `python3 shorts/validate.py <file>` until OK; commit only that file; push; (optional) wait for the render and report the run id and outcome; final message 2-3 lines.
- Never commit a script that fails validation. Never ask questions (unattended).

## 9. Phases and acceptance checks
Phase 1 (DONE, review video approved by the user 2026-10-15): old workflows disabled, backup branch, stack captions, custom worlds, 4 sample formats, outro, AI pronunciation fix, review video with outro. The user must approve the review video before Phase 2.
Phase 2 (Sonnet; status: built and tested locally, see git log): vendor the engine into `shorts/` from `shorts-dev`; write `shorts/WRITING_GUIDE.md` (formats, rules, schema, examples from `shorts/samples/`), `shorts/validate.py` (schema, content rules, length, format rotation, pronunciation), `shorts/build_daily.py` (pick script, render, outro, post text, upload, log), `.github/workflows/shorts.yml`, `shorts/pronounce.json`, `shorts/covered.json`. Create the Drive folder "FredsDesk Shorts"; ask the user to add the secret `GDRIVE_FOLDER_ID_SHORTS` (you cannot). One manual test run (workflow_dispatch, upload true). Acceptance: run green; MP4 plays, 9:16, 1080x1920, 30 fps, 26-60 s including outro, LUFS -14 to -17, true peak below -1.5; no-music file present for voiced formats; post text present; files in the Drive folder; `covered.json` updated.
Phase 3 (Sonnet): create the daily task (section 8); update the skill/notes; delete nothing; tell the user how to disable. Check the first live day (script pushed by ~02:50, files in Drive by ~03:05) and report.

## 10. Rules for the implementer
- Do not modify `main` outside `shorts/` and `.github/workflows/shorts.yml`. Do not touch KDP files or the disabled workflows.
- Commit messages end with the attribution lines required by the session.
- Keep every change small and verify it (contact sheet for visuals, ASR for pronunciation, loudnorm for audio) before moving on.
- When a check fails twice, stop and report instead of working around it.
