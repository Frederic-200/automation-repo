// World A style for props: flat Swiss shapes. Roles: main = ink, acc = accent, paper = paper with an ink outline, soft = grey, glass = translucent accent.
export function drawProp(c, spec, cx, cy, size, pal, anim = {}) {
  const s = size / 2, col = r => ({ main: pal.ink, ink: pal.ink, acc: pal.acc, paper: pal.paper, soft: 'rgba(18,18,18,.18)', glass: pal.acc }[r] || pal.ink);
  c.save(); c.translate(cx, cy); c.scale(s, s); c.lineJoin = 'round'; c.lineCap = 'butt'; const OL = .055;
  spec.forEach(sh => {
    c.save(); if (sh.mv) for (const k in sh.mv) c.translate(sh.mv[k][0] * (anim[k] || 0), sh.mv[k][1] * (anim[k] || 0));
    c.fillStyle = col(sh.c); c.strokeStyle = col(sh.c); if (sh.c === 'glass') c.globalAlpha = .22;
    const outline = sh.c === 'paper' || sh.outline; const strokeOL = () => { if (outline) { c.globalAlpha = 1; c.strokeStyle = sh.outline ? col(sh.outline) : pal.ink; c.lineWidth = OL; c.stroke(); } };
    if (sh.k === 'rect') { c.beginPath(); c.roundRect(sh.x, sh.y, sh.w, sh.h, sh.r || 0); c.fill(); strokeOL(); }
    else if (sh.k === 'circ') { c.beginPath(); c.arc(sh.x, sh.y, sh.r, 0, Math.PI * 2); c.fill(); strokeOL(); }
    else if (sh.k === 'poly') { c.beginPath(); sh.p.forEach(([x, y], i) => i ? c.lineTo(x, y) : c.moveTo(x, y)); c.closePath(); c.fill(); if (sh.round) { c.lineWidth = sh.round; c.stroke(); } strokeOL(); }
    else if (sh.k === 'line') { c.lineWidth = sh.w; c.lineCap = sh.cap || 'butt'; c.beginPath(); sh.p.forEach(([x, y], i) => i ? c.lineTo(x, y) : c.moveTo(x, y)); c.stroke(); }
    else if (sh.k === 'arc') { c.lineWidth = sh.w; c.beginPath(); c.arc(sh.x, sh.y, sh.r, sh.a0, sh.a1); c.stroke(); }
    else if (sh.k === 'text') { c.font = `800 ${sh.sz}px Bricolage`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(sh.s, sh.x, sh.y); }
    c.restore();
  });
  c.restore();
}
