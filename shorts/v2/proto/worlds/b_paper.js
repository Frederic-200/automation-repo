// WORLD B - "Paper cut-out": layered torn paper with real shadows and parallax, cut-letter text, a bubble that tears open.
// Motion grammar: layers slide and drift at different speeds (depth), things drop in and settle, paper tears. Earthy palette, no neon.
import { clamp, lerp, seg, eInOut, eOutExpo, eOutCubic, eOutBack, rng, vnoise } from '/worlds/util.js';

export async function init({ canvas, W, H }) {
  const x = canvas.getContext('2d'), S = W / 1080;
  const CREAM = '#F3E5C8', SAGE = '#9DB08A', MUSTARD = '#E3A93B', TERRA = '#C8553D', PLUM = '#4A2B47', INK = '#2B1B2B', WHITE = '#FFF8EA';
  const FR = s => `900 ${s}px Fraunces`, MONO = s => `700 ${s}px JBMono`;

  // ---- pre-baked paper grain (seeded) ----
  const grain = document.createElement('canvas'); grain.width = 256; grain.height = 256; {
    const g = grain.getContext('2d'), r = rng(5), im = g.createImageData(256, 256);
    for (let i = 0; i < im.data.length; i += 4) { const v = 200 + r() * 55; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255; }
    g.putImageData(im, 0, 0);
  }
  const pattern = x.createPattern(grain, 'repeat');

  // ---- torn-edge hills: each layer is a noisy top edge, built once ----
  const LAYERS = [
    { col: SAGE, base: 1010, amp: 150, seed: 3, depth: .25, rise: .0 },
    { col: MUSTARD, base: 1230, amp: 130, seed: 9, depth: .5, rise: .12 },
    { col: TERRA, base: 1430, amp: 120, seed: 14, depth: .8, rise: .24 },
    { col: PLUM, base: 1640, amp: 90, seed: 21, depth: 1.2, rise: .36 },
  ];
  LAYERS.forEach(L => {
    const n1 = vnoise(L.seed), n2 = vnoise(L.seed + 100), r = rng(L.seed + 7); L.pts = [];
    for (let px = -140; px <= 1220; px += 12) L.pts.push([px, L.base - (n1(px / 230) - .5) * 2 * L.amp - (n2(px / 47) - .5) * 26 + (r() - .5) * 7]);
  });
  function layer(L, t, camS) {
    const rise = eOutCubic(seg(t, L.rise, L.rise + .7)), dy = (1 - rise) * 800, dx = Math.sin(t * .55 + L.seed) * 36 * L.depth + (t - 5) * 8 * L.depth;
    x.save(); x.translate(dx, dy);
    x.shadowColor = 'rgba(40,20,20,.45)'; x.shadowBlur = 30; x.shadowOffsetY = -6;
    x.fillStyle = L.col; x.beginPath(); x.moveTo(-160, 2100); L.pts.forEach(([px, py]) => x.lineTo(px, py)); x.lineTo(1240, 2100); x.closePath(); x.fill();
    x.shadowColor = 'transparent';
    x.fillStyle = pattern; x.globalAlpha = .12; x.globalCompositeOperation = 'multiply'; x.fill(); x.globalCompositeOperation = 'source-over'; x.globalAlpha = 1;
    x.strokeStyle = 'rgba(255,248,234,.75)'; x.lineWidth = 3; x.beginPath(); L.pts.forEach(([px, py], i) => i ? x.lineTo(px, py - 2) : x.moveTo(px, py - 2)); x.stroke();   // torn fibre edge
    x.restore();
  }

  // ---- cut letters: every glyph is its own piece of paper, a little rotated, with a shadow ----
  const rl = rng(33);
  function cutText(txt, cx, cy, size, tiles, t0, t, rotSeed = 0, gap = .08) {
    x.font = FR(size); const ws = [...txt].map(ch => x.measureText(ch).width + size * gap), tot = ws.reduce((a, b) => a + b, 0); let px = cx - tot / 2;
    [...txt].forEach((ch, i) => {
      const lw = ws[i], r1 = Math.sin(i * 12.9898 + rotSeed) * .12, r2 = Math.sin(i * 78.233 + rotSeed) * size * .05, d = clamp((t - t0 - i * .06) / .35), pop = eOutBack(d, 2.4);
      px += lw / 2;
      if (d > 0 && ch !== ' ') {
        x.save(); x.translate(px, cy + r2 + (1 - pop) * -140); x.rotate(r1 + (1 - d) * .5); x.scale(pop, pop);
        x.shadowColor = 'rgba(40,20,20,.35)'; x.shadowBlur = size * .05; x.shadowOffsetY = size * .04;
        x.textAlign = 'center'; x.strokeStyle = tiles; x.lineJoin = 'round'; x.lineWidth = size * .2; x.strokeText(ch, 0, size * .34);
        x.shadowColor = 'transparent'; x.fillStyle = INK; x.textAlign = 'center'; x.fillText(ch, 0, size * .34); x.restore();
      }
      px += lw / 2;
    });
    x.textAlign = 'left';
  }

  function blob(cx, cy, w, h, wob, seed) { // wobbly rounded paper shape
    const n = vnoise(seed), pts = [], N = 40;
    for (let i = 0; i < N; i++) { const a = i / N * Math.PI * 2, rx = w / 2 * (1 + (n(i * .9) - .5) * wob), ry = h / 2 * (1 + (n(i * .9 + 50) - .5) * wob); pts.push([cx + Math.cos(a) * rx, cy + Math.sin(a) * ry]); }
    x.beginPath(); pts.forEach(([a, b], i) => i ? x.lineTo(a, b) : x.moveTo(a, b)); x.closePath();
  }

  // paper question marks drifting down behind the bubble
  const Q = Array.from({ length: 16 }, (_, i) => ({ x: 80 + rl() * 920, s: 80 + rl() * 110, sp: 150 + rl() * 170, ph: rl() * 800, rot: (rl() - .5) * .9, col: [WHITE, MUSTARD, TERRA, SAGE][i % 4], t0: 2.0 + rl() * 1.6 }));

  return {
    frame(t) {
      x.setTransform(S, 0, 0, S, 0, 0);
      // camera dolly: slow push toward the centre of the page
      const cam = 1 + .07 * (t / 10); x.save(); x.translate(540, 960); x.scale(cam, cam); x.translate(-540, -960);
      x.fillStyle = CREAM; x.fillRect(-100, -100, 1280, 2120);
      x.fillStyle = pattern; x.globalAlpha = .1; x.globalCompositeOperation = 'multiply'; x.fillRect(-100, -100, 1280, 2120); x.globalCompositeOperation = 'source-over'; x.globalAlpha = 1;

      LAYERS.slice(0, 2).forEach(L => layer(L, t, cam));

      // falling paper question marks (they land between the hill layers)
      Q.forEach(q => { const d = t - q.t0; if (d < 0) return; const y = -80 + ((d * q.sp + q.ph) % 1500);
        x.save(); x.translate(q.x, y); x.rotate(q.rot + d * .3); x.font = FR(q.s); x.textAlign = 'center';
        x.shadowColor = 'rgba(40,20,20,.4)'; x.shadowBlur = 10; x.shadowOffsetY = 6; x.strokeStyle = WHITE; x.lineJoin = 'round'; x.lineWidth = q.s * .16; x.strokeText('?', 0, q.s * .34);
        x.shadowColor = 'transparent'; x.fillStyle = q.col === WHITE ? INK : q.col; x.fillText('?', 0, q.s * .34); x.restore(); });

      // ---- the confident bubble ----
      const bp = eOutBack(seg(t, .55, 1.2), 1.9), tear = eInOut(seg(t, 3.7, 4.5)), gone = eInOut(seg(t, 6.6, 7.4));
      if (bp > 0 && gone < 1) {
        const cx = 540, cy = 640 - gone * 900, w = 880, h = 470;
        [[-1, 'L'], [1, 'R']].forEach(([side]) => {
          x.save(); x.translate(cx + side * tear * 230, cy + tear * 40); x.rotate(side * tear * .22); x.scale(bp, bp);
          x.beginPath(); x.rect(side < 0 ? -w : 0, -h, w, h * 2); x.clip();   // each half is a clip of the same bubble, cut along a jagged line
          x.shadowColor = 'rgba(40,20,20,.5)'; x.shadowBlur = 36; x.shadowOffsetY = 18; x.fillStyle = WHITE; blob(0, 0, w, h, .1, 4); x.fill(); x.shadowColor = 'transparent';
          x.fillStyle = pattern; x.globalAlpha = .13; x.globalCompositeOperation = 'multiply'; x.fill(); x.globalCompositeOperation = 'source-over'; x.globalAlpha = 1;
          x.restore();
        });
        // cut letters ride on top, split with the halves
        if (tear < .02) cutText("I'M SURE.", cx, cy - 10, 150, MUSTARD, 1.0, t, 1);
        else { x.save(); x.translate(cx - tear * 230, cy + tear * 40); x.rotate(-tear * .22); x.beginPath(); x.rect(-1000, -500, 1000, 1000); x.clip(); x.translate(-(cx - cx), 0); cutText("I'M SURE.", tear * 230, -10 - tear * 40 + 0, 150, MUSTARD, -9, t, 1); x.restore();
          x.save(); x.translate(cx + tear * 230, cy + tear * 40); x.rotate(tear * .22); x.beginPath(); x.rect(0, -500, 1000, 1000); x.clip(); cutText("I'M SURE.", -tear * 230, -10 - tear * 40, 150, MUSTARD, -9, t, 1); x.restore(); }
      }

      // ---- the torn-open note underneath ----
      const np = eOutBack(seg(t, 4.1, 4.9), 2), nOut = eInOut(seg(t, 8.5, 9.2));
      if (np > 0) {
        x.save(); x.translate(540, 700 + nOut * 300); x.rotate(-.05); x.scale(np, np);
        x.shadowColor = 'rgba(40,20,20,.5)'; x.shadowBlur = 26; x.shadowOffsetY = 14; x.fillStyle = '#FBF1D6'; x.beginPath(); x.rect(-400, -190, 800, 380); x.fill(); x.shadowColor = 'transparent';
        x.fillStyle = pattern; x.globalAlpha = .1; x.globalCompositeOperation = 'multiply'; x.fill(); x.globalCompositeOperation = 'source-over'; x.globalAlpha = 1;
        // tape
        x.save(); x.translate(0, -190); x.rotate(.06); x.fillStyle = 'rgba(227,169,59,.75)'; x.fillRect(-90, -26, 180, 52); x.restore();
        x.fillStyle = INK; x.font = MONO(70); x.textAlign = 'center';
        const full = 'OR JUST GUESSING?', n = Math.floor(clamp((t - 4.9) / 1.4) * full.length); x.fillText(full.slice(0, 8).slice(0, n), 0, -20); if (n > 8) x.fillText(full.slice(8, n), 0, 80);
        if (Math.floor(t * 2.4) % 2 === 0 && t < 8) { x.fillStyle = TERRA; x.fillRect(-330 + 0, 118, 24, 8); }
        x.restore();
      }

      LAYERS.slice(2).forEach(L => layer(L, t, cam));
      // tagline cut into the plum hill
      cutText('SURE', 540, 1690, 84, WHITE, 7.7, t, 4, .24); cutText('IS NOT RIGHT', 540, 1795, 84, WHITE, 8.1, t, 8, .24);
      x.restore();
      // vignette
      const gr = x.createRadialGradient(540, 960, 600, 540, 960, 1250); gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(1, 'rgba(40,16,24,.28)'); x.fillStyle = gr; x.fillRect(0, 0, 1080, 1920);
    }
  };
}
