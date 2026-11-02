// Scene: cube cascade. A grid of cubes flips 90 degrees in rippling waves.
// Loop maths: a cube turned 90 degrees looks identical to an unturned one (uniform cube), so the flip can restart each wave.
import { TAU, clamp, frac, smooth, smoother, lerp, range, pick, rampColor } from '../engine/common.js';

export const name = 'cubes';

export function params(rng) {
  return {
    cols: pick(rng, [7, 8, 9]),
    rows: pick(rng, [12, 13, 14]),
    source: pick(rng, ['center', 'corner', 'sweep', 'diagonal']),
    waves: pick(rng, [1, 2]),
    spread: range(rng, 0.7, 1.0),       // how much of the wave cycle spans the grid
    axis: pick(rng, ['x', 'z', 'y']),
    hop: range(rng, 0.35, 0.8),
    win: range(rng, 0.14, 0.2),         // fraction of the wave cycle a cube spends flipping
    colorMode: pick(rng, ['dist', 'rows']),
  };
}

export function build(ctx) {
  const { THREE, scene, palette, makeMat, P, shadowRadius } = ctx;
  const size = 1, pitch = 1.3, C = P.cols, R = P.rows, N = C * R;
  const geo = new THREE.BoxGeometry(size, size, size, 1, 1, 1);
  const mesh = new THREE.InstancedMesh(geo, makeMat(), N);
  mesh.castShadow = true; mesh.receiveShadow = true; mesh.frustumCulled = false; scene.add(mesh);
  const cells = []; let maxD = 0;
  for (let r = 0; r < R; r++) for (let c = 0; c < C; c++) {
    const x = (c - (C - 1) / 2) * pitch, z = (r - (R - 1) / 2) * pitch;
    let d;
    switch (P.source) {
      case 'corner':   d = Math.hypot(x + (C - 1) / 2 * pitch, z + (R - 1) / 2 * pitch); break;
      case 'sweep':    d = z + (R - 1) / 2 * pitch; break;
      case 'diagonal': d = (x + z) + (C + R) / 2 * pitch; break;
      default:         d = Math.hypot(x, z * 0.9);
    }
    cells.push({ x, z, d }); maxD = Math.max(maxD, d);
  }
  const col = new THREE.Color();
  cells.forEach((c, i) => {
    c.u = c.d / maxD;
    const u = P.colorMode === 'rows' ? (Math.floor(i / C) / (R - 1)) : c.u;
    col.copy(rampColor(THREE, palette, 0.3 + 0.7 * u)); mesh.setColorAt(i, col);
  });
  mesh.instanceColor.needsUpdate = true;

  const floor = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), new THREE.ShadowMaterial({ color: new THREE.Color(palette.ground).multiplyScalar(0.35), opacity: 0.55 }));
  floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);

  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), pos = new THREE.Vector3(), sc = new THREE.Vector3();
  const ax = { x: new THREE.Vector3(1, 0, 0), y: new THREE.Vector3(0, 1, 0), z: new THREE.Vector3(0, 0, 1) }[P.axis];
  function update(t) {
    for (let i = 0; i < N; i++) {
      const c = cells[i];
      const p = frac(P.waves * t - c.u * P.spread), k = clamp(p / P.win);
      const e = smoother(k), ang = (Math.PI / 2) * e, bump = Math.sin(Math.PI * k);
      q.setFromAxisAngle(ax, ang);
      const s = 1 + 0.08 * bump;
      pos.set(c.x, size / 2 + P.hop * bump * bump * (P.axis === 'y' ? 0.5 : 1), c.z);
      sc.set(s, s, s); m4.compose(pos, q, sc); mesh.setMatrixAt(i, m4);
    }
    mesh.instanceMatrix.needsUpdate = true;
  }

  // sound events: group cubes into rings of equal distance so a wave = a rising run of taps
  const events = [], BINS = 14;
  for (let b = 0; b < BINS; b++) for (let k = 0; k < P.waves; k++) {
    const u = (b + 0.5) / BINS;
    events.push({ t: frac((u * P.spread + P.win + k) / P.waves), kind: 'thud', pitch: u, vel: 0.7 });
  }
  const hull = []; for (const sx of [-1, 1]) for (const sz of [-1, 1]) for (const y of [0, 1.9]) hull.push(new THREE.Vector3(sx * (C * pitch / 2 + 0.2), y, sz * (R * pitch / 2 + 0.2)));
  return { hull, update, events, view: { center: [0, 0.4, 0], dist: C * pitch * 3.55 + 2, elev: P.source === 'sweep' ? 50 : 58, azim: 0 }, shadowRadius: Math.max(C, R) * pitch * 0.8 };
}
