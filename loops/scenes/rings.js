// Scene: gyroscope rings. Nested rings each spin a whole number of turns per loop about alternating axes.
import { TAU, range, pick, rampColor, addShadowFloor, ringHull } from '../engine/common.js';
export const name = 'rings';

export function params(rng) {
  return { count: pick(rng, [6, 7, 8]), gap: range(rng, 0.62, 0.8), tube: range(rng, 0.11, 0.17), speeds: Array.from({ length: 10 }, () => pick(rng, [1, 1, 2, -1, -2, 3, -3])) };
}

export function build(ctx) {
  const { THREE, scene, palette, makeMat, P } = ctx; const R0 = 6.2, cy = R0 + 1.6;
  const root = new THREE.Group(); root.position.set(0, cy, 0); scene.add(root);
  let parent = root; const pivots = [], events = [];
  for (let j = 0; j < P.count; j++) {
    const r = R0 - j * P.gap, pivot = new THREE.Group(); parent.add(pivot);
    const mat = makeMat(); mat.color.copy(rampColor(THREE, palette, j / Math.max(1, P.count - 1)));
    const ring = new THREE.Mesh(new THREE.TorusGeometry(r, P.tube, 20, 120), mat); ring.castShadow = true; ring.receiveShadow = true; pivot.add(ring);
    const bead = new THREE.Mesh(new THREE.SphereGeometry(P.tube * 2.1, 20, 14), makeMat()); bead.material.color.set(palette.ramp[0]); bead.position.set(r, 0, 0); bead.castShadow = true; pivot.add(bead);
    pivots.push({ pivot, axis: j % 2 === 0 ? 'x' : 'y', s: P.speeds[j] }); parent = pivot;
    const s = Math.abs(P.speeds[j]); for (let m = 0; m < 2 * s; m++) events.push({ t: m / (2 * s), kind: 'chime', pitch: j / P.count, vel: 0.55 });
  }
  const core = new THREE.Mesh(new THREE.SphereGeometry(Math.max(0.5, R0 - P.count * P.gap), 32, 20), makeMat()); core.material.color.set(palette.ramp[1]); core.castShadow = true; parent.add(core);
  addShadowFloor(THREE, scene, palette);
  const update = t => { for (const p of pivots) p.pivot.rotation[p.axis] = TAU * p.s * t; };
  return { hull: ringHull(THREE, R0 + 0.8, [cy - R0 - 0.8, cy - R0 / 2, cy, cy + R0 / 2, cy + R0 + 0.8], 40), update, events, view: { center: [0, cy, 0], dist: 42, elev: 14, azim: 0 }, shadowRadius: 16 };
}
