// Scene: pendulum wave. Pendulum i swings (k0+i) whole cycles per loop, so they drift apart and snap back into line exactly at the loop point.
import { TAU, range, pick, rampColor, addShadowFloor, instanced, boxHull } from '../engine/common.js';
export const name = 'pendulum';

export function params(rng) {
  return { n: pick(rng, [14, 16, 18, 20]), k0: pick(rng, [4, 5, 6]), amp: range(rng, 30, 42), spacing: range(rng, 0.9, 1.05), lenRatio: range(rng, 0.4, 0.7), bobR: range(rng, 0.36, 0.46) };
}

export function build(ctx) {
  const { THREE, scene, palette, makeMat, P } = ctx; const { n, k0 } = P;
  const Lmax = 8, topY = Lmax + 1.4, ampR = P.amp * Math.PI / 180;
  const bobs = instanced(THREE, scene, new THREE.SphereGeometry(1, 32, 20), makeMat(), n);
  const rods = instanced(THREE, scene, new THREE.CylinderGeometry(1, 1, 1, 8), (() => { const m = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.4, metalness: 0.6 }); return m; })(), n);
  const bar = new THREE.Mesh(new THREE.BoxGeometry(n * P.spacing + 1.6, 0.35, 0.5), makeMat()); bar.material.color.set(palette.ramp[2]); bar.position.set(0, topY + 0.15, 0); bar.castShadow = true; scene.add(bar);
  addShadowFloor(THREE, scene, palette);
  const col = new THREE.Color(), L = [], X = [];
  for (let i = 0; i < n; i++) {
    L.push(Lmax * (1 - (1 - P.lenRatio) * i / (n - 1))); X.push((i - (n - 1) / 2) * P.spacing);
    bobs.setColorAt(i, col.copy(rampColor(THREE, palette, i / (n - 1)))); rods.setColorAt(i, col.set(0xdddddd));
  }
  bobs.instanceColor.needsUpdate = true; rods.instanceColor.needsUpdate = true;
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), pos = new THREE.Vector3(), sc = new THREE.Vector3(), xAxis = new THREE.Vector3(1, 0, 0);
  function update(t) {
    for (let i = 0; i < n; i++) {
      const a = ampR * Math.sin(TAU * (k0 + i) * t);
      const by = topY - L[i] * Math.cos(a), bz = L[i] * Math.sin(a);
      pos.set(X[i], by, bz); sc.setScalar(P.bobR); m4.compose(pos, q.identity(), sc); bobs.setMatrixAt(i, m4);
      pos.set(X[i], (topY + by) / 2, bz / 2); q.setFromAxisAngle(xAxis, -a); sc.set(0.03, L[i], 0.03); m4.compose(pos, q, sc); rods.setMatrixAt(i, m4);
    }
    bobs.instanceMatrix.needsUpdate = true; rods.instanceMatrix.needsUpdate = true;
  }
  const events = [];
  for (let i = 0; i < n; i++) { const f = k0 + i; for (let c = 0; c < f; c++) events.push({ t: c / f, kind: 'ping', pitch: i / (n - 1), vel: 0.55 }); }
  const zr = Lmax * Math.sin(ampR) + 0.6;
  return { hull: boxHull(THREE, n * P.spacing / 2 + 0.6, zr, [0, topY + 0.8]), update, events, view: { center: [0, topY * 0.5, 0], dist: 46, elev: 24, azim: 26 }, shadowRadius: 16 };
}
