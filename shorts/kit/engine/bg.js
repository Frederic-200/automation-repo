/* Story-made backgrounds (PLAN_V4). A scene with type "story" (or any scene carrying `bg` that calls bgFill) is composed from:
   - the video's own drawings (meta.art: tiny vector objects the writer draws from the story, 0..200 grid, colour roles),
   - an arrangement (hero/scatter/grid/orbit/stream/stack/split/path/explode/ring/tunnel/wall, combinable with "+"),
   - motions per subject (enter / living / leave tokens), beats tied to spoken keywords (crack, shatter, open, morph, multiply, ...),
   - a generated backdrop (flow, mesh, contour, grid, iso, rays, paper, halftone, scan, ribbon, rings, stars, tile),
   - faint story words and optional data shapes (coins, bars, ring, gauge, line, compare, number).
   Deterministic: only R()/hash. Uses globals of kit.js (x, S, TL, W, H, CX, HY). */
'use strict';
const BG = {};
const BG_BAND = 430;   // half height around HY that every layout shows

/* ---------------------------------------------------------------- colour roles */
BG.col = (role, e) => {
  const P = S.palette;
  switch (role) {
    case 'ink': return e.ink; case 'accent': return S.accent; case 'accent2': return P[1] || S.accent; case 'accent3': return P[2] || e.ink;
    case 'paper': return e.bright ? '#ffffff' : '#f4f1ea'; case 'dark': return '#0b0b10'; case 'gold': return '#ffc94d'; case 'white': return '#ffffff'; case 'red': return '#ff3b30'; case 'green': return '#2ecc71'; case 'blue': return '#3b82f6'; case 'dim': return e.soft; case 'bg': return e.bg[0];
    default: return /^#/.test(role) ? role : e.ink;
  }
};

/* ---------------------------------------------------------------- art renderer */
const _pathLen = {}, _p2d = {};
function artShapeLen(s) {
  if (s._len) return s._len;
  let L = 400;
  if (s.t === 'rect') L = 2 * (s.w + s.h); else if (s.t === 'circle') L = TAU * s.r; else if (s.t === 'ellipse') L = TAU * (s.rx + s.ry) * .5;
  else if (s.t === 'line' || s.t === 'poly') { L = 0; for (let i = 1; i < s.pts.length; i++) L += Math.hypot(s.pts[i][0] - s.pts[i - 1][0], s.pts[i][1] - s.pts[i - 1][1]); if (s.t === 'poly') L += Math.hypot(s.pts[0][0] - s.pts[s.pts.length - 1][0], s.pts[0][1] - s.pts[s.pts.length - 1][1]); }
  else if (s.t === 'path') { try { const el = document.createElementNS('http://www.w3.org/2000/svg', 'path'); el.setAttribute('d', s.d); L = el.getTotalLength(); } catch (e) { L = 400; } }
  return (s._len = Math.max(20, L));
}
/* draw one art object at the origin, size 200 units -> px by the caller's transform.
   o: {style, draw (0..1 draw-on), alpha, partFx {part:{dx,dy,rot,s,a}}, shardT (>0 = shattering), tint (0..1 to white), glitch} */
BG.drawArt = (art, e, o = {}) => {
  const st = o.style || 'flat', shapes = art.shapes || [], draw = o.draw ?? 1;
  x.save(); x.translate(-100, -100); x.lineJoin = 'round'; x.lineCap = 'round';
  shapes.forEach((s, i) => {
    const fx = (s.part && o.partFx && o.partFx[s.part]) || null;
    x.save();
    let a = (s.o ?? 1) * (o.alpha ?? 1);
    if (o.asm > 0.005) { const q = o.asm; x.translate(100 + (hash(TL.seed, 'as', art.id, i, 0) - .5) * 900 * q, 100 + (hash(TL.seed, 'as', art.id, i, 1) - .5) * 900 * q); x.rotate((hash(TL.seed, 'as', art.id, i, 2) - .5) * 5 * q); x.translate(-100, -100); a *= clamp(1 - q * .8); }
    if (o.shardT > 0) { const vx = (hash(TL.seed, 'sh', art.id, i, 0) - .5) * 700, vy = (hash(TL.seed, 'sh', art.id, i, 1) - .3) * 700 + 500 * o.shardT, rr = (hash(TL.seed, 'sh', art.id, i, 2) - .5) * 6;
      const p = o.shardT; x.translate(100 + vx * p, 100 + vy * p * p * .5 + vy * p * .5); x.rotate(rr * p); x.translate(-100, -100); a *= clamp(1 - p * 1.1); }
    if (fx) { const pv = s.pv || [100, 100]; x.translate(pv[0] + (fx.dx || 0), pv[1] + (fx.dy || 0)); x.rotate(fx.rot || 0); const k = fx.s ?? 1; x.scale(k, k); x.translate(-pv[0], -pv[1]); a *= fx.a ?? 1; }
    if (a <= 0.01) { x.restore(); return; }
    x.globalAlpha = clamp(a);
    const bgL = lum(e.bg[0]), fixc = (c) => { const L = lum(c); return Math.abs(L - bgL) < .3 ? (bgL < .5 ? mixc(c, '#ffffff', .62) : mixc(c, '#000000', .6)) : c; };
    const colr = fixc(BG.col(s.c || 'ink', e)), fillOn = s.fill !== undefined ? !!s.fill : (st !== 'line');
    let fillCol = colr; if (o.tint) fillCol = mixc(colr, '#ffffff', o.tint);
    const lw = s.sw ?? (s.t === 'rect' ? undefined : s.w) ?? (st === 'line' ? 8 : st === 'blueprint' ? 4 : st === 'sticker' ? 9 : 7);
    const strokeCol = (st === 'sticker' || st === 'flat' || st === 'paper') ? (bgL < .5 ? '#fbf8f0' : '#14141a') : (st === 'blueprint' ? mixc(colr, '#ffffff', .25) : colr);
    const P2 = () => {
      x.beginPath();
      if (s.t === 'rect') { x.roundRect(s.x, s.y, s.w, s.h, s.r || 0); }
      else if (s.t === 'circle') { x.arc(s.x, s.y, s.r, 0, TAU); }
      else if (s.t === 'ellipse') { x.ellipse(s.x, s.y, s.rx, s.ry, s.rot || 0, 0, TAU); }
      else if (s.t === 'line' || s.t === 'poly') { s.pts.forEach((p, k) => k ? x.lineTo(p[0], p[1]) : x.moveTo(p[0], p[1])); if (s.t === 'poly') x.closePath(); }
    };
    const strokeIt = (w, col) => { x.lineWidth = w; x.strokeStyle = col; if (draw < 1) { const L = artShapeLen(s); x.setLineDash([L, L + 5]); x.lineDashOffset = L * (1 - draw); } x.stroke(); x.setLineDash([]); };
    if (s.t === 'text') {
      x.font = `${S.fonts.display_weight} ${s.size || 40}px "${S.fonts.display}"`; x.textAlign = s.align || 'center'; x.textBaseline = 'middle';
      if (st === 'sticker') { x.lineWidth = 8; x.strokeStyle = strokeCol; x.strokeText(String(s.s), s.x, s.y); }
      x.fillStyle = fillCol; x.globalAlpha = clamp(a) * clamp(draw * 1.6); x.fillText(String(s.s), s.x, s.y);
    } else {
      const isPath = s.t === 'path';
      if (st === 'sticker') { x.save(); x.translate(5, 7); x.globalAlpha *= .32; x.fillStyle = '#000'; if (isPath) x.fill(_p2d[s.d] || (_p2d[s.d] = new Path2D(s.d))); else if (s.t !== 'line') { P2(); x.fill(); } x.restore(); }
      if (fillOn && s.t !== 'line') {
        x.globalAlpha = clamp(a) * (st === 'blueprint' ? .14 : 1) * (o.draw < 1 ? clamp((draw - .6) * 2.5) : 1); x.fillStyle = fillCol;
        if (isPath) x.fill(_p2d[s.d] || (_p2d[s.d] = new Path2D(s.d))); else { P2(); x.fill(); } x.globalAlpha = clamp(a);
      }
      if (lw > 0 || s.t === 'line') {
        const w = lw || 7, col = (st === 'line' || st === 'blueprint' || s.t === 'line') ? fillCol : strokeCol;
        if (isPath) { const p = _p2d[s.d] || (_p2d[s.d] = new Path2D(s.d)); x.lineWidth = w; x.strokeStyle = col; if (draw < 1) { const L = artShapeLen(s); x.setLineDash([L, L + 5]); x.lineDashOffset = L * (1 - draw); } x.stroke(p); x.setLineDash([]); }
        else { P2(); strokeIt(w, col); }
      }
    }
    x.restore();
  });
  if (o.glitch) { x.globalAlpha = .5 * o.glitch; x.globalCompositeOperation = 'lighter'; x.translate(8 * o.glitch, 0); }
  x.restore();
};
BG.art = (id) => { const A = (TL.art || {})[id]; return A ? (A.id ? A : (A.id = id, A)) : null; };

/* ---------------------------------------------------------------- motion tokens */
const ENTER = ['pop', 'slide', 'drop', 'crawl', 'draw', 'assemble', 'fade', 'zoom'];
const LIVING = ['float', 'pulse', 'wobble', 'drift', 'breathe', 'blink', 'swarm', 'spin', 'scan'];
const LEAVE = ['fall', 'dissolve', 'shrink', 'wipe'];
BG.parseMotion = (str) => {
  const w = String(str || '').toLowerCase().split(/[^a-z\-]+/).filter(Boolean), m = { enter: null, living: [], leave: null, from: 'left', speed: 1 };
  w.forEach((t, i) => { if (ENTER.includes(t) && !m.enter) m.enter = t; else if (LIVING.includes(t)) m.living.push(t); else if (LEAVE.includes(t)) m.leave = t;
    if (t === 'from' && w[i + 1]) m.from = w[i + 1].replace('top', 'up').replace('bottom', 'down'); if (t === 'fast') m.speed = 1.6; if (t === 'slow') m.speed = .6; });
  return m;
};
BG.knownMotion = (str) => { const m = BG.parseMotion(str); return !!(m.enter || m.living.length || m.leave); };

/* ---------------------------------------------------------------- arrangements -> instance placements */
const BAND_Y0 = () => HY - BG_BAND, BAND_Y1 = () => HY + BG_BAND;
BG.place = (kind, n, subs, bg, lt, sc) => {
  const out = [], sd = (...a) => R('bgp', sc.i, kind, ...a), focus = bg.focus || 'center';
  const fx = focus.includes('left') ? -190 : focus.includes('right') ? 190 : 0, fy = focus.includes('top') ? -170 : focus.includes('bottom') ? 170 : 0;
  const cx = CX + fx, cy = HY + fy, pick = (i) => subs[i % subs.length], dur = Math.max(1, sc.end - sc.start);
  const add = (i, px, py, s, rot = 0, delay = 0, extra = {}) => out.push({ i, art: pick(i), x: px, y: clamp(py, BAND_Y0(), BAND_Y1()), s, rot, delay, ...extra });
  switch (kind) {
    case 'none': break;
    case 'hero': add(0, cx, cy, bg._hs || 3.3, 0, 0, { hero: 1 }); break;
    case 'scatter': for (let i = 0; i < n; i++) add(i, 200 + sd(i, 'x') * 680, BAND_Y0() + 120 + sd(i, 'y') * (BG_BAND * 2 - 240), 1.25 + sd(i, 's') * .6, (sd(i, 'r') - .5) * .8, i * .07); break;
    case 'grid': { const cols = Math.max(2, Math.ceil(Math.sqrt(n * .8))), rows = Math.ceil(n / cols), gx = 760 / cols, gy = Math.min(300, 800 / rows);
      for (let i = 0; i < n; i++) add(i, cx - 380 + gx * (i % cols + .5), cy - (rows - 1) * gy / 2 + Math.floor(i / cols) * gy, Math.min(gx, gy) / 230 * 1.1, 0, i * .06); break; }
    case 'orbit': { const sp = .35 * (bg.speed || 1); for (let i = 0; i < n; i++) { const a = i / n * TAU + lt * sp; add(i, cx + Math.cos(a) * 380, cy + Math.sin(a) * 330, 1.3 + .2 * Math.sin(a + 1), 0, i * .08); } break; }
    case 'stream': { const sp = .16 * (bg.speed || 1), dir = (bg.angle ?? -20) * Math.PI / 180;
      for (let i = 0; i < n; i++) { const u = (((i / n) + lt * sp) % 1 + 1) % 1, px = -120 + u * 1320, py = cy + (u - .5) * Math.tan(dir) * 1000 + Math.sin(u * TAU * 1.5 + i) * 70; add(i, px, py, 1.25 + .35 * sd(i, 's'), Math.sin(u * 8 + i) * .15, 0); } break; }
    case 'stack': { const w = 230; for (let i = 0; i < n; i++) add(i, cx + Math.sin(i * 1.7) * 26, cy + BG_BAND * .72 - i * (w * .6) , 1.45, Math.sin(i * 2.3) * .06, i * .22); break; }
    case 'split': for (let i = 0; i < Math.max(2, n); i++) { const side = i % 2 ? 1 : -1; add(i, CX + side * 255, cy + (Math.floor(i / 2) - .5 * (Math.ceil(n / 2) - 1)) * 330, 2.1 - .15 * Math.floor(i / 2), 0, Math.floor(i / 2) * .2 + (side > 0 ? .15 : 0)); } break;
    case 'path': for (let i = 0; i < n; i++) { const u = (i + .5) / n, px = 150 + u * 780, py = cy + Math.sin(u * Math.PI * 2) * 250; add(i, px, py, 1.4, Math.cos(u * Math.PI * 2) * .35, i * .16); } break;
    case 'explode': for (let i = 0; i < n; i++) { const a = i / n * TAU + sd(i, 'a') * .6, d = 120 + sd(i, 'd') * 330; add(i, cx + Math.cos(a) * d, cy + Math.sin(a) * d * .85, 1.2 + sd(i, 's') * .7, a, 0, { burst: 1, ang: a, dist: d }); } break;
    case 'ring': for (let i = 0; i < n; i++) { const a = i / n * TAU - Math.PI / 2; add(i, cx + Math.cos(a) * 340, cy + Math.sin(a) * 340, 1.3, a + Math.PI / 2, i * .1); } break;
    case 'tunnel': for (let i = 0; i < n; i++) { const z = (((i / n) + lt * .22 * (bg.speed || 1)) % 1 + 1) % 1, a = sd(i, 'a') * TAU, rr = z * z * 520; add(i, cx + Math.cos(a) * rr, cy + Math.sin(a) * rr * .85, .15 + z * z * 2.3, a, 0, { alpha: clamp(z * 2.5) * (1 - clamp((z - .9) * 10)) }); } break;
    case 'wall': { const cols = Math.max(3, Math.round(Math.sqrt(n))), rows = Math.ceil(n / cols), cs = 900 / cols; for (let i = 0; i < n; i++) add(i, 90 + cs * (i % cols + .5) + ((Math.floor(i / cols) % 2) ? cs / 2 : 0), HY - 400 + Math.floor(i / cols) * (800 / rows) + 40, cs / 260, 0, i * .03, { alpha: .35 }); break; }
    default: add(0, cx, cy, 2.2, 0, 0, { hero: 1 });
  }
  return out;
};

/* ---------------------------------------------------------------- per-instance motion -> transform */
BG.motion = (inst, m, lt, tt, sc) => {
  const T = { dx: 0, dy: 0, rot: 0, s: 1, a: 1, draw: 1, assemble: 0 }, d = lt - inst.delay, sp = m.speed || 1;
  const en = m.enter || 'pop', k = clamp(d * 2.6 * sp);
  if (d < 0) { T.a = 0; return T; }
  if (en === 'pop') T.s = Math.max(.001, spring(d * sp, { zeta: .45, w0: 14 }));
  else if (en === 'zoom') { T.s = .2 + .8 * easeOutExpo(k); T.a = clamp(k * 2); }
  else if (en === 'fade') T.a = clamp(d * 2.2 * sp);
  else if (en === 'slide') { const dirx = m.from === 'right' ? 1 : m.from === 'left' ? -1 : 0, diry = m.from === 'down' ? 1 : m.from === 'up' ? -1 : 0, e1 = 1 - easeOutQuart(k); T.dx = dirx * 900 * e1; T.dy = diry * 900 * e1; }
  else if (en === 'drop') { T.dy = -1000 * (1 - easeOutBack(clamp(d * 1.6 * sp), 1.4)); }
  else if (en === 'crawl') { const dirx = m.from === 'right' ? 1 : -1, e1 = clamp(d * .55 * sp); T.dx = dirx * 1000 * (1 - easeInOutCubic(e1)); T.dy = Math.sin(d * 9 * sp) * 14 * (1 - e1); T.rot = Math.sin(d * 9 * sp) * .07 * (1 - e1); }
  else if (en === 'draw') { T.draw = easeInOutCubic(clamp(d * .9 * sp)); T.a = clamp(d * 8); }
  else if (en === 'assemble') { T.assemble = 1 - easeOutQuart(clamp(d * 1.1 * sp)); }
  const tn = tt;   // living motions use absolute time so they continue across the scene
  for (const l of m.living) {
    if (l === 'float') T.dy += Math.sin(tn * 1.6 * sp + inst.i) * 16;
    else if (l === 'pulse') T.s *= 1 + .06 * Math.sin(tn * 4 * sp + inst.i);
    else if (l === 'wobble') T.rot += Math.sin(tn * 3 * sp + inst.i) * .08;
    else if (l === 'drift') { T.dx += Math.sin(tn * .5 * sp + inst.i * 2) * 40; T.dy += Math.cos(tn * .4 * sp + inst.i) * 26; }
    else if (l === 'breathe') T.s *= 1 + .035 * Math.sin(tn * 1.9 * sp);
    else if (l === 'blink') T.a *= (Math.floor(tn * 3 * sp + inst.i * .37) % 4 === 0) ? .35 : 1;
    else if (l === 'swarm') { T.dx += (hash(TL.seed, 'sw', inst.i, Math.floor(tn * 14)) - .5) * 22; T.dy += (hash(TL.seed, 'sw2', inst.i, Math.floor(tn * 14)) - .5) * 22; }
    else if (l === 'spin') T.rot += tn * 1.2 * sp;
  }
  if (m.leave) { const rem = sc.end - tt, k2 = clamp(1 - rem / .45); if (m.leave === 'fall') { T.dy += 900 * k2 * k2; T.rot += k2 * .6; } else if (m.leave === 'shrink') T.s *= 1 - k2; else if (m.leave === 'dissolve') T.a *= 1 - k2; else if (m.leave === 'wipe') T.a *= 1 - k2; }
  return T;
};

/* ---------------------------------------------------------------- beats */
BG.beatTimes = (bg, sc) => (bg.beats || []).map(b => {
  let t0 = null;
  if (b.t !== undefined) t0 = sc.start + b.t;
  else if (b.on) { const w = String(b.on).toLowerCase(), key = sc.keys.find(k => String(k.w).toLowerCase().includes(w)); t0 = key ? key.s : null;
    if (t0 === null) { const ln = (sc.lines || []).find(l => String(l.text || l).toLowerCase().includes(w)); t0 = ln && ln.start !== undefined ? ln.start : (sc.keys[0] ? sc.keys[0].s : sc.start + .6); } }
  const [subj, ...rest] = String(b.do || '').split('.'), act = rest.join('.').split(/[\s:]+/); 
  return { t: t0 ?? sc.start + .6, subj, act: act[0], arg: act[1], raw: b };
});
const crackLine = (sd, w, h, p) => { const pts = [[w * (.35 + sd * .3), 0]]; for (let i = 1; i <= 8; i++) pts.push([w * (.5 + (hash(TL.seed, 'ck', sd, i) - .5) * .7), h * i / 8]); const n = Math.ceil(pts.length * p); return pts.slice(0, Math.max(1, n)); };

/* ---------------------------------------------------------------- backdrops */
BG.backdrop = (bd, e, t, lt, sc) => {
  const kind = (typeof bd === 'string' ? bd : bd && bd.kind) || 'mesh', P = typeof bd === 'object' && bd ? bd : {}, sp = P.speed ?? .5, sc2 = P.scale ?? 1, den = P.density ?? .6, ang = (P.angle ?? 25) * Math.PI / 180;
  const ink = e.ink, acc = S.accent, sd = (...a) => R('bd', sc.i, kind, ...a);
  const g = x.createLinearGradient(0, 0, 0, H); g.addColorStop(0, e.bg[0]); g.addColorStop(1, e.bg[1]); x.fillStyle = g; x.fillRect(-60, -60, W + 120, H + 120);
  x.save();
  if (kind === 'mesh') { for (let i = 0; i < 5; i++) { const px = W * (.15 + .7 * (.5 + .5 * Math.sin(t * sp * .4 + i * 2.1 + sd(i) * 6))), py = H * (.15 + .7 * (.5 + .5 * Math.cos(t * sp * .35 + i * 1.7 + sd(i, 'y') * 6))), col = i % 2 ? S.palette[i % S.palette.length] : acc;
      glowDot(px, py, 620 * sc2, col, .30); } }
  else if (kind === 'flow') { x.lineWidth = 3; const n = Math.round(60 + den * 140);
    for (let i = 0; i < n; i++) { let px = sd(i, 'x') * W, py = sd(i, 'y') * H; x.beginPath(); x.moveTo(px, py);
      for (let k = 0; k < 22; k++) { const a = ang + fbm(px / (420 * sc2), py / (420 * sc2) + t * sp * .12, 3, 2) * 4; px += Math.cos(a) * 26; py += Math.sin(a) * 26; x.lineTo(px, py); }
      x.strokeStyle = rgba(i % 5 ? ink : acc, i % 5 ? .1 : .3); x.stroke(); } }
  else if (kind === 'contour') { const step = 70 / sc2; for (let k = -2; k < 20; k++) { x.beginPath(); for (let px = -20; px <= W + 20; px += 24) { const py = k * step * 1.1 + 80 + fbm(px / 360, k * .4 + t * sp * .08, 7, 3) * 150 * (.6 + den); px === -20 ? x.moveTo(px, py) : x.lineTo(px, py); }
      x.strokeStyle = rgba(k % 4 ? ink : acc, k % 4 ? .09 : .22); x.lineWidth = 3; x.stroke(); } }
  else if (kind === 'grid') { const gs = 120 / sc2, off = (t * sp * 40) % gs; x.strokeStyle = rgba(ink, .09); x.lineWidth = 2; x.translate(CX, HY); x.rotate(ang * .3); x.translate(-CX, -HY);
    for (let px = -gs + off - 600; px < W + 600; px += gs) { x.beginPath(); x.moveTo(px, -600); x.lineTo(px, H + 600); x.stroke(); } for (let py = -gs + off - 600; py < H + 600; py += gs) { x.beginPath(); x.moveTo(-600, py); x.lineTo(W + 600, py); x.stroke(); }
    for (let i = 0; i < 14 * den + 4; i++) circle(Math.round(sd(i, 'x') * 9) * gs + off - 600, Math.round(sd(i, 'y') * 12) * gs + off - 600, 6, acc, .5); }
  else if (kind === 'iso') { const s = 110 / sc2, off = (t * sp * 30) % s; x.strokeStyle = rgba(ink, .1); x.lineWidth = 2;
    for (let k = -20; k < 30; k++) { x.beginPath(); x.moveTo(-100, HY + 200 + k * s * .58 + off); x.lineTo(W + 100, HY + 200 + k * s * .58 + off + (W + 200) * .577); x.stroke(); x.beginPath(); x.moveTo(-100, HY + 200 + k * s * .58 + off); x.lineTo(W + 100, HY + 200 + k * s * .58 + off - (W + 200) * .577); x.stroke(); }
    for (let i = 0; i < 6 + den * 8; i++) { const px = sd(i, 'x') * W, py = HY + 100 + sd(i, 'y') * 700, h2 = 40 + sd(i, 'h') * 160 * (.6 + .4 * Math.sin(t * sp + i)); poly([[px, py - h2], [px + 70, py - h2 + 40], [px, py - h2 + 80], [px - 70, py - h2 + 40]], rgba(acc, .22)); poly([[px - 70, py - h2 + 40], [px, py - h2 + 80], [px, py + 80], [px - 70, py + 40]], rgba(ink, .09)); poly([[px + 70, py - h2 + 40], [px, py - h2 + 80], [px, py + 80], [px + 70, py + 40]], rgba(ink, .15)); } }
  else if (kind === 'rays') { x.translate(CX, HY); const n = Math.round(10 + den * 20); for (let i = 0; i < n; i++) { const a = i / n * TAU + t * sp * .1 + ang, w = TAU / n * .45; x.beginPath(); x.moveTo(0, 0); x.arc(0, 0, 1700, a, a + w); x.closePath(); x.fillStyle = rgba(i % 3 ? ink : acc, i % 3 ? .05 : .11); x.fill(); } }
  else if (kind === 'paper') { x.globalAlpha = .6; x.drawImage(PAPER, 0, 0, 512, 512, 0, 0, W, H); x.globalAlpha = 1; for (let i = 0; i < 5; i++) { x.save(); x.translate(sd(i, 'x') * W, sd(i, 'y') * H); x.rotate(sd(i, 'r') * 3); x.fillStyle = rgba(i % 2 ? acc : S.palette[1] || acc, .14); x.fillRect(-260 * sc2, -140 * sc2, 520 * sc2, 280 * sc2); x.restore(); } }
  else if (kind === 'halftone') { const gs = 46 / sc2; for (let py = 0; py < H + gs; py += gs) for (let px = ((py / gs) % 2 ? gs / 2 : 0); px < W + gs; px += gs) { const v = .5 + .5 * Math.sin(px * .006 + py * .004 + t * sp * .6 + ang), r = gs * .5 * v * (.5 + den * .5); circle(px, py, r, rgba(ink, .1)); } }
  else if (kind === 'scan') { x.fillStyle = rgba(ink, .06); for (let py = (t * sp * 60) % 14; py < H; py += 14) x.fillRect(0, py, W, 4); const by = ((t * sp * .22) % 1.2 - .1) * H; const gg = x.createLinearGradient(0, by - 140, 0, by + 140); gg.addColorStop(0, rgba(acc, 0)); gg.addColorStop(.5, rgba(acc, .16)); gg.addColorStop(1, rgba(acc, 0)); x.fillStyle = gg; x.fillRect(0, by - 140, W, 280); }
  else if (kind === 'ribbon') { const n = Math.round(4 + den * 6); for (let k = 0; k < n; k++) { x.beginPath(); for (let px = -40; px <= W + 40; px += 20) { const py = H * (.12 + .76 * k / n) + Math.sin(px * .004 * sc2 + t * sp * .6 + k * 1.3) * 120 + Math.sin(px * .011 + t * sp + k) * 34; px === -40 ? x.moveTo(px, py) : x.lineTo(px, py); } x.strokeStyle = rgba(k % 2 ? acc : ink, k % 2 ? .24 : .1); x.lineWidth = 12 + 8 * (k % 3); x.stroke(); } }
  else if (kind === 'rings') { for (let k = 0; k < 14 * (.6 + den); k++) { const r = ((k * 90 + t * sp * 50) % (1500)) * sc2; ring(CX, HY, r, 3 + (k % 3) * 2, k % 4 ? ink : acc, (k % 4 ? .09 : .22) * (1 - r / 1500)); } }
  else if (kind === 'stars') { const n = Math.round(80 + den * 220); for (let i = 0; i < n; i++) { const z = (((sd(i, 'z')) + t * sp * .04) % 1), px = CX + (sd(i, 'x') - .5) * 2200 * z, py = HY + (sd(i, 'y') - .5) * 2200 * z; circle(px, py, .6 + z * 4.2, i % 7 ? ink : acc, .15 + z * .6); } }
  else if (kind === 'tile') { const art = BG.art(P.art || (sc.bg && sc.bg.subject && sc.bg.subject[0])); if (art) { const cs = 260 / sc2, st = (TL.meta_art_style || 'flat'); for (let j = -1; j < H / cs + 1; j++) for (let i = -1; i < W / cs + 1; i++) { x.save(); x.translate(i * cs + (j % 2 ? cs / 2 : 0) + ((t * sp * 18) % cs), j * cs); x.rotate((j + i) % 2 ? .18 : -.18); x.scale(cs / 420, cs / 420); BG.drawArt(art, e, { style: st, alpha: .07 }); x.restore(); } } }
  x.restore();
};

/* faint story words, kept inside the band so they never reach the caption area */
BG.texture = (words, e, t, sc) => {
  if (!words || !words.length) return; x.save(); x.textAlign = 'center'; x.textBaseline = 'middle'; x.font = `${S.fonts.display_weight} 190px "${S.fonts.display}"`;
  words.slice(0, 4).forEach((w, i) => { const sz = 150 + R('tx', sc.i, i) * 120, px = CX + Math.sin(t * .12 + i * 2) * 220, py = HY - 330 + i * 230 + Math.cos(t * .1 + i) * 50, txt = String(w).toUpperCase();
    x.font = `${S.fonts.display_weight} ${sz}px "${S.fonts.display}"`; x.fillStyle = rgba(e.ink, .06 + .03 * (i % 2)); const wdt = x.measureText(txt).width; if (wdt > 1000) x.font = `${S.fonts.display_weight} ${sz * 1000 / wdt}px "${S.fonts.display}"`; x.fillText(txt, px, py); });
  x.restore();
};

/* ---------------------------------------------------------------- data shapes (built from the real number) */
BG.data = (d, bg, e, t, lt, sc, beats) => {
  const K = keyInfo(sc, t), p = d.progress ?? clamp(spring(lt - .25, { zeta: .8, w0: 7 }) * (d.value / (d.max || d.value)), 0, 1.02) , art = BG.art(d.art), st = TL.meta_art_style || 'flat';
  const lab = d.label || ((d.prefix || '') + d.value + (d.unit || ''));
  const big = (txt, px, py, sz) => { x.save(); x.font = `${S.fonts.display_weight} ${sz}px "${S.fonts.display}"`; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillStyle = '#000'; x.globalAlpha = .25; x.fillText(txt, px + 5, py + 7); x.globalAlpha = 1; x.fillStyle = e.ink; x.fillText(txt, px, py); x.restore(); };
  const mini = (px, py, s, rot = 0, a = 1) => { if (!art) { circle(px, py, 60 * s, S.accent, a); return; } x.save(); x.translate(px, py); x.rotate(rot); x.scale(s, s); BG.drawArt(art, e, { style: st, alpha: a }); x.restore(); };
  const kind = d.kind;
  if (kind === 'ring') { const r = 300; ring(CX, HY, r, 36, e.soft, .5); x.save(); x.lineCap = 'round'; x.strokeStyle = S.accent; x.lineWidth = 36; x.beginPath(); x.arc(CX, HY, r, -Math.PI / 2, -Math.PI / 2 + TAU * clamp(p)); x.stroke(); x.restore(); if (art) mini(CX, HY - 5, 1.05, 0, .95); else big(lab, CX, HY, 150); }
  else if (kind === 'coins') { const n = Math.max(2, Math.min(24, d.count || Math.round(4 + p * 18))); for (let i = 0; i < n; i++) { const dd = lt - i * .08 - .2, pop = spring(dd, { zeta: .5, w0: 14 }); if (dd < 0) continue; mini(CX + Math.sin(i * 1.9) * 34 * (i % 2 ? 1 : -1), HY + 330 - i * 34, .78 * pop, Math.sin(i * 2.2) * .05); } if (d.show_number !== false) big(lab, CX, HY - 330, 140); }
  else if (kind === 'bars') { const vals = d.values || [.3, .5, .8, 1], n = vals.length, bw = 640 / n; vals.forEach((v, i) => { const dd = lt - i * .18 - .2, h = 640 * v * easeOutBack(clamp(dd * 1.3), 1.2); x.fillStyle = i === n - 1 ? S.accent : mixc(e.bg[0], e.ink, .35); x.beginPath(); x.roundRect(CX - 320 + i * bw + 10, HY + 320 - h, bw - 20, h, 18); x.fill(); if (art && dd > .3) mini(CX - 320 + i * bw + bw / 2, HY + 320 - h - 70, .55 * easeOutBack(clamp((dd - .3) * 3)), 0); }); big(lab, CX, HY - 360, 130); }
  else if (kind === 'gauge') { const r = 330, a0 = Math.PI * 1.1, a1 = Math.PI * 1.9; x.save(); x.lineCap = 'round'; x.lineWidth = 44; x.strokeStyle = e.soft; x.beginPath(); x.arc(CX, HY + 120, r, a0, a1); x.stroke(); x.strokeStyle = S.accent; x.beginPath(); x.arc(CX, HY + 120, r, a0, a0 + (a1 - a0) * clamp(p)); x.stroke(); x.restore(); const na = a0 + (a1 - a0) * clamp(p); x.save(); x.translate(CX, HY + 120); x.rotate(na); x.fillStyle = e.ink; x.beginPath(); x.moveTo(-10, 0); x.lineTo(r - 50, 0); x.lineTo(-10, 14); x.fill(); x.restore(); circle(CX, HY + 120, 30, e.ink); big(lab, CX, HY + 330, 130); }
  else if (kind === 'line') { const pts = d.values || [.2, .35, .3, .6, .55, .9], n = pts.length, prog = easeInOutCubic(clamp(lt / 1.4)); x.save(); x.lineWidth = 14; x.strokeStyle = S.accent; x.lineJoin = 'round'; x.lineCap = 'round'; x.beginPath(); let last = [0, 0];
    for (let i = 0; i < n; i++) { const u = i / (n - 1); if (u > prog + 1e-6) { const pu = (prog - (i - 1) / (n - 1)) * (n - 1), a = pts[i - 1], b = pts[i], v = lerp(a, b, clamp(pu)); last = [CX - 380 + prog * 760, HY + 300 - v * 600]; x.lineTo(last[0], last[1]); break; } last = [CX - 380 + u * 760, HY + 300 - pts[i] * 600]; i ? x.lineTo(last[0], last[1]) : x.moveTo(last[0], last[1]); } x.stroke(); x.restore(); mini(last[0], last[1], .5, 0); big(lab, CX, HY - 360, 130); }
  else if (kind === 'compare') { const A = d.a ?? .3, B = d.b ?? 1, nA = Math.max(1, Math.round(A * 10)), nB = Math.max(1, Math.round(B * 10)); [[-250, nA, d.label_a], [250, nB, d.label_b]].forEach(([ox, n, lb], s) => { for (let i = 0; i < n; i++) { const dd = lt - i * .07 - s * .3 - .2; if (dd < 0) continue; mini(CX + ox + ((i % 3) - 1) * 70, HY + 330 - Math.floor(i / 3) * 90, .42 * spring(dd, { zeta: .5, w0: 14 })); } if (lb) big(lb, CX + ox, HY - 380, 90); }); }
  else big(lab, CX, HY, 260);
};


/* giant on-screen numbers: every number the narrator says becomes a picture. bg.numbers = ["27%", "9%"] or [{"text":"27% > 9%","on":"nine"}] */
BG.numbers = (list, e, t, lt, sc) => {
  if (!list || !list.length) return;
  const items = list.map(n => typeof n === 'string' ? { text: n } : n), n = items.length, beats = BG.beatTimes({ beats: items.map(i => ({ on: i.on, t: i.t, do: 'x.pop' })) }, sc);
  const ink = e.ink, dark = lum(e.bg[0]) < .5, plate = dark ? 'rgba(0,0,0,.55)' : 'rgba(255,255,255,.7)';
  items.forEach((it, i) => {
    const t0 = (it.on || it.t !== undefined) ? beats[i].t : sc.start + .25 + i * .5, d = t - t0; if (d < 0) return;
    const txt = String(it.text).replace(/>/g, '\u2192'), size0 = n === 1 ? 330 : 250, py = n === 1 ? HY - 250 : HY - 330 + i * 250;
    x.save(); x.font = `${S.fonts.display_weight} ${size0}px "${S.fonts.display}"`; let w = x.measureText(txt).width, size = size0; if (w > 760) { size = size0 * 760 / w; x.font = `${S.fonts.display_weight} ${size}px "${S.fonts.display}"`; w = x.measureText(txt).width; }
    const k = Math.max(.001, spring(d, { zeta: .5, w0: 15 })), a = clamp(d * 8);
    x.translate(CX, py); x.scale(k, k); x.globalAlpha = a; x.textAlign = 'center'; x.textBaseline = 'middle';
    x.fillStyle = plate; x.beginPath(); x.roundRect(-w / 2 - 34, -size * .62, w + 68, size * 1.18, 30); x.fill();
    x.lineJoin = 'round'; x.lineWidth = size * .08; x.strokeStyle = dark ? '#000' : '#fff'; x.strokeText(txt, 0, 0);
    x.fillStyle = it.accent ? S.accent : ink; x.fillText(txt, 0, 0); x.restore(); });
};

/* ---------------------------------------------------------------- scene entry */
BG.scene = (t, lt, sc, e) => {
  let bg = sc.bg || {}; const tt = t; if ((bg.numbers || []).length && !bg.focus) bg = Object.assign({}, bg, { focus: 'bottom' });
  BG.backdrop(bg.backdrop || 'mesh', e, t, lt, sc);
  BG.texture(bg.texture_words, e, t, sc);
  const style = TL.meta_art_style || 'flat';
  const subs = (bg.subject || []).filter(id => BG.art(id)); const beats = BG.beatTimes(bg, sc);
  const parts = String(bg.arrangement || 'hero').toLowerCase().split(/[+&]/).map(s => s.trim()).filter(Boolean);
  let placed = [];
  parts.forEach((kind, pi) => { const mine = parts.length > 1 ? (pi === 0 ? subs.slice(0, 1) : subs.slice(1)) : subs; if (!mine.length) return;
    const n = (bg.counts && bg.counts[kind]) || bg.count || ({ hero: 1, split: 2, stack: 5, orbit: 5, ring: 6, grid: 6, path: 5, stream: 5, explode: 7, tunnel: 22, scatter: 6, wall: 30 }[kind] || 6);
    BG.place(kind, n, mine, parts.length > 1 ? Object.assign({}, bg, { _hs: 2.6 }) : bg, lt, sc).forEach(p => { p.part = pi; placed.push(p); }); });
  const fxAll = [];
  // draw order: back to front (smaller first) so heroes sit on top
  placed.sort((a, b) => (a.hero ? 1 : 0) - (b.hero ? 1 : 0) || a.s - b.s);
  const mcache = {}; const mfor = (id) => mcache[id] || (mcache[id] = BG.parseMotion((bg.motion || {})[id]));
  for (const p of placed) {
    const art = BG.art(p.art), m = mfor(p.art), T = BG.motion(p, m, lt, tt, sc); if (!art) continue;
    let px = p.x + T.dx, py = p.y + T.dy, s = p.s * T.s, rot = p.rot + T.rot, a = T.a * (p.alpha ?? 1), ex = { style, draw: T.draw, alpha: 1, partFx: {} };
    if (p.burst) { const bt = clamp(lt * 1.3 - .05); px = lerp(CX, p.x, easeOutExpo(bt)); py = lerp(HY, p.y, easeOutExpo(bt)); }
    // beats that target this subject
    for (const b of beats) { if (b.subj !== p.art && b.subj !== '*') continue; const d = tt - b.t; if (d < 0) continue;
      const hero = p.hero || placed.filter(q => q.art === p.art).length === 1 || (p.i === 0);
      if (b.act === 'pop' || b.act === 'grow') s *= 1 + (b.act === 'grow' ? .25 : .0) + .25 * kick(d, 7, 16) + (b.act === 'grow' ? .1 * easeOutQuart(d * 3) : 0);
      else if (b.act === 'shake') { px += Math.sin(d * 90) * 18 * decay(d, 6); py += Math.cos(d * 80) * 12 * decay(d, 6); }
      else if (b.act === 'spin') rot += TAU * easeOutQuart(clamp(d * 1.2));
      else if (b.act === 'flash') ex.tint = .9 * decay(d, 9);
      else if (b.act === 'glow') glowDot(px, py, 260 * s, S.accent, .5 * decay(d, 2.4));
      else if (b.act === 'glitch') { ex.glitch = decay(d, 7); px += (hash(TL.seed, 'gl', Math.floor(d * 30)) - .5) * 30 * decay(d, 7); }
      else if (b.act === 'shatter' && hero) { ex.shardT = clamp(d * 1.1); a *= 1; }
      else if (b.act === 'open') { const part = b.arg || 'lid'; ex.partFx[part] = { rot: -1.15 * easeOutBack(clamp(d * 2.2), 1.6), dy: -10 * clamp(d * 3) }; }
      else if (b.act === 'part') { /* generic: arg is part name, moves it up */ ex.partFx[b.arg] = { dy: -60 * easeOutBack(clamp(d * 2.5)) }; }
      else if (b.act === 'remove') a *= clamp(1 - d * 4);
      else if (b.act === 'crack' && hero) ex.crack = clamp(d * 1.8);
      else if (b.act === 'morph' && b.arg && BG.art(b.arg)) { const k = clamp(d * 2.2); if (k > .5) { ex.swap = b.arg; } s *= 1 + .3 * Math.sin(k * Math.PI); }
    }
    if (a <= .005 || s <= .001) continue;
    const use = ex.swap ? BG.art(ex.swap) : art;
    x.save(); x.translate(px, py); x.rotate(rot); x.scale(s * 1.0, s * 1.0);
    BG.drawArt(use, e, { ...ex, alpha: a, asm: T.assemble });
    if (ex.crack > 0) { x.save(); x.translate(-100, -100); const cl = crackLine(p.i, 200, 200, ex.crack); x.strokeStyle = e.bright ? '#14141a' : '#ffffff'; x.lineWidth = 6; x.lineJoin = 'miter'; x.beginPath(); cl.forEach((q, i) => i ? x.lineTo(q[0], q[1]) : x.moveTo(q[0], q[1])); x.stroke(); x.strokeStyle = S.accent; x.lineWidth = 2.5; x.stroke(); x.restore(); }
    x.restore();
  }
  // beat particles shaped like the subject (mini copies flying out)
  for (const b of beats) { const art = BG.art(b.subj); const d = tt - b.t; if (!art || d < 0 || d > .9 || ['remove', 'part'].includes(b.act)) continue;
    for (let k = 0; k < 9; k++) { const a = k / 9 * TAU + R('bp', sc.i, k), r = 380 * easeOutExpo(d * 1.4), px = CX + Math.cos(a) * r, py = HY + Math.sin(a) * r * .8; x.save(); x.translate(px, clamp(py, BAND_Y0(), BAND_Y1())); x.rotate(a * 2 + d * 3); x.scale(.2, .2); BG.drawArt(art, e, { style, alpha: clamp(1 - d * 1.2) * .9 }); x.restore(); } }
  if (bg.data) BG.data(bg.data, bg, e, t, lt, sc, beats);
  BG.numbers(bg.numbers, e, t, lt, sc);
  // scan sweep
  if (Object.values(bg.motion || {}).some(m => /scan/.test(String(m)))) { const by = HY - BG_BAND + ((t * .5) % 1) * BG_BAND * 2; x.fillStyle = rgba(S.accent, .22); x.fillRect(0, by - 5, W, 10); }
  sc.keys.forEach(k => shockwave && shockwave(CX, HY, t - k.s, S.accent, 700, 10));
};
SCENES.story = (t, lt, sc, e) => BG.scene(t, lt, sc, e);

/* scenes of other types (chat, stat, echo...) that carry `bg` get the story backdrop + faint words behind them */
BG.under = (sc, e, t, lt) => { if (!sc.bg || sc.type === 'story') return false; BG.backdrop(sc.bg.backdrop || 'mesh', e, t, lt, sc); BG.texture(sc.bg.texture_words, e, t, sc); BG.numbers(sc.bg.numbers, e, t, lt, sc); return true; };
