/* ============================================================
   Scene library, part 2: flow, network, chat, stat, compare, anatomy, map
   (same contract as scenes.js: plan / draw / events, cue words in props.cues)
   ============================================================ */

/* ---------- little vector icons ---------- */
function icon(kind, x, y, s, color) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = 6; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  const L = (...p) => { ctx.beginPath(); ctx.moveTo(p[0], p[1]); for (let i = 2; i < p.length; i += 2) ctx.lineTo(p[i], p[i + 1]); ctx.stroke() };
  switch (kind) {
    case 'chat': rr(-26, -22, 52, 36, 10); ctx.stroke(); ctx.beginPath(); ctx.moveTo(-10, 14); ctx.lineTo(-14, 26); ctx.lineTo(2, 14); ctx.stroke(); break;
    case 'search': circ(-5, -5, 16); ctx.stroke(); L(7, 7, 24, 24); break;
    case 'db': ctx.beginPath(); ctx.ellipse(0, -17, 24, 9, 0, 0, TAU); ctx.stroke(); L(-24, -17, -24, 17); L(24, -17, 24, 17);
      ctx.beginPath(); ctx.ellipse(0, 0, 24, 9, 0, 0, Math.PI); ctx.stroke(); ctx.beginPath(); ctx.ellipse(0, 17, 24, 9, 0, 0, Math.PI); ctx.stroke(); break;
    case 'brain': [[-14, 10], [14, 10], [0, -14]].forEach(([a, b]) => { circ(a, b, 7); ctx.fill() }); L(-14, 10, 14, 10, 0, -14, -14, 10); break;
    case 'doc': rr(-18, -26, 36, 52, 6); ctx.stroke(); L(-8, -10, 8, -10); L(-8, 2, 8, 2); L(-8, 14, 2, 14); break;
    case 'gear': circ(0, 0, 11); ctx.stroke(); for (let i = 0; i < 8; i++) { const a = i / 8 * TAU; L(Math.cos(a) * 17, Math.sin(a) * 17, Math.cos(a) * 25, Math.sin(a) * 25) } break;
    case 'user': circ(0, -10, 10); ctx.stroke(); ctx.beginPath(); ctx.arc(0, 26, 22, Math.PI * 1.15, Math.PI * 1.85); ctx.stroke(); break;
    case 'check': L(-18, 2, -6, 14, 18, -12); break;
    case 'spark': ctx.beginPath(); ctx.moveTo(0, -26); ctx.quadraticCurveTo(3, -3, 26, 0); ctx.quadraticCurveTo(3, 3, 0, 26); ctx.quadraticCurveTo(-3, 3, -26, 0); ctx.quadraticCurveTo(-3, -3, 0, -26); ctx.fill(); break;
    case 'cloud': ctx.beginPath(); ctx.arc(-10, 4, 12, Math.PI * .5, Math.PI * 1.5); ctx.arc(2, -8, 14, Math.PI, Math.PI * 1.9); ctx.arc(14, 4, 12, Math.PI * 1.5, Math.PI * .5); ctx.closePath(); ctx.stroke(); break;
    case 'bolt': ctx.beginPath(); ctx.moveTo(6, -26); ctx.lineTo(-14, 4); ctx.lineTo(0, 4); ctx.lineTo(-6, 26); ctx.lineTo(16, -6); ctx.lineTo(2, -6); ctx.closePath(); ctx.fill(); break;
    case 'target': circ(0, 0, 24); ctx.stroke(); circ(0, 0, 12); ctx.stroke(); circ(0, 0, 3); ctx.fill(); break;
    default: circ(0, 0, 18); ctx.stroke();
  }
  ctx.restore();
}
/* start time of the i-th of n items: explicit cue (cues.<prefix><i+1>) or evenly spread */
function cueSeq(S, prefix, n, from = 1.0, to = null) {
  const end = to === null ? (S.voice_end - S.start - 1.2) : to, out = [];
  for (let i = 0; i < n; i++) out.push(cue(S, prefix + (i + 1), from + (end - from) * (n === 1 ? 0 : i / n)));
  return out;
}

/* ---------------- STAT: one big number ---------------- */
SCENES.stat = {
  plan(S) { return { tNum: cue(S, 'reveal', 1.0), tSub: cue(S, 'sub', 3.0) } },
  draw(S, t) {
    const P = S.props, pl = this.plan(S);
    glass(90, 360, 900, 720, 48, .07);
    const a = A(t, pl.tNum - .2, .5);
    for (let i = 0; i < 3; i++) {   // pulse rings
      const u = ((t - pl.tNum) * .5 + i / 3) % 1; if (t < pl.tNum || u < 0) continue;
      ctx.strokeStyle = `rgba(92,224,181,${.35 * (1 - u)})`; ctx.lineWidth = 4; circ(540, 640, 120 + u * 330); ctx.stroke();
    }
    if (P.icon) icon(P.icon, 540, 470, 1.9, C.tealL);
    let txt;
    if (P.text !== undefined) txt = P.text;
    else {
      const k = eo3((t - pl.tNum) / 1.8), v = P.value * k, dec = P.decimals || 0;
      txt = (P.prefix || '') + v.toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec }) + (P.suffix || '');
    }
    const full = P.text !== undefined ? P.text : (P.prefix || '') + P.value.toLocaleString('en-US', { minimumFractionDigits: P.decimals || 0, maximumFractionDigits: P.decimals || 0 }) + (P.suffix || '');
    const size = fitSize(full, 800, 280, 800, false, 2), pop = eback((t - pl.tNum) / .45);
    ctx.save(); ctx.translate(540, 730); ctx.scale(lerp(.8, 1, clamp(pop)), lerp(.8, 1, clamp(pop))); ctx.globalAlpha *= a;
    const g = lg(-400, 0, 400, 0, [[0, C.blue], [1, C.tealL]]);
    T(txt, 0, 0, { font: FM(800, size), color: g, ls: 2, shadow: 30 }); ctx.restore();
    const la = A(t, pl.tNum + .5, .5);
    if (la > 0) {
      const lf = FM(800, fitSize(P.label, 800, 62, 800)); T(P.label.toUpperCase(), 540, 830, { font: lf, color: '#fff', ls: 4, alpha: la });
      rr(540 - 90, 862, 180, 8, 4); ctx.fillStyle = C.warm; ctx.globalAlpha *= la; ctx.fill(); ctx.globalAlpha /= la;
    }
    if (P.sub) { const sa = A(t, pl.tSub, .5); const lines = wrap(P.sub, 740, FM(500, 38)); lines.forEach((l, i) => T(l, 540, 940 + i * 52, { font: FM(500, 38), color: C.mute, alpha: sa })) }
    if (P.note) note(P.note, 1130, t, pl.tSub);
  },
  events(S) { const pl = this.plan(S); return [{ t: pl.tNum, kind: 'swoosh' }, { t: pl.tNum + 1.8, kind: 'ding' }] }
};

/* ---------------- NETWORK: data flowing through a neural net ---------------- */
SCENES.network = {
  plan(S) { return { tFwd: cue(S, 'forward', 1.2), tOut: cue(S, 'output', 4.5) } },
  draw(S, t) {
    const P = S.props, pl = this.plan(S), Ls = P.layers, nL = Ls.length;
    const x0 = 170, x1 = 910, top = 420, bot = 1000;
    const pos = Ls.map((n, li) => { const x = x0 + (x1 - x0) * li / (nL - 1), gap = Math.min(110, (bot - top) / Math.max(1, n - 1)), h = gap * (n - 1); return Array.from({ length: n }, (_, i) => ({ x, y: (top + bot) / 2 - h / 2 + i * gap })) });
    const ent = A(t, S.start + .1, .6), f = (t - pl.tFwd) / .6;      // f = layer index the wave has reached
    ctx.save(); ctx.globalAlpha *= ent;
    for (let l = 0; l < nL - 1; l++) {
      for (let i = 0; i < Ls[l]; i++) for (let j = 0; j < Ls[l + 1]; j++) {
        const w = H2(l * 97 + i * 13 + j, 5), a = pos[l][i], b = pos[l + 1][j], lit = clamp(f - l) * (.3 + .7 * H2(l * 31 + i * 7 + j, 6));
        ctx.strokeStyle = `rgba(${lerp(120, 92, lit) | 0},${lerp(170, 224, lit) | 0},${lerp(210, 181, lit) | 0},${.12 + .55 * lit * w})`; ctx.lineWidth = 1.2 + 3 * w * lit;
        ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
        const u = f - l; if (u > 0 && u < 1 && w > .45) { const px = lerp(a.x, b.x, u), py = lerp(a.y, b.y, u); ctx.fillStyle = C.warm; circ(px, py, 5); ctx.fill() }
      }
    }
    for (let l = 0; l < nL; l++) for (let i = 0; i < Ls[l]; i++) {
      const n = pos[l][i], act = sstep(f - l + 1) * (l === 0 ? 1 : .35 + .65 * H2(l * 53 + i, 9)), last = l === nL - 1;
      const isWin = last && P.outputs && i === (P.winner || 0), pop = eback((t - S.start - .15 - l * .12) / .35);
      ctx.save(); ctx.translate(n.x, n.y); ctx.scale(clamp(pop, 0, 1.2), clamp(pop, 0, 1.2));
      ctx.fillStyle = rg(0, 0, 0, 0, 0, 56, [[0, `rgba(92,224,181,${.55 * act})`], [1, 'rgba(92,224,181,0)']]); circ(0, 0, 56); ctx.fill();
      circ(0, 0, 32); ctx.fillStyle = lerpColor('#0F2D48', isWin && t > pl.tOut ? '#FFC857' : '#34B08A', clamp(act)); ctx.fill();
      ctx.lineWidth = 4; ctx.strokeStyle = `rgba(255,255,255,${.25 + .5 * act})`; ctx.stroke(); ctx.restore();
    }
    // layer labels
    (P.labels || []).forEach((lab, l) => T(lab.toUpperCase(), pos[l][0].x, bot + 90, { size: 22, ls: 3, color: C.mute }));
    // outputs: labels + confidence bars
    if (P.outputs) {
      const oa = A(t, pl.tOut, .5);
      P.outputs.forEach((o, i) => {
        const n = pos[nL - 1][i]; if (oa <= 0) return;
        ctx.save(); ctx.globalAlpha *= oa;
        const w = 200 * o.p * eo3((t - pl.tOut) / .8) ;
        T(o.label, n.x, n.y - 48, { font: mono(700, 34), color: i === (P.winner || 0) ? C.warm : '#fff' });
        rr(n.x - 100, n.y + 46, 200, 14, 7); ctx.fillStyle = 'rgba(255,255,255,.14)'; ctx.fill();
        rr(n.x - 100, n.y + 46, Math.max(14, w), 14, 7); ctx.fillStyle = i === (P.winner || 0) ? C.warm : C.blue; ctx.fill();
        T(Math.round(o.p * 100) + '%', n.x, n.y + 92, { font: mono(700, 28), color: '#fff' });
        ctx.restore();
      });
    }
    if (P.inputText) T(P.inputText, pos[0][0].x, top - 70, { font: mono(700, 34), color: C.tealL, alpha: ent });
    ctx.restore();
    if (P.note) note(P.note, 1215, t, pl.tOut);
  },
  events(S) {
    const pl = this.plan(S), ev = [{ t: pl.tFwd, kind: 'swoosh' }];
    for (let l = 1; l < S.props.layers.length; l++) ev.push({ t: pl.tFwd + l * .6, kind: 'tick' });
    ev.push({ t: pl.tOut, kind: 'ding' }); return ev;
  }
};

/* ---------------- CHAT: prompt + streamed reply, with flagged spans ---------------- */
SCENES.chat = {
  plan(S) {
    const P = S.props, n = P.messages.length, starts = P.messages.map((m, i) => cue2(S, m.cue, 1.0 + i * ((S.voice_end - S.start - 2) / n)));
    return { starts };
  },
  layout(S) {
    const P = S.props, f = FM(500, 38), maxW = 640, items = []; let y = 360;
    P.messages.forEach((m, i) => {
      const words = m.text.split(' '), lines = []; let cur = [];
      words.forEach((w, k) => { const trial = cur.concat([w]).join(' '); if (measure(trial, f) > maxW && cur.length) { lines.push(cur); cur = [w] } else cur.push(w) });
      if (cur.length) lines.push(cur);
      const h = lines.length * 54 + 56; items.push({ m, lines, y, h }); y += h + 34 + (m.flags && m.flags.length ? 50 : 0);
    });
    return items;
  },
  draw(S, t) {
    const P = S.props, pl = this.plan(S), items = this.layout(S), f = FM(500, 38);
    glass(70, 320, 940, 940, 44, .05);
    items.forEach((it, i) => {
      const t0 = pl.starts[i], a = A(t, t0, .35); if (a <= 0) return;
      const user = it.m.role === 'user', bw = 700, bx = user ? 1010 - 60 - bw : 70 + 60 + 70;
      ctx.save(); ctx.globalAlpha *= a; ctx.translate(user ? (1 - a) * 40 : -(1 - a) * 40, 0);
      // avatar
      const ax = user ? 1010 - 50 : 70 + 56; circ(ax, it.y + 36, 30); ctx.fillStyle = user ? C.blue : C.teal; ctx.fill(); T(user ? 'YOU' : 'AI', ax, it.y + 47, { size: user ? 19 : 24, color: C.ink, ls: 1 });
      const w = Math.max(...it.lines.map(l => measure(l.join(' '), f))) + 56, bx2 = user ? 1010 - 110 - w : 70 + 110;
      rr(bx2, it.y, w, it.h - 0, 30); ctx.fillStyle = user ? 'rgba(63,167,214,.9)' : 'rgba(255,255,255,.12)'; ctx.fill();
      if (!user) { ctx.lineWidth = 2; ctx.strokeStyle = 'rgba(255,255,255,.16)'; ctx.stroke() }
      // stream text word by word
      const total = it.m.text.length, shown = it.m.role === 'ai' && it.m.stream !== false ? Math.floor(clamp((t - t0 - .15) / (total / 34)) * total) : total;
      const flag = (it.m.flags || [])[0], fi = flag ? it.m.text.indexOf(flag.text) : -1; let used = 0;
      it.lines.forEach((ln, li) => {
        let x = bx2 + 28; const y = it.y + 28 + li * 54 + 36;
        ln.forEach(wd => {
          const start = used; used += wd.length + 1;
          const vis = clamp(shown - start, 0, wd.length); if (vis <= 0) return;
          const inFlag = fi >= 0 && start >= fi && start < fi + flag.text.length && shown >= total;
          const col = user ? C.ink : (inFlag ? (flag.kind === 'good' ? C.tealL : C.coral) : '#fff');
          const ww = measure(wd, f);
          if (inFlag) { ctx.fillStyle = flag.kind === 'good' ? 'rgba(52,176,138,.28)' : 'rgba(255,122,107,.25)'; rr(x - 6, y - 36, ww + 12, 48, 10); ctx.fill() }
          T(wd.slice(0, vis), x, y, { font: f, color: col, align: 'left' });
          x += ww + measure(' ', f);
        });
      });
      if (shown < total && !user) { const cx = bx2 + w - 22; T('▌', cx, it.y + it.h - 30, { font: f, color: C.tealL, alpha: .5 + .5 * Math.sin(t * 12) }) }
      if (flag && shown >= total) { const ta = A(t, t0 + .15 + total / 34, .4); if (ta > 0) { pill(bx2, it.y + it.h + 6, measure(flag.note, FM(800, 24), 2) + 40, 40, flag.kind === 'good' ? 'rgba(52,176,138,.3)' : 'rgba(255,122,107,.3)', null); T(flag.note, bx2 + 20, it.y + it.h + 34, { size: 24, ls: 2, color: flag.kind === 'good' ? C.tealL : C.coral, align: 'left', alpha: ta }) } }
      ctx.restore();
    });
  },
  events(S) {
    const pl = this.plan(S), ev = []; S.props.messages.forEach((m, i) => { ev.push({ t: pl.starts[i], kind: 'pop' });
      if (m.role === 'ai' && m.stream !== false) for (let k = 0; k < m.text.length; k += 4) ev.push({ t: pl.starts[i] + .15 + k / 34, kind: 'key' });
      if (m.flags && m.flags.length) ev.push({ t: pl.starts[i] + .15 + m.text.length / 34, kind: m.flags[0].kind === 'good' ? 'ding' : 'glitch' }) });
    return ev;
  }
};
function cue2(S, c, fb) { return c ? wordTime(S, c, S.start + fb) : S.start + fb }

/* ---------------- COMPARE: two ideas, three points each ---------------- */
SCENES.compare = {
  plan(S) { const d = S.voice_end - S.start; return { tL: cue(S, 'left', 1.0), tR: cue(S, 'right', d * .5), tV: cue(S, 'verdict', d - 2) } },
  draw(S, t) {
    const P = S.props, pl = this.plan(S);
    const panel = (side, y, t0, color, dir) => {
      const a = A(t, t0 - .2, .5); if (a <= 0) return;
      ctx.save(); ctx.globalAlpha *= a; ctx.translate(dir * (1 - a) * 80, 0);
      glass(90, y, 900, 370, 40, .08);
      rr(90, y, 14, 370, 7); ctx.fillStyle = color; ctx.fill();
      if (side.icon) icon(side.icon, 190, y + 70, 1.2, color);
      T(side.title, side.icon ? 250 : 140, y + 92, { font: FM(800, fitSize(side.title, 800, 58, side.icon ? 680 : 740)), color, align: 'left' });
      side.points.forEach((p, i) => {
        const pa = A(t, t0 + .5 + i * .85, .4); if (pa <= 0) return;
        ctx.save(); ctx.globalAlpha *= pa; ctx.translate((1 - pa) * 30, 0);
        circ(150, y + 168 + i * 76, 14); ctx.fillStyle = color; ctx.fill();
        const f = FM(500, 38), ls = wrap(p, 760, f); T(ls[0], 190, y + 181 + i * 76, { font: f, color: '#fff', align: 'left' });
        ctx.restore();
      });
      ctx.restore();
    };
    panel(P.left, 330, pl.tL, C.blue, -1); panel(P.right, 800, pl.tR, C.tealL, 1);
    const vb = A(t, pl.tR - .2, .4); if (vb > 0) { ctx.globalAlpha *= vb; circ(540, 755, 38); ctx.fillStyle = C.warm; ctx.fill(); T('VS', 540, 768, { size: 32, color: C.ink }); ctx.globalAlpha /= vb }
    if (P.verdict) { const va = A(t, pl.tV, .5); if (va > 0) { pill(90, 1196, 900, 80, 'rgba(255,200,87,.15)', C.warm); T(P.verdict, 540, 1250, { font: FM(800, fitSize(P.verdict, 800, 38, 840)), color: C.warm, alpha: va }) } }
  },
  events(S) { const pl = this.plan(S), ev = [{ t: pl.tL, kind: 'whoosh2' }, { t: pl.tR, kind: 'whoosh2' }];
    [pl.tL, pl.tR].forEach((t0, k) => (k ? S.props.right : S.props.left).points.forEach((_, i) => ev.push({ t: t0 + .5 + i * .85, kind: 'pop' })));
    if (S.props.verdict) ev.push({ t: pl.tV, kind: 'ding' }); return ev; }
};

/* ---------------- ANATOMY: the parts of a prompt ---------------- */
SCENES.anatomy = {
  plan(S) { return { t: cueSeq(S, 'p', S.props.parts.length, 1.0), tFoot: cue(S, 'footer', S.voice_end - S.start - 1.5) } },
  layout(S) {
    const f = mono(500, 34), items = []; let y = 440;
    S.props.parts.forEach(p => { const lines = wrap(p.text, 730, f); const h = 56 + lines.length * 48 + 24; items.push({ p, lines, y, h }); y += h + 22 });
    return { items, end: y };
  },
  draw(S, t) {
    const P = S.props, pl = this.plan(S), L = this.layout(S), f = mono(500, 34);
    const pa = A(t, S.start + .1, .5), bottom = Math.max(L.end + 10, 700);
    ctx.save(); ctx.globalAlpha *= pa; glass(80, 330, 920, bottom - 330, 36, .08);
    [C.coral, C.warm, C.teal].forEach((c, i) => { circ(122 + i * 30, 372, 9); ctx.fillStyle = c; ctx.fill() });
    T('prompt.txt', 540, 380, { font: mono(500, 24), color: C.mute }); ctx.restore();
    L.items.forEach((it, i) => {
      const t0 = pl.t[i], a = A(t, t0, .4); if (a <= 0) return; const col = ({ blue: C.blue, teal: C.teal, warm: C.warm, coral: C.coral, violet: C.violet, tealL: C.tealL })[it.p.color] || PAL[i % PAL.length];
      ctx.save(); ctx.globalAlpha *= a; ctx.translate((1 - a) * 50, 0);
      rr(120, it.y, 10, it.h - 8, 5); ctx.fillStyle = col; ctx.fill();
      const lw = measure(it.p.label, FM(800, 24), 3) + 36; pill(150, it.y, lw, 40, col, null); T(it.p.label.toUpperCase(), 150 + lw / 2, it.y + 28, { size: 24, ls: 3, color: C.ink });
      const total = it.p.text.length, shown = Math.floor(clamp((t - t0 - .2) / (total / 40)) * total); let used = 0;
      it.lines.forEach((ln, li) => { const k = clamp(shown - used, 0, ln.length); used += ln.length + 1; if (k > 0) T(ln.slice(0, k), 154, it.y + 82 + li * 48, { font: f, color: 'rgba(255,255,255,.94)', align: 'left' }) });
      ctx.restore();
    });
    if (P.footer) { const fa = A(t, pl.tFoot, .5); if (fa > 0) { const fy = bottom + 40; ctx.save(); ctx.globalAlpha *= fa; ctx.translate(0, (1 - fa) * 30); pill(540 - 330, fy, 660, 90, 'rgba(52,176,138,.2)', C.tealL); checkIcon(540 - 330 + 50, fy + 45, 24, (t - pl.tFoot - .1) / .4); T(P.footer, 540 + 20, fy + 60, { font: FM(800, fitSize(P.footer, 800, 40, 520)), color: C.tealL }); ctx.restore() } }
  },
  events(S) { const pl = this.plan(S), ev = pl.t.map(t => ({ t, kind: 'pop' })); if (S.props.footer) ev.push({ t: pl.tFoot, kind: 'ding' }); return ev }
};

/* ---------------- MAP: meaning as distance (embedding space) ---------------- */
SCENES.map = {
  plan(S) { return { tPts: cue(S, 'points', 1.0), tQ: cue(S, 'query', 4.0), tM: cue(S, 'match', 6.0) } },
  geom(S) {
    const P = S.props, X0 = 130, X1 = 950, Y0 = 400, Y1 = 1120, mp = p => ({ x: X0 + p.x * (X1 - X0), y: Y0 + p.y * (Y1 - Y0) });
    const pts = P.points.map(p => ({ ...p, ...mp(p) })), q = P.query ? { ...P.query, ...mp(P.query) } : null;
    let near = []; if (q) near = pts.map((p, i) => ({ i, d: Math.hypot(p.x - q.x, p.y - q.y) })).sort((a, b) => a.d - b.d).slice(0, P.k || 3).map(o => o.i);
    return { pts, q, near };
  },
  draw(S, t) {
    const P = S.props, pl = this.plan(S), G = this.geom(S), colors = [C.blue, C.coral, C.warm, C.violet, C.teal];
    glass(80, 350, 920, 790, 36, .06);
    ctx.save(); rr(80, 350, 920, 790, 36); ctx.clip();
    ctx.strokeStyle = 'rgba(255,255,255,.05)'; ctx.lineWidth = 2; for (let x = 80; x <= 1000; x += 92) { ctx.beginPath(); ctx.moveTo(x, 350); ctx.lineTo(x, 1140); ctx.stroke() } for (let y = 350; y <= 1140; y += 79) { ctx.beginPath(); ctx.moveTo(80, y); ctx.lineTo(1000, y); ctx.stroke() }
    const groups = {}; G.pts.forEach(p => { (groups[p.g] = groups[p.g] || []).push(p) });
    const matchA = A(t, pl.tM, .5), dim = 1 - .6 * matchA;
    Object.entries(groups).forEach(([g, arr]) => {
      const cx = arr.reduce((a, p) => a + p.x, 0) / arr.length, cy = arr.reduce((a, p) => a + p.y, 0) / arr.length, ha = A(t, pl.tPts + .6, .8);
      ctx.fillStyle = rg(cx, cy, 0, cx, cy, 150, [[0, lerpColor('#0A1F33', colors[g % 5], .35)], [1, 'rgba(10,31,51,0)']]); ctx.globalAlpha *= ha * .8; circ(cx, cy, 150); ctx.fill(); ctx.globalAlpha /= ha * .8;
      if (P.groups && P.groups[g] && ha > 0) T(P.groups[g].toUpperCase(), cx, cy - 78, { size: 20, ls: 3, color: colors[g % 5], alpha: ha * .85 });
    });
    G.pts.forEach((p, i) => {
      const e = eback((t - pl.tPts - i * .09) / .35); if (e <= 0) return;
      const isNear = G.near.includes(i) && t > pl.tM, col = colors[p.g % 5];
      ctx.save(); ctx.globalAlpha *= (isNear ? 1 : (t > pl.tM ? dim : 1)); ctx.translate(p.x, p.y); ctx.scale(clamp(e, 0, 1.3), clamp(e, 0, 1.3));
      if (isNear) { ctx.strokeStyle = C.warm; ctx.lineWidth = 5; circ(0, 0, 24 + 3 * Math.sin(t * 6)); ctx.stroke() }
      circ(0, 0, 14); ctx.fillStyle = col; ctx.fill(); T(p.label, 0, 46, { font: mono(700, 28), color: '#fff' }); ctx.restore();
    });
    if (G.q) {
      const qa = eback((t - pl.tQ) / .5);
      if (qa > 0) {
        G.near.forEach((i, k) => { const u = eo3((t - pl.tM - k * .2) / .5); if (u > 0) { ctx.strokeStyle = `rgba(255,200,87,${.9 * u})`; ctx.setLineDash([10, 8]); ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(G.q.x, G.q.y); ctx.lineTo(lerp(G.q.x, G.pts[i].x, u), lerp(G.q.y, G.pts[i].y, u)); ctx.stroke(); ctx.setLineDash([]) } });
        ctx.save(); ctx.translate(G.q.x, G.q.y); ctx.scale(clamp(qa, 0, 1.3), clamp(qa, 0, 1.3));
        ctx.fillStyle = rg(0, 0, 0, 0, 0, 60, [[0, 'rgba(255,200,87,.5)'], [1, 'rgba(255,200,87,0)']]); circ(0, 0, 60); ctx.fill();
        ctx.save(); ctx.rotate(t); icon('spark', 0, 0, .8, C.warm); ctx.restore(); T(G.q.label, 0, -40, { font: mono(700, 30), color: C.warm }); ctx.restore();
      }
    }
    ctx.restore();
    if (P.axisNote) note(P.axisNote, 1180, t, pl.tPts);
    if (P.matchLabel) { const ma = A(t, pl.tM + .5, .5); if (ma > 0) { pill(540 - 270, 1196, 540, 70, 'rgba(255,200,87,.16)', C.warm); T(P.matchLabel, 540, 1244, { size: 34, color: C.warm, alpha: ma }) } }
  },
  events(S) { const pl = this.plan(S), ev = []; S.props.points.forEach((_, i) => ev.push({ t: pl.tPts + i * .09 + .1, kind: 'pop' })); ev.push({ t: pl.tQ, kind: 'swoosh' }); ev.push({ t: pl.tM, kind: 'ding' }); return ev }
};

/* ---------------- FLOW: a pipeline, step by step ---------------- */
SCENES.flow = {
  plan(S) { return { t: cueSeq(S, 's', S.props.steps.length, .9) } },
  draw(S, t) {
    const P = S.props, pl = this.plan(S), n = P.steps.length, h = Math.min(150, (800 - (n - 1) * 56) / n), gap = 56, top = 340;
    const x0 = 150, w = 780, ys = P.steps.map((_, i) => top + i * (h + gap));
    P.steps.forEach((st, i) => {
      const t0 = pl.t[i], act = A(t, t0, .4), ent = A(t, S.start + .1 + i * .08, .45), y = ys[i];
      ctx.save(); ctx.globalAlpha *= ent; ctx.translate(0, (1 - ent) * 30);
      rr(x0, y, w, h, 32); ctx.fillStyle = lerpColor('#13304D', '#1B5E63', act); ctx.fill();
      ctx.lineWidth = 3 + 2 * act; ctx.strokeStyle = lerpColor('#2B4A66', '#5CE0B5', act); ctx.stroke();
      circ(x0 + 80, y + h / 2, 44); ctx.fillStyle = lerpColor('#1C3F5F', PAL[i % PAL.length], act); ctx.fill();
      icon(st.icon || 'gear', x0 + 80, y + h / 2, .95, lerpColor('#8FB3CC', '#08182A', act));
      const lf = FM(800, fitSize(st.label, 800, 46, w - 230)); T(st.label, x0 + 150, y + h / 2 + (st.sub ? -4 : 16), { font: lf, color: '#fff', align: 'left' });
      if (st.sub) T(st.sub, x0 + 150, y + h / 2 + 38, { font: FM(500, 28), color: C.mute, align: 'left', alpha: .9 });
      ctx.restore();
      if (i < n - 1) {                       // arrow + travelling packet
        const ax = 540, ay0 = y + h + 6, ay1 = ys[i + 1] - 8, aa = A(t, S.start + .3 + i * .08, .4);
        ctx.strokeStyle = `rgba(255,255,255,${.25 * aa})`; ctx.lineWidth = 5; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(ax, ay0); ctx.lineTo(ax, ay1 - 8); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(ax - 12, ay1 - 16); ctx.lineTo(ax, ay1); ctx.lineTo(ax + 12, ay1 - 16); ctx.stroke();
        const u = (t - pl.t[i + 1] + .45) / .5; if (u > 0 && u < 1) { ctx.fillStyle = C.warm; circ(ax, lerp(ay0, ay1, eo3(u)), 9); ctx.fill() }
      }
    });
    if (P.loop) {
      const la = A(t, pl.t[n - 1] + .4, .6); if (la > 0) {
        ctx.save(); ctx.globalAlpha *= la; ctx.strokeStyle = C.warm; ctx.lineWidth = 5; ctx.setLineDash([14, 10]); ctx.lineDashOffset = -t * 40; ctx.lineCap = 'round';
        const yb = ys[n - 1] + h / 2, yt = ys[0] + h / 2, rx = x0 + w + 40; ctx.beginPath(); ctx.moveTo(x0 + w + 6, yb); ctx.bezierCurveTo(rx + 80, yb, rx + 80, yt, x0 + w + 6, yt); ctx.stroke(); ctx.setLineDash([]);
        ctx.beginPath(); ctx.moveTo(x0 + w + 24, yt - 16); ctx.lineTo(x0 + w + 4, yt); ctx.lineTo(x0 + w + 24, yt + 16); ctx.stroke();
        T('repeat', rx + 92, (yb + yt) / 2, { size: 26, color: C.warm, ls: 2 }); ctx.restore();
      }
    }
    if (P.note) note(P.note, 1200, t, pl.t[n - 1]);
  },
  events(S) { const pl = this.plan(S); return pl.t.flatMap((t, i) => [{ t, kind: i ? 'flip' : 'pop' }]).concat(S.props.loop ? [{ t: pl.t[pl.t.length - 1] + .4, kind: 'swoosh' }] : []) }
};
