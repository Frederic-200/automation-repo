"""News script validator: reject a FredsDesk News script before any expensive work happens."""
import json, sys, re, os
TYPES = {
 'breaking': ['lines', 'accent'], 'story': ['source', 'headline', 'facts'], 'quote': ['text', 'who'],
 'timeline': ['events'], 'why': ['points'], 'engage': ['line'], 'takeaways': ['points'], 'sources_end': ['sources'],
 # reused from the lessons
 'concept': ['term', 'definition'], 'analogy': ['sentence', 'bricks'], 'stat': ['label'], 'compare': ['left', 'right'],
 'flow': ['steps'], 'chat': ['messages'], 'anatomy': ['parts'], 'map': ['points', 'query'], 'network': ['layers', 'labels'],
}
MIN_WORDS, MAX_WORDS = 170, 300
MAX_SECONDS = 120

def _norm(x): return re.sub(r'[^a-z0-9]+', ' ', x.lower()).strip()

def validate(path):
    s = json.load(open(path)); errs = []
    for k in ('kind', 'date', 'title', 'scenes', 'post', 'ticker', 'sources'):
        if k not in s: errs.append(f'missing top-level "{k}"')
    if s.get('kind') != 'news': errs.append('kind must be "news"')
    if s.get('date') and not re.match(r'^\d{4}-\d\d-\d\d$', s['date']): errs.append('date must be YYYY-MM-DD (Manila date)')
    m = re.match(r'(\d{4}-\d\d-\d\d)-', os.path.basename(path))
    if m and s.get('date') and m.group(1) != s['date']: errs.append(f'filename date {m.group(1)} does not match "date" {s["date"]}')
    if len(s.get('sources', [])) < 2: errs.append('need at least 2 independent sources in "sources"')
    for x in s.get('sources', []):
        if not isinstance(x, dict) or not x.get('name') or not str(x.get('url', '')).startswith('http'): errs.append('each source needs "name" and an http "url"')
    if not 3 <= len(s.get('ticker', [])) <= 6: errs.append('ticker needs 3-6 short headlines')
    sc = s.get('scenes', [])
    if not sc: errs.append('no scenes')
    else:
        if sc[0].get('type') != 'breaking': errs.append('first scene must be "breaking"')
        if sc[-1].get('type') != 'sources_end': errs.append('last scene must be "sources_end"')
        if sum(1 for c in sc if c.get('type') == 'engage') != 1: errs.append('exactly one "engage" (like/share) scene is required')
        if 'takeaways' not in [c.get('type') for c in sc]: errs.append('a "takeaways" scene is required before the end card')
        if not (sc[0].get('narration', '').lower().lstrip().startswith('did you know')): errs.append('opening narration must start with "Did you know"')
        if sc[-1].get('type') == 'sources_end' and 'follow' not in sc[-1].get('narration', '').lower(): errs.append('closing narration must ask people to follow')
    words = 0
    for i, c in enumerate(sc):
        t = c.get('type')
        if t not in TYPES: errs.append(f'scene {i}: unknown type {t!r}'); continue
        for r in TYPES[t]:
            if r not in c: errs.append(f'scene {i} ({t}): missing "{r}"')
        n = len(c.get('narration', '').split())
        if n == 0: errs.append(f'scene {i}: empty narration')
        words += n
        if t == 'analogy' and ''.join(c.get('bricks', [])).replace(' ', '') != c.get('sentence', '').replace(' ', ''): errs.append('analogy: bricks must spell the sentence')
        if t == 'story' and len(c.get('headline', '')) > 110: errs.append('story: headline over 110 characters')
        if t == 'story' and not 1 <= len(c.get('facts', [])) <= 3: errs.append('story: 1-3 facts')
        if t in ('why', 'takeaways') and not 2 <= len(c.get('points', [])) <= 3: errs.append(f'{t}: 2-3 points')
        if t == 'timeline' and not 2 <= len(c.get('events', [])) <= 4: errs.append('timeline: 2-4 events')
    if sc and not MIN_WORDS <= words <= MAX_WORDS: errs.append(f'narration is {words} words (need {MIN_WORDS}-{MAX_WORDS})')
    for k in ('title', 'description', 'hashtags', 'pinned_comment'):
        if k not in s.get('post', {}): errs.append(f'post: missing "{k}"')
    no_dates_on_screen(sc, errs)
    story_checks(s, errs)
    return s, errs, words

DATE_RE = re.compile(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+\d{1,2}\b|\b\d{4}-\d\d-\d\d\b|\b(19|20)\d\d\b|\b(today|yesterday|tomorrow)\b', re.I)
def no_dates_on_screen(scenes, errs):
    """the user wants no dates in the video: on-screen text (everything except narration/cues) must not contain one"""
    def strings(x):
        if isinstance(x, str): yield x
        elif isinstance(x, list):
            for v in x: yield from strings(v)
        elif isinstance(x, dict):
            for k, v in x.items():
                if k not in ('narration', 'cues', 'type', 'icon', 'icons'): yield from strings(v)
    for i, c in enumerate(scenes):
        for txt in strings(c):
            if DATE_RE.search(txt): errs.append(f'scene {i} ({c.get("type")}): no dates on screen, found {DATE_RE.search(txt).group(0)!r} in {txt!r}')

def story_checks(s, errs):
    """don't cover the same story twice"""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try: covered = json.load(open(os.path.join(root, 'news', 'covered.json')))['covered']
    except Exception: return
    t = _norm(s.get('title', ''))
    for c in covered:
        if c.get('date') != s.get('date') and _norm(c.get('title', '')) == t: errs.append(f'story already covered on {c.get("date")}')

if __name__ == '__main__':
    s, errs, w = validate(sys.argv[1])
    print(f'{len(s.get("scenes", []))} scenes, {w} narration words')
    if errs: print('INVALID:'); [print(' -', e) for e in errs]; sys.exit(1)
    print('OK')
