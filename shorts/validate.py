#!/usr/bin/env python3
"""Validate a FredsDesk Shorts script before it is committed.

    python3 shorts/validate.py shorts/queue/2026-10-16-some-slug.json [--quiet]

Exit 0 = OK (warnings allowed), exit 1 = errors (do NOT commit the script).
Checks what can be checked mechanically: schema, format rules, length estimate, rotation vs covered.json,
sources (2 independent sources per fact), content-rule word lists, numbers/dates, pronunciation list, ending.
"""
import json, os, re, sys
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
FORMATS = {  # estimated spoken seconds (before the 3 s outro) allowed range; real length is re-checked after rendering
    "A": {"voiced": True, "est": (18, 36), "max_seconds": (22, 36), "min_sources": 2},
    "B": {"voiced": True, "est": (14, 31), "max_seconds": (18, 33), "min_sources": 2},
    "C": {"voiced": False, "est": (7, 24), "max_seconds": (9, 30), "min_sources": 0},
    "D": {"voiced": True, "est": (14, 32), "max_seconds": (18, 35), "min_sources": 2},
    # E = "Human wonder of AI": a question answered through a short story about Jake (PLAN_V5.md). Length is set by the question: 60-190 s, explained in detail (review 2026-10-24: 45-55 s felt rushed).
    "E": {"voiced": True, "est": (50, 185), "max_seconds": (60, 190), "min_sources": 2},
}
SCENE_LIMITS = {"E": (8, 40)}          # scenes per video; everything else 3-9
REHOOK = re.compile(r"\b(but|however|except|catch|twist|wait|turns out|here is|here's|yet|and then|plot)\b", re.I)
CAPTION_PRESETS = ("stack", "typeon", "slam", "clean", "off")
TRANSITIONS = {"liquid", "iris", "whip", "glitch", "pixel", "flash", "card", "none"}
VOICES = ("am_fenrir", "af_heart")
TEMPLATES = ("classic", "chat_drop", "headline_drop", "split_screen", "countdown_list", "terminal", "guess_quiz", "meme_skit", "kinetic_type")
HOOK_TYPES = ("number", "callout", "pov", "question", "this_ai_just", "before_after", "myth", "countdown", "guess", "mid_action")
MUSIC = ("lofi", "gentle", "upbeat", "synthwave", "epic", "trap")
WORDS_PER_SEC = 2.75   # am_fenrir at speed 1.0, measured on the samples

POLITICS = ["election", "elections", "vote", "voting", "voters", "ballot", "president", "presidential", "senate", "senator", "congress", "congressman",
            "republican", "democrat", "democratic party", "gop", "trump", "biden", "harris", "obama", "putin", "xi jinping", "parliament", "prime minister",
            "campaign trail", "left-wing", "right-wing", "liberal", "conservative", "war", "invasion", "genocide", "abortion", "immigration"]
DISPARAGE = ["scam", "scammers", "garbage", "trash", "sucks", "idiot", "idiots", "stupid", "evil", "greedy", "liar", "liars", "crooks", "fraud",
             "pathetic", "disgusting", "worthless", "clowns", "losers", "useless company", "shame on"]
MONTHS = "january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec"


def load(p, d=None):
    try: return json.load(open(p))
    except Exception: return d


def strip_marks(s): return s.replace("*", "")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    quiet = "--quiet" in sys.argv
    if not args: print(__doc__); sys.exit(2)
    path = args[0]; errs, warns = [], []
    E = lambda m: errs.append(m); W = lambda m: warns.append(m)
    try: S = json.load(open(path))
    except Exception as ex: print("ERROR: not valid JSON:", ex); sys.exit(1)

    pr = load(os.path.join(HERE, "pronounce.json"), {}); cov = load(os.path.join(HERE, "covered.json"), {"entries": []})["entries"]
    meta = S.get("meta") or {}; fmt = meta.get("format"); post = meta.get("post") or {}
    base = os.path.basename(path)
    m = re.match(r"(\d{4}-\d{2}-\d{2})-([a-z0-9-]+)\.json$", base)
    if not m: E("file name must be queue/YYYY-MM-DD-slug.json (lowercase slug)")
    date = m.group(1) if m else None; slug = m.group(2) if m else None
    if meta.get("slug") and slug and meta["slug"] != slug: E("meta.slug must equal the slug in the file name")

    # ---- schema
    for k in ("title", "style", "scenes", "voice", "meta"):
        if k not in S: E(f"missing key '{k}'")
    if S.get("voice") not in VOICES: E(f"voice must be one of {VOICES}")
    if fmt not in FORMATS: E("meta.format must be one of A B C D E"); fmt = None
    for k in ("topic", "caption_preset", "post"):
        if not meta.get(k): E(f"meta.{k} missing")
    cp = meta.get("caption_preset")
    if cp and cp not in CAPTION_PRESETS: E(f"meta.caption_preset must be one of {CAPTION_PRESETS}")
    if S.get("scenes_custom") != "scenes_fredsdesk.js": E("scenes_custom must be \"scenes_fredsdesk.js\"")
    scenes = S.get("scenes") or []
    lo_s, hi_s = SCENE_LIMITS.get(fmt, (3, 9))
    if not lo_s <= len(scenes) <= hi_s: E(f"{lo_s} to {hi_s} scenes expected for format {fmt}")
    if "style_overrides" in S and "fonts" in (S["style_overrides"] or {}): W("style_overrides.fonts is set by caption_preset; remove unless intended")
    if S.get("end_tail") != 0.5: E("end_tail must be 0.5 (the outro follows)")

    # ---- known scene types
    known = set()
    for f in (os.path.join(HERE, "kit", "engine", "scenes.js"), os.path.join(HERE, "kit", "scenes_fredsdesk.js"), os.path.join(HERE, "kit", "engine", "bg.js")):
        if os.path.exists(f): known |= set(re.findall(r"SCENES\.(\w+)\s*=", open(f).read()))
    for i, sc in enumerate(scenes):
        if sc.get("type") not in known: E(f"scene {i}: unknown type '{sc.get('type')}'")
        tr = (sc.get("params") or {}).get("transition")
        if tr and tr not in TRANSITIONS: E(f"scene {i}: unknown transition '{tr}'")
        if sc.get("act") not in ("problem", "build", "turn", "payoff", "button"): E(f"scene {i}: act must be problem|build|turn|payoff|button")
    if scenes and scenes[-1].get("type") in ("burst",): E("last scene must not be the diamond 'burst' world")
    if sum(1 for s in scenes if (s.get("params") or {}).get("transition") == "card") > 2: E("at most 2 card transitions")

    # ---- narration
    lines = [l for sc in scenes for l in (sc.get("lines") or [])]
    spoken = [strip_marks(l) for l in lines]
    text = " ".join(spoken)
    voiced = FORMATS[fmt]["voiced"] if fmt else True
    if voiced:
        if S.get("silent"): E("voiced formats must not set silent")
        if not all(sc.get("lines") for sc in scenes): E("every scene needs at least one line")
    else:
        if S.get("silent") is not True: E('format C needs "silent": true')
    words = len(re.findall(r"[A-Za-z0-9']+", text))
    est = words / WORDS_PER_SEC + .35 * len(scenes)
    if fmt:
        lo, hi = FORMATS[fmt]["est"]
        if voiced and not lo <= est <= hi: E(f"estimated length {est:.0f}s outside {lo}-{hi}s for format {fmt} ({words} words)")
        ms = S.get("max_seconds")
        if not isinstance(ms, (int, float)) or not FORMATS[fmt]["max_seconds"][0] <= ms <= FORMATS[fmt]["max_seconds"][1]:
            E(f"max_seconds must be {FORMATS[fmt]['max_seconds']} for format {fmt}")
        if ms and ms > (195 if fmt == "E" else 57): E("max_seconds must leave room for the outro (<= 57, format E <= 195)")
    first = (scenes[0].get("lines") or [""])[0] if scenes else ""
    if voiced and len(first.split()) > 18: W("hook line is long; the first sentence should land in about 3 seconds")

    # numbers as words in narration; no dates on screen
    for l in spoken:
        if re.search(r"\d", l): E(f"digits in narration (write numbers as words): '{l[:60]}'")
    screen = []
    def walk(o):
        if isinstance(o, str): screen.append(o)
        elif isinstance(o, dict): [walk(v) for v in o.values()]
        elif isinstance(o, list): [walk(v) for v in o]
    for sc in scenes: walk(sc.get("params") or {})
    for s in screen + spoken:
        if re.search(rf"\b({MONTHS})\.?\s+\d{{1,2}}\b|\b\d{{1,2}}\s+({MONTHS})\b|\b(19|20)\d\d\b|\b\d{{1,2}}/\d{{1,2}}/\d{{2,4}}\b", s, re.I): E(f"date on screen or in narration: '{s[:60]}'")

    # ---- content rules (word lists; the author must still judge the rest)
    blob = (text + " " + " ".join(screen) + " " + json.dumps(post)).lower()
    for w in POLITICS:
        if re.search(rf"\b{re.escape(w)}\b", blob): E(f"political / sensitive word '{w}' (no politics, elections, wars)")
    for w in DISPARAGE:
        if re.search(rf"\b{re.escape(w)}\b", blob): E(f"disparaging word '{w}' (never mock or insult companies or people)")
    if re.search(r"\b(lyrics?|chorus)\b", blob): W("mentions lyrics: do not quote songs")

    # ---- v2 retention rules (hook at frame 0, short sentences, variety)
    hk = S.get("hook") or {}
    htxt = str(hk.get("text", "")).replace("*", "")
    if not htxt: E("hook.text missing: the hook must be on screen from frame 0")
    elif len(htxt.split()) > 8: E(f"hook has {len(htxt.split())} words (max 8)")
    if hk and hk.get("hold", 2.4) > 3.0: E("hook.hold max 3.0 s")
    if meta.get("hook_type") not in HOOK_TYPES: E(f"meta.hook_type must be one of {HOOK_TYPES}")
    tpl = meta.get("template")
    if tpl not in TEMPLATES: E(f"meta.template must be one of {TEMPLATES}")
    if meta.get("look") not in ("light", "dark"): E("meta.look must be 'light' or 'dark' (background of the main scenes)")
    if S.get("music_mood") not in MUSIC and voiced is not None and S.get("music", True): E(f"music_mood must be one of {MUSIC}")
    if voiced:
        for l in spoken:
            for sent in re.split(r"(?<=[.!?])\s+", l):
                n = len(re.findall(r"[A-Za-z']+", sent))
                if n > (18 if fmt == "E" else 12): E(f"sentence has {n} words (max {18 if fmt == 'E' else 12}): '{sent[:60]}'")
    if tpl in ("chat_drop", "meme_skit") and not re.search(r"\b(skit|demo|mock)", post.get("pinned_comment", ""), re.I): E("fake chats/skits: pinned_comment must say it is a skit/demo")
    pv = [e for e in cov if date and e.get("date", "") < date]
    p3 = pv[-3:]; y = pv[-1] if pv else {}
    types = [sc.get("type") for sc in scenes if sc.get("type") != "story"]   # story scenes are checked by bgcheck.py
    if tpl and tpl != "classic" and any(e.get("template") == tpl for e in p3): E(f"template '{tpl}' used in the last 3 videos")
    if tpl == "classic" and any(e.get("template") in (None, "classic") for e in p3): W("classic template already used recently: switch to a v2 template")
    if y.get("hook_type") and y.get("hook_type") == meta.get("hook_type"): E("same hook type as yesterday")
    if y.get("music") and y.get("music") == S.get("music_mood") and voiced is not None: E("same music genre as yesterday")
    if y.get("sound_kit") and y.get("sound_kit") == ((S.get("style_overrides") or {}).get("sfx") or {}).get("kit"): E("same sound-effect kit as yesterday")
    if voiced and len(pv) >= 2 and all(e.get("voice") == S.get("voice") for e in pv[-2:]): E(f"voice '{S.get('voice')}' used the last 2 videos")
    if len(pv) >= 2 and all(e.get("look") == meta.get("look") for e in pv[-2:]): E(f"look '{meta.get('look')}' used the last 2 videos")
    for e in p3:
        old = e.get("scene_types") or []
        if old and types and sum(1 for t in types if t in old) > len(types) / 2: E("more than half of the scene types repeat a recent video: change the visuals")
    if y.get("scene_types") and types and scenes and scenes[0].get("type") != "story" and y["scene_types"][0] == types[0]: E("same opening scene type as yesterday")

    # ---- format E: Jake story + retention strategy (open loop, re-hook, pattern interrupts, loop or cliffhanger). See WRITING_GUIDE section 12.
    if fmt == "E":
        import jake as JK
        lib = JK.build(); art_ = meta.get("art") or {}
        if meta.get("character") not in ("Jake", "You"): E('format E: meta.character must be "Jake" or "You" (unnamed figure, second-person story)')
        q = str(meta.get("question", "")).strip()
        if not q.endswith("?") or len(q.split()) < 3: E("format E: meta.question must be the viewer's question (ends with ?)")
        pc = post.get("pinned_comment", "")
        if not re.search(r"\bfictional\b", pc, re.I): E("format E: pinned_comment must say Jake is a fictional character and the story is an illustration")
        # Jake in the pictures
        def jids(sc):
            bg = sc.get("bg") or {}
            ids = {s for s in (bg.get("subject") or []) if str(s).startswith("jake_")}
            ids |= set(re.findall(r"jake_[a-z]+", json.dumps(bg.get("beats") or [])))
            return ids
        js = [jids(sc) for sc in scenes]
        used = set().union(*js) if js else set()
        if scenes and sum(1 for x_ in js if x_) < len(scenes) / 2: E("format E: Jake must be on screen in at least half of the scenes")
        if len(used) < 3: E(f"format E: use at least 3 different Jake expressions (uses {sorted(used)})")
        for i_ in sorted(used):
            if i_ not in lib: E(f"unknown Jake drawing '{i_}' (see python3 shorts/jake.py --list)")
            elif art_.get(i_) != lib[i_]: E(f"'{i_}' in meta.art differs from the Jake library: run python3 shorts/jake.py <file>")
        # user review 2026-10-24: never open with the answer
        for i_, sc_ in enumerate(scenes[:7]):
            if re.search(r"\b(short answer|the answer is|simple answer|quick answer|in short)\b", " ".join(sc_.get("lines") or []), re.I): E(f"scene {i_}: do not give the answer or say 'the short answer' in the opening (hold the answer for the last third; give a clue instead)")
        # retention plan (a checkable commitment): open loop at the hook, first payoff early, re-hook in the middle, full answer late
        rt = meta.get("retention") or {}
        n_ = len(scenes)
        try:
            fp, rh, fa = int(rt["first_payoff_scene"]), int(rt["rehook_scene"]), int(rt["final_answer_scene"])
            if fp > 7: E("retention.first_payoff_scene must be 7 or less: a first clue (not the full answer) inside the first ~20 s; the answer itself is held for the last third")
            if not .3 * n_ <= rh <= .7 * n_: E(f"retention.rehook_scene {rh} must sit in the middle third of {n_} scenes")
            if fa < max(rh + 1, .6 * n_) or fa > n_ - 1: E(f"retention.final_answer_scene {fa} must come after the re-hook, in the last 40% of the video")
            if 0 <= rh < n_ and not REHOOK.search(" ".join(scenes[rh].get("lines") or [])): E("the re-hook scene needs a turn word (but / however / here's the catch / turns out / wait ...)")
        except (KeyError, TypeError, ValueError):
            E("meta.retention needs first_payoff_scene, rehook_scene, final_answer_scene (scene indexes)")
        # pattern interrupts: no long unchanged stretch, a beat or morph in most scenes
        for i_, sc in enumerate(scenes):
            w_ = len(re.findall(r"[A-Za-z0-9']+", strip_marks(" ".join(sc.get("lines") or []))))
            secs = w_ / WORDS_PER_SEC + .35
            if secs > 7.5: E(f"scene {i_} runs about {secs:.0f}s: split it (the picture must change every 2-6 s)")
            elif secs > 5.5: W(f"scene {i_} runs about {secs:.0f}s: consider splitting")
        with_beats = sum(1 for sc in scenes if (sc.get("bg") or {}).get("beats"))
        if scenes and with_beats < .7 * len(scenes): E("format E: at least 70% of the scenes need bg.beats (a visible change on a spoken word)")
        if len({(sc.get('params') or {}).get('transition') for sc in scenes} - {None}) < 3: E("format E: use at least 3 different scene transitions")
        # ending: rotate loop / cliffhanger
        en = meta.get("ending")
        last_line = strip_marks((scenes[-1].get("lines") or [""])[-1]) if scenes else ""
        hl = (S.get("hook") or {}).get("loop")
        if en not in ("loop", "cliffhanger"): E('meta.ending must be "loop" or "cliffhanger"')
        elif en == "cliffhanger":
            nq = str(meta.get("next_question", "")).strip()
            if not nq.endswith("?"): E("cliffhanger: meta.next_question (tomorrow's question, ends with ?) is required")
            if hl is not False: E('cliffhanger: set hook.loop to false (the end must not replay the hook)')
            if not re.search(r"(\?|tomorrow|next|part (two|2))", last_line, re.I): E("cliffhanger: the last spoken line must tease the next question")
        else:
            if hl is False: E("loop ending: hook.loop must not be false")
            if len(last_line.split()) > 10: W("loop ending: keep the last line short so it flows back into the hook")
        if y.get("ending") and y.get("ending") == en: E(f"same ending style ('{en}') as yesterday: alternate loop and cliffhanger")
        # yesterday's cliffhanger sets today's question
        if y.get("ending") == "cliffhanger" and y.get("next_question") and q and y["next_question"].strip().lower().rstrip("?") not in q.lower().rstrip("?") and q.lower().rstrip("?") not in y["next_question"].strip().lower():
            W(f"yesterday promised: '{y['next_question']}'. Answer it today (or the cliffhanger breaks its promise)")

    # ---- pronunciation
    say = S.get("say") or {}
    allowed_say = pr.get("allowed_say", {})
    for k, v in say.items():
        if allowed_say.get(k) != v: E(f"say['{k}']='{v}' is not in pronounce.json allowed_say (never respell AI)")
    if "AI" in say: E("never respell AI")
    acr = set(re.findall(r"\b[A-Z]{2,}s?\b", text)) if voiced else set()
    for a in sorted(acr):
        b = a.rstrip("s") if a.endswith("s") and a[:-1].isupper() else a
        if b in say: continue
        if b in pr.get("avoid", {}): E(f"acronym {a} avoided: {pr['avoid'][b]}")
        elif b not in pr.get("allowed_acronyms_by_voice", {}).get(S.get("voice"), pr.get("allowed_acronyms", [])): E(f"acronym {a} not verified for the voice: write it as a normal word, or test it (TTS + ASR) and add to pronounce.json")

    # ---- sources: every fact needs 2 independent sources
    srcs = post.get("sources") or []
    need = FORMATS[fmt]["min_sources"] if fmt else 2
    for i, s in enumerate(srcs):
        u = (s or {}).get("url", "")
        if not (isinstance(s, dict) and s.get("name") and u.startswith("https://") and urlparse(u).netloc): E(f"sources[{i}] needs name + https url")
    doms = {urlparse((s or {}).get("url", "")).netloc.replace("www.", "") for s in srcs if isinstance(s, dict)}
    if len(srcs) < need: E(f"at least {need} sources required")
    if need and len(doms) < 2: E("sources must come from at least 2 different sites")
    facts = meta.get("facts") or []
    if need and not facts: E("meta.facts: list each factual claim with sources:[indexes] (at least 2 independent per claim)")
    for i, f in enumerate(facts):
        ix = f.get("sources") if isinstance(f, dict) else None
        if not (isinstance(f, dict) and f.get("claim") and isinstance(ix, list) and all(isinstance(j, int) and 0 <= j < len(srcs) for j in ix or [-1])):
            E(f"facts[{i}] needs claim and valid sources indexes"); continue
        d = {urlparse(srcs[j].get("url", "")).netloc.replace("www.", "") for j in ix}
        if len(d) < 2: E(f"facts[{i}] '{f['claim'][:40]}' needs 2 independent sources (different sites)")
    if fmt == "C" and srcs: W("format C makes no factual claims; sources not needed")

    # ---- post text
    if post:
        for k in ("title", "tiktok_caption", "yt_caption", "pinned_comment", "hashtags"):
            if not post.get(k): E(f"meta.post.{k} missing")
        if len(post.get("title", "")) > 100: E("post.title max 100 chars")
        if len(post.get("tiktok_caption", "")) > 300: E("post.tiktok_caption max 300 chars")
        if len(post.get("yt_caption", "")) > 400: E("post.yt_caption max 400 chars")
        ht = post.get("hashtags") or []
        if not (5 <= len(ht) <= 12 and all(isinstance(h, str) and re.fullmatch(r"#\w+", h) for h in ht)): E("post.hashtags: 5-12 items like #AI")
        if "#FredsDesk" not in ht: E("post.hashtags must include #FredsDesk")
        if fmt == "D" and not re.search(r"\bskit\b", post.get("pinned_comment", ""), re.I): E("format D: pinned_comment must say it is a skit")
        if fmt == "C" and "narrat" in json.dumps(post).lower(): W("format C has no voice")

    # ---- rotation vs covered.json (cov is oldest->newest; entries on/after this date are ignored)
    prev = [e for e in cov if date and e.get("date", "") < date][-7:]
    if fmt and fmt != "E" and len(prev) >= 2 and prev[-1].get("format") == fmt and prev[-2].get("format") == fmt: E(f"format {fmt} was used the last 2 days; rotate")
    if fmt and fmt not in ("C", "E") and len(prev) >= 6 and all(e.get("format") != "C" for e in prev[-6:]): E("no format C in the last 6 videos: make a pure animation (C) today")
    if cp and len(prev) >= 2 and prev[-1].get("caption_preset") == cp and prev[-2].get("caption_preset") == cp: E(f"caption preset '{cp}' used the last 2 videos; mix the text styles")
    if slug and any(e.get("slug") == slug for e in cov if date and e.get("date", "") < date): E("slug already published")
    topic = (meta.get("topic") or "").lower()
    if topic and any(topic == (e.get("topic") or "").lower() for e in prev): E("topic already covered in the last 7 videos")

    # ---- story-made backgrounds (PLAN_V4)
    import bgcheck
    bgcheck.check(S, date, prev, E, W)

    # ---- visual recipe (12 axes, see pick_recipe.py): required from 2026-10-17
    rec = meta.get("recipe")
    if not rec:
        (E if date and date >= "2026-10-17" else W)("meta.recipe missing: run python3 shorts/pick_recipe.py <script>")
    else:
        import pick_recipe as PR
        chk = {"layout": PR.LAYOUTS, "caption_style": PR.CAPTION_STYLES + ["off"], "caption_pos": PR.CAPTION_POS, "hook_style": PR.HOOK_STYLES,
               "hook_pos": list(PR.HOOK_POS), "fonts": list(PR.FONTS), "camera": list(PR.CAMERAS), "finish": list(PR.FINISHES),
               "transitions": list(PR.TRANSITIONS), "anim": list(PR.ANIMS)}
        for k, allowed in chk.items():
            if rec.get(k) not in allowed: E(f"recipe.{k} must be one of {allowed}")
        for k in ("family", "sound"):
            if not rec.get(k): E(f"recipe.{k} missing")
        try:
            cap = PR.overrides(rec)["caption"]
            if cap.get("mode") in ("slam", "clean") and cap.get("size", 0) < PR.CAPTION_MIN: E(f"caption size {cap.get('size')} below the readability floor {PR.CAPTION_MIN}")
            if cap.get("mode") == "stack" and cap.get("stack_size", 1) < .7: E("stack caption scale below the readability floor (0.7)")
            if cap.get("mode") == "typeon" and cap.get("typeon_size", 999) < 110: E("typeon caption size below the readability floor (110)")
        except Exception as ex: E(f"recipe cannot be resolved: {ex}")
        if rec.get("caption_style") and cp and rec["caption_style"] != cp: E("meta.caption_preset must equal recipe.caption_style")
        rprev = [e for e in prev if isinstance(e.get("recipe"), dict)]
        if rprev:
            y = rprev[-1]["recipe"]
            if rec.get("layout") == y.get("layout"): E(f"frame layout '{rec.get('layout')}' same as yesterday")
            if rec.get("caption_style") == y.get("caption_style"): E(f"caption style '{rec.get('caption_style')}' same as yesterday")
            for e in rprev:
                d = PR.distance(rec, e["recipe"])
                if d < PR.MIN_DIFF: E(f"recipe differs from {e['date']} on only {d} of 12 axes (need {PR.MIN_DIFF}+): re-run pick_recipe.py")
    if not quiet or errs or warns:
        print(f"{base}: format {fmt} preset {cp} scenes {len(scenes)} words {words} est {est:.0f}s sources {len(srcs)}")
        for w in warns: print("WARN:", w)
        for e in errs: print("ERROR:", e)
    print("OK" if not errs else f"FAILED ({len(errs)} errors)")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
