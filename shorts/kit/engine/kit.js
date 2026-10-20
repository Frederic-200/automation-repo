/* video-kit engine core. Every frame is a pure function of time: no Math.random, no Date,
   no state carried between frames. Globals: W, H, S (style), TL (timeline), x (current ctx). */
'use strict';
const W = 1080, H = 1920, CX = 540, HY = 720, FPS = 30;
let S = null, TL = null, x = null;

/* ------------------------------------------------------------------ math */
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const inv = (a, b, v) => clamp((v - a) / (b - a));
const smooth = t => { t = clamp(t); return t * t * (3 - 2 * t); };
const easeOutExpo = t => (t = clamp(t)) >= 1 ? 1 : 1 - Math.pow(2, -10 * t);
const easeInExpo = t => (t = clamp(t)) <= 0 ? 0 : Math.pow(2, 10 * t - 10);
const easeOutQuart = t => 1 - Math.pow(1 - clamp(t), 4);
const easeInQuad = t => clamp(t) ** 2;
const easeInOutCubic = t => (t = clamp(t)) < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
const easeOutBack = (t, k = 1.7) => { t = clamp(t) - 1; return 1 + (k + 1) * t * t * t + k * t * t; };
const TAU = Math.PI * 2;

/* Closed-form damped spring (popmotion maths). zeta .3 bouncy .5 lively .7 snappy 1 none. */
function spring(t, { from = 0, to = 1, v = 0, zeta = null, w0 = null } = {}) {
  zeta = zeta ?? S.motion.zeta; w0 = w0 ?? S.motion.w0;
  if (t <= 0) return from;
  const d = to - from;
  if (zeta < 1) { const wd = w0 * Math.sqrt(1 - zeta * zeta);
    return to - Math.exp(-zeta * w0 * t) * (((zeta * w0 * d - v) / wd) * Math.sin(wd * t) + d * Math.cos(wd * t)); }
  return to - Math.exp(-w0 * t) * (d + (w0 * d - v) * t);
}
const springStep = d => d <= 0 ? 0 : 1 - Math.exp(-8 * d) * Math.cos(14 * d);
const kick = (d, k = 6, w = 14) => d <= 0 ? 0 : Math.exp(-k * d) * Math.sin(w * d);
const decay = (d, k = 6) => d < 0 ? 0 : Math.exp(-k * d);

/* Deterministic hash -> [0,1). hash(seed, 'id', i, ...) */
function hash(...a) {
  let h = 2166136261 >>> 0;
  const s = a.join('|');
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
  h ^= h >>> 13; h = Math.imul(h, 0x5bd1e995); h ^= h >>> 15;
  return (h >>> 0) / 4294967296;
}
const R = (...a) => hash(TL.seed, ...a);
const Rs = (...a) => R(...a) * 2 - 1;

/* Smooth value noise 1D/2D (deterministic) */
function vnoise(xv, seed = 0) { const i = Math.floor(xv), f = xv - i, u = f * f * (3 - 2 * f);
  return lerp(hash(seed, i), hash(seed, i + 1), u) * 2 - 1; }
function vnoise2(xv, yv, seed = 0) { const i = Math.floor(xv), j = Math.floor(yv), fx = xv - i, fy = yv - j;
  const u = fx * fx * (3 - 2 * fx), v = fy * fy * (3 - 2 * fy);
  const a = hash(seed, i, j), b = hash(seed, i + 1, j), c = hash(seed, i, j + 1), d = hash(seed, i + 1, j + 1);
  return lerp(lerp(a, b, u), lerp(c, d, u), v) * 2 - 1; }
const fbm = (xv, yv, seed = 0, o = 4) => { let s = 0, a = .5, f = 1; for (let k = 0; k < o; k++) { s += a * vnoise2(xv * f, yv * f, seed + k * 17); f *= 2; a *= .5; } return s; };

/* ------------------------------------------------------------------ color */
function rgb(hex) { hex = hex.replace('#', ''); if (hex.length === 3) hex = [...hex].map(c => c + c).join('');
  return [parseInt(hex.slice(0, 2), 16), parseInt(hex.slice(2, 4), 16), parseInt(hex.slice(4, 6), 16)]; }
const rgba = (hex, a = 1) => { const [r, g, b] = rgb(hex); return `rgba(${r},${g},${b},${a})`; };
function mixc(a, b, t) { const A = rgb(a), B = rgb(b); t = clamp(t);
  return '#' + A.map((v, i) => Math.round(v + (B[i] - v) * t).toString(16).padStart(2, '0')).join(''); }
const lum = hex => { const [r, g, b] = rgb(hex); return (.2126 * r + .7152 * g + .0722 * b) / 255; };
/* IQ cosine palette */
const cosPal = (t, a, b, c, d) => '#' + [0, 1, 2].map(i => Math.round(clamp(a[i] + b[i] * Math.cos(TAU * (c[i] * t + d[i]))) * 255).toString(16).padStart(2, '0')).join('');

/* scene-aware colors: env(sc) gives the colors a scene should use */
function env(sc) {
  const bright = sc.bright, P = S.palette;
  return { bright, bg: bright ? S.bg2 : S.bg, ink: bright ? S.ink2 : S.ink, accent: S.accent, P,
    soft: bright ? mixc(S.bg2[0], S.ink2, .18) : mixc(S.bg[0], S.ink, .22),
    dim: bright ? mixc(S.bg2[0], S.ink2, .08) : mixc(S.bg[0], S.ink, .08) };
}

/* ------------------------------------------------------------------ layers */
function layer(w = W, h = H) { const c = document.createElement('canvas'); c.width = w; c.height = h;
  c.style.display = 'none'; document.body.appendChild(c); return c; }
let OUT, octx, LA, LB, FR, TMP, GA, GB, SM, ga, gb, smx, GRAIN, VIG, SCAN, PAPER;

function initLayers() {
  OUT = document.getElementById('c'); octx = OUT.getContext('2d');
  LA = layer(); LB = layer(); FR = layer(); TMP = layer();
  GA = layer(540, 960); GB = layer(540, 960); ga = GA.getContext('2d'); gb = GB.getContext('2d');
  SM = layer(270, 480); smx = SM.getContext('2d');
  // grain tile 320x320 seeded
  GRAIN = layer(320, 320); { const g = GRAIN.getContext('2d'), im = g.createImageData(320, 320);
    for (let i = 0; i < 320 * 320; i++) { const v = Math.floor(hash(TL.seed, 'grain', i) * 255); im.data[i * 4] = im.data[i * 4 + 1] = im.data[i * 4 + 2] = v; im.data[i * 4 + 3] = 255; }
    g.putImageData(im, 0, 0); }
  VIG = layer(); { const v = VIG.getContext('2d'), gr = v.createRadialGradient(CX, H * .45, H * .25, CX, H * .45, H * .78);
    gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(1, 'rgba(0,0,0,1)'); v.fillStyle = gr; v.fillRect(0, 0, W, H); }
  SCAN = layer(4, 4); { const s = SCAN.getContext('2d'); s.fillStyle = 'rgba(0,0,0,1)'; s.fillRect(0, 0, 4, 2); }
  PAPER = layer(512, 512); { const p = PAPER.getContext('2d'), im = p.createImageData(512, 512);
    for (let j = 0; j < 512; j++) for (let i = 0; i < 512; i++) { const n = .5 + .5 * fbm(i / 18, j / 90, 5, 3) * .6 + (hash(9, i, j) - .5) * .25;
      const v = Math.floor(clamp(.82 + n * .18) * 255), k = (j * 512 + i) * 4; im.data[k] = v; im.data[k + 1] = v; im.data[k + 2] = v - 6; im.data[k + 3] = 255; }
    p.putImageData(im, 0, 0); }
}

/* ------------------------------------------------------------------ drawing helpers (use global x) */
let CURSC = null, CURT = 0;
function bgFill(e, t = 0, shift = 0) { if (CURSC && CURSC.bg && CURSC.type !== 'story' && typeof BG !== 'undefined' && BG.under(CURSC, e, CURT, CURT - CURSC.start)) return; const g = x.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, e.bg[0]); g.addColorStop(1, e.bg[1]); x.fillStyle = g; x.fillRect(-60, -60, W + 120, H + 120); }
function circle(cx, cy, r, fill, a = 1) { if (r <= 0) return; x.globalAlpha = a; x.fillStyle = fill; x.beginPath(); x.arc(cx, cy, r, 0, TAU); x.fill(); x.globalAlpha = 1; }
function ring(cx, cy, r, w, col, a = 1) { if (r <= 0) return; x.globalAlpha = a; x.strokeStyle = col; x.lineWidth = w; x.beginPath(); x.arc(cx, cy, r, 0, TAU); x.stroke(); x.globalAlpha = 1; }
function glowDot(cx, cy, r, col, a = 1) { const g = x.createRadialGradient(cx, cy, 0, cx, cy, r);
  g.addColorStop(0, rgba(col, a)); g.addColorStop(1, rgba(col, 0)); x.fillStyle = g; x.fillRect(cx - r, cy - r, r * 2, r * 2); }
function poly(pts, fill, stroke, lw = 4) { x.beginPath(); pts.forEach((p, i) => i ? x.lineTo(p[0], p[1]) : x.moveTo(p[0], p[1])); x.closePath();
  if (fill) { x.fillStyle = fill; x.fill(); } if (stroke) { x.strokeStyle = stroke; x.lineWidth = lw; x.stroke(); } }
/* Morphable shapes: 96 perimeter points, start bottom-left, clockwise. kind: circle|square|triangle|diamond */
function shapePts(kind, cx, cy, r, rot = 0, n = 96) {
  const pts = [];
  for (let i = 0; i < n; i++) { const u = i / n; let px, py;
    if (kind === 'circle') { const a = Math.PI * .75 + u * TAU; px = Math.cos(a); py = Math.sin(a); }
    else { const V = kind === 'square' ? [[-1, 1], [-1, -1], [1, -1], [1, 1]] : kind === 'diamond' ? [[0, 1.2], [-1.2, 0], [0, -1.2], [1.2, 0]] : [[-1.1, .8], [0, -1.15], [1.1, .8]];
      const m = V.length, s = u * m, k = Math.floor(s), f = s - k, A = V[k % m], B = V[(k + 1) % m];
      px = lerp(A[0], B[0], f); py = lerp(A[1], B[1], f); }
    const c = Math.cos(rot), sn = Math.sin(rot); pts.push([cx + r * (px * c - py * sn), cy + r * (px * sn + py * c)]); }
  return pts;
}
const morph = (A, B, t) => A.map((p, i) => [lerp(p[0], B[i][0], t), lerp(p[1], B[i][1], t)]);

/* keys of a scene relative to global time t */
function keyInfo(sc, t) {
  let pulse = 0, step = 0, count = 0, last = -9, lastStr = 0;
  for (const k of sc.keys) { const d = t - k.s; if (d >= 0) { count++; last = d; lastStr = k.str; }
    pulse += k.str * decay(d, 5); step += springStep(d); }
  return { pulse: clamp(pulse, 0, 2.5), step, count, since: last, str: lastStr, n: sc.keys.length };
}

/* Gooey metaballs: draw(g) paints white shapes in FULL-res coords; returns GB (half-res) */
function goo(draw, fill) {
  ga.setTransform(1, 0, 0, 1, 0, 0); ga.clearRect(0, 0, 540, 960); ga.setTransform(.5, 0, 0, .5, 0, 0); ga.fillStyle = '#fff'; draw(ga);
  gb.setTransform(1, 0, 0, 1, 0, 0); gb.globalCompositeOperation = 'source-over'; gb.clearRect(0, 0, 540, 960);
  gb.filter = 'url(#goo)'; gb.drawImage(GA, 0, 0); gb.filter = 'none';
  gb.globalCompositeOperation = 'source-in'; gb.setTransform(.5, 0, 0, .5, 0, 0);
  gb.fillStyle = typeof fill === 'function' ? fill(gb) : fill; gb.fillRect(0, 0, W, H);
  gb.setTransform(1, 0, 0, 1, 0, 0); gb.globalCompositeOperation = 'source-over'; return GB;
}
function drawGoo(draw, fill, glow = 0) { const g = goo(draw, fill);
  if (glow) { x.save(); x.globalAlpha = glow; x.filter = 'blur(26px)'; x.drawImage(g, 0, 0, W, H); x.restore(); x.filter = 'none'; }
  x.drawImage(g, 0, 0, W, H); }
const gcirc = (g, cx, cy, r) => { if (r > 0) { g.beginPath(); g.arc(cx, cy, r, 0, TAU); g.fill(); } };
const gell = (g, cx, cy, rx, ry, rot = 0) => { if (rx > 0 && ry > 0) { g.beginPath(); g.ellipse(cx, cy, rx, ry, rot, 0, TAU); g.fill(); } };

/* ------------------------------------------------------------------ hits -> camera / post amounts */
let _HX = null;   // hits + synthetic micro-hits: never more than ~1.7 s without a visual event
function allHits() {
  if (_HX) return _HX; const base = TL.hits.slice().sort((a, b) => a.t - b.t), ex = []; let prev = 0;
  for (const h of base.concat([{ t: TL.duration }])) { for (let q = prev + 1.7; q < h.t - .6; q += 1.7) ex.push({ t: q, s: .22, micro: 1 }); prev = h.t; }
  return (_HX = base.concat(ex));
}
function fx(t) {
  let amp = 0, zoom = 0, flashW = 0, flashO = 0, rgbv = 0, glitch = 0, impact = 0;
  const sh = S.camera.shake, zh = S.camera.zoom_hit ?? 1;
  for (const h of allHits()) { const d = t - h.t; if (d < 0 || d > 2.5) continue;
    amp += h.s * 46 * Math.exp(-d * 6) * sh; zoom += h.s * .085 * Math.exp(-d * 7) * Math.cos(d * 13) * zh;
    if (h.micro) continue;
    if (h.s >= 1) flashW += (h.s - .6) * .75 * Math.exp(-d * 13); else flashO += h.s * .35 * Math.exp(-d * 12);
    if (h.s >= .8) rgbv += h.s * 24 * Math.exp(-d * 8);
    if ((h.s >= 1 && d < .22) || (h.tr && d < .12)) glitch = Math.max(glitch, h.s);
    if (h.impact && d < 1 / FPS) impact = 1; }
  return { amp, zoom, flashW: Math.min(flashW, .95) * (S.post.flash ?? 1), flashO: Math.min(flashO, .6), rgb: rgbv * S.post.rgb, glitch: glitch * S.post.glitch, impact };
}

/* ------------------------------------------------------------------ scene dispatch */
const SCENES = {};   // filled by scenes.js: SCENES[type] = (t, lt, sc, e) => draws with global x
function sceneAt(t) { const sc = TL.scenes; for (let i = sc.length - 1; i >= 0; i--) if (t >= sc[i].start) return i; return 0; }
function drawScene(i, t, ctx) {
  x = ctx; const sc = TL.scenes[i];
  const tq = S.motion.on_twos ? Math.floor(t * 12) / 12 : t;
  x.setTransform(1, 0, 0, 1, 0, 0); x.globalAlpha = 1; x.globalCompositeOperation = 'source-over'; x.filter = 'none';
  const fn = SCENES[sc.type] || SCENES.shapes; CURSC = sc; CURT = tq;
  x.save(); fn(tq, tq - sc.start, sc, env(sc)); x.restore();
}

/* ------------------------------------------------------------------ transitions */
const TR_IN = .30, TR_OUT = .34;
function transition(kind, p, A, B, out, t, sc) {   // A = outgoing canvas, B = incoming canvas
  const o = out; o.setTransform(1, 0, 0, 1, 0, 0); o.globalAlpha = 1; o.globalCompositeOperation = 'source-over';
  const acc = S.accent;
  if (kind === 'liquid') {
    o.drawImage(A, 0, 0); const wf = clamp(p);
    const r = easeInQuad(wf) * 1750 + easeOutQuart(wf) * 120, cx = CX, cy = HY + 160;
    const blobs = g => { gcirc(g, cx, cy, r); for (let k = 0; k < 12; k++) { const a = k / 12 * TAU + hash(sc.i, k) * .5, rr = r + 40 + 120 * hash(sc.i, k, 1) * Math.sin(Math.PI * wf);
      gcirc(g, cx + Math.cos(a) * rr, cy + Math.sin(a) * rr, (24 + 44 * hash(sc.i, k, 2)) * Math.sin(Math.PI * clamp(wf * 1.3))); } };
    const rim = g => { gcirc(g, cx, cy, r + 46); };
    x = o; x.drawImage(goo(g => { blobs(g); rim(g); }, acc), 0, 0, W, H);
    const m = goo(blobs, '#fff'); TMP.getContext('2d').setTransform(1, 0, 0, 1, 0, 0);
    const tx = TMP.getContext('2d'); tx.globalCompositeOperation = 'source-over'; tx.clearRect(0, 0, W, H); tx.drawImage(B, 0, 0);
    tx.globalCompositeOperation = 'destination-in'; tx.drawImage(m, 0, 0, W, H); tx.globalCompositeOperation = 'source-over';
    o.drawImage(TMP, 0, 0);
  } else if (kind === 'iris') {
    o.drawImage(A, 0, 0); const r = easeInOutCubic(p) * 1250;
    o.save(); o.beginPath(); o.arc(CX, HY, r, 0, TAU); o.clip(); o.drawImage(B, 0, 0); o.restore();
    o.strokeStyle = acc; o.lineWidth = 34 * Math.sin(Math.PI * p); o.beginPath(); o.arc(CX, HY, r, 0, TAU); o.stroke();
  } else if (kind === 'whip') {
    const e = easeInOutCubic(p), off = e * W * 1.15;
    for (let k = 3; k >= 0; k--) { o.globalAlpha = k ? .18 : 1; o.drawImage(A, -off - k * 40 * Math.sin(Math.PI * p), 0); o.drawImage(B, W * 1.15 - off + k * 40 * Math.sin(Math.PI * p), 0); }
    o.globalAlpha = 1;
  } else if (kind === 'glitch') {
    o.drawImage(p < .5 ? A : B, 0, 0); const n = 14, f = Math.floor(t * FPS);
    for (let k = 0; k < n; k++) { const y0 = Math.floor(hash(f, k) * H), h = 20 + hash(f, k, 1) * 180, src = hash(f, k, 2) < p ? B : A;
      const dx = (hash(f, k, 3) - .5) * 220 * Math.sin(Math.PI * p); o.drawImage(src, 0, y0, W, h, dx, y0, W, h); }
    o.globalCompositeOperation = 'lighter'; o.globalAlpha = .25 * Math.sin(Math.PI * p); o.fillStyle = acc; o.fillRect(0, Math.floor(hash(f, 'bar') * H), W, 30); o.globalAlpha = 1; o.globalCompositeOperation = 'source-over';
  } else if (kind === 'pixel') {
    const src = p < .5 ? A : B, k = Math.sin(Math.PI * p), cell = Math.max(1, Math.round(2 + k * 60));
    const w = Math.max(2, Math.round(W / cell)), h = Math.max(2, Math.round(H / cell));
    const tx = TMP.getContext('2d'); tx.setTransform(1, 0, 0, 1, 0, 0); tx.imageSmoothingEnabled = true; tx.clearRect(0, 0, W, H); tx.drawImage(src, 0, 0, w, h);
    o.imageSmoothingEnabled = false; o.drawImage(TMP, 0, 0, w, h, 0, 0, W, H); o.imageSmoothingEnabled = true;
  } else if (kind === 'card') {   // outgoing frame shrinks into a tilted floating card, then drops away to reveal the next scene
    const bz = 1.08 - .08 * easeOutQuart(p); o.save(); o.translate(CX, H / 2); o.scale(bz, bz); o.translate(-CX, -H / 2); o.drawImage(B, 0, 0); o.restore();
    const s1 = easeInOutCubic(clamp(p / .62)), q = p > .62 ? easeInQuad((p - .62) / .38) : 0, cs = lerp(1, .58, s1) * lerp(1, .8, q), rot = -.07 * s1 - .12 * q, ty = -280 * q;
    o.save(); o.globalAlpha = 1 - q; o.translate(CX, H / 2 + ty); o.rotate(rot); o.scale(cs, cs);
    o.shadowColor = 'rgba(0,0,0,.45)'; o.shadowBlur = 70; o.shadowOffsetY = 34; o.fillStyle = '#000'; o.beginPath(); o.roundRect(-CX, -H / 2, W, H, 60); o.fill();
    o.shadowColor = 'transparent'; o.clip(); o.drawImage(A, -CX, -H / 2); o.restore();
  } else { // flash (default)
    o.drawImage(p < .5 ? A : B, 0, 0); o.globalAlpha = Math.pow(Math.sin(Math.PI * p), 2) * .9; o.fillStyle = mixc('#ffffff', acc, .25); o.fillRect(0, 0, W, H); o.globalAlpha = 1;
  }
}

/* ------------------------------------------------------------------ post FX on octx */
function post(t, F, sc) {
  const P = S.post, f = Math.floor(t * FPS), o = octx;
  // RGB split
  if (F.rgb > 1.5) { const tx = TMP.getContext('2d'); tx.setTransform(1, 0, 0, 1, 0, 0);
    tx.globalCompositeOperation = 'source-over'; tx.drawImage(OUT, 0, 0);
    o.fillStyle = '#000'; o.fillRect(0, 0, W, H); o.globalCompositeOperation = 'lighter';
    [['#f00', F.rgb, 0], ['#0f0', 0, 0], ['#00f', -F.rgb, F.rgb * .3]].forEach(([c, dx, dy]) => {
      const lx = FR.getContext('2d'); lx.setTransform(1, 0, 0, 1, 0, 0); lx.globalCompositeOperation = 'source-over'; lx.drawImage(TMP, 0, 0);
      lx.globalCompositeOperation = 'multiply'; lx.fillStyle = c; lx.fillRect(0, 0, W, H); lx.globalCompositeOperation = 'source-over';
      o.drawImage(FR, dx - W * .012, dy - H * .012, W * 1.024, H * 1.024); });
    o.globalCompositeOperation = 'source-over'; }
  // glitch slices
  if (F.glitch > .05) { for (let k = 0; k < 9; k++) { const y0 = Math.floor(hash(f, 'g', k) * H), h = 12 + hash(f, 'gh', k) * 120;
      const dx = (hash(f, 'gx', k) - .5) * 90 * F.glitch; o.drawImage(OUT, 0, y0, W, h, dx, y0, W, h); }
    if (hash(f, 'gd') < .4 * F.glitch) { o.globalCompositeOperation = 'difference'; o.fillStyle = '#fff'; o.fillRect(0, hash(f, 'gy') * H, W, 14 + 40 * hash(f, 'gz')); o.globalCompositeOperation = 'source-over'; } }
  // bloom (quarter-res blurred copy, added)
  if (P.bloom > 0) { smx.setTransform(1, 0, 0, 1, 0, 0); smx.filter = 'blur(7px)'; smx.clearRect(0, 0, 270, 480); smx.drawImage(OUT, 0, 0, 270, 480); smx.filter = 'none';
    o.globalCompositeOperation = 'lighter'; o.globalAlpha = .28 * P.bloom; o.drawImage(SM, 0, 0, W, H); o.globalAlpha = 1; o.globalCompositeOperation = 'source-over'; }
  // halftone (risograph dots)
  if (P.halftone > 0) halftone(P.halftone);
  // pixel / palette quantize (1-bit, Game Boy)
  if (P.pixel > 0) pixelQuant();
  // flashes
  if (F.flashW > .01) { o.globalAlpha = F.flashW; o.fillStyle = '#fff'; o.fillRect(0, 0, W, H); o.globalAlpha = 1; }
  if (F.flashO > .01) { o.globalCompositeOperation = 'lighter'; o.globalAlpha = F.flashO; o.fillStyle = S.accent; o.fillRect(0, 0, W, H); o.globalAlpha = 1; o.globalCompositeOperation = 'source-over'; }
  if (F.impact) { // one-frame silhouette impact frame
    const tx = TMP.getContext('2d'); tx.setTransform(1, 0, 0, 1, 0, 0); tx.globalCompositeOperation = 'source-over'; tx.filter = 'grayscale(1) contrast(9) invert(1)'; tx.drawImage(OUT, 0, 0); tx.filter = 'none';
    o.drawImage(TMP, 0, 0); }
  // paper fibres
  if (P.paper > 0) { o.globalCompositeOperation = 'multiply'; o.globalAlpha = .55 * P.paper; o.fillStyle = o.createPattern(PAPER, 'repeat'); o.fillRect(0, 0, W, H); o.globalAlpha = 1; o.globalCompositeOperation = 'source-over'; }
  // scanlines
  if (P.scanlines > 0) { o.globalAlpha = P.scanlines; o.fillStyle = o.createPattern(SCAN, 'repeat'); o.fillRect(0, 0, W, H); o.globalAlpha = 1; }
  // vignette
  if (P.vignette > 0) { o.globalAlpha = P.vignette; o.drawImage(VIG, 0, 0); o.globalAlpha = 1; }
  // grain (also kills H.264 banding)
  if (P.grain > 0) { o.save(); o.globalCompositeOperation = 'overlay'; o.globalAlpha = P.grain; o.translate(-hash(f, 'gx') * 320, -hash(f, 'gy') * 320);
    o.fillStyle = o.createPattern(GRAIN, 'repeat'); o.fillRect(0, 0, W + 320, H + 320); o.restore(); }
}
function halftone(k) {
  const cell = 14, cw = Math.ceil(W / cell), ch = Math.ceil(H / cell);
  const sm = TMP.getContext('2d', { willReadFrequently: true }); sm.setTransform(1, 0, 0, 1, 0, 0); sm.clearRect(0, 0, cw, ch);
  sm.drawImage(OUT, 0, 0, cw, ch); const d = sm.getImageData(0, 0, cw, ch).data;
  const o = octx, paper = lum(S.bg[0]) > .5 ? S.bg[0] : '#f3ecd8';
  o.globalAlpha = k; o.fillStyle = paper; o.fillRect(0, 0, W, H); o.globalAlpha = 1;
  for (let j = 0; j < ch; j++) for (let i = 0; i < cw; i++) { const q = (j * cw + i) * 4, r = d[q], g = d[q + 1], b = d[q + 2];
    const L = (.2126 * r + .7152 * g + .0722 * b) / 255, pr = lum(paper);
    if (Math.abs(L - pr) < .04 && Math.abs(r - rgb(paper)[0]) < 12) continue;
    const rad = cell * .72 * Math.sqrt(clamp(1 - L * .8 + .12)); const ox = (j % 2) * cell / 2;
    o.fillStyle = `rgb(${r},${g},${b})`; o.beginPath(); o.arc(i * cell + ox + cell / 2 + 1.5, j * cell + cell / 2 + 1, rad, 0, TAU); o.fill(); }
}
const BAYER = [0, 32, 8, 40, 2, 34, 10, 42, 48, 16, 56, 24, 50, 18, 58, 26, 12, 44, 4, 36, 14, 46, 6, 38, 60, 28, 52, 20, 62, 30, 54, 22, 3, 35, 11, 43, 1, 33, 9, 41, 51, 19, 59, 27, 49, 17, 57, 25, 15, 47, 7, 39, 13, 45, 5, 37, 63, 31, 55, 23, 61, 29, 53, 21];
function pixelQuant() {
  const w = 270, h = 480, s = smx; s.setTransform(1, 0, 0, 1, 0, 0); s.filter = 'none'; s.imageSmoothingEnabled = true; s.drawImage(OUT, 0, 0, w, h);
  const im = s.getImageData(0, 0, w, h), d = im.data, pal = S.palette.map(rgb).sort((a, b) => (a[0] + a[1] + a[2]) - (b[0] + b[1] + b[2]));
  const n = pal.length;
  for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) { const q = (j * w + i) * 4, L = (.2126 * d[q] + .7152 * d[q + 1] + .0722 * d[q + 2]) / 255;
    const th = (BAYER[(j % 8) * 8 + (i % 8)] + .5) / 64 - .5; const k = clamp(Math.round(L * (n - 1) + th * .9), 0, n - 1);
    d[q] = pal[k][0]; d[q + 1] = pal[k][1]; d[q + 2] = pal[k][2]; }
  s.putImageData(im, 0, 0); octx.imageSmoothingEnabled = false; octx.drawImage(SM, 0, 0, W, H); octx.imageSmoothingEnabled = true;
}

/* ------------------------------------------------------------------ captions */
let CHUNKS = [];
function buildChunks() {
  CHUNKS = [];
  TL.scenes.forEach(sc => sc.lines.forEach(ln => {
    let cur = null; const ws = ln.words;
    const mode = S.caption.mode;
    if (mode === 'stack' || mode === 'typeon') { // phrase-sized blocks: break at punctuation (>=3 words) or after 7 words; merge a tiny tail into the previous block
      let g = [], first = CHUNKS.length;
      const flush = () => { if (!g.length) return; if (g.length < 3 && CHUNKS.length > first) { const pv = CHUNKS[CHUNKS.length - 1]; pv.words = pv.words.concat(g); pv.lineEnd = g[g.length - 1].e; }
        else CHUNKS.push({ words: g, key: 0, s: g[0].s, lineEnd: g[g.length - 1].e, scene: sc.i, line: 1 }); g = []; };
      ws.forEach(w => { g.push(w); if ((/[.,!?;:]$/.test(w.w) && g.length >= 3) || g.length >= 7) flush(); }); flush(); return; }
    if (mode === 'clean' || mode === 'type') { CHUNKS.push({ words: ws, key: 0, s: ws[0].s, lineEnd: ln.e, scene: sc.i, line: 1 }); return; }
    ws.forEach((w, i) => {
      const brk = !cur || cur.key !== w.k || (!w.k && cur.words.length >= 3) || (!w.k && /[.,!?;:]$/.test(cur.words[cur.words.length - 1].w) && cur.key === 0);
      if (brk) { cur = { words: [], key: w.k, s: w.s, lineEnd: ln.e, scene: sc.i }; CHUNKS.push(cur); }
      cur.words.push(w);
    });
  }));
  CHUNKS.forEach((c, i) => { const nx = CHUNKS[i + 1]; c.end = Math.min(nx ? nx.s - .02 : 1e9, c.lineEnd + (c.key ? .55 : .35)); c.s -= .04; });
}
function fitFont(text, fam, wt, maxW, start, min = 40) { let sz = start; x.font = `${wt} ${sz}px "${fam}"`;
  while (x.measureText(text).width > maxW && sz > min) { sz -= 4; x.font = `${wt} ${sz}px "${fam}"`; } return sz; }
const caseT = s => S.upper ? s.toUpperCase() : s;

/* ------------------------------------------------------------------ frame layouts, header/ticker, progress bar, source chip */
const LAYOUTS = {
  card: { x: 70, y: 190, w: 940, h: 1000, r: 56, k: .9, shadow: 1 },
  top_stage: { x: 0, y: 0, w: 1080, h: 1160, r: 0, k: 1 },
  tilt_card: { x: 120, y: 240, w: 880, h: 980, r: 48, k: .88, rot: -.05, shadow: 1 },
  letterbox: { x: 0, y: 150, w: 1080, h: 1180, r: 0, k: 1 },
};
function rrPath(o, x0, y0, w, h, r) { o.beginPath(); o.moveTo(x0 + r, y0); o.arcTo(x0 + w, y0, x0 + w, y0 + h, r); o.arcTo(x0 + w, y0 + h, x0, y0 + h, r); o.arcTo(x0, y0 + h, x0, y0, r); o.arcTo(x0, y0, x0 + w, y0, r); o.closePath(); }
function drawStage(o, z, rot, F, sc) {
  const name = (S.layout && S.layout.name) || 'full', R = LAYOUTS[name], e = env(sc);
  const full = (a) => { o.save(); o.globalAlpha = a; o.translate(CX, HY); o.scale(z, z); o.rotate(rot); o.translate(-CX + F.sx, -HY + F.sy); o.drawImage(FR, 0, 0); o.restore(); };
  if (name === 'text_first') { full(.42); return; }
  if (!R) { full(1); return; }
  o.fillStyle = mixc(e.bg[0], e.ink, .07); o.fillRect(0, 0, W, H);
  o.save();
  if (R.rot) { o.translate(R.x + R.w / 2, R.y + R.h / 2); o.rotate(R.rot); o.translate(-(R.x + R.w / 2), -(R.y + R.h / 2)); }
  if (R.shadow) { o.save(); o.shadowColor = 'rgba(0,0,0,.38)'; o.shadowBlur = 46; o.shadowOffsetY = 20; o.fillStyle = e.bg[0]; rrPath(o, R.x, R.y, R.w, R.h, R.r); o.fill(); o.restore(); }
  rrPath(o, R.x, R.y, R.w, R.h, R.r); o.clip();
  o.translate(R.x + R.w / 2, R.y + R.h / 2); o.scale(z * R.k, z * R.k); o.rotate(rot); o.translate(-CX + F.sx, -HY + F.sy); o.drawImage(FR, 0, 0);
  o.restore();
}
function decor(t, F, sc) {
  const o = octx, e = env(sc), name = (S.layout && S.layout.name) || 'full', X = S.extras || {};
  o.save(); o.setTransform(1, 0, 0, 1, 0, 0);
  if (name === 'letterbox') {
    o.fillStyle = S.accent; o.fillRect(0, 0, W, 150);
    o.fillStyle = S.on_accent; o.font = `${S.fonts.display_weight} 72px "${S.fonts.display}"`; o.textBaseline = 'middle'; o.textAlign = 'left'; o.fillText('FREDSDESK', 56, 78);
    o.font = `${S.fonts.text_weight} 38px "${S.fonts.text}"`; o.textAlign = 'right'; o.fillText(TL.tag || 'DAILY AI', W - 56, 78);
    const tx = (TL.ticker || 'FREDSDESK  /  DAILY AI  /  '); o.font = `${S.fonts.display_weight} 40px "${S.fonts.display}"`; const tw = o.measureText(tx).width;
    o.fillStyle = e.ink; o.fillRect(0, 1330, W, 56); o.fillStyle = e.bg[0]; o.textAlign = 'left'; const off = (t * 120) % tw;
    for (let q = -off; q < W; q += tw) o.fillText(tx, q, 1359);
  }
  if (X.progress) { o.fillStyle = 'rgba(0,0,0,.25)'; o.fillRect(0, 0, W, 16); o.fillStyle = S.accent; o.fillRect(0, 0, W * clamp(t / TL.duration), 16); }
  if (TL.chip) { const c = TL.chip, a = clamp((t - c.at) / .18) * clamp((c.at + c.hold - t) / .18); if (a > 0) {
      o.globalAlpha = a; o.font = `${S.fonts.text_weight} 38px "${S.fonts.text}"`; o.textBaseline = 'middle'; o.textAlign = 'left'; const txt = String(c.text).toUpperCase(), tw = o.measureText(txt).width + 56, cy = name === 'letterbox' ? 200 : 120;
      o.fillStyle = e.ink; rrPath(o, 54, cy - 36 + (1 - a) * -14, tw, 72, 36); o.fill(); o.fillStyle = e.bg[0]; o.fillText(txt, 82, cy + (1 - a) * -14 + 2); o.globalAlpha = 1; } }
  o.restore();
}

/* ------------------------------------------------------------------ hook overlay (frame 0) + loop echo */
function hookOverlay(t, F) {
  const H = TL.hook, HY0 = H.y ?? ((S.hook && S.hook.y) || 560), hold = H.hold ?? 2.4, dur = TL.duration, echoT = Math.max(0, dur - (H.echo ?? .55));
  let a = 0, k = 1;
  if (t < hold) { a = 1; k = 1 + .14 * Math.exp(-t * 22) * Math.cos(t * 30); if (t > hold - .22) a = clamp((hold - t) / .22); }   // visible and popping from frame 0, no fade-in
  else if (H.loop !== false && t >= echoT) { a = easeOutQuart(clamp((t - echoT) / .4)); k = 1; }                                   // the end shows the hook again: seamless replay
  if (a <= 0) return;
  const words = String(H.text).toUpperCase().split(/\s+/).filter(Boolean), fam = S.fonts.display, wt = S.fonts.display_weight, W0 = H.w ?? 920, size0 = H.size ?? 150;
  const sc = TL.scenes[sceneAt(t)], e = env(sc);
  let size = size0, lines;
  for (let tries = 0; tries < 8; tries++) { x = octx; x.font = `${wt} ${size}px "${fam}"`; lines = []; let cur = [];
    for (const w of words) { const t2 = cur.concat([w]).map(z => z.replace(/\*/g, '')).join(' '); if (x.measureText(t2).width > W0 && cur.length) { lines.push(cur); cur = [w]; } else cur.push(w); }
    if (cur.length) lines.push(cur); if (lines.length <= 3) break; size *= .9; }
  const lh = size * .98, y0 = (HY0) - (lines.length * lh) / 2 + lh * .8;
  x = octx; x.save(); x.setTransform(1, 0, 0, 1, 0, 0); x.translate(F.sx * .5, F.sy * .5); x.globalAlpha = a; x.textBaseline = 'alphabetic'; x.textAlign = 'center';
  x.translate(CX, HY0); x.scale(k, k); x.translate(-CX, -(HY0)); x.font = `${wt} ${size}px "${fam}"`; x.lineJoin = 'round'; x.lineWidth = size * .09;
  const dark = lum(e.bg[0]) < .5, hs = (S.hook && S.hook.style) || 'pop';
  const blockW = Math.max(...lines.map(ln => x.measureText(ln.map(z => z.replace(/\*/g, '')).join(' ')).width)), blockH = lines.length * lh;
  if (hs === 'sticker') { x.save(); x.translate(CX, (HY0)); x.rotate(-.045); x.fillStyle = 'rgba(0,0,0,.35)'; rrPath(x, -blockW / 2 - 40 + 10, -blockH / 2 - 26 + 14, blockW + 80, blockH + 60, 30); x.fill();
    x.fillStyle = S.accent; rrPath(x, -blockW / 2 - 40, -blockH / 2 - 26, blockW + 80, blockH + 60, 30); x.fill(); x.restore(); x.translate(CX, HY0); x.rotate(-.045); x.translate(-CX, -(HY0)); }
  if (hs === 'terminal') { x.save(); x.fillStyle = 'rgba(4,10,8,.88)'; rrPath(x, CX - blockW / 2 - 50, (HY0) - blockH / 2 - 60, blockW + 100, blockH + 120, 22); x.fill();
    x.fillStyle = S.accent; x.fillRect(CX - blockW / 2 - 50, (HY0) - blockH / 2 - 60, blockW + 100, 8); x.restore(); }
  const nChars = hs === 'terminal' ? Math.floor(t * 46) + 6 : 1e9; let used = 0;
  lines.forEach((ln, li) => { const txt = ln.map(z => z.replace(/\*/g, '')), full = txt.join(' '), tw = x.measureText(full).width; let px = CX - tw / 2;
    ln.forEach((w, wi) => { const key = w.includes('*'); let word = txt[wi]; const ww = x.measureText(word).width, yy = y0 + li * lh;
      if (hs === 'terminal') { const left = Math.max(0, nChars - used); used += word.length + 1; word = word.slice(0, left); }
      if (hs === 'pop' && key) { x.fillStyle = S.accent; x.fillRect(px - 12, yy - size * .8, ww + 24, size * .98); }
      x.textAlign = 'left';
      if (hs === 'outline') { x.strokeStyle = key ? S.accent : e.ink; x.lineWidth = size * .045; x.strokeText(word, px, yy); if (key) { x.fillStyle = S.accent; x.fillText(word, px, yy); } }
      else if (hs === 'sticker') { x.fillStyle = S.on_accent; x.fillText(word, px, yy); }
      else if (hs === 'terminal') { x.fillStyle = key ? S.accent : '#b6ffcc'; x.fillText(word, px, yy); }
      else { x.strokeStyle = dark ? 'rgba(0,0,0,.75)' : 'rgba(255,255,255,.8)'; if (!key) x.strokeText(word, px, yy); x.fillStyle = key ? S.on_accent : e.ink; x.fillText(word, px, yy); }
      px += ww + x.measureText(' ').width; x.textAlign = 'center'; }); });
  if (hs === 'terminal' && Math.floor(t * 3) % 2 === 0) { x.fillStyle = S.accent; x.fillRect(CX + blockW / 2 + 8, y0 + (lines.length - 1) * lh - size * .8, size * .4, size * .85); }
  x.restore();
}
function captions(t, F) {
  if (S.caption.mode === 'off') return;
  const c = CHUNKS.find(c => t >= c.s && t < c.end); if (!c) return;
  const sc = TL.scenes[c.scene], e = env(sc), mode = S.caption.mode;
  x = octx; x.save(); x.setTransform(1, 0, 0, 1, 0, 0);
  x.translate(F.sx * .5, F.sy * .5);
  const out = clamp((c.end - t) / .1), Y = S.caption.y ?? 1390;
  x.globalAlpha = out;
  if (mode === 'typeon') { const ci = CHUNKS.indexOf(c), pc = CHUNKS[ci - 1];
    if (pc && pc.scene === c.scene && t - c.s < 3 / FPS) { x.save(); captionTypeOn(pc, t, e, .28, pc.end); x.restore(); }   // word swap: old phrase ghosts for 2-3 frames
    captionTypeOn(c, t, e, 1, t); }
  else if (mode === 'stack') captionStack(c, t, e); else if (mode === 'clean') captionClean(c, t, e, Y); else if (mode === 'type') captionType(c, t, e, Y);
  else if (c.key) captionSlam(c, t, e, Y); else captionPop(c, t, e, Y);
  x.restore();
}
function shadowText(s, px, py, fill, sh = 'rgba(0,0,0,.55)') { x.fillStyle = sh; x.fillText(s, px + 4, py + 6); x.fillStyle = fill; x.fillText(s, px, py); }
function captionPop(c, t, e, Y) {
  const fam = S.fonts.text, wt = S.fonts.text_weight, size = S.caption.size || 86;
  const txt = c.words.map(w => caseT(w.w)).join(' '); const sz = fitFont(txt, fam, wt, 960, size);
  x.textBaseline = 'middle'; x.textAlign = 'left'; const sp = x.measureText(' ').width; let px = CX - x.measureText(txt).width / 2;
  for (const w of c.words) { const s = caseT(w.w), ww = x.measureText(s).width, l = t - w.s;
    if (l >= -.02) { const k = 1 - .5 * Math.exp(-12 * Math.max(0, l)) * Math.cos(16 * Math.max(0, l));
      x.save(); x.translate(px + ww / 2, Y); x.scale(k, k); x.textAlign = 'center';
      shadowText(s, 0, 0, e.ink, e.bright ? 'rgba(0,0,0,.18)' : 'rgba(0,0,0,.6)'); x.restore(); }
    px += ww + sp; }
}
function balanced(words) { if (words.length < 2) return [words.join(' ')];
  let best = null; for (let i = 1; i < words.length; i++) { const a = words.slice(0, i).join(' '), b = words.slice(i).join(' ');
    const d = Math.abs(a.length - b.length); if (!best || d < best[0]) best = [d, [a, b]]; } return best[1]; }
function captionSlam(c, t, e, Y) {
  const fam = S.fonts.display, wt = S.fonts.display_weight, l = Math.max(0, t - c.s - .04);
  const words = c.words.map(w => caseT(w.w.replace(/[.,!?;:]+$/, '')));
  let lines = [words.join(' ')]; x.font = `${wt} 210px "${fam}"`;
  if (x.measureText(lines[0]).width > 820 && words.length > 1) lines = balanced(words);
  let sz = 220; for (const ln of lines) sz = Math.min(sz, fitFont(ln, fam, wt, 800, 220, 60));
  x.font = `${wt} ${sz}px "${fam}"`; const lh = sz * 1.02, h = lines.length * lh, wmax = Math.max(...lines.map(s => x.measureText(s).width));
  const sc = 1 + .55 * Math.exp(-11 * l) * Math.cos(17 * l), rot = -.07 * Math.exp(-9 * l);
  // when the stage behind is accent-colored (burst finale, accent backgrounds) invert: dark slab, white text
  const scn = TL.scenes[c.scene], burstOn = scn.type === 'burst' && t >= (scn.keys[0] ? scn.keys[0].s : scn.start);
  const near = (a, b) => { const A = rgb(a), B = rgb(b); return Math.hypot(A[0] - B[0], A[1] - B[1], A[2] - B[2]) < 120; };
  const inv = burstOn || near(S.accent, e.bg[0]) || near(S.accent, e.bg[1]);
  const slab = S.caption.slab, slabCol = inv ? '#0b0b0f' : S.accent, onAcc = inv ? '#ffffff' : S.on_accent;
  x.save(); x.translate(CX, Y); x.rotate(rot); x.scale(sc, sc);
  // outline echo
  const ek = clamp(l / .35); if (ek < 1) { x.save(); x.globalAlpha *= (1 - ek) * .7; x.scale(1 + ek * .35, 1 + ek * .35); x.strokeStyle = inv ? '#ffffff' : S.accent; x.lineWidth = 4;
    x.textAlign = 'center'; x.textBaseline = 'middle'; x.font = `${wt} ${sz}px "${fam}"`; lines.forEach((s, i) => x.strokeText(s, 0, -h / 2 + lh * (i + .5))); x.restore(); }
  if (slab) { const wp = easeOutExpo(l / .14), pw = wmax + 56, ph = h + 30; x.save(); x.transform(1, 0, -.16, 1, 0, 0);
    x.fillStyle = slabCol; x.fillRect(-pw / 2, -ph / 2, pw * wp, ph); x.restore(); }
  x.textAlign = 'center'; x.textBaseline = 'middle';
  lines.forEach((s, i) => { const yy = -h / 2 + lh * (i + .5) + sz * .04;
    if (slab) { x.fillStyle = onAcc; x.fillText(s, 0, yy); } else shadowText(s, 0, yy, S.accent); });
  x.restore();
}
function wrapWords(words, maxW) { const lines = [[]]; let w0 = 0; const sp = x.measureText(' ').width;
  for (const w of words) { const ww = x.measureText(w.t).width; if (lines[lines.length - 1].length && w0 + sp + ww > maxW) { lines.push([]); w0 = 0; }
    lines[lines.length - 1].push(w); w0 += (w0 ? sp : 0) + ww; } return lines; }
function captionClean(c, t, e, Y) {
  const fam = S.fonts.text, wt = S.fonts.text_weight; const size = Math.min(84, S.caption.size || 84);
  x.font = `${wt} ${size}px "${fam}"`; x.textBaseline = 'middle'; x.textAlign = 'left';
  const ws = c.words.map(w => ({ ...w, t: caseT(w.w) })); const lines = wrapWords(ws, 920), lh = size * 1.22, sp = x.measureText(' ').width;
  lines.forEach((ln, li) => { const lw = ln.reduce((a, w) => a + x.measureText(w.t).width, 0) + sp * (ln.length - 1); let px = CX - lw / 2;
    const yy = Y - (lines.length - 1) * lh / 2 + li * lh;
    for (const w of ln) { const ww = x.measureText(w.t).width, l = t - w.s;
      if (l > -.02) { const p = easeOutExpo(l / .25);
        x.save(); x.beginPath(); x.rect(px - 10, yy - lh / 2, ww + 20, lh); x.clip();
        if (w.k && S.caption.slab) { const hp = easeOutExpo(l / .2); x.fillStyle = S.accent; x.fillRect(px - 8, yy - size * .56, (ww + 16) * hp, size * 1.18); }
        const col = w.k ? (S.caption.slab ? S.on_accent : S.accent) : e.ink;
        x.fillStyle = e.bright ? 'rgba(0,0,0,.08)' : 'rgba(0,0,0,.45)'; x.fillText(w.t, px + 3, yy + lh * (1 - p) + 4);
        x.fillStyle = col; x.fillText(w.t, px, yy + lh * (1 - p)); x.restore(); }
      px += ww + sp; } });
}
function captionType(c, t, e, Y) {
  const fam = S.fonts.text, wt = S.fonts.text_weight, size = 70; x.font = `${wt} ${size}px "${fam}"`; x.textBaseline = 'middle'; x.textAlign = 'left';
  const ws = c.words.map(w => ({ ...w, t: caseT(w.w) })); const lines = wrapWords(ws, 940), lh = size * 1.3, sp = x.measureText(' ').width;
  let cursor = null;
  lines.forEach((ln, li) => { const lw = ln.reduce((a, w) => a + x.measureText(w.t).width, 0) + sp * (ln.length - 1); let px = CX - lw / 2; const yy = Y - (lines.length - 1) * lh / 2 + li * lh;
    for (const w of ln) { const n = Math.floor(clamp((t - w.s) / Math.max(.05, (w.e - w.s) * .8)) * w.t.length); const s = w.t.slice(0, n);
      if (n > 0) { if (w.k && S.caption.slab) { x.fillStyle = S.accent; x.fillRect(px - 6, yy - size * .55, x.measureText(s).width + 12, size * 1.1); x.fillStyle = S.on_accent; }
        else x.fillStyle = w.k ? S.accent : e.ink; x.fillText(s, px, yy); cursor = [px + x.measureText(s).width + 6, yy]; }
      px += x.measureText(w.t).width + sp; } });
  if (cursor && Math.floor(t * 2.5) % 2 === 0) { x.fillStyle = S.accent; x.fillRect(cursor[0], cursor[1] - size * .45, size * .5, size * .9); }
}


/* ---- stack mode: kinetic typography "text stack". Words pop in one by one as spoken and pile up into a tight,
   ragged block. Size follows importance (*keywords* huge, short filler words small), one accent word per
   sentence uses the text font, phrase after a comma/period flips color, block clears at sentence end. */
function stackLayout(c) {
  if (c._lay) return c._lay;
  const fam = S.fonts.display, wt = S.fonts.display_weight, fam2 = S.fonts.text, wt2 = S.fonts.text_weight;
  const maxW = 900, maxH = S.caption.stack_h || 800, cap = S.caption.stack_size || 1.2;
  let ph = 0;
  const items = c.words.map((w, i) => { const brk = /[.,!?;:]$/.test(w.w); const t = caseT(w.w.replace(/[.,!?;:"]+$/, ''));
    const n = t.replace(/[^A-Za-z0-9]/g, '').length || 1;
    const it = { w, t, ph, i, key: !!w.k, base: (w.k ? 250 : n <= 3 ? 88 : n <= 5 ? 128 : 156) * cap, fam, wt }; if (brk) ph++; return it; });
  let best = -1, bs = -1;
  items.forEach((it, i) => { if (!it.key && it.t.length >= 5) { const sc = R('stk', c.scene, i); if (sc > bs) { bs = sc; best = i; } } });
  if (best >= 0) { items[best].fam = fam2; items[best].wt = wt2; items[best].base *= .78; }
  x = octx; let k = 1, lines = [], H2 = 0;
  for (let pass = 0; pass < 10; pass++) {
    items.forEach(it => { it.size = it.base * k; x.font = `${it.wt} ${it.size}px "${it.fam}"`; it.ww = x.measureText(it.t).width;
      if (it.ww > maxW) { it.size *= maxW / it.ww; x.font = `${it.wt} ${it.size}px "${it.fam}"`; it.ww = x.measureText(it.t).width; } });
    lines = [[]]; let w0 = 0;
    for (const it of items) { const gap = 12 * k; if (lines[lines.length - 1].length && w0 + gap + it.ww > maxW) { lines.push([]); w0 = 0; }
      lines[lines.length - 1].push(it); w0 += (w0 ? gap : 0) + it.ww; }
    H2 = lines.reduce((a, ln) => a + Math.max(...ln.map(i => i.size)) * .9, 0);
    if (H2 <= maxH) break; k *= .88;
  }
  let yy = -H2 / 2;
  lines.forEach((ln, li) => { const lh = Math.max(...ln.map(i => i.size)) * .9; const lw = ln.reduce((a, i) => a + i.ww, 0) + 12 * k * (ln.length - 1);
    let px = -lw / 2 + Rs('stkx', c.scene, li) * 24;
    for (const it of ln) { it.x = px + it.ww / 2; it.y = yy + lh + it.size * .08 - Math.abs(Rs('stky', c.scene, it.i)) * lh * .12; it.rot = Rs('stkr', c.scene, it.i) * .035; px += it.ww + 12 * k; }
    yy += lh; });
  return (c._lay = items);
}
function captionStack(c, t, e) {
  const items = stackLayout(c), cy = S.caption.stack_y ?? 1200;
  x.textBaseline = 'alphabetic'; x.textAlign = 'center';
  for (const it of items) { const l = t - it.w.s; if (l < -.02) continue; const L = Math.max(0, l);
    const sc = 1 + .32 * Math.exp(-13 * L) * Math.cos(19 * L), a = clamp((l + .02) / .06);
    const col = it.key ? S.accent : (it.ph % 2 ? mixc(e.ink, S.accent, .6) : e.ink);
    x.save(); x.globalAlpha *= a; x.translate(CX - 20 + it.x, cy + it.y); x.rotate(it.rot); x.scale(sc, sc);
    x.font = `${it.wt} ${it.size}px "${it.fam}"`;
    x.fillStyle = e.bright ? 'rgba(0,0,0,.16)' : 'rgba(0,0,0,.62)'; x.fillText(it.t, 5, 7);
    x.fillStyle = col; x.fillText(it.t, 0, 0); x.restore(); }
}


/* ---- typeon mode: heavy condensed capitals typed letter by letter on the spoken word; *keywords* sit on an accent label box that grows with
   the letters; scene param "scramble": true makes keywords decode from random letters; a trailing "..." types on like any letters. */
function typeonLayout(c) {
  if (c._tl) return c._tl;
  const fam = S.fonts.display, wt = S.fonts.display_weight, maxW = S.caption.typeon_w || 900, pad = 24; let size = S.caption.typeon_size || 168, lines = [], sp = 0;
  const items = c.words.map(w => ({ w, t: (w.k ? w.w.replace(/[,.;:!?]+$/, '') : w.w).toUpperCase().replace(/[“”"]/g, ''), key: !!w.k }));
  x = octx;
  for (let pass = 0; pass < 10; pass++) {
    x.font = `${wt} ${size}px "${fam}"`; sp = x.measureText(' ').width * .9; lines = [[]]; let w0 = 0;
    for (const it of items) { it.ww = x.measureText(it.t).width; it.bw = it.ww + (it.key ? pad * 2 : 0);
      if (lines[lines.length - 1].length && w0 + sp + it.bw > maxW) { lines.push([]); w0 = 0; } lines[lines.length - 1].push(it); w0 += (w0 ? sp : 0) + it.bw; }
    const fits = lines.length <= 4 && lines.every(l => l.reduce((a, i) => a + i.bw, 0) + sp * (l.length - 1) <= maxW + 1);
    if (fits) break; size *= .9;
  }
  const lh = size * 1.04; let y = -(lines.length * lh) / 2 + lh * .84;
  lines.forEach(ln => { ln.forEach((it, k) => { it.pk = it.key && k > 0 && ln[k - 1].key; it.nk = it.key && k < ln.length - 1 && ln[k + 1].key;   // keyword run = one box
      it.bw = it.ww + (it.key ? (it.pk ? 0 : pad) + (it.nk ? 0 : pad) : 0); });
    const lw = ln.reduce((a, i) => a + i.bw, 0) + sp * (ln.length - 1); let px = -lw / 2;
    ln.forEach(it => { it.bx = px - (it.pk ? sp : 0); it.bwd = it.bw + (it.pk ? sp : 0); it.x = px + (it.key && !it.pk ? pad : 0); it.y = y; px += it.bw + sp; }); y += lh; });
  return (c._tl = { items, size, fam, wt, pad });
}
const SCR = 'ABCDEFGHKLMNPRSTUWXYZ';
function captionTypeOn(c, t, e, alpha, tEff) {
  const L = typeonLayout(c), cy = S.caption.typeon_y ?? 1180, scr = !!(TL.scenes[c.scene].params || {}).scramble;
  x.save(); x.globalAlpha *= alpha; x.translate(CX, cy); x.textBaseline = 'alphabetic'; x.textAlign = 'left'; x.font = `${L.wt} ${L.size}px "${L.fam}"`;
  const dark = lum(e.bg[0]) < .5, shCol = dark ? 'rgba(0,0,0,.55)' : 'rgba(0,0,0,.14)';
  for (const it of L.items) { const w = it.w, n = it.t.length, dur = Math.max(.14, (w.e || w.s + .3) - w.s) * .85, age0 = tEff - w.s; if (age0 < -.02) continue;
    const doScr = scr && it.key, shown = doScr ? n : Math.min(n, Math.max(1, Math.ceil(clamp((age0 + .02) / dur) * n)));
    // label box (keywords): grows with the letters, or eases open while scrambling
    if (it.key) { const target = it.bwd, cur = doScr ? target * easeOutExpo(clamp(age0 / .22)) : Math.min(target, x.measureText(it.t.slice(0, shown)).width + (it.pk ? 0 : L.pad) + (it.nk || shown < n ? 0 : L.pad) + (it.pk ? 0 : 0) + (it.pk ? (it.bwd - it.bw) : 0));
      const bx = it.bx + (doScr ? (target - cur) / 2 : 0); x.fillStyle = S.accent; x.fillRect(bx, it.y - L.size * .80, cur, L.size * .98); }
    for (let j = 0; j < shown; j++) { const born = w.s + j * dur / n, age = Math.max(0, tEff - born); let ch = it.t[j];
      if (doScr) { const lock = w.s + dur * (j + 1) / n + .28; if (tEff < lock) ch = SCR[Math.floor(hash(TL.seed, 'scr', c.scene, j, Math.floor(tEff * 15)) * SCR.length)]; else if (tEff - lock < .1) ch = it.t[j]; }
      const px = it.x + x.measureText(it.t.slice(0, j)).width, cw = x.measureText(ch).width, k = 1 + .34 * Math.exp(-18 * age) * Math.cos(24 * age), rise = (1 - easeOutExpo(age / .1)) * 20;
      x.save(); x.translate(px + cw / 2, it.y + rise); x.scale(k, k);
      x.fillStyle = it.key ? 'rgba(0,0,0,0)' : shCol; if (!it.key) x.fillText(ch, -cw / 2 + 4, 6);
      x.fillStyle = it.key ? S.on_accent : e.ink; x.fillText(ch, -cw / 2, 0); x.restore(); } }
  x.restore();
}

/* ------------------------------------------------------------------ frame */
function renderFrame(f) {
  const t = f / FPS, i = sceneAt(t), sc = TL.scenes[i];
  const fctx = FR.getContext('2d'); fctx.setTransform(1, 0, 0, 1, 0, 0);
  // transitions: window [start-TR_IN, start+TR_OUT] around each cut
  let tr = null;
  const nx = TL.scenes[i + 1]; if (nx && t >= nx.start - TR_IN) tr = { a: i, b: i + 1, p: (t - (nx.start - TR_IN)) / (TR_IN + TR_OUT) };
  else if (i > 0 && t < sc.start + TR_OUT) tr = { a: i - 1, b: i, p: (t - (sc.start - TR_IN)) / (TR_IN + TR_OUT) };
  if (tr && TL.scenes[tr.b].transition !== 'none') {
    drawScene(tr.a, t, LB.getContext('2d')); drawScene(tr.b, t, LA.getContext('2d'));
    transition(TL.scenes[tr.b].transition, clamp(tr.p), LB, LA, fctx, t, TL.scenes[tr.b]);
  } else { drawScene(i, t, LA.getContext('2d')); fctx.globalCompositeOperation = 'source-over'; fctx.drawImage(LA, 0, 0); }
  // camera
  const F = fx(t), lt = t - sc.start, dur = sc.end - sc.start, push = S.camera.push * smooth(lt / dur);
  F.sx = F.amp * (Math.sin(t * 71) * .6 + Math.sin(t * 113 + 1) * .4); F.sy = F.amp * (Math.cos(t * 67) * .6 + Math.sin(t * 97 + 2) * .4);
  const rot = F.amp * .0006 * Math.sin(t * 53), z = 1.05 + push + F.zoom + F.amp / 900;
  const o = octx; o.setTransform(1, 0, 0, 1, 0, 0); o.globalAlpha = 1; o.globalCompositeOperation = 'source-over'; o.filter = 'none';
  o.fillStyle = env(sc).bg[0]; o.fillRect(0, 0, W, H);
  if (S.camera.drift) { F.sx += S.camera.drift * 26 * Math.sin(t * .8) + S.camera.drift * 12 * Math.sin(t * 1.9 + 1); F.sy += S.camera.drift * 20 * Math.cos(t * .7 + 2); }
  drawStage(o, z, rot, F, sc);
  post(t, F, sc);
  decor(t, F, sc);
  captions(t, F);
  if (TL.hook) hookOverlay(t, F);
  // fade in (max .3 s), no fade out (loop-ready); with a hook the first frame is already the hook
  if (!TL.hook && t < .3) { o.globalAlpha = 1 - t / .3; o.fillStyle = S.bg[0]; o.fillRect(0, 0, W, H); o.globalAlpha = 1; }
}
