/* FredsDesk custom worlds for video-kit (neural, fleet, chat, tokens, haunt).
   Same contract as scenes.js: SCENES[type] = (t, lt, sc, e). Deterministic: only R()/Rs()/hash for randomness. */
'use strict';

/* ---- neural: layered network, pulses travel along edges, nodes flare on keywords. params.layers */
SCENES.neural = (t, lt, sc, e) => {
  bgFill(e); const K = keyInfo(sc, t), layers = sc.params.layers || [3, 5, 5, 3], gx = 760 / (layers.length - 1), nodes = [];
  layers.forEach((n, li) => { for (let i = 0; i < n; i++) nodes.push({ li, i, px: CX - 380 + li * gx + Math.sin(t * .8 + li + i) * 8, py: HY - (n - 1) * 70 + i * 140 + Math.cos(t * .7 + i * 2) * 8 }); });
  const byL = layers.map((_, li) => nodes.filter(n => n.li === li)); x.lineWidth = 2;
  for (let li = 0; li < layers.length - 1; li++) for (const a of byL[li]) for (const b of byL[li + 1]) {
    x.strokeStyle = rgba(e.ink, .10 + .08 * Math.min(1, K.pulse)); x.beginPath(); x.moveTo(a.px, a.py); x.lineTo(b.px, b.py); x.stroke();
    if (R('np', a.i, b.i, li) > .45) { const p = (lt * .9 + R('npp', a.i, b.i, li)) % 1; circle(lerp(a.px, b.px, p), lerp(a.py, b.py, p), 6, S.accent, .85); } }
  nodes.forEach(n => { const fire = clamp(K.pulse * (.55 + .45 * Math.sin(n.li * 1.7 + n.i * 2.3))); glowDot(n.px, n.py, 60 + fire * 80, S.accent, .16 + fire * .5);
    circle(n.px, n.py, 20 + fire * 10, mixc(e.soft, S.accent, fire)); ring(n.px, n.py, 25 + fire * 10, 3, e.ink, .55); });
  sc.keys.forEach(k => shockwave(CX, HY, t - k.s, S.accent, 900, 14));
};

/* ---- fleet: grid of little TV boxes that light up one by one and link together. params.count */
SCENES.fleet = (t, lt, sc, e) => {
  bgFill(e); const K = keyInfo(sc, t), n = sc.params.count || 15, cols = 5, rows = Math.ceil(n / cols), dur = sc.end - sc.start;
  const prog = clamp(lt / (dur * .8)), cw = 150, ch = 100, gx = cw + 40, gy = ch + 70, x0 = CX - (cols - 1) * gx / 2, y0 = HY - (rows - 1) * gy / 2 - 20;
  const pos = i => [x0 + (i % cols) * gx, y0 + Math.floor(i / cols) * gy];
  x.lineWidth = 3;
  for (let i = 0; i < n; i++) { const [ax, ay] = pos(i);
    [[i + 1, (i + 1) % cols !== 0], [i + cols, true]].forEach(([j, ok]) => { if (!ok || j >= n) return; const [bx, by] = pos(j);
      const lit = clamp((prog * n - Math.max(i, j)) * 2); x.strokeStyle = rgba(S.accent, .10 + .4 * lit); x.beginPath(); x.moveTo(ax, ay); x.lineTo(bx, by); x.stroke();
      if (lit > .5) { const p = (lt * 1.2 + R('fl', i, j)) % 1; circle(lerp(ax, bx, p), lerp(ay, by, p), 5, '#ffffff', .8); } }); }
  for (let i = 0; i < n; i++) { const [px, py] = pos(i), on = clamp((prog * n - i) * 2.5), pop = 1 + .12 * kick(lt - i * .03 - .1, 9, 18) * (on > 0 ? 1 : 0);
    x.save(); x.translate(px, py); x.scale(pop, pop);
    x.fillStyle = mixc(e.dim, '#000000', .35); x.beginPath(); x.roundRect(-cw / 2, -ch / 2, cw, ch, 14); x.fill();
    x.fillStyle = mixc('#0b0b10', S.accent, .15 + .85 * on * (.8 + .2 * Math.sin(t * 4 + i))); x.beginPath(); x.roundRect(-cw / 2 + 8, -ch / 2 + 8, cw - 16, ch - 16, 8); x.fill();
    x.fillStyle = mixc(e.dim, '#000000', .35); x.fillRect(-18, ch / 2, 36, 14); x.fillRect(-40, ch / 2 + 14, 80, 8);
    if (on > 0 && on < 1) ring(0, 0, 60 + on * 110, 3, S.accent, 1 - on);
    x.restore(); if (on > .3) glowDot(px, py, 120, S.accent, .22 * on); }
  sc.keys.forEach(k => shockwave(CX, HY, t - k.s, S.accent, 1100, 16));
};

/* ---- chat: message bubbles. params.bubbles [{who:"a"|"b", text, at}], params.names ["Interviewer","Candidate"] */
SCENES.chat = (t, lt, sc, e) => {
  bgFill(e); const B = sc.params.bubbles || [], names = sc.params.names || ['', ''], fam = S.fonts.text, wt = S.fonts.text_weight, size = 52, maxW = 700;
  x.font = `${wt} ${size}px "${fam}"`; x.textBaseline = 'middle'; x.textAlign = 'left';
  const wrap = s => { const out = []; let cur = ''; for (const w of s.split(' ')) { const tt = cur ? cur + ' ' + w : w; if (x.measureText(tt).width > maxW && cur) { out.push(cur); cur = w; } else cur = tt; } out.push(cur); return out; };
  const items = B.map(b => { const L = wrap(b.text), w = Math.min(maxW, Math.max(...L.map(l => x.measureText(l).width))) + 64, h = L.length * size * 1.3 + 44; return { ...b, L, w, h }; });
  let y = 0; items.forEach(it => { it.y = y; y += it.h + 48; }); const vis = items.filter(it => lt >= it.at - .6);
  const total = vis.length ? vis[vis.length - 1].y + vis[vis.length - 1].h : 0, shift = Math.max(0, total - 760), top = 330;
  for (const it of items) { const l = lt - it.at, typing = lt >= it.at - .6 && l < 0; if (lt < it.at - .6) continue;
    const mine = it.who === 'a', bx = mine ? W - 70 - it.w : 70, by = top + it.y - shift, name = names[mine ? 0 : 1];
    x.font = `700 32px "${fam}"`; x.fillStyle = rgba(e.ink, .6); x.textAlign = mine ? 'right' : 'left'; x.fillText(name, mine ? W - 70 : 70, by - 22); x.textAlign = 'left';
    if (typing) { x.fillStyle = e.soft; x.beginPath(); x.roundRect(bx, by, 150, 80, 36); x.fill(); for (let d = 0; d < 3; d++) circle(bx + 45 + d * 30, by + 40 - Math.abs(Math.sin(t * 7 + d * .8)) * 10, 9, e.ink, .8); continue; }
    const p = clamp(l / .3), s = spring(l, { from: .6, to: 1, zeta: .5 }), a = clamp(l / .12);
    x.save(); x.globalAlpha = a; x.translate(bx + (mine ? it.w : 0), by + it.h / 2); x.scale(s, s); x.translate(-(mine ? it.w : 0), -it.h / 2);
    x.fillStyle = mine ? S.accent : e.soft; x.beginPath(); x.roundRect(0, 0, it.w, it.h, 38); x.fill();
    x.fillStyle = mine ? S.on_accent : e.ink; x.font = `${wt} ${size}px "${fam}"`; it.L.forEach((ln, i) => x.fillText(ln, 32, 22 + size * 1.3 * (i + .5))); x.restore(); }
  x.globalAlpha = 1;
};

/* ---- tokens: rows of word-chip tiles streaming sideways. params.tokens [..] */
SCENES.tokens = (t, lt, sc, e) => {
  bgFill(e); const K = keyInfo(sc, t), T = sc.params.tokens || ['the', 'AI', 'model', 'writes', 'code', 'tokens', 'one', 'by', 'one'], fam = S.fonts.text, rows = 6, span = 2600;
  x.font = `700 46px "${fam}"`; x.textBaseline = 'middle'; x.textAlign = 'center';
  for (let r = 0; r < rows; r++) { const dir = r % 2 ? -1 : 1, sp = 90 + r * 35, y = HY - 300 + r * 105;
    for (let i = 0; i < 10; i++) { const born = r * .12 + i * .05; if (lt < born) continue; const a = easeOutExpo((lt - born) / .3), tk = T[(i + r * 3) % T.length], w = x.measureText(tk).width + 56;
      let px = ((i * 260 + dir * lt * sp + r * 90) % span + span) % span - 260; const hot = (i + r) % 5 === 0 || K.pulse > 1.2 && (i + r) % 2 === 0;
      x.globalAlpha = a * .95; x.fillStyle = hot ? S.accent : e.soft; x.beginPath(); x.roundRect(px - w / 2, y - 38, w, 76, 20); x.fill();
      x.fillStyle = hot ? S.on_accent : e.ink; x.fillText(tk, px, y + 2); } }
  x.globalAlpha = 1; sc.keys.forEach(k => shockwave(CX, HY, t - k.s, S.accent, 1000, 12));
};

/* ---- haunt: spooky stage (moon, ghosts, pumpkin, constellation). Original shapes only. */
function ghostShape(cx, cy, r, t, col, eye, ph) {
  x.save(); x.translate(cx, cy); x.fillStyle = col; x.beginPath(); x.arc(0, 0, r, Math.PI, 0); x.lineTo(r, r * 1.2);
  for (let i = 0; i <= 40; i++) { const px = r - i / 40 * 2 * r, py = r * 1.2 + Math.sin(i / 40 * TAU * 2.5 + t * 5 + ph) * r * .13; x.lineTo(px, py); }
  x.closePath(); x.fill(); x.fillStyle = eye; [-1, 1].forEach(s => { x.beginPath(); x.ellipse(s * r * .36, -r * .1, r * .13, r * .2, 0, 0, TAU); x.fill(); });
  x.beginPath(); x.ellipse(0, r * .32, r * .15, r * .1 + Math.abs(Math.sin(t * 2 + ph)) * r * .08, 0, 0, TAU); x.fill(); x.restore();
}
function pumpkinShape(cx, cy, r, t, body, dark, glow) {
  glowDot(cx, cy, r * 2.4, glow, .35 + .12 * Math.sin(t * 9)); x.save(); x.translate(cx, cy);
  x.fillStyle = dark; x.fillRect(-r * .07, -r * .98, r * .14, r * .26);
  x.fillStyle = body; [-.5, 0, .5].forEach(k => { x.beginPath(); x.ellipse(k * r * .6, 0, r * (.62 - Math.abs(k) * .12), r * .82, 0, 0, TAU); x.fill(); });
  x.fillStyle = dark; [-1, 1].forEach(s => poly([[s * r * .16, -r * .08], [s * r * .5, -r * .08], [s * r * .33, -r * .38]], dark));
  x.beginPath(); x.moveTo(-r * .5, r * .2); for (let i = 0; i <= 8; i++) x.lineTo(-r * .5 + i * r * .125, r * (i % 2 ? .45 : .22)); x.lineTo(r * .5, r * .3); x.lineTo(-r * .5, r * .3); x.closePath(); x.fill(); x.restore();
}
SCENES.haunt = (t, lt, sc, e) => {
  bgFill(e); const K = keyInfo(sc, t), n = sc.params.ghosts ?? 3;
  glowDot(CX + 230, 360, 520, '#fff3c9', .32); circle(CX + 230, 360, 150, '#fff3c9', .92); circle(CX + 190, 330, 24, '#e8dcae', .6); circle(CX + 270, 400, 34, '#e8dcae', .5);
  for (let i = 0; i < 26; i++) { const px = R('hs', i) * W, py = R('hy', i) * 900 + 120, tw = .4 + .6 * Math.abs(Math.sin(t * 1.5 + i)); circle(px, py, 2 + R('hr', i) * 3, '#ffffff', tw * .8); }
  for (let i = 0; i < 12; i++) { const a = [R('ca', i) * W, R('cb', i) * 500 + 700], b = [R('cc', i) * W, R('cd', i) * 500 + 700]; x.strokeStyle = rgba(S.accent, .12); x.lineWidth = 2; x.beginPath(); x.moveTo(a[0], a[1]); x.lineTo(b[0], b[1]); x.stroke(); circle(a[0], a[1], 7, S.accent, .5); }
  for (let i = 0; i < n; i++) { const bx = CX + (i - (n - 1) / 2) * 300 + Math.sin(t * .9 + i * 2) * 40, by = 560 + Math.sin(t * 1.6 + i * 1.9) * 40 - 80 * kick(lt - .2 * i, 4, 10) * 0 - 120 * clamp(K.pulse) * (i % 2 ? 1 : .6);
    const rr = 92 + (i % 2) * 24; glowDot(bx, by, rr * 2, '#ffffff', .16); ghostShape(bx, by, rr, t, rgba('#ffffff', .93), '#14101f', i * 1.3); }
  pumpkinShape(CX, 1010 - 30 * clamp(K.pulse), 150 * spring(lt, { from: .5, to: 1, zeta: .45 }), t, S.accent, '#1a0f10', S.accent);
  sc.keys.forEach(k => shockwave(CX, 1010, t - k.s, S.accent, 900, 16));
};

/* ---- stat: big counting number over rising bars (supports decimals). params: values[], number, decimals, prefix, suffix */
SCENES.stat = (t, lt, sc, e) => {
  bgFill(e); const K = keyInfo(sc, t), vals = sc.params.values || [.25, .4, .55, .75, 1], n = vals.length, base = 880, left = 140, bw = (W - 280) / n;
  x.strokeStyle = rgba(e.ink, .3); x.lineWidth = 3; x.beginPath(); x.moveTo(left - 20, base); x.lineTo(W - left + 20, base); x.stroke();
  const shown = Math.min(n, 1 + K.count + Math.floor(smooth(lt / (sc.end - sc.start)) * 1.5));
  vals.forEach((v, i) => { const st = sc.start + .15 + i * .18, p = i < shown ? spring(t - st, { from: 0, to: 1, zeta: .55 }) : 0, h = v * 340 * p, px = left + i * bw + bw * .15, w = bw * .7, last = i === n - 1;
    x.fillStyle = last ? S.accent : e.soft; x.fillRect(px, base - h, w, h); if (last && p > .5) glowDot(px + w / 2, base - h, 160, S.accent, .4); });
  const target = sc.params.number ?? 100, d = sc.params.decimals ?? 0, v = target * smooth((t - sc.start) / Math.max(.5, (lastKey(sc).s - sc.start)));
  x.font = `${S.fonts.display_weight} 230px "${S.fonts.display}"`; x.textAlign = 'center'; x.textBaseline = 'alphabetic';
  const sc2 = 1 + .12 * K.pulse; x.save(); x.translate(CX, 400); x.scale(sc2, sc2); x.fillStyle = e.ink; x.fillText((sc.params.prefix || '') + v.toFixed(d) + (sc.params.suffix ?? '%'), 0, 0); x.restore();
};

/* ---- echo: giant outlined keyword sliding diagonally behind the text (params.word, else the first keyword) */
SCENES.echo = (t, lt, sc, e) => {
  bgFill(e); const K = keyInfo(sc, t), fam = S.fonts.display, wt = S.fonts.display_weight;
  const word = ((sc.params.word || (sc.keys[0] ? sc.keys[0].w : 'AI')) + '').replace(/[.,!?;:*]+/g, '').toUpperCase();
  x.font = `${wt} 400px "${fam}"`; const w0 = x.measureText(word).width, sz = 400 * Math.min(1, 760 / w0); x.font = `${wt} ${sz}px "${fam}"`;
  x.save(); x.translate(CX, HY); x.rotate(-.2); x.textAlign = 'center'; x.textBaseline = 'middle'; x.lineWidth = 5; x.lineJoin = 'round';
  for (let r = -3; r <= 3; r++) { const slide = (r % 2 ? -1 : 1) * lt * 120 + r * 90, yy = r * sz * .95;
    if (r === 0 && K.count > 0) { x.fillStyle = rgba(S.accent, .22 + .5 * Math.min(1, K.pulse)); x.fillText(word, slide, yy); }
    x.strokeStyle = rgba(e.ink, r === 0 ? .55 : .26); x.strokeText(word, slide, yy); }
  x.restore(); sc.keys.forEach(k => shockwave(CX, HY, t - k.s, S.accent, 1000, 12));
};
