/* video-kit scene worlds. Signature: SCENES[type] = (t, lt, sc, e) with global ctx x.
   t = global time, lt = time since the scene's start (may be <0 or > duration during transitions),
   sc = timeline scene {start,end,keys,act,bright,params}, e = env colors {bg,ink,accent,P,soft,dim,bright}.
   Every world reacts to keywords (keyInfo) and ends stronger than it began. Colors only from e/S. */
'use strict';
const HERO = [CX, HY];

/* fake-3D diamond: 8-sided girdle + table, rotation phi, front faces only, shaded by cos */
function diamond(cx, cy, r, phi, { tint = '#ffffff', bright = 1, glow = 0, cracks = 0, crackCol = '#ffc94d' } = {}) {
  if (r <= 1) return;
  if (glow) glowDot(cx, cy, r * 2.4, tint, .35 * glow);
  const n = 8, tilt = .24, top = cy - r * .55, gird = cy - r * .1, tip = cy + r * 1.05, tw = .55;
  const faces = [];
  for (let k = 0; k < n; k++) { const a0 = phi + k / n * TAU, a1 = phi + (k + 1) / n * TAU;
    const g0 = [cx + Math.cos(a0) * r, gird + Math.sin(a0) * r * tilt], g1 = [cx + Math.cos(a1) * r, gird + Math.sin(a1) * r * tilt];
    const t0 = [cx + Math.cos(a0) * r * tw, top + Math.sin(a0) * r * tw * tilt], t1 = [cx + Math.cos(a1) * r * tw, top + Math.sin(a1) * r * tw * tilt];
    const am = (a0 + a1) / 2; if (Math.sin(am) > -0.05) {
      const sh = .55 + .45 * Math.cos(am + .7);
      faces.push({ z: Math.sin(am), pts: [g0, g1, [cx, tip]], c: mixc('#0b0b10', tint, clamp(sh * bright * .9)) });
      faces.push({ z: Math.sin(am) + .01, pts: [t0, t1, g1, g0], c: mixc('#0b0b10', tint, clamp((sh * .8 + .35) * bright)) }); } }
  faces.sort((a, b) => a.z - b.z).forEach(f => poly(f.pts, f.c, rgba('#ffffff', .25), 1.5));
  const tb = []; for (let k = 0; k < n; k++) { const a = phi + k / n * TAU; tb.push([cx + Math.cos(a) * r * tw, top + Math.sin(a) * r * tw * tilt]); }
  poly(tb, mixc(tint, '#ffffff', .55 * bright));
  if (cracks > 0) { x.strokeStyle = crackCol; x.lineWidth = 4; x.globalAlpha = clamp(cracks);
    for (let k = 0; k < 5; k++) { x.beginPath(); let px = cx + Rs('ck', k) * r * .4, py = cy + Rs('cky', k) * r * .3; x.moveTo(px, py);
      for (let s = 0; s < 4; s++) { px += Rs('cs', k, s) * r * .3; py += Rs('ct', k, s) * r * .25; x.lineTo(px, py); } x.stroke(); }
    x.globalAlpha = 1; }
  const gl = Math.pow(Math.max(0, Math.sin(2.3 * phi)), 12); if (gl > .05) star4(cx + r * .3, top, r * .5 * gl, '#ffffff');
}
function star4(cx, cy, r, col) { x.fillStyle = col; x.beginPath(); for (let k = 0; k < 8; k++) { const a = k / 8 * TAU, rr = k % 2 ? r * .12 : r; x.lineTo(cx + Math.cos(a) * rr, cy + Math.sin(a) * rr); } x.closePath(); x.fill(); }
function shards(cx, cy, d, n, col, id, spread = 900) { // shatter pieces flying out (d = time since break)
  if (d < 0 || d > 1.6) return; for (let k = 0; k < n; k++) { const a = R(id, k) * TAU, v = (300 + R(id, k, 'v') * spread), g = 900;
    const px = cx + Math.cos(a) * v * d, py = cy + Math.sin(a) * v * d * .8 + g * d * d * .5, s = 10 + R(id, k, 's') * 26, rot = d * (R(id, k, 'r') * 12 - 6);
    x.save(); x.translate(px, py); x.rotate(rot); x.globalAlpha = clamp(1.4 - d); poly([[-s, -s * .6], [s, -s * .2], [-s * .2, s]], col); x.restore(); } x.globalAlpha = 1; }
function sparks(cx, cy, d, n, col, id, speed = 1400) { if (d < 0 || d > .9) return; x.strokeStyle = col; x.lineCap = 'round';
  for (let k = 0; k < n; k++) { const a = R(id, k) * TAU, v = speed * (.4 + R(id, k, 'v') * .6), r0 = v * easeOutQuart(d / .9) * .55, l = 40 * (1 - d);
    x.lineWidth = 5 * (1 - d); x.globalAlpha = 1 - d; x.beginPath(); x.moveTo(cx + Math.cos(a) * r0, cy + Math.sin(a) * r0); x.lineTo(cx + Math.cos(a) * (r0 + l), cy + Math.sin(a) * (r0 + l)); x.stroke(); } x.globalAlpha = 1; }
function shockwave(cx, cy, d, col, maxR = 1300, w = 26) { if (d < 0 || d > 1.2) return; const r = easeOutExpo(d / 1.2) * maxR; ring(cx, cy, r, w * (1 - d / 1.2) + 1, col, 1 - d / 1.2); }
function rays(cx, cy, n, r0, r1, rot, col, a) { x.save(); x.globalAlpha = a; x.fillStyle = col; for (let k = 0; k < n; k++) { const a0 = rot + k / n * TAU, w = TAU / n * .28;
  x.beginPath(); x.moveTo(cx + Math.cos(a0 - w) * r0, cy + Math.sin(a0 - w) * r0); x.lineTo(cx + Math.cos(a0) * r1, cy + Math.sin(a0) * r1); x.lineTo(cx + Math.cos(a0 + w) * r0, cy + Math.sin(a0 + w) * r0); x.fill(); } x.restore(); }
const lastKey = sc => sc.keys.length ? sc.keys[sc.keys.length - 1] : { s: sc.start + (sc.end - sc.start) * .5, str: 1 };

/* ---------------------------------------------------------------- STORM (problem) */
SCENES.storm = (t, lt, sc, e) => {
  bgFill(e); const K = keyInfo(sc, t);
  // lightning flicker before each key: 3 flickers 70 ms apart then strike
  let lit = 0; for (const k of sc.keys) { const d = t - k.s; [-.21, -.14, -.07].forEach(o => lit = Math.max(lit, .35 * decay(d - o, 40) * (d - o > 0))); lit = Math.max(lit, decay(d, 7) * (d >= 0)); }
  for (let k = 0; k < 7; k++) { const cx = (R('cl', k) * 1.4 - .2) * W + Math.sin(t * .2 + k) * 60, cy = 120 + R('cly', k) * 600, r = 380 + R('clr', k) * 360;
    glowDot(cx, cy, r, mixc(e.soft, '#ffffff', lit * .8), .14 + lit * .45); }
  // rain
  x.strokeStyle = rgba(e.ink, .22 + lit * .2); x.lineWidth = 2.5; x.beginPath();
  for (let k = 0; k < 190; k++) { const sp = 1900 + R('rs', k) * 900, px = R('rx', k) * (W + 400) - 200, py = ((R('ry', k) * (H + 400) + t * sp) % (H + 400)) - 200;
    x.moveTo(px, py); x.lineTo(px - 18, py + 70); } x.stroke();
  // bolts on keys
  sc.keys.forEach((k, j) => { const d = t - k.s; if (d < 0 || d > .35) return; const a = 1 - d / .35; let px = CX + Rs('bx', j) * 200, py = -20;
    const pts = [[px, py]]; for (let s = 1; s <= 16; s++) { px += Rs('b', j, s) * 70; py = s / 16 * (HY + 120); pts.push([px, py]); }
    x.lineJoin = 'round'; [[46, rgba(S.accent, .25 * a)], [16, rgba('#ffffff', .6 * a)], [6, rgba('#ffffff', a)]].forEach(([w, c]) => { x.strokeStyle = c; x.lineWidth = w;
      x.beginPath(); pts.forEach((p, i) => i ? x.lineTo(p[0], p[1]) : x.moveTo(p[0], p[1])); x.stroke(); }); });
  // falling heavy shapes that land on each key and shatter
  const floor = 1160;
  sc.keys.forEach((k, j) => { const d = t - k.s, kind = ['square', 'triangle', 'diamond'][j % 3], cx = CX + (j % 2 ? 1 : -1) * (120 + 60 * j), r = 120 - 15 * j;
    if (d < 0) { const fall = clamp((d + .6) / .6), py = lerp(-300, floor - r, easeInQuad(fall));
      for (let g = 3; g >= 0; g--) { x.globalAlpha = g ? .12 : 1; poly(shapePts(kind, cx, py - g * 50 * fall, r, d * 2), g ? e.soft : e.ink); } x.globalAlpha = 1; }
    else { shards(cx, floor - r, d, 22, e.ink, 'sh' + sc.i + j); sparks(cx, floor - r * .3, d, 18, S.accent, 'sp' + sc.i + j); } });
  // floor waves
  x.strokeStyle = rgba(e.ink, .35); x.lineWidth = 3;
  for (let row = 0; row < 6; row++) { const y0 = floor + 30 + row * 46; x.beginPath();
    for (let px = 0; px <= W; px += 20) { let dy = 0; sc.keys.forEach((k, j) => { const d = t - k.s; if (d > 0) { const dist = Math.abs(px - (CX + (j % 2 ? 1 : -1) * (120 + 60 * j))); dy += 70 * Math.exp(-2 * d) * Math.sin(dist * .02 - 15 * d) * Math.exp(-dist / 600) * (1 - row * .12); } });
      px ? x.lineTo(px, y0 + dy) : x.moveTo(px, y0 + dy); } x.stroke(); }
  // small hero ember that refuses to die
  const hr = 34 + 10 * Math.sin(t * 5) + 20 * K.pulse; glowDot(CX, floor - 40, hr * 4, S.accent, .5); circle(CX, floor - 40, hr, S.accent);
};

/* ---------------------------------------------------------------- PRESSURE (build) */
SCENES.pressure = (t, lt, sc, e) => {
  bgFill(e); const K = keyInfo(sc, t), n = Math.max(1, K.n), dur = sc.end - sc.start;
  const squeeze = clamp((K.step + smooth(lt / dur) * .6) / (n + .6)), gap = lerp(820, 300, squeeze);
  const rum = (4 + 16 * squeeze) * (S.camera.shake || 1), jx = Math.sin(t * 61) * rum, jy = Math.cos(t * 53) * rum * .6;
  // contour lines compressed toward the center
  x.strokeStyle = rgba(e.ink, .12); x.lineWidth = 2;
  for (let k = 0; k < 16; k++) { const yy = HY - 700 + k * 90; x.beginPath(); for (let px = 0; px <= W; px += 24) { const c = Math.abs(px - CX) / (gap / 2);
    const py = yy + Math.sin(px * .01 + k + t) * 12 * (1 + squeeze * 3) / (1 + c); px ? x.lineTo(px, py) : x.moveTo(px, py); } x.stroke(); }
  // walls
  [-1, 1].forEach(side => { const inner = CX + side * gap / 2 + jx, outer = side < 0 ? -100 : W + 100;
    const x0 = Math.min(inner, outer), x1 = Math.max(inner, outer);
    x.fillStyle = e.dim; x.fillRect(x0, -100, x1 - x0, H + 200);
    x.strokeStyle = rgba(e.ink, .14); x.lineWidth = 2; x.beginPath();
    for (let gy = -100; gy < H + 100; gy += 90) { x.moveTo(x0, gy); x.lineTo(x1, gy); }
    for (let gx = inner; side < 0 ? gx > -100 : gx < W + 100; gx += side * 90) { x.moveTo(gx, -100); x.lineTo(gx, H + 100); } x.stroke();
    const hot = x.createLinearGradient(inner, 0, inner - side * 120, 0); hot.addColorStop(0, rgba(S.accent, .3 + .7 * squeeze)); hot.addColorStop(1, rgba(S.accent, 0));
    x.fillStyle = hot; x.fillRect(Math.min(inner, inner - side * 120), -100, 120, H + 200);
    // glowing cracks
    x.strokeStyle = rgba(S.accent, .8 * squeeze); x.lineWidth = 4;
    for (let c = 0; c < K.count * 2; c++) { let px = inner - side * 10, py = 300 + R('cr', side, c) * 1000; x.beginPath(); x.moveTo(px, py);
      for (let s = 0; s < 5; s++) { px -= side * (30 + R('cx', side, c, s) * 50); py += Rs('cy', side, c, s) * 60; x.lineTo(px, py); } x.stroke(); } });
  sc.keys.forEach((k, j) => { const d = t - k.s; sparks(CX - gap / 2 + jx, HY + Rs('spy', j) * 300, d, 14, S.accent, 'pl' + j); sparks(CX + gap / 2 + jx, HY + Rs('spz', j) * 300, d, 14, S.accent, 'pr' + j); });
  // squeezed hero
  const rx = Math.min(200, gap / 2 - 30), ry = 200 * 200 / rx * (1 + .08 * Math.sin(t * 9) * squeeze);
  drawGoo(g => { gell(g, CX + jx * .5, HY + jy, rx, ry); for (let k = 0; k < 5; k++) { const a = t * 1.8 + k / 5 * TAU; gcirc(g, CX + Math.cos(a) * rx * 1.05, HY + Math.sin(a) * ry * 1.05, 34); } },
    g => { const gr = g.createRadialGradient(CX - 60, HY - 80, 10, CX, HY, ry * 1.2); gr.addColorStop(0, '#ffffff'); gr.addColorStop(.6, mixc(e.ink, S.accent, squeeze * .6)); gr.addColorStop(1, S.accent); return gr; }, .4 + squeeze * .5);
};

/* ---------------------------------------------------------------- LIQUID (hero goo -> crystallizes) */
SCENES.liquid = (t, lt, sc, e) => {
  bgFill(e); const K = keyInfo(sc, t), lk = lastKey(sc), dl = t - lk.s, dur = sc.end - sc.start;
  // orbit rings
  for (let k = 0; k < 3; k++) { x.save(); x.translate(CX, HY); x.rotate(.3 + k * .5 + t * .05); x.scale(1, .32); ring(0, 0, 330 + k * 90, 3, e.soft, .6); x.restore();
    const a = t * (.6 + k * .2) + k * 2; circle(CX + Math.cos(a) * (330 + k * 90) * Math.cos(.3 + k * .5), HY + Math.sin(a) * (330 + k * 90) * .32, 8, S.accent); }
  const cryst = sc.keys.length > 1 ? clamp(dl / .5) : 0;
  const R0 = 190 * (1 + .12 * Math.sin(t * 2.2)) * (1 - .25 * K.pulse * (dl < 0 ? 1 : 0)), sq = kick(t - (sc.keys[0] ? sc.keys[0].s : 99), 5, 12);
  if (cryst < 1) {
    drawGoo(g => {
      const rr = R0 * (1 - cryst * .9); gell(g, CX, HY, rr * (1 + .25 * sq), rr * (1 - .25 * sq));
      for (let k = 0; k < 6; k++) { const a = t * 1.3 + k / 6 * TAU + .3 * Math.sin(t + k), rr2 = rr * (1.05 + .25 * Math.sin(t * 2 + k)); gcirc(g, CX + Math.cos(a) * rr2, HY + Math.sin(a) * rr2, rr * .3); }
      sc.keys.forEach((kk, j) => { const d = t - kk.s; if (d < 0 || d > 1.3) return; for (let s = 0; s < 8; s++) { const a = R('dr', j, s) * TAU, dd = (220 + R('dv', j, s) * 260) * Math.sin(Math.PI * clamp(d / 1.3));
        gcirc(g, CX + Math.cos(a) * (rr + dd), HY + Math.sin(a) * (rr + dd), 20 + 18 * R('ds', j, s)); } });
    }, g => { const gr = g.createRadialGradient(CX - 70, HY - 90, 10, CX, HY, R0 * 1.4); gr.addColorStop(0, '#ffffff'); gr.addColorStop(.45, mixc('#ffffff', S.accent, .3)); gr.addColorStop(1, S.accent); return gr; }, .55);
  }
  if (cryst > 0) { const s = easeOutBack(cryst, 2.2); rays(CX, HY, 14, 120, 900 * s, t * .25, S.accent, .22 * cryst);
    diamond(CX, HY, 200 * s, t * 1.2, { tint: mixc('#ffffff', S.accent, .25), glow: cryst, bright: 1.1 }); shockwave(CX, HY, dl, S.accent); sparks(CX, HY, dl, 26, '#ffffff', 'lq' + sc.i); }
};

/* ---------------------------------------------------------------- TUNNEL (ascent) */
SCENES.tunnel = (t, lt, sc, e) => {
  bgFill(e); const K = keyInfo(sc, t);
  const speed = .35 + .5 * K.pulse + .1 * K.count, ph = lt * .35 + K.step * .18;
  x.save(); x.translate(CX, HY);
  for (let k = 0; k < 22; k++) { const z = ((k / 22 + ph * (1 + speed * .2)) % 1), r = 20 + 1450 * Math.pow(z, 2.3), a = clamp(z * 1.6);
    x.globalAlpha = a; x.strokeStyle = k % 4 === 0 ? S.accent : (e.bright ? rgba(e.ink, .35) : e.soft); x.lineWidth = 2 + 10 * z;
    if (k % 3 === 0) { x.save(); x.rotate(z * 2 + t * .3); x.strokeRect(-r, -r, r * 2, r * 2); x.restore(); } else { x.beginPath(); x.arc(0, 0, r, 0, TAU); x.stroke(); } }
  // radial streaks
  x.globalAlpha = .5 + .5 * clamp(K.pulse); x.strokeStyle = e.ink; x.lineWidth = 3; x.beginPath();
  for (let k = 0; k < 70; k++) { const a = R('st', k) * TAU, z = (R('sz', k) + lt * (.8 + speed)) % 1, r0 = 60 + 1400 * z * z, l = 30 + 260 * z * (1 + K.pulse);
    x.moveTo(Math.cos(a) * r0, Math.sin(a) * r0); x.lineTo(Math.cos(a) * (r0 + l), Math.sin(a) * (r0 + l)); } x.stroke();
  // shapes flying past
  for (let k = 0; k < 9; k++) { const z = (R('fz', k) + lt * .55) % 1, a = R('fa', k) * TAU, r = 120 + 1100 * z * z;
    x.globalAlpha = clamp(z * 2); poly(shapePts(['square', 'triangle', 'circle'][k % 3], Math.cos(a) * r, Math.sin(a) * r, 10 + 70 * z, t + k), k % 2 ? S.palette[1 % S.palette.length] : e.ink); }
  x.restore(); x.globalAlpha = 1;
  // hero on a liquid flame trail
  const hy = HY + 260 - 140 * smooth(lt / (sc.end - sc.start)) + 30 * Math.sin(t * 3);
  drawGoo(g => { gcirc(g, CX, hy, 95 + 25 * K.pulse); for (let k = 1; k < 9; k++) gcirc(g, CX + Math.sin(t * 6 + k) * 10 * k, hy + k * 52, 80 - k * 8);
    for (let k = 0; k < 4; k++) { const ph2 = (t * 1.6 + k / 4) % 1; gcirc(g, CX + Math.sin(k * 3 + t * 4) * 30, hy + 480 + ph2 * 400, 30 * (1 - ph2)); } },
    g => { const gr = g.createLinearGradient(0, hy - 100, 0, hy + 600); gr.addColorStop(0, '#ffffff'); gr.addColorStop(.25, S.accent); gr.addColorStop(1, rgba(S.accent, .0)); return gr; }, .6);
};

/* ---------------------------------------------------------------- BURST (finale) */
SCENES.burst = (t, lt, sc, e) => {
  const dur = sc.end - sc.start, bt = sc.keys.length ? sc.keys[0].s : sc.start + dur * .35, d = t - bt;
  const dark = { ...e, bg: S.bg }; x.fillStyle = S.bg[0]; x.fillRect(-60, -60, W + 120, H + 120);
  if (d < 0) { // implosion
    const p = clamp(1 + d / Math.max(.4, bt - sc.start));
    for (let k = 0; k < 6; k++) ring(CX, HY, (1 - ((k / 6 + lt * .9) % 1)) * 900 * (1 - p * .5), 4, S.ink, .5);
    for (let k = 0; k < 90; k++) { const a = R('im', k) * TAU, r = (1 - ((R('ir', k) + lt * 1.2) % 1)) * 1000; circle(CX + Math.cos(a) * r, HY + Math.sin(a) * r, 4, k % 3 ? S.ink : S.accent); }
    const c = 50 + 30 * Math.sin(t * 20) * p; glowDot(CX, HY, c * 4, S.accent, .7); circle(CX, HY, c, '#ffffff');
  }
  if (d >= 0) {
    const r = d * 2600; x.save(); x.beginPath(); x.arc(CX, HY, r, 0, TAU); x.clip();
    const g = x.createLinearGradient(0, 0, 0, H); g.addColorStop(0, S.accent); g.addColorStop(1, mixc(S.accent, S.palette[1] || '#ffffff', .45)); x.fillStyle = g; x.fillRect(0, 0, W, H);
    rays(CX, HY, 16, 140, 1600, t * .3, '#ffffff', .18); rays(CX, HY, 16, 140, 1600, -t * .2 + .1, S.on_accent === '#111111' ? '#ffffff' : '#000000', .06);
    for (let k = 0; k < 4; k++) ring(CX, HY, 260 + k * 120 + 20 * Math.sin(t * 4 + k), 6, '#ffffff', .35);
    for (let k = 0; k < 6; k++) { const a = t * .9 + k / 6 * TAU; poly(shapePts(['circle', 'square', 'triangle'][k % 3], CX + Math.cos(a) * 430, HY + Math.sin(a) * 430 * .55, 34, t * 2 + k), '#ffffff'); }
    for (let k = 0; k < 60; k++) { const a = R('ob', k) * TAU, rr = ((R('or', k) + d * .7) % 1) * 1100 + 200; circle(CX + Math.cos(a) * rr, HY + Math.sin(a) * rr, 3 + 4 * R('os', k), '#ffffff', .8); }
    diamond(CX, HY, 210 * easeOutBack(clamp(d / .45), 2), t * 1.1, { tint: '#ffffff', glow: 1, bright: 1.15 });
    x.restore();
    shockwave(CX, HY, d, '#ffffff', 1500, 30); shockwave(CX, HY, d - .18, S.accent, 1500, 20); sparks(CX, HY, d, 40, '#ffffff', 'bu' + sc.i, 2200);
    sc.keys.slice(1).forEach((k, j) => { shockwave(CX, HY, t - k.s, '#ffffff', 900, 16); });
  }
};

/* ---------------------------------------------------------------- SHAPES (Swiss / geometric) */
SCENES.shapes = (t, lt, sc, e) => {
  bgFill(e); const K = keyInfo(sc, t);
  // background grid of small marks
  x.fillStyle = e.soft; for (let j = 0; j < 22; j++) for (let i = 0; i < 12; i++) { const px = 45 + i * 90, py = 45 + j * 90, s = 3 + 3 * Math.sin(t * 2 + i * .5 + j * .3) * .5; x.fillRect(px - s, py - s, s * 2, s * 2); }
  // color blocks that swing in 90° with expo easing
  const blocks = [[0, 0, 540, 420], [540, 1500, 540, 420], [0, 1500, 280, 420]];
  blocks.forEach((b, j) => { const p = easeOutExpo((lt - .1 - j * .12) / .6); x.save(); x.translate(b[0] + (j === 1 ? b[2] : 0), b[1]); x.rotate((1 - p) * (j === 1 ? 1 : -1) * Math.PI / 2);
    x.fillStyle = j === 0 ? S.palette[2 % S.palette.length] : j === 1 ? S.accent : e.dim; x.globalAlpha = j === 0 ? .18 : .9; x.fillRect(j === 1 ? -b[2] : 0, 0, b[2], b[3]); x.restore(); }); x.globalAlpha = 1;
  // morphing hero shape per keyword
  const kinds = ['circle', 'square', 'triangle', 'diamond', 'circle'];
  const i0 = K.count, d = K.since, mp = K.count ? easeInOutCubic(d / .35) : 1;
  const A = shapePts(kinds[Math.max(0, i0 - 1) % kinds.length], CX, HY, 230, 0), B = shapePts(kinds[i0 % kinds.length], CX, HY, 230, 0);
  const pts = K.count ? morph(A, B, mp) : A, sc2 = K.count ? spring(d, { from: .82, to: 1 }) : spring(lt, { from: 0, to: 1 });
  x.save(); x.translate(CX, HY); x.scale(sc2, sc2); x.rotate(.08 * Math.sin(t)); x.translate(-CX, -HY);
  poly(pts.map(p => [p[0] + 22, p[1] + 26]), rgba('#000000', e.bright ? .15 : .35)); poly(pts, S.accent); x.restore();
  ring(CX, HY, 330 + 20 * K.pulse, 4, e.ink, .8);
  for (let k = 0; k < 3; k++) { const a = t * (1 + k * .3) + k * 2.1; circle(CX + Math.cos(a) * 330, HY + Math.sin(a) * 330, 14 + 6 * k, k === 1 ? e.ink : S.palette[1 % S.palette.length]); }
  sc.keys.forEach((k, j) => shockwave(CX, HY, t - k.s, e.ink, 700, 10));
};

/* ---------------------------------------------------------------- PARTICLES (converge / explode) */
SCENES.particles = (t, lt, sc, e) => {
  bgFill(e); const K = keyInfo(sc, t), N = 260, dur = sc.end - sc.start;
  const form = smooth(lt / Math.min(1.4, dur * .5)) * (1 - .7 * decay(K.since, 3) * (K.count ? 1 : 0)), lastD = K.count ? K.since : -1;
  const targetKinds = ['circle', 'diamond', 'square', 'triangle']; const T = shapePts(targetKinds[K.count % 4], CX, HY, 300, t * .2, N);
  for (let k = 0; k < N; k++) { const fx0 = R('px', k) * W, fy0 = R('py', k) * H;
    const nx = fx0 + fbm(fx0 * .002, t * .15, 3) * 300, ny = fy0 + fbm(fy0 * .002 + 9, t * .15, 4) * 300;
    let px = lerp(nx, T[k][0], form), py = lerp(ny, T[k][1], form);
    if (lastD >= 0 && lastD < 1.2) { const a = Math.atan2(py - HY, px - CX), b = 400 * Math.sin(Math.PI * clamp(lastD / 1.2)) * (.4 + R('pb', k)); px += Math.cos(a) * b; py += Math.sin(a) * b; }
    const s = 5 + 7 * R('ps', k); circle(px, py, s, k % 7 === 0 ? S.accent : e.ink, .5 + .5 * form); }
  glowDot(CX, HY, 260 + 100 * K.pulse, S.accent, .25 + .3 * form);
  sc.keys.forEach(k => shockwave(CX, HY, t - k.s, S.accent, 900, 14));
};

/* ---------------------------------------------------------------- GRID (synthwave) */
SCENES.grid = (t, lt, sc, e) => {
  bgFill(e); const K = keyInfo(sc, t), hz = 1050;
  for (let k = 0; k < 80; k++) circle(R('sx', k) * W, R('sy', k) * hz * .9, 1.5 + 2 * R('ss', k), e.ink, .3 + .5 * Math.abs(Math.sin(t * 2 + k)));
  // banded sun
  const sr = 330 * (1 + .06 * K.pulse), sy = hz - 120 - 40 * smooth(lt / (sc.end - sc.start));
  x.save(); const g = x.createLinearGradient(0, sy - sr, 0, sy + sr); g.addColorStop(0, S.palette[2 % S.palette.length]); g.addColorStop(1, S.accent);
  glowDot(CX, sy, sr * 1.8, S.accent, .35); x.fillStyle = g; x.beginPath(); x.arc(CX, sy, sr, 0, TAU); x.fill();
  x.globalCompositeOperation = 'destination-out'; for (let b = 0; b < 7; b++) { const yy = sy + sr * (.05 + b * .14), h = 6 + b * 5 + 6 * Math.sin(t * 2 + b); x.fillRect(CX - sr, yy, sr * 2, h); }
  x.restore();
  // mountains
  x.fillStyle = mixc(e.bg[1], '#000000', .3); x.beginPath(); x.moveTo(0, hz);
  for (let px = 0; px <= W; px += 30) x.lineTo(px, hz - 60 - 120 * Math.abs(fbm(px * .004, 3, 8, 3)) - (Math.abs(px - CX) < 260 ? 0 : 60)); x.lineTo(W, hz); x.fill();
  // floor + perspective grid
  const fg = x.createLinearGradient(0, hz, 0, H); fg.addColorStop(0, mixc(e.bg[1], '#000000', .2)); fg.addColorStop(1, e.bg[0]); x.fillStyle = fg; x.fillRect(0, hz, W, H - hz);
  const spd = 1.2 + 1.6 * K.pulse, f = 500; x.strokeStyle = S.palette[1 % S.palette.length]; x.lineWidth = 3; x.globalAlpha = .9;
  x.beginPath(); for (let k = -14; k <= 14; k++) { x.moveTo(CX + k * 40, hz); x.lineTo(CX + k * 520, H); }
  for (let k = 0; k < 18; k++) { const z = ((k - (lt * spd) % 1) + 18) % 18 + .4, y = hz + f / z; if (y > H) continue; x.moveTo(0, y); x.lineTo(W, y); } x.stroke(); x.globalAlpha = 1;
  glowDot(CX, hz, 700, S.palette[1 % S.palette.length], .18 + .2 * K.pulse);
  sc.keys.forEach(k => { const d = t - k.s; if (d > 0 && d < .6) { x.globalAlpha = 1 - d / .6; x.fillStyle = S.accent; x.fillRect(0, hz - 3, W, 6); x.globalAlpha = 1; } });
};

/* ---------------------------------------------------------------- AURORA (calm) */
SCENES.aurora = (t, lt, sc, e) => {
  bgFill(e); const K = keyInfo(sc, t);
  x.globalCompositeOperation = e.bright ? 'multiply' : 'screen';
  S.palette.slice(0, 5).forEach((c, k) => { const px = CX + Math.sin(t * .23 * (1 + k * .17) + k * 1.7) * 380, py = HY + Math.cos(t * .19 * (1 + k * .13) + k) * 520;
    glowDot(px, py, 620 + 120 * Math.sin(t * .5 + k) + 80 * K.pulse, c, e.bright ? .55 : .5); });
  x.globalCompositeOperation = 'source-over';
  for (let k = 0; k < 70; k++) circle(R('as', k) * W, (R('ay', k) * H - lt * 20 * (.5 + R('av', k))) % H + (lt * 20 > R('ay', k) * H ? H : 0), 1.5 + 2 * R('az', k), e.ink, .25 + .35 * Math.sin(t * 1.5 + k) ** 2);
  const br = 1 + .05 * Math.sin(t * 1.3) + .08 * K.pulse; ring(CX, HY, 250 * br, 3, e.ink, .55); ring(CX, HY, 330 * br, 1.5, e.ink, .3);
  sc.keys.forEach(k => { const d = t - k.s; if (d > 0 && d < 2) ring(CX, HY, 250 + d * 380, 3, e.ink, .6 * (1 - d / 2)); });
};

/* ---------------------------------------------------------------- PAPER (cut-out layers) */
SCENES.paper = (t, lt, sc, e) => {
  bgFill(e); const K = keyInfo(sc, t), P = S.palette;
  const sun = spring(lt - .1, { from: 0, to: 1 }); circle(CX + 180, 520 - 60 * K.step * .2, 170 * sun, P[1 % P.length]);
  for (let L = 0; L < 5; L++) { const enter = spring(lt - .08 * L - (L >= 3 ? (sc.keys[L - 3] ? sc.keys[L - 3].s - sc.start : 99) : 0), { from: 0, to: 1, zeta: .45 });
    const base = 900 + L * 190 + (1 - enter) * 900, amp = 140 - L * 18, col = mixc(P[L % P.length], e.bg[0], .15 * (4 - L) / 4);
    const pts = [[-40, H + 40]]; for (let px = -40; px <= W + 40; px += 36) { const n = fbm(px * .003 + L * 3, L, 21 + L, 3) + Math.sin(px * .01 + L) * .2;
      pts.push([px + Rs('pj', L, px) * 4, base - n * amp + Math.sin(t * .8 + L) * 6 + Rs('pk', L, px) * 3]); } pts.push([W + 40, H + 40]);
    x.save(); x.translate(10, 14); poly(pts, rgba('#000000', .22)); x.restore(); poly(pts, col); }
  sc.keys.forEach((k, j) => { const d = t - k.s; if (d < 0) return; const s = spring(d, { from: 0, to: 1, zeta: .4 }); const px = 220 + j * 320, py = 640 + 40 * Math.sin(t * 2 + j);
    x.save(); x.translate(px + 8, py + 10); x.scale(s, s); poly(shapePts(['circle', 'diamond', 'triangle'][j % 3], 0, 0, 70, 0), rgba('#000000', .2)); x.restore();
    x.save(); x.translate(px, py); x.scale(s, s); x.rotate(.15 * Math.sin(t * 2 + j)); poly(shapePts(['circle', 'diamond', 'triangle'][j % 3], 0, 0, 70, 0), j % 2 ? e.ink : S.accent); x.restore(); });
};

/* ---------------------------------------------------------------- BLUEPRINT (draw-on explainer) */
SCENES.blueprint = (t, lt, sc, e) => {
  bgFill(e); const K = keyInfo(sc, t);
  x.strokeStyle = rgba(e.ink, .08); x.lineWidth = 1; x.beginPath(); for (let i = 0; i <= W; i += 45) { x.moveTo(i, 0); x.lineTo(i, H); } for (let j = 0; j <= H; j += 45) { x.moveTo(0, j); x.lineTo(W, j); } x.stroke();
  x.strokeStyle = rgba(e.ink, .18); x.beginPath(); for (let i = 0; i <= W; i += 225) { x.moveTo(i, 0); x.lineTo(i, H); } for (let j = 0; j <= H; j += 225) { x.moveTo(0, j); x.lineTo(W, j); } x.stroke();
  const draw = (pts, p, col, lw = 6) => { const L = pts.reduce((a, q, i) => i ? a + Math.hypot(q[0] - pts[i - 1][0], q[1] - pts[i - 1][1]) : 0, 0);
    x.setLineDash([L, L]); x.lineDashOffset = L * (1 - easeOutQuart(p)); x.strokeStyle = col; x.lineWidth = lw; x.lineJoin = 'round';
    x.beginPath(); pts.forEach((q, i) => i ? x.lineTo(q[0], q[1]) : x.moveTo(q[0], q[1])); x.stroke(); x.setLineDash([]); };
  const main = shapePts('circle', CX, HY, 260, 0, 120); main.push(main[0]);
  draw(main, lt / .9, e.ink);
  const sq = shapePts('square', CX, HY, 160, Math.PI / 4 * smooth(lt), 96); sq.push(sq[0]); draw(sq, (lt - .3) / .8, e.ink, 4);
  sc.keys.forEach((k, j) => { const d = t - k.s; if (d < -.05) return; const a = -2.3 + j * 1.6, ex = CX + Math.cos(a) * 260, ey = HY + Math.sin(a) * 260;
    const lx = ex + Math.cos(a) * 160, ly = ey + Math.sin(a) * 160, tx = lx + (Math.cos(a) > 0 ? 120 : -120);
    draw([[ex, ey], [lx, ly], [tx, ly]], d / .4, S.accent, 5); circle(ex, ey, 12 * spring(d), S.accent);
    if (d > .25) { x.font = `${S.fonts.text_weight} 40px "${S.fonts.text}"`; x.fillStyle = e.ink; x.textBaseline = 'bottom'; x.textAlign = Math.cos(a) > 0 ? 'right' : 'left';
      x.globalAlpha = clamp((d - .25) / .2); x.fillText(caseT(k.w.replace(/[.,!?;:]+$/, '')), tx, ly - 10); x.globalAlpha = 1; } });
  const lk = lastKey(sc), fd = t - lk.s; if (sc.keys.length && fd > .2) { x.save(); x.beginPath(); x.arc(CX, HY, 260, 0, TAU); x.clip(); x.globalAlpha = .9; x.fillStyle = S.accent;
    x.fillRect(CX - 300, HY + 300 - 600 * easeOutQuart((fd - .2) / .6), 600, 600); x.restore(); x.globalAlpha = 1; poly(sq.slice(0, -1), null, e.ink, 4); }
};

/* ---------------------------------------------------------------- BARS (stat / growth) */
SCENES.bars = (t, lt, sc, e) => {
  bgFill(e); const K = keyInfo(sc, t), vals = sc.params.values || [.25, .4, .55, .75, 1], n = vals.length;
  const base = 1160, left = 140, bw = (W - 280) / n;
  x.strokeStyle = rgba(e.ink, .3); x.lineWidth = 3; x.beginPath(); x.moveTo(left - 20, base); x.lineTo(W - left + 20, base); x.stroke();
  const shown = Math.min(n, 1 + K.count + Math.floor(smooth(lt / (sc.end - sc.start)) * 1.5));
  vals.forEach((v, i) => { const st = sc.start + .15 + i * .18 + (i >= 2 && sc.keys[i - 2] ? 0 : 0), p = i < shown ? spring(t - st, { from: 0, to: 1, zeta: .55 }) : 0;
    const h = v * 700 * p, px = left + i * bw + bw * .15, w = bw * .7, last = i === n - 1;
    x.fillStyle = last ? S.accent : e.soft; x.fillRect(px, base - h, w, h); if (last && p > .5) { glowDot(px + w / 2, base - h, 160, S.accent, .4); } });
  const target = sc.params.number ?? 100, num = Math.round(target * smooth((t - sc.start) / Math.max(.5, (lastKey(sc).s - sc.start))));
  x.font = `${S.fonts.display_weight} 220px "${S.fonts.display}"`; x.textAlign = 'center'; x.textBaseline = 'alphabetic';
  const s = 1 + .12 * K.pulse; x.save(); x.translate(CX, 380); x.scale(s, s); x.fillStyle = e.ink; x.fillText((sc.params.prefix || '') + num + (sc.params.suffix ?? '%'), 0, 0); x.restore();
};

/* ---------------------------------------------------------------- MATRIX (terminal) */
SCENES.matrix = (t, lt, sc, e) => {
  bgFill(e); const K = keyInfo(sc, t), cols = 30, cw = W / cols, ch = 44, glyphs = '01<>/{}[]=+*#$%&ABCDEFabcdef0123456789';
  x.font = `700 36px "${S.fonts.text}"`; x.textAlign = 'center'; x.textBaseline = 'middle';
  for (let c = 0; c < cols; c++) { const sp = 6 + R('ms', c) * 10, head = ((R('mh', c) * 50 + lt * sp) % 50), burst = sc.keys.some((k, j) => (j * 7 + 3) % cols === c && t >= k.s && t - k.s < .8);
    for (let r = 0; r < 45; r++) { const d = head - r; if (d < 0 || d > 16) continue; const g = glyphs[Math.floor(hash(c, r, Math.floor(t * 8 + R('mg', c, r) * 8)) * glyphs.length)];
      x.globalAlpha = d < 1 ? 1 : (1 - d / 16) * .8; x.fillStyle = d < 1 || burst ? '#ffffff' : (c % 5 === 0 ? S.accent : e.soft); x.fillText(g, c * cw + cw / 2, r * ch); } }
  x.globalAlpha = 1;
  const s = spring(lt, { from: .6, to: 1 }) * (1 + .06 * K.pulse), bw = 520 * s, bh = 360 * s;
  x.fillStyle = rgba(e.bg[0], .85); x.fillRect(CX - bw / 2, HY - bh / 2, bw, bh); x.strokeStyle = S.accent; x.lineWidth = 6;
  const c = 60; [[-1, -1], [1, -1], [1, 1], [-1, 1]].forEach(([sx, sy]) => { x.beginPath(); x.moveTo(CX + sx * bw / 2, HY + sy * (bh / 2 - c)); x.lineTo(CX + sx * bw / 2, HY + sy * bh / 2); x.lineTo(CX + sx * (bw / 2 - c), HY + sy * bh / 2); x.stroke(); });
  x.font = `800 120px "${S.fonts.text}"`; x.fillStyle = S.accent; x.fillText(Math.floor(t * 2.5) % 2 ? '>_' : '> ', CX, HY);
};

/* ---------------------------------------------------------------- TYPE (giant background word) */
SCENES.type = (t, lt, sc, e) => {
  bgFill(e); const K = keyInfo(sc, t); const k = sc.keys[Math.max(0, K.count - 1)]; const word = caseT((k ? k.w : (sc.params.word || '')).replace(/[.,!?;:]+$/, ''));
  if (!word) return; const fam = S.fonts.display, wt = S.fonts.display_weight; x.font = `${wt} 600px "${fam}"`; const w = x.measureText(word).width, sz = 600 * Math.min(1, 980 / w);
  x.font = `${wt} ${sz}px "${fam}"`; x.textAlign = 'center'; x.textBaseline = 'middle';
  x.save(); x.translate(CX, HY); x.scale(1 + lt * .03, 1 + lt * .03);
  x.strokeStyle = e.soft; x.lineWidth = 4; for (let r = -2; r <= 2; r++) x.strokeText(word, 0, r * sz * .9 - (lt * 60) % (sz * .9));
  x.fillStyle = S.accent; x.globalAlpha = .9 * spring(K.since, { from: 0, to: 1 }); x.fillText(word, 0, 0); x.restore(); x.globalAlpha = 1;
};
