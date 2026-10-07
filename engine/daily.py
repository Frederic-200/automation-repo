#!/usr/bin/env python3
"""Daily run: pick the next lesson script -> validate -> build video -> (upload) -> log as covered.
Usage: python3 engine/daily.py [--lesson N] [--no-upload] [--no-log] [--force]
Without --lesson/--force it does nothing if a lesson was already logged today (Manila date),
so a late scheduled run plus a watchdog re-run can never publish two lessons in one day.
Exit 1 (red run, GitHub emails you) if nothing is queued or the script is invalid; nothing is logged then."""
import json, os, re, subprocess, sys, shutil, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from validate import validate

def fail(msg):
    print('::error::' + msg)
    s = os.environ.get('GITHUB_STEP_SUMMARY')
    if s: open(s, 'a').write('### Lesson skipped\n' + msg + '\n')
    sys.exit(1)

def manila_today():
    return (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).date().isoformat()

def main():
    cov_path = os.path.join(ROOT, 'curriculum', 'covered.json')
    cov = json.load(open(cov_path)); done = {c['lesson'] for c in cov['covered']}
    today = manila_today()
    if '--lesson' not in sys.argv and '--force' not in sys.argv:
        already = [c for c in cov['covered'] if c.get('date') == today]
        if already:
            msg = f'Lesson {already[-1]["lesson"]} was already published today ({today}); nothing to do.'
            print(msg)
            s = os.environ.get('GITHUB_STEP_SUMMARY')
            if s: open(s, 'a').write('### Already done today\n' + msg + '\n')
            return
    q = os.path.join(ROOT, 'queue')
    files = {}
    for f in sorted(os.listdir(q)):
        m = re.match(r'(\d+)-.*\.json$', f)
        if m: files[int(m.group(1))] = f
    want = int(sys.argv[sys.argv.index('--lesson') + 1]) if '--lesson' in sys.argv else None
    todo = sorted(n for n in files if n not in done) if want is None else [want]
    if not todo or todo[0] not in files:
        fail('No lesson script is queued. The weekly writing task must add queue/NNN-slug.json files.')
    n = todo[0]; path = os.path.join(q, files[n])
    script, errs, words = validate(path)
    if errs: fail(f'Lesson {n} script is invalid:\n- ' + '\n- '.join(errs))
    nxt = n + 1
    print(f'Building lesson {n}: {script["title"]} ({words} words)', flush=True)
    subprocess.run([sys.executable, os.path.join(HERE, 'build.py'), path], check=True)   # build.py refuses >90s
    slug = os.path.splitext(files[n])[0]
    out = os.path.join(ROOT, 'output')
    label = f'Lesson {n:02d} - {re.sub(r"[/\\\\]", "-", script["title"])}'
    uploads = [(f'{slug}.mp4', f'{label}.mp4'), (f'{slug}.post.txt', f'{label} - post text.txt'), (f'{slug}.preview.jpg', f'{label} - preview.jpg')]
    if '--no-upload' not in sys.argv:
        for src, name in uploads:
            subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'upload_drive.py'), os.path.join(out, src), name], check=True)
    if '--no-log' not in sys.argv:
        hook = next(s for s in script['scenes'] if s['type'] == 'hook')['narration']
        ana = next((s for s in script['scenes'] if s['beat'] == 'analogy'), {})
        ex = next((s for s in script['scenes'] if s['beat'] == 'example'), {})
        cov['covered'].append({'lesson': n, 'title': script['title'], 'date': today, 'hook': hook,
                               'analogy': ana.get('narration', '')[:140], 'example': ex.get('narration', '')[:140], 'status': 'rendered'})
        json.dump(cov, open(cov_path, 'w'), indent=1, ensure_ascii=False)
        os.makedirs(os.path.join(ROOT, 'archive'), exist_ok=True)
        shutil.move(path, os.path.join(ROOT, 'archive', files[n]))
    s = os.environ.get('GITHUB_STEP_SUMMARY')
    if s: open(s, 'a').write(f'### Lesson {n} ready: {script["title"]}\nUploaded to Google Drive: {label}\n')

main()
