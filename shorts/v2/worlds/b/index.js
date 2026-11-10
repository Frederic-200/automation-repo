// WORLD B - "Paper cut-out" (v2 scene kinds, same params as world A so one script works in either world).
// Layered torn-paper hills with parallax, every letter a cut piece of paper with a shadow, strips and notes that drop and settle.
// Scene kinds: headline, bars, stat, finale.   Captions: a paper label with word-timed type.
import { clamp, lerp, seg, eInOut, eOutExpo, eOutCubic, eOutBack, rng, vnoise } from '/proto/worlds/util.js';
import { PROPS } from '/props/props.js';
import { drawProp } from '/props/style_b.js';
import { beatTimes } from '/worlds/a/index.js';   // beat cue timing is shared by every world

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
      if (sc.params.beats && kinds.stage) kinds.stage.draw(c, lt, sc, { pal });   // hook scene: a paper prop moves under the hook text from frame 0
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

// ---- more kinds (same params in every world): list, versus, counter, steps
function card(c, x, y, w, h, fill, rot, p, drawIn) {   // a sheet of paper that drops in and settles; drawIn(c) draws its contents in local coords (0,0 = centre)
  if (p <= 0) return; c.save(); c.translate(x + w / 2, y + h / 2 + (1 - p) * -90); c.rotate(rot + (1 - p) * .12); c.scale(.85 + .15 * p, .85 + .15 * p); c.globalAlpha = clamp(p * 1.6);
  c.shadowColor = SH(.45); c.shadowBlur = 22; c.shadowOffsetY = 12; c.fillStyle = fill; c.beginPath(); c.rect(-w / 2, -h / 2, w, h); c.fill(); c.shadowColor = 'transparent'; grainOver(c, .1); if (drawIn) drawIn(c); c.restore();
}
const fitBR = (c, t, base, maxW) => { c.font = BR(base); return base * Math.min(1, maxW / (c.measureText(t).width || 1)); };
const bTitle = (c, P, lt, pal) => { if (P.title) { const sz = fitCut(c, P.title, 100, 900); cutLine(c, P.title, 300, sz, pal.tiles[0], pal.ink, -.1, lt, 2); } };
const disc = (c, x, y, r, fill, txt, ink, size, rot = 0) => { c.save(); c.translate(x, y); c.rotate(rot); c.shadowColor = SH(.4); c.shadowBlur = 12; c.shadowOffsetY = 6; c.fillStyle = fill; c.beginPath(); c.arc(0, 0, r, 0, 7); c.fill(); c.shadowColor = 'transparent'; grainOver(c, .1); c.fillStyle = ink; c.font = MONO(size); c.textAlign = 'center'; c.fillText(txt, 0, size * .35); c.restore(); };
Object.assign(kinds, {
  list: {
    draw(c, lt, sc, { pal }) {
      const Pm = sc.params, items = Pm.items || []; bTitle(c, Pm, lt, pal); const y0 = Pm.title ? 480 : 340, step = Math.min(250, 1000 / Math.max(items.length, 1)), h = Math.min(160, step - 30);
      items.forEach((it, i) => { const t0 = .25 + i * .45, p = eOutBack(seg(lt, t0, t0 + .5), 1.6), last = i === items.length - 1;
        card(c, 80, y0 + i * step, 920, h, last ? pal.acc : pal.white, (i % 2 ? .012 : -.012), p, cc => { disc(cc, -920 / 2 + 80, 0, 38, pal.tiles[0], String(i + 1), pal.ink, 34); cc.fillStyle = last ? pal.white : pal.ink; cc.textAlign = 'left'; cc.font = BR(fitBR(cc, it, 80, 720)); cc.fillText(it, -920 / 2 + 150, 26); }); });
    }
  },
  versus: {
    draw(c, lt, sc, { pal }) {
      const Pm = sc.params, side = (d, x, t0, fill, ink, rot) => { d = d || {}; const p = eOutBack(seg(lt, t0, t0 + .55), 1.6);
        card(c, x, 340, 440, 920, fill, rot, p, cc => { cc.fillStyle = ink; cc.textAlign = 'left'; cc.font = MONO(30); cc.fillText(d.label || '', -184, -380); (d.text || '').split('\n').forEach((ln, i) => { cc.font = FR(fitBR(cc, ln, 110, 360)); cc.fillStyle = ink; cc.fillText(ln, -184, -170 + i * 140); }); }); };
      side(Pm.a, 70, .2, pal.white, pal.ink, -.02); side(Pm.b, 570, .6, pal.acc, pal.white, .02);
      const pv = eOutBack(seg(lt, .5, .85), 2); if (pv > 0) disc(c, 540, 800, 66 * pv, pal.tiles[0], 'VS', pal.ink, 40, -.08);
    }
  },
  counter: {
    draw(c, lt, sc, { pal }) {
      const Pm = sc.params, to = +Pm.to, from = +(Pm.from || 0), dec = Pm.decimals || 0, fmt = v => (dec ? v.toFixed(dec) : Math.round(v).toString()) + (Pm.suffix || ''), v = lerp(from, to, eOutCubic(seg(lt, .1, 1.4)));
      if (Pm.label) tag(c, Pm.label, 80, 520, 30, pal.tiles[0], pal.ink, -.03, eOutExpo(seg(lt, -.1, .3)));
      const p = eOutBack(seg(lt, -.05, .45), 1.7), fin = fmt(to); c.font = FR(100); const sz = Math.min(P_size(Pm), 100 * 820 / (c.measureText(fin).width || 1));
      card(c, 80, 600, 920, sz * 1.5, pal.white, -.015, p, cc => { cc.font = FR(sz); cc.fillStyle = pal.acc; cc.textAlign = 'left'; cc.fillText(fmt(v), -920 / 2 + 50, sz * .36); });
      (Pm.sub || '').split('\n').forEach((t, i) => card(c, 130, 600 + sz * 1.5 + 70 + i * 130, 820, 110, pal.tiles[0], (i % 2 ? .012 : -.012), eOutBack(seg(lt, 1.0 + i * .15, 1.5 + i * .15), 1.6), cc => { cc.fillStyle = pal.ink; cc.textAlign = 'center'; cc.font = BR(fitBR(cc, t, 70, 760)); cc.fillText(t, 0, 24); }));
      if (Pm.note) { c.font = MONO(24); c.fillStyle = 'rgba(43,27,43,.6)'; c.textAlign = 'left'; c.fillText(Pm.note, 80, 1470); }
    }
  },
  steps: {
    draw(c, lt, sc, { pal }) {
      const Pm = sc.params, st = Pm.steps || [], n = st.length; bTitle(c, Pm, lt, pal); const y0 = Pm.title ? 480 : 360, bh = 170, step = Math.min(330, (1060 - bh) / Math.max(n - 1, 1));
      st.forEach((t, i) => { const t0 = .25 + i * .5, p = eOutBack(seg(lt, t0, t0 + .5), 1.6), y = y0 + i * step, last = i === n - 1;
        if (i > 0) { const pa = eOutExpo(seg(lt, t0 - .2, t0 + .1)), ya = y0 + (i - 1) * step + bh; if (pa > 0) { strip(c, 520, ya + 4, 1, 1, pal.ink); c.save(); c.shadowColor = SH(.35); c.shadowBlur = 8; c.shadowOffsetY = 4; c.fillStyle = pal.acc; c.fillRect(526, ya + 6, 28, (step - bh - 12) * pa); if (pa > .9) { c.beginPath(); c.moveTo(540, y - 2); c.lineTo(510, y - 34); c.lineTo(570, y - 34); c.closePath(); c.fill(); } c.restore(); } }
        card(c, 80, y, 920, bh, last ? pal.acc : pal.white, (i % 2 ? .01 : -.01), p, cc => { disc(cc, -920 / 2 + 80, 0, 42, pal.tiles[0], String(i + 1), pal.ink, 36); cc.fillStyle = last ? pal.white : pal.ink; cc.textAlign = 'left'; cc.font = BR(fitBR(cc, t, 78, 700)); cc.fillText(t, -920 / 2 + 150, 26); }); });
    }
  },
});
function P_size(Pm) { return Pm.size || 330; }

// ---- stage (see world A): ONE paper prop at a time + a cut-letter label of <=3 words; beats follow the narration
const SLOT = { c: [540, 840, 560], l: [290, 840, 340], r: [790, 840, 340] };
const grainFill = (c, a) => grainOver(c, a);
Object.assign(kinds, {
  stage: {
    draw(c, lt, sc, { pal }) {
      const B = beatTimes(sc), lr = B.filter(b => b.slot === 'l' || b.slot === 'r').map(b => b.t), firstLR = lr.length ? Math.min(...lr) : 1e9, slots = {};
      B.forEach(b => { const s = b.slot || 'c'; if (b.t > lt) return; if (s === 'c' && lt >= firstLR) return; (slots[s] = slots[s] || []).push(b); });
      const show = (b, age, out) => {
        const spec = PROPS[b.prop]; if (!spec) return; const s = b.slot || 'c', [x0, y0, sz0] = SLOT[s] || SLOT.c, mv = b.move || 'pop';
        let dx = 0, dy = 0, k = 1, rot = 0; if (mv === 'drop') { const q = eOutBack(clamp(age / .55), 1.7); dy = (1 - q) * -700; rot = (1 - q) * .35; } else if (mv === 'slide') { dx = (1 - eOutExpo(clamp(age / .5))) * 520; rot = (1 - eOutExpo(clamp(age / .5))) * .2; } else { k = eOutBack(clamp(age / .5), 2); }
        dy += Math.sin(age * 2.3) * 9; let al = clamp(age / .15); if (out != null) { dx += (s === 'r' ? 1 : -1) * out * 520; al = 1 - out; }
        c.save(); c.globalAlpha = al; c.translate(x0 + dx, y0 + dy); c.rotate(rot + Math.sin(age * 1.7) * .02);
        drawProp(c, spec, 0, 0, sz0 * Math.max(k, .001), pal, { on: eOutCubic(seg(age, .35, 1.0)), ...(b.anim || {}) }, grainFill); c.restore();
        if (b.label && out == null) { const sz = fitCut(c, b.label, 92, s === 'c' ? 900 : 400); cutLine(c, b.label, y0 + sz0 * .62 + 60, sz, pal.tiles[age < 0 ? 0 : (b.prop.length % 3)], pal.ink, .12, age, b.prop.length, .08, x0); }
      };
      for (const s in slots) { const a = slots[s], cur = a[a.length - 1], prv = a[a.length - 2]; if (prv && lt - cur.t < .3) show(prv, lt - prv.t, eInOut((lt - cur.t) / .3)); show(cur, lt - cur.t, null); }
      if (firstLR < 1e9 && lt >= firstLR && lt < firstLR + .3) { const a = B.filter(b => (b.slot || 'c') === 'c' && b.t < firstLR), prv = a[a.length - 1]; if (prv) show(prv, lt - prv.t, eInOut((lt - firstLR) / .3)); }
    }
  },
});

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
