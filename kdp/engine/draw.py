"""Drawing core for Tiny Comet Prints books.

All page drawing happens in a 1700 x 2200 "page space" (US Letter at 200 units/inch).
A Pen wraps a cairo context that the caller has already scaled to that space, so the same
drawing code renders a vector PDF page or a PNG preview.

Style rules (see kdp/STYLE.md): pure black, thick, even outlines with round caps; cute
rounded shapes; white fills on interior pages (line art) or crayon colours on covers.
"""
import math
import random

import cairo

W, H = 1700, 2200
BLACK = (0, 0, 0)
WHITE = (1, 1, 1)

# Crayon palette used for colour-by-number keys and cover colouring (name -> rgb).
CRAYON = {
    "red": "#ff5a4e", "orange": "#ff9a2e", "yellow": "#ffd93b", "green": "#5cc95a",
    "blue": "#4aa8ff", "purple": "#a77bff", "pink": "#ff9bbf", "brown": "#a86b45",
    "gray": "#a9b2bd", "black": "#2b2b2b", "white": "#ffffff", "lightblue": "#9fd8ff",
    "darkgreen": "#2f9e4f", "tan": "#f2c891", "darkbrown": "#6b4a3a", "lightpink": "#ffc9d9",
}


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def col(name):
    """crayon name or hex -> rgb tuple"""
    if name is None:
        return None
    if isinstance(name, tuple):
        return name
    return hexc(CRAYON.get(name, name))


class Pen:
    def __init__(self, ctx, seed=1, lw=7.0):
        self.c = ctx
        self.lw = lw
        self.rng = random.Random(seed)
        self.k = 1.0
        self.colour = False      # True on covers: use palette fills
        self.labels = []         # (key, page_x, page_y, colour_name) recorded by part()
        self.names = {}          # last colour name used per part key
        self._base_inv = cairo.Matrix(*ctx.get_matrix())
        self._base_inv.invert()
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)

    # ---- transforms ------------------------------------------------
    def at(self, cx, cy, s, rot=0.0, flip=False):
        return _Scope(self, cx, cy, s, rot, flip)

    def page_xy(self, x, y):
        dx, dy = self.c.user_to_device(x, y)
        return self._base_inv.transform_point(dx, dy)

    # ---- fills -----------------------------------------------------
    def fill_of(self, F, key, default="white"):
        """Pick the fill for a part. Line-art mode always returns white."""
        name = (F or {}).get(key, default)
        self.names[key] = name
        if not self.colour:
            return WHITE
        return col(name)

    def part(self, key, x, y):
        """Record a label position (local coords) for colour-by-number."""
        px, py = self.page_xy(x, y)
        self.labels.append((key, px, py, self.names.get(key)))

    # ---- primitives ------------------------------------------------
    def _paint(self, fill, stroke=True, lw=None):
        c = self.c
        if fill is not None:
            c.set_source_rgb(*fill)
            if stroke:
                c.fill_preserve()
            else:
                c.fill()
        if stroke:
            c.set_source_rgb(*BLACK)
            c.set_line_width((lw or self.lw) / self.k)
            c.stroke()
        else:
            c.new_path()

    def ell(self, cx, cy, rx, ry, fill=WHITE, rot=0, lw=None, stroke=True):
        c = self.c
        c.save()
        c.translate(cx, cy)
        c.rotate(rot)
        c.scale(max(rx, .01), max(ry, .01))
        c.new_sub_path()
        c.arc(0, 0, 1, 0, 2 * math.pi)
        c.restore()
        self._paint(fill, stroke, lw)

    def circ(self, cx, cy, r, fill=WHITE, lw=None, stroke=True):
        self.ell(cx, cy, r, r, fill, lw=lw, stroke=stroke)

    def rrect_path(self, x, y, w, h, r):
        c = self.c
        r = min(r, w / 2, h / 2)
        c.new_sub_path()
        c.arc(x + w - r, y + r, r, -math.pi / 2, 0)
        c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
        c.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
        c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
        c.close_path()

    def rrect(self, x, y, w, h, r, fill=WHITE, lw=None, stroke=True):
        self.rrect_path(x, y, w, h, r)
        self._paint(fill, stroke, lw)

    def poly(self, pts, fill=WHITE, closed=True, lw=None):
        c = self.c
        c.move_to(*pts[0])
        for p in pts[1:]:
            c.line_to(*p)
        if closed:
            c.close_path()
        self._paint(fill if closed else None, True, lw)

    def spline_path(self, pts, closed=True, t=0.5):
        """Catmull-Rom spline through pts (adds to current path)."""
        c = self.c
        n = len(pts)
        c.move_to(*pts[0])
        rng = range(n) if closed else range(n - 1)
        for i in rng:
            p0 = pts[(i - 1) % n] if (closed or i > 0) else pts[0]
            p1 = pts[i]
            p2 = pts[(i + 1) % n]
            p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else pts[-1]
            c1 = (p1[0] + (p2[0] - p0[0]) * t / 3, p1[1] + (p2[1] - p0[1]) * t / 3)
            c2 = (p2[0] - (p3[0] - p1[0]) * t / 3, p2[1] - (p3[1] - p1[1]) * t / 3)
            c.curve_to(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
        if closed:
            c.close_path()

    def blob(self, pts, fill=WHITE, lw=None):
        self.spline_path(pts, True)
        self._paint(fill, True, lw)

    def curve(self, pts, lw=None):
        self.spline_path(pts, False)
        self._paint(None, True, lw)

    def line(self, pts, lw=None, dash=None):
        c = self.c
        c.move_to(*pts[0])
        for p in pts[1:]:
            c.line_to(*p)
        if dash:
            c.set_dash([d / self.k for d in dash])
        self._paint(None, True, lw)
        if dash:
            c.set_dash([])

    def arc(self, cx, cy, r, a0, a1, lw=None):
        c = self.c
        c.new_sub_path()
        c.arc(cx, cy, r, a0, a1)
        self._paint(None, True, lw)

    def dot(self, x, y, r, rgb=BLACK):
        c = self.c
        c.new_sub_path()
        c.arc(x, y, r, 0, 2 * math.pi)
        c.set_source_rgb(*rgb)
        c.fill()

    def star_pts(self, cx, cy, r, inner=.48, n=5, rot=-math.pi / 2):
        pts = []
        for i in range(n * 2):
            rr = r if i % 2 == 0 else r * inner
            a = rot + i * math.pi / n
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
        return pts

    def heart_path(self, cx, cy, s):
        c = self.c
        c.move_to(cx, cy + s * .9)
        c.curve_to(cx - s * 1.3, cy + s * .1, cx - s * .9, cy - s * .9, cx, cy - s * .35)
        c.curve_to(cx + s * .9, cy - s * .9, cx + s * 1.3, cy + s * .1, cx, cy + s * .9)
        c.close_path()

    # ---- text ------------------------------------------------------
    def font(self, size, bold=True):
        c = self.c
        c.select_font_face("Poppins", cairo.FONT_SLANT_NORMAL,
                           cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
        c.set_font_size(size)

    def text_w(self, s, size, bold=True):
        self.font(size, bold)
        return self.c.text_extents(s).x_advance

    def text(self, s, x, y, size, bold=True, anchor="l", rgb=BLACK):
        c = self.c
        self.font(size, bold)
        adv = c.text_extents(s).x_advance
        if anchor == "m":
            x -= adv / 2
        elif anchor == "r":
            x -= adv
        c.move_to(x, y)
        c.set_source_rgb(*rgb)
        c.show_text(s)
        return adv

    def fit_size(self, s, max_w, size, bold=True, min_size=20):
        while size > min_size and self.text_w(s, size, bold) > max_w:
            size -= 2
        return size

    def outline_text(self, s, x, y, size, anchor="m", lw=6, dash=None, fill=None):
        """Hollow letters for tracing pages (optionally dashed)."""
        c = self.c
        self.font(size, True)
        adv = c.text_extents(s).x_advance
        if anchor == "m":
            x -= adv / 2
        c.move_to(x, y)
        c.text_path(s)
        if fill is not None:
            c.set_source_rgb(*fill)
            c.fill_preserve()
        if dash:
            c.set_dash(dash)
        c.set_source_rgb(*BLACK)
        c.set_line_width(lw)
        c.stroke()
        c.set_dash([])

    # ---- face parts ------------------------------------------------
    def eye(self, cx, cy, r):
        self.ell(cx, cy, r, r * 1.15, WHITE)
        self.ell(cx + r * .08, cy + r * .1, r * .64, r * .74, BLACK, stroke=False)
        self.ell(cx + r * .3, cy - r * .2, r * .22, r * .22, WHITE, stroke=False)

    def happy_eye(self, cx, cy, r):
        self.arc(cx, cy + r * .5, r * .8, math.radians(200), math.radians(340), lw=self.lw * 1.2)

    def smile(self, cx, cy, w):
        self.arc(cx, cy - w * .35, w * .55, math.radians(30), math.radians(150))

    def open_smile(self, cx, cy, w, tongue=True):
        c = self.c
        c.new_sub_path()
        c.arc(cx, cy, w / 2, 0, math.pi)
        c.close_path()
        self._paint(WHITE if not self.colour else col("darkbrown"), True)
        if tongue:
            self.ell(cx, cy + w * .3, w * .22, w * .13, WHITE if not self.colour else col("pink"), lw=self.lw * .7)

    def cheeks(self, x, y, r, F=None):
        for sx in (-1, 1):
            self.ell(sx * x, y, r, r * .7, self.fill_of(F, "cheek", "lightpink"), lw=self.lw * .7)

    # ---- scenery (line art) ---------------------------------------
    def wobbly_frame(self, x0, y0, x1, y1, lw=9):
        r = self.rng
        for k in range(2):
            j = 4 if k == 0 else 6
            pts = []
            for (x, y, dx, dy, n) in [(x0, y0, 1, 0, 26), (x1, y0, 0, 1, 30), (x1, y1, -1, 0, 26), (x0, y1, 0, -1, 30)]:
                for i in range(n):
                    t = i / n
                    px = x + dx * (x1 - x0) * t if dx else x
                    py = y + dy * (y1 - y0) * t if dy else y
                    pts.append((px + r.uniform(-j, j), py + r.uniform(-j, j)))
            self.spline_path(pts, True)
            self._paint(None, True, lw if k == 0 else lw * .5)

    def bush(self, x0, y, n, r, fill=WHITE):
        c = self.c

        def build(close):
            c.new_path()
            c.move_to(x0, y)
            for i in range(n):
                c.arc(x0 + r * (2 * i + 1), y, r, math.pi, 2 * math.pi)
            if close:
                c.line_to(x0 + 2 * r * n, y + r * 1.6)
                c.line_to(x0, y + r * 1.6)
                c.close_path()
        build(True)
        c.set_source_rgb(*fill)
        c.fill()
        build(False)
        self._paint(None, True)

    def grass(self, x, y, s=1.0, n=3):
        pts = [(x, y)]
        for i in range(n):
            pts += [(x + (i * 22 + 8) * s, y - (36 + (i % 2) * 20) * s), (x + (i * 22 + 18) * s, y - 8 * s)]
        pts.append((x + n * 22 * s + 6 * s, y))
        self.line(pts, lw=self.lw * .85)

    def cloud(self, cx, cy, s=1.0, fill=WHITE):
        c = self.c
        parts = [(-90, 20, 55), (-30, -20, 70), (45, -5, 65), (100, 25, 48)]

        def build():
            c.new_path()
            for dx, dy, r in parts:
                c.new_sub_path()
                c.arc(cx + dx * s, cy + dy * s, r * s, 0, 2 * math.pi)
            self.rrect_path(cx - 120 * s, cy + 10 * s, 250 * s, 60 * s, 30 * s)
        build()
        c.set_source_rgb(*BLACK)
        c.set_line_width(self.lw * 2 / self.k)
        c.stroke_preserve()
        c.fill()
        build()
        c.set_source_rgb(*fill)
        c.fill()

    def bubbles(self, avoid, n=30, rmin=9, rmax=20, box=(170, 470, 1530, 1840), gap=85, ring=True):
        r = self.rng
        placed = []
        tries = 0
        while len(placed) < n and tries < 6000:
            tries += 1
            x = r.uniform(box[0], box[2])
            y = r.uniform(box[1], box[3])
            rad = r.uniform(rmin, rmax)
            if any(a[0] - rad - 10 < x < a[2] + rad + 10 and a[1] - rad - 10 < y < a[3] + rad + 10 for a in avoid):
                continue
            if any((x - px) ** 2 + (y - py) ** 2 < (rad + pr + gap) ** 2 for px, py, pr in placed):
                continue
            placed.append((x, y, rad))
        for x, y, rad in placed:
            if ring:
                self.circ(x, y, rad, WHITE, lw=self.lw * .8)
            else:
                self.poly(self.star_pts(x, y, rad * 1.4), WHITE, lw=self.lw * .7)
        return placed


class _Scope:
    def __init__(self, p, cx, cy, s, rot, flip):
        self.p, self.cx, self.cy, self.s, self.rot, self.flip = p, cx, cy, s, rot, flip

    def __enter__(self):
        p = self.p
        p.c.save()
        p.c.translate(self.cx, self.cy)
        if self.rot:
            p.c.rotate(self.rot)
        p.c.scale(-self.s if self.flip else self.s, self.s)
        self._k = p.k
        p.k = p.k * self.s
        return self

    def __exit__(self, *a):
        self.p.c.restore()
        self.p.k = self._k
