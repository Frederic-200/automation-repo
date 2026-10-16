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

## 9. v2 retention rules (approved 2026-10-16, see PLAN_V2.md; the validator enforces them)
- `hook`: {"text": "An AI just *hacked* Chrome", "hold": 2.4}: 8 words or fewer, shown big from frame 0 (no fade-in) with an opening sound hit, and shown again in the last half second (loop). `*word*` highlights a word.
- Required meta: `hook_type` (number | callout | pov | question | this_ai_just | before_after | myth | countdown | guess | mid_action; not the same as yesterday), `template` (classic | chat_drop | headline_drop | split_screen | countdown_list | terminal | guess_quiz | meme_skit | kinetic_type; not used in the last 3 videos; "classic" only until the v2 templates are live), `look` (light | dark; not the same 3 videos in a row).
- Voices: am_fenrir or af_heart (not the same voice 3 videos in a row). Allowed acronyms differ per voice (shorts/pronounce.json).
- Every spoken sentence is 12 words or fewer. Length 15-35 s (format ranges in validate.py). First payoff by 5-8 s, a re-hook at about the middle ("But...", "Here is the catch"). A visual change every 1.5-2 s (the engine adds micro-motion automatically).
- Music genre and sound kit must differ from yesterday; scene types must not repeat more than half of any of the last 3 videos, and the opening scene type must differ from yesterday's.
- The outro is 1.5 s (`meta.outro_seconds` to override).

## 10. Visual recipe (approved 2026-10-16: layouts must not repeat)
After writing the script, run `python3 shorts/pick_recipe.py shorts/queue/<file>.json`. It writes `meta.recipe` (12 axes: layout, caption style/position, hook style/position, fonts, palette family, camera, finish, transitions, scene animation, sound) and sets `meta.caption_preset` to the recipe's caption style. Do not edit the recipe by hand and do not set style_overrides fonts/captions/camera/post. The validator requires a recipe that differs from each of the last 7 videos on 5+ of 12 axes, with a different frame layout and caption style than yesterday. Re-run the picker if validation fails.
- You still choose the palette (free-text `style`, light/dark via `meta.look`), `music_mood` and the content. The recipe changes the frame, typography, motion and finish around it.
- Optional script fields used by some layouts: `"chip": {"text": "Source: Google", "at": 3.0, "hold": 2.5}` (small source label), `"tag": "SECURITY"` and `"ticker": "FREDSDESK / DAILY AI / "` (letterbox bands). Chip text must match the sources.
- `caption_preset` may now be stack | typeon | slam | clean | off.
- After rendering, the build prints look-alike distances against the last 7 videos (shorts/fingerprints.json); a FLAGGED line means the structure is too close: mention it in the run report.

## 11. Story-made backgrounds (approved 2026-10-16, PLAN_V4.md; the validator enforces it from 2026-10-17)
Backgrounds are NOT picked from a list of worlds any more. Every scene's background comes from what that scene says. Scene `type` is `story` (or `chat`, `stat`, `echo` when you need those foregrounds; they can carry a `bg` block too and then get the story backdrop behind them). The old worlds (matrix, tokens, neural, fleet, grid, aurora, particles, ...) are retired as scene types, and sections 5 and 6 above are superseded where they mention them. Study `shorts/samples/B-chrome-story.json` and `A-meta-memory-story.json`: they show the format, never copy their wording, drawings or structure.

**Workflow:** (1) after the script lines are final, sketch each scene in one line: "what would a designer show here?" (2) draw 2-6 objects from THIS story in `meta.art` (3) write a `bg` block for every scene (4) `python3 shorts/pick_recipe.py <file>` (5) `python3 shorts/bg_preview.py <file>` and open the printed contact.png with Read: fix anything weak, off-story, cluttered or hard to read (6) validate (7) commit and push.

**Drawings (`meta.art`, `meta.art_style`):** `art_style` is one of flat | line | sticker | blueprint | paper, picked to suit the story's tone (sticker = playful/news, line or blueprint = technical, paper = warm/human, flat = bold/clean). Each drawing is `{"shapes": [...]}` on a 0..200 grid (centre 100,100), 1-40 shapes drawn in order. Shapes: `rect` (x,y,w,h,r), `circle` (x,y,r), `ellipse` (x,y,rx,ry), `line` (pts), `poly` (pts, closed), `path` (SVG path `d` with M L H V C S Q T A Z only), `text` (s <=14 chars, x,y,size). Colour `c` is a role: ink accent accent2 accent3 paper dark dim bg gold white red green blue (or #rrggbb). `fill:false` + `w` (stroke width; for rects use `sw`) makes an outline; `part` names a piece so a beat can move it (`"part":"shackle"` with pivot `pv`:[x,y]). Keep silhouettes simple and readable at 200 px. Draw things that carry the story: the product as OUR object (a browser window with a "CHROME" tab text), the threat (a bug), the thing at stake (coin, lock, shield, notebook, wall, podium), the people as simple busts.
- NEVER draw a real logo or a look-alike of one (no colour wheels, knots, sparkles, apples, swooshes), a real app interface, a real person or a copyrighted character. A company or product name appears only as text in our font on our own drawing. The validator rejects drawing names containing "logo" and similar.
- New objects for every video: do not reuse more than half of the last 3 videos' drawing ids.

**Scene direction (`bg` per scene):**
```
"bg": {"intent": "one line: what the viewer should feel or understand",
       "subject": ["browser", "bug"],                  // ids from meta.art
       "arrangement": "hero+stream",                   // hero scatter grid orbit stream stack split path explode ring tunnel wall none; combine with +
       "count": 8,                                     // instances for multi-item arrangements
       "motion": {"browser": "pop float", "bug": "crawl from left"},
       "beats": [{"on": "hacked", "do": "browser.glitch"}, {"on": "two hundred", "do": "browser.shake"}],
       "backdrop": {"kind": "scan", "speed": 0.8},     // mesh flow contour grid iso rays paper halftone scan ribbon rings stars tile; options speed scale density angle
       "texture_words": ["EXPLOIT"],                   // 0-4 faint story words
       "data": null, "focus": "center"}
```
- `arrangement` with `+`: the first part uses the first subject, the rest use the remaining subjects (hero+stream = browser big in the middle, bugs streaming across). `split` puts subject 0 left and 1 right; `orbit`/`ring` circle around the focus; `path` follows an S-curve; `explode` bursts from the centre; `stack` builds a pile; `tunnel` flies toward the viewer; `wall` is a dense pattern; `none` for data-only or foreground-only scenes.
- Motion words per subject (any mix): enter = pop slide drop crawl draw assemble fade zoom; living = float pulse wobble drift breathe blink swarm spin scan; leave = fall dissolve shrink wipe; add `from left|right|up|down`, `fast`, `slow`.
- Beats land on a spoken keyword (`on` matches the scene's keywords, the `*starred*` words) or at `t` seconds into the scene. `do` = `<subject>.<action>`: pop grow shake spin flash glow glitch shatter open[:part] part:<name> remove crack morph:<other drawing id>. Use 1-3 per scene, on the words that matter; shatter/crack act on the single hero.
- `data` (number scenes): `{"kind": "coins|bars|gauge|ring|line|compare|number", "value": 40, "prefix": "$", "unit": "K", "label": "$40K", "art": "coin", "fact": 2}`; `fact` is the index of the `meta.facts` entry that backs the number. The number must match the sources exactly. Never invent chart values: bars/line/compare only with real figures from the sources, otherwise use coins, ring or number.
- Keep the caption area clear: backgrounds work inside the middle band of the frame; do not rely on text or objects outside it.

**Variety rules the validator enforces:** every scene has a bg block with intent, subject, arrangement, motion and backdrop; at least 2 different arrangements, 3 different motion words and 3 different backdrops in a video; no arrangement+backdrop combination repeated inside the video or used in any of the last 7 videos; the opening scene differs from yesterday's opening on both arrangement and backdrop; a different recipe layout and caption style than yesterday (section 10). Format C (no voice): lean on drawings, beats at `t` times and story objects only; D (skit): `chat` scenes with `bg` backdrops behind them, people drawn as simple busts in the other scenes.
**Review before pushing:** open the contact sheet. Would a stranger understand the scene without the captions? Is anything cut off, black, tiny, overlapping the caption, or the same look as yesterday? Fix the drawing or the `bg` block, not the engine.
