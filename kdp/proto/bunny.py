"""Sample page: bunny hugging a carrot (hand-drawn curves, big head, tilted pose, varied line weights)."""
import math, random, sys
import numpy as np
from crv import *


def carrot(ctx, T):
    # T: carrot transform, local root top near (0,0), leaves up, tip down
    for k, (dx, ang, L_) in enumerate(((-18, -26, 190), (0, 2, 225), (20, 30, 190))):
        o = T((dx, -100))
        L = Xf(o[0], o[1], T.s, ang + math.degrees(T.r))
        blob(ctx, L, [(0, 6), (-30, -50), (-28, -L_ * 0.65), (0, -L_), (28, -L_ * 0.65), (30, -50)], MID + 1, seed=40 + k, n=100)
        stroke(ctx, L, [(0, -20), (2, -L_ * 0.5), (0, -L_ * 0.82)], THIN, (0.1, 0.8))
    body = blob(ctx, T, [(-85, -102), (0, -114), (85, -102), (108, 0), (74, 140), (38, 270), (0, 420), (-38, 270), (-74, 140), (-108, 0)], OUT - 2, seed=41)
    with clip(ctx, body):
        for (a, b, c, d) in ((-112, -30, -30, -14), (30, 20, 112, 4), (-80, 100, -10, 116), (20, 170, 80, 158), (-34, 250, 14, 262), (-8, 330, 22, 340)):
            stroke(ctx, T, [(a, b), ((a + c) / 2, (b + d) / 2 - 8), (c, d)], THIN + 1, (0.15, 0.5))


def bunny_head(ctx, T):
    # ears (behind the head). origin = head center
    blob(ctx, T, [(-85, -90), (-165, -215), (-190, -370), (-150, -500), (-90, -490), (-50, -340), (-20, -190)], OUT, seed=1)
    stroke(ctx, T, [(-105, -150), (-125, -300), (-112, -420)], MID, (0.1, 0.5))
    blob(ctx, T, [(40, -90), (125, -190), (240, -235), (335, -205), (340, -140), (260, -105), (150, -70)], OUT, seed=2)
    stroke(ctx, T, [(130, -135), (225, -165), (290, -165)], MID, (0.1, 0.5))
    # head: cheeks lower and wider
    blob(ctx, T, [(-255, -30), (-235, -140), (-120, -205), (0, -215), (120, -205), (235, -140), (255, -30), (292, 60), (225, 150), (110, 190), (0, 198), (-110, 190), (-225, 150), (-292, 60)], OUT, seed=6)
    # face
    eye2(ctx, T, -112, -5, 40); eye2(ctx, T, 115, -5, 40)
    stroke(ctx, T, [(-170, -80), (-112, -105), (-62, -88)], MID, (0.3, 0.5))
    stroke(ctx, T, [(172, -80), (115, -105), (64, -88)], MID, (0.5, 0.3))
    spot(ctx, T, [(-34, 58), (34, 58), (42, 82), (0, 112), (-42, 82)])
    stroke(ctx, T, [(0, 112), (0, 140)], MID, (0.1, 0.1))
    stroke(ctx, T, [(0, 140), (-30, 168), (-72, 160)], MID, (0.1, 0.5))
    stroke(ctx, T, [(0, 140), (30, 168), (72, 160)], MID, (0.1, 0.5))
    blob(ctx, T, [(-26, 158), (26, 158), (28, 215), (0, 222), (-28, 215)], THIN + 1, seed=7, n=60)  # buck teeth
    line(ctx, [T((0, 160)), T((0, 218))], 4)
    for sg in (-1, 1):
        p = T((sg * 170, 118)); cheeks(ctx, p[0], p[0], p[1], 20 * T.s)
        for dy in (-18, 24):
            stroke(ctx, T, [(sg * 262, 70 + dy * 0.3), (sg * 320, 65 + dy), (sg * 385, 68 + dy * 1.8)], THIN, (0.05, 0.9))


def bunny_body(ctx, T):
    # hind feet: big rounded paws with toe lines, pointing outward
    for flip, sd in ((False, 3), (True, 4)):
        F = Xf(T.x, T.y, T.s, math.degrees(T.r), flip)
        foot = blob(ctx, F, [(-70, 300), (-200, 280), (-340, 325), (-385, 410), (-300, 470), (-130, 470), (-60, 430)], OUT, seed=sd)
        for k, (x, y) in enumerate(((-300, 400), (-245, 420), (-190, 430))):
            stroke(ctx, F, [(x - 38, y - 8), (x - 4, y + 2), (x + 8, y + 28)] if False else [(x - 8, y + 18), (x - 14, y + 62)], MID - 2, (0.05, 0.5))
    # body: soft pear
    blob(ctx, T, [(-215, -190), (-270, -20), (-245, 190), (-120, 335), (0, 360), (120, 335), (245, 190), (270, -20), (215, -190), (100, -250), (-100, -250)], OUT, seed=5)
    stroke(ctx, T, [(-130, 190), (-95, 290), (0, 322), (95, 290), (130, 190)], MID, (0.3, 0.3))


def arm(ctx, T, ctrl, seed):
    limb(ctx, T, ctrl, 112, 84, OUT, seed=seed)
    end = ctrl[-1]
    for k in (-1, 0, 1):
        stroke(ctx, T, [(end[0] + k * 22 - 4, end[1] - 34), (end[0] + k * 22, end[1] - 8)], 5, (0.1, 0.1))


def page(out):
    surf, ctx = new_page()
    ctx.save(); frame_clip(ctx)
    ground(ctx, 1925)
    tilt = -5
    TB = Xf(840, 1490, 0.86, tilt)
    TH = Xf(855, 1050, 1.28, tilt * 1.4)
    bunny_body(ctx, TB)
    bunny_head(ctx, TH)
    # carrot lying across the tummy, leaves up-right
    TC = Xf(1020, 1470, 1.2, 62)
    carrot(ctx, TC)
    arm(ctx, TB, [(-230, -120), (-255, 40), (-170, 135), (-70, 150)], 8)
    arm(ctx, TB, [(230, -120), (262, 20), (195, 80), (120, 70)], 9)
    # fillers: hearts, flowers, sparkles, none in rows
    for (x, y, r, a) in ((250, 500, 48, -15), (1400, 380, 38, 12), (1470, 980, 30, -10), (200, 1180, 32, 18), (1440, 1480, 42, 14)):
        hearts(ctx, x, y, r, a)
    flower(ctx, 300, 1985, 56, 10); flower(ctx, 1330, 1995, 66, 30); flower(ctx, 1570, 1760, 42, 0)
    for (x, y, s) in ((150, 1960, 1.0), (580, 2050, 0.9), (1150, 2060, 1.1), (1560, 2040, 0.8), (130, 1740, 0.8)):
        grass(ctx, x, y, s)
    for (x, y, r) in ((470, 300, 26), (1150, 240, 20), (1290, 560, 18), (330, 800, 16), (1520, 1250, 22), (120, 1480, 20)):
        sparkle(ctx, x, y, r)
    for (x, y) in ((600, 190), (1500, 690), (250, 960), (1520, 1640), (300, 1700)):
        dot(ctx, x, y, 8)
    ctx.restore(); frame(ctx)
    surf.write_to_png(out)


if __name__ == "__main__":
    page(sys.argv[1])
