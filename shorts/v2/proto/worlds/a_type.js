// WORLD A - "Type + Data": Swiss-poster typography on warm paper, hard masked reveals, a data panel with a hatched gap.
// Motion grammar: linear/expo wipes and masked line reveals. No springs, no bouncing hero object, no figure.
import { clamp, lerp, seg, eInOut, eOutExpo, eOutCubic, vnoise } from '/worlds/util.js';

export async function init({ canvas, W, H }) {
  const x = canvas.getContext('2d'), S = W / 1080;
  const INK = '#121212', PAPER = '#F1EDE4', ACC = '#FF4A1C', MUTE = '#B9B3A6';
  const noise = vnoise(11);
  const BR = s => `800 ${s}px Bricolage`, FR = s => `italic 900 ${s}px Fraunces`, MONO = s => `700 ${s}px JBMono`;
  // headline: [text, font fn, base size, colour]
  const LINES = [['WHY DOES', BR, 160, INK], ['AI SOUND', BR, 160, INK], ['SO SURE', FR, 240, ACC], ["WHEN IT'S", BR, 160, INK], ['WRONG?', BR, 240, INK]];
  const MAXW = 920;
  x.textBaseline = 'alphabetic';
  const sizes = LINES.map(([t, f, b]) => { x.font = f(b); return b * Math.min(1, MAXW / x.measureText(t).width); });
  const tops = []; let cum = 0; LINES.forEach((l, i) => { tops.push(cum); cum += sizes[i] * .92; });
  const headH = cum;

  const line = (x1, y1, x2, y2, w = 2, c = INK) => { x.strokeStyle = c; x.lineWidth = w; x.beginPath(); x.moveTo(x1, y1); x.lineTo(x2, y2); x.stroke(); };
  const mono = (s, px, py, size = 26, c = INK, align = 'left') => { x.font = MONO(size); x.fillStyle = c; x.textAlign = align; x.fillText(s, px, py); x.textAlign = 'left'; };

  function headline(t, pHead) {
    x.save(); const sc = lerp(1, .50, pHead); x.translate(80, lerp(250, 190, pHead)); x.scale(sc, sc);
    LINES.forEach(([txt, f, , col], i) => {
      const a0 = .3 + i * .17, p = eOutExpo(seg(t, a0, a0 + .6)); if (p <= 0) return;
      const sz = sizes[i], h = sz * .92;
      x.save(); x.beginPath(); x.rect(-20, tops[i], 1100, h + 6); x.clip();
      x.translate(0, (1 - p) * h); x.font = f(sz); x.fillStyle = col; x.fillText(txt, 0, tops[i] + sz * .78); x.restore();
    });
    // accent bar that underlines the last word
    const pb = eOutExpo(seg(t, 1.7, 2.2)); if (pb > 0) { x.font = BR(sizes[4]); const w = x.measureText('WRONG?').width; x.fillStyle = ACC; x.fillRect(0, tops[4] + sizes[4] * .92 + 4, w * pb, 24); }
    x.restore();
  }

  function chart(t) {
    const y1 = 900, y2 = 1200, bh = 140, X0 = 80, FULL = 920;
    const a = eOutExpo(seg(t, 3.0, 3.35)); if (a <= 0) return;
    x.globalAlpha = a;
    mono('WHAT IT SOUNDS LIKE', X0, y1 - 28, 30); mono('HOW OFTEN IT IS RIGHT', X0, y2 - 28, 30);
    [y1, y2].forEach(y => { x.fillStyle = 'rgba(18,18,18,.08)'; x.fillRect(X0, y, FULL, bh); for (let k = 0; k <= 10; k++) line(X0 + k * FULL / 10, y + bh, X0 + k * FULL / 10, y + bh + (k % 5 ? 10 : 20), 2); });
    x.globalAlpha = 1;
    // confidence: shoots to the end and stays dead still
    const p1 = eOutExpo(seg(t, 3.3, 3.8)); x.fillStyle = ACC; x.fillRect(X0, y1, FULL * p1, bh);
    // accuracy: crawls, then wobbles around a lower value
    const g = eOutCubic(seg(t, 3.6, 4.7)), wob = seg(t, 4.7, 9) > 0 ? (noise(t * 5) - .5) * 90 + Math.sin(t * 9) * 14 : 0, w2 = FULL * .56 * g + wob * g;
    x.fillStyle = INK; x.fillRect(X0, y2, Math.max(0, w2), bh);
    // the hatched gap
    const pg = eOutExpo(seg(t, 4.9, 5.5));
    if (pg > 0) {
      const gx0 = X0 + w2, gx1 = X0 + FULL * p1;
      x.save(); x.beginPath(); x.rect(gx0, y2, (gx1 - gx0) * pg, bh); x.clip(); x.strokeStyle = ACC; x.lineWidth = 6;
      for (let k = -200; k < FULL; k += 26) { x.beginPath(); x.moveTo(gx0 + k, y2 + bh); x.lineTo(gx0 + k + bh, y2); x.stroke(); } x.restore();
      x.globalAlpha = pg; line(gx0, y2 + bh + 70, gx1, y2 + bh + 70, 4, ACC); line(gx0, y2 + bh + 56, gx0, y2 + bh + 84, 4, ACC); line(gx1, y2 + bh + 56, gx1, y2 + bh + 84, 4, ACC);
      mono('THE GAP', (gx0 + gx1) / 2, y2 + bh + 130, 40, ACC, 'center'); x.globalAlpha = 1;
    }
    mono('ILLUSTRATION. NOT REAL DATA.', X0, 1640, 24, '#6f6a5e');
  }

  function finale(t) {
    const p = eInOut(seg(t, 6.4, 7.1)); if (p <= 0) return;
    const top = lerp(1920, 0, p); x.fillStyle = INK; x.fillRect(0, top, 1080, 1920 - top);
    const reveal = (txt, font, size, cx, base, t0, col = PAPER) => {
      const r = eOutExpo(seg(t, t0, t0 + .5)); if (r <= 0) return; x.save(); x.beginPath(); x.rect(0, base - size * .85, 1080, size * 1.0); x.clip();
      x.font = font(size); const fw = x.measureText(txt).width, k = Math.min(1, 900 / fw); x.translate(0, (1 - r) * size); x.font = font(size * k); x.fillStyle = col; x.textAlign = 'center'; x.fillText(txt, cx, base); x.restore();
    };
    x.save(); x.translate(0, 0);
    reveal('SOUNDING', BR, 190, 540, 700, 7.0); reveal('SURE', FR, 330, 540, 980, 7.15, ACC);
    // "is not" sign: two bars, then the slash cuts through
    const ps = eOutExpo(seg(t, 7.6, 8.1)); if (ps > 0) { x.strokeStyle = PAPER; x.lineWidth = 26; x.lineCap = 'butt'; const w = 150 * ps; [1130, 1190].forEach(y => { x.beginPath(); x.moveTo(540 - w, y); x.lineTo(540 + w, y); x.stroke(); }); }
    const pl = eOutExpo(seg(t, 8.0, 8.35)); if (pl > 0) { x.strokeStyle = ACC; x.lineWidth = 26; x.beginPath(); x.moveTo(540 - 70 * pl, 1230 + 0 * pl); x.lineTo(540 + 70 * pl, 1090 - 0 * pl); x.stroke(); x.lineCap = 'butt'; }
    reveal('BEING', BR, 190, 540, 1470, 8.2); reveal('RIGHT', BR, 190, 540, 1660, 8.35);
    x.restore();
    // closing sweep
    const pc = eInOut(seg(t, 9.35, 9.9)); if (pc > 0) { x.fillStyle = ACC; x.fillRect(0, 0, 1080 * pc, 1920); }
  }

  return {
    frame(t) {
      x.setTransform(S, 0, 0, S, 0, 0); x.fillStyle = PAPER; x.fillRect(0, 0, 1080, 1920);
      // frame rules and labels
      const g = eOutExpo(seg(t, 0, .7)); line(48, 120, 48 + 984 * g, 120, 3); line(48, 1840, 48 + 984 * g, 1840, 3);
      x.globalAlpha = clamp(g * 1.5); mono('FIELD NOTE 07', 48, 100, 24); mono('ABOUT AI', 1032, 100, 24, INK, 'right'); mono('CONFIDENCE VS TRUTH', 48, 1882, 24, '#6f6a5e'); x.globalAlpha = 1;
      headline(t, eInOut(seg(t, 2.5, 3.2)));
      x.save(); const clipW = 1080 * (1 - eInOut(seg(t, 6.3, 6.9))); x.beginPath(); x.rect(0, 700, clipW, 1200); x.clip(); chart(t); x.restore();
      finale(t);
    }
  };
}
