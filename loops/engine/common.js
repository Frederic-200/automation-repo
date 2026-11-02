// FredsDesk Loops - shared helpers: seeded RNG, palettes, materials, studio environment, camera rig.
// Everything here is deterministic: same cfg => same pixels. No Math.random anywhere.

export function hashSeed(...parts) {
  let h = 2166136261 >>> 0;
  for (const ch of parts.join('|')) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619) >>> 0; }
  return h >>> 0;
}
export function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
export const TAU = Math.PI * 2;
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const frac = x => x - Math.floor(x);
export const smooth = x => { x = clamp(x); return x * x * (3 - 2 * x); };
export const smoother = x => { x = clamp(x); return x * x * x * (x * (x * 6 - 15) + 10); };
export const lerp = (a, b, t) => a + (b - a) * t;
export const pick = (rng, arr) => arr[Math.floor(rng() * arr.length) % arr.length];
export const range = (rng, a, b) => a + (b - a) * rng();

// ---- palettes (P1 ships 8; P2 grows this to ~25 + seasonal sets) -------------------------------
// bg: [top, bottom] of the backdrop gradient. ramp: colour stops used across the objects. ground: floor tint.
// palettes live in palettes.json (single source of truth); pick.py passes the chosen one in cfg.palette

export function rampColor(THREE, palette, u) {
  const stops = palette.ramp.map(c => new THREE.Color(c));
  const x = clamp(u) * (stops.length - 1), i = Math.min(stops.length - 2, Math.floor(x));
  return stops[i].clone().lerp(stops[i + 1], x - i);
}

// ---- materials -----------------------------------------------------------------------------------
export const MATERIAL_KINDS = ['matte', 'glossy', 'metal', 'toon', 'glass'];
export function makeMaterial(THREE, kind, envMap, opts = {}) {
  const base = { color: 0xffffff, ...opts };
  switch (kind) {
    case 'glossy': return new THREE.MeshPhysicalMaterial({ ...base, roughness: 0.18, metalness: 0.0, clearcoat: 1, clearcoatRoughness: 0.08, envMap, envMapIntensity: 1.0 });
    case 'metal':  return new THREE.MeshStandardMaterial({ ...base, roughness: 0.28, metalness: 0.9, envMap, envMapIntensity: 1.25 });
    case 'toon':   return new THREE.MeshToonMaterial({ ...base });
    case 'glass':  return new THREE.MeshPhysicalMaterial({ ...base, roughness: 0.06, metalness: 0, transmission: 0.9, thickness: 0.9, ior: 1.45, clearcoat: 1, clearcoatRoughness: 0.04, envMap, envMapIntensity: 1.4, attenuationDistance: 3, attenuationColor: new THREE.Color(opts.color ?? 0xffffff) });
    default:       return new THREE.MeshStandardMaterial({ ...base, roughness: 0.62, metalness: 0.0, envMap, envMapIntensity: 0.6 });
  }
}

// ---- backdrop gradient (screen-filling texture) ---------------------------------------------------
export function gradientTexture(THREE, top, bottom) {
  const c = document.createElement('canvas'); c.width = 8; c.height = 512;
  const g = c.getContext('2d'), grad = g.createLinearGradient(0, 0, 0, 512);
  grad.addColorStop(0, top); grad.addColorStop(0.55, bottom); grad.addColorStop(1, top);
  g.fillStyle = grad; g.fillRect(0, 0, 8, 512);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; return tex;
}

// ---- studio environment for reflections (own tiny scene -> PMREM) --------------------------------
export function makeStudioEnv(THREE, renderer, palette) {
  const s = new THREE.Scene();
  const dome = new THREE.Mesh(new THREE.SphereGeometry(50, 32, 16), new THREE.MeshBasicMaterial({ side: THREE.BackSide, map: gradientTexture(THREE, palette.bg[0], palette.bg[1]) }));
  s.add(dome);
  const box = (w, h, x, y, z, col, k) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color: new THREE.Color(col).multiplyScalar(k), side: THREE.DoubleSide }));
    m.position.set(x, y, z); m.lookAt(0, 0, 0); s.add(m);
  };
  box(30, 18, -25, 22, 20, palette.key, 6); box(14, 30, 30, 8, -10, palette.key, 4); box(40, 6, 0, 35, -25, '#ffffff', 3);
  const pm = new THREE.PMREMGenerator(renderer);
  const env = pm.fromScene(s, 0.03).texture; pm.dispose(); return env;
}

// ---- camera rig: all motion is periodic in t (0..1) so the loop is seamless -----------------------
// view: {center:[x,y,z], dist, elev(deg), azim(deg)}   cam: {move, amp, ...} chosen by the picker
export const CAMERA_MOVES = ['orbit', 'pushin', 'sway', 'rise'];
export function placeCamera(THREE, camera, view, cam, t) {
  const s = Math.sin(TAU * t), c = Math.cos(TAU * t);
  let az = view.azim, el = view.elev, d = view.dist;
  switch (cam.move) {
    case 'orbit':  az += cam.amp * 24 * s; el += 2.5 * c; break;
    case 'pushin': d *= 1 - 0.13 * cam.amp * (0.5 - 0.5 * c); az += 6 * s; break;
    case 'sway':   az += cam.amp * 11 * s; el += cam.amp * 5 * c; break;
    case 'rise':   el += cam.amp * 10 * (0.5 - 0.5 * c); d *= 1 + 0.04 * s; az += 7 * s; break;
  }
  const A = az * Math.PI / 180, E = el * Math.PI / 180;
  const [cx, cy, cz] = view.center;
  camera.position.set(cx + d * Math.cos(E) * Math.sin(A), cy + d * Math.sin(E), cz + d * Math.cos(E) * Math.cos(A));
  camera.lookAt(cx, cy, cz);
}

// ---- helpers shared by scenes ---------------------------------------------------------------------
export function addShadowFloor(THREE, scene, palette, size = 160) {
  const f = new THREE.Mesh(new THREE.PlaneGeometry(size, size), new THREE.ShadowMaterial({ color: new THREE.Color(palette.ground).multiplyScalar(0.35), opacity: 0.55 }));
  f.rotation.x = -Math.PI / 2; f.receiveShadow = true; scene.add(f); return f;
}
export function instanced(THREE, scene, geo, mat, n, shadow = true) {
  const m = new THREE.InstancedMesh(geo, mat, n); m.castShadow = shadow; m.receiveShadow = shadow; m.frustumCulled = false; scene.add(m); return m;
}
export function ringHull(THREE, radius, ys, n = 40, cx = 0, cz = 0) {
  const pts = []; for (let k = 0; k < n; k++) for (const y of ys) pts.push(new THREE.Vector3(cx + Math.cos(k / n * TAU) * radius, y, cz + Math.sin(k / n * TAU) * radius)); return pts;
}
export function boxHull(THREE, hx, hz, ys) {
  const pts = []; for (const sx of [-1, 1]) for (const sz of [-1, 1]) for (const y of ys) pts.push(new THREE.Vector3(sx * hx, y, sz * hz)); return pts;
}
