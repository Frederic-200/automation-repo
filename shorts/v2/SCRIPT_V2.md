# FredsDesk v2 videos: script format and writing guide

One video = one **world** (a = Type + Data, b = Paper cut-out, c = 3D token blocks). 60-90 s, voice-over, world-styled captions, foley sfx and a quiet music bed.
Everything is drawn by code (`shorts/v2/engine`, `worlds/`). Old formats (loops, format E) are untouched.

## Daily flow (what the scheduled task does)
1. `python3 shorts/v2/pick_world.py --date YYYY-MM-DD [--reroll N]` -> world, palette, voice, music, hook_type, ending (rotation is enforced, see below).
2. Write the script (this guide) into `shorts/v2/queue/YYYY-MM-DD-slug.json`, using the picked values.
3. `python3 shorts/v2/validate_v2.py <script> --date YYYY-MM-DD` -> must print OK. Fix errors; never loosen the validator.
4. `python3 shorts/v2/build.py <script> --out DIR --preview` then `python3 shorts/v2/novelty.py check DIR`. Exit 3 = too close to a recent video: `pick_world.py --reroll N+1`, rewrite the world/palette, repeat.
5. `python3 shorts/v2/build.py <script> --out DIR` (full render; world c is slow, ~15-20 min for 60-90 s). Also render `--no-music` if wanted.
6. After the video is accepted/posted: `python3 shorts/v2/novelty.py add DIR --date ... --slug ... --world ... --palette ... --extra '{"hook_type":..,"ending":..,"voice":..,"music":..}'` (the log is what rotation and novelty compare against: v2 videos only).

## Script format (see tests/example_valid.json)
```
title, v2{world,palette,number,kicker,footer}, hook (<= 8 words), voice, audio{music, sfx:"foley"}, say{}, end_tail 1.2,
scenes[{kind, lines[], params{}}], meta{slug, topic, kind:"concept"|omit, hook_type, ending, next_question?, post{...}, facts[], data_sourced?}
```
Scene kinds (same in every world): `headline` (lines[{text,font,color,size}], underline), `bars` (title, rows[{label,value 0-1,color,wobble}], gap, note),
`stat` (small, big, sub), `finale` (top, accent, mark neq|eq, bottom[]). `*word*` in narration marks a keyword (accent colour in captions).

**Beats (one focal point per moment).** `stage` scenes show ONE drawn prop at a time (book mic document cursor coin toggle arrow bubble lock magnifier warning dice gear check) with a label of at most 3 words; captions carry the sentence at the bottom.
`params.beats: [{cue: "word of the narration" | t: seconds, prop, label, move: pop|drop|slide, slot: c|l|r}]`. A new beat in a slot replaces the old one; l and r show two props side by side.
Rules: first beat within about 1 s, no gap over 3.6 s between beats, a beat near the end, props only from the library, generic metaphors only (no people, products or logos).
**Hook with beats.** Scene 0 stays a `headline` (text equals `hook`, so frame 0 is still the hook) and may also carry `params.beats`: a prop moves under the hook text from frame 0 (use headline size about 125 and `params.y` about 170 so the prop has room). Captions stay hidden for the first 2.6 s. World A only so far.

## Rules the validator enforces
- **Frame 0 is the hook.** Scene 0 is a `headline` whose text equals `hook` (<= 8 words). Hook type rotates: curiosity_gap, doing_it_wrong, pov, myth_bust, number_shock, comment_reply (never the same as either of the last 2).
  The hook must be answered in the video: no bait-and-switch.
- **Length 60-90 s** (estimate; real length is checked after voice), 8-16 scenes, no scene longer than ~9 s, sentences <= 14 words.
- **Pictures change every few seconds:** no kind twice in a row, none more than 3 times, at least 4 different kinds.
- **Re-hook in the middle third** (a scene with "but / however / here's the catch / turns out / until / instead"); the full answer comes late.
- **Ending alternates** loop / cliffhanger. Cliffhanger needs `meta.next_question`; tomorrow's video should answer it.
- **Comment-inviting:** the last spoken line is a question or says tell me / comment / which one; `post.pinned_comment` asks a question.
- **Numbers as words** in narration, no dates anywhere, no politics, no insults. Same pronunciation list as the old validator (never respell AI).
- **Facts:** 2 independent sites per claim (`meta.facts` + `post.sources`). Only `meta.kind: "concept"` (general how-it-works, no figures, names or dates) may skip sources. Bars need the note `ILLUSTRATION. NOT REAL DATA.` unless the numbers are sourced (`meta.data_sourced: true`).
- **Rotation vs the v2 log:** world differs from the last 2, palette not in the last 4 for that world, voice and music differ from the last video, ending alternates.

## Writing tips
- Open on the tension, not the topic: "Ask AI twice, get two answers" beats "How language models sample tokens".
- One idea per video. Say it in the hook, complicate it in the middle, resolve it late, then ask the viewer something.
- Short sentences, plain words, second person. Write for someone watching with the sound off: the headline/stat text must carry the point alone.

## Known limits (honest)
- Beats/stage exist in world A only; worlds B and C still need their prop renderers (paper cut-out, 3D extrusion). Kinds list, versus, counter, steps exist in all worlds. Motion and focus checks (frame-difference) are not built yet; only the beat-timing checks in the validator exist.
- Palette-only changes are small (novelty distance ~0.05 for the same script); real variety comes from the world and from different scene content.
- Music and sfx pools are small; foley variation comes from per-video seeds.
