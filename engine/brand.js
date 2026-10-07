/* ============================================================
   FredsDesk brand kit: colors, type, logo (draw-on), background,
   chrome (badge / progress bar) and word-by-word captions.
   Everything is a pure function of time t, so any frame can be
   rendered on its own.
   ============================================================ */
const cv = document.getElementById('c'), ctx = cv.getContext('2d');
const W = 1080, H = 1920, TAU = Math.PI * 2;

const C = {
  bg: '#0A1F33', bg2: '#0F2D48', navy: '#0F4664', teal: '#34B08A', tealL: '#5CE0B5', blue: '#3FA7D6',
  white: '#FFFFFF', mute: 'rgba(255,255,255,.64)', warm: '#FFC857', coral: '#FF7A6B', violet: '#A78BFA', ink: '#08182A'
};
const PAL = [C.blue, C.teal, C.warm, C.coral, C.violet, C.tealL];

/* ---------- math helpers ---------- */
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, t) => a + (b - a) * t;
const sstep = x => { x = clamp(x); return x * x * (3 - 2 * x) };
const eo3 = x => { x = clamp(x); return 1 - Math.pow(1 - x, 3) };
const eback = x => { x = clamp(x); const c = 1.70158, y = x - 1; return 1 + (c + 1) * y * y * y + c * y * y };
const eio = x => { x = clamp(x); return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2 };
const A = (t, t0, d) => eo3((t - t0) / d);                      // 0->1 ease-out starting at t0
const H1 = n => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x) };
const H2 = (n, k) => H1(n * 7.13 + k * 91.7 + k * k * .37);

/* ---------- canvas helpers ---------- */
const FM = (w, s) => `${w} ${s}px M`, FJ = (w, s) => `${w} ${s}px J`;
function circ(x, y, r) { ctx.beginPath(); ctx.arc(x, y, Math.max(.01, r), 0, TAU) }
function rr(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r) }
function rg(x0, y0, r0, x1, y1, r1, st) { const g = ctx.createRadialGradient(x0, y0, r0, x1, y1, r1); for (const [o, c] of st) g.addColorStop(o, c); return g }
function lg(x0, y0, x1, y1, st) { const g = ctx.createLinearGradient(x0, y0, x1, y1); for (const [o, c] of st) g.addColorStop(o, c); return g }
function T(s, x, y, o = {}) {
  ctx.save();
  ctx.font = o.font || FM(800, o.size || 48);
  ctx.textAlign = o.align || 'center'; ctx.textBaseline = o.base || 'alphabetic';
  ctx.letterSpacing = (o.ls || 0) + 'px';
  if (o.alpha !== undefined) ctx.globalAlpha *= clamp(o.alpha);
  if (o.stroke) { ctx.lineJoin = 'round'; ctx.lineWidth = o.stroke; ctx.strokeStyle = o.strokeColor || 'rgba(6,18,32,.92)'; ctx.strokeText(s, x, y) }
  if (o.shadow) { ctx.shadowColor = 'rgba(0,0,0,.45)'; ctx.shadowBlur = o.shadow; ctx.shadowOffsetY = 4 }
  ctx.fillStyle = o.color || C.white; ctx.fillText(s, x, y);
  ctx.restore();
}
function measure(s, font, ls = 0) { ctx.save(); ctx.font = font; ctx.letterSpacing = ls + 'px'; const w = ctx.measureText(s).width; ctx.restore(); return w }
function wrap(s, maxW, font, ls = 0) {
  const words = s.split(' '), lines = []; let cur = '';
  for (const w of words) { const t = cur ? cur + ' ' + w : w; if (measure(t, font, ls) > maxW && cur) { lines.push(cur); cur = w } else cur = t }
  if (cur) lines.push(cur); return lines;
}
function fitSize(s, weight, size, maxW, mono = false, ls = 0) {
  const w = measure(s, mono ? FJ(weight, size) : FM(weight, size), ls); return w > maxW ? size * maxW / w : size;
}
function glass(x, y, w, h, r = 36, a = .07) {
  rr(x, y, w, h, r); ctx.fillStyle = `rgba(255,255,255,${a})`; ctx.fill();
  ctx.lineWidth = 2; ctx.strokeStyle = 'rgba(255,255,255,.13)'; ctx.stroke();
}
function pill(x, y, w, h, fill, stroke) { rr(x, y, w, h, h / 2); if (fill) { ctx.fillStyle = fill; ctx.fill() } if (stroke) { ctx.lineWidth = 2; ctx.strokeStyle = stroke; ctx.stroke() } }

/* ---------- cue lookup: when does the narrator say a word? ---------- */
const norm = s => s.toLowerCase().replace(/[^a-z0-9']/g, '');
function wordTime(S, cue, fallback) {
  if (!cue) return fallback;
  let exact = false, n = 1, c = cue;
  if (c[0] === '=') { exact = true; c = c.slice(1) }
  const m = /^(.*)#(\d+)$/.exec(c); if (m) { c = m[1]; n = +m[2] }
  c = norm(c); let k = 0;
  for (const w of S.words) { const nw = norm(w.w); if (exact ? nw === c : nw.startsWith(c)) { if (++k === n) return w.t0 } }
  return fallback;
}

/* ---------- logo: desk + monitor + cursor, drawn as line art ---------- */
const LOGO = {
  cx: 704, cy: 311,
  paths: [
    { p: [[613, 161], [795, 161], [795, 272], [613, 272], [613, 161]], lw: 12 },
    { p: [[685, 278], [679, 299]], lw: 9 }, { p: [[722, 278], [731, 299]], lw: 9 },
    { p: [[532, 306], [876, 306], [876, 339], [532, 339], [532, 306]], lw: 12 },
    { p: [[564, 345], [564, 461], [588, 461], [588, 353]], lw: 12 },
    { p: [[843, 345], [843, 467]], lw: 12 },
    { p: [[747, 340], [747, 413], [843, 413]], lw: 12 },
    { p: [[747, 360], [843, 360]], lw: 12 }
  ],
  cursor: [[724, 203], [759, 216], [748, 222], [762, 236], [755, 242], [741, 228], [736, 240]]
};
for (const q of LOGO.paths) { q.len = 0; for (let i = 1; i < q.p.length; i++) q.len += Math.hypot(q.p[i][0] - q.p[i - 1][0], q.p[i][1] - q.p[i - 1][1]) }
const logoGrad = (cx, sc) => lg(cx - 180 * sc, 0, cx + 180 * sc, 0, [[0, '#3F8FD6'], [.5, '#34B8A0'], [1, '#5CE0B5']]);

/* prog: 0..1 draw-on; cur: {a,dx,dy,s} cursor state (a=0 hides it) */
function drawLogo(cx, cy, sc, prog, cur) {
  ctx.save(); ctx.translate(cx, cy); ctx.scale(sc, sc); ctx.translate(-LOGO.cx, -LOGO.cy);
  ctx.lineJoin = 'miter'; ctx.lineCap = 'butt'; ctx.miterLimit = 4;
  const g = lg(526, 0, 882, 0, [[0, '#3F8FD6'], [.55, '#34B8A0'], [1, '#5CE0B5']]);
  ctx.strokeStyle = g;
  LOGO.paths.forEach((q, i) => {
    const l = clamp((prog - i * .085) / .32); if (l <= 0) return;
    ctx.lineWidth = q.lw; ctx.setLineDash([q.len + 2, q.len + 2]); ctx.lineDashOffset = (q.len + 2) * (1 - eio(l));
    ctx.beginPath(); q.p.forEach(([x, y], k) => k ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke();
  });
  ctx.setLineDash([]);
  if (cur && cur.a > 0) {
    ctx.save(); ctx.globalAlpha *= cur.a;
    ctx.translate(724 + cur.dx, 203 + cur.dy); ctx.scale(cur.s, cur.s); ctx.translate(-724, -203);
    ctx.fillStyle = lg(724, 203, 762, 242, [[0, '#3FB8C8'], [1, '#34D3A0']]);
    ctx.beginPath(); LOGO.cursor.forEach(([x, y], k) => k ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath(); ctx.fill();
    ctx.restore();
  }
  ctx.restore();
}
/* the cursor on its own (for the 'click' gag): tip position in canvas space */
function logoCursorTip(cx, cy, sc) { return [cx + (724 - LOGO.cx) * sc, cy + (203 - LOGO.cy) * sc] }
function ripple(x, y, t, t0, d = .6, R = 110) {
  const u = (t - t0) / d; if (u <= 0 || u >= 1) return;
  ctx.save(); ctx.strokeStyle = `rgba(92,224,181,${(1 - u) * .85})`; ctx.lineWidth = 6 * (1 - u) + 1; circ(x, y, R * eo3(u)); ctx.stroke(); ctx.restore();
}
/* Freds (white) + Desk (teal) wordmark; pr 0..1 staggered letter entrance */
function wordmark(cx, y, size, pr = 1, alpha = 1) {
  const f = FM(800, size), w1 = measure('Freds', f), w2 = measure('Desk', f), x0 = cx - (w1 + w2) / 2;
  let x = x0;
  const s = 'FredsDesk';
  for (let i = 0; i < s.length; i++) {
    const ch = s[i], cw = measure(ch, f), a = clamp(pr * 2.2 - i * .12) * alpha; const e = eo3(a);
    if (e > 0) T(ch, x + cw / 2, y + (1 - e) * 30, { font: f, color: i < 5 ? '#FFFFFF' : C.tealL, alpha: e });
    x += cw;
  }
}

/* ---------- background ---------- */
function drawBackground(t) {
  ctx.fillStyle = lg(0, 0, 0, H, [[0, '#0B2238'], [1, '#07172A']]); ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = rg(540, 780, 0, 540, 780, 980, [[0, `rgba(52,176,138,${.13 + .025 * Math.sin(t * .8)})`], [.55, 'rgba(63,167,214,.05)'], [1, 'rgba(0,0,0,0)']]); ctx.fillRect(0, 0, W, H);
  const sp = 64, off = (t * 9) % sp;
  for (let y = -sp; y < H + sp; y += sp) for (let x = 0; x <= W; x += sp) {
    const yy = y - off, d = Math.hypot(x - 540, yy - 780) / 900;
    ctx.fillStyle = `rgba(150,210,230,${.075 * (1 - clamp(d) * .75)})`; ctx.fillRect(x - 1.5, yy - 1.5, 3, 3);
  }
  for (let i = 0; i < 9; i++) {      // faint drifting token outlines for depth
    const x = H2(i, 1) * W, y = ((H2(i, 2) * H - t * (10 + H2(i, 3) * 14)) % (H + 200) + H + 200) % (H + 200) - 100, w = 70 + H2(i, 4) * 90;
    ctx.strokeStyle = 'rgba(120,190,220,.07)'; ctx.lineWidth = 2; rr(x, y, w, 46, 14); ctx.stroke();
  }
}

/* ---------- chrome: lesson badge, mini logo, progress bar ---------- */
function drawChrome(t, TL) {
  const a = sstep((t - .45) / .4); if (a <= 0) return;
  ctx.save(); ctx.globalAlpha *= a;
  const lesson = String(TL.lesson).padStart(2, '0');
  pill(60, 92, 196, 54, 'rgba(52,176,138,.16)', 'rgba(92,224,181,.55)');
  T('LESSON ' + lesson, 158, 129, { size: 26, ls: 3, color: C.tealL });
  T(TL.season.toUpperCase(), 276, 128, { size: 22, weight: 500, font: FM(500, 22), ls: 3, align: 'left', color: C.mute });
  drawLogo(768, 119, .15, 1, { a: 1, dx: 0, dy: 0, s: 1 });
  T('FredsDesk', 1020, 130, { size: 30, align: 'right', color: '#fff' });
  const bx = 60, bw = 960, by = 176, p = clamp(t / TL.duration);
  rr(bx, by, bw, 7, 4); ctx.fillStyle = 'rgba(255,255,255,.14)'; ctx.fill();
  rr(bx, by, Math.max(7, bw * p), 7, 4); ctx.fillStyle = lg(bx, 0, bx + bw, 0, [[0, C.blue], [1, C.tealL]]); ctx.fill();
  ctx.fillStyle = rg(bx + bw * p, by + 3, 0, bx + bw * p, by + 3, 22, [[0, 'rgba(92,224,181,.9)'], [1, 'rgba(92,224,181,0)']]); circ(bx + bw * p, by + 3, 22); ctx.fill();
  ctx.restore();
}

/* ---------- captions: 3-4 word chunks, current word highlighted ---------- */
function buildCaptions(TL) {
  const chunks = [];
  for (const S of TL.scenes) {
    if (S.type === 'hook') continue;
    let cur = [];
    const flush = () => { if (cur.length) { chunks.push({ words: cur, t0: cur[0].t0, t1: cur[cur.length - 1].t1 }); cur = [] } };
    for (const w of S.words) {
      cur.push(w);
      const chars = cur.map(x => x.w).join(' ').length;
      if (/[.,;:!?—]$/.test(w.w) || cur.length >= 4 || chars > 26) flush();
    }
    flush();
  }
  chunks.forEach((c, i) => { const nx = chunks[i + 1]; c.show0 = c.t0 - .05; c.show1 = Math.min(c.t1 + .3, nx ? nx.t0 - .02 : 1e9); if (c.show1 < c.t1) c.show1 = c.t1 });
  return chunks;
}
function drawCaptions(t, chunks) {
  const c = chunks.find(c => t >= c.show0 && t < c.show1); if (!c) return;
  const f = FM(800, 74), maxW = 920;
  const words = c.words.map(w => w.w);
  const lines = wrap(words.join(' '), maxW, f); const lh = 92; const y0 = 1400 - (lines.length - 1) * lh / 2;
  const pop = eback((t - c.show0) / .14);
  ctx.save(); ctx.translate(540, y0); ctx.scale(lerp(.9, 1, pop), lerp(.9, 1, pop)); ctx.translate(-540, -y0);
  let wi = 0;
  lines.forEach((ln, li) => {
    const lw = measure(ln, f) + measure(' ', f) * .35 * (ln.split(' ').length - 1); let x = 540 - lw / 2; const y = y0 + li * lh;
    for (const w of ln.split(' ')) {
      const word = c.words[wi++], ww = measure(w, f), sp = measure(' ', f) * 1.35;
      const act = t >= word.t0 && t < word.t1 + .02, done = t >= word.t1 + .02;
      const sc = act ? 1 + .06 * Math.sin(clamp((t - word.t0) / Math.max(.08, word.t1 - word.t0)) * Math.PI) : 1;
      ctx.save(); ctx.translate(x + ww / 2, y - 26); ctx.scale(sc, sc);
      T(w, 0, 26, { font: f, color: act ? C.tealL : (done ? '#FFFFFF' : 'rgba(255,255,255,.5)'), stroke: 15, align: 'center' });
      ctx.restore(); x += ww + sp;
    }
  });
  ctx.restore();
}
