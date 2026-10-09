"""Sample page: Astronaut on the moon."""
import math, random, sys
import numpy as np
from ink import *


def planet_ring(ctx, cx, cy, r, tilt=-18, stripes=True, seed=0):
    ringf = D(E(cx, cy, r * 1.75, r * 0.5, tilt), E(cx, cy, r * 1.35, r * 0.3, tilt))
    shape(ctx, ringf, LD + 1, seed=seed)                      # back of ring
    body = shape(ctx, E(cx, cy, r), LW - 1, seed=seed + 1)
    if stripes:
        with clip(ctx, body):
            for k in (-0.45, 0.05, 0.5):
                line(ctx, [(cx - r, cy + k * r - 10), (cx, cy + k * r + 12), (cx + r, cy + k * r - 6)], LD - 1)
    # front half of the ring (below the planet's middle) drawn over the planet
    front = I(ringf, HALF(cy + 0, below=True))
    a = math.radians(tilt)
    front = I(ringf, lambda X, Y: -((X - cx) * -math.sin(a) + (Y - cy) * math.cos(a)))
    front.bb = ringf.bb
    shape(ctx, front, LD + 1, seed=seed + 2)


def earth(ctx, cx, cy, r, seed=0):
    body = shape(ctx, E(cx, cy, r), LW - 1, seed=seed)
    with clip(ctx, body):
        shape(ctx, U(E(cx - 0.45 * r, cy - 0.45 * r, 0.35 * r, 0.22 * r, 25), E(cx - 0.25 * r, cy - 0.15 * r, 0.2 * r, 0.25 * r, -20),
                     E(cx - 0.35 * r, cy + 0.2 * r, 0.12 * r, 0.3 * r, 15), k=25), LD, seed=seed + 1)
        shape(ctx, U(E(cx + 0.35 * r, cy - 0.5 * r, 0.3 * r, 0.16 * r, -15), E(cx + 0.5 * r, cy - 0.2 * r, 0.18 * r, 0.2 * r),
                     E(cx + 0.3 * r, cy + 0.25 * r, 0.16 * r, 0.32 * r, 25), k=25), LD, seed=seed + 2)
        shape(ctx, E(cx + 0.05 * r, cy + 0.7 * r, 0.3 * r, 0.12 * r), LD, seed=seed + 3)



def astronaut(ctx, cx, cy, s=1.0):
    """Sitting astronaut; (cx, cy) = seat point."""
    S = lambda x, y: (cx + x * s, cy + y * s)
    # backpack
    shape(ctx, RR(*S(0, -150), 250 * s, 230 * s, 40 * s), seed=30)
    # legs dangling forward/down: thighs toward viewer then shins down
    for sg in (-1, 1):
        tube(ctx, [S(sg * 50, -10), S(sg * 68, 50), S(sg * 78, 110)], 96 * s, 88 * s, seed=31)
        boot = shape(ctx, U(RR(*S(sg * 84, 150), 120 * s, 84 * s, 32 * s), E(*S(sg * 104, 176), 82 * s, 44 * s), k=20), seed=32)
        with clip(ctx, boot):
            for k in range(-3, 4):
                line(ctx, [S(sg * 84 + k * 24 - 30, 215), S(sg * 84 + k * 24 + 10, 120)], 5)
        line(ctx, [S(sg * 84 - 58, 116), S(sg * 84 + 58, 116)], LD)
        line(ctx, [S(sg * 74 - 46, 66), S(sg * 74 + 46, 70)], LD)
    # torso
    torso = shape(ctx, RR(*S(0, -110), 230 * s, 230 * s, 70 * s), seed=33)
    panel = shape(ctx, RR(*S(0, -95), 120 * s, 75 * s, 16 * s), LD, seed=34)
    shape(ctx, RR(*S(-25, -95), 40 * s, 36 * s, 8 * s), 5)
    ring(ctx, *S(30, -95), 15 * s, 5)
    line(ctx, [S(-105, -15), S(105, -15)], LD)
    # arms resting on knees
    for sg in (-1, 1):
        tube(ctx, [S(sg * 105, -190), S(sg * 150, -110), S(sg * 120, -30)], 70 * s, 62 * s, seed=35)
        line(ctx, [S(sg * 120 - 32, -70), S(sg * 120 + 34, -60)], LD)
        shape(ctx, E(*S(sg * 112, 5), 42 * s, 38 * s), seed=36)
    # helmet
    for sg in (-1, 1):
        shape(ctx, RR(*S(sg * 168, -330), 46 * s, 90 * s, 20 * s), seed=37)
    helmet = shape(ctx, E(*S(0, -335), 175 * s, 165 * s), seed=38)
    visor = shape(ctx, RR(*S(0, -335), 250 * s, 185 * s, 85 * s), LD + 1, seed=39)
    # face inside visor (kids like a face better than a black visor)
    face(ctx, *S(0, -350), 1.25 * s, 'dots')
    line(ctx, [S(-95, -390), S(-75, -405), S(-55, -410)], 6)
    ring(ctx, *S(-120, -370), 9 * s, 5) if False else None
    # antenna
    line(ctx, [S(60, -495), S(80, -560)], LD)
    dot(ctx, *S(82, -575), 18 * s)


def page(out):
    surf, ctx = new_page()
    ctx.save(); frame_clip(ctx)
    rng = random.Random(7)
    # big crescent moon
    mc, mr = (790, 1180), 600
    ic, ir = (1030, 1010), 500
    moon = shape(ctx, D(E(*mc, mr), E(*ic, ir)), LW + 2, seed=1)
    with clip(ctx, moon):
        for (x, y, r, a) in ((420, 980, 60, 20), (330, 1260, 45, -10), (470, 1530, 70, 30), (640, 1700, 50, 0), (840, 1660, 34, 10), (380, 1120, 24, 0), (560, 1360, 28, 0)):
            shape(ctx, E(x, y, r, r * 0.72, a), LD, seed=int(x))
            line(ctx, [(x - r * 0.6, y + r * 0.15), (x - r * 0.1, y + r * 0.55)], 5)
    # astronaut sitting on the inner edge
    a = math.radians(108)
    seat = (ic[0] + ir * math.cos(a), ic[1] + ir * math.sin(a))
    astronaut(ctx, seat[0] + 10, seat[1] + 10, 1.08)
    # sky friends
    cloud(ctx, 330, 360, 1.15, seed=2)
    cloud(ctx, 1380, 1580, 0.95, seed=3)
    cloud(ctx, 240, 1900, 0.8, seed=4)
    planet_ring(ctx, 1290, 430, 110, seed=5)
    earth(ctx, 1360, 1900, 140, seed=6)
    shape(ctx, E(1460, 1090, 55), LW - 2, seed=8)           # little moon
    for (x, y, r) in ((1440, 1075, 12), (1478, 1110, 9)):
        ring(ctx, x, y, r, 5)
    # stars + sparkles + dots
    avoid = [(330, 340, 210), (1290, 430, 210), (790, 1180, 610), (1380, 1560, 170), (240, 1890, 140), (1360, 1900, 160), (1460, 1090, 70), (820, 1020, 320)]
    boxes = [(130, 140, 1570, 2060)]
    for i, (x, y) in enumerate(scatter(rng, 14, boxes, avoid, 55)):
        star(ctx, x, y, rng.choice([34, 42, 52]), rng.uniform(-15, 15))
    avoid2 = avoid + [(x, y, 50) for (x, y) in []]
    for (x, y) in scatter(random.Random(3), 12, boxes, avoid, 30):
        sparkle(ctx, x, y, rng.choice([18, 24]))
    for (x, y) in scatter(random.Random(9), 16, boxes, avoid, 18):
        dot(ctx, x, y, rng.choice([6, 8, 10]))
    ctx.restore(); frame(ctx)
    surf.write_to_png(out)


if __name__ == "__main__":
    page(sys.argv[1])
