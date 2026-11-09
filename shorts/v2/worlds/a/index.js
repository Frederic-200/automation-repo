// WORLD A - "Type + Data" (v2 scene kinds). Swiss-poster typography on a coloured paper, hard masked reveals, data panels.
// Motion grammar: masked line reveals, expo/linear wipes, bars that shoot or crawl. No springs, no figure, no hero object.
// Scene kinds: headline, bars, stat, finale.   Captions: word-timed plain type at the bottom.
import { clamp, lerp, seg, eInOut, eOutExpo, eOutCubic, vnoise } from '/proto/worlds/util.js';

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
