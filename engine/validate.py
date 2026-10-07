"""Script validator: reject a lesson script before any expensive work happens."""
import json, sys, re
TYPES = {
 'hook': ['lines','accent'], 'promise': [], 'concept': ['term','definition'], 'analogy': ['sentence','bricks'],
 'tokens': ['sentence','chips','ids'], 'versus': ['word','chips','question'], 'recap': ['points'],
 'quiz_end': ['question','options','teaser'],
 'stat': ['label'], 'network': ['layers','labels'], 'chat': ['messages'], 'compare': ['left','right'],
 'anatomy': ['parts'], 'map': ['points','query'], 'flow': ['steps'],
}
MAX_WORDS = 215
def validate(path):
    s = json.load(open(path)); errs = []
    for k in ('lesson','title','scenes','post','season'):
        if k not in s: errs.append(f'missing top-level "{k}"')
    sc = s.get('scenes', [])
    if not sc: errs.append('no scenes')
    else:
        if sc[0].get('type') != 'hook': errs.append('first scene must be "hook"')
        if sc[-1].get('type') != 'quiz_end': errs.append('last scene must be "quiz_end"')
    words = 0
    for i, c in enumerate(sc):
        t = c.get('type')
        if t not in TYPES: errs.append(f'scene {i}: unknown type {t!r}'); continue
        for r in TYPES[t]:
            if r not in c: errs.append(f'scene {i} ({t}): missing "{r}"')
        n = len(c.get('narration','').split())
        if n == 0: errs.append(f'scene {i}: empty narration')
        words += n
        if t == 'hook' and ' '.join(c.get('lines',[])).lower().split() != re.sub(r'\s+',' ',c.get('narration','')).lower().split():
            errs.append('hook lines must spell out the narration exactly')
        if t == 'tokens' and len(c.get('chips',[])) != len(c.get('ids',[])): errs.append('tokens: chips/ids length mismatch')
        if t == 'tokens' and ''.join(c.get('chips',[])).replace(' ','').lower() != c.get('sentence','').replace(' ','').lower():
            errs.append('tokens: chips must spell the sentence')
        if t == 'analogy' and ''.join(c.get('bricks',[])).replace(' ','') != c.get('sentence','').replace(' ',''):
            errs.append('analogy: bricks must spell the sentence')
        if t == 'versus' and ''.join(c.get('chips',[])) != c.get('word'): errs.append('versus: chips must spell the word')
    if words > MAX_WORDS: errs.append(f'narration is {words} words (max {MAX_WORDS})')
    for k in ('title','description','hashtags','pinned_comment'):
        if k not in s.get('post',{}): errs.append(f'post: missing "{k}"')
    curriculum_checks(s, path, errs)
    return s, errs, words

def _norm(x): return re.sub(r'[^a-z0-9]+',' ',x.lower()).strip()
def curriculum_checks(s, path, errs):
    """script must match the curriculum: right title, teaser = next lesson, filename number, fresh hook"""
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        L = {l['lesson']: l for l in json.load(open(os.path.join(root, 'curriculum', 'lessons.json')))['lessons']}
        covered = json.load(open(os.path.join(root, 'curriculum', 'covered.json')))['covered']
    except Exception: return
    n = s.get('lesson')
    m = re.match(r'(\d+)-', os.path.basename(path))
    if m and int(m.group(1)) != n: errs.append(f'filename number {m.group(1)} does not match lesson {n}')
    if n in L and _norm(L[n]['title']) != _norm(s.get('title','')): errs.append(f'title must be "{L[n]["title"]}" (curriculum)')
    if n in L and s.get('season') != L[n]['season']: errs.append(f'season must be "{L[n]["season"]}"')
    last = s.get('scenes', [{}])[-1]
    if (n or 0) + 1 in L and _norm(last.get('teaser','')) != _norm(L[n + 1]['title']): errs.append(f'teaser must be the next lesson: "{L[n + 1]["title"]}"')
    if 'tomorrow' not in last.get('narration','').lower(): errs.append('quiz_end narration must contain "Tomorrow:" teaser')
    hook = _norm(s.get('scenes', [{}])[0].get('narration',''))
    for c in covered:
        if c['lesson'] != n and _norm(c.get('hook','')) == hook: errs.append(f'hook repeats lesson {c["lesson"]}')
if __name__ == '__main__':
    s, errs, w = validate(sys.argv[1])
    print(f'{len(s.get("scenes",[]))} scenes, {w} narration words')
    if errs: print('INVALID:'); [print(' -', e) for e in errs]; sys.exit(1)
    print('OK')
