// Scene: gear train. A chain of meshing gears; every gear turns a whole number of tooth-steps per loop, with tooth/gap phases solved so they truly mesh.
import { TAU, range, pick, mulberry32, rampColor, addShadowFloor, ringHull } from '../engine/common.js';
export const name = 'gears';

export function params(rng) {
  return { teeth: Array.from({ length: 7 }, () => pick(rng, [10, 12, 14, 16, 18, 20, 24, 28])), steps: pick(rng, [24, 30, 36]), turn: range(rng, 25, 60), module: range(rng, 0.34, 0.4) };
}

function gearShape(THREE, N, rp, m) {
  const ro = rp + 0.5 * m, ri = rp - 0.7 * m, pitch = TAU / N, sh = new THREE.Shape(), pts = [];
  for (let k = 0; k < N; k++) { const a = k * pitch;
    pts.push([ri, a - pitch * 0.30], [ri * 1.02, a - pitch * 0.2], [ro, a - pitch * 0.12], [ro, a + pitch * 0.12], [ri * 1.02, a + pitch * 0.2], [ri, a + pitch * 0.30]); }
  pts.forEach(([r, a], i) => { const x = r * Math.cos(a), y = r * Math.sin(a); i ? sh.lineTo(x, y) : sh.moveTo(x, y); }); sh.closePath();
  const hole = new THREE.Path(); hole.absarc(0, 0, Math.max(0.3, rp * 0.28), 0, TAU, true); sh.holes.push(hole); return sh;
}

export function build(ctx) {
  const { THREE, scene, palette, makeMat, P } = ctx; const G = P.teeth.length, m = P.module, rng = mulberry32(5150 + G);
  const rp = P.teeth.map(n => n * m / 2), depth = 0.7;
  // lay the chain out in the XY plane (later mapped onto the floor), retrying turns until no two gears collide
  let C = null;
  for (let attempt = 0; attempt < 400 && !C; attempt++) {
    const c = [{ x: 0, y: 0, phi: 0 }]; let phi = rng() * TAU, ok = true;
    for (let i = 1; i < G && ok; i++) {
      phi += (rng() < 0.5 ? -1 : 1) * (P.turn + rng() * 40) * Math.PI / 180 * (attempt < 200 ? 1 : 0.5);
      const d = rp[i - 1] + rp[i], x = c[i - 1].x + d * Math.cos(phi), y = c[i - 1].y + d * Math.sin(phi);
      for (let j = 0; j < i - 1; j++) if (Math.hypot(x - c[j].x, y - c[j].y) < rp[i] + rp[j] + 1.4 * m) ok = false;
      c.push({ x, y, phi });
    }
    if (ok) C = c;
  }
  if (!C) { C = [{ x: 0, y: 0, phi: 0 }]; for (let i = 1; i < G; i++) { const phi = (i % 2 ? 1 : -1) * 0.5, d = rp[i - 1] + rp[i]; C.push({ x: C[i - 1].x + d * Math.cos(phi), y: C[i - 1].y + d * Math.sin(phi), phi }); } }
  // centre the chain
  const mx = C.reduce((a, g) => a + g.x, 0) / G, my = C.reduce((a, g) => a + g.y, 0) / G; C.forEach(g => { g.x -= mx; g.y -= my; });
  // turn the chain so its long axis runs up the (portrait) screen: screen-vertical = local y
  let sxx = 0, syy = 0, sxy = 0; C.forEach(g => { sxx += g.x * g.x; syy += g.y * g.y; sxy += g.x * g.y; });
  const rot = Math.PI / 2 - 0.5 * Math.atan2(2 * sxy, sxx - syy), cr = Math.cos(rot), sr = Math.sin(rot); C.forEach(g => { const x = g.x * cr - g.y * sr, y = g.x * sr + g.y * cr; g.x = x; g.y = y; });
  // tooth / gap phases: gear 0 starts at 0, each next gear solved against its predecessor
  const th0 = [0], dir = [1];
  for (let i = 1; i < G; i++) {
    const dx = C[i].x - C[i - 1].x, dy = C[i].y - C[i - 1].y, phi = Math.atan2(dy, dx);
    th0.push(phi + Math.PI - (Math.PI - P.teeth[i - 1] * (phi - th0[i - 1])) / P.teeth[i]); dir.push(-dir[i - 1]);
  }
  const spinners = [];
  for (let i = 0; i < G; i++) {
    const geo = new THREE.ExtrudeGeometry(gearShape(THREE, P.teeth[i], rp[i], m), { depth, bevelEnabled: true, bevelThickness: 0.05, bevelSize: 0.05, bevelSegments: 2, curveSegments: 6 });
    const mat = makeMat(); mat.color.copy(rampColor(THREE, palette, 0.15 + 0.85 * i / (G - 1)));
    const mesh = new THREE.Mesh(geo, mat); mesh.castShadow = true; mesh.receiveShadow = true;
    const piv = new THREE.Group(); piv.rotation.x = -Math.PI / 2; piv.position.set(C[i].x, 0.05, -C[i].y); piv.add(mesh); scene.add(piv); spinners.push(mesh);
  }
  addShadowFloor(THREE, scene, palette);
  const update = t => { for (let i = 0; i < G; i++) spinners[i].rotation.z = th0[i] + dir[i] * TAU * P.steps / P.teeth[i] * t; };
  const events = []; for (let k = 0; k < P.steps; k++) events.push({ t: k / P.steps, kind: 'tick', pitch: (k % 7) / 6, vel: 0.5 });
  const hull = []; for (let i = 0; i < G; i++) hull.push(...ringHull(THREE, rp[i] + 0.6, [0, depth + 0.2], 24, C[i].x, -C[i].y));
  const ext = Math.max(...C.map(g => Math.hypot(g.x, g.y) + 6));
  return { hull, update, events, view: { center: [0, 0.3, 0], dist: ext * 3.1 + 12, elev: 62, azim: 0 }, shadowRadius: ext };
}
