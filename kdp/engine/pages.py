"""Interior page types. Every function draws one full page in page space (1700 x 2200)
and takes (p, theme, rng, n) where n is a per-type counter used for variety."""
import math
import random

from draw import W, H, WHITE, BLACK, CRAYON
from chars import CHARACTERS, draw_char
from props import PROPS, draw_prop

FR = (110, 400, 1590, 1930)          # picture frame
CX = (FR[0] + FR[2]) / 2

NICE = {"lightblue": "light blue", "darkgreen": "dark green", "darkbrown": "dark brown",
        "lightpink": "light pink", "tan": "tan", "gray": "gray"}


def header(p, title, sub):
    size = p.fit_size(title, 1480, 78)
    p.text(title, 110, 215, size)
    size2 = p.fit_size(sub, 1480, 40, bold=False)
    p.text(sub, 110, 300, size2, bold=False)


def footer_brand(p):
    p.text("Tiny Comet Prints", W / 2, 2120, 26, bold=False, anchor="m")


def draw_thing(p, name, x, y, h, flip=False):
    if name in CHARACTERS:
        return draw_char(p, name, x, y, h, flip=flip)
    return draw_prop(p, name, x, y, h, flip=flip)


# ---------------------------------------------------------------- scenery
def scene_decor(p, theme, rng, keep_out, ground=True, bubbles=True, small=False):
    """Line-art scenery for the theme's scene. keep_out: list of boxes to avoid."""
    scene = theme.get("scene", "meadow")
    avoid = list(keep_out)
    top_y = FR[1] + 150
    if scene in ("meadow", "farm", "forest", "jungle", "town", "party", "snow"):
        xs = [340, 1290] if rng.random() < .5 else [400, 1250]
        for i, x in enumerate(xs):
            s = .9 if i == 0 else .75
            if scene == "party":
                draw_prop(p, "balloon", x, top_y + 60, 300)
                avoid.append((x - 120, top_y - 110, x + 120, top_y + 220))
            elif scene == "snow":
                draw_prop(p, "snowflake", x, top_y + 10, 170)
                avoid.append((x - 100, top_y - 100, x + 100, top_y + 100))
            else:
                p.cloud(x, top_y, s)
                avoid.append((x - 150 * s - 30, top_y - 120 * s, x + 150 * s + 30, top_y + 100 * s))
    elif scene == "ocean":
        for x in (300, 1400):
            draw_prop(p, "seaweed", x, 1700, 520)
            avoid.append((x - 140, 1430, x + 140, 1930))
    elif scene == "space":
        draw_prop(p, "planet", 360, top_y + 40, 260)
        draw_prop(p, "moon", 1350, top_y + 30, 230)
        avoid += [(200, top_y - 120, 520, top_y + 180), (1240, top_y - 110, 1460, top_y + 160)]

    if ground:
        if scene in ("meadow", "farm", "party", "town"):
            p.bush(150, 1860, 3, 45)
            p.bush(1330, 1860, 3, 45)
            p.grass(560, 1900)
            p.grass(1010, 1900)
            avoid += [(130, 1790, 440, 1930), (1310, 1790, 1600, 1930)]
        elif scene == "forest":
            draw_prop(p, "mushroom", 260, 1790, 230)
            draw_prop(p, "mushroom", 1450, 1810, 180)
            p.grass(560, 1900)
            p.grass(1010, 1900)
            avoid += [(130, 1650, 400, 1930), (1340, 1690, 1580, 1930)]
        elif scene == "jungle":
            draw_prop(p, "tree", 230, 1700, 420)
            draw_prop(p, "flower", 1460, 1780, 260)
            avoid += [(110, 1480, 380, 1930), (1360, 1640, 1560, 1930)]
        elif scene == "snow":
            draw_prop(p, "pine", 240, 1720, 380)
            draw_prop(p, "pine", 1470, 1750, 320)
            avoid += [(110, 1520, 380, 1930), (1360, 1580, 1590, 1930)]
        elif scene == "ocean":
            draw_prop(p, "shell", 600, 1860, 120)
            draw_prop(p, "rock", 1150, 1870, 120)
            avoid += [(520, 1790, 680, 1930), (1080, 1800, 1230, 1930)]
    if bubbles:
        p.bubbles(avoid, n=26 if not small else 14, ring=(scene != "space"))


# ---------------------------------------------------------------- page types
def coloring(p, theme, rng, n):
    chars = theme["characters"]
    props = theme.get("props", [])
    k = len(chars)
    hero = chars[(n * 5) % k] if k not in (5,) else chars[(n * 3) % k]
    buddy = chars[(n * 5 + 1 + n // k) % k]
    if buddy == hero:
        buddy = chars[(chars.index(hero) + 1) % k]
    variant = n % 5
    big_props = [x for x in props if x in ("barn", "house", "tree", "pine", "xmastree", "rocket", "train", "truck", "car", "boat", "cake", "planet")] or props
    keep = []
    H_, X_ = cap(hero), cap(buddy)
    where = theme.get("place", "the " + theme.get("scene", "meadow"))
    if variant == 1 and big_props:
        bp = big_props[n % len(big_props)]
        header(p, f"{H_} and the {cap(bp)}", f"Color the {hero} and the big {bp}!")
        side = 1 if n % 2 else -1
        draw_prop(p, bp, CX + side * 330, 1150, 820)
        draw_thing(p, hero, CX - side * 260, 1350, 900, flip=side > 0)
        keep = [(CX - 760, 680, CX + 760, 1830)]
    elif variant == 2:
        header(p, f"{H_} and {X_}", theme.get("coloring_line", "Color these best friends!"))
        draw_thing(p, hero, 560, 1270, 820)
        draw_thing(p, buddy, 1150, 1330, 700, flip=True)
        keep = [(220, 820, 1500, 1800)]
    elif variant == 3:
        header(p, f"{H_} Says Hello!", f"Color the {hero} and its little friend in {where}.")
        draw_thing(p, hero, CX - 120, 1240, 1000)
        draw_thing(p, buddy, CX + 470, 1580, 430, flip=True)
        keep = [(CX - 600, 680, CX + 700, 1830)]
    elif variant == 4:
        header(p, f"A Happy {H_}", f"Use lots of colors on this big {hero}!")
        draw_thing(p, hero, CX, 1200, 1320)
        keep = [(CX - 560, 500, CX + 560, 1880)]
    else:
        header(p, f"Color the {H_}", rng.choice([
            f"Color the happy {hero} and the world around it.",
            f"Give the {hero} your favorite colors!",
            f"Can you color the {hero} and everything around it?"]))
        draw_thing(p, hero, CX, 1260, 1100)
        keep = [(CX - 470, 1260 - 640, CX + 470, 1260 + 520)]
        if props:
            pr = props[n % len(props)]
            side = 1 if n % 2 else -1
            px = CX + side * 560
            draw_prop(p, pr, px, 1640, 300)
            keep.append((px - 170, 1460, px + 170, 1800))
    scene_decor(p, theme, rng, keep)
    p.wobbly_frame(*FR)


def color_by_number(p, theme, rng, n):
    chars = theme["characters"]
    hero = chars[(n * 2 + 1) % len(chars)]
    header(p, f"{cap(hero)} Color by Number", "Use the key at the bottom of the page to color the picture.")
    # ground hill
    hill = [(110, 1830), (300, 1780), (560, 1752), (850, 1766), (1130, 1752), (1400, 1780), (1590, 1830)]
    c = p.c
    c.save()
    c.rectangle(FR[0], FR[1], FR[2] - FR[0], FR[3] - FR[1])
    c.clip()
    p.blob(hill + [(1590, 1960), (110, 1960)], WHITE)
    c.restore()
    p.labels = []
    draw_char(p, hero, CX, 1240, 1050)
    entries = [(nm, x, y) for (k, x, y, nm) in p.labels if nm and nm != "white"]
    props = theme.get("props", [])
    if props:
        pr = props[n % len(props)]
        for x in (300, 1400):
            p.labels = []
            draw_prop(p, pr, x, 1560, 300)
            entries += [(nm, lx, ly) for (k, lx, ly, nm) in p.labels if nm and nm != "white"]
    p.labels = []
    sky = theme.get("sky_colour", "lightblue")
    for (x, y) in [(300, 560), (850, 520), (1400, 560), (240, 1050), (1460, 1050), (480, 820), (1220, 820)]:
        entries.append((sky, x, y))
    for (x, y) in [(560, 1860), (850, 1880), (1140, 1860), (250, 1870), (1450, 1870)]:
        entries.append(("green", x, y))
    names = []
    for e in entries:
        if e[0] not in names:
            names.append(e[0])
    names = names[:9]
    num = {nm: i + 1 for i, nm in enumerate(names)}
    placed = []
    for (nm, x, y) in entries:
        if nm not in num:
            continue
        if any((x - a) ** 2 + (y - b) ** 2 < 75 ** 2 for a, b in placed):
            continue
        placed.append((x, y))
        p.text(str(num[nm]), x, y + 17, 46, anchor="m")
    p.wobbly_frame(*FR)
    key = [f"{i + 1}. {NICE.get(nm, nm)}" for i, nm in enumerate(names)]
    lines = [key[i:i + 4] for i in range(0, len(key), 4)]
    for li, ln in enumerate(lines):
        p.text("     ".join(ln), W / 2, 2020 + li * 58, 40, bold=False, anchor="m")


def maze(p, theme, rng, n):
    chars = theme["characters"]
    props = theme.get("props", []) or ["star"]
    hero = chars[(n + 2) % len(chars)]
    goal = theme.get("maze_goals", props)[n % len(theme.get("maze_goals", props))]
    header(p, f"Help the {cap(hero)} Find the {cap(goal)}", f"Draw a path from the {hero} to the {goal}.")
    p.wobbly_frame(*FR)
    cols, rows = [(8, 9), (9, 10), (10, 11)][n % 3]
    cs = min(1300 / cols, 1300 / rows)
    mx0 = CX - cols * cs / 2
    my0 = 470 + (1380 - rows * cs) / 2
    wh = [[True] * cols for _ in range(rows + 1)]
    wv = [[True] * (cols + 1) for _ in range(rows)]
    seen = [[False] * cols for _ in range(rows)]
    stack = [(0, 0)]
    seen[0][0] = True
    while stack:
        r, c = stack[-1]
        nb = [(r + dr, c + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
              if 0 <= r + dr < rows and 0 <= c + dc < cols and not seen[r + dr][c + dc]]
        if not nb:
            stack.pop()
            continue
        nr, nc = rng.choice(nb)
        if nr == r + 1:
            wh[nr][c] = False
        elif nr == r - 1:
            wh[r][c] = False
        elif nc == c + 1:
            wv[r][nc] = False
        else:
            wv[r][c] = False
        seen[nr][nc] = True
        stack.append((nr, nc))
    wh[0][0] = False
    wh[rows][cols - 1] = False
    lw = p.lw
    p.lw = 12
    for r in range(rows + 1):
        for c in range(cols):
            if wh[r][c]:
                p.line([(mx0 + c * cs, my0 + r * cs), (mx0 + (c + 1) * cs, my0 + r * cs)])
    for r in range(rows):
        for c in range(cols + 1):
            if wv[r][c]:
                p.line([(mx0 + c * cs, my0 + r * cs), (mx0 + c * cs, my0 + (r + 1) * cs)])
    p.lw = lw
    draw_thing(p, hero, mx0 + cs / 2, my0 + cs / 2, cs * .82)
    p.text("START", mx0 + cs / 2, my0 - 18, 32, anchor="m")
    draw_thing(p, goal, mx0 + (cols - .5) * cs, my0 + (rows - .5) * cs, cs * .78)
    p.text("FINISH", mx0 + (cols - .5) * cs, my0 + rows * cs + 48, 32, anchor="m")


def counting(p, theme, rng, n):
    chars = theme["characters"]
    hero = chars[(n + 3) % len(chars)]
    count = rng.randint(5, 9) if n % 2 else rng.randint(3, 7)
    header(p, f"Count the {plural(hero)}", f"How many {plural(hero).lower()} do you see? Circle the right number.")
    spots = []
    tries = 0
    while len(spots) < count and tries < 4000:
        tries += 1
        x = rng.uniform(330, 1370)
        y = rng.uniform(640, 1500)
        if all((x - a) ** 2 + (y - b) ** 2 > 330 ** 2 for a, b in spots):
            spots.append((x, y))
    count = len(spots)
    for i, (x, y) in enumerate(spots):
        draw_thing(p, hero, x, y, rng.uniform(260, 320), flip=bool(i % 2))
    opts = sorted(set([count] + rng.sample([v for v in range(2, 11) if v != count], 3)))
    for i, v in enumerate(opts):
        x = 330 + i * 345
        p.circ(x, 1760, 95, WHITE)
        p.text(str(v), x, 1790, 86, anchor="m")
    p.wobbly_frame(*FR)


DOT_SHAPES = ["star", "heart", "fish", "balloon", "apple", "house", "rocket", "egg"]


def shape_points(name, n):
    """Return n points around an outline in page space (frame area)."""
    cx, cy, s = CX, 1150, 560
    if name == "star":
        pts = []
        for i in range(10):
            r = s if i % 2 == 0 else s * .45
            a = -math.pi / 2 + i * math.pi / 5
            pts.append((cx + math.cos(a) * r, cy + 60 + math.sin(a) * r))
        return resample(pts, n, closed=True)
    if name == "heart":
        pts = []
        for i in range(200):
            t = i / 200 * 2 * math.pi
            x = 16 * math.sin(t) ** 3
            y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
            pts.append((cx + x * 34, cy - y * 34))
        return resample(pts, n, closed=True)
    blobs = {
        "fish": [(-1, 0), (-.7, -.5), (0, -.6), (.55, -.3), (.95, -.65), (.9, 0), (.95, .65), (.55, .3), (0, .6), (-.7, .5)],
        "balloon": [(0, -1), (.55, -.8), (.7, -.25), (.4, .35), (0, .55), (.12, .7), (-.12, .7), (0, .55), (-.4, .35), (-.7, -.25), (-.55, -.8)],
        "apple": [(0, -.55), (.45, -.8), (.8, -.3), (.7, .45), (.35, .85), (0, .75), (-.35, .85), (-.7, .45), (-.8, -.3), (-.45, -.8)],
        "house": [(-.7, -.1), (0, -.9), (.7, -.1), (.55, -.1), (.55, .8), (-.55, .8), (-.55, -.1)],
        "rocket": [(0, -1), (.3, -.55), (.3, .35), (.6, .75), (.3, .7), (0, .85), (-.3, .7), (-.6, .75), (-.3, .35), (-.3, -.55)],
        "egg": [(0, -.95), (.5, -.55), (.65, .15), (.45, .7), (0, .88), (-.45, .7), (-.65, .15), (-.5, -.55)],
    }
    pts = [(cx + x * s, cy + y * s) for x, y in blobs[name]]
    return resample(pts, n, closed=True)


def resample(pts, n, closed=True):
    seg = list(zip(pts, pts[1:] + ([pts[0]] if closed else [])))
    lens = [math.dist(a, b) for a, b in seg]
    total = sum(lens)
    out = []
    for i in range(n):
        d = total * i / n
        for (a, b), L in zip(seg, lens):
            if d <= L:
                t = d / L if L else 0
                out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
                break
            d -= L
    return out


def dot_to_dot(p, theme, rng, n):
    shapes = theme.get("dot_shapes", DOT_SHAPES)
    shape = shapes[n % len(shapes)]
    count = [15, 20, 25][n % 3]
    header(p, f"Connect the Dots: {cap(shape)}", f"Draw a line from 1 to {count}, then color your picture.")
    pts = shape_points(shape, count)
    for i, (x, y) in enumerate(pts):
        p.dot(x, y, 15)
        dx, dy = x - CX, y - 1150
        d = math.hypot(dx, dy) or 1
        p.text(str(i + 1), x + dx / d * 52, y + dy / d * 52 + 15, 42, anchor="m")
    hero = theme["characters"][n % len(theme["characters"])]
    draw_thing(p, hero, 1340, 1680, 380)
    p.wobbly_frame(*FR)


def tracing(p, theme, rng, n):
    words = theme.get("words", [c.upper() for c in theme["characters"]])
    start = (n * 3) % len(words)
    pick = [words[(start + i) % len(words)] for i in range(3)]
    header(p, "Trace the Words", "Trace each word with your pencil, then write it on the line.")
    p.wobbly_frame(*FR)
    for i, wd in enumerate(pick):
        y0 = 470 + i * 485
        thing = wd.lower()
        if thing in CHARACTERS or thing in PROPS:
            draw_thing(p, thing, 330, y0 + 210, 330)
        else:
            draw_thing(p, theme["characters"][i % len(theme["characters"])], 330, y0 + 210, 330)
        size = p.fit_size(wd, 950, 170)
        p.outline_text(wd, 1030, y0 + 200, size, lw=4, dash=[14, 12])
        for yy, dash in ((y0 + 330, None), (y0 + 400, [18, 14])):
            p.line([(560, yy), (1500, yy)], lw=4, dash=dash)
        p.line([(560, y0 + 440), (1500, y0 + 440)], lw=5)


def spot_difference(p, theme, rng, n):
    header(p, "Find 5 Differences", "Look at both pictures. Circle 5 things missing in the bottom one.")
    chars = theme["characters"]
    props = theme.get("props", []) or ["star", "flower"]
    hero = chars[(n + 1) % len(chars)]
    items = [(hero, 850, 330, 470)]
    pool = [chars[(n + 2 + i) % len(chars)] for i in range(2)] + [props[i % len(props)] for i in range(6)]
    slots = [(290, 260, 250), (1410, 260, 250), (300, 520, 200), (1400, 520, 200), (560, 530, 170), (1140, 530, 170),
             (580, 170, 140), (1120, 170, 140)]
    for name, (x, y, h) in zip(pool, slots):
        items.append((name, x, y, h))
    missing = set(rng.sample(range(1, len(items)), 5))
    for panel, (y0, y1) in enumerate([(400, 1150), (1180, 1930)]):
        p.wobbly_frame(110, y0, 1590, y1)
        c = p.c
        c.save()
        c.rectangle(115, y0 + 5, 1470, y1 - y0 - 10)
        c.clip()
        for i, (name, x, y, h) in enumerate(items):
            if panel == 1 and i in missing:
                continue
            draw_thing(p, name, x, y0 + y + 20, h)
        p.line([(110, y0 + 640), (1590, y0 + 640)], lw=6)
        c.restore()


def matching(p, theme, rng, n):
    chars = theme["characters"]
    pick = [chars[(n + i) % len(chars)] for i in range(min(4, len(chars)))]
    if len(pick) < 4:
        pick += [theme.get("props", ["star"])[i % len(theme.get("props", ["star"]))] for i in range(4 - len(pick))]
    right = pick[:]
    while right == pick:
        rng.shuffle(right)
    header(p, "Match the Friends", "Draw a line to connect each picture with its twin.")
    p.wobbly_frame(*FR)
    for i in range(4):
        y = 620 + i * 350
        draw_thing(p, pick[i], 430, y, 290)
        p.dot(640, y, 16)
        draw_thing(p, right[i], 1270, y, 290, flip=True)
        p.dot(1060, y, 16)


def word_search(p, theme, rng, n):
    words = [w for w in theme.get("words", []) if 3 <= len(w) <= 9][:8]
    size = 11
    grid = [[None] * size for _ in range(size)]
    placed = []
    for wd in sorted(words, key=len, reverse=True):
        for _ in range(300):
            horiz = rng.random() < .55
            r = rng.randrange(size if horiz else size - len(wd) + 1)
            c = rng.randrange(size - len(wd) + 1 if horiz else size)
            cells = [(r, c + i) if horiz else (r + i, c) for i in range(len(wd))]
            if all(grid[a][b] in (None, wd[i]) for i, (a, b) in enumerate(cells)):
                for i, (a, b) in enumerate(cells):
                    grid[a][b] = wd[i]
                placed.append(wd)
                break
    letters = "ABCDEFGHIKLMNOPRSTUWY"
    header(p, f"{theme['title']} Word Search", "Find the words. They go across and down.")
    p.wobbly_frame(*FR)
    cs = 112
    x0 = CX - size * cs / 2
    y0 = 470
    for r in range(size):
        for c in range(size):
            ch = grid[r][c] or rng.choice(letters)
            p.text(ch, x0 + c * cs + cs / 2, y0 + r * cs + cs / 2 + 22, 60, anchor="m")
    yb = y0 + size * cs + 70
    for i, wd in enumerate(placed):
        x = 260 + (i % 4) * 340
        y = yb + (i // 4) * 80
        p.rrect(x - 30, y - 34, 34, 34, 6, WHITE, lw=4)
        p.text(wd, x + 20, y, 42)


def title_page(p, theme, rng):
    p.wobbly_frame(110, 110, 1590, 2090)
    p.text("This book belongs to", W / 2, 520, 92, anchor="m")
    p.line([(330, 760), (1370, 760)], lw=8)
    chars = theme["characters"]
    draw_char(p, chars[0], W / 2, 1380, 900)
    p.cloud(420, 1000, .8)
    p.cloud(1280, 960, .7)
    p.bubbles([(400, 850, 1300, 1900), (250, 880, 600, 1100), (1100, 840, 1460, 1080)], n=18, box=(180, 850, 1520, 1950))
    t = theme["title"] + " " + theme.get("cover_line", "Coloring & Activity Book")
    p.text(t, W / 2, 1990, p.fit_size(t, 1300, 44), anchor="m")


def thanks_page(p, theme, rng):
    p.wobbly_frame(110, 110, 1590, 2090)
    p.text("Great job!", W / 2, 520, 120, anchor="m")
    p.text("You finished the whole book.", W / 2, 640, 56, bold=False, anchor="m")
    chars = theme["characters"]
    draw_char(p, chars[1 % len(chars)], 600, 1180, 700)
    draw_char(p, chars[2 % len(chars)], 1120, 1230, 600, flip=True)
    for i, (x, y) in enumerate([(300, 820), (1400, 860), (850, 800)]):
        draw_prop(p, "star", x, y, 130)
    lines = ["Did you have fun? Grown-ups, a short review on Amazon",
             "helps our tiny studio make more books for kids.",
             "Thank you from Tiny Comet Prints!"]
    for i, ln in enumerate(lines):
        p.text(ln, W / 2, 1700 + i * 70, 44, bold=(i == 2), anchor="m")


def cap(s):
    return " ".join(w.capitalize() for w in s.replace("_", " ").split())


def plural(s):
    s = cap(s)
    if s.lower().endswith(("fish", "sheep", "deer")):
        return s
    if s.endswith(("sh", "ch", "x", "s")):
        return s + "es"
    if s.endswith("y") and s[-2] not in "aeiou":
        return s[:-1] + "ies"
    return s + "s"


# The order of the 30 activity pages in a book.
BOOK_PLAN = [
    "coloring", "coloring", "maze", "coloring", "color_by_number", "coloring", "tracing", "coloring",
    "counting", "coloring", "dot_to_dot", "coloring", "spot_difference", "coloring", "color_by_number",
    "coloring", "maze", "coloring", "matching", "coloring", "tracing", "coloring", "counting", "coloring",
    "dot_to_dot", "coloring", "word_search", "color_by_number", "maze", "spot_difference",
]

PAGE_TYPES = {
    "coloring": coloring, "color_by_number": color_by_number, "maze": maze, "counting": counting,
    "dot_to_dot": dot_to_dot, "tracing": tracing, "spot_difference": spot_difference,
    "matching": matching, "word_search": word_search,
}
