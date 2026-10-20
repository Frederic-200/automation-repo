"""Validation of story-made backgrounds (PLAN_V4): drawings (meta.art), per-scene `bg` blocks, variety inside the video and vs the last 7 videos."""
import re

REQUIRED_FROM = "2026-10-17"
NUMBERS_FROM = "2026-10-20"
NUM_WORDS = re.compile(r"\b(two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|billion|trillion|percent|half|double|doubled|triple|tripled)\b", re.I)
ART_STYLES = ("flat", "line", "sticker", "blueprint", "paper")
SHAPES = {"rect", "circle", "ellipse", "line", "poly", "path", "text"}
ROLES = {"ink", "accent", "accent2", "accent3", "paper", "dark", "dim", "bg", "gold", "white", "red", "green", "blue"}
ARRANGEMENTS = {"hero", "scatter", "grid", "orbit", "stream", "stack", "split", "path", "explode", "ring", "tunnel", "wall", "none"}
BACKDROPS = {"mesh", "flow", "contour", "grid", "iso", "rays", "paper", "halftone", "scan", "ribbon", "rings", "stars", "tile"}
ENTER = {"pop", "slide", "drop", "crawl", "draw", "assemble", "fade", "zoom"}
LIVING = {"float", "pulse", "wobble", "drift", "breathe", "blink", "swarm", "spin", "scan"}
LEAVE = {"fall", "dissolve", "shrink", "wipe"}
ACTIONS = {"pop", "grow", "shake", "spin", "flash", "glow", "glitch", "shatter", "open", "part", "remove", "crack", "morph"}
DATA_KINDS = {"ring", "coins", "bars", "gauge", "line", "compare", "number"}
MOTION_WORDS = ENTER | LIVING | LEAVE
BAD_ART = re.compile(r"logo|trademark|colou?r.?wheel|four.?colou?r|swoosh|apple|bitten|knot|sparkle.?star|windows.?flag|google.?g\b", re.I)
SCENE_TYPES_OK = {"story", "chat", "stat", "echo"}


def motion_ok(s):
    return any(w in MOTION_WORDS for w in re.split(r"[^a-z\-]+", str(s).lower()))


def check(S, date, prev, E, W):
    """prev = covered.json entries before this date (oldest -> newest). Returns the bg signature list for logging."""
    meta = S.get("meta") or {}; scenes = S.get("scenes") or []
    needed = bool(date and date >= REQUIRED_FROM)
    uses = any((sc.get("bg") or sc.get("type") == "story") for sc in scenes)
    if not uses:
        (E if needed else W)("story backgrounds missing: every scene needs a `bg` block and meta.art drawings (see WRITING_GUIDE section 11)")
        return []
    art = meta.get("art") or {}
    if meta.get("art_style") not in ART_STYLES: E(f"meta.art_style must be one of {ART_STYLES}")
    if not 2 <= len(art) <= 6: E(f"meta.art needs 2-6 drawings (has {len(art)})")
    for aid, a in art.items():
        sh = (a or {}).get("shapes") or []
        if not 1 <= len(sh) <= 40: E(f"art '{aid}': 1-40 shapes (has {len(sh)})")
        if BAD_ART.search(aid + " " + str(a.get("name", ""))): E(f"art '{aid}': no logos or logo look-alikes; draw our own object and put the name as text")
        for k, s in enumerate(sh):
            t = s.get("t")
            if t not in SHAPES: E(f"art '{aid}' shape {k}: type must be one of {sorted(SHAPES)}")
            c = s.get("c", "ink")
            if c not in ROLES and not re.fullmatch(r"#[0-9a-fA-F]{6}", str(c)): E(f"art '{aid}' shape {k}: colour role must be one of {sorted(ROLES)} or #rrggbb")
            if t == "text" and len(str(s.get("s", ""))) > 14: E(f"art '{aid}' shape {k}: text label max 14 chars")
            if t == "path" and not re.fullmatch(r"[MmLlHhVvCcSsQqTtAaZz0-9eE.,\- ]+", str(s.get("d", ""))): E(f"art '{aid}' shape {k}: invalid path data")
            if t == "path" and len(str(s.get("d", ""))) > 400: E(f"art '{aid}' shape {k}: path too long")
    sigs, arrs, mots, combos = [], [], set(), []
    facts = meta.get("facts") or []
    for i, sc in enumerate(scenes):
        bg = sc.get("bg")
        if sc.get("type") not in SCENE_TYPES_OK and needed: E(f"scene {i}: type '{sc.get('type')}' is retired; use story (or chat/stat/echo with a bg block)")
        if not bg:
            if needed: E(f"scene {i}: missing bg block")
            continue
        if not bg.get("intent"): E(f"scene {i}: bg.intent missing (one line: what should the viewer feel or understand)")
        subj = bg.get("subject") or []
        if not subj: E(f"scene {i}: bg.subject needs at least one drawing id")
        for s_ in subj:
            if s_ not in art: E(f"scene {i}: subject '{s_}' is not in meta.art")
        arr = str(bg.get("arrangement", "")).lower(); parts = [p.strip() for p in re.split(r"[+&]", arr) if p.strip()]
        if not parts or any(p not in ARRANGEMENTS for p in parts): E(f"scene {i}: bg.arrangement must be from {sorted(ARRANGEMENTS)} (combine with +)")
        bd = bg.get("backdrop"); kind = bd if isinstance(bd, str) else (bd or {}).get("kind")
        if kind not in BACKDROPS: E(f"scene {i}: bg.backdrop.kind must be one of {sorted(BACKDROPS)}")
        mo = bg.get("motion") or {}
        if parts != ["none"] and not mo: E(f"scene {i}: bg.motion needs a motion for each subject")
        for sid, m in mo.items():
            if sid not in art: E(f"scene {i}: motion subject '{sid}' is not in meta.art")
            elif not motion_ok(m): E(f"scene {i}: motion '{m}' for '{sid}' has no known word ({sorted(MOTION_WORDS)})")
            else: mots |= {w for w in re.split(r"[^a-z\-]+", str(m).lower()) if w in MOTION_WORDS}
        for b in bg.get("beats") or []:
            sj, _, act = str(b.get("do", "")).partition(".")
            if sj not in art and sj != "*": E(f"scene {i}: beat subject '{sj}' is not in meta.art")
            if re.split(r"[\s:]+", act)[0] not in ACTIONS: E(f"scene {i}: beat action '{act}' must start with one of {sorted(ACTIONS)}")
            if "on" not in b and "t" not in b: E(f"scene {i}: beat needs `on` (a spoken keyword) or `t`")
        if len(bg.get("texture_words") or []) > 4: E(f"scene {i}: texture_words max 4")
        d = bg.get("data")
        if d:
            if d.get("kind") not in DATA_KINDS: E(f"scene {i}: data.kind must be one of {sorted(DATA_KINDS)}")
            if not isinstance(d.get("fact"), int) or not 0 <= d["fact"] < len(facts): E(f"scene {i}: data.fact must be the index of the meta.facts entry that backs the number")

        # every spoken number must become a picture (giant number or data scene)
        spoken = " ".join(sc.get("lines") or []) if isinstance(sc.get("lines"), list) else ""
        spoken = " ".join(l if isinstance(l, str) else str(l.get("text", "")) for l in (sc.get("lines") or []))
        nums = bg.get("numbers") or []
        if date and date >= NUMBERS_FROM and NUM_WORDS.search(spoken) and not nums and not bg.get("data"):
            E(f"scene {i}: the narration says a number ('{NUM_WORDS.search(spoken).group(0)}') but the scene shows none: add bg.numbers [{{\"text\": \"27% > 9%\", \"fact\": 0, \"on\": \"keyword\"}}] or a bg.data scene")
        for k, nn in enumerate(nums):
            if not isinstance(nn, dict) or not nn.get("text"): E(f"scene {i}: bg.numbers[{k}] must be an object with text and fact"); continue
            if len(str(nn["text"])) > 18: E(f"scene {i}: bg.numbers[{k}].text max 18 chars so it can be shown huge")
            if not isinstance(nn.get("fact"), int) or not 0 <= nn["fact"] < len(facts): E(f"scene {i}: bg.numbers[{k}].fact must be the index of the meta.facts entry that backs it")
        if BAD_ART.search(str(bg.get("intent", ""))) and "logo" in str(bg.get("intent", "")).lower(): E(f"scene {i}: no logos")
        sigs.append(f"{'+'.join(parts)}|{kind}"); arrs.append("+".join(parts)); combos.append(f"{'+'.join(parts)}|{kind}")
    if sigs:
        if len(set(a.split('+')[0] for a in arrs)) < 2: E("use at least 2 different arrangements in a video")
        if len(mots) < 3: E(f"use at least 3 different motion words across the video (has {sorted(mots)})")
        if len(set(combos)) < len(combos): E("an arrangement+backdrop combination repeats inside the video")
        if len(set(c.split('|')[1] for c in combos)) < min(3, len(combos)): E("use at least 3 different backdrops in a video")
        past = {}
        for e in prev[-7:]:
            for s_ in e.get("bg_sigs") or []: past[s_] = e.get("date")
        for s_ in sigs:
            if s_ in past: E(f"background '{s_}' was already used on {past[s_]} (last 7 videos): change arrangement or backdrop")
        ys = [e for e in prev if e.get("bg_sigs")]
        if ys:
            y0 = ys[-1]["bg_sigs"][0].split("|"); m0 = sigs[0].split("|")
            if y0[0] == m0[0] or y0[1] == m0[1]: E("opening scene must differ from yesterday's opening on both arrangement and backdrop")
        ids = set(art)
        for e in prev[-3:]:
            old = set(e.get("art_ids") or [])
            if old and len(ids & old) > len(ids) / 2: W(f"more than half of the drawings repeat {e.get('date')}: draw new objects for this story")
    return sigs


def signatures(S):
    """arrangement|backdrop per scene (what covered.json stores)."""
    out = []
    for sc in S.get("scenes") or []:
        bg = sc.get("bg")
        if not bg: continue
        bd = bg.get("backdrop"); kind = bd if isinstance(bd, str) else (bd or {}).get("kind")
        parts = [p.strip() for p in re.split(r"[+&]", str(bg.get("arrangement", "")).lower()) if p.strip()]
        out.append(f"{'+'.join(parts)}|{kind}")
    return out
