"""Character library. Every character is drawn in a local box about 900 wide x 1000 tall,
centred on (0, 0) with the feet near y = +480, so `with pen.at(x, y, h / 1000)` places a
character of height h. Each function takes (pen, F) where F maps part -> crayon colour name
(used on covers and for colour-by-number keys). Parts that should get a number call
pen.part(key, x, y) with a point inside that region.

CHARACTERS lists every available name with its default colours.
"""
import math

from draw import BLACK, WHITE, col


# ---------------------------------------------------------------- helpers
def outlined_stroke(p, pts, w, fill, smooth=True):
    c = p.c
    for width, rgb in ((w + 2 * p.lw / p.k, BLACK), (w, fill)):
        if smooth and len(pts) > 2:
            p.spline_path(pts, False)
        else:
            c.move_to(*pts[0])
            for q in pts[1:]:
                c.line_to(*q)
        c.set_source_rgb(*rgb)
        c.set_line_width(width)
        c.stroke()


def scallop_ring(p, cx, cy, rx, ry, n, bump, fill):
    """Cloud-like scalloped closed shape (manes, wool)."""
    c = p.c
    pts = []
    for i in range(n):
        a0 = i * 2 * math.pi / n
        pts.append((cx + math.cos(a0) * rx, cy + math.sin(a0) * ry))

    def build():
        c.new_path()
        for (x, y) in pts:
            c.new_sub_path()
            c.arc(x, y, bump, 0, 2 * math.pi)
        c.new_sub_path()
        c.save()
        c.translate(cx, cy)
        c.scale(rx, ry)
        c.arc(0, 0, 1, 0, 2 * math.pi)
        c.restore()
    build()
    c.set_source_rgb(*BLACK)
    c.set_line_width(2 * p.lw / p.k)
    c.stroke_preserve()
    c.fill()
    build()
    c.set_source_rgb(*fill)
    c.fill()


# ---------------------------------------------------------------- chibi critter
def critter(p, F, ears="round", snout="muzzle", tail=None, extras=(), belly=False, eye_r=46):
    f = lambda k, d="white": p.fill_of(F, k, d)
    ex = set(extras)

    # --- tails (behind) ---
    if tail == "curl":
        outlined_stroke(p, [(170, 330), (330, 300), (390, 160), (330, 60), (270, 110)], 46, f("tail", F.get("body", "white")))
        p.part("tail", 385, 170)
    elif tail == "puff":
        p.circ(235, 380, 70, f("tail", "white"))
    elif tail == "pig":
        outlined_stroke(p, [(200, 330), (280, 320), (300, 260), (250, 250), (260, 300), (320, 300)], 18, f("body"))
    elif tail == "bushy":
        p.blob([(160, 360), (330, 330), (440, 180), (420, 40), (350, 120), (250, 260)], f("tail", F.get("body", "white")))
        p.blob([(400, 70), (430, 30), (450, 110), (415, 140)], f("tailtip", "white"))
        p.part("tail", 330, 230)
    elif tail == "striped":
        p.blob([(160, 360), (330, 330), (440, 180), (420, 40), (350, 120), (250, 260)], f("tail", F.get("body", "white")))
        for (a, b) in [((300, 290), (380, 250)), ((360, 200), (430, 160)), ((385, 110), (440, 90))]:
            p.line([a, b], lw=p.lw * 2.2)
        p.part("tail", 300, 250)
    elif tail == "thin":
        outlined_stroke(p, [(190, 380), (340, 400), (400, 300), (450, 230)], 16, f("body"))
    elif tail == "tuft":
        outlined_stroke(p, [(190, 380), (330, 380), (380, 260)], 20, f("body"))
        p.blob([(370, 270), (330, 210), (390, 150), (430, 220)], f("mane", "orange"))
    elif tail == "short":
        p.ell(240, 300, 40, 75, f("body"), rot=.6)
    elif tail == "dino":
        p.blob([(150, 240), (330, 300), (460, 380), (330, 440), (170, 430)], f("body"))
        p.part("body", 320, 370)
    elif tail == "dragon":
        outlined_stroke(p, [(150, 380), (320, 420), (410, 340), (430, 240)], 60, f("body"))
        p.poly([(390, 250), (430, 160), (480, 250)], f("spike", "yellow"))

    # --- back extras ---
    if "wings" in ex:
        for sx in (-1, 1):
            p.poly([(sx * 120, 140), (sx * 330, -60), (sx * 360, 40), (sx * 440, 50), (sx * 400, 150), (sx * 450, 200), (sx * 220, 260)], f("wing", "purple"))
        p.part("wing", 320, 70)
    if "quills" in ex:
        pts = []
        n = 26
        for i in range(n):
            a = 2 * math.pi * i / n
            r = 1.0 if i % 2 == 0 else .78
            pts.append((math.cos(a) * 400 * r, -150 + math.sin(a) * 370 * r))
        p.poly(pts, f("quill", "brown"))
        p.part("quill", 0, -470)
    if "mane" in ex:
        scallop_ring(p, 0, -180, 330, 300, 16, 75, f("mane", "orange"))
        p.part("mane", -330, -40)
    if "wool" in ex:
        scallop_ring(p, 0, 270, 220, 170, 12, 70, f("wool", "white"))
    if "spikes" in ex:
        for i, (x, y, a) in enumerate([(0, -450, 0), (-150, -420, -.35), (150, -420, .35), (250, -330, .7), (-250, -330, -.7)]):
            with p.at(x, y, 1, rot=a):
                p.poly([(-55, 30), (0, -80), (55, 30)], f("spike", "yellow"))
        p.part("spike", 0, -470)
    if "unicorn_mane" in ex:
        for i, (x, y, rx, ry, r) in enumerate([(-250, -330, 95, 70, -.6), (-310, -220, 80, 70, -.3), (-320, -100, 70, 75, 0), (-290, 20, 70, 60, .3)]):
            p.ell(x, y, rx, ry, f("mane", "purple"), rot=r)
        p.part("mane", -320, -150)

    # --- ears behind head ---
    if ears == "round":
        for sx in (-1, 1):
            p.circ(sx * 215, -385, 88, f("ear", F.get("body", "white")))
            p.circ(sx * 215, -385, 48, f("inner", "lightpink"))
        p.part("inner", 215, -385)
    elif ears == "pointy":
        for sx in (-1, 1):
            p.blob([(sx * 100, -390), (sx * 235, -540), (sx * 290, -300)], f("ear", F.get("body", "white")))
            p.blob([(sx * 150, -390), (sx * 232, -480), (sx * 255, -340)], f("inner", "lightpink"))
        p.part("inner", 215, -400)
    elif ears == "long":
        for sx in (-1, 1):
            p.ell(sx * 115, -560, 72, 200, f("ear", F.get("body", "white")), rot=sx * .12)
            p.ell(sx * 115, -545, 36, 140, f("inner", "lightpink"), rot=sx * .12)
        p.part("inner", 115, -560)
    elif ears == "side":
        for sx in (-1, 1):
            p.ell(sx * 315, -260, 100, 50, f("ear", F.get("body", "white")), rot=sx * .45)
            p.ell(sx * 315, -260, 55, 25, f("inner", "lightpink"), rot=sx * .45)
    elif ears == "big":
        for sx in (-1, 1):
            p.ell(sx * 320, -170, 170, 215, f("ear", F.get("body", "white")))
            p.ell(sx * 330, -170, 105, 145, f("inner", "lightpink"))
        p.part("inner", 340, -170)
    elif ears == "mouse":
        for sx in (-1, 1):
            p.circ(sx * 250, -370, 135, f("ear", F.get("body", "white")))
            p.circ(sx * 250, -370, 82, f("inner", "lightpink"))
        p.part("inner", 255, -370)
    elif ears == "tiny":
        for sx in (-1, 1):
            p.circ(sx * 200, -400, 48, f("ear", F.get("body", "white")))
    elif ears == "fluffy":
        for sx in (-1, 1):
            scallop_ring(p, sx * 290, -330, 95, 95, 9, 38, f("ear", F.get("body", "white")))
            p.circ(sx * 290, -330, 55, f("inner", "white"))
    elif ears == "monkey":
        for sx in (-1, 1):
            p.circ(sx * 315, -170, 85, f("ear", F.get("body", "white")))
            p.circ(sx * 315, -170, 48, f("inner", "tan"))

    if "horns" in ex:
        for sx in (-1, 1):
            p.blob([(sx * 95, -400), (sx * 140, -560), (sx * 185, -390)], f("horn", "tan"))
    if "antlers" in ex:
        for sx in (-1, 1):
            outlined_stroke(p, [(sx * 130, -390), (sx * 170, -520), (sx * 250, -620)], 34, f("antler", "tan"))
            outlined_stroke(p, [(sx * 172, -515), (sx * 270, -540)], 30, f("antler", "tan"), smooth=False)
            outlined_stroke(p, [(sx * 155, -470), (sx * 90, -560)], 30, f("antler", "tan"), smooth=False)
        p.part("antler", 210, -580)

    # --- feet, body, arms ---
    for sx in (-1, 1):
        p.ell(sx * 115, 455, 95, 50, f("feet", F.get("body", "white")))
    if "wool" not in ex:
        p.ell(0, 270, 225, 200, f("body"))
    else:
        p.ell(0, 270, 200, 165, f("wool", "white"))
    if belly:
        p.ell(0, 300, 130, 125, f("belly", "white"))
        p.part("belly", 0, 300)
    elif "wool" not in ex:
        p.part("body", 0, 260)
    if "spots" in ex:
        p.ell(-130, 230, 50, 38, f("spot", "darkbrown"), rot=.4)
        p.ell(120, 330, 55, 42, f("spot", "darkbrown"), rot=-.3)
    if "stripes" in ex:
        for y in (180, 260, 340):
            p.arc(0, y - 300, 300, math.radians(60), math.radians(120), lw=p.lw * 2)
    for sx in (-1, 1):
        p.ell(sx * 205, 250, 62, 105, f("arm", F.get("body", "white")), rot=-sx * .45)
    p.part("arm", -205, 250)
    p.part("feet", 115, 460)
    if "panda" in ex:
        pass

    # --- head ---
    if "wool" in ex:
        scallop_ring(p, 0, -200, 300, 250, 14, 72, f("wool", "white"))
        p.part("wool", 0, -440)
        p.ell(0, -160, 210, 200, f("body", "white"))
        p.part("body", 0, -290)
    else:
        p.ell(0, -180, 300, 265, f("body"))
        p.part("body", 0, -360)
    if "heartface" in ex:
        p.blob([(0, -260), (-120, -320), (-230, -200), (-170, -10), (0, 30), (170, -10), (230, -200), (120, -320)], f("face", "tan"))
    if "mask" in ex:
        p.blob([(-270, -200), (-140, -250), (0, -190), (140, -250), (270, -200), (220, -110), (0, -130), (-220, -110)], f("mask", "darkbrown"))
    if "patches" in ex:
        for sx in (-1, 1):
            p.ell(sx * 120, -165, 85, 100, f("patch", "black"), rot=-sx * .5)
    if "spots" in ex:
        p.ell(-150, -300, 75, 60, f("spot", "darkbrown"), rot=.3)
    if "tuft" in ex:
        for dx, rot in ((-50, -.4), (0, 0), (50, .4)):
            p.ell(dx, -455, 26, 60, f("body"), rot=rot)
    if "unicorn_horn" in ex:
        p.poly([(-55, -420), (0, -640), (55, -420)], f("horn", "yellow"))
        p.line([(-38, -470), (30, -495)], lw=p.lw * .8)
        p.line([(-25, -530), (20, -548)], lw=p.lw * .8)
        p.part("horn", 0, -470)
    if ears == "floppy":
        for sx in (-1, 1):
            p.ell(sx * 290, -170, 78, 165, f("ear", "brown"), rot=sx * .35)
        p.part("ear", 300, -150)
    if "eyespot" in ex:
        p.ell(-120, -175, 90, 85, f("spot", "brown"))

    # --- face ---
    if "frog_eyes" in ex:
        for sx in (-1, 1):
            p.circ(sx * 140, -390, 105, f("body"))
            p.eye(sx * 140, -390, 62)
    else:
        for sx in (-1, 1):
            p.eye(sx * 115, -170, eye_r)
    p.cheeks(195, -70, 42, F)

    if snout == "muzzle":
        p.ell(0, -55, 120, 85, f("snout", "white"))
        p.ell(0, -90, 38, 26, BLACK, stroke=False)
        p.arc(-30, -55, 30, math.radians(10), math.radians(170))
        p.arc(30, -55, 30, math.radians(10), math.radians(170))
        p.part("snout", -75, -40)
    elif snout == "small":
        p.poly([(-24, -85), (24, -85), (0, -60)], f("nose", "pink"), lw=p.lw * .7)
        p.arc(-24, -55, 24, math.radians(10), math.radians(170))
        p.arc(24, -55, 24, math.radians(10), math.radians(170))
        if "teeth" in ex:
            p.rrect(-26, -38, 52, 42, 8, WHITE, lw=p.lw * .7)
            p.line([(0, -38), (0, 4)], lw=p.lw * .6)
    elif snout == "pig":
        p.ell(0, -55, 105, 75, f("snout", "pink"))
        p.ell(-35, -55, 15, 24, BLACK, stroke=False)
        p.ell(35, -55, 15, 24, BLACK, stroke=False)
        p.smile(0, 50, 90)
        p.part("snout", 0, -10)
    elif snout == "big":
        p.ell(0, -30, 170, 105, f("snout", "pink"))
        p.ell(-55, -45, 18, 26, BLACK, stroke=False)
        p.ell(55, -45, 18, 26, BLACK, stroke=False)
        p.smile(0, 35, 90)
        p.part("snout", 0, 25)
    elif snout == "boxy":
        p.rrect(-160, -130, 320, 175, 80, f("snout", "tan"))
        p.ell(-55, -80, 16, 22, BLACK, stroke=False)
        p.ell(55, -80, 16, 22, BLACK, stroke=False)
        p.smile(0, 0, 90)
        p.part("snout", -110, -30)
    elif snout == "trunk":
        outlined_stroke(p, [(0, -110), (10, -10), (-20, 80), (40, 150), (100, 120)], 70, f("body"))
        p.smile(-130, -10, 70)
        p.smile(130, -10, 70)
    elif snout == "nose":
        p.ell(0, -80, 70, 55, f("nose", "black") if p.colour else BLACK, stroke=not p.colour)
        p.smile(0, 15, 90)
    elif snout == "wide":
        p.arc(0, -220, 230, math.radians(55), math.radians(125), lw=p.lw * 1.2)
    else:
        p.dot(0, -80, 18)
        p.smile(0, -20, 80)
    if "rednose" in ex:
        p.circ(0, -95, 42, f("nose", "red"))
    if "whiskers" in ex:
        for sx in (-1, 1):
            p.line([(sx * 150, -60), (sx * 280, -90)], lw=p.lw * .7)
            p.line([(sx * 150, -35), (sx * 285, -30)], lw=p.lw * .7)


def _crit(**kw):
    return lambda p, F: critter(p, F, **kw)


# ---------------------------------------------------------------- birds
def chick(p, F):
    f = lambda k, d="white": p.fill_of(F, k, d)
    for x in (-95, 75):
        p.line([(x, 250), (x, 330)], lw=p.lw * 1.2)
        p.poly([(x - 55, 375), (x, 320), (x + 55, 375)], f("feet", "orange"))
    for dx, rot in ((-55, -.45), (0, 0), (55, .45)):
        p.ell(dx, -300, 30, 70, f("body", "yellow"), rot=rot)
    p.ell(0, 0, 310, 290, f("body", "yellow"))
    p.part("body", 0, -170)
    for sx in (-1, 1):
        p.ell(sx * 255, 40, 85, 135, f("wing", "orange"), rot=-sx * .3)
    p.part("wing", 255, 50)
    p.cheeks(165, 20, 42, F)
    p.eye(-100, -90, 46)
    p.eye(100, -90, 46)
    p.poly([(-62, -10), (62, -10), (0, 78)], f("beak", "orange"))
    p.part("body", 0, 170)


def duck(p, F):
    f = lambda k, d="white": p.fill_of(F, k, d)
    for x in (-95, 75):
        p.line([(x, 250), (x, 330)], lw=p.lw * 1.2)
        p.poly([(x - 60, 380), (x, 320), (x + 60, 380)], f("feet", "orange"))
    p.ell(0, 120, 300, 230, f("body", "white"))
    p.part("body", -60, 220)
    p.ell(230, 140, 110, 75, f("wing", "white"), rot=-.4)
    p.ell(0, -220, 220, 205, f("body", "white"))
    p.part("body", 0, -350)
    p.blob([(-110, -150), (110, -150), (130, -100), (0, -60), (-130, -100)], f("beak", "orange"))
    p.part("beak", 0, -110)
    p.eye(-90, -240, 40)
    p.eye(90, -240, 40)
    p.cheeks(150, -170, 34, F)


def owl(p, F):
    f = lambda k, d="white": p.fill_of(F, k, d)
    for sx in (-1, 1):
        p.poly([(sx * 110, -360), (sx * 250, -470), (sx * 270, -300)], f("body", "brown"))
    p.blob([(0, -390), (260, -330), (330, -60), (300, 260), (170, 440), (-170, 440), (-300, 260), (-330, -60), (-260, -330)], f("body", "brown"))
    p.part("body", 0, -330)
    p.ell(0, 220, 190, 210, f("belly", "tan"))
    for (x, y) in [(-70, 130), (70, 130), (0, 210), (-90, 290), (90, 290), (0, 370)]:
        p.arc(x, y, 34, math.radians(20), math.radians(160), lw=p.lw * .8)
    p.part("belly", -10, 280)
    for sx in (-1, 1):
        p.ell(sx * 300, 140, 75, 180, f("wing", "darkbrown"), rot=-sx * .15)
        p.circ(sx * 120, -150, 120, f("eyering", "white"))
        p.eye(sx * 120, -150, 62)
    p.part("wing", 300, 150)
    p.poly([(-40, -50), (40, -50), (0, 30)], f("beak", "orange"))
    for x in (-80, 80):
        for dx in (-30, 0, 30):
            p.ell(x + dx, 445, 18, 34, f("feet", "orange"))


def penguin(p, F):
    f = lambda k, d="white": p.fill_of(F, k, d)
    for sx in (-1, 1):
        p.ell(sx * 110, 460, 100, 45, f("feet", "orange"))
    p.blob([(0, -470), (240, -360), (320, 0), (290, 330), (160, 450), (-160, 450), (-290, 330), (-320, 0), (-240, -360)], f("body", "black"))
    p.part("body", 0, -390)
    p.blob([(0, -300), (180, -250), (210, 50), (190, 300), (0, 420), (-190, 300), (-210, 50), (-180, -250)], f("belly", "white"))
    p.part("belly", 0, 200)
    for sx in (-1, 1):
        p.ell(sx * 300, 120, 65, 190, f("body", "black"), rot=-sx * .3)
        p.eye(sx * 85, -170, 44)
    p.cheeks(150, -90, 36, F)
    p.poly([(-55, -100), (55, -100), (0, -30)], f("beak", "orange"))


# ---------------------------------------------------------------- sea
def fish(p, F):
    f = lambda k, d="white": p.fill_of(F, k, d)
    p.blob([(250, 0), (430, -200), (440, 0), (430, 200)], f("fin", "yellow"))
    p.blob([(-120, -230), (60, -380), (160, -230)], f("fin", "yellow"))
    p.blob([(-400, 0), (-280, -230), (0, -280), (260, -150), (300, 0), (260, 150), (0, 280), (-280, 230)], f("body", "orange"))
    p.part("body", -60, 160)
    c = p.c
    c.save()
    p.spline_path([(-400, 0), (-280, -230), (0, -280), (260, -150), (300, 0), (260, 150), (0, 280), (-280, 230)], True)
    c.clip()
    for x in (0, 150):
        p.rrect(x - 30, -300, 60, 600, 0, f("stripe", "white"))
    c.restore()
    p.ell(80, 120, 70, 40, f("fin", "yellow"), rot=-.6)
    p.part("fin", 390, 0)
    p.eye(-220, -60, 52)
    p.smile(-300, 90, 70)


def whale(p, F):
    f = lambda k, d="white": p.fill_of(F, k, d)
    for x, h in ((-60, 160), (0, 200), (60, 160)):
        p.curve([(0, -320), (x * 1.5, -320 - h * .6), (x * 3, -320 - h)], lw=p.lw)
    p.blob([(330, -60), (430, -260), (470, -120), (440, -40)], f("body", "blue"))
    p.blob([(-430, 80), (-380, -200), (-120, -330), (200, -250), (380, -20), (320, 200), (40, 330), (-300, 300)], f("body", "blue"))
    p.part("body", 0, -180)
    p.blob([(-400, 120), (-200, 120), (100, 150), (260, 200), (40, 320), (-300, 290)], f("belly", "lightblue"))
    p.part("belly", -200, 220)
    p.eye(-220, -20, 46)
    p.smile(-310, 90, 80)
    p.ell(40, 140, 90, 45, f("fin", "blue"), rot=.6)


def octopus(p, F):
    f = lambda k, d="white": p.fill_of(F, k, d)
    fill = f("body", "purple")
    for i in range(8):
        x0 = -260 + i * 74
        sx = 1 if i % 2 else -1
        outlined_stroke(p, [(x0, 120), (x0 + sx * 40, 260), (x0 - sx * 30, 380), (x0 + sx * 50, 470)], 60, fill)
    p.blob([(0, -470), (270, -380), (330, -80), (270, 160), (0, 200), (-270, 160), (-330, -80), (-270, -380)], fill)
    p.part("body", 0, -330)
    for sx in (-1, 1):
        p.circ(sx * 200, -330, 30, f("spot", "pink"), lw=p.lw * .8)
    p.eye(-110, -110, 50)
    p.eye(110, -110, 50)
    p.cheeks(190, 0, 40, F)
    p.smile(0, 40, 90)


def crab(p, F):
    f = lambda k, d="white": p.fill_of(F, k, d)
    for sx in (-1, 1):
        for i in range(3):
            outlined_stroke(p, [(sx * 200, 120 + i * 60), (sx * 330, 170 + i * 70), (sx * 380, 260 + i * 70)], 32, f("body", "red"))
        outlined_stroke(p, [(sx * 230, -40), (sx * 340, -160), (sx * 330, -260)], 46, f("body", "red"))
        p.blob([(sx * 330, -230), (sx * 250, -330), (sx * 300, -480), (sx * 420, -440), (sx * 430, -300), (sx * 360, -330)], f("claw", "red"))
        p.line([(sx * 90, -230), (sx * 110, -350)], lw=p.lw * 1.3)
        p.eye(sx * 110, -380, 52)
    p.part("claw", 380, -390)
    p.blob([(-330, 60), (-230, -150), (0, -200), (230, -150), (330, 60), (200, 250), (-200, 250)], f("body", "red"))
    p.part("body", 0, 170)
    p.cheeks(150, 60, 38, F)
    p.smile(0, 50, 100)


def turtle(p, F):
    f = lambda k, d="white": p.fill_of(F, k, d)
    for sx in (-1, 1):
        p.ell(sx * 230, 320, 90, 70, f("skin", "green"))
    p.blob([(-420, 40), (-300, -110), (-210, -100), (-200, 60)], f("skin", "green"))
    p.ell(-330, -220, 150, 140, f("skin", "green"))
    p.part("skin", -330, -330)
    p.blob([(300, 200), (440, 230), (330, 280)], f("skin", "green"))
    c = p.c
    c.new_path()
    c.save()
    c.translate(60, 230)
    c.scale(380, 380)
    c.arc(0, 0, 1, math.pi, 2 * math.pi)
    c.restore()
    c.close_path()
    p._paint(f("shell", "darkgreen"), True)
    p.rrect(-340, 200, 800, 70, 35, f("rim", "tan"))
    for (x, y, r) in [(60, -20, 85), (-140, 80, 65), (260, 80, 65), (60, 140, 55)]:
        p.blob([(x + math.cos(a) * r, y + math.sin(a) * r) for a in [i * math.pi / 3 for i in range(6)]], f("tile", "green"))
    p.part("tile", 60, -20)
    p.part("shell", -110, -40)
    p.eye(-370, -240, 42)
    p.smile(-290, -150, 70)


def starfish(p, F):
    f = lambda k, d="white": p.fill_of(F, k, d)
    p.blob(p.star_pts(0, 30, 470, inner=.52), f("body", "orange"))
    p.part("body", 0, -280)
    for (x, y) in [(-140, 230), (140, 230), (0, -150), (-260, -20), (260, -20)]:
        p.circ(x, y, 18, f("dot", "yellow"), lw=p.lw * .7)
    p.eye(-80, 10, 44)
    p.eye(80, 10, 44)
    p.smile(0, 110, 80)


# ---------------------------------------------------------------- bugs
def bee(p, F):
    f = lambda k, d="white": p.fill_of(F, k, d)
    for sx in (-1, 1):
        p.ell(sx * 190, -230, 160, 110, f("wing", "lightblue"), rot=-sx * .6)
    p.part("wing", 230, -270)
    p.poly([(330, 120), (450, 150), (330, 190)], f("stinger", "black"))
    p.ell(60, 130, 300, 230, f("body", "yellow"))
    c = p.c
    for x in (60, 190):
        c.save()
        c.new_path()
        c.translate(60, 130)
        c.scale(300, 230)
        c.arc(0, 0, 1, 0, 2 * math.pi)
        c.restore()
        c.clip()
        p.rrect(x - 40, -200, 80, 600, 10, f("stripe", "black"))
        c.reset_clip()
    p.part("body", -60, 230)
    p.circ(-200, -60, 190, f("body", "yellow"))
    for sx in (-1, 1):
        outlined_stroke(p, [(-200 + sx * 60, -230), (-200 + sx * 90, -330), (-200 + sx * 140, -380)], 14, BLACK if not p.colour else col("black"))
        p.circ(-200 + sx * 145, -385, 24, f("stripe", "black"))
    p.eye(-270, -70, 40)
    p.eye(-130, -70, 40)
    p.smile(-200, 30, 70)


def ladybug(p, F):
    f = lambda k, d="white": p.fill_of(F, k, d)
    for sx in (-1, 1):
        for i in range(3):
            p.line([(sx * 250, 50 + i * 120), (sx * 380, 90 + i * 120)], lw=p.lw * 1.3)
    p.ell(0, 120, 330, 320, f("shell", "red"))
    p.line([(0, -80), (0, 440)], lw=p.lw)
    for (x, y, r) in [(-170, 60, 55), (170, 60, 55), (-150, 250, 50), (150, 250, 50), (-60, 360, 35), (60, 360, 35)]:
        p.circ(x, y, r, f("spot", "black"))
    p.part("shell", -150, 160)
    p.ell(0, -200, 210, 180, f("head", "black"))
    p.part("head", 0, -320)
    for sx in (-1, 1):
        p.curve([(sx * 70, -350), (sx * 110, -440), (sx * 170, -470)], lw=p.lw)
        p.circ(sx * 175, -475, 22, f("head", "black"))
        p.eye(sx * 85, -210, 46)
    p.smile(0, -110, 80)


def butterfly(p, F):
    f = lambda k, d="white": p.fill_of(F, k, d)
    for sx in (-1, 1):
        p.blob([(sx * 30, -40), (sx * 200, -360), (sx * 430, -350), (sx * 430, -120), (sx * 200, 20)], f("wing", "purple"))
        p.blob([(sx * 30, 40), (sx * 300, 60), (sx * 360, 280), (sx * 180, 380), (sx * 40, 200)], f("wing2", "pink"))
        p.circ(sx * 280, -200, 70, f("dot", "yellow"))
        p.circ(sx * 220, 220, 50, f("dot", "yellow"))
    p.part("wing", 340, -280)
    p.part("wing2", 280, 300)
    p.part("dot", 280, -200)
    p.ell(0, 80, 55, 280, f("body", "brown"))
    p.circ(0, -260, 95, f("body", "brown"))
    for sx in (-1, 1):
        p.curve([(sx * 30, -340), (sx * 70, -430), (sx * 130, -470)], lw=p.lw)
        p.circ(sx * 135, -475, 20, f("body", "brown"))
    p.eye(-35, -270, 26)
    p.eye(35, -270, 26)
    p.smile(0, -215, 44)


def snail(p, F):
    f = lambda k, d="white": p.fill_of(F, k, d)
    p.blob([(-420, 420), (-330, 250), (-320, -40), (-250, -100), (-180, -40), (-160, 250), (300, 300), (430, 420)], f("body", "green"))
    p.part("body", 300, 380)
    for sx, x in ((-1, -300), (1, -200)):
        p.line([(x, -60), (x + sx * 40, -200)], lw=p.lw * 1.2)
        p.circ(x + sx * 40, -210, 28, f("body", "green"))
    p.eye(-280, 20, 38)
    p.eye(-190, 20, 38)
    p.smile(-235, 120, 60)
    p.circ(110, 80, 280, f("shell", "orange"))
    c = p.c
    c.new_path()
    pts = [(110 + math.cos(t) * (230 - t * 30), 80 + math.sin(t) * (230 - t * 30)) for t in [i * .2 for i in range(0, 34)]]
    p.curve(pts, lw=p.lw * 1.2)
    p.part("shell", 110, -110)


def caterpillar(p, F):
    f = lambda k, d="white": p.fill_of(F, k, d)
    segs = [(350, 300), (220, 240), (90, 280), (-40, 230), (-170, 260)]
    for i, (x, y) in enumerate(segs):
        p.circ(x, y, 120, f("body" if i % 2 == 0 else "body2", "green" if i % 2 == 0 else "yellow"))
        p.line([(x - 30, y + 110), (x - 30, y + 160)], lw=p.lw * 1.2)
        p.line([(x + 30, y + 110), (x + 30, y + 160)], lw=p.lw * 1.2)
    p.part("body", 350, 300)
    p.part("body2", 220, 240)
    p.circ(-300, 60, 190, f("head", "green"))
    p.part("head", -300, -60)
    for sx in (-1, 1):
        p.curve([(-300 + sx * 60, -110), (-300 + sx * 80, -220), (-300 + sx * 140, -260)], lw=p.lw)
        p.circ(-300 + sx * 145, -265, 26, f("dot", "red"))
        p.eye(-300 + sx * 70, 50, 42)
    p.smile(-300, 140, 80)


# ---------------------------------------------------------------- others
def robot(p, F):
    f = lambda k, d="white": p.fill_of(F, k, d)
    p.line([(0, -420), (0, -500)], lw=p.lw * 1.2)
    p.circ(0, -520, 40, f("light", "red"))
    for sx in (-1, 1):
        outlined_stroke(p, [(sx * 250, 150), (sx * 360, 250), (sx * 330, 360)], 60, f("arm", "gray"))
        p.circ(sx * 330, 380, 55, f("hand", "blue"))
        p.rrect(sx * 130 - 70, 380, 140, 100, 25, f("feet", "blue"))
    p.rrect(-250, 60, 500, 350, 60, f("body", "lightblue"))
    p.part("body", -150, 320)
    p.rrect(-100, 130, 200, 140, 30, f("panel", "yellow"))
    for (x, y) in ((-45, 200), (45, 200)):
        p.circ(x, y, 24, f("button", "red"))
    p.part("panel", 0, 245)
    for sx in (-1, 1):
        p.rrect(sx * 330 - 40, -260, 80, 120, 30, f("bolt", "gray"))
    p.rrect(-310, -420, 620, 420, 90, f("head", "gray"))
    p.part("head", -200, -350)
    p.rrect(-230, -330, 460, 230, 70, f("screen", "white"))
    p.eye(-100, -230, 50)
    p.eye(100, -230, 50)
    p.smile(0, -140, 80)


def snowman(p, F):
    f = lambda k, d="white": p.fill_of(F, k, d)
    p.circ(0, 270, 240, f("snow", "white"))
    p.part("snow", -100, 330)
    for sx in (-1, 1):
        outlined_stroke(p, [(sx * 150, -40), (sx * 300, -120), (sx * 380, -100)], 22, f("arm", "brown"), smooth=False)
    p.circ(0, -20, 180, f("snow", "white"))
    for y in (-40, 40, 230, 330):
        p.circ(0, y, 22, f("button", "black"))
    p.circ(0, -250, 150, f("snow", "white"))
    p.rrect(-150, -160, 300, 60, 30, f("scarf", "red"))
    p.rrect(60, -140, 70, 200, 30, f("scarf", "red"))
    p.part("scarf", -60, -130)
    p.rrect(-130, -390, 260, 40, 15, f("hat", "black"))
    p.rrect(-90, -540, 180, 160, 20, f("hat", "black"))
    p.rrect(-90, -430, 180, 35, 0, f("band", "green"))
    p.part("hat", 0, -480)
    p.eye(-55, -270, 34)
    p.eye(55, -270, 34)
    p.poly([(0, -230), (110, -200), (0, -185)], f("nose", "orange"))
    p.smile(0, -170, 60)


def dino(p, F):
    """Standing chibi dinosaur (no ears, back plates, long tail)."""
    critter(p, F, ears="none", snout="none", tail="dino", extras=("spikes",), belly=True)


CHARACTERS = {
    # name: (draw_fn, default colours)
    "cat": (_crit(ears="pointy", snout="small", tail="curl", extras=("whiskers",), belly=True), {"body": "orange", "belly": "white", "inner": "pink", "tail": "orange"}),
    "dog": (_crit(ears="floppy", snout="muzzle", tail="short", extras=("eyespot",)), {"body": "tan", "ear": "brown", "spot": "brown", "snout": "white"}),
    "bunny": (_crit(ears="long", snout="small", tail="puff", extras=("teeth",), belly=True), {"body": "white", "inner": "pink", "belly": "lightpink"}),
    "bear": (_crit(ears="round", snout="muzzle", belly=True), {"body": "brown", "inner": "tan", "snout": "tan", "belly": "tan"}),
    "panda": (_crit(ears="round", snout="muzzle", extras=("patches",)), {"body": "white", "ear": "black", "inner": "black", "patch": "black", "arm": "black", "feet": "black", "snout": "white"}),
    "pig": (_crit(ears="pointy", snout="pig", tail="pig"), {"body": "pink", "inner": "lightpink", "snout": "lightpink"}),
    "cow": (_crit(ears="side", snout="big", tail="thin", extras=("horns", "spots")), {"body": "white", "spot": "darkbrown", "snout": "pink", "horn": "tan", "inner": "pink"}),
    "sheep": (_crit(ears="side", snout="small", extras=("wool",)), {"body": "tan", "wool": "white", "ear": "tan", "arm": "tan", "feet": "darkbrown"}),
    "fox": (_crit(ears="pointy", snout="muzzle", tail="bushy", belly=True), {"body": "orange", "belly": "white", "snout": "white", "tail": "orange", "inner": "white"}),
    "mouse": (_crit(ears="mouse", snout="small", tail="thin", belly=True), {"body": "gray", "inner": "pink", "belly": "white"}),
    "lion": (_crit(ears="round", snout="muzzle", tail="tuft", extras=("mane",), belly=True), {"body": "yellow", "mane": "orange", "snout": "white", "belly": "tan", "inner": "tan"}),
    "elephant": (_crit(ears="big", snout="trunk", belly=False), {"body": "gray", "inner": "pink"}),
    "monkey": (_crit(ears="monkey", snout="small", tail="curl", extras=("heartface",), belly=True), {"body": "brown", "face": "tan", "inner": "tan", "belly": "tan", "tail": "brown"}),
    "koala": (_crit(ears="fluffy", snout="nose", belly=True), {"body": "gray", "ear": "gray", "inner": "white", "belly": "white", "nose": "black"}),
    "raccoon": (_crit(ears="pointy", snout="small", tail="striped", extras=("mask",), belly=True), {"body": "gray", "mask": "darkbrown", "belly": "white", "tail": "gray", "inner": "white"}),
    "hedgehog": (_crit(ears="tiny", snout="small", extras=("quills",), belly=True), {"body": "tan", "quill": "brown", "belly": "white"}),
    "capybara": (_crit(ears="tiny", snout="boxy", eye_r=34), {"body": "#c98b5b", "snout": "#a8703f", "ear": "#a8703f"}),
    "reindeer": (_crit(ears="side", snout="muzzle", tail="short", extras=("antlers", "rednose"), belly=True), {"body": "brown", "antler": "tan", "nose": "red", "belly": "tan", "snout": "tan", "inner": "tan"}),
    "unicorn": (_crit(ears="pointy", snout="small", tail="puff", extras=("unicorn_horn", "unicorn_mane")), {"body": "white", "mane": "purple", "horn": "yellow", "tail": "pink", "inner": "pink"}),
    "dragon": (_crit(ears="none", snout="small", tail="dragon", extras=("wings", "spikes"), belly=True), {"body": "green", "wing": "purple", "spike": "yellow", "belly": "yellow"}),
    "dino": (dino, {"body": "green", "spike": "orange", "belly": "yellow"}),
    "frog": (_crit(ears="none", snout="wide", extras=("frog_eyes",), belly=True), {"body": "green", "belly": "yellow"}),
    "chick": (chick, {"body": "yellow", "wing": "orange", "beak": "orange", "feet": "orange"}),
    "duck": (duck, {"body": "white", "beak": "orange", "feet": "orange", "wing": "white"}),
    "owl": (owl, {"body": "brown", "belly": "tan", "wing": "darkbrown", "beak": "orange", "eyering": "white", "feet": "orange"}),
    "penguin": (penguin, {"body": "black", "belly": "white", "beak": "orange", "feet": "orange"}),
    "fish": (fish, {"body": "orange", "fin": "yellow"}),
    "whale": (whale, {"body": "blue", "belly": "lightblue", "fin": "blue"}),
    "octopus": (octopus, {"body": "purple", "spot": "pink"}),
    "crab": (crab, {"body": "red", "claw": "red"}),
    "turtle": (turtle, {"skin": "green", "shell": "darkgreen", "tile": "green", "rim": "tan"}),
    "starfish": (starfish, {"body": "orange", "dot": "yellow"}),
    "bee": (bee, {"body": "yellow", "stripe": "black", "wing": "lightblue", "stinger": "black"}),
    "ladybug": (ladybug, {"shell": "red", "spot": "black", "head": "black"}),
    "butterfly": (butterfly, {"wing": "purple", "wing2": "pink", "dot": "yellow", "body": "brown"}),
    "snail": (snail, {"body": "green", "shell": "orange"}),
    "caterpillar": (caterpillar, {"body": "green", "body2": "yellow", "head": "green", "dot": "red"}),
    "robot": (robot, {"body": "lightblue", "head": "gray", "panel": "yellow", "button": "red", "arm": "gray", "hand": "blue", "feet": "blue", "light": "red", "screen": "white", "bolt": "gray"}),
    "snowman": (snowman, {"snow": "white", "scarf": "red", "hat": "black", "band": "green", "nose": "orange", "arm": "brown", "button": "black"}),
}


def draw_char(p, name, x, y, h, colour=None, flip=False, palette=None):
    """Draw character `name` with height h centred at (x, y). Returns its colour map."""
    fn, default = CHARACTERS[name]
    F = dict(default)
    if palette:
        F.update(palette)
    with p.at(x, y, h / 1000, flip=flip):
        fn(p, F)
    return F
