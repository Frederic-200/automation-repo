#!/usr/bin/env python3
"""Validate a v2 script before it is built.   python3 shorts/v2/validate_v2.py script.json [--date YYYY-MM-DD] [--log shorts/v2/novelty_log.json] [--quiet]

Exit 0 = OK (warnings allowed), 1 = errors (do NOT build/post). Never loosens the old validate.py: its word lists, pronunciation and source rules are reused.
Checks: schema, kinds/params, hook (<= 8 words, on screen at frame 0, rotating type), length (60-90 s), sentence length, digits/dates, content word lists,
pronunciation, sources (2 independent per fact), post text, ending (loop / cliffhanger alternate), comment prompt, retention (re-hook), variety vs v2 history.
"""
import json, os, re, sys
from urllib.parse import urlparse
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import validate as V          # shorts/validate.py: word lists + constants (import is side-effect free)
import pick_world as PW

KINDS = {   # required params per scene kind (the same kinds exist in worlds a, b, c)
    "headline": ["lines"], "bars": ["rows"], "stat": ["big"], "finale": ["top", "accent"],
    "list": ["items"], "versus": ["a", "b"], "counter": ["label", "to"], "steps": ["steps"], "stage": ["beats"],
}
WORLDS = PW.WORLDS; LEN = (60, 90); WPS = {"am_fenrir": 2.75, "af_heart": 2.6}
MAX_SAME_KIND = 3; MIN_KINDS = 5; BEAT_GAP = 3.6
STAGE_PROPS = set(json.load(open(os.path.join(HERE, 'props', 'prop_names.json')))); MAX_SCENE_SEC = 9.5; MAX_SENT = 14
TURN = re.compile(r"\b(but|however|except|catch|twist|wait|turns out|here is|here's|yet|until|instead)\b", re.I)
NORM = lambda s: re.sub(r"[^a-z0-9 ]", "", s.lower().replace("it's", "it is").replace("*", ""))


def main():
    a = sys.argv[1:]; args = [x for x in a if not x.startswith("--")]; opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if not args: print(__doc__); sys.exit(2)
    errs, warns = [], []; E = errs.append; Wn = warns.append
    try: S = json.load(open(args[0]))
    except Exception as ex: print("ERROR: not valid JSON:", ex); sys.exit(1)
    logp = opt("--log", os.path.join(HERE, "novelty_log.json")); hist = json.load(open(logp))["entries"] if os.path.exists(logp) else []
    date = opt("--date"); hist = [h for h in hist if not date or (h.get("date") or "") < date]
    meta = S.get("meta") or {}; post = meta.get("post") or {}; v2 = S.get("v2") or {}; scenes = S.get("scenes") or []; voice = S.get("voice")

    # ---- schema
    for k in ("title", "v2", "hook", "voice", "scenes", "audio", "meta"):
        if k not in S: E(f"missing key '{k}'")
    w, pal = v2.get("world"), v2.get("palette")
    if w not in WORLDS: E(f"v2.world must be one of {list(WORLDS)}")
    elif pal not in WORLDS[w]: E(f"v2.palette for world {w} must be one of {WORLDS[w]}")
    if voice not in V.VOICES: E(f"voice must be one of {V.VOICES}")
    if (S.get("audio") or {}).get("sfx") != "foley": E('audio.sfx must be "foley"')
    if (S.get("audio") or {}).get("music") not in V.MUSIC: E(f"audio.music must be one of {V.MUSIC}")
    if not 8 <= len(scenes) <= 16: E(f"8 to 16 scenes expected for a 60-90 s video (got {len(scenes)})")
    for i, sc in enumerate(scenes):
        k = sc.get("kind")
        if k not in KINDS: E(f"scene {i}: unknown kind '{k}' (known: {list(KINDS)})"); continue
        P = sc.get("params") or {}
        for r in KINDS[k]:
            if not P.get(r): E(f"scene {i} ({k}): params.{r} missing")
        if not sc.get("lines"): E(f"scene {i}: every scene needs narration lines")
        if k == "bars":
            for j, r in enumerate(P.get("rows") or []):
                if not (isinstance(r.get("value"), (int, float)) and 0 <= r["value"] <= 1): E(f"scene {i} row {j}: value must be 0..1")
            if len(P.get("rows") or []) > 3: E(f"scene {i}: at most 3 bar rows fit")
            if P.get("gap") is None and len(P.get("rows") or []) >= 2: pass
            if "ILLUSTRATION" not in str(P.get("note", "")).upper() and not meta.get("data_sourced"): E(f"scene {i}: bars need params.note 'ILLUSTRATION. NOT REAL DATA.' unless meta.data_sourced is true and sources are listed")
        if k == "stage" or (k == "headline" and P.get("beats")):
            bs = P.get("beats") or []; lines = " ".join(sc.get("lines") or []); toks = re.findall(r"[A-Za-z0-9']+", strip(lines)); dur = len(toks) / WPS.get(voice, 2.7) + .45; last_t = 0.0
            for j, b in enumerate(bs):
                if b.get("prop") not in STAGE_PROPS: E(f"scene {i} beat {j}: unknown prop '{b.get('prop')}' (known: {sorted(STAGE_PROPS)})")
                if len(str(b.get("label", "")).split()) > 3: E(f"scene {i} beat {j}: label max 3 words")
                if b.get("slot", "c") not in ("c", "l", "r"): E(f"scene {i} beat {j}: slot must be c, l or r")
                if b.get("cue"):
                    idx = [n for n, t in enumerate(toks) if t.lower() == str(b["cue"]).lower()]
                    if not idx: E(f"scene {i} beat {j}: cue '{b['cue']}' is not a word of the narration"); continue
                    t = idx[0] / max(len(toks), 1) * dur
                elif isinstance(b.get("t"), (int, float)): t = b["t"]
                else: t = 0.0 if j == 0 else last_t + 1.5
                if j == 0 and t > 1.2: E(f"scene {i}: first beat must start within about one second (starts ~{t:.1f}s)")
                if j and t - last_t > BEAT_GAP: E(f"scene {i} beat {j}: about {t - last_t:.1f}s since the previous beat (max {BEAT_GAP}s)")
                last_t = max(last_t, t)
            if dur - last_t > BEAT_GAP + 1: E(f"scene {i}: last beat about {dur - last_t:.1f}s before the scene ends: add a beat")
            if not bs: E(f"scene {i}: stage needs beats")
        if k == "list" and not 2 <= len(P.get("items") or []) <= 5: E(f"scene {i}: list needs 2 to 5 items")
        if k == "steps" and not 2 <= len(P.get("steps") or []) <= 4: E(f"scene {i}: steps needs 2 to 4 steps")
        if k in ("list", "steps") and any(len(str(t).split()) > 6 for t in (P.get("items") or P.get("steps") or [])): E(f"scene {i}: each {k} entry max 6 words")
        if k == "versus":
            for side in ("a", "b"):
                if not (P.get(side) or {}).get("text"): E(f"scene {i}: versus.{side}.text missing")
        if k == "counter":
            if not isinstance(P.get("to"), (int, float)): E(f"scene {i}: counter.to must be a number")
            if "ILLUSTRATION" not in str(P.get("note", "")).upper() and not meta.get("data_sourced"): E(f"scene {i}: counter needs params.note 'ILLUSTRATION. NOT REAL DATA.' unless meta.data_sourced is true and sources are listed")
        if k == "headline" and sum(len(l.get("text", "").split()) for l in P.get("lines") or []) > 9: E(f"scene {i}: headline longer than 9 words")
        if k == "headline" and len(P.get("lines") or []) > 5: E(f"scene {i}: at most 5 headline lines")
    kinds = [sc.get("kind") for sc in scenes]
    if scenes and kinds[0] != "headline": E("scene 0 must be a headline: the hook is on screen from frame 0")
    if scenes and kinds[-1] != "finale": E("last scene must be the finale")
    if kinds.count("finale") > 1: E("one finale only")
    for k in set(kinds) - {"stage"}:
        if kinds.count(k) > MAX_SAME_KIND: E(f"scene kind '{k}' used {kinds.count(k)} times (max {MAX_SAME_KIND}): vary the visuals")
    if len(set(kinds)) < (4 if "stage" in kinds else MIN_KINDS) and len(scenes) >= 8: E(f"use at least {MIN_KINDS} different scene kinds")
    if any(kinds[i] == kinds[i + 1] and kinds[i] != "stage" for i in range(len(kinds) - 1)): E("the same scene kind must not appear twice in a row")

    # ---- hook (frame 0, <= 8 words, rotating type)
    hook = str(S.get("hook") or ""); hw = hook.split()
    if not hook: E("hook missing")
    if len(hw) > 8: E(f"hook has {len(hw)} words (max 8)")
    if scenes and scenes[0].get("kind") == "headline":
        htxt = NORM(" ".join(l.get("text", "") for l in (scenes[0].get("params") or {}).get("lines") or []))
        if hook and NORM(hook) != htxt: E("hook must equal the scene-0 headline text exactly (so the hook IS the first frame)")
    if meta.get("hook_type") not in PW.HOOK_TYPES: E(f"meta.hook_type must be one of {PW.HOOK_TYPES}")
    if meta.get("hook_type") and meta["hook_type"] in [h.get("hook_type") for h in hist[-2:]]: E(f"hook type '{meta['hook_type']}' used in the last 2 videos")
    first_line = strip(scenes[0]["lines"][0]) if scenes and scenes[0].get("lines") else ""
    if len(first_line.split()) > 14: Wn("first spoken sentence is long: it should land in ~3 s")

    # ---- narration
    spoken = [strip(l) for sc in scenes for l in sc.get("lines") or []]; text = " ".join(spoken)
    words = len(re.findall(r"[A-Za-z0-9']+", text)); est = words / WPS.get(voice, 2.7) + .45 * len(scenes)
    if not LEN[0] <= est <= LEN[1]: E(f"estimated length {est:.0f}s outside {LEN[0]}-{LEN[1]}s ({words} words)")
    for i, sc in enumerate(scenes):
        sec = len(re.findall(r"[A-Za-z0-9']+", strip(" ".join(sc.get("lines") or [])))) / WPS.get(voice, 2.7) + .45
        if sec > MAX_SCENE_SEC: E(f"scene {i} runs about {sec:.0f}s (max {MAX_SCENE_SEC}): split it")
    for l in spoken:
        if re.search(r"\d", l): E(f"digits in narration (write numbers as words): '{l[:60]}'")
        for sent in re.split(r"(?<=[.!?])\s+", l):
            n = len(re.findall(r"[A-Za-z']+", sent))
            if n > MAX_SENT: E(f"sentence has {n} words (max {MAX_SENT}): '{sent[:60]}'")
    screen = []
    def walk(o):
        if isinstance(o, str): screen.append(o)
        elif isinstance(o, dict): [walk(v) for v in o.values()]
        elif isinstance(o, list): [walk(v) for v in o]
    for sc in scenes: walk(sc.get("params") or {})
    for s in screen + spoken:
        if re.search(rf"\b({V.MONTHS})\.?\s+\d{{1,2}}\b|\b\d{{1,2}}\s+({V.MONTHS})\b|\b(19|20)\d\d\b|\b\d{{1,2}}/\d{{1,2}}/\d{{2,4}}\b", s, re.I): E(f"date on screen or in narration: '{s[:60]}'")
    blob = (text + " " + " ".join(screen) + " " + json.dumps(post)).lower()
    for x in V.POLITICS:
        if re.search(rf"\b{re.escape(x)}\b", blob): E(f"political / sensitive word '{x}'")
    for x in V.DISPARAGE:
        if re.search(rf"\b{re.escape(x)}\b", blob): E(f"disparaging word '{x}'")
    if re.search(r"\b(lyrics?|chorus)\b", blob): Wn("mentions lyrics: do not quote songs")

    # ---- retention: re-hook in the middle third, answer late, comment-inviting ending
    n = len(scenes); mid = [i for i in range(n) if .3 * n <= i <= .7 * n]
    if n >= 8 and not any(TURN.search(" ".join(scenes[i].get("lines") or [])) for i in mid): E("no re-hook in the middle third: one scene there needs a turn word (but / however / here's the catch / turns out)")
    en = meta.get("ending"); last = strip((scenes[-1].get("lines") or [""])[-1]) if scenes else ""
    if en not in PW.ENDINGS: E('meta.ending must be "loop" or "cliffhanger"')
    elif hist and hist[-1].get("ending") == en: E(f"same ending style '{en}' as the last video: alternate loop and cliffhanger")
    if en == "cliffhanger" and not str(meta.get("next_question", "")).strip().endswith("?"): E("cliffhanger: meta.next_question (ends with ?) required")
    if en == "loop" and hook and scenes and NORM(last).split()[-2:] == NORM(hook).split()[:2]: pass
    if not (last.endswith("?") or re.search(r"\b(comment|tell me|which one|let me know|your turn|reply)\b", last, re.I)): E("the last spoken line must invite a comment (a question, or 'tell me / comment / which one')")
    pc = str(post.get("pinned_comment", ""))
    if "?" not in pc: E("post.pinned_comment must ask a question (it starts the comments)")

    # ---- pronunciation
    pr = V.load(os.path.join(os.path.dirname(HERE), "pronounce.json"), {}); say = S.get("say") or {}
    for k, v in say.items():
        if pr.get("allowed_say", {}).get(k) != v: E(f"say['{k}']='{v}' not in pronounce.json allowed_say")
    for acr in sorted(set(re.findall(r"\b[A-Z]{2,}s?\b", text))):
        b = acr.rstrip("s") if acr.endswith("s") and acr[:-1].isupper() else acr
        if b in say: continue
        if b in pr.get("avoid", {}): E(f"acronym {acr} avoided: {pr['avoid'][b]}")
        elif b not in pr.get("allowed_acronyms_by_voice", {}).get(voice, pr.get("allowed_acronyms", [])): E(f"acronym {acr} not verified for the voice: write it as a word or test it")

    # ---- sources (2 independent per fact) unless this is a general concept video with no figures/names/dates
    concept = meta.get("kind") == "concept"; srcs = post.get("sources") or []
    if concept:
        if srcs: Wn("concept video: sources not required")
        if re.search(r"\d", " ".join(screen)) and not meta.get("data_sourced"): Wn("numbers on screen in a concept video: make sure they are illustration only")
    else:
        for i, s in enumerate(srcs):
            u = (s or {}).get("url", "")
            if not (isinstance(s, dict) and s.get("name") and u.startswith("https://") and urlparse(u).netloc): E(f"sources[{i}] needs name + https url")
        if len(srcs) < 2 or len({urlparse((s or {}).get("url", "")).netloc.replace("www.", "") for s in srcs if isinstance(s, dict)}) < 2: E("at least 2 sources from 2 different sites required")
        facts = meta.get("facts") or []
        if not facts: E("meta.facts: list each factual claim with sources:[indexes] (2 independent sites each)")
        for i, f in enumerate(facts):
            ix = f.get("sources") if isinstance(f, dict) else None
            if not (isinstance(f, dict) and f.get("claim") and isinstance(ix, list) and ix and all(isinstance(j, int) and 0 <= j < len(srcs) for j in ix)): E(f"facts[{i}] needs claim + valid sources indexes"); continue
            if len({urlparse(srcs[j].get("url", "")).netloc.replace("www.", "") for j in ix}) < 2: E(f"facts[{i}] needs 2 independent sources")

    # ---- post text
    for k in ("title", "tiktok_caption", "yt_caption", "pinned_comment", "hashtags"):
        if not post.get(k): E(f"meta.post.{k} missing")
    if len(post.get("title", "")) > 100: E("post.title max 100 chars")
    if len(post.get("tiktok_caption", "")) > 300: E("post.tiktok_caption max 300 chars")
    ht = post.get("hashtags") or []
    if not (5 <= len(ht) <= 12 and all(isinstance(h, str) and re.fullmatch(r"#\w+", h) for h in ht)): E("post.hashtags: 5-12 items like #AI")
    if "#FredsDesk" not in ht: E("post.hashtags must include #FredsDesk")
    if not meta.get("slug") or not re.fullmatch(r"[a-z0-9-]+", meta.get("slug", "")): E("meta.slug (lowercase-with-dashes) required")
    if hist and any(h.get("slug") == meta.get("slug") for h in hist): E("slug already used")

    # ---- variety vs the v2 history (cheap rules; novelty.py does the picture test)
    if w and hist and w in [h.get("world") for h in hist[-2:]]: E(f"world '{w}' used in the last 2 videos")
    if w and pal and any(h.get("world") == w and h.get("palette") == pal for h in hist[-4:]): E(f"palette {w}/{pal} used in the last 4 videos")
    if hist and hist[-1].get("voice") == voice: E("same voice as the last video")
    if hist and hist[-1].get("music") == (S.get("audio") or {}).get("music"): E("same music mood as the last video")

    if not ("--quiet" in a and not errs and not warns):
        print(f"{os.path.basename(args[0])}: world {w}/{pal} scenes {n} words {words} est {est:.0f}s hook_type {meta.get('hook_type')} ending {en}")
        for x in warns: print("WARN:", x)
        for x in errs: print("ERROR:", x)
    print("OK" if not errs else f"FAILED ({len(errs)} errors)"); sys.exit(1 if errs else 0)


def strip(s): return s.replace("*", "")


if __name__ == "__main__":
    main()
