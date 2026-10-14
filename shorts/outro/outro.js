/* FredsDesk outro world (3 s). BRAND is injected by outro_build.py (geometry + colors from brand/brand.json).
   Images (served from the work dir): brand_icon.png (desk+monitor, cursor removed), brand_cursor.png, brand_word.png.
   Colors adapt to the video's background: dark bg -> light logo, light bg -> original navy/teal. */
'use strict';
const _OA = {};
function oimg(n) { if (!_OA[n]) { const im = new Image(); im.src = (new URLSearchParams(location.search).get('w') || '/w/') + n; _OA[n] = im; } return _OA[n]; }
['brand_icon.png', 'brand_cursor.png', 'brand_word.png'].forEach(oimg);
const _OC = {};
function ocan(n, w, h) { let c = _OC[n]; if (!c) { c = _OC[n] = document.createElement('canvas'); } if (c.width !== w || c.height !== h) { c.width = w; c.height = h; } const g = c.getContext('2d'); g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1; g.clearRect(0, 0, w, h); return [c, g]; }

SCENES.outro = (t, lt, sc, e) => {
  bgFill(e);
  const B = BRAND, icon = oimg('brand_icon.png'), cur = oimg('brand_cursor.png'), word = oimg('brand_word.png');
  if (!(icon.complete && icon.naturalWidth && cur.complete && word.complete && word.naturalWidth)) return;
  const dark = lum(e.bg[0]) < .5, teal = dark ? mixc(B.teal, '#ffffff', .12) : B.teal;
  const cA = dark ? mixc(B.teal, '#ffffff', .62) : B.navy, cB = teal, wordA = dark ? '#ffffff' : B.navy, accent = S.accent;
  const IS = 1.9, ix = CX - B.icon.w * IS / 2, iy = 470, iw = B.icon.w * IS, ih = B.icon.h * IS;
  const g = lt < 0 ? 0 : lt, ss = (a, b) => smooth((g - a) / (b - a));
  // soft stage glow behind the logo
  glowDot(CX, iy + ih * .45, 620, accent, .05 + .08 * ss(1.3, 1.9) * (1 - ss(2.4, 3.0) * .5));

  /* ---- icon: desk draws on (0.3-1.0 s), monitor boots (1.0-1.3 s) ---- */
  const [ic, ig] = ocan('icon', Math.ceil(iw), Math.ceil(ih));
  ig.drawImage(icon, 0, 0, iw, ih);
  const splitY = 132 * IS, deskP = ss(.3, 1.0), monP = ss(1.0, 1.3);
  // reveal mask: desk = left->right wipe of the lower part, monitor = top->down wipe of the upper part
  ig.globalCompositeOperation = 'destination-in'; ig.fillStyle = '#000';
  ig.beginPath(); ig.rect(0, splitY, iw * deskP, ih - splitY); ig.rect(0, 0, iw, monP > 0 ? splitY * monP + 4 : 0); ig.fill();
  // flicker while the screen boots
  const flick = monP > 0 && monP < 1 ? (.55 + .45 * Math.abs(Math.sin(g * 70))) : 1;
  ig.globalCompositeOperation = 'source-in'; const gr = ig.createLinearGradient(0, 0, iw, 0); gr.addColorStop(0, cA); gr.addColorStop(1, cB); ig.fillStyle = gr; ig.fillRect(0, 0, iw, ih);
  x.globalAlpha = flick; x.drawImage(ic, ix, iy); x.globalAlpha = 1;
  // pen glow riding the desk wipe
  if (deskP > 0 && deskP < 1) { const px = ix + iw * deskP, py = iy + 175 * IS; glowDot(px, py, 90, '#ffffff', .85); glowDot(px, py, 200, accent, .35); }
  // screen glow after the click
  const clickT = 1.55, since = g - clickT;
  if (since > 0) { const a = Math.min(1, since / .15) * (.28 - .12 * ss(1.8, 3.0)); x.save(); x.beginPath(); x.rect(ix + 96 * IS, iy + 12 * IS, 170 * IS, 108 * IS); x.clip(); glowDot(ix + 180 * IS, iy + 66 * IS, 300, accent, a * 1.6); x.restore(); }

  /* ---- cursor: curves in (1.3-1.55 s), presses on the click, ripple ---- */
  const cw = B.cursor.w * IS, ch = B.cursor.h * IS, rx = ix + B.cursor.x * IS, ry = iy + B.cursor.y * IS;
  const p = clamp((g - 1.2) / .35), ep = easeOutQuart(p);
  const sx = rx + 520, sy = ry + 560, mx = rx + 260, my = ry + 80;       // start (off-screen low right), control point
  const cxp = (1 - ep) * (1 - ep) * sx + 2 * (1 - ep) * ep * mx + ep * ep * rx, cyp = (1 - ep) * (1 - ep) * sy + 2 * (1 - ep) * ep * my + ep * ep * ry;
  const press = since > 0 ? 1 - .22 * Math.exp(-since * 14) * Math.cos(since * 22) : 1;
  if (g > 1.2) { x.save(); x.translate(cxp + cw * .12, cyp + ch * .06); x.scale(press, press); x.translate(-cw * .12, -ch * .06);
    const [cc, cg] = ocan('cur', Math.ceil(cw), Math.ceil(ch)); cg.drawImage(cur, 0, 0, cw, ch); cg.globalCompositeOperation = 'source-in'; cg.fillStyle = dark ? '#ffffff' : cA; cg.fillRect(0, 0, cw, ch);
    x.shadowColor = 'rgba(0,0,0,.35)'; x.shadowBlur = 14; x.shadowOffsetY = 6; x.drawImage(cc, 0, 0); x.restore(); }
  if (since > 0) { const tx = rx + cw * .12, ty = ry + ch * .06; ring(tx, ty, easeOutExpo(since / .6) * 150, 8 * (1 - since / .6) + 1, accent, clamp(1 - since / .6)); if (since < .25) glowDot(tx, ty, 90 * (1 - since / .25) + 20, '#ffffff', .9 * (1 - since / .25)); }

  /* ---- wordmark: letters rise in (1.7-2.3 s), "Freds" / "Desk" colors ---- */
  const WS = 1.1, wy = iy + ih + 60, wxl = CX - B.word.w * WS / 2, [wc, wg] = ocan('word', Math.ceil(B.word.w * WS) + 40, Math.ceil(B.word.h * WS) + 80);
  B.letters.forEach(([a, b], i) => { const t0 = 1.7 + i * .065, k = clamp((g - t0) / .28); if (k <= 0) return;
    const rise = (1 - easeOutBack(k, 2.2)) * 46, sw = (b - a + 1) * WS;
    const [lc, lg] = ocan('letter', Math.ceil(sw) + 4, Math.ceil(B.word.h * WS) + 4);
    lg.drawImage(word, a, 0, b - a + 1, B.word.h, 0, 0, sw, B.word.h * WS); lg.globalCompositeOperation = 'source-in'; lg.fillStyle = i < 5 ? wordA : cB; lg.fillRect(0, 0, lc.width, lc.height);
    wg.globalAlpha = clamp(k * 2.2); wg.drawImage(lc, 20 + a * WS, 40 + rise); wg.globalAlpha = 1; });
  // light sweep across the wordmark (2.55-3.0 s)
  const sw0 = ss(2.55, 3.0); if (sw0 > 0 && sw0 < 1) { wg.globalCompositeOperation = 'source-atop'; const sxp = -200 + (wc.width + 400) * sw0, gs = wg.createLinearGradient(sxp - 90, 0, sxp + 90, 0);
    gs.addColorStop(0, 'rgba(255,255,255,0)'); gs.addColorStop(.5, 'rgba(255,255,255,.75)'); gs.addColorStop(1, 'rgba(255,255,255,0)'); wg.fillStyle = gs; wg.fillRect(0, 0, wc.width, wc.height); wg.globalCompositeOperation = 'source-over'; }
  x.drawImage(wc, wxl - 20, wy - 40);

  /* ---- call to action + blinking cursor (2.3 s on) ---- */
  const ck = clamp((g - 2.3) / .35);
  if (ck > 0) { const fam = S.fonts.text, wt = S.fonts.text_weight, size = 54, txt = BRAND.cta; x.font = `${wt} ${size}px "${fam}"`; x.textBaseline = 'middle'; x.textAlign = 'left';
    const tw = x.measureText(txt).width, cx0 = CX - (tw + 36) / 2, cyy = wy + B.word.h * WS + 105, n = Math.floor(clamp((g - 2.3) / .4) * txt.length);
    x.save(); x.globalAlpha = easeOutExpo(ck); x.translate(0, (1 - easeOutExpo(ck)) * 18);
    x.fillStyle = dark ? 'rgba(255,255,255,.88)' : e.ink === '#ffffff' ? B.navy : e.ink; x.fillText(txt.slice(0, n), cx0, cyy);
    if (Math.floor(g * 2.4) % 2 === 0 || g < 2.8) { x.fillStyle = accent; x.fillRect(cx0 + x.measureText(txt.slice(0, n)).width + 8, cyy - size * .42, size * .36, size * .84); }
    x.restore(); }
};
