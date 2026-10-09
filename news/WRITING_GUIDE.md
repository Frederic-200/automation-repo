# FredsDesk News: writing guide

One AI news story per day, told as a 70-115 second vertical short that teaches as well as informs. Every visual is drawn in code (no stock footage, no logos, no photos). The video lands in Google Drive as `News YYYY-MM-DD - <Title>.mp4` (+ post text + preview) and the user posts it by hand.

## 1. Pick the story
- AI news from the **last 48 hours** that a curious non-expert would stop scrolling for: a surprising capability, a big number, a clash, a first, a risk, something that changes how people work or live.
- One story only. Go deep, not wide.
- **Verify every fact in the script with at least 2 independent sources** (the company's own post/repo/paper counts as one; a reputable outlet as another). If two sources disagree, use the cautious version or drop the claim. Never invent quotes, numbers or names. Quotes must be exact and attributed.
- Not already covered: check `news/covered.json` (titles and hooks) and `news/archive/`.
- Avoid stories that are only rumours, single-source leaks, or personal attacks on people.

## 2. Shape (scene order)
1. `breaking`: opener. Narration **must start with "Did you know"**. 2-3 short headline lines on screen, one accent line.
2. `story`: what happened, in plain words (source, headline, 1-3 short facts).
3. 1-3 explainer scenes: the **concept behind the story**, taught simply (`concept`, `stat`, `compare`, `flow`, `timeline`, `quote`, `chat`, `anatomy`, `network`, `map`, `analogy`).
4. `engage`: exactly one, roughly in the middle. A creative like-and-share line tied to the story (never the same wording twice in a row).
5. More explainer scenes if needed, then `why`: why it matters (2-3 points).
6. `takeaways`: 2-3 takeaways.
7. `sources_end`: last scene. Says where it was checked and asks to **follow** (narration must contain "follow").

Narration total **170-300 words** (about 2.6 words per second; aim for 220-270 = 85-110 s). The build fails above 118 s of voice.

## 3. No dates on screen
The user does not want dates in the video. On-screen text (every prop except narration and cues) must not contain a month + day, a year (19xx/20xx), an ISO date, or "today/yesterday/tomorrow". The validator rejects them. Narration may say when something happened ("on Tuesday", "this week"). For `timeline` labels use words like "Before", "Then", "Now", "Next".

## 4. File
`news/queue/<Manila date>-<slug>.json` where the date is `TZ=Asia/Manila date +%F`. Example: `samples/news-2026-10-09-openai-722-math-papers.json` (read it first; it is a complete, working script).

```json
{"kind": "news", "date": "2026-10-10", "title": "...", "voice": "af_heart", "speed": 1.04, "max_duration": 118,
 "say": {"FredsDesk": "Freds Desk"},
 "ticker": ["3-6 short real AI headlines from this week, max ~45 chars each"],
 "sources": [{"name": "Outlet or org", "url": "https://..."}, {"name": "...", "url": "https://..."}],
 "scenes": [ ... ],
 "post": {"title": "...", "description": "...", "hashtags": ["#AI", "#AINews", "..."], "pinned_comment": "a question to the viewer"}}
```
- `voice` is always `af_heart` (the news voice; lessons use a different one).
- `say`: spoken-word fixes for brand names or acronyms the voice reads badly (e.g. "ChatGPT": "Chat G P T"). **Never add "AI"**: the voice already says it right, and "A I" is read as "uh-eye".
- Spell numbers as words in narration when they should be read aloud ("seven hundred twenty-two"); on-screen props use digits ("722").
- `ticker` items must be real, current AI headlines you saw while researching (no dates in them).
- `post.hashtags`: 5-7 tags, include #AI and #AINews. `post.title` <= 90 characters.

## 5. Scene types
News scenes (all take `narration` and optional `cues`):

| type | required props | optional | cues |
|---|---|---|---|
| breaking | lines[2-3], accent (index) | kicker (default "DID YOU KNOW?"), source ("OpenAI · The Verge") | l1, l2, l3, source |
| story | source, headline (<=110 chars), facts[1-3] (short) | | headline, f1..f3 |
| quote | text (exact quote), who | role | quote, who |
| timeline | events[2-4] {when (no dates), what} | title | e1..e4 |
| why | points[2-3] | icons[] | p1..p3 |
| engage | line (like/share call, <=60 chars) | sub | like, share |
| takeaways | points[2-3] | | p1..p3 |
| sources_end | sources[1-3] (short names shown on screen) | | sources, follow |

Reused lesson scenes (props in `/WRITING_GUIDE.md`, section "Scene types and props"): `concept`, `stat`, `compare`, `flow`, `chat`, `anatomy`, `map`, `network`, `analogy` (LEGO bricks only when the analogy really is about bricks).
Icons: chat search db brain doc gear user check spark cloud bolt target.

## 6. Cues
`cues: {"name": "word"}` makes that visual beat land when the narrator says the word (prefix match on the lowercase word; `"=word"` exact; `"word#2"` the 2nd time). Use words that really occur in that scene's narration, and remember a word like "three" may appear earlier in the same scene (then use `"three#2"`).

## 7. Check before you commit
`python3 engine/validate_news.py news/queue/<file>.json` must print OK. Read the narration aloud in your head: it should be clear to someone who knows nothing about AI, punchy, and accurate.
