// v2 PROPS: generic objects drawn once as shapes in a unit box (-1..1, y down); every world renders the same spec in its own style.
// Shape kinds: rect{x,y,w,h,r} circ{x,y,r} poly{p} line{p,w} arc{x,y,r,a0,a1,w} text{s,x,y,sz}.   c = colour role: main ink acc paper soft glass.
// mv: {param:[dx,dy]} moves the shape by (dx,dy) * anim[param]   (e.g. the toggle knob).   Generic metaphors only: no people, products or logos.
const R = (x, y, w, h, r, c, o = {}) => ({ k: 'rect', x, y, w, h, r, c, ...o });
const C = (x, y, r, c, o = {}) => ({ k: 'circ', x, y, r, c, ...o });
const P = (p, c, o = {}) => ({ k: 'poly', p, c, ...o });
const L = (p, w, c, o = {}) => ({ k: 'line', p, w, c, ...o });
const A = (x, y, r, a0, a1, w, c, o = {}) => ({ k: 'arc', x, y, r, a0, a1, w, c, ...o });
const T = (s, x, y, sz, c, o = {}) => ({ k: 'text', s, x, y, sz, c, ...o });
const gearPts = (n, r0, r1) => { const p = []; for (let i = 0; i < n; i++) { const a = i / n * Math.PI * 2, d = Math.PI / n * .5; [[a - d * 1.3, r0], [a - d * .7, r1], [a + d * .7, r1], [a + d * 1.3, r0]].forEach(([t, r]) => p.push([Math.cos(t) * r, Math.sin(t) * r])); } return p; };

export const PROPS = {
  book: [P([[-1.05, -.55], [0, -.4], [1.05, -.55], [1.05, .75], [0, .6], [-1.05, .75]], 'acc'), P([[-.92, -.46], [-.04, -.33], [-.04, .5], [-.92, .63]], 'paper'), P([[.92, -.46], [.04, -.33], [.04, .5], [.92, .63]], 'paper'),
    L([[-.74, -.22], [-.2, -.14]], .06, 'ink'), L([[-.74, .0], [-.2, .08]], .06, 'ink'), L([[-.74, .22], [-.4, .27]], .06, 'ink'), L([[.74, -.22], [.2, -.14]], .06, 'ink'), L([[.74, .0], [.2, .08]], .06, 'ink'), L([[.74, .22], [.4, .27]], .06, 'ink')],
  mic: [A(0, -.05, .58, 0, Math.PI, .1, 'acc'), R(-.32, -.95, .64, 1.1, .32, 'main'), L([[-.2, -.65], [.2, -.65]], .05, 'paper'), L([[-.2, -.45], [.2, -.45]], .05, 'paper'), L([[-.2, -.25], [.2, -.25]], .05, 'paper'), L([[0, .52], [0, .85]], .1, 'acc'), L([[-.42, .88], [.42, .88]], .1, 'acc')],
  document: [R(-.62, -.95, 1.24, 1.9, .06, 'paper'), P([[.18, -.95], [.62, -.5], [.18, -.5]], 'soft'), L([[-.4, -.3], [.4, -.3]], .07, 'ink'), L([[-.4, -.05], [.4, -.05]], .07, 'ink'), L([[-.4, .2], [.22, .2]], .07, 'ink'), C(.28, .62, .22, 'acc'), L([[-.4, .62], [-.02, .62]], .07, 'ink')],
  cursor: [A(-.5, -.8, .55, 0, Math.PI * 2, .06, 'acc'), P([[-.5, -.8], [-.5, .62], [-.15, .32], [.1, .88], [.32, .78], [.06, .22], [.52, .2]], 'main', { outline: 'paper' })],
  coin: [C(0, 0, .92, 'acc'), A(0, 0, .68, 0, Math.PI * 2, .07, 'paper'), T('$', 0, .02, 1.15, 'paper')],
  toggle: [R(-.95, -.48, 1.9, .96, .48, 'main'), C(-.47, 0, .34, 'paper', { mv: { on: [.94, 0] } }), C(.47, 0, .1, 'acc')],
  arrow: [P([[-1, -.26], [.2, -.26], [.2, -.7], [1, 0], [.2, .7], [.2, .26], [-1, .26]], 'acc')],
  bubble: [R(-.95, -.72, 1.9, 1.25, .32, 'main'), P([[-.55, .45], [-.65, .98], [-.05, .5]], 'main'), C(-.42, -.1, .13, 'paper'), C(0, -.1, .13, 'paper'), C(.42, -.1, .13, 'paper')],
  lock: [A(0, -.22, .46, Math.PI, Math.PI * 2, .17, 'main'), L([[-.46, -.22], [-.46, -.05]], .17, 'main'), L([[.46, -.22], [.46, -.05]], .17, 'main'), R(-.72, -.22, 1.44, 1.15, .16, 'acc'), C(0, .2, .15, 'main'), R(-.05, .2, .1, .38, .03, 'main')],
  magnifier: [C(-.2, -.2, .62, 'glass'), A(-.2, -.2, .62, 0, Math.PI * 2, .14, 'main'), L([[.26, .26], [.82, .82]], .22, 'main'), A(-.2, -.2, .38, Math.PI * 1.1, Math.PI * 1.45, .06, 'paper')],
  warning: [P([[0, -.95], [1, .8], [-1, .8]], 'acc', { round: .1 }), R(-.07, -.35, .14, .62, .05, 'main'), C(0, .52, .09, 'main')],
  dice: [R(-.82, -.82, 1.64, 1.64, .3, 'paper'), C(-.42, -.42, .12, 'main'), C(.42, -.42, .12, 'main'), C(0, 0, .12, 'main'), C(-.42, .42, .12, 'main'), C(.42, .42, .12, 'main')],
  gear: [P(gearPts(8, .72, .95), 'main'), C(0, 0, .26, 'paper')],
  check: [C(0, 0, .92, 'acc'), L([[-.42, .02], [-.1, .34], [.5, -.3]], .2, 'paper', { cap: 'round' })],
};
export const PROP_NAMES = Object.keys(PROPS);
