# FredsDesk script writing guide

You write ONE JSON script per lesson into `queue/NNN-slug.json` (NNN = lesson number, 3 digits).
Lessons come from `curriculum/lessons.json`; never write one listed in `curriculum/covered.json` or already in `queue/`/`archive/`.
Check yourself with `python3 engine/validate.py queue/NNN-slug.json` (must print OK). Look at `samples/`, `archive/` and `queue/` for working examples.

## The pattern (every lesson)
1. **hook** (one punchy line, 6-12 words, a surprising claim or question) -> 2. **promise** (always: "Welcome to FredsDesk, lesson N. In under a minute, you'll ...") -> 3. **definition** -> 4. **analogy** -> 5. **how it works** -> 6. **example or myth-vs-fact** -> 7. **recap** (3 points) -> 8. **quiz_end** (quiz + "Tomorrow: <next lesson title>." + follow call).
Scenes may be added between 3 and 6 (up to 9 scenes total) but order of the beats stays.

## Hard limits (validator enforces most)
- Narration 165-215 words total. Video must stay under 90s. One idea per lesson. Plain words, friendly teacher voice, short sentences.
- `title` and `season` must equal the curriculum entry. Last scene `teaser` = next lesson's title, and its narration says "Tomorrow: ...".
- Hook narration must be new: never reuse a hook, analogy or example listed in `covered.json`. Make each lesson's analogy and example fresh and concrete (cooking, sport, cities, music, travel, school...), not always LEGO.
- Facts must be accurate and not time-sensitive. No hype, no medical/financial claims. If unsure of a number, leave it out.
- Spoken-word fixes go in `say` (e.g. "ChatGPT": "Chat G P T", "AI": "A I"). Spell numbers as words in narration when they should be read aloud.
- `post`: title (<=90 chars, ends "| AI Lesson #N"), description (1-2 sentences + "Quiz inside!"), 6 hashtags (#AI #LearnAI ... #Shorts), pinned_comment with the quiz answer + a question.

## Top-level shape
```json
{"lesson": 5, "season": "Foundations", "title": "How does an AI learn?", "voice": "auto",
 "say": {"FredsDesk": "Freds Desk"}, "scenes": [ ... ], "post": {"title":"","description":"","hashtags":[],"pinned_comment":""}}
```
Every scene: `type`, `beat` (hook|promise|definition|analogy|how_it_works|example|recap|quiz_teaser), `narration`, scene props, optional `cues` (see below).

## Scene types and props
| type | required props | notes |
|---|---|---|
| hook | lines[], accent (index of the highlighted line), input (text typed in a chat box) | lines must spell the narration exactly; first scene only |
| promise | cues {logo, title} | `cues: {"logo":"Welcome","title":"lesson"}` |
| concept | term, definition, example {text, tokens[]} | tokens must join to text |
| analogy | sentence, bricks[] | LEGO bricks; bricks must spell the sentence; narration must be about bricks/LEGO |
| tokens | sentence, chips[], ids[] | chips spell sentence; same length as ids |
| versus | word, highlight, chips[], question | chips spell word |
| stat | label; value (+prefix/suffix/decimals) OR text; sub, icon, note | big number or word |
| network | layers[], labels[], inputText, outputs[{label,p}], winner, note | neural net diagram |
| chat | messages[{role:"user"/"ai", text, flags[{text,kind,note}]}] | streaming chat |
| compare | left/right {title, icon, points[3]}, verdict | two columns; cues left, right, verdict |
| anatomy | parts[{label,text,color}], footer | colors: blue teal warm coral violet; cues p1..pn, footer |
| map | points[{label,x,y,g}], groups, query, k, axisNote, matchLabel | embedding space; cues points, query, match |
| flow | steps[{label,sub,icon}], loop, note | 3-5 steps; cues s1..sn |
| recap | points[3] | cues p1,p2,p3 |
| quiz_end | question, options[2], teaser | last scene; cues quiz, optA ("=a"), optB ("=b"), answer, end ("tomorrow"), follow |
Icons: chat search db brain doc gear user check spark cloud bolt target.

## Cues (sync visuals to the spoken word)
`cues: {"name": "word"}` makes that visual beat appear when the narrator says the word. Prefix match on the lowercase word; `"=word"` exact; `"word#2"` the 2nd time it is said. Pick words that really occur in that scene's narration. If a cue is missing, a default timing is used.

## Quality bar
Read the narration aloud: it should sound natural and fit ~25-30 words per 10 seconds. The viewer knows nothing about AI: define terms before using them. End the lesson with a quiz whose answer is stated in the pinned comment.
