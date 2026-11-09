// WORLD C - "Token blocks" (3D, Three.js): word blocks with real depth and shadows, a gently moving camera, gold flashes on the key moments.
// Same scene kinds and params as worlds A and B (headline, bars, stat, finale). Each scene is rendered by WebGL and drawn onto the 2D frame;
// captions and the wipe are 2D on top.
import * as THREE from 'three';
import { clamp, lerp, seg, eInOut, eOutExpo, eOutCubic, rng, vnoise } from '/proto/worlds/util.js';

const palettes = {
  indigo: { wall: 0x3a2f86, bgTop: '#1b1440', bgBot: '#07051a', hemiS: 0xa8acff, hemiG: 0x2a2060, key: 0xffe2b0, rim: 0x6c8cff, acc: 0xffc857, accEm: 0x6b4a00, accCss: '#ffc857', block: 0xf4efe6, blockInk: '#1a1230', alt: 0x6c5ce7, altInk: '#ffffff', altEm: 0x1a1260, dust: 0xb9b0ff, deep: 0x120c33 },
  teal: { wall: 0x14586a, bgTop: '#0b2b3a', bgBot: '#03121a', hemiS: 0xb0f0ff, hemiG: 0x103848, key: 0xfff0d0, rim: 0x5fe0d0, acc: 0xff7a59, accEm: 0x6a2410, accCss: '#ff7a59', block: 0xf2f7f4, blockInk: '#0b2230', alt: 0x1f9d8f, altInk: '#ffffff', altEm: 0x0b4a44, dust: 0xa0f0e0, deep: 0x06222c },
};
const W3 = 7.0;                       // max row width in world units (the frame is ~7.6 units wide at the base camera distance)
let R, GL, root, cam, wall, flash, dust, key, pal, STY, BG, built = [];
const settle = d => d <= 0 ? 0 : 1 - Math.exp(-6 * d) * Math.cos(15 * d);
const meas = document.createElement('canvas').getContext('2d');
const wordW1 = txt => { meas.font = '800 100px Bricolage'; return meas.measureText(txt).width / 100 * .56 + .85; };   // block width for a word at block height 1

function rrect(w, h, r) { const s = new THREE.Shape(), x = -w / 2, y = -h / 2; s.moveTo(x + r, y); s.lineTo(x + w - r, y); s.absarc(x + w - r, y + r, r, -Math.PI / 2, 0, false); s.lineTo(x + w, y + h - r); s.absarc(x + w - r, y + h - r, r, 0, Math.PI / 2, false); s.lineTo(x + r, y + h); s.absarc(x + r, y + h - r, r, Math.PI / 2, Math.PI, false); s.lineTo(x, y + r); s.absarc(x + r, y + r, r, Math.PI, Math.PI * 1.5, false); return s; }
function label(txt, w, h, col, align = 'center') {
  const px = 128, c = document.createElement('canvas'); c.width = Math.round(w * px); c.height = Math.round(h * px); const g = c.getContext('2d');
  g.font = `800 ${h * px * .56}px Bricolage`; g.textAlign = align; g.textBaseline = 'middle'; g.fillStyle = col; g.fillText(txt, align === 'center' ? c.width / 2 : 0, c.height / 2 + h * px * .04);
  const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; tx.anisotropy = 4; return tx;
}
function makeBlock(txt, h, st) {
  const w = wordW1(txt) * h, g = new THREE.Group(), r = Math.min(.22, h * .21);
  const geo = new THREE.ExtrudeGeometry(rrect(w, h, r), { depth: .4 * Math.min(1, h + .3), bevelEnabled: true, bevelThickness: .07, bevelSize: .07, bevelSegments: 3, curveSegments: 10 }); geo.center();
  const body = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: st.color, roughness: st.rough ?? .45, metalness: .05, emissive: st.emissive ?? 0, transparent: true })); body.castShadow = true; body.receiveShadow = true; g.add(body);
  const tag = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: label(txt, w, h, st.ink), transparent: true, toneMapped: false })); tag.position.z = .28 * Math.min(1, h + .3) + .02; g.add(tag);
  g.userData = { w, h, body, tag }; return g;
}
const setOp = (g, o) => { g.userData.body.material.opacity = o; g.userData.tag.material.opacity = o; g.visible = o > .01; };
function dropIn(b, lt, t0, sgn = 1) { const k = settle(lt - t0), h = b.userData.home; b.position.set(h.x, h.y + (1 - k) * 7, h.z); b.rotation.z = (1 - k) * .25 * sgn; setOp(b, clamp((lt - t0) / .12)); }
// a centred row of word blocks, scaled down to fit W3; blocks get .userData.home
function row(group, text, h, st, y) {
  const ws = text.split(/\s+/).filter(Boolean), n = ws.length, tot1 = ws.reduce((a, w) => a + wordW1(w), 0) + .3 * (n - 1), hh = Math.min(h, W3 / tot1), gap = .3 * hh;
  const bl = ws.map(w => makeBlock(w, hh, st)), tot = bl.reduce((a, b) => a + b.userData.w, 0) + gap * (n - 1); let px = -tot / 2;
  bl.forEach(b => { b.userData.home = new THREE.Vector3(px + b.userData.w / 2, y, 0); px += b.userData.w + gap; group.add(b); }); return { blocks: bl, h: hh, w: tot };
}
const box = (w, h, d, mat) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); m.castShadow = true; m.receiveShadow = true; return m; };

// ------------------------------------------------------------------ scene kinds: build(params) -> {group, update(lt)}
const BUILD = {
  headline(P) {
    const g = new THREE.Group(), L = P.lines || [], rows = [], hs = L.map(l => Math.min(1.8, Math.max(.8, (l.size || 150) / 150 * 1.05))), tot = hs.reduce((a, h) => a + h * 1.32, 0); let top = 1.6 + tot / 2;
    L.forEach((ln, i) => {
      const st = ln.color === 'acc' ? STY.gold : [STY.cream, STY.alt, STY.cream][i % 3], y = top - hs[i] * .66, r = row(g, ln.text, hs[i], st, y); rows.push(r); top -= hs[i] * 1.32;
      if (P.underline === i) { const bar = box(1, .17, .3, new THREE.MeshStandardMaterial({ color: pal.acc, emissive: pal.accEm, roughness: .4 })); bar.position.set(0, y - r.h * .62, .1); g.add(bar); r.bar = bar; }
    });
    return { group: g, update(lt) {
      rows.forEach((r, i) => { r.blocks.forEach((b, j) => dropIn(b, lt, -.2 + i * .14 + j * .08, (i + j) % 2 ? 1 : -1)); if (r.bar) { const pb = eOutExpo(seg(lt, .5 + i * .14, 1.0 + i * .14)); r.bar.scale.x = Math.max(.001, (r.w + .2) * pb); r.bar.visible = pb > .01; } });
    } };
  },
  bars(P) {
    const g = new THREE.Group(), rows = P.rows || [], LEFT = -3.4, FULL = 6.8, title = P.title ? row(g, P.title, .85, STY.gold, 5.0) : null, items = [];
    rows.forEach((r, i) => {
      const y = 2.55 - i * 2.4, lab = makeBlock(r.label, .5, STY.alt), track = box(FULL, .85, .2, new THREE.MeshStandardMaterial({ color: pal.deep, roughness: .9 }));
      lab.userData.home = new THREE.Vector3(LEFT + lab.userData.w / 2, y + .95, 0); g.add(lab); track.position.set(LEFT + FULL / 2, y, -.2); g.add(track);
      const mat = new THREE.MeshStandardMaterial({ color: r.color === 'acc' ? pal.acc : pal.block, emissive: r.color === 'acc' ? pal.accEm : 0, roughness: .4, transparent: true }), bar = box(1, .85, .45, mat); g.add(bar); items.push({ lab, track, bar, y, r, i, mat });
    });
    let gap = null; if (P.gap) { const gm = new THREE.MeshBasicMaterial({ color: pal.acc, transparent: true, opacity: .42, toneMapped: false }), gb = box(1, .85, .45, gm); gb.castShadow = false; g.add(gb); const gl = makeBlock(P.gap.label || 'THE GAP', .6, STY.gold); gl.userData.home = new THREE.Vector3(0, 2.55 - P.gap.to * 2.4 - 1.25, .1); g.add(gl); gap = { gb, gl }; }
    let note = null; if (P.note) { const nt = new THREE.Mesh(new THREE.PlaneGeometry(6.8, .4), new THREE.MeshBasicMaterial({ map: label(P.note, 6.8, .4, 'rgba(255,255,255,.55)', 'left'), transparent: true, toneMapped: false })); nt.position.set(0, -3.7, .1); g.add(nt); note = nt; }
    const noise = vnoise(11), ends = [];
    return { group: g, update(lt) {
      if (title) title.blocks.forEach((b, j) => dropIn(b, lt, -.1 + j * .08));
      items.forEach(({ lab, track, bar, y, r, i, mat }) => {
        const a0 = .2 + i * .35; dropIn(lab, lt, a0); track.visible = lt > a0; track.scale.y = eOutExpo(seg(lt, a0, a0 + .3)) || .001;
        const t0 = .35 + i * .35, grow = r.wobble ? eOutCubic(seg(lt, t0, t0 + 1.1)) : eOutExpo(seg(lt, t0, t0 + .5));
        const wob = r.wobble && lt > t0 + 1.1 ? ((noise(lt * 5) - .5) * 1.2 + Math.sin(lt * 9) * .18) * grow : 0, len = Math.max(.001, FULL * r.value * grow + wob);
        bar.scale.x = len; bar.position.set(LEFT + len / 2, y, .05); bar.visible = len > .02; ends[i] = len;
      });
      if (gap) { const e0 = ends[P.gap.from] || 0, e1 = ends[P.gap.to] || 0, tg = .35 + P.gap.to * .35 + 1.3, pg = eOutExpo(seg(lt, tg, tg + .5)), x0 = LEFT + Math.min(e0, e1), x1 = LEFT + Math.max(e0, e1), len = Math.max(.001, (x1 - x0) * pg);
        gap.gb.scale.x = len; gap.gb.position.set(x0 + len / 2, 2.55 - P.gap.to * 2.4, .05); gap.gb.visible = pg > .01 && e0 > 0 && e1 > 0; dropIn(gap.gl, lt, tg + .1); gap.gl.userData.home.x = (x0 + x1) / 2; gap.gl.visible = gap.gl.visible && pg > .01; }
      if (note) note.material.opacity = eOutExpo(seg(lt, .8, 1.3));
    } };
  },
  stat(P) {
    const g = new THREE.Group(), big = P.big || '', hb = Math.min(3.2, (P.size || 360) / 360 * 3.0), rb = row(g, big, hb, STY.gold, 1.45), subs = (P.sub || '').split('\n').filter(Boolean).map((s, i) => row(g, s, .95, STY.cream, -.95 - i * 1.25));
    let sm = null; if (P.small) { sm = makeBlock(P.small, .55, STY.alt); sm.userData.home = new THREE.Vector3(-3.4 + sm.userData.w / 2, 3.65 + (rb.h - 3) * .5, 0); g.add(sm); }
    return { group: g, update(lt) {
      if (sm) dropIn(sm, lt, -.1); rb.blocks.forEach(b => dropIn(b, lt, -.05, -1)); subs.forEach((r, i) => r.blocks.forEach((b, j) => dropIn(b, lt, .5 + i * .15 + j * .06)));
    } };
  },
  finale(P) {
    const g = new THREE.Group(), top = P.top ? row(g, P.top, 1.4, STY.cream, 4.2) : null, acc = P.accent ? row(g, P.accent, 2.4, STY.gold, 2.0) : null, bottom = (P.bottom || []).map((w, i) => row(g, w, 1.3, STY.cream, -2.1 - i * 1.7));
    const mk = new THREE.MeshStandardMaterial({ color: pal.block, roughness: .4 }), bars = [0, 1].map(i => { const b = box(1, .22, .3, mk); b.position.set(0, .15 - i * .55, .1); g.add(b); return b; });
    const sl = box(1, .24, .34, new THREE.MeshStandardMaterial({ color: pal.acc, emissive: pal.accEm, roughness: .4 })); sl.position.set(0, -.12, .35); sl.rotation.z = .42; g.add(sl);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(1, .05, 12, 64), new THREE.MeshBasicMaterial({ color: pal.acc, transparent: true, toneMapped: false })); ring.position.set(0, 2.0, .6); g.add(ring);
    return { group: g, dark: true, update(lt) {
      if (top) top.blocks.forEach((b, j) => dropIn(b, lt, .3 + j * .08)); if (acc) acc.blocks.forEach((b, j) => dropIn(b, lt, .45 + j * .08, -1));
      const ps = eOutExpo(seg(lt, .9, 1.4)); bars.forEach(b => { b.scale.x = Math.max(.001, 2.6 * ps); b.visible = ps > .01; });
      const pl = eOutExpo(seg(lt, 1.3, 1.65)); sl.visible = P.mark === 'neq' && pl > 0; sl.scale.x = Math.max(.001, 2.0 * pl); bars.forEach(b => b.visible = b.visible && !!P.mark);
      bottom.forEach((r, i) => r.blocks.forEach((b, j) => dropIn(b, lt, 1.5 + i * .15 + j * .06)));
      const f = seg(lt, .5, .7) * (1 - seg(lt, .7, 1.4)); flash.intensity = f * 140; flash.position.set(0, 3, 5); const rp = seg(lt, .55, 1.7); ring.visible = rp > 0 && rp < 1; ring.scale.setScalar(.8 + rp * 3.4); ring.material.opacity = (1 - rp) * .6;
    } };
  },
};

function renderScene(sc, lt) {
  const t = sc.start + lt; if (!sc.__c) { sc.__c = BUILD[sc.type](sc.params || {}); root.add(sc.__c.group); built.push(sc.__c); }
  built.forEach(b => b.group.visible = false); sc.__c.group.visible = true; flash.intensity = 0;
  const dark = sc.__c.dark ? eInOut(seg(lt, -.05, .45)) : 0; wall.material.color.setHex(pal.wall).lerp(new THREE.Color(pal.deep), dark * .8);
  sc.__c.update(lt);
  dust.rotation.y = t * .03; dust.position.y = (t * .12) % 3 - 1.5;
  const u = clamp(lt / 6), z = 28 - 2.6 * u - (sc.__c.dark ? .6 * eInOut(seg(lt, -.05, .5)) : 0);
  cam.position.set(Math.sin(t * .5) * .35, -.2 + Math.cos(t * .4) * .2, z); cam.lookAt(0, 0, 0); R.render(root, cam);
}

const kinds = Object.fromEntries(['headline', 'bars', 'stat', 'finale'].map(k => [k, { caps: k !== 'finale', draw(c, lt, sc) { renderScene(sc, lt); c.drawImage(GL, 0, 0, 1080, 1920); } }]));

export default {
  name: 'C', title: 'Token blocks (3D)', palettes, kinds,
  async init({ pal: p, tl }) {
    pal = p; const Wp = tl.W, Hp = tl.H; GL = document.createElement('canvas'); GL.width = Wp; GL.height = Hp;
    R = new THREE.WebGLRenderer({ canvas: GL, antialias: true, powerPreference: 'high-performance' }); R.setPixelRatio(1); R.setSize(Wp, Hp, false);
    R.outputColorSpace = THREE.SRGBColorSpace; R.toneMapping = THREE.ACESFilmicToneMapping; R.toneMappingExposure = 1.1; R.shadowMap.enabled = true; R.shadowMap.type = THREE.PCFSoftShadowMap;
    root = new THREE.Scene(); { const c = document.createElement('canvas'); c.width = 8; c.height = 512; const g = c.getContext('2d'), gr = g.createLinearGradient(0, 0, 0, 512); gr.addColorStop(0, pal.bgTop); gr.addColorStop(.6, pal.bgBot); gr.addColorStop(1, pal.bgBot); g.fillStyle = gr; g.fillRect(0, 0, 8, 512); const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; root.background = tx; }
    cam = new THREE.PerspectiveCamera(30, Wp / Hp, .5, 200); root.add(new THREE.HemisphereLight(pal.hemiS, pal.hemiG, 1.2));
    key = new THREE.DirectionalLight(pal.key, 2.6); key.position.set(3.5, 7, 16); key.castShadow = true; key.shadow.mapSize.set(2048, 2048); Object.assign(key.shadow.camera, { left: -12, right: 12, top: 12, bottom: -12, near: 1, far: 60 }); key.shadow.bias = -.0005; key.shadow.normalBias = .03; key.shadow.radius = 5; root.add(key);
    { const rim = new THREE.DirectionalLight(pal.rim, 1.1); rim.position.set(-9, 4, -6); root.add(rim); } flash = new THREE.PointLight(pal.acc, 0, 30, 1.6); root.add(flash);
    wall = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), new THREE.MeshStandardMaterial({ color: pal.wall, roughness: .9 })); wall.position.z = -1.2; wall.receiveShadow = true; root.add(wall);
    const rd = rng(8), N = 160, dp = new Float32Array(N * 3); for (let i = 0; i < N; i++) { dp[i * 3] = (rd() - .5) * 16; dp[i * 3 + 1] = (rd() - .5) * 22; dp[i * 3 + 2] = -1.8 + rd() * 8; }
    dust = new THREE.Points(new THREE.BufferGeometry().setAttribute('position', new THREE.BufferAttribute(dp, 3)), new THREE.PointsMaterial({ color: pal.dust, size: .07, transparent: true, opacity: .5 })); root.add(dust);
    STY = { cream: { color: pal.block, ink: pal.blockInk }, alt: { color: pal.alt, ink: pal.altInk, emissive: pal.altEm, rough: .35 }, gold: { color: pal.acc, ink: pal.blockInk, emissive: pal.accEm } };
  },
  background(c) { c.fillStyle = '#07051a'; c.fillRect(0, 0, 1080, 1920); },
  // a slanted gold edge sweeps across; the new scene is revealed behind it
  wipe(c, p, { pal: pl }, drawNew) {
    const e = eInOut(p), x = lerp(-300, 1080 + 40, e), sk = 260; c.save(); c.beginPath(); c.moveTo(0, 0); c.lineTo(x + sk, 0); c.lineTo(x - sk, 1920); c.lineTo(0, 1920); c.closePath(); c.clip(); drawNew(); c.restore();
    c.save(); c.fillStyle = pl.accCss; c.globalAlpha = .95; c.beginPath(); c.moveTo(x + sk, 0); c.lineTo(x + sk + 30, 0); c.lineTo(x - sk + 30, 1920); c.lineTo(x - sk, 1920); c.closePath(); c.fill(); c.restore();
  },
  // frosted pill at the bottom; the spoken word gets a gold underline, keywords in the accent colour
  captions(c, t, ch, { pal: pl }) {
    const a = eOutExpo(seg(t, ch.s - .05, ch.s + .15)); if (a <= 0) return; c.font = '800 64px Bricolage';
    const sp = c.measureText(' ').width, ws = ch.words.map(w => c.measureText(w.w).width), tot = ws.reduce((x, y) => x + y, 0) + sp * (ws.length - 1), k = Math.min(1, 860 / tot), size = 64 * k; c.font = `800 ${size}px Bricolage`;
    const sp2 = c.measureText(' ').width, ws2 = ch.words.map(w => c.measureText(w.w).width), tw = ws2.reduce((x, y) => x + y, 0) + sp2 * (ws2.length - 1), Wd = tw + 80, Hd = size * 1.8, cy = 1650;
    c.save(); c.globalAlpha = a; c.translate(0, (1 - a) * 20); c.fillStyle = 'rgba(8,6,28,.62)'; c.beginPath(); c.roundRect(540 - Wd / 2, cy - Hd / 2, Wd, Hd, Hd / 2); c.fill(); c.strokeStyle = 'rgba(255,255,255,.18)'; c.lineWidth = 2; c.stroke();
    let x = 540 - tw / 2; ch.words.forEach((w, i) => { if (t >= w.s && t < w.e + .02) { c.fillStyle = pl.accCss; c.fillRect(x, cy + size * .3, ws2[i], size * .09); } c.fillStyle = w.k ? pl.accCss : '#ffffff'; c.textAlign = 'left'; c.fillText(w.w, x, cy + size * .22); x += ws2[i] + sp2; }); c.restore();
  },
};
