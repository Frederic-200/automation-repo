# FredsDesk Shorts: writing guide (read this fully before writing today's script)

You write ONE script file per day: `shorts/queue/<YYYY-MM-DD>-<slug>.json` (date = today in Asia/Manila, slug = lowercase words with dashes). Code renders it. Check it with `python3 shorts/validate.py <file>` until it prints `OK`, then commit only that file. Never ask questions: nobody is watching.

The approved plan is `shorts/PLAN.md` (rules there win if this guide seems to disagree).

## 1. Pick the day's format
Read `shorts/covered.json` (oldest first). Rules the validator enforces: never the same format 3 days in a row; at least one C in every 7 videos; never the same topic as the last 7 videos; never the same caption preset 3 videos in a row.

| Format | Use when | Length (before 3 s outro) | Voice |
|---|---|---|---|
| A Explainer | a concept or study is trending and needs 30 s of explaining | 35-45 s, about 90-115 words | voice + music |
| B Breaking hit | a big, verifiable announcement or number | 25-35 s, about 65-90 words | voice + music |
| C Pure animation | a vibe/visual trend, holiday, meme mood; NO factual claims | 15-25 s | music + SFX only (`"silent": true`), text lands on beats |
| D Skit / meme | a relatable trend or real survey that works as a mini dialogue | 25-35 s, about 55-80 words | voice + chat bubbles |

Prefer the format that matches what is trending: breaking news -> B; confusing hot topic -> A; relatable AI-at-work/school behavior -> D; quiet news day or holiday -> C.

## 2. Find the topic (research)
6-10 searches (use extended mode where it helps). Look for: AI announcements/releases/research/outages/regulation-free news of the last 48 h, and what AI content is working now on TikTok/Shorts/Reels. Pick one topic that is AI-related, current, and explainable in 30 s with a strong first second. Skip anything political (no elections, governments' politics, wars), anything about private individuals, and anything you cannot verify.

## 3. Truth rules (not negotiable)
- Every factual claim needs 2 independent sources (the company's own post/paper + a reputable outlet, or two outlets), listed in `meta.facts` with the source indexes. If sources disagree, use only the cautious common part or drop the claim.
- Attribute: "Google says", "Anthropic estimates". Never invent facts, numbers or quotes. A number on screen must match the sources exactly (rounded numbers must say "about").
- Companies, products and public figures may be named in factual statements only. No insults, speculation about people, mocking companies, logos, copyrighted characters or lyrics. No politics.
- Skits (D) are labeled "skit" in the pinned comment and use real facts for any statistic. The pinned comment states the limits of the claim (what the number does and does not mean).
- No dates on screen or in narration. Numbers in narration are written as words ("thirty two thousand"); on-screen numbers go in `params` (stat world).
- Format C makes no factual claims.

## 4. Voice and pronunciation
Voice is always `am_fenrir`. Write plain English. NEVER respell "AI" (not "A I"). `say` stays `{}` unless `shorts/pronounce.json` lists it (`EU` -> `E.U.`). Allowed acronyms are listed there (AI UK US TV API AGI GPT GPU CPU CEO); any other ALL-CAPS word fails validation: write "language model" not "LLM", "Nvidia" not "NVIDIA". Use `*asterisks*` around 1-3 keywords per scene; they drive captions, camera hits and sound.

## 5. Script schema (copy a sample in `shorts/samples/`)
```
{"title": "...", "style": "<free-text look cues>", "voice": "am_fenrir", "music": true, "music_mood": "lofi|gentle|upbeat|synthwave|epic|trap",
 "seed": 44, "max_seconds": 34, "end_tail": 0.5, "scenes_custom": "scenes_fredsdesk.js", "say": {},
 "scenes": [{"act": "problem|build|turn|payoff|button", "type": "<world>", "params": {...}, "lines": ["Sentence with a *keyword*."]}],
 "meta": {"format": "A|B|C|D", "slug": "same-as-file-name", "topic": "short topic", "caption_preset": "stack|typeon|off",
          "facts": [{"claim": "...", "sources": [0, 1]}],
          "post": {"title": "<=100 chars", "tiktok_caption": "<=300 chars with hashtags", "yt_caption": "<=400 chars, ends with Follow FredsDesk for daily AI",
                   "pinned_comment": "caveats and where the numbers come from", "hashtags": ["#AI", "... 5-12, must include #FredsDesk"],
                   "sources": [{"name": "Outlet, headline", "url": "https://..."}]}}}
```
Always `end_tail: 0.5` and `scenes_custom: "scenes_fredsdesk.js"`. Do NOT set `style_overrides` fonts/captions: `caption_preset` does it. C: `"silent": true` and `lead` 0.2 is fine; lines still define the on-screen text timing. `style` examples: "neon dark, cyan accent, hype energetic", "swiss playful light, yellow accent, funny", "blueprint dark navy, teal accent, calm explainer", "storm dark purple, orange accent, spooky playful". Vary the look from the previous days.

## 6. Text styles: mix them (decide by content, rotate by day)
`meta.caption_preset` chooses the whole video's text style:
- `stack` (Archivo Black phrase blocks, size by importance, accent word): best for A and B, long or number-heavy lines, calm explainers.
- `typeon` (Anton caps, letters pop in, keyword label boxes, word swap): best for D skits, punchy hooks, short sentences, hype/funny tone, memes.
- `off`: only for C when the scenes carry the text.
Same preset never 3 videos in a row. Inside a video also mix the extras:
- `stat` world: counter + bars for a number that matters (`params`: `values` [0.3, ...] bar heights, `number`, `suffix`, `prefix`, `decimals`). Use for the headline number.
- `echo` world: giant outlined keyword behind the line (`params.word`, `params.scramble: true` makes the keyword letters scramble then lock in; use for a payoff word). Good last-but-one scene.
- `chat` world: chat bubbles for D (`params.names` ["A","B"], `params.bubbles` [{"who":"a|b","text":"...","at":0.2}], "..." typing bubble).
- `tokens`, `neural`, `fleet` (`count`), `haunt` (`ghosts`) for AI-themed visuals; built-in: matrix, grid, blueprint, aurora, particles, type, storm, pressure, liquid, tunnel, shapes, paper, bars. Change the world every scene, never end with `burst` (the diamond).
- Transitions: per scene `params.transition` = liquid|iris|whip|glitch|pixel|flash|card. Use `card` (the shrinking card drop) on 1-2 hard turns per video max (a number reveal, a twist), where the story pivots; use whip/glitch for fast news, liquid/iris for calm.
Retention: hook in the first second (strongest line, motion); change the picture every 3-5 s; payoff by 10-15 s; end on a short button line. Last scene types that work: `type`, `particles`, `aurora`, `neural`, `echo`.

## 7. Post text
The workflow writes the post-text file from `meta.post`: TikTok caption (short, with hashtags), YouTube Shorts/Reels caption, pinned comment (caveats + provenance, "skit" for D), hashtags, sources. The outro ("Follow for daily AI") is added automatically: do not write a call to action in the narration other than at most "Follow for more".

## 8. Final steps
1. `python3 shorts/validate.py shorts/queue/<file>.json` until `OK` (fix every ERROR; read WARN).
2. `git add shorts/queue/<file>.json` only, commit "Shorts script <date> <slug>" (with the attribution lines), `git pull --rebase origin main`, `git push origin main`.
3. The push triggers the render (about 12 min) and the Drive upload. If you are asked to wait, check the workflow run `Daily FredsDesk Shorts`.
