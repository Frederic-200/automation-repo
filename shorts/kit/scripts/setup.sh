#!/usr/bin/env bash
# video-kit setup: idempotent, safe to run every session (~1-2 min first time, ~2 s after).
# Cache lives in $VIDEO_KIT_CACHE (default ~/.cache/video-kit): node_modules, Kokoro models, soundfonts.
set -u
CACHE="${VIDEO_KIT_CACHE:-$HOME/.cache/video-kit}"
mkdir -p "$CACHE/models" "$CACHE/node"
ok(){ printf '  [ok] %s\n' "$1"; }
bad(){ printf '  [!!] %s\n' "$1"; FAIL=1; }
FAIL=0
echo "video-kit setup -> $CACHE"

# 1. Python packages
python3 - <<'PY' 2>/dev/null || pip install -q --break-system-packages numpy scipy soundfile mido pillow kokoro-onnx >/dev/null 2>&1
import numpy, scipy, soundfile, mido, PIL, kokoro_onnx
PY
python3 -c "import numpy, scipy, soundfile, mido, PIL, kokoro_onnx" 2>/dev/null && ok "python: numpy scipy soundfile mido pillow kokoro-onnx" || bad "python packages (pip install --break-system-packages numpy scipy soundfile mido pillow kokoro-onnx)"

# 2. System tools
command -v ffmpeg >/dev/null && ok "ffmpeg" || bad "ffmpeg missing (apt-get install -y ffmpeg)"
if ! command -v fluidsynth >/dev/null; then
  (apt-get install -y -qq fluidsynth >/dev/null 2>&1 || (apt-get update -qq >/dev/null 2>&1; apt-get install -y -qq fluidsynth >/dev/null 2>&1)) || true
fi
command -v fluidsynth >/dev/null && ok "fluidsynth" || echo "  [--] fluidsynth unavailable: music falls back to the built-in numpy synth"

# 3. Soundfont (first found wins; GeneralUser GS > FluidR3 > any GM bank)
SF=""
for f in "$CACHE/GeneralUser-GS.sf2" /usr/share/sounds/sf2/FluidR3_GM.sf2 /usr/share/sounds/sf2/default-GM.sf2 /usr/share/sounds/sf2/TimGM6mb.sf2; do
  [ -f "$f" ] && { SF="$f"; break; }
done
if [ -z "$SF" ] && command -v fluidsynth >/dev/null; then
  apt-get install -y -qq fluid-soundfont-gm >/dev/null 2>&1 && SF=/usr/share/sounds/sf2/FluidR3_GM.sf2
fi
[ -n "$SF" ] && { ok "soundfont $SF"; echo "$SF" > "$CACHE/soundfont.txt"; } || echo "  [--] no soundfont: numpy synth fallback"

# 4. Kokoro voice models (GitHub release thewh1teagle/kokoro-onnx model-files-v1.0)
BASE=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
for m in kokoro-v1.0.int8.onnx voices-v1.0.bin; do
  if [ ! -s "$CACHE/models/$m" ]; then
    curl -fsSL --retry 2 -o "$CACHE/models/$m.part" "$BASE/$m" && mv "$CACHE/models/$m.part" "$CACHE/models/$m"
  fi
  [ -s "$CACHE/models/$m" ] && ok "model $m" || bad "model $m (download blocked? attach it, then copy into $CACHE/models/)"
done

# 5. Node: playwright-core + base fonts (more fonts are fetched per style by fonts.py)
cd "$CACHE/node"
[ -f package.json ] || echo '{"name":"video-kit-cache","private":true}' > package.json
need=""
[ -d node_modules/playwright-core ] || need="$need playwright-core@1.56.0"
for f in inter anton; do [ -d "node_modules/@fontsource/$f" ] || need="$need @fontsource/$f"; done
[ -n "$need" ] && npm i -s --no-audit --no-fund $need >/dev/null 2>&1
[ -d node_modules/playwright-core ] && ok "playwright-core" || bad "playwright-core (npm i playwright-core)"

# 6. Chromium (never 'playwright install': reuse the preinstalled one)
CH=$(ls -d /opt/pw-browsers/chromium-*/chrome-linux/chrome 2>/dev/null | tail -1)
[ -z "$CH" ] && CH=$(command -v chromium || command -v chromium-browser || command -v google-chrome || true)
[ -n "$CH" ] && { ok "chromium $CH"; echo "$CH" > "$CACHE/chromium.txt"; } || bad "no Chromium found (set VIDEO_KIT_CHROME=/path/to/chrome)"

echo "CPUs: $(nproc)"
[ $FAIL = 0 ] && echo "SETUP OK" || { echo "SETUP INCOMPLETE (see [!!] lines)"; exit 1; }
