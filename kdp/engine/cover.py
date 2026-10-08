"""Full-wrap paperback cover (back + spine + front, with 0.125in bleed) as a print PDF,
plus a PNG preview of the front. Painted background is raster (soft watercolour look),
characters and lettering are vector on top."""
import math

import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from draw import Pen, col, hexc, WHITE, BLACK
from chars import draw_char
from props import draw_prop

U = 200            # drawing units per inch
BLEED = 0.125
TRIM_W, TRIM_H = 8.5, 11.0
PAPER_IN = {"white": 0.002252, "cream": 0.0025}
BG_DPI = 150

TITLE_COLOURS = ["#ff6b2c", "#ffc61a", "#3a86ff", "#9b5de5", "#2fbf71", "#ff4f8b"]


def spine_width(pages, paper="white"):
    return pages * PAPER_IN[paper]


def _noise(w, h, scale, seed):
    r = np.random.default_rng(seed)
    small = r.random((max(2, h // scale), max(2, w // scale))).astype("float32")
    im = Image.fromarray((small * 255).astype("uint8")).resize((w, h), Image.BICUBIC)
    im = im.filter(ImageFilter.GaussianBlur(max(1, scale / 4)))
    return np.asarray(im, dtype="float32") / 255.0


def _vgrad(h, w, stops):
    """stops: list of (t, hex)."""
    t = np.linspace(0, 1, h, dtype="float32")
    out = np.zeros((h, 3), dtype="float32")
    for ch in range(3):
        xs = [s[0] for s in stops]
        ys = [hexc(s[1])[ch] for s in stops]
        out[:, ch] = np.interp(t, xs, ys)
    return np.broadcast_to(out[:, None, :], (h, w, 3)).copy()


def _hill(img, base, amp, ph, c_top, c_bot, seed, w, h, freq=.9):
    x = np.arange(w, dtype="float32")[None, :]
    Y = np.arange(h, dtype="float32")[:, None]
    edge = base + amp * np.sin(x / w * 2 * math.pi * freq + ph) + amp * .35 * np.sin(x / w * 2 * math.pi * freq * 2.3 + ph * 2)
    m = (Y > edge).astype("float32")
    m = np.asarray(Image.fromarray((m * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(1.0)), dtype="float32")[..., None] / 255
    k = np.clip((Y - edge) / (h * .3), 0, 1)[..., None]
    colr = np.array(hexc(c_top))[None, None, :] * (1 - k) + np.array(hexc(c_bot))[None, None, :] * k
    colr = colr + ((_noise(w, h, 40, seed) - .5) * .12)[..., None] + ((_noise(w, h, 10, seed + 9) - .5) * .04)[..., None]
    return img * (1 - m) + np.clip(colr, 0, 1) * m


def _clouds(img, w, h, spots, alpha=.9, blur=10):
    cl = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(cl)
    for (cx, cy, s) in spots:
        for dx, dy, r in [(-120, 20, 70), (-40, -25, 95), (60, -5, 85), (140, 25, 62), (0, 40, 90)]:
            d.ellipse((cx + (dx - r) * s, cy + (dy - r) * s, cx + (dx + r) * s, cy + (dy + r) * s), fill=255)
    cl = cl.filter(ImageFilter.GaussianBlur(blur))
    a = (np.asarray(cl, dtype="float32") / 255 * alpha)[..., None]
    return img * (1 - a) + a


def background(scene, w, h, seed):
    """Painted background as an RGB uint8 array (w x h pixels)."""
    rng = np.random.default_rng(seed)
    s = h / 1700  # scale factor for hand-tuned sizes (h ~ 1690 at 150dpi)
    if scene == "ocean":
        img = _vgrad(h, w, [(0, "#8fe0ff"), (.5, "#3fb3e8"), (1, "#1f7fc8")])
        img += ((_noise(w, h, 120, seed) - .5) * .12)[..., None]
        for i in range(6):   # light rays
            x0 = rng.uniform(0, w)
            ray = Image.new("L", (w, h), 0)
            ImageDraw.Draw(ray).polygon([(x0, 0), (x0 + 120 * s, 0), (x0 + 380 * s, h), (x0 + 160 * s, h)], fill=255)
            a = (np.asarray(ray.filter(ImageFilter.GaussianBlur(40 * s)), dtype="float32") / 255 * .12)[..., None]
            img = img * (1 - a) + a
        img = _hill(img, h * .86, h * .02, 1.0, "#ffe2a6", "#f1c27a", seed + 3, w, h, freq=1.6)
    elif scene == "space":
        img = _vgrad(h, w, [(0, "#1b1d4f"), (.6, "#2c2a6e"), (1, "#3d2f7d")])
        neb = _noise(w, h, 260, seed)
        img += (np.clip(neb - .5, 0, 1) * .5)[..., None] * np.array(hexc("#c86bff"))[None, None, :]
        star = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(star)
        for _ in range(int(w * h / 9000)):
            x, y, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(1, 3.2) * s
            d.ellipse((x - r, y - r, x + r, y + r), fill=int(rng.uniform(140, 255)))
        a = (np.asarray(star, dtype="float32") / 255)[..., None]
        img = img * (1 - a) + a
    elif scene == "snow":
        img = _vgrad(h, w, [(0, "#a9dcff"), (.6, "#e3f4ff"), (1, "#f4fbff")])
        img += ((_noise(w, h, 150, seed) - .5) * .08)[..., None]
        img = _clouds(img, w, h, [(w * .15, h * .6, s), (w * .55, h * .55, s * .8), (w * .85, h * .63, s * .9)], .8, 14 * s)
        img = _hill(img, h * .74, h * .035, .5, "#ffffff", "#d6ecff", seed + 1, w, h)
        img = _hill(img, h * .86, h * .03, 2.1, "#ffffff", "#e6f3ff", seed + 2, w, h, freq=1.3)
        snow = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(snow)
        for _ in range(int(w * h / 14000)):
            x, y, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(3, 7) * s
            d.ellipse((x - r, y - r, x + r, y + r), fill=230)
        a = (np.asarray(snow.filter(ImageFilter.GaussianBlur(1.2)), dtype="float32") / 255)[..., None]
        img = img * (1 - a) + a
    elif scene == "party":
        img = _vgrad(h, w, [(0, "#ffd6ec"), (.55, "#fff1c9"), (1, "#ffe2b8")])
        img += ((_noise(w, h, 150, seed) - .5) * .08)[..., None]
        conf = np.zeros((h, w, 3), dtype="float32")
        mask = Image.new("L", (w, h), 0)
        cimg = Image.new("RGB", (w, h), (0, 0, 0))
        d = ImageDraw.Draw(cimg)
        dm = ImageDraw.Draw(mask)
        pal = ["#ff6b6b", "#4aa8ff", "#ffd93b", "#5cc95a", "#a77bff", "#ff9a2e"]
        for _ in range(int(w * h / 12000)):
            x, y = rng.uniform(0, w), rng.uniform(0, h)
            r = rng.uniform(5, 11) * s
            c = tuple(int(v * 255) for v in hexc(pal[rng.integers(len(pal))]))
            d.ellipse((x - r, y - r, x + r, y + r), fill=c)
            dm.ellipse((x - r, y - r, x + r, y + r), fill=200)
        a = (np.asarray(mask, dtype="float32") / 255)[..., None]
        img = img * (1 - a) + (np.asarray(cimg, dtype="float32") / 255) * a
        img = _hill(img, h * .86, h * .02, 1.4, "#9bdc74", "#6fc558", seed + 2, w, h)
    else:   # meadow, farm, forest, jungle, town
        img = _vgrad(h, w, [(0, "#6cc4f2"), (.62, "#d8f1fc"), (1, "#e9f8ff")])
        img += ((_noise(w, h, 200, seed) - .5) * .16 + (_noise(w, h, 60, seed + 1) - .5) * .05)[..., None]
        img = _clouds(img, w, h, [(w * .12, h * .55, s), (w * .42, h * .62, s * .8), (w * .7, h * .5, s * .9), (w * .9, h * .66, s * .7)], .85, 12 * s)
        top = {"forest": ("#7cc96a", "#4aa54c"), "jungle": ("#5fbf5a", "#2f9a4a")}.get(scene, ("#9bdc74", "#6fc558"))
        bot = {"forest": ("#4fb150", "#2e8f42"), "jungle": ("#3fae45", "#23803c")}.get(scene, ("#6fcd55", "#3fae45"))
        img = _hill(img, h * .68, h * .04, .4, top[0], top[1], seed + 2, w, h)
        img = _hill(img, h * .8, h * .035, 2.2, bot[0], bot[1], seed + 3, w, h)
        if scene == "town":
            road = Image.new("L", (w, h), 0)
            ImageDraw.Draw(road).rectangle((0, h * .9, w, h), fill=255)
            a = (np.asarray(road.filter(ImageFilter.GaussianBlur(2)), dtype="float32") / 255)[..., None]
            img = img * (1 - a) + np.array(hexc("#6b7380"))[None, None, :] * a
    return (np.clip(img, 0, 1) * 255).astype("uint8")


def chunky_title(p, text, cx, base, size, off=0):
    c = p.c
    p.font(size, True)
    adv = [c.text_extents(ch).x_advance for ch in text]
    x = cx - sum(adv) / 2
    for i, ch in enumerate(text):
        if ch == " ":
            x += adv[i]
            continue
        colr = hexc(TITLE_COLOURS[(i + off) % len(TITLE_COLOURS)])
        y = base + math.sin(i * 1.3 + off) * size * .03
        c.move_to(x, y)
        c.text_path(ch)
        c.set_source_rgb(*BLACK)
        c.set_line_width(size * .085)
        c.stroke_preserve()
        c.set_source_rgb(*WHITE)
        c.set_line_width(size * .04)
        c.stroke_preserve()
        c.set_source_rgb(*colr)
        c.fill()
        x += adv[i]


def outlined_label(p, text, cx, base, size, fill="#e0521f", outline=WHITE, ow=.24):
    c = p.c
    p.font(size, True)
    adv = c.text_extents(text).x_advance
    c.move_to(cx - adv / 2, base)
    c.text_path(text)
    c.set_source_rgb(*outline)
    c.set_line_width(size * ow)
    c.stroke_preserve()
    c.set_source_rgb(*hexc(fill) if isinstance(fill, str) else fill)
    c.fill()


def split_title(t):
    words = t.split()
    if len(t) <= 10 or len(words) == 1:
        return [t]
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        score = max(len(a), len(b))
        if best is None or score < best[0]:
            best = (score, [a, b])
    return best[1]


def draw_front(p, theme, dark_bg):
    """Front cover art in a 1700 x 2200 trim box (origin top-left of trim)."""
    lines = split_title(theme["title"])
    max_len = max(len(l) for l in lines)
    size = min(330, int(1500 / (max_len * .62)))
    top = 150 if len(lines) == 2 else 260
    base = top
    for i, ln in enumerate(lines):
        sz = p.fit_size(ln, 1480, size)
        base = top + sz * .78 + i * size * .98
        chunky_title(p, ln, 850, base, sz, off=i * 2)
    y_after = base
    line2 = theme.get("cover_line", "Coloring & Activity Book")
    outlined_label(p, line2, 850, y_after + 150, p.fit_size(line2, 1350, 92), fill="#e0521f" if not dark_bg else "#ffd93b",
                   outline=WHITE if not dark_bg else (0.1, 0.1, 0.25))
    p.lw = 6
    age = theme.get("age_line", "For Kids Ages 4-8")
    pw = p.text_w(age, 64) + 160
    p.rrect(850 - pw / 2, y_after + 200, pw, 105, 52, hexc("#2b3a8f"))
    p.text(age, 850, y_after + 275, 64, anchor="m", rgb=WHITE)
    # size badge (beside the age pill, clear of the title)
    by = y_after + 250
    p.circ(1480, by, 105, hexc("#2b3a8f"))
    p.text("Large", 1480, by - 22, 40, anchor="m", rgb=WHITE)
    p.text("Size", 1480, by + 22, 40, anchor="m", rgb=WHITE)
    p.text("8.5 x 11", 1480, by + 66, 30, bold=False, anchor="m", rgb=WHITE)
    # characters
    p.lw = 11
    p.colour = True
    chars = theme.get("cover_characters", theme["characters"])[:3]
    props = theme.get("cover_props", theme.get("props", []))[:2]
    if len(props) > 0:
        draw_prop(p, props[0], 170, 1880, 330)
    if len(props) > 1:
        draw_prop(p, props[1], 1560, 1640, 300)
    spots = [(560, 1560, 860, False), (1240, 1600, 720, True), (930, 1900, 440, False)]
    for name, (x, yy, h, fl) in zip(chars, spots):
        draw_char(p, name, x, yy, h, flip=fl)
    p.colour = False


def draw_back(p, theme, dark_bg):
    """Back cover (1700 x 2200 trim box)."""
    txt = WHITE if dark_bg else hexc("#1f2a5a")
    p.c.set_source_rgba(1, 1, 1, .55 if not dark_bg else 0)
    p.rrect_path(140, 260, 1420, 1020, 60)
    p.c.fill()
    p.text(theme.get("back_headline", "Hours of Coloring Fun!"), 850, 410, p.fit_size(theme.get("back_headline", "Hours of Coloring Fun!"), 1300, 84), anchor="m", rgb=txt)
    y = 520
    for ln in theme.get("back_lines", []):
        p.text(ln, 850, y, p.fit_size(ln, 1300, 46, bold=False), bold=False, anchor="m", rgb=txt)
        y += 66
    y += 30
    for b in theme.get("back_bullets", ["30 fun pages to color and solve", "Mazes, counting, dot-to-dot and more",
                                        "Single-sided pages, no bleed-through", "Big 8.5 x 11 inch pages"]):
        p.c.set_source_rgb(*hexc("#ff6b2c"))
        p.poly(p.star_pts(300, y - 16, 22), hexc("#ffc61a"), lw=4)
        p.text(b, 350, y, p.fit_size(b, 1150, 46), anchor="l", rgb=txt)
        y += 78
    p.colour = True
    p.lw = 10
    chars = theme["characters"]
    draw_char(p, chars[-1], 470, 1660, 620)
    p.colour = False
    p.text("Tiny Comet Prints", 470, 2080, 46, anchor="m", rgb=txt)


def build_cover(theme, pages, out_pdf, out_png, paper="white", seed=1):
    sp = spine_width(pages, paper)
    W_in = BLEED * 2 + TRIM_W * 2 + sp
    H_in = TRIM_H + BLEED * 2
    scene = theme.get("scene", "meadow")
    dark = scene == "space"
    bgw, bgh = int(W_in * BG_DPI), int(H_in * BG_DPI)
    bg = background(scene, bgw, bgh, seed)
    bg_rgba = np.dstack([bg[..., 2], bg[..., 1], bg[..., 0], np.full(bg.shape[:2], 255, np.uint8)]).copy()
    bg_surf = cairo.ImageSurface.create_for_data(bg_rgba, cairo.FORMAT_RGB24, bgw, bgh)

    def paint(ctx, unit_scale):
        ctx.save()
        ctx.scale(unit_scale * U / BG_DPI, unit_scale * U / BG_DPI)
        ctx.set_source_surface(bg_surf, 0, 0)
        ctx.get_source().set_filter(cairo.FILTER_BEST)
        ctx.paint()
        ctx.restore()
        ctx.save()
        ctx.scale(unit_scale, unit_scale)
        # spine band
        sx0 = (BLEED + TRIM_W) * U
        ctx.set_source_rgb(*hexc(theme.get("spine_colour", "#2b3a8f")))
        ctx.rectangle(sx0, 0, sp * U, H_in * U)
        ctx.fill()
        # back panel (trim origin)
        ctx.save()
        ctx.translate(BLEED * U, BLEED * U)
        p = Pen(ctx, seed=seed, lw=8)
        draw_back(p, theme, dark)
        ctx.restore()
        # front panel
        ctx.save()
        ctx.translate((BLEED + TRIM_W + sp) * U, BLEED * U)
        p = Pen(ctx, seed=seed, lw=8)
        draw_front(p, theme, dark)
        ctx.restore()
        ctx.restore()

    surf = cairo.PDFSurface(out_pdf, W_in * 72, H_in * 72)
    ctx = cairo.Context(surf)
    paint(ctx, 72 / U)
    surf.finish()

    # front preview PNG (trim only) at 100 dpi
    pw, ph = int(TRIM_W * 100), int(TRIM_H * 100)
    img = cairo.ImageSurface(cairo.FORMAT_RGB24, pw, ph)
    ctx = cairo.Context(img)
    ctx.translate(-(BLEED + TRIM_W + sp) * 100, -BLEED * 100)
    paint(ctx, 100 / U)
    img.write_to_png(out_png)
    return {"width_in": round(W_in, 4), "height_in": H_in, "spine_in": round(sp, 4)}
