#!/usr/bin/env python3
"""Daily FredsDesk News run: pick today's news script -> validate -> build video -> (upload) -> log.
Usage: python3 engine/news_daily.py [--file PATH] [--no-upload] [--no-log] [--force]
Picks news/queue/<today>-*.json (Manila date); if none, yesterday's unpublished script; older ones are stale.
Without --file/--force it does nothing if a news video was already logged today (Manila date),
so the push-triggered run, the backup cron run and a watchdog re-run can never publish twice.
Exit 1 (red run, GitHub emails you) if nothing is queued or the script is invalid; nothing is logged then."""
import json, os, re, subprocess, sys, shutil, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from validate_news import validate

def summary(title, msg):
    s = os.environ.get('GITHUB_STEP_SUMMARY')
    if s: open(s, 'a').write(f'### {title}\n{msg}\n')

def fail(msg):
    print('::error::' + msg); summary('News skipped', msg); sys.exit(1)

def manila_today():
    return (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).date()

def main():
    cov_path = os.path.join(ROOT, 'news', 'covered.json')
    cov = json.load(open(cov_path)) if os.path.exists(cov_path) else {'covered': []}
    today = manila_today(); ts = today.isoformat()
    explicit = '--file' in sys.argv
    if not explicit and '--force' not in sys.argv:
        already = [c for c in cov['covered'] if c.get('date') == ts]
        if already:
            msg = f'News "{already[-1]["title"]}" was already published today ({ts}); nothing to do.'
            print(msg); summary('Already done today', msg); return
    q = os.path.join(ROOT, 'news', 'queue')
    if explicit:
        path = os.path.join(ROOT, sys.argv[sys.argv.index('--file') + 1])
        if not os.path.exists(path): fail(f'Script not found: {path}')
    else:
        files = sorted(f for f in os.listdir(q) if re.match(r'\d{4}-\d\d-\d\d-.+\.json$', f)) if os.path.isdir(q) else []
        ok_dates = [ts, (today - datetime.timedelta(days=1)).isoformat()]
        pick = next((f for d in ok_dates for f in files if f.startswith(d + '-')), None)
        if not pick: fail(f'No news script is queued for {ts}. The daily news task must add news/queue/{ts}-slug.json.')
        path = os.path.join(q, pick)
    script, errs, words = validate(path)
    if errs: fail(f'News script {os.path.basename(path)} is invalid:\n- ' + '\n- '.join(errs))
    print(f'Building news: {script["title"]} ({words} words)', flush=True)
    subprocess.run([sys.executable, os.path.join(HERE, 'build.py'), path], check=True)   # build.py refuses >125s
    slug = os.path.splitext(os.path.basename(path))[0]
    out = os.path.join(ROOT, 'output')
    title = re.sub(r'[/\\:*?"<>|]', '-', script['title'])
    label = f'News {ts} - {title}'
    uploads = [(f'{slug}.mp4', f'{label}.mp4'), (f'{slug}.post.txt', f'{label} - post text.txt'), (f'{slug}.preview.jpg', f'{label} - preview.jpg')]
    if '--no-upload' not in sys.argv:
        for src, name in uploads:
            subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'upload_drive.py'), os.path.join(out, src), name], check=True)
    if '--no-log' not in sys.argv:
        cov['covered'].append({'date': ts, 'script_date': script.get('date'), 'title': script['title'],
                               'hook': script['scenes'][0]['narration'], 'sources': [s['name'] for s in script['sources']],
                               'urls': [s['url'] for s in script['sources']], 'status': 'rendered'})
        os.makedirs(os.path.dirname(cov_path), exist_ok=True)
        json.dump(cov, open(cov_path, 'w'), indent=1, ensure_ascii=False)
        if os.path.dirname(os.path.abspath(path)) == os.path.abspath(q):
            os.makedirs(os.path.join(ROOT, 'news', 'archive'), exist_ok=True)
            shutil.move(path, os.path.join(ROOT, 'news', 'archive', os.path.basename(path)))
    summary(f'News ready: {script["title"]}', f'Drive: {label}.mp4' if '--no-upload' not in sys.argv else 'Dry run: not uploaded.')

main()
