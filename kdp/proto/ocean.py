"""Sample page: Under the Sea."""
import math, random, sys
import numpy as np
from ink import *


def curl_path(x, y, heading, length, curl, turns=1.0, n=40):
    """Centerline that starts heading in a direction and curls at the end."""
    pts = [(x, y)]; th = math.radians(heading); ds = length / n
    for i in range(1, n + 1):
        s = i / n
        th += curl * (s ** 2.0) * turns * 2 * math.pi / n * 1.7
        x += math.cos(th) * ds; y += math.sin(th) * ds
        pts.append((x, y))
    return pts[::4] + [pts[-1]]


def octopus(ctx, cx, cy, s=1.0):
    # tentacles behind the head: (start dx, heading, length, curl dir)
    specs = [(-175, 160, 360, -1), (-115, 120, 400, -1), (-40, 98, 360, 1),
             (40, 82, 360, -1), (115, 60, 400, 1), (175, 20, 360, 1)]
    for i, (dx, hd, ln, cd) in enumerate(specs):
        c = curl_path(cx + dx * s, cy + 150 * s, hd, ln * s, cd * 1.15)
        tube(ctx, c, 84 * s, 30 * s, seed=i)
        # suckers on a couple of tentacles
        if i in (0, 5, 2):
            P = spline(c)
            for t in (0.35, 0.5, 0.64):
                k = int(t * (len(P) - 1)); p = P[k]
                d = P[min(k + 1, len(P) - 1)] - P[k]; nrm = np.array([d[1], -d[0]]) / (np.linalg.norm(d) + 1e-9)
                wid = (84 + (30 - 84) * t) * s
                side = -cd if i != 2 else cd
                q = p + nrm * side * wid * 0.25
                ring(ctx, q[0], q[1], wid * 0.17, 5)
    head = shape(ctx, U(E(cx, cy - 30 * s, 220 * s, 205 * s), E(cx, cy + 115 * s, 240 * s, 95 * s), k=60), seed=11)
    face(ctx, cx, cy + 5 * s, 1.5 * s, 'dots')
    # head shine + spots
    line(ctx, [(cx - 160 * s, cy - 70 * s), (cx - 135 * s, cy - 135 * s), (cx - 90 * s, cy - 175 * s)], LD)
    for (ox, oy, r) in ((100, -140, 26), (150, -80, 16), (55, -185, 14)):
        ring(ctx, cx + ox * s, cy + oy * s, r * s, 6)


def fish_scales(ctx, cx, cy, s=1.0, flip=False):
    sg = -1 if flip else 1
    X = lambda dx: cx + sg * dx * s
    poly_shape(ctx, [(X(-150), cy), (X(-290), cy - 130 * s), (X(-250), cy), (X(-290), cy + 130 * s)], LW, seed=3)
    for k in (-60, 0, 60):
        line(ctx, [(X(-175), cy + k * 0.2 * s), (X(-255), cy + k * 1.2 * s)], LD - 2)
    # dorsal fin
    poly_shape(ctx, [(X(-90), cy - 110 * s), (X(-40), cy - 200 * s), (X(60), cy - 175 * s), (X(80), cy - 110 * s)], LW, seed=4)
    for dx in (-30, 10, 45):
        line(ctx, [(X(dx), cy - 120 * s), (X(dx + 5), cy - 175 * s)], LD - 2)
    body = shape(ctx, E(cx, cy, 200 * s, 135 * s, n=2.1), seed=5)
    with clip(ctx, body):
        # scales: rows of scallops behind the gill line
        for row, yy in enumerate(np.arange(cy - 150 * s, cy + 160 * s, 42 * s)):
            off = 0 if row % 2 == 0 else 24 * s
            for xx in np.arange(-190, 60, 48):
                x0 = X(xx) + sg * off
                ctx.new_path(); ctx.arc(x0, yy, 24 * s, 0, math.pi)
                ctx.set_line_width(LD - 2); ctx.set_source_rgb(0, 0, 0); ctx.stroke()
        # white head area covers scales
        f = E(X(140), cy, 130 * s, 170 * s)
        shape(ctx, f, 0)
    line(ctx, [(X(30), cy - 120 * s), (X(10), cy), (X(30), cy + 120 * s)], LD)
    shape(ctx, E(cx, cy, 200 * s, 135 * s, n=2.1), LW, fill=None, seed=5)
    # side fin
    shape(ctx, E(X(-40), cy + 60 * s, 55 * s, 26 * s, -25 * sg), LD, seed=6)
    eye(ctx, X(115), cy - 30 * s, 22 * s)
    smile(ctx, X(150), cy + 30 * s, 26 * s)


def clownfish(ctx, cx, cy, s=1.0, flip=True):
    sg = -1 if flip else 1
    X = lambda dx: cx + sg * dx * s
    poly_shape(ctx, [(X(-120), cy), (X(-230), cy - 100 * s), (X(-200), cy), (X(-230), cy + 100 * s)], LW, seed=7)
    poly_shape(ctx, [(X(-70), cy - 85 * s), (X(-20), cy - 160 * s), (X(60), cy - 140 * s), (X(70), cy - 80 * s)], LW, seed=8)
    body = shape(ctx, E(cx, cy, 165 * s, 105 * s, n=2.1), seed=9)
    with clip(ctx, body):
        for bx in (-90, 20, 115):
            for o in (-14, 14):
                line(ctx, [(X(bx + o - 10), cy - 120 * s), (X(bx + o + 12), cy), (X(bx + o - 10), cy + 120 * s)], LD - 1)
    shape(ctx, E(X(-25), cy + 50 * s, 45 * s, 22 * s, -25 * sg), LD, seed=10)
    eye(ctx, X(85), cy - 25 * s, 19 * s)
    smile(ctx, X(120), cy + 25 * s, 20 * s)


def jelly(ctx, cx, cy, s=1.0):
    for i, dx in enumerate((-110, -55, 0, 55, 110)):
        pts = [(cx + dx * s, cy + 60 * s)]
        for k in range(1, 6):
            pts.append((cx + dx * s + (20 if k % 2 else -20) * s, cy + 60 * s + k * 55 * s))
        line(ctx, pts, LD + 1)
    dome = U(I(E(cx, cy, 190 * s, 175 * s), HALF(cy + 55 * s, below=False)),
             *[E(cx + dx * s, cy + 55 * s, 34 * s, 26 * s) for dx in (-150, -90, -30, 30, 90, 150)], k=10)
    shape(ctx, dome, seed=12)
    face(ctx, cx, cy - 25 * s, 1.0 * s, 'happy')


def turtle(ctx, cx, cy, s=1.0):
    for (dx, dy, a) in ((-150, 90, 35), (150, 90, -35), (-140, -60, -30), (140, -60, 30)):
        shape(ctx, E(cx + dx * s, cy + dy * s, 85 * s, 42 * s, a), seed=13)
    tube(ctx, [(cx - 180 * s, cy + 40 * s), (cx - 230 * s, cy + 55 * s)], 40 * s, 16 * s, seed=14)
    head = shape(ctx, E(cx + 230 * s, cy - 40 * s, 95 * s, 85 * s), seed=15)
    eye(ctx, cx + 255 * s, cy - 65 * s, 15 * s); smile(ctx, cx + 260 * s, cy - 15 * s, 22 * s)
    rim = shape(ctx, I(E(cx, cy, 210 * s, 160 * s), HALF(cy + 60 * s, below=False)), seed=16)
    shell = shape(ctx, I(E(cx, cy, 185 * s, 140 * s), HALF(cy + 40 * s, below=False)), LW, seed=17)
    with clip(ctx, shell):
        hexes = [(0, -40), (-110, -10), (110, -10), (-55, -120), (55, -120)]
        for hx, hy in hexes:
            poly_shape(ctx, [(cx + hx * s + 48 * s * math.cos(math.radians(60 * k)), cy + hy * s + 44 * s * math.sin(math.radians(60 * k))) for k in range(6)], LD, smooth=1)


def crab(ctx, cx, cy, s=1.0):
    for sg in (-1, 1):
        for i, a in enumerate((20, 40, 60)):
            x0 = cx + sg * 120 * s; y0 = cy + 10 * s + i * 25 * s
            tube(ctx, [(x0, y0), (x0 + sg * 110 * s, y0 + 10 * s - 0), (x0 + sg * 150 * s, y0 + 70 * s)], 28 * s, 14 * s, LD, seed=20 + i)
        # arm + claw
        tube(ctx, [(cx + sg * 110 * s, cy - 40 * s), (cx + sg * 190 * s, cy - 110 * s), (cx + sg * 200 * s, cy - 170 * s)], 34 * s, 28 * s, LD, seed=24)
        claw = D(E(cx + sg * 205 * s, cy - 230 * s, 70 * s, 78 * s), E(cx + sg * 222 * s, cy - 295 * s, 26 * s, 48 * s, sg * 20))
        shape(ctx, claw, LW, seed=25)
        # eye stalks
        line(ctx, [(cx + sg * 45 * s, cy - 90 * s), (cx + sg * 55 * s, cy - 160 * s)], LW)
        ring(ctx, cx + sg * 55 * s, cy - 180 * s, 30 * s, LD)
        eye(ctx, cx + sg * 58 * s, cy - 178 * s, 16 * s)
    shape(ctx, E(cx, cy, 165 * s, 110 * s, n=2.2), seed=26)
    smile(ctx, cx, cy - 5 * s, 34 * s)
    cheeks(ctx, cx - 85 * s, cx + 85 * s, cy - 15 * s, 18 * s)
    for dx in (-60, 0, 60):
        dot(ctx, cx + dx * s, cy + 55 * s, 6 * s)


def seaweed(ctx, x, y, h, lean, s=1.0, seed=0):
    c = [(x, y)]
    for k in range(1, 6):
        c.append((x + (35 if k % 2 else -35) * s + lean * k / 5, y - h * k / 5))
    tube(ctx, c, 55 * s, 14 * s, LW - 2, seed=seed)
    line(ctx, [(p[0] * 0.92 + c[0][0] * 0.08, p[1]) for p in c[1:-1]], LD - 3)


def coral(ctx, x, y, s=1.0):
    for (dx, h, a) in ((-60, 170, -12), (0, 230, 0), (60, 150, 14)):
        bx = x + dx * s; top = (bx + math.sin(math.radians(a)) * h * s, y - h * s)
        tube(ctx, [(bx, y), top], 62 * s, 52 * s, LW - 2, seed=int(h), cap=False)
        shape(ctx, E(top[0], top[1], 30 * s, 16 * s, a), LD)
        shape(ctx, E(top[0], top[1], 16 * s, 7 * s, a), 5, fill='black')


def page(out):
    surf, ctx = new_page()
    ctx.save(); frame_clip(ctx)
    # sand
    # waves at top
    for k, y in enumerate((250, 290)):
        pts = [(x, y + 18 * math.sin(x / 70 + k)) for x in range(80, 1640, 30)]
        line(ctx, pts, LD if k == 0 else LD - 2)
    seaweed(ctx, 190, 1880, 620, 40, 1.1, seed=2); seaweed(ctx, 300, 1930, 420, -30, 0.9, seed=3)
    seaweed(ctx, 1530, 1850, 600, -40, 1.1, seed=4); seaweed(ctx, 1430, 1950, 380, 30, 0.85, seed=5)
    sand = shape(ctx, U(E(400, 2050, 650, 330), E(1350, 2100, 600, 300), E(850, 2250, 900, 300), k=80), LW - 2, seed=1)
    coral(ctx, 1010, 2010, 1.0)
    for (x, y, rx, ry) in ((680, 2040, 70, 34), (760, 2060, 44, 24), (1250, 2060, 60, 28)):
        shape(ctx, E(x, y, rx, ry), LD)
    fish_scales(ctx, 460, 560, 0.95)
    jelly(ctx, 1260, 520, 1.0)
    octopus(ctx, 850, 1090, 1.05)
    clownfish(ctx, 1230, 1560, 1.0)
    crab(ctx, 520, 1640, 0.9)
    turtle(ctx, 1210, 1040, 0.72) if False else None
    rng = random.Random(4)
    avoid = [(460, 560, 290), (1260, 640, 240), (850, 1130, 430), (1230, 1560, 240), (520, 1600, 260), (1010, 1880, 160)]
    for (x, y) in scatter(rng, 26, [(130, 330, 1570, 1750)], avoid, 30):
        bubble(ctx, x, y, rng.choice([14, 18, 24, 30]))
    for (x, y) in ((620, 2000), (900, 2090), (1150, 2000), (480, 2100), (1330, 1990)):
        line(ctx, [(x, y), (x + 22, y - 6)], 6)
    ctx.restore()
    frame(ctx)
    surf.write_to_png(out)


if __name__ == "__main__":
    page(sys.argv[1])
