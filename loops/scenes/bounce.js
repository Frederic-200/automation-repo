// Scene: bounce grid. A grid of balls hops in a travelling wave; each lands and squashes exactly once per wave.
import { TAU, clamp, frac, range, pick, rampColor, addShadowFloor, instanced, boxHull } from '../engine/common.js';
export const name = 'bounce';

export function params(rng) {
  return { cols: pick(rng, [7, 8, 9]), rows: pick(rng, [11, 12, 13]), source: pick(rng, ['center', 'corner', 'sweep', 'diagonal']), waves: pick(rng, [1, 2]),
    spread: range(rng, 0.7, 1.0), hop: range(rng, 1.4, 2.4), radius: range(rng, 0.46, 0.56), colorMode: pick(rng, ['dist', 'rows']) };
}

export function build(ctx) {
  const { THREE, scene, palette, makeMat, P } = ctx; const C = P.cols, R = P.rows, N = C * R, pitch = 1.3;
  const mesh = instanced(THREE, scene, new THREE.SphereGeometry(1, 28, 18), makeMat(), N);
  const cells = []; let maxD = 0;
  for (let r = 0; r < R; r++) for (let c = 0; c < C; c++) {
    const x = (c - (C - 1) / 2) * pitch, z = (r - (R - 1) / 2) * pitch; let d;
    switch (P.source) { case 'corner': d = Math.hypot(x + (C - 1) / 2 * pitch, z + (R - 1) / 2 * pitch); break; case 'sweep': d = z + (R - 1) / 2 * pitch; break;
      case 'diagonal': d = x + z + (C + R) / 2 * pitch; break; default: d = Math.hypot(x, z * 0.9); }
    cells.push({ x, z, d }); maxD = Math.max(maxD, d);
  }
  const col = new THREE.Color();
  cells.forEach((c, i) => { c.u = c.d / maxD; mesh.setColorAt(i, col.copy(rampColor(THREE, palette, 0.25 + 0.75 * (P.colorMode === 'rows' ? Math.floor(i / C) / (R - 1) : c.u)))); });
  mesh.instanceColor.needsUpdate = true; addShadowFloor(THREE, scene, palette);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), pos = new THREE.Vector3(), sc = new THREE.Vector3();
  function update(t) {
    for (let i = 0; i < N; i++) {
      const c = cells[i], p = frac(P.waves * t - c.u * P.spread), air = 4 * p * (1 - p);
      const dl = Math.min(p, 1 - p), sq = Math.max(0, 1 - dl / 0.07) * 0.28;          // squash while touching the floor (symmetric across the wrap)
      sc.set(P.radius * (1 + sq * 0.6), P.radius * (1 - sq), P.radius * (1 + sq * 0.6));
      pos.set(c.x, P.radius * (1 - sq) + P.hop * air, c.z); m4.compose(pos, q.identity(), sc); mesh.setMatrixAt(i, m4);
    }
    mesh.instanceMatrix.needsUpdate = true;
  }
  const events = [], BINS = 14;
  for (let b = 0; b < BINS; b++) for (let k = 0; k < P.waves; k++) { const u = (b + 0.5) / BINS; events.push({ t: frac((u * P.spread + k) / P.waves), kind: 'ping', pitch: u, vel: 0.7 }); }
  return { hull: boxHull(THREE, C * pitch / 2 + 0.2, R * pitch / 2 + 0.2, [0, P.hop + 1.4]), update, events, view: { center: [0, 0.8, 0], dist: C * pitch * 3.5 + 2, elev: 52, azim: 0 }, shadowRadius: Math.max(C, R) * pitch * 0.8 };
}
