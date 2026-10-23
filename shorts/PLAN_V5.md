# FredsDesk Shorts v5: "Human wonder of AI" (Jake stories), approved by the user 2026-10-23

Goal: answer the questions AI lovers actually ask ("Can AI get sued?", "Will AI take over?", "How does AI learn from its users?", "Why does AI forget details in long chats?") through a short story about an invented character, Jake, ending with the real, sourced answer. Built for audience retention.

## Decisions (user answers)
- Niche: common questions of AI lovers ("Human wonder of AI"). Not tied to the news of the last 48 h; evergreen questions are allowed, current ones preferred.
- One recurring character: **Jake**, invented, a simple friendly bust drawn by the engine (`shorts/jake.py`). Never a real person. Pinned comment always says he is fictional and the story is an illustration.
- A narrator tells Jake's story (Jake never speaks). Voices am_fenrir or af_heart.
- Length is decided by the question and the story is explained in detail: about 60-190 s (format **E**; the first samples at 45-55 s felt narrow and rushed).
- No punch sound effect on highlighted words (also no risers or braams) in format E; Jake has a single silhouette shadow.
- Retention strategy applied to every video (validator enforces what can be checked):
  1. **Hook** in the first 1-3 s: the question or Jake mid-moment, on screen from frame 0 (8 words or fewer).
  2. **Open loop**: the hook promises an answer; a first fragment lands by 5-8 s, the full answer is held for the last third.
  3. **Pattern interrupts**: the picture changes every 2-6 s (scene cut, Jake expression morph, beat on a spoken word, transition).
  4. **Re-hook** in the middle ("But here is the catch").
  5. **Ending rotates**: `loop` (last line flows into the hook, hook echoes at the end) and `cliffhanger` (teases tomorrow's question; stored in covered.json as `next_question`; never two of the same in a row).
- The daily task stays paused until the user approves two sample videos (rendered to a separate Drive folder, not logged as covered).
- The news image set (up to 10 slides, 4:5, daily 3:30 AM PHT) is a separate task, built after the samples.

## Honest limits
- Retention cannot be measured from here. After posting, the user sends the retention graphs (average view duration, first-3-second drop-off) and the hook and pacing rules are tuned from them.
- Jake is drawn by code: 7 expressions (neutral, think, worried, surprised, happy, confused, blank). New poses need engine work.
- Legal and "takeover" questions are explained neutrally with sources; no legal advice, no scare framing.
