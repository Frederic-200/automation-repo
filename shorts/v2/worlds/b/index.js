// WORLD B - "Paper cut-out" (v2 scene kinds, same params as world A so one script works in either world).
// Layered torn-paper hills with parallax, every letter a cut piece of paper with a shadow, strips and notes that drop and settle.
// Scene kinds: headline, bars, stat, finale.   Captions: a paper label with word-timed type.
import { clamp, lerp, seg, eInOut, eOutExpo, eOutCubic, eOutBack, rng, vnoise } from '/proto/worlds/util.js';

const FR = s => `900 ${s}px Fraunces`, MONO = s => `700 ${s}px JBMono`, BR = s => `800 ${s}px Bricolage`;
const palettes = {
  earth: { cream: '#F3E5C8', ink: '#2B1B2B', white: '#FFF8EA', acc: '#C8553D', hills: ['#9DB08A', '#E3A93B', '#C8553D', '#4A2B47'], tiles: ['#E3A93B', '#9DB08A', '#FFF8EA'], panel: '#4A2B47' },
  harbor: { cream: '#E6EEF0', ink: '#12263A', white: '#FAFDFE', acc: '#E8744F', hills: ['#8FB8C4', '#3E86A0', '#E8744F', '#12384F'], tiles: ['#F2C14E', '#8FB8C4', '#FAFDFE'], panel: '#12384F' },
  blush: { cream: '#F7E6E4', ink: '#3A1F2D', white: '#FFF6F3', acc: '#D6455D', hills: ['#E8B4B8', '#F2C14E', '#D6455D', '#5B2A4E'], tiles: ['#F2C14E', '#E8B4B8', '#FFF6F3'], panel: '#5B2A4E' },
};
const SH = a => `rgba(40,20,20,${a})`;

// ---- paper grain (seeded, built once) ----
const grain = document.createElement('canvas'); grain.width = grain.height = 256;
{ const g = grain.getContext('2d'), r = rng(5), im = g.createImageData(256, 256); for (let i = 0; i < im.data.length; i += 4) { const v = 200 + r() * 55; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255; } g.putImageData(im, 0, 0); }
let pat = null; const P = c => pat || (pat = c.createPattern(grain, 'repeat'));
const grainOver = (c, a = .12) => { c.save(); c.globalAlpha = a; c.globalCompositeOperation = 'multiply'; c.fillStyle = P(c); c.fill(); c.restore(); };

// ---- hills: low torn layers along the bottom so the middle of the frame stays clear for the scene ----
const LAYERS = [
  { base: 1560, amp: 55, seed: 3, depth: .25, rise: .0 }, { base: 1665, amp: 45, seed: 9, depth: .5, rise: .1 },
  { base: 1760, amp: 40, seed: 14, depth: .8, rise: .2 }, { base: 1850, amp: 28, seed: 21, depth: 1.2, rise: .3 },
];
LAYERS.forEach(L => { const n1 = vnoise(L.seed), n2 = vnoise(L.seed + 100), r = rng(L.seed + 7); L.pts = []; for (let px = -140; px <= 1220; px += 12) L.pts.push([px, L.base - (n1(px / 230) - .5) * 2 * L.amp - (n2(px / 47) - .5) * 20 + (r() - .5) * 6]); });
function hill(c, L, col, t) {
  const rise = eOutCubic(seg(t, L.rise, L.rise + .7)), dy = (1 - rise) * 600, dx = Math.sin(t * .55 + L.seed) * 30 * L.depth + (t - 5) * 6 * L.depth;
  c.save(); c.translate(dx, dy); c.shadowColor = SH(.45); c.shadowBlur = 26; c.shadowOffsetY = -6;
  c.fillStyle = col; c.beginPath(); c.moveTo(-160, 2100); L.pts.forEach(([x, y]) => c.lineTo(x, y)); c.lineTo(1240, 2100); c.closePath(); c.fill(); c.shadowColor = 'transparent'; grainOver(c);
  c.strokeStyle = 'rgba(255,248,234,.7)'; c.lineWidth = 3; c.beginPath(); L.pts.forEach(([x, y], i) => i ? c.lineTo(x, y - 2) : c.moveTo(x, y - 2)); c.stroke(); c.restore();
}

// ---- paper pieces ----
function measure(c, txt, size, gap) { c.font = FR(size); return [...txt].map(ch => c.measureText(ch).width + size * gap); }
const fitCut = (c, txt, base, maxW, gap = .08) => { const w = measure(c, txt, base, gap).reduce((a, b) => a + b, 0); return base * Math.min(1, maxW / w); };
// every glyph is its own piece of paper: tile colour = outline stroke, drops in with a small overshoot
function cutLine(c, txt, cy, size, tile, ink, t0, lt, seed = 0, gap = .08, cx = 540) {
  const ws = measure(c, txt, size, gap), tot = ws.reduce((a, b) => a + b, 0); let px = cx - tot / 2;
  [...txt].forEach((ch, i) => {
    const lw = ws[i], r1 = Math.sin(i * 12.9898 + seed) * .12, r2 = Math.sin(i * 78.233 + seed) * size * .05, d = clamp((lt - t0 - i * .035) / .35), pop = eOutBack(d, 2.4); px += lw / 2;
    if (d > 0 && ch !== ' ') {
      c.save(); c.translate(px, cy + r2 + (1 - pop) * -140); c.rotate(r1 + (1 - d) * .5); c.scale(pop, pop); c.font = FR(size); c.textAlign = 'center';
      c.shadowColor = SH(.35); c.shadowBlur = size * .05; c.shadowOffsetY = size * .04; c.strokeStyle = tile; c.lineJoin = 'round'; c.lineWidth = size * .2; c.strokeText(ch, 0, size * .34);
      c.shadowColor = 'transparent'; c.fillStyle = ink; c.fillText(ch, 0, size * .34); c.restore();
    }
    px += lw / 2;
  });
}
// a strip of paper with a torn (jagged) right end
function strip(c, x, y, w, h, col, seed = 1, shadow = true) {
  if (w <= 2) return; const r = rng(seed * 31 + 7); c.save(); if (shadow) { c.shadowColor = SH(.4); c.shadowBlur = 16; c.shadowOffsetY = 8; }
  c.fillStyle = col; c.beginPath(); c.moveTo(x, y); c.lineTo(x + w, y); for (let k = 0; k <= 8; k++) c.lineTo(x + w + (r() - .5) * 14, y + h * k / 8); c.lineTo(x, y + h); c.closePath(); c.fill(); c.shadowColor = 'transparent'; grainOver(c, .1); c.restore();
}
function tag(c, txt, x, y, size, fill, ink, rot = -.02, a = 1, align = 'left') {   // label on a paper tag
  c.save(); c.globalAlpha = a; c.font = MONO(size); const w = c.measureText(txt).width + 40, h = size * 1.7, x0 = align === 'center' ? x - w / 2 : x;
  c.translate(x0, y); c.rotate(rot); c.shadowColor = SH(.35); c.shadowBlur = 10; c.shadowOffsetY = 5; c.fillStyle = fill; c.beginPath(); c.rect(0, -h * .75, w, h); c.fill(); c.shadowColor = 'transparent'; grainOver(c, .1);
  c.fillStyle = ink; c.textAlign = 'left'; c.fillText(txt, 20, 0); c.restore(); return w;
}
function tornTop(c, y, seed) {   // path: everything below a torn horizontal edge at y
  const n = vnoise(seed), r = rng(seed + 3); c.beginPath(); c.moveTo(-40, 2000); c.lineTo(-40, y);
  for (let x = -40; x <= 1120; x += 12) c.lineTo(x, y + (n(x / 60) - .5) * 40 + (r() - .5) * 8); c.lineTo(1120, 2000); c.closePath();
}

const kinds = {
  // params.lines [{text, color:'ink'|'acc', size}], params.underline index, params.y (top of the first line)
  headline: {
    draw(c, lt, sc, { pal }) {
      const L = sc.params.lines || [], y0 = sc.params.y ?? 300; let y = y0;
      L.forEach((ln, i) => {
        const base = ln.size || 150, sz = fitCut(c, ln.text, base, 900), acc = ln.color === 'acc', tile = acc ? pal.acc : pal.tiles[i % 3], ink = acc ? pal.white : pal.ink, cy = y + sz * .56;
        cutLine(c, ln.text, cy, sz, tile, ink, -.2 + i * .14, lt, i * 3.1);
        if (sc.params.underline === i) { const pb = eOutExpo(seg(lt, .5 + i * .14, 1.0 + i * .14)), w = measure(c, ln.text, sz, .08).reduce((a, b) => a + b, 0); strip(c, 540 - w / 2, y + sz * 1.0, (w + 20) * pb, 22, pal.acc, 5 + i); }
        y += sz * 1.12;
      });
    }
  },
  // params.title, params.rows [{label, value 0..1, color:'acc'|'ink', wobble}], params.gap {from,to,label}, params.note
  bars: {
    draw(c, lt, sc, { pal }) {
      const P_ = sc.params, X0 = 80, FULL = 920, bh = 150, y0 = 600, step = 330, rows = P_.rows || [];
      if (P_.title) { const sz = fitCut(c, P_.title, 100, 900); cutLine(c, P_.title, 300, sz, pal.tiles[0], pal.ink, -.1, lt, 2); }
      const ends = [];
      rows.forEach((r, i) => {
        const y = y0 + i * step, a = eOutExpo(seg(lt, .2 + i * .35, .5 + i * .35)); if (a <= 0) { ends.push(0); return; }
        tag(c, r.label, X0, y - 30, 26, pal.white, pal.ink, -.015 + i * .03, a);
        c.save(); c.globalAlpha = a; c.fillStyle = 'rgba(43,27,43,.12)'; c.fillRect(X0, y, FULL, bh); c.restore();
        const t0 = .35 + i * .35, grow = r.wobble ? eOutCubic(seg(lt, t0, t0 + 1.1)) : eOutExpo(seg(lt, t0, t0 + .5));
        const wob = r.wobble && lt > t0 + 1.1 ? ((vnoise(11)(lt * 5) - .5) * 90 + Math.sin(lt * 9) * 14) * grow : 0, w = Math.max(0, FULL * r.value * grow + wob);
        strip(c, X0, y, w, bh, r.color === 'acc' ? pal.acc : pal.panel, 10 + i); ends.push(w);
      });
      const g = P_.gap; if (g && ends[g.from] > 0 && ends[g.to] > 0) {
        const tg = .35 + g.to * .35 + 1.3, pg = eOutExpo(seg(lt, tg, tg + .5)), y = y0 + g.to * step, gx0 = X0 + Math.min(ends[g.from], ends[g.to]), gx1 = X0 + Math.max(ends[g.from], ends[g.to]);
        if (pg > 0) {
          c.save(); c.beginPath(); c.rect(gx0, y, (gx1 - gx0) * pg, bh); c.clip(); c.strokeStyle = pal.tiles[0]; c.lineWidth = 16;
          for (let k = -200; k < FULL; k += 38) { c.beginPath(); c.moveTo(gx0 + k, y + bh); c.lineTo(gx0 + k + bh, y); c.stroke(); } c.restore();
          tag(c, g.label || 'THE GAP', (gx0 + gx1) / 2, y + bh + 90, 36, pal.acc, pal.white, .02, pg, 'center');
        }
      }
      if (P_.note) { c.font = MONO(24); c.fillStyle = 'rgba(43,27,43,.6)'; c.textAlign = 'left'; c.fillText(P_.note, X0, 1470); }
    }
  },
  // params.small, params.big, params.sub (lines separated by \n)
  stat: {
    draw(c, lt, sc, { pal }) {
      const P_ = sc.params; if (P_.small) tag(c, P_.small, 80, 520, 30, pal.tiles[0], pal.ink, -.03, eOutExpo(seg(lt, -.1, .3)));
      const big = P_.big || '', sz = fitCut(c, big, P_.size || 360, 900, .06); cutLine(c, big, 760, sz, pal.acc, pal.white, -.05, lt, 6, .06);
      const lines = (P_.sub || '').split('\n'), np = eOutBack(seg(lt, .5, 1.1), 1.8); if (np > 0 && lines[0]) {
        const h = 60 + lines.length * 110; c.save(); c.translate(540, 1060 + h / 2); c.rotate(-.03); c.scale(np, np); c.shadowColor = SH(.45); c.shadowBlur = 24; c.shadowOffsetY = 12; c.fillStyle = pal.white; c.beginPath(); c.rect(-420, -h / 2, 840, h); c.fill(); c.shadowColor = 'transparent'; grainOver(c, .1);
        c.fillStyle = pal.tiles[0]; c.globalAlpha = .75; c.save(); c.translate(0, -h / 2); c.rotate(.05); c.fillRect(-90, -24, 180, 48); c.restore(); c.globalAlpha = 1;
        c.fillStyle = pal.ink; c.textAlign = 'center'; lines.forEach((s, i) => { c.font = BR(90); c.font = BR(Math.min(90, 90 * 780 / (c.measureText(s).width || 1))); c.fillText(s, 0, -h / 2 + 100 + i * 110); }); c.restore();
      }
    }
  },
  // params.top, params.accent, params.mark 'neq'|'eq'|null, params.bottom [words]. Full panel, no captions.
  finale: {
    caps: false,
    draw(c, lt, sc, { pal }) {
      const P_ = sc.params, pp = eInOut(seg(lt, -.05, .45)), top = lerp(1960, -60, pp);
      c.save(); c.shadowColor = SH(.5); c.shadowBlur = 40; c.shadowOffsetY = -14; tornTop(c, top, 40); c.fillStyle = pal.panel; c.fill(); c.shadowColor = 'transparent'; grainOver(c, .12); c.restore();
      if (P_.top) { const sz = fitCut(c, P_.top, 190, 880); cutLine(c, P_.top, 520, sz, pal.white, pal.ink, .3, lt, 1); }
      if (P_.accent) { const sz = fitCut(c, P_.accent, 330, 880); cutLine(c, P_.accent, 840, sz, pal.tiles[0], pal.ink, .45, lt, 8); }
      if (P_.mark) {
        const ps = eOutExpo(seg(lt, .9, 1.4)); [1090, 1150].forEach((y, i) => strip(c, 540 - 150 * ps, y, 300 * ps, 28, pal.cream, 20 + i));
        const pl = eOutExpo(seg(lt, 1.3, 1.65)); if (P_.mark === 'neq' && pl > 0) { c.save(); c.translate(540, 1130); c.rotate(-.42); strip(c, -120, -14, 240 * pl, 28, pal.acc, 33); c.restore(); }
      }
      (P_.bottom || []).forEach((w, i) => { const sz = fitCut(c, w, 170, 880); cutLine(c, w, 1380 + i * 200, sz, pal.white, pal.ink, 1.5 + i * .15, lt, 3 + i); });
    }
  },
};

export default {
  name: 'B', title: 'Paper cut-out', palettes, kinds,
  background(c, t, { pal }) {
    c.fillStyle = pal.cream; c.fillRect(0, 0, 1080, 1920); c.beginPath(); c.rect(0, 0, 1080, 1920); grainOver(c, .1);
    LAYERS.forEach((L, i) => hill(c, L, pal.hills[i], t));
  },
  // the new scene is a sheet of paper with a torn top edge that slides up over the old one
  wipe(c, p, { pal }, drawNew, drawBg) {
    const y = lerp(1960, -60, eInOut(p));
    c.save(); c.shadowColor = SH(.5); c.shadowBlur = 36; c.shadowOffsetY = -12; tornTop(c, y, 77); c.fillStyle = pal.cream; c.fill(); c.restore();
    c.save(); tornTop(c, y, 77); c.clip(); c.fillStyle = pal.cream; c.fillRect(0, 0, 1080, 1920); drawBg(); drawNew(); c.restore();
  },
  // a paper label on the hills; type in the same ink, the spoken word gets a strip of tape underneath, keywords in the accent colour
  captions(c, t, ch, { pal }) {
    const a = eOutBack(seg(t, ch.s - .05, ch.s + .22), 1.8); if (a <= 0) return;
    c.font = BR(62); const sp = c.measureText(' ').width, ws = ch.words.map(w => c.measureText(w.w).width), tot = ws.reduce((x, y) => x + y, 0) + sp * (ws.length - 1), k = Math.min(1, 860 / tot), size = 62 * k;
    c.font = BR(size); const sp2 = c.measureText(' ').width, ws2 = ch.words.map(w => c.measureText(w.w).width), tw = ws2.reduce((x, y) => x + y, 0) + sp2 * (ws2.length - 1), W = tw + 80, H = size * 1.9, cy = 1650;
    c.save(); c.translate(540, cy); c.rotate(-.012); c.scale(.8 + .2 * a, .8 + .2 * a); c.globalAlpha = clamp(a * 1.5);
    c.shadowColor = SH(.5); c.shadowBlur = 18; c.shadowOffsetY = 10; c.fillStyle = pal.white; c.beginPath(); c.rect(-W / 2, -H / 2, W, H); c.fill(); c.shadowColor = 'transparent'; grainOver(c, .1);
    let x = -tw / 2; ch.words.forEach((w, i) => {
      if (t >= w.s && t < w.e + .02) { c.fillStyle = pal.tiles[0]; c.globalAlpha = .85; c.fillRect(x - 4, size * .22, ws2[i] + 8, size * .2); c.globalAlpha = clamp(a * 1.5); }
      c.font = BR(size); c.textAlign = 'left'; c.fillStyle = w.k ? pal.acc : pal.ink; c.fillText(w.w, x, size * .3); x += ws2[i] + sp2;
    }); c.restore();
  },
};
