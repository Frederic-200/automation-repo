"""Exact word times for a synthesized line (replaces the length-based estimate in voice.word_times).

Method (offline; sherpa-onnx and the zipformer model are Apache-2.0):
  1. A streaming zipformer recognizer returns a timestamp per token for the synthesized line.
  2. Recognized words are matched to the script words with difflib (ASR slips do not shift the rest).
  3. The recognizer emits tokens LATE (chunked decoding, measured 0.3-0.39 s). Each line is trimmed to
     its first sound, so word 1 starts at the first energy rise: that measures the delay for the line.
     Every matched word = token time - delay, snapped to an energy rise within +/-70 ms.
  4. Unmatched words are interpolated between neighbouring anchors by the old length weights.
Falls back to the length-based estimate when sherpa-onnx or the model is missing.
Env: VIDEO_KIT_ASR_DIR overrides the model directory.
"""
import difflib, os, re, sys
import numpy as np
from scipy import signal

CACHE = os.environ.get("VIDEO_KIT_CACHE", os.path.expanduser("~/.cache/video-kit"))
ASR_DIR = os.environ.get("VIDEO_KIT_ASR_DIR", os.path.join(CACHE, "models", "sherpa-onnx-streaming-zipformer-en-2023-06-26"))
SFX = "epoch-99-avg-1-chunk-16-left-128"
_REC = None
STATS = []   # per-line alignment stats, written into voice.json
LAGS = []    # per-line recognizer delay measured from lines whose first word was matched


def _recognizer():
    global _REC
    if _REC is None:
        import sherpa_onnx
        m = ASR_DIR.rstrip("/") + "/"
        _REC = sherpa_onnx.OnlineRecognizer.from_transducer(
            tokens=m + "tokens.txt", encoder=f"{m}encoder-{SFX}.int8.onnx",
            decoder=f"{m}decoder-{SFX}.int8.onnx", joiner=f"{m}joiner-{SFX}.int8.onnx",
            num_threads=2, sample_rate=16000, feature_dim=80, decoding_method="greedy_search")
    return _REC


def _norm(w): return re.sub(r"[^a-z0-9]", "", w.lower())


def asr_words(x48, sr=48000):
    """[(word, t_sec)] from recognizer tokens; a token with a leading space starts a new word."""
    y = signal.resample_poly(x48, 16000, sr).astype(np.float32)
    rec = _recognizer(); s = rec.create_stream()
    s.accept_waveform(16000, y); s.accept_waveform(16000, np.zeros(int(.6 * 16000), np.float32)); s.input_finished()
    while rec.is_ready(s): rec.decode_stream(s)
    r = rec.get_result_all(s)
    out = []
    for tok, ts in zip(r.tokens, r.timestamps):
        if tok.startswith(" ") or not out: out.append([tok.strip(), float(ts)])
        else: out[-1][0] += tok
    return [(w, t) for w, t in out]


def onset_candidates(x48, sr=48000, hop=.005):
    """Times (s) of energy rises: peaks of the positive derivative of smoothed log energy."""
    n = int(hop * sr); m = len(x48) // n
    e = np.sqrt((x48[: m * n].reshape(m, n) ** 2).mean(1)) + 1e-6
    le = 20 * np.log10(e); le = np.convolve(le, np.ones(3) / 3, "same")
    d = np.maximum(0, np.diff(le, prepend=le[0]))
    d = np.convolve(d, np.ones(3) / 3, "same")
    pk = [i for i in range(1, m - 1) if d[i] >= d[i - 1] and d[i] > d[i + 1] and d[i] > 1.2]
    return np.array(pk) * hop, d


def exact_words(toks, kflags, start, dur, x48, weights, sr=48000):
    """toks: clean script words; returns [{"w","k","s","e"}] in absolute time (start offset added)."""
    asr = asr_words(x48, sr)
    a_n = [_norm(w) for w, _ in asr]; s_n = [_norm(w) for w in toks]
    sm = difflib.SequenceMatcher(None, s_n, a_n, autojunk=False)
    anchor = {}
    for blk in sm.get_matching_blocks():
        for k in range(blk.size): anchor[blk.a + k] = asr[blk.b + k][1]
    cands, _ = onset_candidates(x48, sr)
    v0 = float(cands[0]) if len(cands) else 0.0
    if 0 in anchor: lag = anchor[0] - v0; LAGS.append(lag)
    else: lag = float(np.median(LAGS)) if LAGS else .30
    lag = min(max(lag, .05), .50)
    st, snapped = {}, {}
    for i, t in anchor.items():
        tc = t - lag                                   # delay-corrected time
        c = cands[(cands >= tc - .07) & (cands <= tc + .07)]   # snap only to a very near energy rise
        if len(c) and i != 0: snapped[i] = float(c[np.argmin(np.abs(c - tc))]); st[i] = snapped[i]
        else: st[i] = max(tc, 0.0) if i != 0 else v0
    n = len(toks); ws = np.array(weights, float); cum = np.concatenate([[0], np.cumsum(ws)]) / ws.sum()
    voiced0 = v0
    # interpolate unmatched words between anchors using weight proportions
    T = [None] * n
    for i, v in st.items(): T[i] = v
    known = [i for i in range(n) if T[i] is not None]
    if not known:
        T = [cum[i] * dur for i in range(n)]
    else:
        for i in range(n):
            if T[i] is not None: continue
            lo = max([k for k in known if k < i], default=None); hi = min([k for k in known if k > i], default=None)
            if lo is None: lo_t, lo_c = voiced0, 0.0
            else: lo_t, lo_c = T[lo], cum[lo]
            if hi is None: hi_t, hi_c = dur, 1.0
            else: hi_t, hi_c = T[hi], cum[hi]
            span = max(hi_c - lo_c, 1e-6); T[i] = lo_t + (cum[i] - lo_c) / span * (hi_t - lo_t)
    for i in range(1, n): T[i] = max(T[i], T[i - 1] + .06)   # strictly increasing
    out = []
    for i, w in enumerate(toks):
        s = start + T[i]; e = start + (T[i + 1] - .02 if i + 1 < n else dur)
        if re.search(r"[.,!?;:]$", w): e -= min(.18, max(0, (e - s) * .35))
        out.append({"w": w, "k": 1 if kflags[i] else 0, "s": round(s, 3), "e": round(max(e, s + .06), 3)})
    STATS.append({"words": n, "asr_words": len(asr), "matched": len(anchor), "snapped": len(snapped), "lag_ms": round(lag * 1000), "v0_ms": round(v0 * 1000)})
    return out
