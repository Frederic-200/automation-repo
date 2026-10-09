"""Phase 1 prototype: SDF smooth-union silhouettes, variable-weight ink, spot blacks, overlap, 3-band background."""
import math, random, sys
import numpy as np, cairo
from skimage import measure
from scipy.ndimage import gaussian_filter1d

W, H = 1700, 2200
LIGHT = np.array([0.45, 0.89])   # ink is heavier on the lower-right edges

def rot(x, y, a):
    c, s = math.cos(a), math.sin(a); return c*x - s*y, s*x + c*y

class P:   # a primitive: squircle/ellipse in page coords
    def __init__(s, cx, cy, rx, ry, a=0, n=2.4): s.cx, s.cy, s.rx, s.ry, s.a, s.n = cx, cy, rx, ry, math.radians(a), n
    def f(s, X, Y):
        x, y = rot(X - s.cx, Y - s.cy, -s.a)
        v = (np.abs(x/s.rx)**s.n + np.abs(y/s.ry)**s.n)**(1/s.n)
        return (v - 1) * min(s.rx, s.ry)
    def bbox(s, m=0):
        r = max(s.rx, s.ry) + m; return s.cx-r, s.cy-r, s.cx+r, s.cy+r

def smin(a, b, k):
    h = np.maximum(k - np.abs(a-b), 0)/k; return np.minimum(a, b) - h*h*k/4

def union_contour(parts, k=40, step=3):
    x0 = min(p.bbox(k)[0] for p in parts); y0 = min(p.bbox(k)[1] for p in parts)
    x1 = max(p.bbox(k)[2] for p in parts); y1 = max(p.bbox(k)[3] for p in parts)
    xs = np.arange(x0, x1, step); ys = np.arange(y0, y1, step); X, Y = np.meshgrid(xs, ys)
    f = parts[0].f(X, Y)
    for p in parts[1:]: f = smin(f, p.f(X, Y), k)
    cs = measure.find_contours(f, 0.0)
    c = max(cs, key=len)
    pts = np.stack([x0 + c[:, 1]*step, y0 + c[:, 0]*step], 1)
    for _ in range(2):
        pts = np.stack([gaussian_filter1d(pts[:, i], 2, mode='wrap') for i in (0, 1)], 1)
    return pts[::2]

def normals(pts, closed=True):
    d = np.roll(pts, -1, 0) - np.roll(pts, 1, 0) if closed else np.gradient(pts, axis=0)
    n = np.stack([d[:, 1], -d[:, 0]], 1); n /= (np.linalg.norm(n, axis=1, keepdims=True) + 1e-9); return n

def ink_poly(ctx, pts, w, closed=True, taper=False, seed=1):
    ctx.new_path()
    rng = np.random.RandomState(seed)
    n = normals(pts, closed)
    if closed:
        # orient so n points outward (area sign)
        area = 0.5*np.sum(pts[:, 0]*np.roll(pts[:, 1], -1) - np.roll(pts[:, 0], -1)*pts[:, 1])
        if area > 0: n = -n
        wob = gaussian_filter1d(rng.randn(len(pts)), 6, mode='wrap'); wob /= (np.abs(wob).max()+1e-9)
        lit = np.clip(n @ LIGHT, -1, 1)
        wid = w*(0.62 + 0.38*(lit*0.5+0.5)*1.5 + 0.12*wob)
    else:
        t = np.linspace(0, 1, len(pts)); prof = np.sin(np.pi*t)**0.6 if taper else 1+0*t
        wid = w*(0.25 + 0.95*prof)
    a = pts + n*wid[:, None]/2; b = pts - n*wid[:, None]/2
    ctx.move_to(*a[0])
    for p in a[1:]: ctx.line_to(*p)
    if closed: ctx.close_path(); ctx.new_sub_path(); ctx.move_to(*b[0])
    else: pass
    for p in (b if closed else b[::-1]): ctx.line_to(*p)
    ctx.close_path()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD if closed else cairo.FILL_RULE_WINDING)
    ctx.fill()

def poly_path(ctx, pts):
    ctx.move_to(*pts[0]); [ctx.line_to(*p) for p in pts[1:]]; ctx.close_path()

def layer(ctx, parts, k=40, w=11, fill=True, seed=1):
    pts = union_contour(parts, k)
    if fill:
        poly_path(ctx, pts); ctx.set_source_rgb(1, 1, 1); ctx.fill()
    ctx.set_source_rgb(0, 0, 0); ink_poly(ctx, pts, w, True, seed=seed); return pts

def stroke(ctx, ctrl, w, taper=True, seed=1):
    ctrl = np.array(ctrl, float)
    t = np.linspace(0, 1, 60); m = len(ctrl)
    pts = np.stack([np.interp(t*(m-1), range(m), ctrl[:, i]) for i in (0, 1)], 1)
    pts = np.stack([gaussian_filter1d(pts[:, i], 4, mode='nearest') for i in (0, 1)], 1)
    ctx.set_source_rgb(0, 0, 0); ink_poly(ctx, pts, w, False, taper, seed)

def blob(ctx, cx, cy, rx, ry, a=0, black=True, n=2.2):
    pts = union_contour([P(cx, cy, rx, ry, a, n)], 1, 2); poly_path(ctx, pts)
    ctx.set_source_rgb(*( (0,0,0) if black else (1,1,1) )); ctx.fill(); return pts

def eye(ctx, x, y, r):
    blob(ctx, x, y, r*0.85, r, 0); blob(ctx, x - r*0.28, y - r*0.35, r*0.28, r*0.28, 0, black=False, n=2)

def smile(ctx, x, y, w, depth, up=True):
    stroke(ctx, [(x - w/2, y), (x - w*0.2, y + depth), (x + w*0.2, y + depth), (x + w/2, y - depth*0.1)], 7, True)

def clipped(ctx, region, fn):
    ctx.save(); poly_path(ctx, region); ctx.clip(); fn(); ctx.restore()

# ---------------- animals ----------------
def cow(ctx, X, Y, s, flip=False, seed=3):
    def T(x, y): return (X + (-x if flip else x)*s, Y + y*s)
    def pr(x, y, rx, ry, a=0, n=2.4): 
        cx, cy = T(x, y); return P(cx, cy, rx*s, ry*s, -a if flip else a, n)
    # back legs, tail, body w/ front legs, ears, head, snout
    tl = T(-330, -20); stroke(ctx, [T(-310, 10), T(-420, -40), T(-440, 110), T(-420, 190)], 13*s/1.0, True)
    blob(ctx, *T(-420, 205), 38*s, 55*s, 15)
    layer(ctx, [pr(-190, 330, 62, 120, 4), ], 20, 10*s/0.9)
    body = layer(ctx, [pr(-20, 80, 360, 230, -3), pr(120, 330, 66, 130, -3), pr(-210, 330, 60, 115, 4)], 70, 12*s/0.9, seed=seed)
    def spots():
        ctx.set_source_rgb(0, 0, 0)
        blob(ctx, *T(-130, 20), 120*s, 85*s, 20, n=2.0); blob(ctx, *T(130, 150), 90*s, 70*s, -30, n=2.0)
        blob(ctx, *T(-250, 190), 60*s, 48*s, 10, n=2.0)
    clipped(ctx, body, spots)
    ctx.set_source_rgb(0, 0, 0); poly_path(ctx, body); ink_poly(ctx, body, 12*s/0.9, True, seed=seed)
    # hooves
    for hx, hy in ((120, 440), (-210, 435)): blob(ctx, *T(hx, hy), 56*s, 24*s)
    # ears + horns behind head
    for ex, ey, ea in ((130, -230, -40), (350, -230, 40)):
        layer(ctx, [pr(ex, ey, 70, 38, ea)], 10, 8*s/0.9)
    for hx, hy, ha in ((200, -300, -20), (290, -300, 20)):
        layer(ctx, [pr(hx, hy, 24, 46, ha)], 10, 8*s/0.9)
    head = layer(ctx, [pr(245, -95, 175, 160, 8, 2.6)], 10, 12*s/0.9, seed=seed+1)
    # eye patch spot
    clipped(ctx, head, lambda: blob(ctx, *T(180, -150), 70*s, 62*s, -20, n=2.0))
    ctx.set_source_rgb(0, 0, 0); poly_path(ctx, head); ink_poly(ctx, head, 12*s/0.9, True, seed=seed+1)
    snout = layer(ctx, [pr(265, -20, 118, 74, 6)], 10, 8*s/0.9, seed=seed+2)
    blob(ctx, *T(235, -30), 15*s, 21*s, 0); blob(ctx, *T(300, -26), 15*s, 21*s, 0)
    smile(ctx, *T(268, 28), 90*s, 14*s)
    eye(ctx, *T(215, -135), 27*s); eye(ctx, *T(320, -125), 27*s)
    # tuft + hair swirl
    stroke(ctx, [T(260, -250), T(270, -215), T(285, -205)], 7*s/0.9, True)

def pig(ctx, X, Y, s, flip=False, seed=5):
    def T(x, y): return (X + (-x if flip else x)*s, Y + y*s)
    def pr(x, y, rx, ry, a=0, n=2.4): cx, cy = T(x, y); return P(cx, cy, rx*s, ry*s, -a if flip else a, n)
    stroke(ctx, [T(-250, 40), T(-330, 0), T(-300, -50), T(-350, -80)], 11*s/0.9, True)
    layer(ctx, [pr(-110, 300, 55, 100, 3)], 10, 10*s/0.9)
    layer(ctx, [pr(80, 300, 55, 100, -3), pr(-30, 60, 280, 220, 0, 2.2)], 80, 12*s/0.9, seed=seed)
    for hx in (-110, 80): blob(ctx, *T(hx, 395), 46*s, 20*s)
    for ex, ey, ea, sg in ((150, -230, -35, 1), (330, -235, 35, 1)):
        layer(ctx, [pr(ex, ey, 62, 70, ea, 2.0)], 10, 9*s/0.9); blob(ctx, *T(ex, ey+5), 28*s, 36*s, ea, n=2)
    head = layer(ctx, [pr(240, -90, 190, 165, 6, 2.5)], 10, 12*s/0.9, seed=seed+1)
    layer(ctx, [pr(285, -20, 112, 80, 5, 2.0)], 10, 8*s/0.9, seed=seed+2)
    blob(ctx, *T(255, -22), 14*s, 22*s); blob(ctx, *T(320, -20), 14*s, 22*s)
    smile(ctx, *T(285, 50), 70*s, 12*s)
    eye(ctx, *T(200, -130), 26*s); eye(ctx, *T(310, -125), 26*s)
    # cheek blush lines
    for cx in (170, 345): stroke(ctx, [T(cx-14, -45), T(cx, -40), T(cx+14, -45)], 5*s/0.9, True)

def sheep(ctx, X, Y, s, flip=False, seed=7):
    def T(x, y): return (X + (-x if flip else x)*s, Y + y*s)
    def pr(x, y, rx, ry, a=0, n=2.4): cx, cy = T(x, y); return P(cx, cy, rx*s, ry*s, -a if flip else a, n)
    for lx in (-120, 100):
        layer(ctx, [pr(lx, 300, 28, 110, 0, 2.2)], 10, 9*s/0.9); blob(ctx, *T(lx, 405), 34*s, 18*s)
    # fluffy wool: scalloped union of circles
    rng = random.Random(seed); wool = []
    for i in range(11):
        a = i/11*2*math.pi; wool.append(pr(-10 + 250*math.cos(a), 40 + 170*math.sin(a), 100, 100, 0, 2.0))
    wool.append(pr(-10, 40, 240, 160, 0, 2.0))
    layer(ctx, wool, 8, 11*s/0.9, seed=seed)
    # wool curls inside
    for cx, cy in ((-120, 20), (20, -20), (110, 90), (-60, 120)):
        stroke(ctx, [T(cx-30, cy), T(cx-10, cy-30), T(cx+25, cy-15), T(cx+15, cy+15)], 6*s/0.9, True)
    layer(ctx, [pr(130, -70, 70, 38, -30)], 10, 8*s/0.9)
    layer(ctx, [pr(360, -70, 70, 38, 30)], 10, 8*s/0.9)
    layer(ctx, [pr(240, -120, 120, 90, 4, 2.4)], 30, 10*s/0.9, seed=seed+1)  # wool tuft on head
    head = layer(ctx, [pr(245, -60, 125, 140, 5, 2.6)], 10, 12*s/0.9, seed=seed+2)
    clipped(ctx, head, lambda: None)
    blob(ctx, *T(250, 10), 22*s, 17*s)  # nose
    smile(ctx, *T(250, 45), 60*s, 11*s)
    eye(ctx, *T(205, -75), 24*s); eye(ctx, *T(295, -72), 24*s)

def chick(ctx, X, Y, s, flip=False, seed=9):
    def T(x, y): return (X + (-x if flip else x)*s, Y + y*s)
    def pr(x, y, rx, ry, a=0, n=2.4): cx, cy = T(x, y); return P(cx, cy, rx*s, ry*s, -a if flip else a, n)
    for lx in (-60, 70): stroke(ctx, [T(lx, 230), T(lx, 300), T(lx-30, 330)], 9*s/0.9, False); stroke(ctx, [T(lx, 300), T(lx+35, 330)], 9*s/0.9, False)
    layer(ctx, [pr(0, 40, 220, 215, 0, 2.1)], 10, 12*s/0.9, seed=seed)
    layer(ctx, [pr(-180, 70, 70, 120, 25, 2.0)], 10, 9*s/0.9)  # wing
    stroke(ctx, [T(-5, -190), T(-30, -260), T(-5, -270)], 8*s/0.9, True); stroke(ctx, [T(20, -190), T(35, -265), T(60, -255)], 8*s/0.9, True)
    layer(ctx, [pr(95, 40, 55, 30, 0, 2.0), pr(95, 76, 50, 26, 0, 2.0)], 14, 8*s/0.9)  # beak
    eye(ctx, *T(55, -40), 24*s); eye(ctx, *T(-30, -40), 24*s)
    for cx in (110, -85): blob(ctx, *T(cx, 20), 1, 1, 0)

# ---------------- background ----------------
def tree(ctx, x, y, s, w=7):
    layer(ctx, [P(x, y - 90*s, 42*s, 110*s, 3, 2.4)], 10, w)
    layer(ctx, [P(x - 130*s, y - 330*s, 140*s, 120*s, 0, 2.0), P(x + 130*s, y - 330*s, 140*s, 120*s, 0, 2.0), P(x, y - 430*s, 170*s, 130*s, 0, 2.0), P(x, y - 300*s, 220*s, 100*s, 0, 2.0)], 40, w, seed=4)
    for dx, dy in ((-80, -340), (60, -400), (110, -320)):
        stroke(ctx, [(x+dx*s-18, y+dy*s), (x+dx*s, y+dy*s-22), (x+dx*s+18, y+dy*s)], w*0.7, True)

def bush(ctx, x, y, s, w=7):
    layer(ctx, [P(x - 90*s, y, 90*s, 70*s, 0, 2.0), P(x + 90*s, y, 90*s, 70*s, 0, 2.0), P(x, y - 35*s, 110*s, 80*s, 0, 2.0)], 30, w, seed=2)

def cloud(ctx, x, y, s, w=5):
    layer(ctx, [P(x, y, 150*s, 52*s, 0, 2.0), P(x - 60*s, y - 30*s, 70*s, 60*s, 0, 2.0), P(x + 40*s, y - 40*s, 85*s, 70*s, 0, 2.0)], 30, w, seed=6)

def grass(ctx, x, y, s, w=6):
    for dx, h, lean in ((-20, 45, -8), (0, 62, 0), (20, 45, 8)):
        stroke(ctx, [(x+dx*s, y), (x+(dx+lean/2)*s, y-h*s*0.6), (x+(dx+lean)*s, y-h*s)], w, True)

def flower(ctx, x, y, s, w=6):
    stroke(ctx, [(x, y), (x+4*s, y-45*s), (x, y-90*s)], w, True)
    for i in range(5):
        a = i/5*2*math.pi - math.pi/2
        layer(ctx, [P(x+math.cos(a)*30*s, y-100*s+math.sin(a)*30*s, 22*s, 14*s, math.degrees(a), 2.0)], 6, w*0.8)
    blob(ctx, x, y-100*s, 14*s, 14*s, 0, black=True, n=2)

def frame(ctx, m=70):
    ctx.set_source_rgb(0, 0, 0); ctx.set_line_width(10)
    ctx.rectangle(m, m, W-2*m, H-2*m); ctx.stroke()

def page(path):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); ctx = cairo.Context(surf)
    ctx.set_source_rgb(1, 1, 1); ctx.paint(); ctx.set_antialias(cairo.ANTIALIAS_BEST)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    # clip scene to frame
    ctx.save(); ctx.rectangle(70, 70, W-140, H-140); ctx.clip()
    # sky band (thin lines)
    cloud(ctx, 400, 330, 1.1, 5); cloud(ctx, 1250, 250, 0.8, 5)
    blob(ctx, 1450, 330, 80, 80, 0, False); layer(ctx, [P(1450, 330, 80, 80, 0, 2)], 5, 5)
    for a in range(0, 360, 45):
        r1, r2 = 110, 150; ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        stroke(ctx, [(1450+ca*r1, 330+sa*r1), (1450+ca*r2, 330+sa*r2)], 6, True)
    # mid band: trees and bushes (medium)
    tree(ctx, 330, 1020, 1.25, 7); tree(ctx, 1330, 980, 1.0, 7)
    bush(ctx, 820, 900, 1.2, 7); bush(ctx, 1560, 1020, 0.9, 7)
    # ground line
    stroke(ctx, [(70, 1070), (500, 1050), (1000, 1075), (1630, 1055)], 7, True)
    # foreground: hero cow big, others overlapping
    sheep(ctx, 340, 1500, 0.78, flip=False)
    pig(ctx, 1360, 1480, 0.75, flip=True)
    cow(ctx, 800, 1300, 1.12, flip=False)
    chick(ctx, 1210, 1830, 0.55, flip=True)
    # flowers and grass bottom band
    for x, y, s in ((180, 1950, 1.0), (1500, 1985, 1.1), (700, 2040, 0.9), (1050, 2010, 0.8)): flower(ctx, x, y, s)
    for x, y in ((120, 1700), (1560, 1760), (520, 1990), (880, 2060), (1330, 2060), (300, 2070)): grass(ctx, x, y, 1.2)
    ctx.restore(); frame(ctx)
    # to pure 1-bit
    surf.write_to_png(path)

if __name__ == "__main__":
    page(sys.argv[1] if len(sys.argv) > 1 else "/tmp/p1.png")
