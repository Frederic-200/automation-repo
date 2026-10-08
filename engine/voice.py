"""Offline narration: script.json -> voice.wav + timeline.json (per-scene and per-word timings).
Uses Kokoro (open-source, runs on CPU, no network at render time).
Usage: python3 voice.py <script.json> <outdir> [--voice am_michael] [--speed 1.0]"""
import json, re, sys, subprocess, os
import numpy as np, soundfile as sf

LEAD, TAIL, MAXDUR = 0.15, 0.35, 88.0
PAUSE = {',': .12, ';': .20, ':': .20, '—': .15, '.': .30, '?': .34, '!': .30}
SR = 24000

def clauses(text):
    """split narration into clauses, keeping punctuation attached"""
    parts = re.findall(r'[^,;:.!?—]+[,;:.!?—]*\s*', text)
    return [p.strip() for p in parts if p.strip()]

def trim(a, thr=0.004, keep=int(0.012 * SR)):
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx) == 0: return a
    return a[max(0, idx[0] - keep): min(len(a), idx[-1] + keep)]

def fade(a, n=int(0.006 * SR)):
    a = a.copy(); n = min(n, len(a) // 2)
    a[:n] *= np.linspace(0, 1, n); a[-n:] *= np.linspace(1, 0, n); return a

def main():
    script_path, outdir = sys.argv[1], sys.argv[2]
    script = json.load(open(script_path))
    voice = script.get('voice', 'auto'); speed = 1.0
    if voice == 'auto':   # daily rotation from voices.json
        cyc = json.load(open(os.path.join(os.path.dirname(__file__), 'voices.json')))['cycle']
        voice = cyc[(int(script['lesson']) - 1) % len(cyc)]
    if '--voice' in sys.argv: voice = sys.argv[sys.argv.index('--voice') + 1]
    if '--speed' in sys.argv: speed = float(sys.argv[sys.argv.index('--speed') + 1])
    # "AI" must stay "AI": the engine already says "ay-eye"; "A I" makes it read the article "uh" ("uh-eye")
    say = {k: v for k, v in script.get('say', {}).items() if not re.fullmatch(r'A\s+I[.,;:!?]*', v.strip())}
    os.makedirs(outdir, exist_ok=True)
    from kokoro_onnx import Kokoro
    k = Kokoro(os.path.join(os.path.dirname(__file__), '..', 'models', 'kokoro-v1.0.int8.onnx'),
               os.path.join(os.path.dirname(__file__), '..', 'models', 'voices-v1.0.bin'))
    lang = 'en-gb' if voice.startswith('b') else 'en-us'

    blocks, scenes_tl, t = [], [], 0.0
    for i, sc in enumerate(script['scenes']):
        clip_parts, words, pos = [np.zeros(int(LEAD * SR), dtype=np.float32)], [], LEAD
        for cl in clauses(sc['narration']):
            disp = cl.split()
            # keep trailing punctuation for prosody, apply pronunciation overrides to the bare word
            sp_words = []
            for w in disp:
                bare = w.rstrip('.,;:!?—'); tail = w[len(bare):]
                sp_words.append(say.get(bare, bare) + tail)
            audio, _ = k.create(' '.join(sp_words), voice=voice, speed=speed, lang=lang)
            audio = fade(trim(audio.astype(np.float32)))
            dur = len(audio) / SR
            wts = [len(re.sub(r'\W', '', s)) + 1.5 for s in sp_words]
            tot = sum(wts); acc = 0.0
            for w, wt in zip(disp, wts):
                words.append({'w': w, 't0': round(t + pos + acc / tot * dur, 3), 't1': round(t + pos + (acc + wt) / tot * dur, 3)})
                acc += wt
            clip_parts.append(audio); pos += dur
            pz = PAUSE.get(cl[-1], 0.1) if cl[-1] in PAUSE else 0.1
            clip_parts.append(np.zeros(int(pz * SR), dtype=np.float32)); pos += pz
        voice_end = pos
        clip_parts.append(np.zeros(int(TAIL * SR), dtype=np.float32)); pos += TAIL
        blocks.append(np.concatenate(clip_parts))
        scenes_tl.append({'i': i, 'type': sc['type'], 'start': round(t, 3), 'end': round(t + pos, 3),
                          'voice_start': round(t + LEAD, 3), 'voice_end': round(t + voice_end - 0.1, 3),
                          'words': words, 'props': sc})
        t += pos
        print(f'scene {i} {sc["type"]:9s} {pos:5.1f}s', flush=True)
    audio = np.concatenate(blocks)
    dur = len(audio) / SR
    stretch = 1.0
    if dur > MAXDUR:
        stretch = dur / MAXDUR + 0.002
        print(f'too long ({dur:.1f}s) -> tempo x{stretch:.3f}')
    sf.write(os.path.join(outdir, 'voice_raw.wav'), audio, SR)
    if stretch > 1.0:
        if stretch > 1.15: sys.exit(f'script needs {stretch:.2f}x speed-up; shorten the narration')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(outdir, 'voice_raw.wav'), '-af', f'atempo={stretch:.4f}',
                        os.path.join(outdir, 'voice.wav')], check=True)
        for s in scenes_tl:
            for key in ('start', 'end', 'voice_start', 'voice_end'): s[key] = round(s[key] / stretch, 3)
            for w in s['words']: w['t0'] = round(w['t0'] / stretch, 3); w['t1'] = round(w['t1'] / stretch, 3)
        dur /= stretch
    else:
        os.replace(os.path.join(outdir, 'voice_raw.wav'), os.path.join(outdir, 'voice.wav'))
    tl = {'fps': 30, 'duration': round(dur, 3), 'lesson': script['lesson'], 'season': script['season'],
          'title': script['title'], 'voice': voice, 'scenes': scenes_tl}
    json.dump(tl, open(os.path.join(outdir, 'timeline.json'), 'w'), indent=1)
    open(os.path.join(outdir, 'timeline.js'), 'w').write('window.TIMELINE=' + json.dumps(tl) + ';')
    print(f'voice done: {dur:.1f}s total, tempo {stretch:.3f}')

main()
