"""Ink library for Tiny Comet Prints coloring pages (Phase 1, free tools only).

Shapes are signed-distance fields (SDF) combined with smooth union / difference, traced with
marching squares, then drawn as a white fill plus a slightly varying black ink outline.
Painter's order gives occlusion: whatever is drawn later covers what is behind it.
"""
import math
import numpy as np
import cairo
from skimage import measure
from scipy.ndimage import gaussian_filter1d

W, H = 1700, 2200
LW = 12          # main outline weight (px at 200 dpi page units)
LD = 7           # detail line weight
LIGHT = np.array([0.45, 0.89])


# ---------------------------------------------------------------- SDF primitives
def E(cx, cy, rx, ry=None, a=0, n=2.0):
    """Ellipse / squircle field (n=2 ellipse, n>2 squarer)."""
    ry = rx if ry is None else ry
    ar = math.radians(a); c, s = math.cos(ar), math.sin(ar)
    def f(X, Y):
        x = (X - cx) * c + (Y - cy) * s
        y = -(X - cx) * s + (Y - cy) * c
        v = (np.abs(x / rx) ** n + np.abs(y / ry) ** n) ** (1 / n)
        return (v - 1) * min(rx, ry)
    f.bb = (cx - max(rx, ry), cy - max(rx, ry), cx + max(rx, ry), cy + max(rx, ry))
    return f


def RR(cx, cy, w, h, r, a=0):
    """Rounded rectangle field."""
    ar = math.radians(a); c, s = math.cos(ar), math.sin(ar)
    def f(X, Y):
        x = (X - cx) * c + (Y - cy) * s
        y = -(X - cx) * s + (Y - cy) * c
        qx = np.abs(x) - (w / 2 - r); qy = np.abs(y) - (h / 2 - r)
        return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
    m = math.hypot(w, h) / 2
    f.bb = (cx - m, cy - m, cx + m, cy + m)
    return f


def _bb(fs):
    return (min(f.bb[0] for f in fs), min(f.bb[1] for f in fs), max(f.bb[2] for f in fs), max(f.bb[3] for f in fs))


def U(*fs, k=30):
    """Smooth union."""
    def f(X, Y):
        d = fs[0](X, Y)
        for g in fs[1:]:
            e = g(X, Y)
            h = np.maximum(k - np.abs(d - e), 0) / k
            d = np.minimum(d, e) - h * h * k / 4
        return d
    f.bb = _bb(fs)
    return f


def D(a, *bs):
    """a minus bs."""
    def f(X, Y):
        d = a(X, Y)
        for b in bs:
            d = np.maximum(d, -b(X, Y))
        return d
    f.bb = a.bb
    return f


def I(a, b):
    def f(X, Y):
        return np.maximum(a(X, Y), b(X, Y))
    f.bb = a.bb
    return f


def HALF(y0, below=True):
    """Half plane field: inside where Y < y0 (below=False keeps the top part)."""
    def f(X, Y):
        return (Y - y0) if not below else (y0 - Y)
    f.bb = (-1e5, -1e5, 1e5, 1e5)
    return f


# ---------------------------------------------------------------- tracing
def contours(field, step=2, pad=20):
    x0, y0, x1, y1 = field.bb
    x0, y0 = max(x0 - pad, -50), max(y0 - pad, -50)
    x1, y1 = min(x1 + pad, W + 50), min(y1 + pad, H + 50)
    xs = np.arange(x0, x1, step); ys = np.arange(y0, y1, step)
    X, Y = np.meshgrid(xs, ys)
    F = field(X, Y)
    F[0, :] = F[-1, :] = F[:, 0] = F[:, -1] = 1.0   # close shapes at the grid edge
    out = []
    for c in measure.find_contours(F, 0.0):
        if len(c) < 12:
            continue
        pts = np.stack([x0 + c[:, 1] * step, y0 + c[:, 0] * step], 1)[:-1]
        pts = np.stack([gaussian_filter1d(pts[:, i], 1.5, mode='wrap') for i in (0, 1)], 1)
        out.append(pts)
    return out


def path(ctx, polys):
    ctx.new_path()
    for p in polys:
        ctx.move_to(*p[0])
        for q in p[1:]:
            ctx.line_to(*q)
        ctx.close_path()


def _normals(pts):
    d = np.roll(pts, -1, 0) - np.roll(pts, 1, 0)
    n = np.stack([d[:, 1], -d[:, 0]], 1)
    return n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-9)


def ink_closed(ctx, pts, w, seed=0, vary=0.22):
    """Variable-weight outline around a closed polygon (heavier on lower-right edges)."""
    n = _normals(pts)
    area = 0.5 * np.sum(pts[:, 0] * np.roll(pts[:, 1], -1) - np.roll(pts[:, 0], -1) * pts[:, 1])
    if area > 0:
        n = -n
    rng = np.random.RandomState(seed)
    wob = gaussian_filter1d(rng.randn(len(pts)), 8, mode='wrap')
    wob /= (np.abs(wob).max() + 1e-9)
    lit = np.clip(n @ LIGHT, -1, 1) * 0.5 + 0.5
    wid = w * (1 - vary + 2 * vary * lit + 0.06 * wob)
    a = pts + n * wid[:, None] / 2
    b = pts - n * wid[:, None] / 2
    ctx.new_path()
    ctx.move_to(*a[0]); [ctx.line_to(*p) for p in a[1:]]; ctx.close_path()
    ctx.move_to(*b[0]); [ctx.line_to(*p) for p in b[1:]]; ctx.close_path()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.set_source_rgb(0, 0, 0); ctx.fill()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)


def shape(ctx, field, w=LW, fill='white', seed=0, step=2):
    """Fill + outline a field. fill: 'white', 'black' or None. Returns the polygons."""
    polys = contours(field, step)
    if not polys:
        return polys
    if fill:
        path(ctx, polys)
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.set_source_rgb(*((1, 1, 1) if fill == 'white' else (0, 0, 0)))
        ctx.fill()
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    if w and fill != 'black':
        for i, p in enumerate(polys):
            ink_closed(ctx, p, w, seed + i)
    return polys


def poly_shape(ctx, pts, w=LW, fill='white', seed=0, smooth=3):
    """Fill + outline a polygon given by points (corners rounded by Chaikin)."""
    pts = np.array(pts, float)
    for _ in range(smooth):
        q = np.roll(pts, -1, 0)
        pts = np.stack([0.75 * pts + 0.25 * q, 0.25 * pts + 0.75 * q], 1).reshape(-1, 2)
    pts = _resample(pts, closed=True)
    if fill:
        path(ctx, [pts]); ctx.set_source_rgb(*((1, 1, 1) if fill == 'white' else (0, 0, 0))); ctx.fill()
    if w and fill != 'black':
        ink_closed(ctx, pts, w, seed)
    return [pts]


def _resample(pts, closed=False, spacing=4):
    P = np.vstack([pts, pts[:1]]) if closed else pts
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    if s[-1] < 1:
        return pts
    t = np.linspace(0, s[-1], max(int(s[-1] / spacing), 8), endpoint=not closed)
    return np.stack([np.interp(t, s, P[:, i]) for i in (0, 1)], 1)


def spline(ctrl, n=80, closed=False):
    """Catmull-Rom through control points."""
    P = np.array(ctrl, float)
    if closed:
        P = np.vstack([P[-1:], P, P[:2]])
    else:
        P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    segs = len(P) - 3
    per = max(n // segs, 4)
    for i in range(segs):
        p0, p1, p2, p3 = P[i:i + 4]
        for t in np.linspace(0, 1, per, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not closed:
        out.append(P[-2])
    return np.array(out)


def line(ctx, ctrl, w=LD, smooth=True, cap=cairo.LINE_CAP_ROUND):
    pts = spline(ctrl) if (smooth and len(ctrl) > 2) else np.array(ctrl, float)
    ctx.new_path(); ctx.move_to(*pts[0]); [ctx.line_to(*p) for p in pts[1:]]
    ctx.set_line_width(w); ctx.set_line_cap(cap); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgb(0, 0, 0); ctx.stroke()


def tapered(ctx, ctrl, w=LD, taper=(0.3, 0.3)):
    """Open stroke that thins toward its ends (for hair, grass, motion lines)."""
    pts = _resample(spline(ctrl) if len(ctrl) > 2 else np.array(ctrl, float))
    t = np.linspace(0, 1, len(pts))
    prof = np.minimum(np.clip(t / max(taper[0], 1e-3), 0, 1), np.clip((1 - t) / max(taper[1], 1e-3), 0, 1))
    wid = w * (0.25 + 0.75 * np.sin(prof * math.pi / 2))
    d = np.gradient(pts, axis=0)
    n = np.stack([d[:, 1], -d[:, 0]], 1); n /= (np.linalg.norm(n, axis=1, keepdims=True) + 1e-9)
    a = pts + n * wid[:, None] / 2; b = pts - n * wid[:, None] / 2
    ctx.new_path(); ctx.move_to(*a[0]); [ctx.line_to(*p) for p in a[1:]]
    [ctx.line_to(*p) for p in b[::-1]]; ctx.close_path()
    ctx.set_source_rgb(0, 0, 0); ctx.fill()


def tube_field(ctrl, w0, w1):
    """SDF of a tapered capsule chain along a smooth centerline (no self-intersection glitches)."""
    c = _resample(spline(ctrl) if len(ctrl) > 2 else np.array(ctrl, float), spacing=6)
    r = (w0 + (w1 - w0) * np.linspace(0, 1, len(c))) / 2
    A, B = c[:-1], c[1:]; ra, rb = r[:-1], r[1:]
    def f(X, Y):
        d = np.full(X.shape, 1e9)
        for a, b, r0, r1 in zip(A, B, ra, rb):
            ab = b - a; L2 = ab @ ab + 1e-9
            t = np.clip(((X - a[0]) * ab[0] + (Y - a[1]) * ab[1]) / L2, 0, 1)
            dist = np.hypot(X - (a[0] + t * ab[0]), Y - (a[1] + t * ab[1])) - (r0 + (r1 - r0) * t)
            d = np.minimum(d, dist)
        return d
    m = max(w0, w1)
    f.bb = (c[:, 0].min() - m, c[:, 1].min() - m, c[:, 0].max() + m, c[:, 1].max() + m)
    return f


def tube(ctx, ctrl, w0, w1, lw=LW, fill='white', seed=0, cap=True):
    """A limb / tentacle / stem with width going w0 -> w1 and rounded ends."""
    return shape(ctx, tube_field(ctrl, w0, w1), lw, fill, seed)


class clip:
    """with clip(ctx, polys): draw details only inside a shape."""
    def __init__(self, ctx, polys):
        self.ctx, self.polys = ctx, polys
    def __enter__(self):
        self.ctx.save(); path(self.ctx, self.polys)
        self.ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD); self.ctx.clip()
        self.ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    def __exit__(self, *a):
        self.ctx.restore()


# ---------------------------------------------------------------- small elements
def dot(ctx, x, y, r, black=True):
    ctx.new_path(); ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.set_source_rgb(*((0, 0, 0) if black else (1, 1, 1))); ctx.fill()


def ring(ctx, x, y, r, w=LD):
    ctx.new_path(); ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.set_source_rgb(1, 1, 1); ctx.fill_preserve()
    ctx.set_source_rgb(0, 0, 0); ctx.set_line_width(w); ctx.stroke()


def bubble(ctx, x, y, r, w=LD):
    ring(ctx, x, y, r, w)
    if r > 18:
        ctx.new_path(); ctx.arc(x, y, r * 0.62, math.radians(200), math.radians(250))
        ctx.set_line_width(max(w * 0.7, 4)); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()


def star_pts(x, y, r, rot=0, inner=0.5, pts=5):
    out = []
    for i in range(pts * 2):
        a = math.radians(rot) - math.pi / 2 + i * math.pi / pts
        rr = r if i % 2 == 0 else r * inner
        out.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    return out


def star(ctx, x, y, r, rot=0, w=LD, fill='white'):
    return poly_shape(ctx, star_pts(x, y, r, rot, 0.48), w, fill, smooth=2)


def sparkle(ctx, x, y, r, w=LD, filled=True):
    """Four-point twinkle."""
    pts = []
    for i in range(8):
        a = -math.pi / 2 + i * math.pi / 4
        rr = r if i % 2 == 0 else r * 0.22
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    return poly_shape(ctx, pts, w * 0.8, 'black' if filled else 'white', smooth=1)


def eye(ctx, x, y, r, look=(0, 0)):
    ctx.new_path(); ctx.save(); ctx.translate(x, y); ctx.scale(0.86, 1)
    ctx.arc(0, 0, r, 0, 2 * math.pi); ctx.restore()
    ctx.set_source_rgb(0, 0, 0); ctx.fill()
    dot(ctx, x - r * 0.3 + look[0], y - r * 0.38 + look[1], r * 0.32, black=False)


def happy_eye(ctx, x, y, r, w=LD + 1):
    """Closed smiling eye (an upside-down U)."""
    ctx.new_path(); ctx.arc(x, y + r * 0.3, r, math.radians(200), math.radians(340))
    ctx.set_line_width(w); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_source_rgb(0, 0, 0); ctx.stroke()


def smile(ctx, x, y, r, w=LD + 1, open_mouth=False):
    if open_mouth:
        ctx.new_path(); ctx.arc(x, y, r, 0, math.pi); ctx.close_path()
        ctx.set_source_rgb(0, 0, 0); ctx.fill()
        ctx.new_path(); ctx.arc(x, y + r * 0.55, r * 0.45, math.pi * 1.05, math.pi * 1.95)
        ctx.close_path(); ctx.set_source_rgb(1, 1, 1); ctx.fill()
        return
    ctx.new_path(); ctx.arc(x, y - r * 0.4, r, math.radians(25), math.radians(155))
    ctx.set_line_width(w); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_source_rgb(0, 0, 0); ctx.stroke()


def cheeks(ctx, x1, x2, y, r, w=LD - 2):
    for x in (x1, x2):
        ctx.new_path(); ctx.save(); ctx.translate(x, y); ctx.scale(1, 0.62); ctx.arc(0, 0, r, 0, 2 * math.pi); ctx.restore()
        ctx.set_line_width(w); ctx.set_source_rgb(0, 0, 0); ctx.stroke()


def face(ctx, x, y, s, kind='dots', mouth='smile'):
    """Cute face centered at x,y, s = scale (1 = eyes ~25px)."""
    ex = 48 * s
    if kind == 'dots':
        eye(ctx, x - ex, y, 22 * s); eye(ctx, x + ex, y, 22 * s)
    else:
        happy_eye(ctx, x - ex, y, 20 * s); happy_eye(ctx, x + ex, y, 20 * s)
    smile(ctx, x, y + 46 * s, 26 * s, open_mouth=(mouth == 'open'))
    cheeks(ctx, x - ex - 30 * s, x + ex + 30 * s, y + 42 * s, 16 * s)


def cloud(ctx, x, y, s, w=LD + 2, seed=0):
    f = U(E(x, y, 150 * s, 55 * s), E(x - 70 * s, y - 25 * s, 62 * s, 60 * s), E(x + 35 * s, y - 50 * s, 82 * s, 78 * s),
          E(x + 110 * s, y - 10 * s, 55 * s, 50 * s), k=12)
    return shape(ctx, I(f, HALF(y + 45 * s, below=False)) if False else f, w, seed=seed)


def outline_text(ctx, txt, x, y, size, w=8, font="Poppins", bold=True, center=True):
    ctx.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    ext = ctx.text_extents(txt)
    tx = x - (ext.width / 2 + ext.x_bearing) if center else x
    ctx.new_path(); ctx.move_to(tx, y); ctx.text_path(txt)
    ctx.set_source_rgb(1, 1, 1); ctx.fill_preserve()
    ctx.set_source_rgb(0, 0, 0); ctx.set_line_width(w); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()


def new_page():
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(1, 1, 1); ctx.paint()
    ctx.set_antialias(cairo.ANTIALIAS_BEST)
    return surf, ctx


def frame(ctx, m=80, r=60, w=10):
    ctx.new_path()
    ctx.arc(m + r, m + r, r, math.pi, 1.5 * math.pi); ctx.arc(W - m - r, m + r, r, 1.5 * math.pi, 0)
    ctx.arc(W - m - r, H - m - r, r, 0, 0.5 * math.pi); ctx.arc(m + r, H - m - r, r, 0.5 * math.pi, math.pi)
    ctx.close_path(); ctx.set_source_rgb(0, 0, 0); ctx.set_line_width(w); ctx.stroke()


def frame_clip(ctx, m=80, r=60):
    ctx.new_path()
    ctx.arc(m + r, m + r, r, math.pi, 1.5 * math.pi); ctx.arc(W - m - r, m + r, r, 1.5 * math.pi, 0)
    ctx.arc(W - m - r, H - m - r, r, 0, 0.5 * math.pi); ctx.arc(m + r, H - m - r, r, 0.5 * math.pi, math.pi)
    ctx.close_path(); ctx.clip()


def scatter(rng, n, boxes, avoid, rmin):
    """Random points inside allowed boxes, away from 'avoid' circles (x, y, r)."""
    pts = []
    tries = 0
    while len(pts) < n and tries < n * 400:
        tries += 1
        bx = boxes[rng.randint(0, len(boxes) - 1)]
        x = rng.uniform(bx[0], bx[2]); y = rng.uniform(bx[1], bx[3])
        if any(math.hypot(x - a, y - b) < r + rmin for a, b, r in avoid):
            continue
        if any(math.hypot(x - a, y - b) < rmin * 2.2 for a, b in pts):
            continue
        pts.append((x, y))
    return pts
