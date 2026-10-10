"""Hand-drawn style helpers: closed spline shapes, tapered inner strokes, transforms (no ovals)."""
import math
import numpy as np
import cairo
from ink import (cheeks, spline, _resample, ink_closed, path, tube_field, shape, line, tapered, dot, star, sparkle,
                 E, U, D, I, RR, clip, W, H, LW, LD, eye, new_page, frame, frame_clip, scatter, ring, poly_shape, star_pts)

OUT, MID, THIN = 14, 8, 6      # outline / inner / detail weights at scale 1


class Xf:
    """Local -> page transform: scale, rotate (deg), flip, translate."""
    def __init__(self, x, y, s=1.0, rot=0.0, flip=False):
        self.x, self.y, self.s, self.r, self.f = x, y, s, math.radians(rot), flip
    def __call__(self, p):
        a = np.array(p, float)
        if a.ndim == 1:
            return self._one(a)
        return np.array([self._one(q) for q in a])
    def _one(self, q):
        px, py = q[0] * self.s * (-1 if self.f else 1), q[1] * self.s
        c, sn = math.cos(self.r), math.sin(self.r)
        return np.array([self.x + px * c - py * sn, self.y + px * sn + py * c])


def blob(ctx, T, ctrl, w=OUT, fill='white', seed=0, n=240):
    """Closed Catmull-Rom shape through control points (local coords)."""
    pts = spline(T(ctrl), n=n, closed=True)
    pts = _resample(pts, closed=True, spacing=3)
    if fill:
        path(ctx, [pts]); ctx.set_source_rgb(*((1, 1, 1) if fill == 'white' else (0, 0, 0))); ctx.fill()
    if w and fill != 'black':
        ink_closed(ctx, pts, w * T.s ** 0.5, seed)
    return [pts]


def stroke(ctx, T, ctrl, w=MID, taper=(0.35, 0.35)):
    tapered(ctx, T(ctrl), w * T.s ** 0.5, taper)


def limb(ctx, T, ctrl, w0, w1, lw=OUT, seed=0, fill='white'):
    return shape(ctx, tube_field(T(ctrl), w0 * T.s, w1 * T.s), lw * T.s ** 0.5, fill, seed)


def spot(ctx, T, ctrl, seed=0):
    return blob(ctx, T, ctrl, 0, 'black', seed)


def eye2(ctx, T, x, y, r):
    p = T((x, y))
    eye(ctx, p[0], p[1], r * T.s)


def hearts(ctx, x, y, r, rot=0, fill='white', w=7):
    pts = []
    for t in np.linspace(0, 2 * math.pi, 48, endpoint=False):
        px = 16 * math.sin(t) ** 3
        py = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((px / 17 * r, py / 17 * r))
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    pts = [(x + a * c - b * s, y + a * s + b * c) for a, b in pts]
    return poly_shape(ctx, pts, w, fill, smooth=1)


def flower(ctx, x, y, r, rot=0, petals=5, w=7):
    for i in range(petals):
        a = math.radians(rot + i * 360 / petals)
        T = Xf(x + math.cos(a) * r * 0.78, y + math.sin(a) * r * 0.78, r / 30, math.degrees(a) + 90)
        blob(ctx, T, [(0, -26), (17, -8), (12, 20), (0, 28), (-12, 20), (-17, -8)], w, seed=i, n=60)
    ring(ctx, x, y, r * 0.38, w)
    dot(ctx, x, y, r * 0.12)


def grass(ctx, x, y, s=1.0):
    for dx, h, lean in ((-26, 70, -22), (0, 100, 4), (26, 66, 22)):
        tapered(ctx, [(x + dx * s, y), (x + (dx + lean * 0.4) * s, y - h * s * 0.55), (x + (dx + lean) * s, y - h * s)], 9 * s, (0.05, 0.9))


def ground(ctx, y0, amp=14, w=8):
    pts = [(x, y0 + amp * math.sin(x / 190.0)) for x in range(70, 1640, 40)]
    tapered(ctx, pts, w, (0.08, 0.12))


def ground_y(y0, x, amp=14):
    """Page y of the ground line at x (same curve as ground())."""
    return y0 + amp * math.sin(x / 190.0)


def paw_at(ctx, T, p, d, size=1.0, seed=0, w=OUT - 2):
    """Mitten paw centred at local point p, fingers pointing along local direction d."""
    ang = math.degrees(math.atan2(d[0], -d[1]))
    c = T(p)
    P = Xf(c[0], c[1], T.s * size, math.degrees(T.r) + ang)
    blob(ctx, P, [(-38, -12), (-32, -48), (0, -60), (32, -48), (38, -12), (32, 34), (0, 46), (-32, 34)], w, seed=seed, n=100)
    for x in (-13, 13):
        stroke(ctx, P, [(x, -57), (x, -28)], 5, (0.1, 0.3))


def arm(ctx, T, ctrl, w0=88, w1=76, seed=0, size=1.0):
    """Tapered arm along ctrl, with a paw at the end pointing along the arm."""
    limb(ctx, T, ctrl, w0, w1, OUT, seed=seed)
    (x0, y0), (x1, y1) = ctrl[-2], ctrl[-1]
    n = math.hypot(x1 - x0, y1 - y0)
    d = ((x1 - x0) / n, (y1 - y0) / n)
    paw_at(ctx, T, (x1 + d[0] * 14, y1 + d[1] * 14), d, size, seed + 5)


def flower_stem(ctx, x, gy, h, r, lean=0, rot=0, w=7):
    """Flower on a stem growing up from the ground point (x, gy)."""
    tapered(ctx, [(x, gy + 6), (x + lean * 0.4, gy - h * 0.5), (x + lean, gy - h)], 9, (0.02, 0.2))
    side = 1 if lean >= 0 else -1
    L = Xf(x + lean * 0.4 - side * 4, gy - h * 0.45, 1.0, 60 * side)
    blob(ctx, L, [(0, 0), (22, -14), (46, -4), (24, 10)], 6, seed=5, n=50)
    flower(ctx, x + lean, gy - h - r * 0.7, r, rot, w=w)


def tuft(ctx, x, gy, s=1.0):
    """Grass tuft whose base sits on the ground point (x, gy)."""
    grass(ctx, x, gy + 4, s)
