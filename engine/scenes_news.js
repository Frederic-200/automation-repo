/* ============================================================
   FredsDesk NEWS: sub-brand look + news scene types.
   Same navy / fonts / logo as the lessons, plus a coral NEWS tag,
   pulsing live dot, date stamp and a scrolling headline ticker.
   Same contract as scenes.js: SCENES.<type> = { plan, draw, events }.
   ============================================================ */
const MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
function dateStamp(d) { const m = /^(\d{4})-(\d\d)-(\d\d)$/.exec(d || ''); return m ? `${MONTHS[+m[2] - 1]} ${+m[3]} · ${m[1]}` : '' }

/* ---------- backdrop, chrome, ticker ---------- */
function drawNewsBackdrop(t) {
  ctx.fillStyle = rg(900, 260, 0, 900, 260, 760, [[0, `rgba(255,122,107,${.10 + .02 * Math.sin(t * 1.3)})`], [1, 'rgba(255,122,107,0)']]); ctx.fillRect(0, 0, W, H);
}
function drawChromeNews(t, TL) {
  const a = sstep((t - .3) / .4);
  if (a > 0) {
    ctx.save(); ctx.globalAlpha *= a;
    pill(60, 92, 188, 54, 'rgba(255,122,107,.16)', 'rgba(255,122,107,.65)');
    const pulse = .55 + .45 * Math.sin(t * 5.2);
    ctx.fillStyle = rg(94, 119, 0, 94, 119, 24, [[0, `rgba(255,122,107,${.8 * pulse})`], [1, 'rgba(255,122,107,0)']]); circ(94, 119, 24); ctx.fill();
    circ(94, 119, 8.5); ctx.fillStyle = C.coral; ctx.fill();
    T('NEWS', 122, 129, { size: 26, ls: 4, color: C.coral, align: 'left' });
    T(dateStamp(TL.date), 272, 128, { size: 22, font: FM(500, 22), ls: 3, align: 'left', color: C.mute });
    drawLogo(768, 119, .15, 1, { a: 1, dx: 0, dy: 0, s: 1 });
    T('FredsDesk', 1020, 130, { size: 30, align: 'right', color: '#fff' });
    const bx = 60, bw = 960, by = 176, p = clamp(t / TL.duration);
    rr(bx, by, bw, 7, 4); ctx.fillStyle = 'rgba(255,255,255,.14)'; ctx.fill();
    rr(bx, by, Math.max(7, bw * p), 7, 4); ctx.fillStyle = lg(bx, 0, bx + bw, 0, [[0, C.coral], [1, C.warm]]); ctx.fill();
    ctx.fillStyle = rg(bx + bw * p, by + 3, 0, bx + bw * p, by + 3, 22, [[0, 'rgba(255,200,87,.9)'], [1, 'rgba(255,200,87,0)']]); circ(bx + bw * p, by + 3, 22); ctx.fill();
    ctx.restore();
  }
  drawTicker(t, TL, a);
}
function drawTicker(t, TL, a) {
  const items = TL.ticker && TL.ticker.length ? TL.ticker : []; if (!items.length || a <= 0) return;
  const y = 1528, h = 58, f = FM(800, 28), sep = '   ◆   ';
  const str = items.map(s => s.toUpperCase()).join(sep) + sep, w = measure(str, f, 2);
  ctx.save(); ctx.globalAlpha *= a;
  ctx.fillStyle = 'rgba(255,122,107,.10)'; ctx.fillRect(0, y, W, h);
  ctx.fillStyle = 'rgba(255,122,107,.5)'; ctx.fillRect(0, y, W, 2); ctx.fillRect(0, y + h - 2, W, 2);
  ctx.save(); ctx.beginPath(); ctx.rect(236, y, W - 236, h); ctx.clip();
  const off = (t * 110) % w;
  for (let k = -1; k < 3; k++) T(str, 236 + k * w - off, y + 39, { font: f, color: 'rgba(255,255,255,.82)', align: 'left', ls: 2 });
  ctx.restore();
  ctx.fillStyle = C.coral; ctx.fillRect(0, y, 220, h);
  T('AI NEWS', 110, y + 39, { size: 28, ls: 4, color: C.ink });
  ctx.restore();
}

/* ---------- shared bits ---------- */
function heartPath(x, y, s) {
  ctx.beginPath(); ctx.moveTo(x, y + .9 * s);
  ctx.bezierCurveTo(x - 1.6 * s, y - .2 * s, x - .9 * s, y - 1.3 * s, x, y - .5 * s);
  ctx.bezierCurveTo(x + .9 * s, y - 1.3 * s, x + 1.6 * s, y - .2 * s, x, y + .9 * s); ctx.closePath();
}
function shareIcon(x, y, s, color, lw = 9) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.strokeStyle = color; ctx.lineWidth = lw / s * s; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.beginPath(); ctx.moveTo(-34, -2); ctx.lineTo(-34, 38); ctx.lineTo(34, 38); ctx.lineTo(34, -2); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(0, 24); ctx.lineTo(0, -44); ctx.moveTo(-22, -22); ctx.lineTo(0, -44); ctx.lineTo(22, -22); ctx.stroke();
  ctx.restore();
}
function cursorAt(x, y, sc, a) {
  ctx.save(); ctx.globalAlpha *= a; ctx.translate(x, y); ctx.scale(sc * 1.9, sc * 1.9);
  ctx.fillStyle = '#fff'; ctx.strokeStyle = C.ink; ctx.lineWidth = 2; ctx.beginPath();
  LOGO.cursor.forEach(([px, py], k) => { const qx = px - 724, qy = py - 203; k ? ctx.lineTo(qx, qy) : ctx.moveTo(qx, qy) });
  ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.restore();
}
function typeText(lines, x, y0, lh, font, color, t, t0, dur, o = {}) {
  const total = lines.join(' ').length, n = Math.floor(clamp((t - t0) / dur) * total); let used = 0;
  lines.forEach((ln, i) => { const k = clamp(n - used, 0, ln.length); used += ln.length + 1; if (k > 0) T(ln.slice(0, k), x, y0 + i * lh, Object.assign({ font, color, align: o.align || 'left' }, o)) });
  return n < total;
}
function followButton(bx, by, t, tF) {
  const clicked = t > tF + .55, bw = 420, press = t > tF + .5 && t < tF + .64 ? .94 : 1;
  ctx.save(); ctx.translate(bx, by); ctx.scale(press, press);
  pill(-bw / 2, -50, bw, 100, clicked ? 'rgba(255,122,107,.22)' : C.coral, clicked ? C.coral : null);
  T(clicked ? 'Following ✓' : 'Follow', 0, 20, { size: 46, color: clicked ? C.coral : C.ink });
  ctx.restore();
  const cu = clamp((t - (tF - .2)) / .7);
  if (t > tF - .3 && t < tF + 1.6) {
    const ca = clamp((t - (tF - .3)) / .2) * (1 - clamp((t - (tF + 1.2)) / .4)), cs = (t > tF + .5 && t < tF + .64) ? .8 : 1;
    cursorAt(lerp(bx + 330, bx + 70, eo3(cu)), lerp(by + 250, by + 30, eo3(cu)), cs, ca);
  }
  ripple(bx + 70, by + 30, t, tF + .55, .7, 110);
}

/* ---------------- BREAKING: opener ---------------- */
SCENES.breaking = {
  plan(S) {
    const n = S.props.lines.length, d = S.voice_end - S.start;
    return { l: cueSeq(S, 'l', n, 1.1, Math.max(2, d - 2.2)), tSrc: cue(S, 'source', Math.max(2.5, d - 1.6)) };
  },
  draw(S, t) {
    const P = S.props, pl = this.plan(S), t0 = S.start;
    const sw = eo3((t - t0) / .55);                                    // coral wipe
    if (sw > 0 && sw < 1) { ctx.fillStyle = `rgba(255,122,107,${.5 * (1 - sw)})`; ctx.fillRect(-W + sw * 2 * W, 330, W, 22) }
    const ka = A(t, t0 + .05, .4);
    if (ka > 0) {
      ctx.save(); ctx.globalAlpha *= ka; ctx.translate(0, (1 - ka) * 30);
      const kt = (P.kicker || 'DID YOU KNOW?').toUpperCase(), kw = measure(kt, FM(800, 46), 8) + 90;
      pill(540 - kw / 2, 360, kw, 84, 'rgba(255,122,107,.18)', C.coral); T(kt, 540, 418, { size: 46, ls: 8, color: C.coral });
      ctx.restore();
    }
    P.lines.forEach((ln, i) => {
      const acc = i === P.accent, a = A(t, pl.l[i] - .1, .4), size = fitSize(ln, 800, acc ? 124 : 92, 940, false, 1), y = 590 + i * 156 + (1 - a) * 60;
      if (a <= 0) return;
      const col = acc ? lg(140, 0, 940, 0, [[0, C.coral], [.55, C.warm], [1, C.warm]]) : '#FFFFFF';
      if (acc && t - pl.l[i] < .4) {
        const g = 1 - (t - pl.l[i]) / .4, j = Math.sin(t * 90) * 14 * g;
        T(ln, 540 + j, y, { size, color: 'rgba(63,167,214,.8)', alpha: a * .8 * g, ls: 1 }); T(ln, 540 - j, y, { size, color: 'rgba(255,122,107,.8)', alpha: a * .8 * g, ls: 1 });
      }
      T(ln, 540, y, { size, color: col, alpha: a, ls: 1, shadow: 20 });
      if (acc) { const u = eo3((t - pl.l[i] - .25) / .45), w = measure(ln, FM(800, size), 1); if (u > 0) { rr(540 - w / 2, y + 26, w * u, 10, 5); ctx.fillStyle = C.coral; ctx.fill() } }
    });
    if (P.source) { const sa = A(t, pl.tSrc, .5); if (sa > 0) { pill(540 - 250, 1170, 500, 76, 'rgba(255,255,255,.07)', 'rgba(255,255,255,.2)'); T('via ' + P.source, 540, 1220, { font: FM(500, 34), color: C.mute, alpha: sa }) } }
  },
  events(S) { const pl = this.plan(S), ev = [{ t: S.start + .02, kind: 'stinger' }]; pl.l.forEach((t, i) => ev.push({ t, kind: i === S.props.accent ? 'glitch' : 'pop' })); ev.push({ t: pl.tSrc, kind: 'whoosh2' }); return ev }
};

/* ---------------- STORY: the article card ---------------- */
SCENES.story = {
  plan(S) {
    const n = (S.props.facts || []).length, d = S.voice_end - S.start;
    return { tHead: cue(S, 'headline', .5), f: cueSeq(S, 'f', n, 2.4, Math.max(3, d - 1.2)) };
  },
  draw(S, t) {
    const P = S.props, pl = this.plan(S), hf = FM(800, 54), lines = wrap(P.headline, 800, hf), facts = P.facts || [];
    const yF = 560 + lines.length * 66, bottom = yF + facts.length * 138 + 30;
    const ca = A(t, S.start + .05, .45); ctx.save(); ctx.globalAlpha *= ca; ctx.translate(0, (1 - ca) * 40);
    glass(70, 350, 940, bottom - 350, 44, .08); rr(70, 350, 14, bottom - 350, 7); ctx.fillStyle = C.coral; ctx.fill();
    const sf = FM(800, 26), sw = measure((P.source || '').toUpperCase(), sf, 3) + 50;
    pill(120, 392, sw, 52, 'rgba(255,122,107,.16)', 'rgba(255,122,107,.6)'); T((P.source || '').toUpperCase(), 120 + sw / 2, 428, { size: 26, ls: 3, color: C.coral });
    if (P.when) T(P.when, 980, 428, { font: mono(500, 28), color: C.mute, align: 'right' });
    typeText(lines, 120, 520, 66, hf, '#fff', t, pl.tHead, 1.5, { shadow: 12 });
    ctx.restore();
    facts.forEach((f, i) => {
      const a = eback((t - pl.f[i] + .1) / .4); if (a <= 0) return;
      const y = yF + i * 138, s = clamp(a, 0, 1.1);
      ctx.save(); ctx.translate(540, y + 52); ctx.scale(lerp(.9, 1, clamp(a)), lerp(.9, 1, clamp(a))); ctx.translate(-540, -(y + 52)); ctx.globalAlpha *= clamp(a);
      glass(110, y, 860, 108, 30, .1); circ(172, y + 54, 30); ctx.fillStyle = PAL[(i + 3) % PAL.length]; ctx.fill();
      T(String(i + 1), 172, y + 70, { size: 36, color: C.ink });
      const ff = FM(500, fitSize(f, 500, 40, 700)); T(f, 224, y + 66, { font: ff, align: 'left', color: '#fff' });
      ctx.restore();
    });
  },
  events(S) { const pl = this.plan(S); return [{ t: S.start + .1, kind: 'swoosh' }].concat(pl.f.map(t => ({ t, kind: 'pop' }))) }
};

/* ---------------- QUOTE ---------------- */
SCENES.quote = {
  plan(S) { return { tQ: cue(S, 'quote', .8), tWho: cue(S, 'who', Math.max(3, S.voice_end - S.start - 2)) } },
  draw(S, t) {
    const P = S.props, pl = this.plan(S), qf = FM(800, 56), lines = wrap(P.text, 760, qf), h = 530 + lines.length * 76;
    const ca = A(t, S.start + .05, .45); ctx.save(); ctx.globalAlpha *= ca; ctx.translate(0, (1 - ca) * 40);
    glass(90, 380, 900, h, 44, .08);
    T('“', 175, 640, { size: 300, color: C.coral, alpha: .9 });
    ctx.restore();
    typeText(lines, 150, 700, 76, qf, '#fff', t, pl.tQ, Math.min(4, 0.6 + lines.join(' ').length * .045), { shadow: 12 });
    const wa = A(t, pl.tWho, .5);
    if (wa > 0) {
      const y = 700 + lines.length * 76 + 40; ctx.save(); ctx.globalAlpha *= wa;
      rr(150, y, 80 * wa, 8, 4); ctx.fillStyle = C.coral; ctx.fill();
      T('— ' + P.who, 150, y + 70, { font: FM(800, 44), align: 'left', color: C.warm });
      if (P.role) T(P.role, 150, y + 120, { font: FM(500, 32), align: 'left', color: C.mute });
      ctx.restore();
    }
  },
  events(S) { const pl = this.plan(S); return [{ t: S.start + .1, kind: 'swoosh' }, { t: pl.tWho, kind: 'pop' }] }
};

/* ---------------- TIMELINE ---------------- */
SCENES.timeline = {
  plan(S) { return { e: cueSeq(S, 'e', S.props.events.length, 0.9, Math.max(3, S.voice_end - S.start - 1.5)) } },
  draw(S, t) {
    const P = S.props, pl = this.plan(S), n = P.events.length, x = 190, y0 = 440, gap = Math.min(220, 800 / n);
    T(P.title || 'TIMELINE', 540, 392, { size: 40, ls: 10, color: C.coral, alpha: A(t, S.start + .1, .4) });
    const prog = clamp((t - pl.e[0] + .2) / Math.max(.5, pl.e[n - 1] - pl.e[0] + .6));
    rr(x - 3, y0, 6, (n - 1) * gap * prog, 3); ctx.fillStyle = 'rgba(255,122,107,.6)'; ctx.fill();
    P.events.forEach((ev, i) => {
      const a = eback((t - pl.e[i] + .1) / .4); if (a <= 0) return;
      const y = y0 + i * gap; ctx.save(); ctx.globalAlpha *= clamp(a); ctx.translate((1 - clamp(a)) * 60, 0);
      const hot = Math.max(0, 1 - Math.abs(t - pl.e[i] - .2) / .8);
      ctx.fillStyle = rg(x, y, 0, x, y, 54, [[0, `rgba(255,122,107,${.5 * hot})`], [1, 'rgba(255,122,107,0)']]); circ(x, y, 54); ctx.fill();
      circ(x, y, 22 + 4 * hot); ctx.fillStyle = i === n - 1 ? C.warm : C.coral; ctx.fill(); circ(x, y, 22); ctx.lineWidth = 5; ctx.strokeStyle = C.bg; ctx.stroke();
      T(ev.when, 250, y - 8, { font: mono(700, 36), align: 'left', color: i === n - 1 ? C.warm : C.coral });
      const f = FM(500, 40); wrap(ev.what, 720, f).slice(0, 2).forEach((l, k) => T(l, 250, y + 44 + k * 50, { font: f, align: 'left', color: '#fff' }));
      ctx.restore();
    });
  },
  events(S) { return this.plan(S).e.map(t => ({ t, kind: 'tick' })) }
};

/* ---------------- WHY IT MATTERS ---------------- */
SCENES.why = {
  plan(S) { return { p: cueSeq(S, 'p', S.props.points.length, 1.2, Math.max(3, S.voice_end - S.start - 2)) } },
  draw(S, t) {
    const P = S.props, pl = this.plan(S), icons = P.icons || ['bolt', 'target', 'user', 'spark'];
    T('WHY IT MATTERS', 540, 410, { size: 50, ls: 8, color: C.warm, alpha: A(t, S.start + .1, .4) });
    P.points.forEach((p, i) => {
      const a = A(t, pl.p[i] - .1, .5), y = 480 + i * 250; if (a <= 0) return;
      ctx.save(); ctx.globalAlpha *= a; ctx.translate((1 - a) * 90, 0);
      glass(90, y, 900, 210, 36, .09); rr(90, y, 12, 210, 6); ctx.fillStyle = PAL[(i + 3) % PAL.length]; ctx.fill();
      circ(185, y + 105, 52); ctx.fillStyle = 'rgba(255,255,255,.08)'; ctx.fill();
      icon(icons[i % icons.length], 185, y + 105, 1.05, PAL[(i + 3) % PAL.length]);
      const f = FM(800, 44), lines = wrap(p, 640, f);
      lines.slice(0, 3).forEach((l, k) => T(l, 270, y + 105 + (k - (Math.min(3, lines.length) - 1) / 2) * 54 + 15, { font: f, align: 'left', color: '#fff' }));
      ctx.restore();
    });
  },
  events(S) { return this.plan(S).p.flatMap(t => [{ t, kind: 'whoosh2' }, { t: t + .35, kind: 'pop' }]) }
};

/* ---------------- ENGAGE: mid-video like + share ---------------- */
SCENES.engage = {
  plan(S) { const d = S.voice_end - S.start; return { tLike: cue(S, 'like', d * .4), tShare: cue(S, 'share', d * .75) } },
  draw(S, t) {
    const P = S.props, pl = this.plan(S), ea = A(t, S.start + .05, .45);
    ctx.save(); ctx.globalAlpha *= ea; ctx.translate(0, (1 - ea) * 40);
    const btn = (cx, cy, tC, kind) => {
      const u = t - tC, done = u > 0, bounce = done ? 1 + .22 * Math.exp(-u * 5) * Math.cos(u * 18) : 1 + .02 * Math.sin(t * 3);
      ctx.save(); ctx.translate(cx, cy); ctx.scale(bounce, bounce);
      circ(0, 0, 128); ctx.fillStyle = done ? (kind === 'like' ? 'rgba(255,122,107,.22)' : 'rgba(63,167,214,.22)') : 'rgba(255,255,255,.08)'; ctx.fill();
      ctx.lineWidth = 5; ctx.strokeStyle = done ? (kind === 'like' ? C.coral : C.blue) : 'rgba(255,255,255,.3)'; ctx.stroke();
      if (kind === 'like') { heartPath(0, -4, 62); if (done) { ctx.fillStyle = C.coral; ctx.fill() } else { ctx.lineWidth = 9; ctx.strokeStyle = 'rgba(255,255,255,.75)'; ctx.lineJoin = 'round'; ctx.stroke() } }
      else shareIcon(0, 0, 1.15, done ? C.blue : 'rgba(255,255,255,.75)');
      ctx.restore();
      if (done && u < 1.1) for (let k = 0; k < 14; k++) {      // burst
        const ang = H2(k, 3) * TAU, r = 150 + eo3(u / 1.0) * (110 + 120 * H2(k, 5)), s = (1 - clamp(u / 1.1)) * (8 + 8 * H2(k, 7));
        ctx.globalAlpha = ea * (1 - clamp(u / 1.1)); ctx.fillStyle = [C.coral, C.warm, C.tealL, C.blue][k % 4]; circ(cx + Math.cos(ang) * r, cy + Math.sin(ang) * r, s); ctx.fill(); ctx.globalAlpha = ea;
      }
      ripple(cx, cy, t, tC, .7, 150);
      T(kind === 'like' ? 'LIKE' : 'SHARE', cx, cy + 205, { size: 34, ls: 6, color: done ? '#fff' : C.mute });
    };
    btn(350, 640, pl.tLike, 'like'); btn(730, 640, pl.tShare, 'share');
    const lf = FM(800, 58), lines = wrap(P.line, 860, lf);
    lines.forEach((l, i) => T(l, 540, 1010 + i * 72, { font: lf, color: '#fff', shadow: 14 }));
    if (P.sub) T(P.sub, 540, 1010 + lines.length * 72 + 20, { font: FM(500, 36), color: C.warm });
    ctx.restore();
    const cl = (tc, x) => { const cu = clamp((t - (tc - .7)) / .6); if (t > tc - .8 && t < tc + 1.0) cursorAt(lerp(x + 260, x + 50, eo3(cu)), lerp(840, 690, eo3(cu)), t > tc && t < tc + .14 ? .8 : 1, clamp((t - (tc - .8)) / .2) * (1 - clamp((t - (tc + .7)) / .3))) };
    cl(pl.tLike, 350); cl(pl.tShare, 730);
  },
  events(S) { const pl = this.plan(S); return [{ t: S.start + .1, kind: 'swoosh' }, { t: pl.tLike, kind: 'click' }, { t: pl.tLike + .06, kind: 'thump' }, { t: pl.tShare, kind: 'click' }, { t: pl.tShare + .06, kind: 'ding' }] }
};

/* ---------------- TAKEAWAYS ---------------- */
SCENES.takeaways = {
  plan(S) { return { t: cueSeq(S, 'p', S.props.points.length, 1.2, Math.max(3, S.voice_end - S.start - 1.8)) } },
  draw(S, t) {
    const P = S.props, pl = this.plan(S);
    T('KEY TAKEAWAYS', 540, 400, { size: 50, ls: 8, color: C.coral, alpha: A(t, S.start + .1, .4) });
    P.points.forEach((p, i) => {
      const a = A(t, pl.t[i], .5), y = 470 + i * 250; if (a <= 0) return;
      ctx.save(); ctx.globalAlpha *= a; ctx.translate((1 - a) * 90, 0);
      glass(90, y, 900, 210, 36, .09);
      circ(180, y + 105, 48); ctx.fillStyle = PAL[(i + 3) % PAL.length]; ctx.fill(); T(String(i + 1), 180, y + 125, { size: 56, color: C.ink });
      const f = FM(800, 44), lines = wrap(p, 560, f);
      lines.slice(0, 3).forEach((l, k) => T(l, 262, y + 105 + (k - (Math.min(3, lines.length) - 1) / 2) * 54 + 15, { font: f, align: 'left', color: '#fff' }));
      checkIcon(900, y + 105, 38, (t - pl.t[i] - .35) / .4, C.warm);
      ctx.restore();
    });
  },
  events(S) { return this.plan(S).t.flatMap(t => [{ t, kind: 'whoosh2' }, { t: t + .55, kind: 'ding' }]) }
};

/* ---------------- SOURCES + FOLLOW (outro) ---------------- */
SCENES.sources_end = {
  plan(S) { const d = S.voice_end - S.start; return { tSrc: cue(S, 'sources', 1.0), tFollow: cue(S, 'follow', Math.max(3, d - 2.2)) } },
  draw(S, t) {
    const P = S.props, pl = this.plan(S), src = (P.sources || []).slice(0, 3);
    drawLogo(540, 470, 1.0, clamp((t - S.start - .1) / 1.0), { a: 0, dx: 0, dy: 0, s: 1 });
    wordmark(540, 735, 88, clamp((t - S.start - .5) / .9));
    const na = A(t, S.start + 1.1, .4);
    if (na > 0) { ctx.save(); ctx.globalAlpha *= na; pill(540 - 90, 770, 180, 62, 'rgba(255,122,107,.2)', C.coral); T('NEWS', 540, 814, { size: 34, ls: 8, color: C.coral }); ctx.restore() }
    T('Daily AI news, explained', 540, 890, { font: FM(500, 34), color: C.mute, alpha: A(t, S.start + 1.3, .5) });
    const sa = A(t, pl.tSrc, .5);
    if (sa > 0 && src.length) {
      ctx.save(); ctx.globalAlpha *= sa; ctx.translate(0, (1 - sa) * 30);
      const h = 90 + src.length * 66; glass(120, 940, 840, h, 36, .08); label('SOURCES', 540, 992, C.warm, 'center');
      src.forEach((s, i) => { const a = A(t, pl.tSrc + .25 + i * .3, .4); ctx.save(); ctx.globalAlpha *= a; checkIcon(190, 1043 + i * 66, 18, a, C.tealL); T(s, 235, 1056 + i * 66, { font: FM(500, fitSize(s, 500, 38, 660)), align: 'left', color: '#fff' }); ctx.restore() });
      ctx.restore();
    }
    followButton(540, 1282, t, pl.tFollow);
  },
  events(S) { const pl = this.plan(S); return [{ t: S.start + .1, kind: 'draw' }, { t: pl.tSrc, kind: 'swoosh' }, { t: pl.tFollow + .55, kind: 'click' }, { t: pl.tFollow + .75, kind: 'ding' }] }
};
