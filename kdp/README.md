# Tiny Comet Prints - daily KDP coloring & activity book

Makes one print-ready Amazon KDP paperback per day, drawn entirely in code (no AI image models),
in the house style: thick even black outlines, cute rounded characters, wobbly hand-drawn frames,
bubbles and bushes; covers with a painted watercolour sky and chunky multicolour titles.
You upload each book to KDP by hand.

## How it runs
- **Daily 01:43 PH (GitHub Actions, `.github/workflows/kdp-daily.yml`)**: `kdp/engine/daily.py` takes the
  lowest-numbered theme in `kdp/themes/queue/`, builds the book, uploads it to Google Drive
  (`Tiny Comet Prints/01 Amazon KDP/Daily Books/<date> - <title>/` with subfolders 1 Interior Pages,
  2 Cover, 3 Final KDP Files, 4 Listing Kit), adds a row to the **Catalog Tracker** sheet, logs it in
  `kdp/catalog.json` and moves the theme to `kdp/themes/done/`. It refuses to make two books on one Manila date.
- **Weekly (Claude scheduled task)**: researches themes and adds the next 7 theme files following `THEMES_GUIDE.md`.
- Red run = nothing made (empty queue or invalid theme). Re-run from Actions > Daily KDP book > Run workflow.

## Each book
64 interior pages: title page, 30 activity pages (14 coloring in 5 layouts, 3 colour-by-number,
3 mazes, 2 counting, 2 dot-to-dot, 2 tracing, 2 spot-the-difference, matching, word search) each
followed by a blank back, and a thank-you/review page. 8.5 x 11 in, B&W, no bleed, white paper.
Cover: full wrap with 0.125 in bleed, spine computed from page count (0.002252 in/page).

## Uploading to KDP (about 15 minutes)
1. Open the day's Drive folder > 4 Listing Kit and keep it open.
2. KDP > Create > Paperback. Paste title, subtitle, author, description, keywords, categories.
3. Content: ISBN free KDP ISBN; Print options exactly as the listing kit says; upload
   `3 Final KDP Files/... - interior.pdf` and `... - cover.pdf` (choose "Upload a cover you already have").
4. Answer AI content: **Yes - images**. Launch Previewer, check, then set price and publish.
5. In the Catalog Tracker sheet, change Status to Uploaded.

## Local test
`pip install -r kdp/requirements.txt`, copy `kdp/fonts/*.ttf` to `~/.fonts` and run
`python3 kdp/engine/build.py kdp/themes/queue/001-farm-friends.json --out /tmp/book`.

## Code
`engine/draw.py` pen + scenery · `engine/chars.py` 39 characters · `engine/props.py` 40 props ·
`engine/pages.py` page types + book plan · `engine/cover.py` cover · `engine/build.py` one book ·
`engine/validate.py` theme checks · `engine/daily.py` daily run + Drive upload.
