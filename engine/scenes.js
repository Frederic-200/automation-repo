/* ============================================================
   Scene library. Each scene = { plan(S), draw(S,t), events(S) }.
   S = scene timeline entry { start,end,words[],props }.
   plan() returns the scene's key times (so draw + sound effects agree).
   Visuals are synced to the narration through cue words in props.cues.
   ============================================================ */
const cue = (S, name, fb) => wordTime(S, S.props.cues && S.props.cues[name], S.start + fb);
const mono = (w, s) => FJ(w, s);
const monoW = (str, size, w = 700) => measure(str, FJ(w, size));
const note = (txt, y, t, t0) => T(txt, 540, y, { size: 24, font: FM(500, 24), color: 'rgba(255,255,255,.45)', ls: 1, alpha: A(t, t0, .4) });
const label = (txt, x, y, color = C.mute, align = 'left') => T(txt, x, y, { size: 22, font: FM(800, 22), ls: 4, color, align });

function chip(x, y, w, h, color, text, o = {}) {      // solid, high-contrast token chip (x,y = center)
  const s = o.scale === undefined ? 1 : o.scale; if (s <= 0) return;
  ctx.save(); ctx.translate(x, y); ctx.scale(s, o.scaleY === undefined ? s : o.scaleY); ctx.globalAlpha *= o.alpha === undefined ? 1 : clamp(o.alpha);
  rr(-w / 2, -h / 2, w, h, 22); ctx.fillStyle = color; ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,.22)'; rr(-w / 2, -h / 2, w, h * .45, 22); ctx.fill();
  T(text, 0, o.id !== undefined ? -h * .08 : h * .17, { font: mono(700, o.size || 52), color: C.ink });
  if (o.id !== undefined && o.idAlpha > 0) {
    ctx.fillStyle = 'rgba(8,24,42,.28)'; ctx.fillRect(-w / 2 + 18, h * .12, w - 36, 2);
    T(String(o.id), 0, h * .36, { font: mono(500, 34), color: C.ink, alpha: o.idAlpha });
  }
  ctx.restore();
}
function brick(x, y, w, h, color, text, o = {}) {      // LEGO-style brick (x,y = top-left of body)
  ctx.save(); ctx.translate(0, o.dy || 0);
  const studs = Math.max(1, Math.round(w / 62)), sw = w / studs;
  for (let i = 0; i < studs; i++) {
    const sx = x + sw * (i + .5);
    ctx.fillStyle = color; rr(sx - 17, y - 20, 34, 26, 8); ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,.35)'; rr(sx - 17, y - 20, 34, 10, 8); ctx.fill();
  }
  ctx.fillStyle = lg(0, y, 0, y + h, [[0, color], [1, color]]); rr(x, y, w, h, 14); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,.22)'; rr(x, y, w, h * .38, 14); ctx.fill();
  ctx.fillStyle = 'rgba(0,0,0,.18)'; rr(x, y + h - 14, w, 14, 10); ctx.fill();
  T(text, x + w / 2, y + h * .64, { font: mono(700, 46), color: C.ink });
  ctx.restore();
}
function brickIcon(x, y, s, color, a = 1) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.globalAlpha *= a;
  for (const dx of [-26, 26]) { ctx.fillStyle = color; rr(dx - 15, -52, 30, 24, 7); ctx.fill() }
  ctx.fillStyle = color; rr(-70, -34, 140, 80, 16); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,.28)'; rr(-70, -34, 140, 30, 16); ctx.fill();
  ctx.restore();
}
function checkIcon(x, y, r, p, color = C.tealL) {
  ctx.save(); ctx.strokeStyle = color; ctx.lineWidth = 9; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  circ(x, y, r); ctx.globalAlpha *= .9; ctx.stroke(); ctx.globalAlpha /= .9;
  const pts = [[x - r * .42, y + r * .02], [x - r * .1, y + r * .36], [x + r * .46, y - r * .32]];
  const l1 = Math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]), l2 = Math.hypot(pts[2][0] - pts[1][0], pts[2][1] - pts[1][1]);
  const d = clamp(p) * (l1 + l2); ctx.beginPath(); ctx.moveTo(...pts[0]);
  if (d <= l1) { const u = d / l1; ctx.lineTo(pts[0][0] + (pts[1][0] - pts[0][0]) * u, pts[0][1] + (pts[1][1] - pts[0][1]) * u) }
  else { ctx.lineTo(...pts[1]); const u = (d - l1) / l2; ctx.lineTo(pts[1][0] + (pts[2][0] - pts[1][0]) * u, pts[1][1] + (pts[2][1] - pts[1][1]) * u) }
  ctx.stroke(); ctx.restore();
}

const SCENES = {};

/* ---------------- HOOK ---------------- */
SCENES.hook = {
  plan(S) {
    const P = S.props, idx = []; let n = 0;
    for (const l of P.lines) { idx.push(n); n += l.split(' ').length }
    const ts = idx.map((k, i) => i === 0 ? S.start + .06 : Math.max(S.start + .06, (S.words[k] ? S.words[k].t0 : S.start) - .08));
    return { ts, typeStart: S.start + .25, typeEnd: ts[ts.length - 1] + .1 };
  },
  draw(S, t) {
    const P = S.props, pl = this.plan(S);
    P.lines.forEach((ln, i) => {
      const a = A(t, pl.ts[i], .38), acc = i === P.accent;
      const size = fitSize(ln, 800, acc ? 128 : 96, 940, false, 1), y = 590 + i * 150;
      if (a <= 0) return;
      if (acc) { const mw = measure(ln, FM(800, size), 1); marker(540 - mw / 2, y, mw, size, t, pl.ts[i] + .3, C.blue, .2) }
      if (acc && t - pl.ts[i] < .4) {                    // glitch burst
        const g = 1 - (t - pl.ts[i]) / .4, j = Math.sin(t * 90) * 14 * g;
        T(ln, 540 + j, y, { size, color: 'rgba(255,122,107,.8)', alpha: a * .8 * g, ls: 1 });
        T(ln, 540 - j, y, { size, color: 'rgba(63,167,214,.8)', alpha: a * .8 * g, ls: 1 });
      }
      kinetic(ln, 540, y, t, pl.ts[i], { size, ls: 1, shadow: 20, chars: acc, colors: acc ? sweepColors(C.blue, C.tealL) : undefined });
      if (acc) {                                          // underline sweep
        const u = eo3((t - pl.ts[i] - .25) / .45), w = measure(ln, FM(800, size), 1);
        if (u > 0) { rr(540 - w / 2, y + 26, w * u, 10, 5); ctx.fillStyle = C.warm; ctx.fill() }
      }
    });
    // chat input bar: this is "what you typed"
    const a = A(t, S.start + .15, .4), y = 1090; ctx.save(); ctx.globalAlpha *= a; ctx.translate(0, (1 - a) * 40);
    glass(80, y, 920, 124, 62, .1);
    const full = P.input || '', n = Math.floor(clamp((t - pl.typeStart) / (pl.typeEnd - pl.typeStart)) * full.length);
    const txt = full.slice(0, n), caret = (Math.floor(t * 2.2) % 2 === 0 || n < full.length) ? '▌' : '';
    T(txt + caret, 130, y + 78, { font: mono(500, 44), color: 'rgba(255,255,255,.92)', align: 'left' });
    if (n === 0) T('Message…', 130, y + 78, { font: mono(500, 44), color: 'rgba(255,255,255,.3)', align: 'left' });
    const sp = 1 + (n >= full.length ? .08 * Math.sin((t - pl.typeEnd) * 8) : 0);
    ctx.save(); ctx.translate(930, y + 62); ctx.scale(sp, sp); circ(0, 0, 40); ctx.fillStyle = n >= full.length ? C.teal : 'rgba(255,255,255,.15)'; ctx.fill();
    ctx.strokeStyle = C.ink; ctx.lineWidth = 7; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.beginPath(); ctx.moveTo(0, 14); ctx.lineTo(0, -14); ctx.moveTo(-14, 0); ctx.lineTo(0, -15); ctx.lineTo(14, 0); ctx.stroke(); ctx.restore();
    ctx.restore();
  },
  events(S) {
    const pl = this.plan(S), ev = [], n = (S.props.input || '').length;
    for (let i = 0; i < n; i++) ev.push({ t: pl.typeStart + (pl.typeEnd - pl.typeStart) * i / n, kind: 'key' });
    pl.ts.forEach((t, i) => ev.push({ t, kind: i === S.props.accent ? 'glitch' : 'pop' }));
    return ev;
  }
};

/* ---------------- PROMISE: logo sting + lesson card ---------------- */
SCENES.promise = {
  plan(S) {
    const tLogo = cue(S, 'logo', .05), tClick = tLogo + 1.5;
    return { tLogo, tClick, tTitle: Math.max(tClick + .15, cue(S, 'title', 2.2)) };
  },
  draw(S, t) {
    const pl = this.plan(S), cx = 540, cy = 520, sc = 1.38;
    const prog = clamp((t - pl.tLogo) / 1.3);
    const cu = clamp((t - (pl.tClick - .6)) / .5);                   // cursor flies in
    const press = t > pl.tClick && t < pl.tClick + .14 ? .78 : 1;
    const cur = { a: eo3((t - (pl.tClick - .75)) / .25), dx: (1 - eo3(cu)) * 130, dy: (1 - eo3(cu)) * 110, s: press };
    drawLogo(cx, cy, sc, prog, cur);
    const tip = logoCursorTip(cx, cy, sc); ripple(tip[0] + 8, tip[1] + 8, t, pl.tClick, .7, 130);
    wordmark(540, 885, 100, clamp((t - (pl.tLogo + .9)) / .9));
    const a = A(t, pl.tTitle, .45);
    if (a > 0) {
      ctx.save(); ctx.globalAlpha *= a; ctx.translate(0, (1 - a) * 40);
      const L = 'LESSON ' + String(S.lesson || 0).padStart(2, '0');
      pill(540 - 190, 955, 380, 78, 'rgba(52,176,138,.18)', 'rgba(92,224,181,.6)');
      T(L, 540, 1008, { size: 38, ls: 5, color: C.tealL });
      const title = S.titleText; let sz = 80, f = FM(800, sz), lines = wrap(title, 900, f);
      for (const z of [68, 58]) if (lines.length > 2) { sz = z; f = FM(800, sz); lines = wrap(title, 900, f) }
      lines.forEach((l, i) => kinetic(l, 540, 1125 + i * Math.round(sz * 1.15), t, pl.tTitle + .1 + i * .18, { size: sz, shadow: 18 }));
      ctx.restore();
    }
  },
  events(S) { const pl = this.plan(S); return [{ t: pl.tLogo, kind: 'draw' }, { t: pl.tClick, kind: 'click' }, { t: pl.tTitle, kind: 'pop' }] }
};

/* ---------------- CONCEPT CARD ---------------- */
SCENES.concept = {
  plan(S) { return { tTerm: cue(S, 'term', .5), tDef: cue(S, 'def', 1.8), tEx: cue(S, 'example', 4.2) } },
  draw(S, t) {
    const P = S.props, pl = this.plan(S);
    glass(90, 330, 900, 900, 44, .07);
    const ia = A(t, S.start + .1, .5); brickIcon(540, 470, 1 + .04 * Math.sin(t * 2), C.teal, ia);
    const size = fitSize(P.term, 800, 190, 780, false, 6), f = FM(800, size), tw = measure(P.term, f, 6);
    const g = lg(540 - tw / 2, 0, 540 + tw / 2, 0, [[0, C.blue], [1, C.tealL]]);
    let x = 540 - tw / 2;
    for (let i = 0; i < P.term.length; i++) {
      const ch = P.term[i], cw = measure(ch, f, 6), e = eback((t - pl.tTerm - i * .07) / .3);
      if (e > 0) { ctx.save(); ctx.translate(x + cw / 2, 700); ctx.scale(e, e); T(ch, 0, 0, { font: f, color: g, ls: 6, shadow: 24 }); ctx.restore() }
      x += cw + 6;
    }
    const u = eo3((t - pl.tTerm - .5) / .5); if (u > 0) { rr(540 - 200 * u, 730, 400 * u, 8, 4); ctx.fillStyle = C.warm; ctx.fill() }
    const df = FM(500, 44), lines = wrap(P.definition, 780, df), total = lines.join(' ').length;
    const n = Math.floor(clamp((t - pl.tDef) / 2.2) * total); let used = 0;
    lines.forEach((ln, i) => {
      const k = clamp(n - used, 0, ln.length); used += ln.length + 1;
      if (k > 0) T(ln.slice(0, k), 540, 830 + i * 62, { font: df, color: 'rgba(255,255,255,.92)' });
    });
    if (P.example) {
      const ea = A(t, pl.tEx - .3, .4);
      if (ea > 0) {
        label('EXAMPLE', 540, 1000, 'rgba(255,255,255,.45)', 'center');
        const toks = P.example.tokens, cf = mono(700, 56), ws = toks.map(s => monoW(s.trim(), 56) + 52), gap = 16;
        const total = ws.reduce((a, b) => a + b, 0) + gap * (toks.length - 1); let cx = 540 - total / 2;
        const plain = 1 - A(t, pl.tEx, .25);
        T(P.example.text, 540, 1090, { font: mono(700, 56), color: '#fff', alpha: plain * ea });
        toks.forEach((s, i) => {
          const e = eback((t - pl.tEx - i * .13) / .35);
          chip(cx + ws[i] / 2, 1070, ws[i], 104, PAL[i % PAL.length], s.trim(), { size: 56, scale: e });
          cx += ws[i] + gap;
        });
        const ba = A(t, pl.tEx + .55, .4); T((P.example.label) || (toks.length + ' tokens'), 540, 1190, { size: 40, color: C.tealL, alpha: ba });
      }
    }
  },
  events(S) {
    const pl = this.plan(S), ev = [{ t: pl.tTerm, kind: 'pop' }];
    (S.props.example ? S.props.example.tokens : []).forEach((_, i) => ev.push({ t: pl.tEx + i * .13, kind: 'pop' }));
    return ev;
  }
};

/* ---------------- ANALOGY: LEGO bricks ---------------- */
SCENES.analogy = {
  plan(S) { return { tSent: cue(S, 'sentence', 2.0), tDrop: cue(S, 'drop', 3.5), tLabel: cue(S, 'label', 6) } },
  draw(S, t) {
    const P = S.props, pl = this.plan(S);
    const pileA = A(t, S.start + .1, .5) * (1 - A(t, pl.tSent, .35));
    if (pileA > 0) {
      ctx.save(); ctx.globalAlpha *= pileA;
      [[-150, 880, 2.1, 0], [90, 840, 2.1, 1], [-30, 700, 2.1, 2], [200, 700, 1.7, 4]].forEach(([dx, y, s, k]) => brickIcon(540 + dx, y + Math.sin(t * 2 + k) * 8, s, PAL[k % PAL.length]));
      ctx.restore();
    }
    const sA = A(t, pl.tSent, .5);
    label('YOUR TEXT', 540, 400, C.mute, 'center'); ctx.save(); ctx.globalAlpha *= sA;
    T(P.sentence, 540, 480, { font: mono(700, 62), color: '#fff', alpha: 1 - .6 * A(t, pl.tDrop + .6, .6) }); ctx.restore();
    const lab = P.bricks.map(b => b.trim()), ws = lab.map(l => monoW(l, 46) + 62), gap = 10;
    const total = ws.reduce((a, b) => a + b, 0) + gap * (ws.length - 1); let x = 540 - total / 2;
    const rowY = 760, ah = A(t, pl.tDrop - .2, .4);
    if (ah > 0) { ctx.save(); ctx.globalAlpha *= ah; ctx.strokeStyle = C.warm; ctx.lineWidth = 6; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.beginPath(); ctx.moveTo(540, 530); ctx.lineTo(540, 600); ctx.moveTo(515, 578); ctx.lineTo(540, 603); ctx.lineTo(565, 578); ctx.stroke(); ctx.restore(); T('snap!', 640, 590, { size: 36, color: C.warm, alpha: ah }) }
    // base plate
    const bp = A(t, pl.tDrop - .3, .5); if (bp > 0) { ctx.globalAlpha *= bp; rr(540 - total / 2 - 24, rowY + 150, total + 48, 24, 10); ctx.fillStyle = 'rgba(255,255,255,.14)'; ctx.fill(); ctx.globalAlpha /= bp }
    ws.forEach((w, i) => {
      const t0 = pl.tDrop + .25 + i * .3, u = clamp((t - t0) / .55);
      if (u > 0) { const dy = -(1 - eback(u)) * 420; ctx.save(); ctx.globalAlpha *= clamp(u * 4); brick(x, rowY, w, 150, PAL[i % PAL.length], lab[i], { dy }); ctx.restore() }
      x += w + gap;
    });
    const la = A(t, pl.tLabel, .5);
    if (la > 0) {
      ctx.save(); ctx.globalAlpha *= la; ctx.translate(0, (1 - la) * 30);
      const bx = 540 - total / 2, by = rowY + 215; ctx.strokeStyle = 'rgba(255,255,255,.5)'; ctx.lineWidth = 4; ctx.beginPath();
      ctx.moveTo(bx, by); ctx.lineTo(bx, by + 18); ctx.lineTo(bx + total, by + 18); ctx.lineTo(bx + total, by); ctx.stroke();
      const cnt = Math.min(P.bricks.length, Math.floor((t - pl.tLabel) / .18) + 1);
      pill(540 - 190, by + 50, 380, 92, 'rgba(255,200,87,.16)', C.warm);
      T(cnt + (cnt === 1 ? ' token' : ' tokens'), 540, by + 112, { size: 52, color: C.warm });
      ctx.restore();
    }
    note('Illustrative · real tokenizers split text differently', 1230, t, pl.tLabel);
  },
  events(S) {
    const pl = this.plan(S), ev = [{ t: pl.tDrop - .2, kind: 'swoosh' }];
    S.props.bricks.forEach((_, i) => ev.push({ t: pl.tDrop + .25 + i * .3 + .3, kind: 'brick' }));
    ev.push({ t: pl.tLabel, kind: 'pop' }); return ev;
  }
};

/* ---------------- TOKENS: split + numbers ---------------- */
SCENES.tokens = {
  plan(S) { return { tSplit: cue(S, 'split', 1.2), tNum: cue(S, 'numbers', 8) } },
  layout(S) {
    const P = S.props, size = 50, ws = P.chips.map(c => monoW(c, size) + 56), gap = 16, rows = [[]]; let rw = 0;
    ws.forEach((w, i) => { if (rw + w > 880 && rows[rows.length - 1].length) { rows.push([]); rw = 0 } rows[rows.length - 1].push(i); rw += w + gap });
    const pos = [];
    rows.forEach((r, ri) => {
      const tot = r.reduce((a, i) => a + ws[i], 0) + gap * (r.length - 1); let x = 540 - tot / 2;
      r.forEach(i => { pos[i] = { x: x + ws[i] / 2, y: 740 + ri * 180 }; x += ws[i] + gap });
    });
    // origin of each piece inside the full sentence (at 58px)
    const sf = FM(800, 58), left = 540 - measure(P.sentence, sf) / 2, org = []; let p = 0;
    P.chips.forEach(c => { while (P.sentence[p] === ' ') p++; org.push({ x: left + measure(P.sentence.slice(0, p), sf) + measure(c, sf) / 2, y: 480 }); p += c.length });
    return { ws, pos, org };
  },
  draw(S, t) {
    const P = S.props, pl = this.plan(S), L = this.layout(S);
    const sa = A(t, S.start + .2, .5), dim = 1 - .72 * A(t, pl.tSplit, .5);
    label('ONE SENTENCE', 540, 400, C.mute, 'center');
    T(P.sentence, 540, 500, { font: FM(800, 58), color: '#fff', alpha: sa * dim });
    P.chips.forEach((c, i) => {
      const q = clamp((t - pl.tSplit - i * .09) / .6), e = eo3(q); if (e <= 0) return;
      const x = lerp(L.org[i].x, L.pos[i].x, e), y = lerp(L.org[i].y - 12, L.pos[i].y, e);
      const idA = clamp((t - pl.tNum - i * .12) / .4);
      chip(x, y, L.ws[i], 150, PAL[i % PAL.length], c, { size: 50, scale: lerp(.55, 1, e), alpha: e * 1.2, id: P.ids[i], idAlpha: eo3(idA * 1.3), scaleY: idA > 0 && idA < .5 ? lerp(1, .82, Math.sin(idA * 2 * Math.PI)) : undefined });
    });
    const n = P.chips.length, ca = A(t, pl.tSplit + .8, .4);
    if (ca > 0) { pill(540 - 170, 1040, 340, 92, 'rgba(255,200,87,.16)', C.warm); T(n + ' tokens', 540, 1103, { size: 52, color: C.warm, alpha: ca }) }
    const na = A(t, pl.tNum + .2, .5); if (na > 0) T('each token → a number (its ID)', 540, 1190, { size: 30, font: FM(500, 30), color: C.tealL, alpha: na });
    note('Illustrative split & IDs · real models differ', 1245, t, pl.tSplit);
  },
  events(S) {
    const pl = this.plan(S), ev = [{ t: pl.tSplit, kind: 'split' }];
    S.props.chips.forEach((_, i) => { ev.push({ t: pl.tSplit + .25 + i * .09, kind: 'pop' }); ev.push({ t: pl.tNum + i * .12, kind: 'flip' }) });
    return ev;
  }
};

/* ---------------- VERSUS: what you see vs what the AI sees ---------------- */
SCENES.versus = {
  plan(S) { const tl = cue(S, 'letters', 1.2); return { tLetters: tl, tPanel: tl + 1.5, tTok: Math.max(cue(S, 'tokens', 4), tl + 1.9) } },
  draw(S, t) {
    const P = S.props, pl = this.plan(S), word = P.word, hl = (P.highlight || 'r').toLowerCase();
    const aiA = A(t, pl.tPanel, .5), tokA = A(t, pl.tTok, .5), topDim = 1 - .55 * tokA;
    ctx.save(); ctx.globalAlpha *= topDim;
    glass(90, 320, 900, 330, 40, .07); label('WHAT YOU SEE', 130, 375, C.mute);
    const fs = 86, cw = monoW('m', fs), step = cw + 14, x0 = 540 - (word.length * step - 14) / 2;
    let count = 0;
    for (let i = 0; i < word.length; i++) {
      const ch = word[i], isH = ch.toLowerCase() === hl, x = x0 + i * step + cw / 2;
      if (isH) {
        const th = pl.tLetters + .15 + count * .38, e = eback((t - th) / .3); count++;
        if (e > 0) {
          rr(x - cw / 2 - 6, 470, cw + 12, 128, 16); ctx.fillStyle = `rgba(255,122,107,${.22 * clamp(e)})`; ctx.fill();
          T(ch, x, 565, { font: mono(700, fs), color: lerpColor('#FFFFFF', C.coral, clamp(e)) });
          const bs = clamp(e); ctx.save(); ctx.translate(x, 450); ctx.scale(bs, bs); circ(0, 0, 26); ctx.fillStyle = C.coral; ctx.fill(); T(String(count), 0, 11, { size: 32, color: C.ink }); ctx.restore();
          continue;
        }
      }
      T(ch, x, 565, { font: mono(700, fs), color: '#FFFFFF' });
    }
    T(P.question, 540, 628, { size: 30, font: FM(500, 30), color: C.mute, alpha: A(t, pl.tLetters, .4) });
    ctx.restore();
    // VS badge
    const vb = A(t, pl.tPanel, .4); if (vb > 0) { circ(540, 700, 40); ctx.fillStyle = C.warm; ctx.globalAlpha *= vb; ctx.fill(); T('VS', 540, 714, { size: 34, color: C.ink }); ctx.globalAlpha /= vb }
    // AI side
    if (aiA > 0) {
      ctx.save(); ctx.globalAlpha *= aiA; ctx.translate(0, (1 - aiA) * 40);
      glass(90, 760, 900, 400, 40, .09); label('WHAT AI SEES', 130, 815, C.tealL);
      const cs = 80, ws = P.chips.map(c => monoW(c, cs) + 64), gap = 18, tot = ws.reduce((a, b) => a + b, 0) + gap * (ws.length - 1); let x = 540 - tot / 2;
      P.chips.forEach((c, i) => {
        const e = eback((t - pl.tTok - .1 - i * .14) / .35);
        ctx.save(); ctx.setLineDash([14, 12]); ctx.strokeStyle = 'rgba(255,255,255,.28)'; ctx.lineWidth = 3; rr(x, 910, ws[i], 150, 22); ctx.globalAlpha *= (1 - clamp(e)); ctx.stroke(); ctx.restore();
        chip(x + ws[i] / 2, 985, ws[i], 150, PAL[i % PAL.length], c, { size: cs, scale: e });
        x += ws[i] + gap;
      });
      const q = .5 + .5 * Math.sin(t * 6);
      T('?', 540, 1125, { size: 70, color: C.coral, alpha: A(t, pl.tTok + .6, .3) * (.6 + .4 * q) });
      ctx.restore();
    }
    note('Typical split · varies by model', 1215, t, pl.tTok);
  },
  events(S) {
    const pl = this.plan(S), n = [...S.props.word.toLowerCase()].filter(c => c === (S.props.highlight || 'r').toLowerCase()).length, ev = [];
    for (let i = 0; i < n; i++) ev.push({ t: pl.tLetters + .15 + i * .38, kind: 'tick' });
    ev.push({ t: pl.tPanel, kind: 'swoosh' });
    S.props.chips.forEach((_, i) => ev.push({ t: pl.tTok + .1 + i * .14 + .1, kind: 'pop' }));
    return ev;
  }
};
function lerpColor(a, b, t) {
  const p = s => [1, 3, 5].map(i => parseInt(s.slice(i, i + 2), 16)), x = p(a), y = p(b);
  return `rgb(${x.map((v, i) => Math.round(lerp(v, y[i], t))).join(',')})`;
}

/* ---------------- RECAP ---------------- */
SCENES.recap = {
  plan(S) { return { t: [cue(S, 'p1', 1.2), cue(S, 'p2', 3.5), cue(S, 'p3', 6)] } },
  draw(S, t) {
    const P = S.props, pl = this.plan(S);
    T('RECAP', 540, 400, { size: 50, ls: 10, color: C.tealL, alpha: A(t, S.start + .1, .4) });
    P.points.forEach((p, i) => {
      const a = A(t, pl.t[i], .5), y = 470 + i * 250; if (a <= 0) return;
      ctx.save(); ctx.globalAlpha *= a; ctx.translate((1 - a) * 90, 0);
      glass(90, y, 900, 210, 36, .09, pl.t[i]);
      circ(180, y + 105, 48); ctx.fillStyle = PAL[i]; ctx.fill(); T(String(i + 1), 180, y + 125, { size: 56, color: C.ink });
      const f = FM(800, 46), lines = wrap(p, 560, f);
      lines.forEach((l, k) => kinetic(l, 262, y + 105 + (k - (lines.length - 1) / 2) * 56 + 16, t, pl.t[i] + .12 + k * .15, { size: 46, align: 'left' }));
      checkIcon(900, y + 105, 38, (t - pl.t[i] - .35) / .4);
      ctx.restore();
    });
  },
  events(S) { return this.plan(S).t.flatMap(t => [{ t, kind: 'whoosh2' }, { t: t + .55, kind: 'ding' }]) }
};

/* ---------------- QUIZ + END CARD ---------------- */
SCENES.quiz_end = {
  plan(S) {
    const d = S.end - S.start, tEnd = cue(S, 'end', d * .6);
    return { tQuiz: cue(S, 'quiz', .05), tA: cue(S, 'optA', 1.6), tB: cue(S, 'optB', 3), tAns: cue(S, 'answer', 5), tEnd, tFollow: cue(S, 'follow', d - 2.2) };
  },
  draw(S, t) {
    const P = S.props, pl = this.plan(S), endA = A(t, pl.tEnd, .55), quizA = 1 - endA;
    if (quizA > 0) {
      ctx.save(); ctx.globalAlpha *= quizA; ctx.translate(-endA * 80, 0);
      const qa = A(t, pl.tQuiz, .5);
      pill(540 - 150, 330, 300, 80, 'rgba(255,200,87,.16)', C.warm); T('QUIZ', 540, 387, { size: 46, ls: 10, color: C.warm, alpha: qa });
      const f = FM(800, 62), lines = wrap(P.question, 880, f);
      lines.forEach((l, i) => kinetic(l, 540, 520 + i * 74, t, pl.tQuiz + i * .18, { size: 62, shadow: 18 }));
      const base = 520 + lines.length * 74 + 30;
      P.options.forEach((o, i) => {
        const t0 = [pl.tA, pl.tB][i] - .1, e = eback((t - t0) / .4), y = base + i * 190; if (e <= 0) return;
        const hot = Math.max(0, 1 - Math.abs(t - t0 - .15) / .5);
        ctx.save(); ctx.translate(540, y + 80); ctx.scale(lerp(.9, 1, clamp(e)) + .03 * hot, lerp(.9, 1, clamp(e)) + .03 * hot); ctx.translate(-540, -(y + 80)); ctx.globalAlpha *= clamp(e);
        glass(90, y, 900, 160, 36, .1 + .08 * hot, t0);
        circ(190, y + 80, 52); ctx.fillStyle = PAL[i === 0 ? 0 : 3]; ctx.fill(); T('AB'[i], 190, y + 100, { size: 60, color: C.ink });
        T(o, 275, y + 98, { font: mono(700, fitSize(o, 700, 54, 650, true)), align: 'left', color: '#fff' });
        ctx.restore();
      });
      T('Answer in the comments ↓', 540, base + 2 * 190 + 40, { size: 40, color: C.tealL, alpha: A(t, pl.tAns, .5) * (.75 + .25 * Math.sin(t * 5)) });
      ctx.restore();
    }
    if (endA > 0) {
      ctx.save(); ctx.globalAlpha *= endA; ctx.translate((1 - endA) * 80, 0);
      drawLogo(540, 520, 1.15, 1, { a: 1, dx: 0, dy: 0, s: 1 });
      wordmark(540, 830, 92, 1);
      T('Daily AI lessons · one minute at a time', 540, 905, { size: 34, font: FM(500, 34), color: C.mute });
      const ta = A(t, pl.tEnd + .35, .5);
      if (ta > 0) {
        ctx.save(); ctx.globalAlpha *= ta; ctx.translate(0, (1 - ta) * 30);
        glass(120, 950, 840, 170, 36, .08, pl.tEnd + .35); label('TOMORROW', 540, 1005, C.warm, 'center');
        const tf = FM(800, fitSize(P.teaser, 800, 54, 760)); T(P.teaser, 540, 1080, { font: tf, color: '#fff' });
        ctx.restore();
      }
      // follow button + cursor click
      const bx = 540, by = 1235, clicked = t > pl.tFollow + .55, bw = 420;
      const press = t > pl.tFollow + .5 && t < pl.tFollow + .64 ? .94 : 1;
      ctx.save(); ctx.translate(bx, by); ctx.scale(press, press);
      pill(-bw / 2, -50, bw, 100, clicked ? 'rgba(52,176,138,.25)' : C.teal, clicked ? C.tealL : null);
      T(clicked ? 'Following ✓' : 'Follow', 0, 20, { size: 46, color: clicked ? C.tealL : C.ink });
      ctx.restore();
      const cu = clamp((t - (pl.tFollow - .2)) / .7), cxx = lerp(bx + 330, bx + 70, eo3(cu)), cyy = lerp(by + 250, by + 30, eo3(cu));
      if (t > pl.tFollow - .3 && !(t > pl.tFollow + 1.6)) {
        const ca = clamp((t - (pl.tFollow - .3)) / .2) * (1 - clamp((t - (pl.tFollow + 1.2)) / .4));
        ctx.save(); ctx.globalAlpha *= ca; ctx.translate(cxx, cyy); const cs = (t > pl.tFollow + .5 && t < pl.tFollow + .64) ? .8 : 1; ctx.scale(cs * 1.9, cs * 1.9);
        ctx.fillStyle = '#fff'; ctx.strokeStyle = C.ink; ctx.lineWidth = 2; ctx.beginPath(); LOGO.cursor.forEach(([x, y], k) => { const px = (x - 724), py = (y - 203); k ? ctx.lineTo(px, py) : ctx.moveTo(px, py) }); ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.restore();
      }
      ripple(bx + 70, by + 30, t, pl.tFollow + .55, .7, 110);
      ctx.restore();
    }
  },
  events(S) {
    const pl = this.plan(S);
    return [{ t: pl.tA - .1, kind: 'pop' }, { t: pl.tB - .1, kind: 'pop' }, { t: pl.tEnd, kind: 'swoosh' }, { t: pl.tFollow + .55, kind: 'click' }, { t: pl.tFollow + .75, kind: 'ding' }];
  }
};
