// WORLD A - "Type + Data" (v2 scene kinds). Swiss-poster typography on a coloured paper, hard masked reveals, data panels.
// Motion grammar: masked line reveals, expo/linear wipes, bars that shoot or crawl. No springs, no figure, no hero object.
// Scene kinds: headline, bars, stat, finale.   Captions: word-timed plain type at the bottom.
import { clamp, lerp, seg, eInOut, eOutExpo, eOutCubic, eOutBack, vnoise } from '/proto/worlds/util.js';
import { PROPS } from '/props/props.js';
import { drawProp } from '/props/style_a.js';

const BR = s => `800 ${s}px Bricolage`, FR = s => `italic 900 ${s}px Fraunces`, MONO = s => `700 ${s}px JBMono`;
const palettes = {
  ember: { paper: '#F1EDE4', ink: '#121212', acc: '#FF4A1C', mute: '#6f6a5e', soft: 'rgba(18,18,18,.08)' },
  cobalt: { paper: '#EAF0F8', ink: '#0B1B33', acc: '#2F5BFF', mute: '#5b6b85', soft: 'rgba(11,27,51,.08)' },
  moss: { paper: '#EEEBDC', ink: '#16241A', acc: '#2E8B57', mute: '#66705f', soft: 'rgba(22,36,26,.08)' },
  plum: { paper: '#F4EAF1', ink: '#2A0F2E', acc: '#D6246E', mute: '#7a6579', soft: 'rgba(42,15,46,.08)' },
};
const noise = vnoise(11);
const col = (p, k) => k === 'acc' ? p.acc : k === 'mute' ? p.mute : k === 'paper' ? p.paper : p.ink;
const fitSize = (c, txt, fontFn, base, maxW) => { c.font = fontFn(base); return base * Math.min(1, maxW / c.measureText(txt).width); };
const line = (c, x1, y1, x2, y2, w, color) => { c.strokeStyle = color; c.lineWidth = w; c.beginPath(); c.moveTo(x1, y1); c.lineTo(x2, y2); c.stroke(); };
const mono = (c, s, x, y, size, color, align = 'left') => { c.font = MONO(size); c.fillStyle = color; c.textAlign = align; c.fillText(s, x, y); c.textAlign = 'left'; };
// a line of text revealed from below inside a mask
function maskLine(c, txt, fontFn, size, x, topY, color, p, align = 'left', maxW = 1100) {
  if (p <= 0) return; const h = size * .92; c.save(); c.beginPath(); c.rect(x - (align === 'center' ? maxW / 2 : 20), topY, maxW + 40, h + 6); c.clip();
  c.translate(0, (1 - p) * h); c.font = fontFn(size); c.fillStyle = color; c.textAlign = align; c.fillText(txt, x, topY + size * .78); c.restore();
}
const FONTS = { sans: BR, serif: FR };

const kinds = {
  // params.lines: [{text, font:'sans'|'serif', color:'ink'|'acc', size}], params.underline: line index, params.y
  headline: {
    draw(c, lt, sc, { pal }) {
      const L = sc.params.lines || [], y0 = sc.params.y ?? 250; let y = y0;
      L.forEach((ln, i) => {
        const f = FONTS[ln.font || 'sans'], sz = fitSize(c, ln.text, f, ln.size || 160, 920), p = eOutExpo(seg(lt, -.2 + i * .14, .4 + i * .14));
        maskLine(c, ln.text, f, sz, 80, y, col(pal, ln.color || 'ink'), p);
        if (sc.params.underline === i) { const pb = eOutExpo(seg(lt, .5 + i * .14, 1.0 + i * .14)); c.font = f(sz); c.fillStyle = pal.acc; c.fillRect(80, y + sz * .92 + 6, c.measureText(ln.text).width * pb, 22); }
        y += sz * .92;
      });
    }
  },
  // params.title, params.rows [{label, value 0..1, color, wobble}], params.gap {from, to, label}, params.note
  bars: {
    draw(c, lt, sc, { pal }) {
      const P = sc.params, X0 = 80, FULL = 920, bh = 150, y0 = 600, step = 330, rows = P.rows || [];
      if (P.title) maskLine(c, P.title, BR, fitSize(c, P.title, BR, 110, 920), 80, 250, pal.ink, eOutExpo(seg(lt, -.1, .45)));
      const ends = [];
      rows.forEach((r, i) => {
        const y = y0 + i * step, a = eOutExpo(seg(lt, .2 + i * .35, .5 + i * .35)); if (a <= 0) { ends.push(0); return; }
        c.globalAlpha = a; mono(c, r.label, X0, y - 28, 30, pal.ink); c.fillStyle = pal.soft; c.fillRect(X0, y, FULL, bh);
        for (let k = 0; k <= 10; k++) line(c, X0 + k * FULL / 10, y + bh, X0 + k * FULL / 10, y + bh + (k % 5 ? 10 : 20), 2, pal.ink); c.globalAlpha = 1;
        const t0 = .35 + i * .35, grow = r.wobble ? eOutCubic(seg(lt, t0, t0 + 1.1)) : eOutExpo(seg(lt, t0, t0 + .5));
        const wob = r.wobble && lt > t0 + 1.1 ? ((noise(lt * 5) - .5) * 90 + Math.sin(lt * 9) * 14) * grow : 0, w = Math.max(0, FULL * r.value * grow + wob);
        c.fillStyle = col(pal, r.color || 'ink'); c.fillRect(X0, y, w, bh); ends.push(w);
      });
      const g = P.gap; if (g && ends[g.from] > 0 && ends[g.to] > 0) {
        const tg = .35 + g.to * .35 + 1.3, pg = eOutExpo(seg(lt, tg, tg + .5)), y = y0 + g.to * step, gx0 = X0 + Math.min(ends[g.from], ends[g.to]), gx1 = X0 + Math.max(ends[g.from], ends[g.to]);
        if (pg > 0) {
          c.save(); c.beginPath(); c.rect(gx0, y, (gx1 - gx0) * pg, bh); c.clip(); c.strokeStyle = pal.acc; c.lineWidth = 6;
          for (let k = -200; k < FULL; k += 26) { c.beginPath(); c.moveTo(gx0 + k, y + bh); c.lineTo(gx0 + k + bh, y); c.stroke(); } c.restore();
          c.globalAlpha = pg; line(c, gx0, y + bh + 70, gx1, y + bh + 70, 4, pal.acc); line(c, gx0, y + bh + 56, gx0, y + bh + 84, 4, pal.acc); line(c, gx1, y + bh + 56, gx1, y + bh + 84, 4, pal.acc);
          mono(c, g.label || 'THE GAP', (gx0 + gx1) / 2, y + bh + 130, 40, pal.acc, 'center'); c.globalAlpha = 1;
        }
      }
      if (P.note) mono(c, P.note, X0, 1480, 24, pal.mute);
    }
  },
  // params.small (mono kicker), params.big (giant word, serif italic accent), params.sub (lines separated by \n)
  stat: {
    draw(c, lt, sc, { pal }) {
      const P = sc.params; if (P.small) { c.globalAlpha = eOutExpo(seg(lt, -.1, .3)); mono(c, P.small, 80, 520, 32, pal.ink); c.globalAlpha = 1; }
      const big = P.big || '', sz = fitSize(c, big, FR, P.size || 360, 920), p = eOutExpo(seg(lt, -.1, .5));
      maskLine(c, big, FR, sz, 80, 600, pal.acc, p);
      const pb = eOutExpo(seg(lt, .4, 1.0)); c.fillStyle = pal.ink; c.fillRect(80, 600 + sz * .92 + 24, 920 * pb, 12);
      (P.sub || '').split('\n').forEach((s, i) => maskLine(c, s, BR, fitSize(c, s, BR, 110, 920), 80, 600 + sz * .92 + 80 + i * 110, pal.ink, eOutExpo(seg(lt, .5 + i * .15, 1.0 + i * .15))));
    }
  },
  // params.top (word), params.accent (word, serif italic accent), params.mark 'neq'|'eq'|null, params.bottom [words]. Full dark panel, no captions.
  finale: {
    caps: false,
    draw(c, lt, sc, { pal }) {
      const P = sc.params, pp = eInOut(seg(lt, -.05, .4)); c.fillStyle = pal.ink; c.fillRect(0, lerp(1920, 0, pp), 1080, 1920);
      const rev = (txt, f, size, base, t0, color) => { if (!txt) return; const r = eOutExpo(seg(lt, t0, t0 + .5)); if (r <= 0) return; const k = Math.min(1, 900 / (c.font = f(size), c.measureText(txt).width)); const s2 = size * k;
        c.save(); c.beginPath(); c.rect(0, base - s2 * .85, 1080, s2 * 1.0); c.clip(); c.translate(0, (1 - r) * s2); c.font = f(s2); c.fillStyle = color; c.textAlign = 'center'; c.fillText(txt, 540, base); c.restore(); };
      rev(P.top, BR, 190, 700, .3, pal.paper); rev(P.accent, FR, 330, 980, .45, pal.acc);
      if (P.mark) { const ps = eOutExpo(seg(lt, .9, 1.4)); if (ps > 0) { c.strokeStyle = pal.paper; c.lineWidth = 26; const w = 150 * ps; [1130, 1190].forEach(y => { c.beginPath(); c.moveTo(540 - w, y); c.lineTo(540 + w, y); c.stroke(); }); }
        const pl = eOutExpo(seg(lt, 1.3, 1.65)); if (P.mark === 'neq' && pl > 0) { c.strokeStyle = pal.acc; c.lineWidth = 26; c.beginPath(); c.moveTo(540 - 70 * pl, 1230); c.lineTo(540 + 70 * pl, 1090); c.stroke(); } }
      (P.bottom || []).forEach((w, i) => rev(w, BR, 190, 1470 + i * 190, 1.5 + i * .15, pal.paper));
    }
  },
};

// ---- more kinds (same params in every world): list, versus, counter, steps
const num2 = i => String(i + 1).padStart(2, '0');
const titleLine = (c, P, lt, pal) => { if (P.title) maskLine(c, P.title, BR, fitSize(c, P.title, BR, 110, 920), 80, 250, pal.ink, eOutExpo(seg(lt, -.1, .45))); };
Object.assign(kinds, {
  // params.title?, params.items [2-5 short strings]
  list: {
    draw(c, lt, sc, { pal }) {
      const P = sc.params, items = P.items || []; titleLine(c, P, lt, pal); const y0 = P.title ? 560 : 400, step = Math.min(230, 980 / Math.max(items.length, 1));
      items.forEach((it, i) => {
        const t0 = .25 + i * .45, p = eOutExpo(seg(lt, t0, t0 + .4)); if (p <= 0) return; const y = y0 + i * step;
        line(c, 80, y - 20, 80 + 920 * p, y - 20, 3, pal.ink); mono(c, num2(i), 80, y + 40, 34, pal.acc); maskLine(c, it, BR, fitSize(c, it, BR, 92, 790), 190, y - 8, i === items.length - 1 ? pal.acc : pal.ink, p);
      });
    }
  },
  // params.a / params.b: {label, text (lines separated by \n)}
  versus: {
    draw(c, lt, sc, { pal }) {
      const P = sc.params, panel = (d, side, t0) => {
        d = d || {}; const p = eOutExpo(seg(lt, t0, t0 + .5)); if (p <= 0) return; const x0 = side ? 556 : 80, w = 444, y0 = 330, h = 940;
        c.save(); c.beginPath(); c.rect(x0, y0 + h * (1 - p), w, h * p); c.clip();
        if (side) { c.fillStyle = pal.acc; c.fillRect(x0, y0, w, h); } else { c.fillStyle = pal.soft; c.fillRect(x0, y0, w, h); c.strokeStyle = pal.ink; c.lineWidth = 4; c.strokeRect(x0 + 2, y0 + 2, w - 4, h - 4); }
        const ink = side ? pal.paper : pal.ink; mono(c, d.label || '', x0 + 36, y0 + 80, 30, ink);
        (d.text || '').split('\n').forEach((ln, i) => { const sz = fitSize(c, ln, BR, 120, w - 70); c.font = BR(sz); c.fillStyle = ink; c.fillText(ln, x0 + 36, y0 + 260 + i * 140); });
        c.restore();
      };
      panel(P.a, 0, .2); panel(P.b, 1, .6);
      const pv = eOutExpo(seg(lt, .5, .8)); if (pv > 0) { c.save(); c.translate(540, 800); c.scale(pv, pv); c.fillStyle = pal.ink; c.beginPath(); c.arc(0, 0, 62, 0, 7); c.fill(); c.fillStyle = pal.paper; c.font = MONO(40); c.textAlign = 'center'; c.fillText('VS', 0, 14); c.restore(); c.textAlign = 'left'; }
    }
  },
  // params.label, params.to (number), params.from, params.suffix, params.decimals, params.sub, params.note
  counter: {
    draw(c, lt, sc, { pal }) {
      const P = sc.params, to = +P.to, from = +(P.from || 0), dec = P.decimals || 0, fmt = v => (dec ? v.toFixed(dec) : Math.round(v).toString()) + (P.suffix || ''), v = lerp(from, to, eOutCubic(seg(lt, .1, 1.4)));
      if (P.label) { c.globalAlpha = eOutExpo(seg(lt, -.1, .3)); mono(c, P.label, 80, 520, 32, pal.ink); c.globalAlpha = 1; }
      const fin = fmt(to), sz = fitSize(c, fin, FR, P.size || 420, 920); c.font = FR(sz); c.fillStyle = pal.acc; c.fillText(fmt(v), 80, 600 + sz * .8);
      const pb = eOutExpo(seg(lt, .4, 1.0)); c.fillStyle = pal.ink; c.fillRect(80, 600 + sz * .92 + 24, 920 * pb, 12);
      (P.sub || '').split('\n').forEach((t, i) => maskLine(c, t, BR, fitSize(c, t, BR, 100, 920), 80, 600 + sz * .92 + 80 + i * 110, pal.ink, eOutExpo(seg(lt, 1.0 + i * .15, 1.5 + i * .15))));
      if (P.note) mono(c, P.note, 80, 1480, 24, pal.mute);
    }
  },
  // params.title?, params.steps [2-4 short strings]: boxes joined by arrows
  steps: {
    draw(c, lt, sc, { pal }) {
      const P = sc.params, st = P.steps || [], n = st.length; titleLine(c, P, lt, pal); const y0 = P.title ? 520 : 380, bh = 170, step = Math.min(330, (1060 - bh) / Math.max(n - 1, 1));
      st.forEach((t, i) => {
        const t0 = .25 + i * .5, p = eOutExpo(seg(lt, t0, t0 + .4)), y = y0 + i * step; if (i > 0) { const pa = eOutExpo(seg(lt, t0 - .2, t0 + .1)), ya = y0 + (i - 1) * step + bh; if (pa > 0) { line(c, 540, ya + 6, 540, ya + 6 + (step - bh - 12) * pa, 6, pal.ink); if (pa > .9) { c.fillStyle = pal.ink; c.beginPath(); c.moveTo(540, y - 4); c.lineTo(522, y - 30); c.lineTo(558, y - 30); c.closePath(); c.fill(); } } }
        if (p <= 0) return; const last = i === n - 1; c.save(); c.beginPath(); c.rect(80, y, 920 * p, bh); c.clip();
        if (last) { c.fillStyle = pal.acc; c.fillRect(80, y, 920, bh); } else { c.fillStyle = pal.soft; c.fillRect(80, y, 920, bh); c.strokeStyle = pal.ink; c.lineWidth = 4; c.strokeRect(82, y + 2, 916, bh - 4); }
        const ink = last ? pal.paper : pal.ink; mono(c, num2(i), 120, y + bh / 2 + 12, 34, last ? pal.paper : pal.acc); c.font = BR(fitSize(c, t, BR, 84, 700)); c.fillStyle = ink; c.fillText(t, 230, y + bh / 2 + 28); c.restore();
      });
    }
  },
});

// ---- stage: ONE focal object at a time (a prop from the shared library) + a <=3 word label; beats follow the narration
// params.beats: [{cue:'word' | t:seconds, prop, label, slot:'c'|'l'|'r', move:'pop'|'drop'|'slide', anim:{on:1}}]. A new beat in a slot replaces what was there.
export function beatTimes(sc) {
  if (sc.__beats) return sc.__beats; const words = (sc.lines || []).flatMap(l => l.words || []), nm = w => w.w.toLowerCase().replace(/[^a-z0-9']/g, ''); let prev = -1;
  sc.__beats = (sc.params.beats || []).map((b, i) => { let t; if (typeof b.t === 'number') t = b.t; else if (b.cue) { const w = words.find(x => x.s - sc.start >= prev + .05 && nm(x) === String(b.cue).toLowerCase()); t = w ? w.s - sc.start - .06 : Math.max(prev, 0) + 1.5; } else t = i ? prev + 1.5 : 0; t = Math.max(0, t); prev = t; return { ...b, t }; });
  return sc.__beats;
}
const SLOT = { c: [540, 840, 560], l: [290, 840, 340], r: [790, 840, 340] };
Object.assign(kinds, {
  stage: {
    draw(c, lt, sc, { pal }) {
      const B = beatTimes(sc), lr = B.filter(b => b.slot === 'l' || b.slot === 'r').map(b => b.t), firstLR = lr.length ? Math.min(...lr) : 1e9, slots = {};
      B.forEach(b => { const s = b.slot || 'c'; if (b.t > lt) return; if (s === 'c' && lt >= firstLR) return; (slots[s] = slots[s] || []).push(b); });
      const show = (b, age, out) => {
        const spec = PROPS[b.prop]; if (!spec) return; const s = b.slot || 'c', dual = lt >= firstLR && s !== 'c', [x0, y0, sz0] = SLOT[s] || SLOT.c, mv = b.move || 'pop';
        let dx = 0, dy = 0, k = 1; if (mv === 'drop') { const q = eOutBack(clamp(age / .55), 1.7); dy = (1 - q) * -700; } else if (mv === 'slide') { dx = (1 - eOutExpo(clamp(age / .5))) * 520; } else { k = eOutBack(clamp(age / .5), 2); }
        dy += Math.sin(age * 2.3) * 9; let al = clamp(age / .15); if (out != null) { dx += (s === 'r' ? 1 : -1) * out * 520; al = 1 - out; }
        c.save(); c.globalAlpha = al; drawProp(c, spec, x0 + dx, y0 + dy, sz0 * Math.max(k, .001), pal, { on: eOutCubic(seg(age, .35, 1.0)), ...(b.anim || {}) }); c.restore();
        if (b.label && out == null) { const sz = fitSize(c, b.label, BR, 96, s === 'c' ? 900 : 400), p = eOutExpo(seg(age, .15, .55)); maskLine(c, b.label, BR, sz, x0, y0 + sz0 * .62 + 40, pal.ink, p, 'center', s === 'c' ? 960 : 420); if (p > 0) { c.font = BR(sz); const w = c.measureText(b.label).width; c.fillStyle = pal.acc; c.fillRect(x0 - w / 2 * p, y0 + sz0 * .62 + 40 + sz * .98, w * p, 10); } }
      };
      for (const s in slots) { const a = slots[s], cur = a[a.length - 1], prv = a[a.length - 2]; if (prv && lt - cur.t < .3) show(prv, lt - prv.t, eInOut((lt - cur.t) / .3)); show(cur, lt - cur.t, null); }
      if (firstLR < 1e9 && lt >= firstLR && lt < firstLR + .3) { const a = B.filter(b => (b.slot || 'c') === 'c' && b.t < firstLR), prv = a[a.length - 1]; if (prv) show(prv, lt - prv.t, eInOut((lt - firstLR) / .3)); }
    }
  },
});

export default {
  name: 'A', title: 'Type + Data', palettes, kinds,
  background(c, t, { pal, tl }) {
    c.fillStyle = pal.paper; c.fillRect(0, 0, 1080, 1920);
    const g = eOutExpo(seg(t, 0, .5)); line(c, 48, 120, 48 + 984 * g, 120, 3, pal.ink); line(c, 48, 1840, 48 + 984 * g, 1840, 3, pal.ink);
    c.globalAlpha = clamp(g * 1.5); mono(c, `FIELD NOTE ${String(tl.v2.number || 1).padStart(2, '0')}`, 48, 100, 24, pal.ink); mono(c, tl.v2.kicker || 'ABOUT AI', 1032, 100, 24, pal.ink, 'right');
    mono(c, tl.v2.footer || 'FREDSDESK', 48, 1882, 24, pal.mute); c.globalAlpha = 1;
  },
  // hard vertical wipe: the new scene is revealed behind a bar of accent colour
  wipe(c, p, { pal }, drawNew) {
    const x = 1080 * eInOut(p); c.save(); c.beginPath(); c.rect(0, 0, x, 1920); c.clip(); c.fillStyle = pal.paper; c.fillRect(0, 0, 1080, 1920); drawNew(); c.restore();
    c.fillStyle = pal.acc; c.fillRect(Math.max(0, x - 26), 0, 26, 1920);
  },
  // word-timed caption at the bottom: the chunk is visible, the word being spoken gets an accent bar, keywords are accent coloured
  captions(c, t, ch, { pal }) {
    const size = 66, maxW = 920, a = eOutExpo(seg(t, ch.s - .05, ch.s + .12)), y0 = 1640; c.font = BR(size);
    const words = ch.words.map(w => ({ ...w, wid: c.measureText(w.w + ' ').width })); let x = 80, y = y0; const lay = [];
    words.forEach(w => { if (x + w.wid - c.measureText(' ').width > 80 + maxW && x > 80) { x = 80; y += size * 1.2; } lay.push({ ...w, x, y }); x += w.wid; });
    c.save(); c.beginPath(); c.rect(60, y0 - size, 960, size * 2.6); c.clip(); c.translate(0, (1 - a) * 24); c.textBaseline = 'alphabetic';
    lay.forEach(w => { c.font = BR(size); c.fillStyle = w.k ? pal.acc : pal.ink; c.fillText(w.w, w.x, w.y); if (t >= w.s && t < w.e + .02) { c.fillStyle = pal.acc; c.fillRect(w.x, w.y + 12, c.measureText(w.w).width, 8); } });
    c.restore();
  },
};
