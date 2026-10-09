"""Sample page: Smiling solar system with labels."""
import math, random, sys
from ink import *
from space import planet_ring


LABELS = []


def labelled(ctx, name, x, y, r):
    outline_text(ctx, name, x, y + r + 88, 68, w=5)
    LABELS.append((x, y + r + 65, 130))


def sun(ctx, cx, cy, r):
    poly_shape(ctx, star_pts(cx, cy, r * 1.55, 0, 0.68, 14), LW, seed=1, smooth=1)
    shape(ctx, E(cx, cy, r), LW, seed=2)
    face(ctx, cx, cy - 10, r / 115, 'happy', 'open')


def shooting_star(ctx, x, y, r, ang=200):
    a = math.radians(ang)
    for k, off in enumerate((-0.45, 0, 0.45)):
        ox, oy = -math.sin(a) * off * r, math.cos(a) * off * r
        L = r * (2.6 if off == 0 else 1.9)
        line(ctx, [(x + ox + math.cos(a) * r * 0.9, y + oy + math.sin(a) * r * 0.9),
                   (x + ox + math.cos(a) * (r * 0.9 + L), y + oy + math.sin(a) * (r * 0.9 + L))], LD)
    star(ctx, x, y, r, 10, LD + 1)


def page(out):
    surf, ctx = new_page()
    ctx.save(); frame_clip(ctx)
    outline_text(ctx, "SOLAR SYSTEM", 850, 300, 150, w=10)
    sun(ctx, 400, 640, 165)
    # Venus
    v = shape(ctx, E(1010, 560, 110), seed=3); face(ctx, 1010, 550, 0.95, 'dots'); labelled(ctx, "VENUS", 1010, 560, 110)
    # Mars with craters
    m = shape(ctx, E(1390, 720, 105), seed=4)
    for (dx, dy, rr) in ((-50, -62, 14), (50, -68, 10), (30, 72, 13), (-35, 75, 9)):
        ring(ctx, 1390 + dx, 720 + dy, rr, 5)
    face(ctx, 1390, 710, 0.85, 'happy'); labelled(ctx, "MARS", 1390, 720, 105)
    # Mercury
    shape(ctx, E(330, 1100, 88), seed=5); face(ctx, 330, 1090, 0.75, 'happy'); labelled(ctx, "MERCURY", 330, 1100, 88)
    # Earth
    ex, ey, er = 820, 1060, 160
    body = shape(ctx, E(ex, ey, er), seed=6)
    with clip(ctx, body):
        shape(ctx, U(E(ex - 120, ey - 95, 70, 45, 30), E(ex - 140, ey - 20, 35, 55), k=25), LD, seed=7)
        shape(ctx, U(E(ex + 115, ey - 100, 60, 40, -20), E(ex + 150, ey - 40, 30, 40), k=25), LD, seed=8)
        shape(ctx, U(E(ex - 90, ey + 120, 60, 40, -15), E(ex + 40, ey + 150, 70, 30), k=25), LD, seed=9)
    face(ctx, ex, ey - 5, 1.1, 'dots', 'open'); labelled(ctx, "EARTH", ex, ey, er)
    # Saturn
    planet_ring(ctx, 1320, 1150, 115, stripes=False, seed=10)
    face(ctx, 1320, 1120, 0.8, 'happy'); labelled(ctx, "SATURN", 1320, 1150, 115)
    # Jupiter
    jx, jy, jr = 400, 1530, 160
    body = shape(ctx, E(jx, jy, jr), seed=11)
    with clip(ctx, body):
        for k in (-0.75, -0.4, 0.45, 0.78):
            line(ctx, [(jx - jr, jy + k * jr), (jx - jr * 0.3, jy + k * jr - 14), (jx + jr * 0.4, jy + k * jr + 10), (jx + jr, jy + k * jr - 6)], LD)
        shape(ctx, E(jx + 55, jy + 112, 34, 18), LD, seed=12)
    face(ctx, jx, jy - 5, 1.0, 'dots'); labelled(ctx, "JUPITER", jx, jy, jr)
    # Uranus + Neptune
    shape(ctx, E(870, 1580, 115), seed=13); face(ctx, 870, 1570, 0.9, 'happy', 'open'); labelled(ctx, "URANUS", 870, 1580, 115)
    nb = shape(ctx, E(1310, 1600, 115), seed=14)
    with clip(ctx, nb):
        for k in (-0.5, 0.55):
            line(ctx, [(1195, 1600 + k * 115), (1310, 1600 + k * 115 + 12), (1425, 1600 + k * 115 - 4)], LD - 1)
    face(ctx, 1310, 1590, 0.9, 'dots'); labelled(ctx, "NEPTUNE", 1310, 1600, 115)
    shooting_star(ctx, 1450, 1990, 48, 205)
    shooting_star(ctx, 680, 1990, 40, 200)
    rng = random.Random(5)
    avoid = [(400, 640, 270), (1010, 600, 160), (1390, 760, 160), (330, 1140, 150), (820, 1110, 220), (1320, 1170, 230),
             (400, 1580, 220), (870, 1630, 180), (1310, 1650, 180), (1450, 1990, 120), (680, 1990, 110), (850, 270, 110)]
    avoid += [(x, 270, 90) for x in range(250, 1500, 90)]
    avoid += LABELS
    boxes = [(120, 150, 1580, 2070)]
    for (x, y) in scatter(rng, 18, boxes, avoid, 34):
        star(ctx, x, y, rng.choice([24, 30, 36]), rng.uniform(-15, 15))
    for (x, y) in scatter(random.Random(8), 14, boxes, avoid, 20):
        sparkle(ctx, x, y, rng.choice([14, 18]))
    for (x, y) in scatter(random.Random(2), 14, boxes, avoid, 14):
        dot(ctx, x, y, rng.choice([5, 7]))
    ctx.restore(); frame(ctx)
    surf.write_to_png(out)


if __name__ == "__main__":
    page(sys.argv[1])
