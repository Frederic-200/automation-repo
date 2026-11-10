// FredsDesk v2 engine: draws any frame of a video from timeline.json. One world per video (a world = a module of scene kinds).
// Deterministic: a frame depends only on its index. The world decides what scenes look like; the engine decides WHEN (narration timing),
// handles scene switching, the transition between scenes, and word-timed captions.
import { clamp } from '/proto/worlds/util.js';

export const TRANSITION = 0.38;      // seconds the incoming scene takes to wipe in

// group the spoken words of a scene into short caption chunks (<= 4 words, break after punctuation)
export function chunks(scene) {
  const out = []; let cur = [];
  const flush = () => { if (cur.length) { out.push({ s: cur[0].s, e: cur[cur.length - 1].e, words: cur }); cur = []; } };
  for (const ln of scene.lines || []) for (const w of ln.words) { cur.push(w); if (cur.length >= 4 || /[.,!?;:]$/.test(w.w)) flush(); }
  flush(); return out;
}

export async function createEngine(tl, canvas) {
  const W = tl.W, H = tl.H; canvas.width = W; canvas.height = H;
  const world = (await import(`/worlds/${tl.v2.world}/index.js`)).default;
  const pal = world.palettes[tl.v2.palette] || Object.values(world.palettes)[0];
  const c = canvas.getContext('2d'), S = W / 1080, scenes = tl.scenes, n = scenes.length;
  scenes.forEach(sc => { sc.chunks = chunks(sc); sc.dur = sc.end - sc.start; });
  for (const sc of scenes) if (!world.kinds[sc.type]) throw new Error(`world ${tl.v2.world} has no scene kind "${sc.type}"`);
  const env = { pal, tl, W: 1080, H: 1920 };
  if (world.init) await world.init(env);                                   // worlds with their own renderer (e.g. WebGL) set up here
  const draw = (i, lt) => { c.save(); world.kinds[scenes[i].type].draw(c, lt, scenes[i], env); c.restore(); };

  return {
    info: { world: tl.v2.world, palette: tl.v2.palette, scenes: n },
    frame(f) {
      const t = f / tl.fps; let i = n - 1; for (let k = 0; k < n; k++) if (t < scenes[k].end) { i = k; break; }
      const sc = scenes[i], lt = t - sc.start;
      c.setTransform(S, 0, 0, S, 0, 0); world.background(c, t, env, sc);
      if (i > 0 && lt < TRANSITION) {
        const prev = scenes[i - 1]; draw(i - 1, prev.dur + lt);                 // outgoing scene keeps animating underneath
        c.save(); world.wipe(c, lt / TRANSITION, env, () => draw(i, lt), () => world.background(c, t, env, sc)); c.restore();
      } else draw(i, lt);
      if (world.kinds[sc.type].caps !== false && !(sc.i === 0 && sc.type === 'headline' && t < 2.6) && !(sc.params && sc.params.nocaps)) {   // the hook headline is the one focus for the first 2.6 s
        const ch = sc.chunks.find(k => t >= k.s - .05 && t < k.e + .22) || null; if (ch) { c.save(); world.captions(c, t, ch, env, sc); c.restore(); }
      }
    }
  };
}
