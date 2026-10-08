/* ============================================================
   Motion layer shared by lessons and news:
   living background, camera (push-in, drift, beat punches),
   scene transitions, kinetic typography, card draw-on + shine.
   Everything is a pure function of t (frames render out of order).
   ============================================================ */
let FX = null;                                  // {t, t0, accent} while a scene is drawn
const ACCENT = { lesson: [92, 224, 181], news: [255, 122, 107] };
const rgba = (c, a) => `rgba(${c[0]},${c[1]},${c[2]},${a})`;

/* ---------- glass card with border draw-on + shine sweep (replaces brand.js glass) ---------- */
function glass(x, y, w, h, r = 36, a = .07, t0) {
  rr(x, y, w, h, r); ctx.fillStyle = `rgba(255,255,255,${a})`; ctx.fill();
  ctx.lineWidth = 2;
  if (!FX) { ctx.strokeStyle = 'rgba(255,255,255,.13)'; ctx.stroke(); return }
  const st = t0 === undefined ? FX.t0 + .05 : t0, u = FX.t - st, per = 2 * (w + h), p = eio(clamp(u / .75));
  if (p >= 1) { ctx.strokeStyle = 'rgba(255,255,255,.13)'; ctx.stroke() }
  else if (p > 0) {
    ctx.setLineDash([per * p, per]); ctx.strokeStyle = rgba(FX.accent, .9 * (1 - p) + .13); ctx.lineWidth = 3; ctx.stroke(); ctx.setLineDash([]);
  }
  if (u > .1 && u < 1.2) {                       // diagonal light sweep across the card
    const e = eio((u - .1) / 1.0), bx = x - 260 + (w + 520) * e;
    ctx.save(); rr(x, y, w, h, r); ctx.clip();
    ctx.translate(bx, y + h / 2); ctx.rotate(.38);
    ctx.fillStyle = lg(-90, 0, 90, 0, [[0, 'rgba(255,255,255,0)'], [.5, 'rgba(255,255,255,.16)'], [1, 'rgba(255,255,255,0)']]);
    ctx.fillRect(-90, -h - 300, 180, 2 * h + 600); ctx.restore();
  }
}

/* ---------- camera: slow push-in, drift, small roll, punch on beats ---------- */
const PUNCH_KINDS = { pop: .018, ding: .02, swoosh: .022, click: .025, brick: .03, thump: .035, glitch: .03, stinger: .03, split: .025 };
function sceneEvents(S) { if (!S._ev) S._ev = SCENES[S.type].events(S).filter(e => PUNCH_KINDS[e.kind]); return S._ev }
function camera(S, t) {
  const d = Math.max(1, S.end - S.start), p = clamp((t - S.start) / d);
  let punch = 0;
  for (const e of sceneEvents(S)) { const u = t - e.t; if (u >= 0 && u < 1.2) punch += PUNCH_KINDS[e.kind] * Math.exp(-u * 7) * (1 - u / 1.2) }
  return { z: 1 + .03 * eio(p) + Math.min(.035, punch), dx: 11 * Math.sin(t * .37 + S.i * 1.3), dy: 8 * Math.sin(t * .29 + 1.3 + S.i), rot: .006 * Math.sin(t * .23 + S.i * 1.7) };
}
function withCam(S, t, fn) {
  const c = camera(S, t);
  ctx.save(); ctx.translate(540 + c.dx, 820 + c.dy); ctx.rotate(c.rot); ctx.scale(c.z, c.z); ctx.translate(-540, -820);
  const prev = FX; FX = { t, t0: S.start, accent: prev ? prev.accent : ACCENT.lesson }; fn(); FX = prev;
  ctx.restore();
}

/* ---------- living background: glows, light beams, data lines, parallax particles ---------- */
function livingBackground(t, kind, cam) {
  const ac = ACCENT[kind] || ACCENT.lesson, bl = [63, 167, 214];
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  [[ac, .09, 0], [bl, .07, 2.1]].forEach(([c, a, ph]) => {
    const x = 540 + 330 * Math.sin(t * .11 + ph) - cam.dx * .3, y = 820 + 420 * Math.sin(t * .073 + ph * 1.7) - cam.dy * .3;
    ctx.fillStyle = rg(x, y, 0, x, y, 720, [[0, rgba(c, a)], [1, rgba(c, 0)]]); ctx.fillRect(0, 0, W, H);
  });
  for (let i = 0; i < 3; i++) {                   // slow diagonal light beams
    const span = W + 900, x = ((H2(i, 11) * span + t * (26 + 14 * i)) % span) - 450 - cam.dx * .5;
    ctx.save(); ctx.translate(x, H / 2); ctx.rotate(-.42);
    ctx.fillStyle = lg(-110, 0, 110, 0, [[0, rgba(i === 1 ? bl : ac, 0)], [.5, rgba(i === 1 ? bl : ac, .055)], [1, rgba(i === 1 ? bl : ac, 0)]]);
    ctx.fillRect(-110, -H, 220, 2 * H); ctx.restore();
  }
  for (let i = 0; i < 3; i++) {                   // flowing data lines + travelling dots
    const base = 470 + i * 430 - cam.dy * .6, Y = x => base + 38 * Math.sin(x * .006 + t * .55 + i * 2) + 18 * Math.sin(x * .014 - t * .38 + i);
    ctx.strokeStyle = rgba(i === 1 ? bl : ac, .085); ctx.lineWidth = 2; ctx.beginPath();
    for (let x = -20; x <= W + 20; x += 30) x < 0 ? ctx.moveTo(x, Y(x)) : ctx.lineTo(x, Y(x)); ctx.stroke();
    for (let k = 0; k < 2; k++) {
      const x = ((t * (110 + 40 * i) + k * 560 + i * 200) % (W + 120)) - 60, y = Y(x);
      ctx.fillStyle = rg(x, y, 0, x, y, 26, [[0, rgba(ac, .55)], [1, rgba(ac, 0)]]); circ(x, y, 26); ctx.fill();
      ctx.fillStyle = rgba([255, 255, 255], .8); circ(x, y, 3.2); ctx.fill();
    }
  }
  for (let n = 0; n < 72; n++) {                  // three depth layers of particles (parallax with the camera)
    const depth = (n % 3 + 1) / 3, x = ((H2(n, 1) * W - cam.dx * depth * 2.2) % W + W) % W;
    const y = ((H2(n, 2) * H - t * (10 + 26 * depth) - cam.dy * depth * 2.2) % H + H) % H;
    ctx.fillStyle = rgba(n % 4 === 0 ? bl : (n % 5 === 0 ? [255, 200, 87] : [200, 235, 255]), (.06 + .22 * depth) * (.6 + .4 * Math.sin(t * 2 + n)));
    circ(x, y, .8 + 2.4 * depth); ctx.fill();
  }
  ctx.restore();
}

/* ---------- transitions between scenes ---------- */
const TR_DUR = .5, TR_KINDS = ['zoom', 'sweep', 'glitch', 'push'], TR_SFX = { zoom: 'swoosh', sweep: 'whoosh', glitch: 'glitch', push: 'whoosh2' };
const trKind = i => TR_KINDS[(i - 1) % TR_KINDS.length];
function drawSceneCam(S, t) { withCam(S, t, () => SCENES[S.type].draw(S, t)) }
function renderScenes(t, scenes) {
  let i = scenes.findIndex(s => t >= s.start && t < s.end); if (i < 0) i = scenes.length - 1;
  const S = scenes[i];
  if (i === 0) { const e = eo3((t - S.start) / .32); ctx.save(); ctx.globalAlpha *= e; ctx.translate(0, (1 - e) * 34); drawSceneCam(S, t); ctx.restore(); return S }
  const u = (t - S.start) / TR_DUR;
  if (u >= 1) { drawSceneCam(S, t); return S }
  const P = scenes[i - 1], e = eio(clamp(u)), k = trKind(i), ac = FX.accent;
  if (k === 'zoom') {
    ctx.save(); ctx.globalAlpha *= 1 - e; ctx.translate(540, 820); ctx.scale(1 + .55 * e, 1 + .55 * e); ctx.translate(-540, -820); drawSceneCam(P, t); ctx.restore();
    ctx.save(); ctx.globalAlpha *= e; ctx.translate(540, 820); ctx.scale(.72 + .28 * e, .72 + .28 * e); ctx.translate(-540, -820); drawSceneCam(S, t); ctx.restore();
    ctx.fillStyle = `rgba(255,255,255,${.16 * (1 - Math.abs(2 * e - 1))})`; ctx.fillRect(0, 0, W, H);
  } else if (k === 'sweep') {
    const bx = -500 + (W + 1000) * e, sk = 420;
    const side = left => { ctx.beginPath(); if (left) { ctx.moveTo(-20, -20); ctx.lineTo(bx + sk, -20); ctx.lineTo(bx - sk, H + 20); ctx.lineTo(-20, H + 20) } else { ctx.moveTo(bx + sk, -20); ctx.lineTo(W + 20, -20); ctx.lineTo(W + 20, H + 20); ctx.lineTo(bx - sk, H + 20) } ctx.closePath() };
    ctx.save(); side(false); ctx.clip(); drawSceneCam(P, t); ctx.restore();
    ctx.save(); side(true); ctx.clip(); drawSceneCam(S, t); ctx.restore();
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.translate(bx, H / 2); ctx.rotate(Math.atan2(2 * sk, H));
    ctx.fillStyle = lg(-140, 0, 140, 0, [[0, rgba(ac, 0)], [.45, rgba(ac, .55)], [.5, 'rgba(255,255,255,.9)'], [.55, rgba(ac, .55)], [1, rgba(ac, 0)]]);
    ctx.fillRect(-140, -H, 280, 2 * H); ctx.restore();
  } else if (k === 'glitch') {
    const src = e < .5 ? P : S, amp = 1 - Math.abs(2 * e - 1), fr = Math.floor(t * 30), n = 9;
    for (let b = 0; b < n; b++) {
      const y0 = b * H / n, off = (H2(b, fr) - .5) * 160 * amp;
      ctx.save(); ctx.beginPath(); ctx.rect(0, y0, W, H / n + 1); ctx.clip(); ctx.translate(off, 0); drawSceneCam(src, t); ctx.restore();
    }
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    for (let b = 0; b < 6; b++) {
      const y = H2(b, fr + 7) * H, h = 8 + 40 * H2(b, fr + 3);
      ctx.fillStyle = b % 2 ? `rgba(255,122,107,${.35 * amp})` : `rgba(63,167,214,${.35 * amp})`; ctx.fillRect(0, y, W, h);
    }
    ctx.restore();
  } else {                                        // push with motion streaks
    ctx.save(); ctx.globalAlpha *= 1 - e * .6; ctx.translate(-W * .55 * e, 0); drawSceneCam(P, t); ctx.restore();
    ctx.save(); ctx.globalAlpha *= clamp(e * 1.6); ctx.translate(W * .55 * (1 - e), 0); drawSceneCam(S, t); ctx.restore();
    const amp = 1 - Math.abs(2 * e - 1);
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    for (let s = 0; s < 14; s++) { const y = 260 + H2(s, 4) * 1150, x = W - (W + 600) * e + H2(s, 6) * 400, l = 200 + 400 * H2(s, 8);
      ctx.fillStyle = lg(x, 0, x + l, 0, [[0, rgba(ac, 0)], [1, rgba(ac, .5 * amp)]]); ctx.fillRect(x, y, l, 3 + 3 * H2(s, 9)) }
    ctx.restore();
  }
  return S;
}
function transitionEvents(scenes) { return scenes.slice(1).map((S, j) => ({ t: S.start, kind: TR_SFX[trKind(j + 1)] })) }

/* ---------- kinetic typography ---------- */
/* words (or letters with o.chars) slam in one after another: scale-down, rise, ghost trail.
   o: {size, weight, mono, color | colors(i,n), align, stagger, dur, ls, shadow, stroke} ; returns total width */
function kinetic(str, x, y, t, t0, o = {}) {
  const size = o.size || 60, f = o.mono ? FJ(o.weight || 700, size) : FM(o.weight || 800, size), ls = o.ls || 0;
  const toks = o.chars ? [...str] : str.split(' '), sp = o.chars ? 0 : measure(' ', f, ls);
  const ws = toks.map(w => measure(w, f, ls)), total = ws.reduce((a, b) => a + b, 0) + sp * (toks.length - 1);
  const stg = o.stagger === undefined ? (o.chars ? .035 : .075) : o.stagger, dur = o.dur || .42;
  let cx = o.align === 'left' ? x : o.align === 'right' ? x - total : x - total / 2;
  toks.forEach((w, i) => {
    const u = (t - t0 - i * stg) / dur, cw = ws[i];
    if (u > 0 && w.trim()) {
      const e = eback(u), a = clamp(u * 3), s = lerp(1.55, 1, clamp(e, 0, 1.08)), col = o.colors ? o.colors(i, toks.length) : (o.color || '#fff');
      ctx.save(); ctx.translate(cx + cw / 2, y - size * .34 + (1 - clamp(e)) * size * .5);
      if (u < 1) { ctx.save(); ctx.scale(s * 1.18, s * 1.18); T(w, 0, size * .34, { font: f, color: col, ls, alpha: a * .22 * (1 - u) }); ctx.restore() }
      ctx.scale(s, s); T(w, 0, size * .34, { font: f, color: col, ls, alpha: a, shadow: o.shadow, stroke: o.stroke });
      ctx.restore();
    }
    cx += cw + sp;
  });
  return total;
}
/* highlighter swept behind a word or line (x = left, y = baseline) */
function marker(x, y, w, size, t, t0, color, a = .32) {
  const u = eio((t - t0) / .45); if (u <= 0) return;
  ctx.save(); ctx.globalAlpha *= a; rr(x - 14, y - size * .78, (w + 28) * u, size * 1.02, 12); ctx.fillStyle = color; ctx.fill(); ctx.restore();
}
/* multi-line kinetic block: wraps, then each line slams in after the previous */
function kineticBlock(text, x, y0, maxW, t, t0, o = {}) {
  const size = o.size || 48, f = FM(o.weight || 800, size), lh = o.lh || Math.round(size * 1.2), lines = wrap(text, maxW, f).slice(0, o.maxLines || 4);
  const c0 = lines.length > 1 ? -(lines.length - 1) / 2 : 0;
  lines.forEach((l, k) => kinetic(l, x, y0 + (o.center ? (k + c0) * lh : k * lh), t, t0 + k * (o.lineDelay || .18), Object.assign({}, o, { size })));
  return lines.length;
}
/* gradient-like per-letter colours for kinetic letters */
const sweepColors = (a, b) => (i, n) => lerpColor(a, b, n > 1 ? i / (n - 1) : 0);
