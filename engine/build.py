"""One command per lesson:  python3 engine/build.py scripts/004-what-is-a-token.json [--reuse-voice]
validate -> narration + timings -> frames -> sound -> MP4 + post.txt + preview sheet"""
import json, os, subprocess, sys, shutil, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from validate import validate
from validate_news import validate as validate_news

def run(cmd, **kw):
    print('>', ' '.join(cmd) if isinstance(cmd, list) else cmd, flush=True); subprocess.run(cmd, check=True, **kw)

def main():
    path = sys.argv[1]; reuse = '--reuse-voice' in sys.argv; music = '--music' in sys.argv
    voice = sys.argv[sys.argv.index('--voice') + 1] if '--voice' in sys.argv else None
    is_news = json.load(open(path)).get('kind') == 'news'
    script, errs, words = (validate_news if is_news else validate)(path)
    if errs: sys.exit('INVALID SCRIPT:\n - ' + '\n - '.join(errs))
    slug = os.path.splitext(os.path.basename(path))[0]; tag = ('.' + voice) if voice else ''
    out = os.path.join(ROOT, 'build', ('news-' + slug if is_news else slug.split('-')[0]) + ('-' + voice if voice else '')); os.makedirs(out, exist_ok=True)
    tlp = os.path.join(out, 'timeline.json')
    if not (reuse and os.path.exists(tlp)):
        run([sys.executable, os.path.join(HERE, 'voice.py'), path, out] + (['--voice', voice] if voice else []))
    tl = json.load(open(tlp))                                   # refresh visual props (cues, text) without re-synthesising
    for s, p in zip(tl['scenes'], script['scenes']): s['props'] = p
    json.dump(tl, open(tlp, 'w'), indent=1); open(os.path.join(out, 'timeline.js'), 'w').write('window.TIMELINE=' + json.dumps(tl) + ';')
    limit = 125 if is_news else 90
    if tl['duration'] > limit: sys.exit(f'video is {tl["duration"]:.1f}s, over the {limit}s limit')
    shutil.rmtree(os.path.join(out, 'frames'), ignore_errors=True)
    run(['node', os.path.join(HERE, 'render.js'), out, '2'])
    run([sys.executable, os.path.join(HERE, 'audio.py'), out] + (['--music'] if music else []))
    mp4 = os.path.join(ROOT, 'output', slug + tag + '.mp4'); os.makedirs(os.path.dirname(mp4), exist_ok=True)
    run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(tl['fps']), '-i', os.path.join(out, 'frames', '%05d.jpg'), '-i', os.path.join(out, 'mix.wav'),
         '-af', 'loudnorm=I=-14:TP=-1.5:LRA=9', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
         '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', mp4])
    post = script['post']
    srcs = ('\n\nSOURCES\n' + '\n'.join(f"{x['name']}: {x['url']}" for x in script['sources'])) if is_news else ''
    open(os.path.join(ROOT, 'output', slug + '.post.txt'), 'w').write(
        f"TITLE\n{post['title']}\n\nDESCRIPTION\n{post['description']}\n\n{' '.join(post['hashtags'])}\n\nPINNED COMMENT (post after publishing)\n{post['pinned_comment']}{srcs}\n")
    # preview sheet: one frame from each scene, so a human can sanity-check in two seconds
    from PIL import Image
    fr = sorted(glob.glob(os.path.join(out, 'frames', '*.jpg'))); picks = [fr[min(len(fr) - 1, int((s['start'] + (s['end'] - s['start']) * .75) * tl['fps']))] for s in tl['scenes']]
    sheet = Image.new('RGB', (4 * 270, 3 * 480))
    for i, f in enumerate(picks[:12]): sheet.paste(Image.open(f).resize((270, 480)), ((i % 4) * 270, (i // 4) * 480))
    sheet.save(os.path.join(ROOT, 'output', slug + tag + '.preview.jpg'), quality=85)
    print(f'DONE {mp4}  {tl["duration"]:.1f}s  ({words} words)')
main()
