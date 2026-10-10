"""Sample page: lion cub reaching for a butterfly (hand-drawn curves, spiky mane, tilted pose)."""
import math, random, sys
import numpy as np
from crv import *


def mane(ctx, T, seed=3):
    """Ring of leaf-shaped lobes around the head: clean, scalloped, a bit uneven."""
    rng = random.Random(seed); n = 13
    s = T.s
    fs = [E(*T((0, -5)), 292 * s, 285 * s)]
    for i in range(n):
        if i in (2, n - 2):      # leave room for the ears
            continue
        a = -math.pi / 2 + i * 2 * math.pi / n + rng.uniform(-0.02, 0.02)
        r = 300 + rng.uniform(-8, 22)
        c = T((math.cos(a) * r, math.sin(a) * r * 0.97 - 5))
        fs.append(E(c[0], c[1], 92 * s, 62 * s, math.degrees(a) + math.degrees(T.r), 2.0))
    shape(ctx, U(*fs, k=10 * s), OUT * s ** 0.5, 'white', seed=seed)
    for ang in (-150, -110, -70, -30, 20, 160, 200):
        a = math.radians(ang)
        stroke(ctx, T, [(math.cos(a) * 222, math.sin(a) * 222), (math.cos(a + 0.05) * 268, math.sin(a + 0.05) * 268), (math.cos(a) * 310, math.sin(a) * 310)], THIN, (0.1, 0.8))


def lion_head(ctx, T):
    mane(ctx, T)
    for sg in (-1, 1):   # round ears on top of mane
        blob(ctx, T, [(sg * 150, -205), (sg * 215, -285), (sg * 300, -250), (sg * 305, -170), (sg * 235, -125)], OUT, seed=11 + sg, n=100)
        blob(ctx, T, [(sg * 195, -200), (sg * 235, -243), (sg * 270, -222), (sg * 270, -185), (sg * 232, -168)], THIN + 1, seed=15 + sg, n=60)
    blob(ctx, T, [(-215, -50), (-190, -165), (-90, -225), (0, -235), (90, -225), (190, -165), (215, -50), (240, 45), (170, 140), (80, 185), (0, 195), (-80, 185), (-170, 140), (-240, 45)], OUT, seed=12)
    for dx in (-30, 0, 32):   # forehead tuft
        stroke(ctx, T, [(dx, -215), (dx * 1.1 + 4, -170), (dx * 1.3 + 10, -140)], MID, (0.1, 0.7))
    eye2(ctx, T, -90, -45, 38); eye2(ctx, T, 92, -45, 38)
    stroke(ctx, T, [(-150, -112), (-92, -135), (-40, -118)], MID, (0.3, 0.5))
    stroke(ctx, T, [(152, -112), (94, -135), (42, -118)], MID, (0.5, 0.3))
    blob(ctx, T, [(-135, 75), (-75, 45), (0, 62), (75, 45), (135, 75), (130, 140), (65, 185), (0, 190), (-65, 185), (-130, 140)], MID + 2, seed=13)
    spot(ctx, T, [(-45, 45), (45, 45), (52, 62), (0, 100), (-52, 62)])
    stroke(ctx, T, [(0, 100), (0, 128)], MID, (0.1, 0.1))
    stroke(ctx, T, [(0, 128), (-34, 160), (-82, 148)], MID, (0.1, 0.5))
    stroke(ctx, T, [(0, 128), (34, 160), (82, 148)], MID, (0.1, 0.5))
    for sg in (-1, 1):
        for k, (x, y) in enumerate(((72, 98), (104, 112), (80, 128))):
            p = T((sg * x, y)); dot(ctx, p[0], p[1], 4.5 * T.s)
        p = T((sg * 175, 85)); cheeks(ctx, p[0], p[0], p[1], 20 * T.s)


def lion_body(ctx, T):
    # tail with tuft (behind body)
    limb(ctx, T, [(170, 150), (320, 175), (410, 110), (400, 30)], 50, 30, OUT, seed=20)
    blob(ctx, T, [(398, 40), (345, -30), (355, -105), (405, -160), (455, -110), (462, -30)], OUT, seed=21, n=140)
    for dx in (-30, 6, 34):
        stroke(ctx, T, [(402 + dx, -20), (402 + dx * 1.2, -80), (402 + dx * 1.3, -122)], THIN, (0.1, 0.7))
    # back paws
    for flip, sd in ((False, 22), (True, 23)):
        F = Xf(T.x, T.y, T.s, math.degrees(T.r), flip)
        blob(ctx, F, [(-55, 215), (-185, 205), (-255, 255), (-250, 325), (-140, 350), (-50, 325)], OUT, seed=sd)
        for x in (-215, -170, -125):
            stroke(ctx, F, [(x, 288), (x + 4, 335)], MID - 2, (0.05, 0.4))
    blob(ctx, T, [(-170, -130), (-205, 20), (-178, 175), (-85, 268), (85, 268), (178, 175), (205, 20), (170, -130), (80, -190), (-80, -190)], OUT, seed=24)
    stroke(ctx, T, [(-95, 10), (-110, 110), (-70, 200), (0, 232), (70, 200), (110, 110), (95, 10)], MID, (0.2, 0.2))


def paw(ctx, T, ex, ey, flip=False, seed=0):
    sg = -1 if flip else 1
    blob(ctx, T, [(ex - 20 * sg, ey - 48), (ex + 36 * sg, ey - 50), (ex + 62 * sg, ey - 8), (ex + 50 * sg, ey + 38), (ex + 5 * sg, ey + 54), (ex - 36 * sg, ey + 28), (ex - 38 * sg, ey - 16)], OUT - 2, seed=seed, n=120)
    for k in (-1, 0):
        stroke(ctx, T, [(ex + 14 * sg + k * 24 * sg, ey - 38), (ex + 20 * sg + k * 24 * sg, ey - 4)], 5, (0.1, 0.3))


def lion_arms(ctx, T):
    """Both arms hang down the sides, starting under the mane; paws rest near the hips."""
    arm(ctx, T, [(-185, -120), (-225, -10), (-218, 95), (-208, 150)], 104, 92, seed=25)
    arm(ctx, T, [(185, -120), (225, -10), (218, 95), (208, 150)], 104, 92, seed=26)


def butterfly(ctx, T):
    for flip in (False, True):
        W_ = Xf(T.x, T.y, T.s, math.degrees(T.r), flip)
        blob(ctx, W_, [(-8, -10), (-60, -135), (-175, -190), (-255, -120), (-215, -15), (-90, 22)], OUT - 2, seed=30 + flip)
        blob(ctx, W_, [(-8, 10), (-85, 42), (-175, 95), (-150, 185), (-65, 165), (-10, 80)], OUT - 2, seed=32 + flip)
        for (x, y, r) in ((-150, -105, 30), (-100, -40, 14)):
            p = W_((x, y)); ring(ctx, p[0], p[1], r * T.s, 6)
        p = W_((-95, 118)); ring(ctx, p[0], p[1], 22 * T.s, 6)
        stroke(ctx, W_, [(-20, -5), (-110, -70), (-190, -80)], THIN, (0.1, 0.5))
    limb(ctx, T, [(0, -70), (0, 20), (0, 130)], 38, 22, OUT - 2, seed=34)
    for sg in (-1, 1):
        stroke(ctx, T, [(sg * 6, -70), (sg * 40, -140), (sg * 85, -190)], MID - 1, (0.05, 0.5))
        p = T((sg * 92, -198)); dot(ctx, p[0], p[1], 9 * T.s)
    p = T((0, -62)); dot(ctx, p[0], p[1], 3)


def page(out):
    surf, ctx = new_page()
    ctx.save(); frame_clip(ctx)
    G = 1930
    ground(ctx, G)
    tilt = 3
    TB = Xf(975, 1528, 1.12, tilt)
    TH = Xf(990, 1015, 1.34, tilt)
    lion_body(ctx, TB)
    lion_arms(ctx, TB)
    lion_head(ctx, TH)          # mane drawn last: it covers the shoulders, so head and body are one piece
    butterfly(ctx, Xf(300, 560, 0.66, -20))
    sparkle(ctx, 560, 420, 20); sparkle(ctx, 190, 760, 16); sparkle(ctx, 300, 1380, 14)
    for (x, y, r, a) in ((1370, 350, 38, 12), (1530, 700, 28, -10), (190, 1560, 32, 18), (1545, 1480, 30, 14)):
        hearts(ctx, x, y, r, a)
    gy = lambda x: ground_y(G, x)
    flower_stem(ctx, 260, gy(260), 130, 52, 12, 10); flower_stem(ctx, 470, gy(470), 165, 58, -14, 30)
    for x, s_ in ((140, 1.0), (640, 0.8), (1330, 0.9), (1500, 0.9), (1590, 0.8)):
        tuft(ctx, x, gy(x), s_)
    for (x, y, r) in ((1150, 250, 24), (1250, 430, 20), (230, 1480, 22), (170, 840, 16), (700, 200, 18)):
        sparkle(ctx, x, y, r)
    for (x, y) in ((560, 150), (1480, 640), (150, 1020), (1530, 1650), (320, 1750)):
        dot(ctx, x, y, 8)
    ctx.restore(); frame(ctx)
    surf.write_to_png(out)


if __name__ == "__main__":
    page(sys.argv[1])
