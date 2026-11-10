// World B style for props: every shape is a piece of cut paper with its own shadow, so a prop reads as layered paper. Same specs as style_a.
// grain(c, a): optional callback that fills the current path with paper grain (supplied by the world).
export function drawProp(c, spec, cx, cy, size, pal, anim = {}, grain = null) {
  const s = size / 2, SHC = a => `rgba(40,20,20,${a})`;
  const col = r => ({ main: pal.panel, ink: pal.ink, acc: pal.acc, paper: pal.white, soft: pal.tiles[1], glass: pal.tiles[0] }[r] || pal.ink);
  c.save(); c.translate(cx, cy); c.scale(s, s); c.lineJoin = 'round'; c.lineCap = 'round';
  const sh0 = { b: 10, y: 6 };
  spec.forEach((sh, n) => {
    c.save(); if (sh.mv) for (const k in sh.mv) c.translate(sh.mv[k][0] * (anim[k] || 0), sh.mv[k][1] * (anim[k] || 0));
    const fill = col(sh.c); c.fillStyle = fill; c.strokeStyle = fill; if (sh.c === 'glass') c.globalAlpha = .55;
    c.shadowColor = SHC(.38); c.shadowBlur = sh0.b; c.shadowOffsetY = sh0.y;                         // shadow is in canvas px, not affected by the prop scale
    const edge = () => { c.shadowColor = 'transparent'; c.globalAlpha = 1; c.strokeStyle = 'rgba(255,248,234,.55)'; c.lineWidth = .02; c.stroke(); };
    const gr = () => { c.shadowColor = 'transparent'; if (grain) grain(c, .12); };
    if (sh.k === 'rect') { c.beginPath(); c.roundRect(sh.x, sh.y, sh.w, sh.h, (sh.r || 0) * .6); c.fill(); gr(); edge(); }
    else if (sh.k === 'circ') { c.beginPath(); c.arc(sh.x, sh.y, sh.r, 0, Math.PI * 2); c.fill(); gr(); edge(); }
    else if (sh.k === 'poly') { c.beginPath(); sh.p.forEach(([x, y], i) => i ? c.lineTo(x, y) : c.moveTo(x, y)); c.closePath(); c.fill(); if (sh.round) { c.lineWidth = sh.round; c.stroke(); } gr(); edge(); }
    else if (sh.k === 'line') { c.lineWidth = sh.w * 1.05; c.beginPath(); sh.p.forEach(([x, y], i) => i ? c.lineTo(x, y) : c.moveTo(x, y)); c.stroke(); }
    else if (sh.k === 'arc') { c.lineWidth = sh.w; c.beginPath(); c.arc(sh.x, sh.y, sh.r, sh.a0, sh.a1); c.stroke(); }
    else if (sh.k === 'text') { c.font = `900 ${sh.sz}px Fraunces`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(sh.s, sh.x, sh.y); }
    c.restore();
  });
  c.restore();
}
