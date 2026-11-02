// Scene: bead ribbons. Parallel strands of beads flow along 3D Lissajous curves; time frequencies are whole numbers so the flow loops.
import { TAU, range, pick, rampColor, addShadowFloor, instanced, boxHull } from '../engine/common.js';
export const name = 'ribbons';

export function params(rng) {
  return { strands: pick(rng, [10, 12, 14]), beads: pick(rng, [100, 120]), fx: pick(rng, [1, 2]), fy: pick(rng, [1, 2, 3]), fz: pick(rng, [1, 2]), kx: pick(rng, [-2, -1, 1, 2]), ky: pick(rng, [-1, 1, 2]), kz: pick(rng, [-2, -1, 1]),
    A: range(rng, 4.6, 5.6), B: range(rng, 4.8, 6.4), ph: range(rng, 0.045, 0.085), r0: range(rng, 0.17, 0.23) };
}

export function build(ctx) {
  const { THREE, scene, palette, makeMat, P } = ctx; const K = P.strands, M = P.beads, N = K * M, yoff = P.B + 1.8;
  const mesh = instanced(THREE, scene, new THREE.SphereGeometry(1, 14, 10), makeMat(), N); addShadowFloor(THREE, scene, palette);
  const col = new THREE.Color(); for (let k = 0; k < K; k++) for (let b = 0; b < M; b++) mesh.setColorAt(k * M + b, col.copy(rampColor(THREE, palette, (k / (K - 1)) * 0.7 + (b / M) * 0.3)));
  mesh.instanceColor.needsUpdate = true;
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), pos = new THREE.Vector3(), sc = new THREE.Vector3();
  function update(t) {
    for (let k = 0; k < K; k++) for (let b = 0; b < M; b++) {
      const s = b / (M - 1), ph = k * P.ph;
      const x = P.A * Math.cos(TAU * (P.fx * s * 0.5 + P.kx * t + ph)), y = P.B * Math.sin(TAU * (P.fy * s * 0.5 + P.ky * t + ph * 1.3)), z = P.A * Math.sin(TAU * (P.fz * s * 0.5 + P.kz * t + ph * 0.8));
      pos.set(x, y + yoff, z); sc.setScalar(P.r0 * (0.35 + 0.65 * Math.sin(Math.PI * s))); m4.compose(pos, q.identity(), sc); mesh.setMatrixAt(k * M + b, m4);
    }
    mesh.instanceMatrix.needsUpdate = true;
  }
  const events = []; for (let k = 0; k < K; k++) events.push({ t: k / K, kind: 'ping', pitch: k / (K - 1), vel: 0.5 }, { t: (k / K + 0.5) % 1, kind: 'ping', pitch: 1 - k / (K - 1), vel: 0.4 });
  return { hull: boxHull(THREE, P.A + 0.4, P.A + 0.4, [yoff - P.B - 0.4, yoff + P.B + 0.4]), update, events, view: { center: [0, yoff, 0], dist: 46, elev: 14, azim: 0 }, shadowRadius: 14 };
}
