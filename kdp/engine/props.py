"""Prop / object library (same conventions as chars.py: local box ~900 x 1000,
centred on 0, bottom near +480; F maps part -> crayon colour)."""
import math

from draw import BLACK, WHITE, col
from chars import outlined_stroke, scallop_ring


def _f(p, F):
    return lambda k, d="white": p.fill_of(F, k, d)


def tree(p, F):
    f = _f(p, F)
    p.rrect(-70, 100, 140, 380, 30, f("trunk", "brown"))
    p.part("trunk", 0, 330)
    scallop_ring(p, 0, -150, 300, 260, 11, 110, f("leaves", "green"))
    p.part("leaves", 0, -150)
    for (x, y) in [(-120, -200), (110, -110), (-40, -20)]:
        p.circ(x, y, 34, f("apple", "red"))


def pine(p, F):
    f = _f(p, F)
    p.rrect(-60, 330, 120, 150, 20, f("trunk", "brown"))
    for i, (y, w) in enumerate([(-470, 170), (-260, 260), (-40, 340)]):
        p.blob([(0, y), (w, y + 330), (0, y + 300), (-w, y + 330)], f("leaves", "darkgreen"))
    p.part("leaves", 0, 150)


def flower(p, F):
    f = _f(p, F)
    p.line([(0, 0), (0, 480)], lw=p.lw * 1.4)
    p.ell(-110, 300, 110, 45, f("leaf", "green"), rot=-.5)
    p.ell(110, 380, 110, 45, f("leaf", "green"), rot=.5)
    for i in range(6):
        a = i * math.pi / 3
        p.ell(math.cos(a) * 150, -150 + math.sin(a) * 150, 110, 110, f("petal", "pink"))
    p.part("petal", 150, -150)
    p.circ(0, -150, 110, f("center", "yellow"))
    p.part("center", 0, -150)


def mushroom(p, F):
    f = _f(p, F)
    p.rrect(-120, 0, 240, 470, 90, f("stem", "tan"))
    p.part("stem", 0, 300)
    p.c.new_path()
    p.c.save()
    p.c.translate(0, 40)
    p.c.scale(430, 420)
    p.c.arc(0, 0, 1, math.pi, 2 * math.pi)
    p.c.restore()
    p.c.close_path()
    p._paint(f("cap", "red"), True)
    for (x, y, r) in [(-200, -100, 55), (60, -250, 70), (230, -60, 50), (-30, -60, 40)]:
        p.circ(x, y, r, f("dot", "white"))
    p.part("cap", -100, -250)


def barn(p, F):
    f = _f(p, F)
    p.poly([(-420, -120), (0, -460), (420, -120)], f("roof", "darkbrown"))
    p.rrect(-380, -130, 760, 610, 10, f("wall", "red"))
    p.part("wall", -260, 120)
    p.part("roof", 0, -330)
    p.rrect(-160, 120, 320, 360, 10, f("door", "white"))
    p.line([(-160, 120), (160, 480)])
    p.line([(160, 120), (-160, 480)])
    p.circ(0, -150, 70, f("window", "yellow"))


def house(p, F):
    f = _f(p, F)
    p.rrect(170, -380, 100, 200, 10, f("chimney", "red"))
    p.poly([(-440, -60), (0, -440), (440, -60)], f("roof", "red"))
    p.part("roof", 0, -230)
    p.rrect(-360, -70, 720, 550, 10, f("wall", "yellow"))
    p.part("wall", 250, 330)
    p.rrect(-90, 180, 180, 300, 80, f("door", "brown"))
    for x in (-250, 250):
        p.rrect(x - 75, 30, 150, 130, 15, f("window", "lightblue"))
        p.line([(x, 30), (x, 160)])
        p.line([(x - 75, 95), (x + 75, 95)])


def apple(p, F):
    f = _f(p, F)
    p.blob([(0, -230), (230, -330), (390, -60), (330, 270), (150, 430), (0, 380), (-150, 430), (-330, 270), (-390, -60), (-230, -330)], f("apple", "red"))
    p.part("apple", 0, 80)
    p.line([(0, -230), (30, -420)], lw=p.lw * 1.8)
    p.ell(160, -400, 130, 60, f("leaf", "green"), rot=-.5)
    p.ell(-170, -130, 50, 90, WHITE if not p.colour else col("lightpink"), rot=.5, stroke=False)


def carrot(p, F):
    f = _f(p, F)
    for a in (-.5, 0, .5):
        with p.at(0, -300, 1, rot=a):
            p.ell(0, -120, 55, 150, f("leaf", "green"))
    p.blob([(-200, -300), (200, -300), (40, 470), (-40, 470)], f("carrot", "orange"))
    p.part("carrot", 0, -100)
    for y in (-150, 0, 150):
        p.line([(-120 + y * .25, y), (-40 + y * .2, y + 20)], lw=p.lw * .9)


def strawberry(p, F):
    f = _f(p, F)
    p.blob([(0, -250), (330, -260), (300, 80), (0, 460), (-300, 80), (-330, -260)], f("berry", "red"))
    p.part("berry", 0, 60)
    for (x, y) in [(-150, -120), (0, -120), (150, -120), (-90, 30), (90, 30), (0, 180), (-150, 120), (150, 120)]:
        p.ell(x, y, 12, 20, BLACK, stroke=False)
    for a in (-1.2, -.6, 0, .6, 1.2):
        with p.at(0, -270, 1, rot=a):
            p.ell(0, -90, 50, 110, f("leaf", "green"))


def cupcake(p, F):
    f = _f(p, F)
    p.poly([(-260, 50), (260, 50), (190, 470), (-190, 470)], f("cup", "pink"))
    for x in (-130, 0, 130):
        p.line([(x, 60), (x * .75, 460)])
    p.part("cup", -60, 300)
    scallop_ring(p, 0, -60, 270, 130, 9, 95, f("frosting", "lightpink"))
    p.blob([(-170, -150), (0, -330), (170, -150)], f("frosting", "lightpink"))
    p.part("frosting", 0, -120)
    p.circ(0, -360, 70, f("cherry", "red"))
    p.curve([(0, -420), (40, -500), (100, -520)], lw=p.lw)


def donut(p, F):
    f = _f(p, F)
    p.ell(0, 30, 420, 380, f("dough", "tan"))
    scallop_ring(p, 0, 0, 330, 290, 12, 50, f("icing", "pink"))
    p.part("icing", -200, -120)
    p.ell(0, 0, 120, 100, WHITE)
    for (x, y, a) in [(-150, -200, .3), (180, -150, -.6), (-240, 60, 1.2), (220, 120, .4), (0, 220, -.2), (60, -240, .9)]:
        with p.at(x, y, 1, rot=a):
            p.rrect(-28, -10, 56, 20, 10, f("sprinkle", "yellow"), lw=p.lw * .7)


def icecream(p, F):
    f = _f(p, F)
    p.poly([(-200, -40), (200, -40), (0, 480)], f("cone", "tan"))
    for i in range(3):
        p.line([(-160 + i * 90, -40), (60 + i * 50, 300)], lw=p.lw * .8)
    p.part("cone", 0, 100)
    p.circ(0, -150, 210, f("scoop", "pink"))
    p.circ(0, -380, 170, f("scoop2", "brown"))
    p.part("scoop", -80, -110)
    p.part("scoop2", 0, -400)
    p.circ(0, -560, 50, f("cherry", "red"))


def cake(p, F):
    f = _f(p, F)
    p.rrect(-380, 80, 760, 380, 40, f("cake", "pink"))
    p.part("cake", -250, 330)
    p.rrect(-280, -180, 560, 280, 40, f("cake2", "yellow"))
    p.part("cake2", -170, -40)
    scallop_ring(p, 0, 85, 360, 35, 10, 40, f("icing", "white"))
    for x in (-150, 0, 150):
        p.rrect(x - 25, -380, 50, 200, 15, f("candle", "blue"))
        p.blob([(x, -470), (x + 30, -410), (x, -380), (x - 30, -410)], f("flame", "orange"))


def balloon(p, F):
    f = _f(p, F)
    p.curve([(0, 150), (60, 260), (-40, 380), (20, 480)], lw=p.lw * .9)
    p.blob([(0, -470), (250, -350), (280, -60), (120, 120), (0, 150), (-120, 120), (-280, -60), (-250, -350)], f("balloon", "red"))
    p.poly([(-35, 180), (0, 140), (35, 180)], f("balloon", "red"))
    p.part("balloon", 0, -160)


def gift(p, F):
    f = _f(p, F)
    p.rrect(-360, -100, 720, 580, 20, f("box", "red"))
    p.part("box", -200, 250)
    p.rrect(-400, -220, 800, 150, 20, f("lid", "red"))
    p.rrect(-60, -220, 120, 700, 0, f("ribbon", "yellow"))
    for sx in (-1, 1):
        p.ell(sx * 120, -300, 130, 80, f("ribbon", "yellow"), rot=sx * .4)
    p.circ(0, -280, 50, f("ribbon", "yellow"))
    p.part("ribbon", 0, 200)


def xmastree(p, F):
    f = _f(p, F)
    p.rrect(-80, 360, 160, 120, 20, f("trunk", "brown"))
    for (y, w) in [(-380, 170), (-200, 270), (0, 360)]:
        p.blob([(0, y), (w, y + 370), (0, y + 330), (-w, y + 370)], f("tree", "darkgreen"))
    p.part("tree", 0, 200)
    p.poly(p.star_pts(0, -430, 110), f("star", "yellow"))
    for (x, y, k) in [(-120, -40, "ball"), (110, 60, "ball2"), (-200, 260, "ball2"), (190, 280, "ball"), (0, 180, "ball"), (40, -170, "ball2")]:
        p.circ(x, y, 42, f(k, "red" if k == "ball" else "blue"))


def candycane(p, F):
    f = _f(p, F)
    outlined_stroke(p, [(100, 480), (100, -250), (40, -400), (-120, -430), (-220, -330), (-230, -220)], 130, f("cane", "white"))
    for y in range(-160, 470, 120):
        p.line([(52, y), (148, y - 60)], lw=p.lw * 2.5)
    p.part("cane", 100, 330)


def star(p, F):
    f = _f(p, F)
    p.blob(p.star_pts(0, 30, 470, inner=.5), f("star", "yellow"))
    p.part("star", 0, 80)


def heart(p, F):
    f = _f(p, F)
    p.heart_path(0, 0, 480)
    p._paint(f("heart", "red"), True)
    p.part("heart", 0, 30)


def sun(p, F):
    f = _f(p, F)
    for i in range(10):
        a = i * math.pi / 5
        with p.at(math.cos(a) * 360, math.sin(a) * 360, 1, rot=a + math.pi / 2):
            p.poly([(-60, 40), (0, -90), (60, 40)], f("ray", "orange"))
    p.circ(0, 0, 280, f("sun", "yellow"))
    p.part("sun", 0, -170)
    p.eye(-90, -40, 38)
    p.eye(90, -40, 38)
    p.smile(0, 80, 90)


def moon(p, F):
    f = _f(p, F)
    p.blob([(100, -460), (-200, -380), (-350, 0), (-200, 380), (100, 460), (-60, 250), (-130, 0), (-60, -250)], f("moon", "yellow"))
    p.part("moon", -230, 0)


def planet(p, F):
    f = _f(p, F)
    p.ell(0, 0, 470, 120, f("ring", "orange"), rot=-.3)
    p.circ(0, 0, 290, f("planet", "purple"))
    p.part("planet", -60, -150)
    c = p.c
    c.save()
    c.rotate(-.3)
    c.new_path()
    c.save()
    c.scale(470, 120)
    c.arc(0, 0, 1, 0, math.pi)
    c.restore()
    c.save()
    c.scale(330, 60)
    c.arc_negative(0, 0, 1, math.pi, 0)
    c.restore()
    c.close_path()
    p._paint(f("ring", "orange"), True)
    c.restore()


def rocket(p, F):
    f = _f(p, F)
    p.blob([(-60, 300), (0, 480), (60, 300)], f("flame", "orange"))
    for sx in (-1, 1):
        p.poly([(sx * 120, 100), (sx * 280, 330), (sx * 120, 300)], f("fin", "red"))
    p.blob([(0, -480), (170, -220), (150, 320), (-150, 320), (-170, -220)], f("body", "white"))
    p.part("body", 0, 200)
    p.blob([(0, -480), (140, -280), (-140, -280)], f("nose", "red"))
    p.circ(0, -80, 90, f("window", "lightblue"))
    p.part("fin", 210, 270)


def car(p, F):
    f = _f(p, F)
    p.blob([(-220, -50), (-130, -260), (160, -260), (260, -50)], f("roof", "red"))
    p.rrect(-440, -60, 880, 260, 90, f("body", "red"))
    p.part("body", 0, 80)
    for x in (-160, 100):
        p.rrect(x - 70, -230, 140 if x < 0 else 130, 160, 25, f("window", "lightblue"))
    for x in (-250, 250):
        p.circ(x, 210, 110, f("tire", "black"))
        p.circ(x, 210, 45, f("hub", "gray"))
    p.circ(400, 20, 30, f("light", "yellow"))


def truck(p, F):
    f = _f(p, F)
    p.poly([(-460, -160), (60, -160), (40, 200), (-440, 200)], f("bed", "yellow"))
    p.part("bed", -200, 20)
    p.rrect(60, -280, 380, 480, 50, f("cab", "orange"))
    p.part("cab", 330, 100)
    p.rrect(140, -220, 220, 170, 30, f("window", "lightblue"))
    for x in (-300, 280):
        p.circ(x, 250, 130, f("tire", "black"))
        p.circ(x, 250, 55, f("hub", "gray"))
    for (x, y, r) in [(-320, -230, 90), (-170, -260, 110), (-40, -220, 80)]:
        p.circ(x, y, r, f("dirt", "brown"))


def train(p, F):
    f = _f(p, F)
    p.rrect(-300, -440, 120, 200, 20, f("chimney", "black"))
    scallop_ring(p, -240, -500, 70, 40, 6, 40, WHITE)
    p.rrect(-420, -250, 520, 500, 40, f("body", "blue"))
    p.part("body", -260, 120)
    p.rrect(100, -420, 340, 670, 40, f("cab", "red"))
    p.part("cab", 270, 150)
    p.rrect(170, -350, 200, 170, 30, f("window", "lightblue"))
    p.rrect(-460, -290, 600, 60, 20, f("trim", "yellow"))
    for x in (-300, -60, 270):
        p.circ(x, 330, 120, f("wheel", "gray"))
        p.circ(x, 330, 40, f("hub", "yellow"))


def plane(p, F):
    f = _f(p, F)
    p.poly([(320, -80), (440, -330), (470, -60)], f("tail", "red"))
    p.blob([(-460, 30), (-340, -100), (400, -110), (470, 0), (400, 90), (-340, 100)], f("body", "white"))
    p.part("body", 160, 30)
    p.poly([(-80, 0), (140, 0), (-60, 380), (-180, 380)], f("wing", "blue"))
    p.part("wing", -60, 200)
    for x in (-200, -80, 40, 160):
        p.circ(x, -20, 34, f("window", "lightblue"))


def boat(p, F):
    f = _f(p, F)
    p.line([(0, 200), (0, -470)], lw=p.lw * 1.5)
    p.poly([(20, -440), (360, 120), (20, 120)], f("sail", "white"))
    p.poly([(-20, -340), (-300, 120), (-20, 120)], f("sail2", "yellow"))
    p.part("sail", 130, 30)
    p.blob([(-460, 180), (460, 180), (330, 440), (-330, 440)], f("hull", "red"))
    p.part("hull", 0, 300)
    for x in (-180, 0, 180):
        p.circ(x, 290, 40, f("window", "lightblue"))


def shell(p, F):
    f = _f(p, F)
    p.blob([(0, -400), (330, -200), (420, 150), (200, 380), (-200, 380), (-420, 150), (-330, -200)], f("shell", "pink"))
    for a in (-60, -30, 0, 30, 60):
        r = math.radians(a)
        p.line([(0, 380), (math.sin(r) * 380, 380 - math.cos(r) * 700)])
    p.rrect(-120, 360, 240, 110, 40, f("base", "lightpink"))
    p.part("shell", -100, 0)


def seaweed(p, F):
    f = _f(p, F)
    for x, h in ((-130, 900), (40, 1000), (190, 800)):
        outlined_stroke(p, [(x, 480), (x - 60, 480 - h * .3), (x + 50, 480 - h * .6), (x - 30, 480 - h * .95)], 60, f("weed", "green"))
    p.part("weed", 40, 300)


def coral(p, F):
    f = _f(p, F)
    for pts in ([(0, 480), (0, 100), (-150, -150), (-170, -350)], [(0, 200), (200, -50), (230, -300)], [(0, 100), (40, -200), (20, -440)], [(-90, -40), (-300, -130), (-350, -290)]):
        outlined_stroke(p, pts, 80, f("coral", "pink"))
    p.part("coral", 0, 330)


def rock(p, F):
    f = _f(p, F)
    p.blob([(-420, 470), (-330, 150), (-80, 30), (200, 80), (400, 300), (440, 470)], f("rock", "gray"))
    p.part("rock", 0, 300)


def snowflake(p, F):
    f = _f(p, F)
    for i in range(6):
        a = i * math.pi / 3
        x, y = math.cos(a) * 420, math.sin(a) * 420
        outlined_stroke(p, [(0, 0), (x, y)], 50, f("flake", "lightblue"), smooth=False)
        for t in (.55,):
            bx, by = x * t, y * t
            for d in (-.6, .6):
                outlined_stroke(p, [(bx, by), (bx + math.cos(a + d) * 150, by + math.sin(a + d) * 150)], 40, f("flake", "lightblue"), smooth=False)
    p.circ(0, 0, 70, f("flake", "lightblue"))
    p.part("flake", 0, 0)


def pumpkin(p, F):
    f = _f(p, F)
    p.rrect(-40, -440, 80, 160, 20, f("stem", "green"))
    for x, rx in ((-200, 220), (200, 220), (0, 230)):
        p.ell(x, 50, rx, 380, f("pumpkin", "orange"))
    p.part("pumpkin", 0, 50)


def egg(p, F):
    f = _f(p, F)
    p.blob([(0, -470), (280, -250), (360, 120), (220, 420), (0, 470), (-220, 420), (-360, 120), (-280, -250)], f("egg", "lightblue"))
    p.c.save()
    p.spline_path([(0, -470), (280, -250), (360, 120), (220, 420), (0, 470), (-220, 420), (-360, 120), (-280, -250)], True)
    p.c.clip()
    zig = [(-400 + i * 80, (-60 if i % 2 else 20)) for i in range(11)]
    p.line(zig, lw=p.lw * 1.2)
    p.rrect(-400, 200, 800, 70, 0, f("band", "yellow"))
    p.c.restore()
    p.part("egg", 0, -250)


def fence(p, F):
    f = _f(p, F)
    p.rrect(-460, -150, 920, 80, 20, f("fence", "brown"))
    p.rrect(-460, 150, 920, 80, 20, f("fence", "brown"))
    for x in (-380, -130, 130, 380):
        p.blob([(x - 60, 480), (x - 60, -320), (x, -420), (x + 60, -320), (x + 60, 480)], f("fence", "brown"))
    p.part("fence", -380, 0)


def bone(p, F):
    f = _f(p, F)
    p.rrect(-300, -80, 600, 160, 60, f("bone", "white"))
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.circ(sx * 330, sy * 90, 110, f("bone", "white"))
    p.rrect(-300, -78, 600, 156, 0, f("bone", "white"), stroke=False)
    p.part("bone", 0, 0)


def cookie(p, F):
    f = _f(p, F)
    p.circ(0, 0, 420, f("cookie", "tan"))
    p.part("cookie", -180, -180)
    for (x, y) in [(-100, -200), (150, -150), (-220, 50), (80, 60), (-50, 250), (220, 220), (20, -40)]:
        p.blob([(x - 35, y), (x, y - 30), (x + 40, y - 5), (x + 10, y + 35)], f("chip", "darkbrown"))


def lollipop(p, F):
    f = _f(p, F)
    p.rrect(-25, 0, 50, 480, 20, f("stick", "white"))
    p.circ(0, -180, 300, f("candy", "pink"))
    pts = [(math.cos(t) * t * 32, -180 + math.sin(t) * t * 32) for t in [i * .25 for i in range(0, 38)]]
    p.curve(pts, lw=p.lw * 1.3)
    p.part("candy", 0, -180)


def umbrella(p, F):
    f = _f(p, F)
    outlined_stroke(p, [(0, -100), (0, 380), (-30, 450), (-110, 450), (-130, 390)], 34, f("handle", "brown"))
    c = p.c
    c.new_path()
    c.arc(0, -100, 440, math.pi, 2 * math.pi)
    c.close_path()
    p._paint(f("canopy", "blue"), True)
    for x in (-264, -88, 88, 264):
        p.line([(0, -540), (x, -100)], lw=p.lw * .8)
    p.part("canopy", -180, -260)


PROPS = {
    "tree": tree, "pine": pine, "flower": flower, "mushroom": mushroom, "barn": barn, "house": house,
    "apple": apple, "carrot": carrot, "strawberry": strawberry, "cupcake": cupcake, "donut": donut,
    "icecream": icecream, "cake": cake, "balloon": balloon, "gift": gift, "xmastree": xmastree,
    "candycane": candycane, "star": star, "heart": heart, "sun": sun, "moon": moon, "planet": planet,
    "rocket": rocket, "car": car, "truck": truck, "train": train, "plane": plane, "boat": boat,
    "shell": shell, "seaweed": seaweed, "coral": coral, "rock": rock, "snowflake": snowflake,
    "pumpkin": pumpkin, "egg": egg, "fence": fence, "bone": bone, "cookie": cookie, "lollipop": lollipop,
    "umbrella": umbrella,
}


def draw_prop(p, name, x, y, h, palette=None, flip=False, rot=0.0):
    F = dict(palette or {})
    with p.at(x, y, h / 1000, rot=rot, flip=flip):
        PROPS[name](p, F)
    return F
