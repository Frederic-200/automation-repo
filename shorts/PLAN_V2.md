# FredsDesk Shorts v2: retention and uniqueness plan (approved by the user 2026-10-16)

Status: APPROVED. Replaces the look/pacing parts of PLAN.md; content rules (PLAN.md section 2) are unchanged. The daily task "FredsDesk Shorts daily script" is PAUSED until Phase A and template batch 1 are approved by the user.

## 1. Problem (user's own stats on FB Reels and YouTube Shorts)
90% leave within 3 s, 7% leave later, 3% finish. Causes in our pipeline: frame 0 is an abstract animation with the caption only at ~0.3 s; one engine look every day (camera hits, caption position, sound kit, music, voice); abstract visuals only; a visual change every 3-5 s; 30-45 s length with the payoff at 10-15 s; 3 s outro counts against completion; no loop or reason to rewatch.
Targets after 2-3 weeks: stay past 3 s 45-60% (now ~10%); average view 60%+; finish 20-30% (now 3%).

## 2. Hook (0-3 s)
- At 0.0 s the screen shows: hook text (8 words or fewer, huge, high contrast), a visual already moving (no fade-in, no logo, no intro), an opening sound hit from the template's sound kit.
- Speech starts by 0.3 s in voiced videos (Emplifi 2026: speech in first 3 s = +11.7% 3 s and +24.7% 10 s retention on Facebook Reels).
- Hook types (rotate, never the same two days running): number shock, direct callout ("If you use ChatGPT..."), POV, unanswerable question, "This AI just...", before/after, myth bust, countdown promise, guess challenge, mid-action open.
- Daily task writes 3 hooks, scores each (specific, curiosity gap, stakes, talks to "you"), keeps the best. Open loops only if the video delivers.

## 3. Middle, length, ending
- A visual change every 1.5-2 s (cut, zoom punch, text swap, pop-in, color shift); engine auto-adds a micro motion if nothing happens for 1.8 s. Below 1.2 s is noise, above 2.5 s loses people.
- First payoff by 5-8 s; re-hook at 40-50% ("But here's the catch"); captions 2-4 words, visible from second 1; narration lines 12 words or fewer, voice speed 1.05-1.15.
- Length: default 18-30 s, hard cap 35 s (quiz/meme/kinetic 15-22 s; chat/news/split 20-28 s; countdown list 25-35 s).
- Loop ending: last frame/line leads back into the hook; audio crossfades for a seamless replay.
- Outro (decision D1): 1.5 s version for voiced templates; none for loop templates (T6, T8), which get a small FredsDesk corner watermark instead.

## 4. Eight templates (own layout, motion, typography, palette family, sound kit, music genre, voice, length)
Per-video seed varies the layout (left/right, light/dark, positions). Script field `meta.template`. All UI is our own generic design: no real app logos, no copies of real chatbot interfaces; company names only as text in factual statements.
| # | Template | Use for | Voice | Length |
|---|---|---|---|---|
| T1 | Chat Drop: generic phone, notification drops the hook at 0.0 s, messages pop in with typing dots, zoom + highlighter | chatbot features, prompt tips, funny AI behavior | af_heart or none | 20-28 s |
| T2 | Headline Drop: news cards slam in, BREAKING strip, ticker, counting number, source chip | breaking news, launches, big numbers | am_fenrir | 20-28 s |
| T3 | Split Screen: top/bottom split, slider wipe, scoreboard, winner glows | before/after, old vs new, human vs AI | am_fenrir or af_heart | 20-28 s |
| T4 | Countdown List: top progress bar, big numbers 3-2-1, icon cards, #1 gets a bigger reveal | "3 AI tools that...", prompt lists | af_heart | 25-35 s |
| T5 | Terminal: self-typing prompt, streaming output, highlighted lines | dev tools, agents, open-source, coding AI | am_fenrir (lower) | 20-28 s |
| T6 | Guess Quiz: A/B(/C) cards, 3 s countdown ring, "comment your answer", reveal, loops into next question | real or AI, trivia | af_heart | 15-22 s |
| T7 | Meme Skit: two original drawn characters, bubbles, reaction zooms, freeze-frame, "Me:/AI:" captions | relatable AI-at-work/school skits | both voices | 15-25 s |
| T8 | Kinetic Type: text only cut to the beat (smash, stretch, flip, scramble, stack); 7-12 s micro loop variant | hype stats, official-post quotes, vibe/holiday | none (user adds trending sound) | 7-20 s |
Existing toolkit reused: typeon/stack caption looks per template, `stat` counter (T2, T4), `echo`+scramble (T8), `card` transition (T2, T4). Original mascot "Desk bot" (decision D2) appears in T1, T3, T6, T7 only.

## 5. Audio
- Voices: am_fenrir (news, terminal, hype), af_heart (chat, list, quiz, explainers), both for skit dialogue, none for kinetic/text-only. Run the same TTS + ASR acronym test on af_heart and add results to pronounce.json before first use.
- New music moods: game-show, news, comedic, pop, phonk-like, dark ambient (plus lofi, upbeat, synthwave, epic, trap). Music hits at 0.0 s, no fade-in; never the same genre two days running.
- Five synthesized sound kits (all original): UI, News, Compare/Game, Comedy, Tech. A different kit from the previous day. Loudness target about -16 LUFS, true peak below -2 dBTP; the no-music TikTok version stays.

## 6. Story grammar
Hook 0-2 s -> setup 2-6 s (who, what) -> payoff 1 by 5-8 s -> re-hook at 40-50% -> payoff 2/twist -> button + loop (last 1-2 s). Truth rules unchanged. Fabricated chats (T1) and skits (T7) carry a small on-screen "demo"/"skit" tag and are labeled in the pinned comment.

## 7. Engine and validator changes
- Templates in `shorts/templates/<name>/` (worlds JS, style preset, layout variants, caption look, sound kit, music mood, voice, length range); `meta.template` selects.
- Hook overlay from frame 0; opening hit at 0.0 s; voice lead 0.1 s at most. Auto-motion every 1.8 s of stillness. Loop frame match + audio crossfade. Optional top progress bar (default in T4).
- Validator rules: hook 8 words or fewer; voiced lines 12 words or fewer; length inside the template range; template not used in the last 3 days; hook type not the same as yesterday; voice not the same 3 days in a row; music genre and sound kit not the same as yesterday; light/dark not the same 3 days in a row; more than half of scene types equal to any of the last 3 videos fails; demo/skit label required for T1 fake chats and T7.
- Post-render checks: frame 0 not blank; duration in range; loudness/peak; pronunciation for both voices.
- `covered.json` entries also record: template, hook_type, voice, music, sound_kit, light_dark, length, scene_types (retention numbers can be added later).
- Samples replaced by 8 examples, one per template, marked "shows the format, never copy wording or structure".

## 8. Daily task changes (Opus, 02:35)
Trend research for the week's AI short formats on TikTok/Shorts/Reels (2-3 line trend note in the script); prefer topics for everyday users (ChatGPT, Gemini, phones, jobs, school, money, creativity) over niche enterprise news; pick the template by content + trend note within the variety rules; 3 hooks scored; scroll test before commit (would a stranger stop at frame 0? reason to stay to the end? payoff by 8 s?). Weekly mix guide: ~2 news (T2), 2 practical (T1/T4), 1 compare/quiz (T3/T6), 1 terminal/skit (T5/T7), 1 kinetic (T8). Two-source verification, validator, push, render report unchanged.

## 9. Rollout
A: engine core (hook overlay, auto-motion, loop, outro change, af_heart pronunciation test, sound-kit framework, music moods, validator + log). B1: T1-T4 previews on real topics -> user approves -> restart daily task with these 4. B2: T5-T8 previews. C: weekly feedback (YT "Viewed vs swiped away", average % viewed, FB 3-second views) logged per template and hook type. Quality gate for every template preview: hook at frame 0, a change every 2 s or faster, loudness on target, pronunciation passes, user approval.

## 10. Honest limits
Everything is drawn with code (no real footage, faces or AI images); voices are TTS; this fixes known causes of the drop but cannot guarantee reach; expect trends over 2-3 weeks, not single-video verdicts.

Sources: vidIQ (Shorts algorithm 2026), Aibrify (Shorts retention curve playbook), Emplifi (Facebook Reels data, March 2026).
