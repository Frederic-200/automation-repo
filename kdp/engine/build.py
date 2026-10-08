#!/usr/bin/env python3
"""Build one complete KDP book from a theme JSON.

Usage: python3 kdp/engine/build.py kdp/themes/queue/001-farm-friends.json [--out kdp/output/x] [--previews]

Output folder:
  interior.pdf        print-ready interior (8.5x11, no bleed, B&W, single-sided pages)
  cover.pdf           print-ready full-wrap cover with bleed
  cover_front.png     front cover preview
  pages/NN-type.png   small previews of each activity page
  contact_sheet.png   all pages on one image
  listing.md          title, subtitle, description, keywords, categories, price, AI disclosure
  book.json           facts (page count, spine width, cover size)
"""
import json
import os
import random
import sys

import cairo
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from draw import Pen, W, H                    # noqa: E402
from pages import BOOK_PLAN, PAGE_TYPES, title_page, thanks_page  # noqa: E402
from cover import build_cover                 # noqa: E402
from validate import validate                 # noqa: E402

PT_W, PT_H = 612, 792      # US Letter in points


def render_page(ctx_fn, theme, kind, n, seed):
    rng = random.Random(seed)

    def draw(ctx):
        p = Pen(ctx, seed=seed)
        if kind == "title":
            title_page(p, theme, rng)
        elif kind == "thanks":
            thanks_page(p, theme, rng)
        else:
            PAGE_TYPES[kind](p, theme, rng, n)
    return draw


def build(theme_path, out_dir, previews=True):
    with open(theme_path) as f:
        theme = json.load(f)
    errs = validate(theme)
    if errs:
        raise SystemExit("Theme invalid:\n  " + "\n  ".join(errs))
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.join(out_dir, "pages"), exist_ok=True)
    base_seed = sum(ord(c) for c in theme["slug"]) * 97

    # sequence: title, blank, (activity, blank) x30, thanks, blank  -> 64 pages
    seq = [("title", 0)]
    counters = {}
    for kind in BOOK_PLAN:
        counters[kind] = counters.get(kind, -1) + 1
        seq.append((kind, counters[kind]))
    seq.append(("thanks", 0))

    pdf_path = os.path.join(out_dir, "interior.pdf")
    surf = cairo.PDFSurface(pdf_path, PT_W, PT_H)
    surf.set_metadata(cairo.PDF_METADATA_TITLE, theme["title"] + " " + theme.get("cover_line", ""))
    surf.set_metadata(cairo.PDF_METADATA_AUTHOR, "Tiny Comet Prints")
    ctx = cairo.Context(surf)
    total = 0
    thumbs = []
    for i, (kind, n) in enumerate(seq):
        seed = base_seed + i * 13
        draw = render_page(None, theme, kind, n, seed)
        ctx.save()
        ctx.scale(PT_W / W, PT_H / H)
        draw(ctx)
        ctx.restore()
        surf.show_page()
        total += 1
        surf.show_page()       # blank back side (single-sided printing)
        total += 1
        if previews:
            img = cairo.ImageSurface(cairo.FORMAT_RGB24, 850, 1100)
            ic = cairo.Context(img)
            ic.set_source_rgb(1, 1, 1)
            ic.paint()
            ic.scale(850 / W, 1100 / H)
            draw(ic)
            png = os.path.join(out_dir, "pages", f"{i:02d}-{kind}.png")
            img.write_to_png(png)
            thumbs.append(png)
    surf.finish()

    cover_info = build_cover(theme, total, os.path.join(out_dir, "cover.pdf"),
                             os.path.join(out_dir, "cover_front.png"), seed=base_seed)

    if previews:
        cols = 8
        rows = (len(thumbs) + 1 + cols - 1) // cols
        sheet = Image.new("RGB", (cols * 212, rows * 275), "white")
        imgs = [os.path.join(out_dir, "cover_front.png")] + thumbs
        for k, path in enumerate(imgs):
            im = Image.open(path).convert("RGB").resize((204, 264))
            sheet.paste(im, ((k % cols) * 212 + 4, (k // cols) * 275 + 5))
        sheet.save(os.path.join(out_dir, "contact_sheet.png"))

    facts = {"slug": theme["slug"], "title": theme["title"], "interior_pages": total,
             "activity_pages": len(BOOK_PLAN), "trim": "8.5 x 11 in", "bleed": "interior no bleed; cover 0.125 in",
             "paper": "white", "ink": "black & white interior", **{"cover_" + k: v for k, v in cover_info.items()}}
    with open(os.path.join(out_dir, "book.json"), "w") as f:
        json.dump(facts, f, indent=2)
    with open(os.path.join(out_dir, "listing.md"), "w") as f:
        f.write(listing_md(theme, facts))
    return facts


def listing_md(t, facts):
    kw = "\n".join(f"{i + 1}. {k}" for i, k in enumerate(t["keywords"][:7]))
    cats = "\n".join(f"- {c}" for c in t["categories"][:3])
    desc = t["description"].strip()
    return f"""# KDP listing kit - {t['title']} {t.get('cover_line', 'Coloring & Activity Book')}

Copy each field into KDP (Paperback > Create). Upload interior.pdf and cover.pdf from "3 Final KDP Files".

**Book title:** {t['title']} {t.get('cover_line', 'Coloring & Activity Book')}
**Subtitle:** {t['kdp_subtitle']}
**Series:** Tiny Comet Prints Coloring & Activity Books (optional)
**Author / Contributor:** Tiny Comet Prints
**Reading age:** 4 - 8 years
**Language:** English

## Description (paste into the description box)
{desc}

## 7 keyword slots
{kw}

## Categories (choose up to 3)
{cats}

## Print settings
- Ink and paper: Black & white interior with white paper
- Trim size: 8.5 x 11 in
- Bleed: No bleed (interior)
- Cover finish: Glossy
- Interior pages: {facts['interior_pages']} (spine {facts['cover_spine_in']} in; cover file {facts['cover_width_in']} x {facts['cover_height_in']} in)
- Low-content book: No (it has puzzles and activities)

## Rights, AI disclosure and price
- AI-generated content: **Yes - images** (all art is generated by code). Text: AI-assisted.
- Suggested list price: {t.get('price', '$7.99')} USD (check KDP's minimum for {facts['interior_pages']} pages)
- Territories: all
- Publish date: today; check the preview in KDP's Previewer before submitting.
"""


if __name__ == "__main__":
    args = sys.argv[1:]
    theme = args[0]
    out = args[args.index("--out") + 1] if "--out" in args else os.path.join("kdp", "output", os.path.splitext(os.path.basename(theme))[0])
    print(json.dumps(build(theme, out), indent=2))
