// Scene: domino spiral. A wave of tiles falls outward and stands back up, forever.
// Loop maths: tile i has wave phase p = frac(m*t - u_i*cover); tilt = profile(p). Everything is periodic in t.
import { TAU, clamp, frac, smooth, lerp, range, pick, rampColor } from '../engine/common.js';

export const name = 'domino';

export function params(rng) {
  return {
    radius: range(rng, 6.6, 8.2),      // spiral outer radius (world units)
    gap: range(rng, 1.05, 1.3),        // distance between spiral turns
    waves: pick(rng, [1, 1, 2]),       // waves per loop
    cover: range(rng, 0.7, 0.95),      // how much of a wave cycle spans the whole spiral
    maxTilt: range(rng, 48, 68),       // degrees
    reverse: rng() < 0.4,              // wave travels inward instead of outward
    colorMode: pick(rng, ['along', 'rings']),
  };
}

export function build(ctx) {
  const { THREE, scene, palette, makeMat, P, shadowRadius } = ctx;
  const h = 1.0, w = 0.62, th = 0.14, s = 0.55;           // tile height / width / thickness / spacing along the spiral
  const b = P.gap / TAU, a0 = 0.9;                         // r = a0 + b*theta
  // place tiles at constant arc spacing
  const pts = []; let theta = 0;
  while (true) {
    const r = a0 + b * theta; if (r > P.radius) break;
    pts.push({ x: r * Math.cos(theta), z: r * Math.sin(theta), theta, r });
    theta += s / Math.sqrt(r * r + b * b);
  }
  const N = pts.length;
  for (let i = 0; i < N; i++) {
    const a = pts[i], n = pts[Math.min(N - 1, i + 1)], p = pts[Math.max(0, i - 1)];
    let tx = (i < N - 1 ? n.x - a.x : a.x - p.x), tz = (i < N - 1 ? n.z - a.z : a.z - p.z);
    const L = Math.hypot(tx, tz) || 1; a.tx = tx / L; a.tz = tz / L;
    a.u = P.reverse ? 1 - i / (N - 1) : i / (N - 1);
  }

  const geo = new THREE.BoxGeometry(th, h, w); geo.translate(-th / 2, h / 2, 0);   // pivot at the front-bottom edge
  const mat = makeMat(); const mesh = new THREE.InstancedMesh(geo, mat, N);
  mesh.castShadow = true; mesh.receiveShadow = true; mesh.frustumCulled = false; scene.add(mesh);
  const col = new THREE.Color();
  for (let i = 0; i < N; i++) {
    const u = P.colorMode === 'rings' ? frac(pts[i].theta / TAU * 0.5) * 0.999 : i / (N - 1);
    col.copy(rampColor(THREE, palette, P.colorMode === 'rings' ? Math.abs(1 - 2 * u) : u)); mesh.setColorAt(i, col);
  }
  mesh.instanceColor.needsUpdate = true;

  // floor
  const floor = new THREE.Mesh(new THREE.CircleGeometry(60, 64), new THREE.ShadowMaterial({ color: new THREE.Color(palette.ground).multiplyScalar(0.35), opacity: 0.55 }));
  floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);

  const fw = 0.075, hold = 0.09, rw = 0.075, maxT = P.maxTilt * Math.PI / 180;
  const profile = p => {            // 0 upright -> maxT fallen -> 0 upright
    if (p < fw) { const k = p / fw; return maxT * k * k * (1.6 - 0.6 * k); }       // accelerates like gravity
    if (p < fw + hold) return maxT;
    if (p < fw + hold + rw) return maxT * (1 - smooth((p - fw - hold) / rw));
    return 0;
  };

  const m4 = new THREE.Matrix4(), basis = new THREE.Matrix4(), q = new THREE.Quaternion(), qt = new THREE.Quaternion();
  const pos = new THREE.Vector3(), one = new THREE.Vector3(1, 1, 1), up = new THREE.Vector3(0, 1, 0), zAxis = new THREE.Vector3(0, 0, 1);
  const T = new THREE.Vector3(), W = new THREE.Vector3();
  function update(t) {
    for (let i = 0; i < N; i++) {
      const a = pts[i];
      const tilt = profile(frac(P.waves * t - a.u * P.cover));
      T.set(a.tx, 0, a.tz); W.crossVectors(T, up);
      basis.makeBasis(T, up, W); q.setFromRotationMatrix(basis);
      qt.setFromAxisAngle(zAxis, -tilt); q.multiply(qt);
      pos.set(a.x + a.tx * th / 2, 0, a.z + a.tz * th / 2);
      m4.compose(pos, q, one); mesh.setMatrixAt(i, m4);
    }
    mesh.instanceMatrix.needsUpdate = true;
  }

  // sound events: the moment each tile lands (thinned in audio.py)
  const events = [];
  for (let i = 0; i < N; i++) for (let k = 0; k < P.waves; k++) {
    const tt = frac((pts[i].u * P.cover + fw * 0.85 + k) / P.waves);
    events.push({ t: tt, kind: 'tick', pitch: pts[i].u, vel: 0.5 });
  }
  const hull = []; for (let k = 0; k < 40; k++) for (const y of [0, 1.1]) hull.push(new THREE.Vector3(Math.cos(k / 40 * TAU) * (P.radius + 0.7), y, Math.sin(k / 40 * TAU) * (P.radius + 0.7)));
  return { hull, update, events, view: { center: [0, 0.2, 0], dist: P.radius * 5.0, elev: 56, azim: 0 }, shadowRadius };
}
