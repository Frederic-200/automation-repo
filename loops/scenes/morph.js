// Scene: particle morph. ~2000 beads flow sphere -> cube -> torus -> ... and back to the first shape at the loop point.
import { TAU, clamp, smoother, range, pick, mulberry32, rampColor, addShadowFloor, instanced, ringHull } from '../engine/common.js';
export const name = 'morph';

export function params(rng) {
  return { n: pick(rng, [1800, 2200, 2600]), size: range(rng, 0.085, 0.12), shapes: [0, 1, 2, 3, 4].sort(() => rng() - 0.5).slice(0, 4), swirl: range(rng, 1.0, 2.2), spinTurns: pick(rng, [1, 1, 2]) };
}

export function build(ctx) {
  const { THREE, scene, palette, makeMat, P } = ctx; const N = P.n, R = 4.6, cy = R + 2.2, rng = mulberry32(777 + N);
  const gens = [
    i => { const k = (i + 0.5) / N, ph = Math.acos(1 - 2 * k), th = Math.PI * (1 + Math.sqrt(5)) * i; return [R * Math.sin(ph) * Math.cos(th), R * Math.cos(ph), R * Math.sin(ph) * Math.sin(th)]; },                 // sphere
    () => { const f = Math.floor(rng() * 6), u = rng() * 2 - 1, v = rng() * 2 - 1, s = R * 0.82, p = [u * s, v * s, s * (f % 2 ? 1 : -1)]; return f < 2 ? p : f < 4 ? [p[2], p[0], p[1]] : [p[1], p[2], p[0]]; }, // cube surface
    i => { const u = rng() * TAU, v = rng() * TAU, a = R * 0.72, b = R * 0.3; return [(a + b * Math.cos(v)) * Math.cos(u), b * Math.sin(v) * 1.1, (a + b * Math.cos(v)) * Math.sin(u)]; },                              // torus
    () => { const u = Math.sqrt(rng()), arm = Math.floor(rng() * 3) * TAU / 3, th = u * 3.2 * Math.PI + arm + (rng() - 0.5) * 0.35; return [u * R * 1.15 * Math.cos(th), (rng() - 0.5) * 0.7 * (1.2 - u), u * R * 1.15 * Math.sin(th)]; }, // galaxy disc
    i => { const k = i / N, th = k * 6 * TAU, s = i % 2 ? 1 : -1; return [R * 0.62 * Math.cos(th + (s > 0 ? 0 : Math.PI)), (k - 0.5) * R * 2.1, R * 0.62 * Math.sin(th + (s > 0 ? 0 : Math.PI))]; },        // double helix
  ];
  const shapes = P.shapes.map(g => { const pts = Array.from({ length: N }, (_, i) => gens[g](i)); pts.sort((a, b) => (Math.round(a[1] / 0.35) - Math.round(b[1] / 0.35)) || (Math.atan2(a[2], a[0]) - Math.atan2(b[2], b[0]))); return pts; });
  const S = shapes.length, mesh = instanced(THREE, scene, new THREE.SphereGeometry(1, 10, 8), makeMat(), N); addShadowFloor(THREE, scene, palette);
  const col = new THREE.Color(); for (let i = 0; i < N; i++) mesh.setColorAt(i, col.copy(rampColor(THREE, palette, ((i / N) * 3) % 1)));
  mesh.instanceColor.needsUpdate = true;
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), pos = new THREE.Vector3(), sc = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0);
  function update(t) {
    const seg = Math.min(S - 1, Math.floor(t * S)), loc = t * S - seg, A = shapes[seg], B = shapes[(seg + 1) % S];
    const spin = TAU * P.spinTurns * t, cs = Math.cos(spin), sn = Math.sin(spin);
    for (let i = 0; i < N; i++) {
      const lag = (i / N) * 0.25, e = smoother((loc - 0.22 - lag * 0.6) / 0.5), bump = Math.sin(Math.PI * e);
      let x = A[i][0] + (B[i][0] - A[i][0]) * e, y = A[i][1] + (B[i][1] - A[i][1]) * e, z = A[i][2] + (B[i][2] - A[i][2]) * e;
      const sw = P.swirl * bump * (0.6 + 0.4 * (i / N)), c2 = Math.cos(sw), s2 = Math.sin(sw); const x2 = x * c2 - z * s2, z2 = x * s2 + z * c2; const puff = 1 + 0.22 * bump;
      x = x2 * puff; z = z2 * puff; y = y * puff;
      pos.set(x * cs - z * sn, y + cy, x * sn + z * cs); sc.setScalar(P.size * (1 + 0.5 * bump)); m4.compose(pos, q.identity(), sc); mesh.setMatrixAt(i, m4);
    }
    mesh.instanceMatrix.needsUpdate = true;
  }
  const events = []; for (let s = 0; s < S; s++) events.push({ t: (s + 0.78) / S, kind: 'chime', pitch: s / S, vel: 0.8 }, { t: (s + 0.25) / S, kind: 'chime', pitch: 0.5 + s / (2 * S), vel: 0.4 });
  return { hull: ringHull(THREE, R * 1.5, [cy - R * 1.3, cy, cy + R * 1.3], 32), update, events, view: { center: [0, cy, 0], dist: 40, elev: 16, azim: 0 }, shadowRadius: 14 };
}
