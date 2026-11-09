// WORLD C - "Token blocks" (3D): real depth, shadows and a moving camera. A sentence of word-blocks builds up, then four candidate
// next words appear with near-equal bars; one is chosen and locks in with a flash. Illustrates: a tiny lead still gives a confident answer.
// Motion grammar: damped drops, arcs, camera dolly/orbit. Deep indigo studio, gold accents.
import * as THREE from 'three';
import { clamp, lerp, seg, eInOut, eOutCubic, rng, vnoise } from '/worlds/util.js';

export async function init({ canvas, W, H }) {
  const R = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
  R.setPixelRatio(1); R.setSize(W, H, false); R.outputColorSpace = THREE.SRGBColorSpace; R.toneMapping = THREE.ACESFilmicToneMapping; R.toneMappingExposure = 1.1;
  R.shadowMap.enabled = true; R.shadowMap.type = THREE.PCFSoftShadowMap;
  const scene = new THREE.Scene();
  // backdrop gradient
  { const c = document.createElement('canvas'); c.width = 8; c.height = 512; const g = c.getContext('2d'), gr = g.createLinearGradient(0, 0, 0, 512); gr.addColorStop(0, '#1b1440'); gr.addColorStop(.6, '#0d0a22'); gr.addColorStop(1, '#07051a'); g.fillStyle = gr; g.fillRect(0, 0, 8, 512);
    const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; scene.background = tx; }
  const cam = new THREE.PerspectiveCamera(30, W / H, .5, 200);
  scene.add(new THREE.HemisphereLight(0xa8acff, 0x2a2060, 1.2));
  const key = new THREE.DirectionalLight(0xffe2b0, 2.6); key.position.set(3.5, 7, 16); key.castShadow = true; key.shadow.mapSize.set(2048, 2048);
  Object.assign(key.shadow.camera, { left: -12, right: 12, top: 12, bottom: -12, near: 1, far: 60 }); key.shadow.bias = -.0005; key.shadow.normalBias = .03; key.shadow.radius = 5; scene.add(key);
  const rim = new THREE.DirectionalLight(0x6c8cff, 1.1); rim.position.set(-9, 4, -6); scene.add(rim);
  const flash = new THREE.PointLight(0xffc857, 0, 30, 1.6); scene.add(flash);
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), new THREE.MeshStandardMaterial({ color: 0x3a2f86, roughness: .9 })); wall.position.z = -1.2; wall.receiveShadow = true; scene.add(wall);

  // ---- helpers ----
  const measure = document.createElement('canvas').getContext('2d'); measure.font = '800 100px Bricolage';
  const wordW = (txt, h = 1.05) => measure.measureText(txt).width / 100 * h * .56 + h * .85;       // block width in world units for a word at block height h
  function rrect(w, h, r) { const s = new THREE.Shape(), x = -w / 2, y = -h / 2; s.moveTo(x + r, y); s.lineTo(x + w - r, y); s.absarc(x + w - r, y + r, r, -Math.PI / 2, 0, false); s.lineTo(x + w, y + h - r); s.absarc(x + w - r, y + h - r, r, 0, Math.PI / 2, false); s.lineTo(x + r, y + h); s.absarc(x + r, y + h - r, r, Math.PI / 2, Math.PI, false); s.lineTo(x, y + r); s.absarc(x + r, y + r, r, Math.PI, Math.PI * 1.5, false); return s; }
  function label(txt, w, h, col) {
    const px = 128, c = document.createElement('canvas'); c.width = Math.round(w * px); c.height = Math.round(h * px); const g = c.getContext('2d');
    g.font = `800 ${h * px * .56}px Bricolage`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = col; g.fillText(txt, c.width / 2, c.height / 2 + h * px * .04);
    const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; tx.anisotropy = 4; return tx;
  }
  function makeBlock(txt, { h = 1.05, color = 0xf4efe6, ink = '#1a1230', ink2 = null, emissive = 0x000000, rough = .45 } = {}) {
    const w = wordW(txt, h), g = new THREE.Group();
    const geo = new THREE.ExtrudeGeometry(rrect(w, h, .22), { depth: .4, bevelEnabled: true, bevelThickness: .07, bevelSize: .07, bevelSegments: 3, curveSegments: 10 }); geo.center();
    const body = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color, roughness: rough, metalness: .05, emissive, transparent: true })); body.castShadow = true; body.receiveShadow = true; g.add(body);
    const tag = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: label(txt, w, h, ink), transparent: true, toneMapped: false })); tag.position.z = .28; g.add(tag);
    let tag2 = null; if (ink2) { tag2 = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: label(txt, w, h, ink2), transparent: true, opacity: 0, toneMapped: false })); tag2.position.z = .285; g.add(tag2); }
    g.userData = { w, h, body, tag, tag2 }; return g;
  }
  const setOpacity = (g, o) => { g.userData.body.material.opacity = o; g.userData.tag.material.opacity = o; g.visible = o > .01; };
  const settle = d => d <= 0 ? 0 : 1 - Math.exp(-6 * d) * Math.cos(15 * d);        // damped spring 0 -> 1

  // ---- the sentence ----
  const S = [['The', 0, 2.35, .25], ['capital', 0, 2.35, .6], ['of', 0, 1.0, .95], ['Atlantis', 0, 1.0, 1.3], ['is', 0, -.35, 1.65]];
  const rows = { 2.35: ['The', 'capital'], 1.0: ['of', 'Atlantis'], '-0.35': ['is'] }, GAP = .32, SLOTW = wordW('Poseidonis', 1.05) * 1.02;
  const sent = {}; Object.entries(rows).forEach(([y, ws]) => {
    const blocks = ws.map(wd => makeBlock(wd)), isLast = y === '-0.35', tot = blocks.reduce((a, b) => a + b.userData.w, 0) + GAP * (ws.length - 1 + (isLast ? 1 : 0)) + (isLast ? SLOTW : 0);
    let px = -tot / 2; blocks.forEach((b, i) => { b.userData.home = new THREE.Vector3(px + b.userData.w / 2, +y, 0); px += b.userData.w + GAP; sent[ws[i]] = b; scene.add(b); });
    if (isLast) sent.slotCenter = new THREE.Vector3(px + SLOTW / 2, +y, 0);
  });
  const SLOT = sent.slotCenter;
  const DROPS = { The: .05, capital: .3, of: .55, Atlantis: .8, is: 1.1 };

  // slot frame (pulsing gold outline made of 4 thin bars)
  const frameMat = new THREE.MeshBasicMaterial({ color: 0xffc857, transparent: true, toneMapped: false }), slotFrame = new THREE.Group();
  [[0, 1, SLOTW, .09], [0, -1, SLOTW, .09], [-1, 0, .09, 1.2], [1, 0, .09, 1.2]].forEach(([ax, ay, w, h]) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, .1), frameMat); m.position.set(ax * SLOTW / 2, ay * .55, 0); slotFrame.add(m); });
  slotFrame.position.copy(SLOT); scene.add(slotFrame);

  // ---- candidates + bars ----
  const CAND = [['Poseidonis', .31], ['Atlas', .29], ['Aquaria', .27], ['Thera', .24]], LEFT = -3.05, CY = [-2.55, -3.75, -4.95, -6.15], cands = [], barMat = [];
  CAND.forEach(([wd, p], i) => {
    const b = makeBlock(wd, { h: .82, color: 0x6c5ce7, ink: '#ffffff', ink2: '#1a1230', emissive: 0x1a1260, rough: .35 }); b.userData.start = new THREE.Vector3(LEFT + b.userData.w / 2, CY[i], 0); b.userData.p = p; scene.add(b); cands.push(b);
    const bm = new THREE.MeshStandardMaterial({ color: i === 0 ? 0xffc857 : 0xd9a441, emissive: i === 0 ? 0x6b4a00 : 0x3a2a00, roughness: .4, transparent: true }), bar = new THREE.Mesh(new THREE.BoxGeometry(1, .5, .45), bm); bar.castShadow = true; bar.receiveShadow = true; scene.add(bar); b.userData.bar = bar; barMat.push(bm);
  });
  const noise = vnoise(99);

  // lock-in ring + final text + dust
  const ring = new THREE.Mesh(new THREE.TorusGeometry(1, .04, 12, 64), new THREE.MeshBasicMaterial({ color: 0xffc857, transparent: true, toneMapped: false })); ring.position.copy(SLOT); ring.position.z = .4; scene.add(ring);
  const ft = document.createElement('canvas'); ft.width = 1024; ft.height = 512; { const g = ft.getContext('2d'); g.textAlign = 'center'; g.font = '800 150px Bricolage'; g.fillStyle = '#ffffff'; g.fillText('TINY LEAD.', 512, 190); g.fillStyle = '#ffc857'; g.fillText('FULL CONFIDENCE.', 512, 360); g.font = '800 96px Bricolage'; }
  { const g = ft.getContext('2d'); g.clearRect(0, 0, 1024, 512); g.textAlign = 'center'; g.font = '800 140px Bricolage'; g.fillStyle = '#ffffff'; g.fillText('TINY LEAD.', 512, 190); g.font = '800 104px Bricolage'; g.fillStyle = '#ffc857'; g.fillText('FULL CONFIDENCE.', 512, 340); }
  const ftx = new THREE.CanvasTexture(ft); ftx.colorSpace = THREE.SRGBColorSpace; const fin = new THREE.Mesh(new THREE.PlaneGeometry(7.4, 3.7), new THREE.MeshBasicMaterial({ map: ftx, transparent: true, toneMapped: false })); fin.position.set(0, -4.4, 1.2); scene.add(fin);
  const rd = rng(8), N = 160, dp = new Float32Array(N * 3); for (let i = 0; i < N; i++) { dp[i * 3] = (rd() - .5) * 16; dp[i * 3 + 1] = (rd() - .5) * 22; dp[i * 3 + 2] = -1.8 + rd() * 8; }
  const dust = new THREE.Points(new THREE.BufferGeometry().setAttribute('position', new THREE.BufferAttribute(dp, 3)), new THREE.PointsMaterial({ color: 0xb9b0ff, size: .07, transparent: true, opacity: .5 })); scene.add(dust);

  const KEYS = [  // time, camera position, look-at
    [0, [.9, -1.6, 31], [0, -1.6, 0]], [2.4, [0, -1.2, 26], [0, -1.2, 0]], [3.7, [-.7, -3.6, 22.5], [.1, -3.7, 0]], [5.1, [.6, -2.4, 23.5], [.3, -1.8, 0]], [7.0, [0, -1.0, 26.5], [0, -1.7, 0]], [10, [-.5, -1.3, 28], [0, -1.7, 0]]];
  const sm = x => x * x * (3 - 2 * x);
  function camAt(t) { let i = 0; while (i < KEYS.length - 2 && t > KEYS[i + 1][0]) i++; const [t0, p0, l0] = KEYS[i], [t1, p1, l1] = KEYS[i + 1], u = sm(clamp((t - t0) / (t1 - t0))); return [p0.map((v, k) => lerp(v, p1[k], u)), l0.map((v, k) => lerp(v, l1[k], u))]; }

  return {
    frame(t) {
      // sentence drops
      Object.entries(DROPS).forEach(([wd, t0]) => { const b = sent[wd], k = settle(t - t0), h = b.userData.home; b.position.set(h.x, h.y + (1 - k) * 7, h.z); b.rotation.z = (1 - k) * .25 * (wd.length % 2 ? 1 : -1); setOpacity(b, clamp((t - t0) / .12)); });
      // slot outline pulses until the answer lands
      const lock = seg(t, 5.2, 5.9); slotFrame.visible = t > 1.6 && lock < 1; frameMat.opacity = (.55 + .45 * Math.sin(t * 7)) * (1 - lock); slotFrame.scale.setScalar(1 + .015 * Math.sin(t * 7));
      // candidates
      cands.forEach((b, i) => {
        const t0 = 2.45 + i * .26, k = settle(t - t0), s = b.userData.start, bar = b.userData.bar, isPick = i === 0, d = seg(t, 5.2, 5.9), fadeOut = seg(t, 5.3, 5.8);
        let px = s.x, py = s.y - (1 - k) * 4, pz = 0, sc = 1;
        if (isPick) { const u = eInOut(d); px = lerp(s.x, SLOT.x - SLOT.x * 0 + (SLOT.x - b.userData.w * 0), u) ; px = lerp(s.x, SLOT.x, u); py = lerp(s.y - (1 - k) * 4, SLOT.y, u) + Math.sin(u * Math.PI) * 1.6; pz = Math.sin(u * Math.PI) * 2.2; sc = lerp(1, 1.05 / .82, u); }
        b.position.set(px, py, pz); b.scale.setScalar(sc); b.rotation.y = isPick ? Math.sin(d * Math.PI) * .35 : 0;
        const op = isPick ? clamp((t - t0) / .12) : clamp((t - t0) / .12) * (1 - fadeOut); setOpacity(b, op);
        if (isPick) { const m = b.userData.body.material; m.color.set(0x6c5ce7).lerp(new THREE.Color(0xf4efe6), eInOut(seg(t, 5.55, 5.95))); m.emissive.set(0x1a1260).lerp(new THREE.Color(0x6b4a00), seg(t, 5.55, 6.1)); const cf = eInOut(seg(t, 5.55, 5.95)); b.userData.tag.material.opacity = op * (1 - cf); b.userData.tag2.material.opacity = op * cf; }
        // bars: grow, shimmer around near-equal values, then drop away
        const grow = eOutCubic(seg(t, t0 + .1, t0 + .8)), shim = seg(t, 3.3, 5.0) * (1 - seg(t, 5.0, 5.2));
        const len = 8 * (b.userData.p + (noise(t * 2.2 + i * 7) - .5) * .09 * shim + Math.sin(t * 6 + i * 2) * .008 * shim) * grow * (1 - seg(t, 5.25, 5.7));
        const L = Math.max(.001, len); bar.scale.x = L; bar.position.set(LEFT + b.userData.w + .35 + L / 2, s.y - (1 - k) * 4, 0); bar.visible = L > .01; barMat[i].opacity = clamp((t - t0) / .12);
      });
      // flash, ring, final text, dust
      const f = seg(t, 5.55, 5.75) * (1 - seg(t, 5.75, 6.5)); flash.position.set(SLOT.x, SLOT.y + 1, 5); flash.intensity = f * 140;
      const rp = seg(t, 5.6, 6.8); ring.visible = rp > 0 && rp < 1; ring.scale.setScalar(.8 + rp * 4.2); ring.material.opacity = (1 - rp) * .9;
      const fp = eOutCubic(seg(t, 6.4, 7.1)); fin.material.opacity = fp; fin.position.y = -4.4 - (1 - fp) * .6; fin.visible = fp > 0;
      dust.rotation.y = t * .03; dust.position.y = (t * .12) % 3 - 1.5;
      // camera
      const [p, l] = camAt(t); cam.position.set(p[0] + Math.sin(t * .6) * .35, p[1] + Math.cos(t * .5) * .2, p[2]); cam.lookAt(l[0], l[1], l[2]);
      R.render(scene, cam);
    }
  };
}
