// Scene: helix tower. Blocks climb a spiral staircase; one slot per loop, fading in at the bottom and out at the top, so it never visibly restarts.
import { TAU, clamp, smooth, range, pick, rampColor, addShadowFloor, instanced, ringHull } from '../engine/common.js';
export const name = 'helix';

export function params(rng) {
  return { strands: pick(rng, [1, 1, 2]), slots: pick(rng, [26, 30, 34]), radius: range(rng, 3.8, 4.6), dTheta: range(rng, 0.3, 0.42), dy: range(rng, 0.4, 0.5), spin: pick(rng, [1, 1, 2]) };
}

export function build(ctx) {
  const { THREE, scene, palette, makeMat, P } = ctx; const M = P.slots, S = P.strands, N = (M + 1) * S, H = M * P.dy;
  const geo = new THREE.BoxGeometry(1.5, 0.3, 1); const mesh = instanced(THREE, scene, geo, makeMat(), N); addShadowFloor(THREE, scene, palette);
  const col = new THREE.Color(), m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), pos = new THREE.Vector3(), sc = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0);
  function update(t) {
    let n = 0;
    for (let s = 0; s < S; s++) for (let k = 0; k <= M; k++) {
      const u = k + t, f = u / M, ang = u * P.dTheta + s * TAU / S + TAU * P.spin * t, y = 0.3 + u * P.dy;
      const vis = smooth(u / 3) * smooth((M - u) / 4);                                 // grow in at the bottom, shrink away at the top
      pos.set(Math.cos(ang) * P.radius, y, Math.sin(ang) * P.radius); q.setFromAxisAngle(up, -ang); sc.set(Math.max(0.0001, vis), Math.max(0.0001, vis), Math.max(0.0001, vis) * P.radius * P.dTheta * 0.9);
      m4.compose(pos, q, sc); mesh.setMatrixAt(n, m4); mesh.setColorAt(n, col.copy(rampColor(THREE, palette, clamp(f)))); n++;
    }
    mesh.instanceMatrix.needsUpdate = true; mesh.instanceColor.needsUpdate = true;
  }
  const events = []; for (let k = 0; k < M; k += 1) events.push({ t: k / M, kind: 'ping', pitch: k / M, vel: 0.45 });
  return { hull: ringHull(THREE, P.radius + 1.2, [0, H + 0.6], 32), update, events, view: { center: [0, H * 0.5, 0], dist: 46, elev: 18, azim: 0 }, shadowRadius: 14 };
}
