// Scene: wave field. A carpet of bars rises and falls with two crossing waves (integer time frequencies => perfect loop).
import { TAU, range, pick, rampColor, addShadowFloor, instanced, boxHull } from '../engine/common.js';
export const name = 'wave';

export function params(rng) {
  return { cols: pick(rng, [18, 20, 22]), rows: pick(rng, [26, 30, 34]), m1: pick(rng, [1, 2]), m2: pick(rng, [1, 2, 3]), k1: range(rng, 0.5, 1.1), k2: range(rng, 0.5, 1.1), dir2: pick(rng, ['x', 'z', 'r']), power: range(rng, 1.0, 1.8), amp: range(rng, 3.6, 5.2) };
}

export function build(ctx) {
  const { THREE, scene, palette, makeMat, P } = ctx; const C = P.cols, R = P.rows, N = C * R, pitch = 0.62, w = 0.5;
  const geo = new THREE.BoxGeometry(w, 1, w); geo.translate(0, 0.5, 0);
  const mesh = instanced(THREE, scene, geo, makeMat(), N); addShadowFloor(THREE, scene, palette);
  const cells = []; for (let r = 0; r < R; r++) for (let c = 0; c < C; c++) cells.push({ x: (c - (C - 1) / 2) * pitch, z: (r - (R - 1) / 2) * pitch });
  const col = new THREE.Color(), m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), pos = new THREE.Vector3(), sc = new THREE.Vector3();
  const halfW = C * pitch / 2;
  function update(t) {
    for (let i = 0; i < N; i++) {
      const c = cells[i], d2 = P.dir2 === 'x' ? c.x : P.dir2 === 'z' ? c.z : Math.hypot(c.x, c.z);
      const a = Math.sin(TAU * (P.m1 * t - P.k1 * c.z * 0.25)), b = Math.sin(TAU * (P.m2 * t - P.k2 * d2 * 0.25));
      const v = Math.pow(Math.max(0, (a + b) / 4 + 0.5), P.power), h = 0.12 + P.amp * v;
      pos.set(c.x, 0, c.z); sc.set(1, h, 1); m4.compose(pos, q.identity(), sc); mesh.setMatrixAt(i, m4); mesh.setColorAt(i, col.copy(rampColor(THREE, palette, Math.min(1, v * 1.05))));
    }
    mesh.instanceMatrix.needsUpdate = true; mesh.instanceColor.needsUpdate = true;
  }
  const events = [], BINS = 12;
  for (let b = 0; b < BINS; b++) for (let k = 0; k < P.m1; k++) events.push({ t: (b / BINS + k) / P.m1, kind: 'thud', pitch: b / BINS, vel: 0.6 });
  return { hull: boxHull(THREE, halfW + 0.2, R * pitch / 2 + 0.2, [0, P.amp + 0.6]), update, events, view: { center: [0, 1.2, 0], dist: 40, elev: 46, azim: 0 }, shadowRadius: 12 };
}
