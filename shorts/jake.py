#!/usr/bin/env python3
"""Jake: the recurring FredsDesk character (format E, "Human wonder of AI").

Jake is an ORIGINAL invented character (a simple friendly bust drawn from shapes). He is never a real person.
He is stored here as code so every video draws him identically; only his expression changes.

    python3 shorts/jake.py shorts/queue/<file>.json        # copies the jake_* drawings used by the script into meta.art
    python3 shorts/jake.py --list                           # show the expressions

Expressions (art ids): jake_neutral jake_think jake_worried jake_surprised jake_happy jake_confused jake_blank
Use them like any other drawing in `bg.subject`, and change expression on a spoken word with a morph beat:
    {"on": "sued", "do": "jake_neutral.morph:jake_worried"}   (both ids must be listed as subjects or used in the script)
The validator does not count jake_* drawings toward the 2-6 drawing limit and skips the "drawings repeat" warning for them.
"""
import json, re, sys

SKIN, SKIN2, HAIR = "#f2c29b", "#e0a77c", "#2b2433"
WHITE, PUPIL, BLUSH, MOUTH = "#ffffff", "#1d1b26", "#ee9a8a", "#0b0b10"
SWEAT = "#7ec8ff"


def S(t, **k): d = {"t": t}; d.update(k); return d


def base():
    """body + head + hair (no face features)."""
    return [
        S("rect", x=86, y=112, w=28, h=40, r=8, c=SKIN2, sw=0),                                   # neck
        S("path", d="M22 200 Q22 150 64 140 L90 138 L100 158 L110 138 L136 140 Q178 150 178 200 Z", c="accent2"),   # shirt, V neck
        S("circle", x=55, y=90, r=10, c=SKIN, w=3),                                               # ears
        S("circle", x=145, y=90, r=10, c=SKIN, w=3),
        S("ellipse", x=100, y=88, rx=46, ry=50, c=SKIN, w=5),                                     # head
        S("path", d="M52 88 Q44 30 100 28 Q156 30 148 88 Q142 60 120 54 Q96 66 72 56 Q56 66 52 88 Z", c=HAIR, w=4),   # hair
        S("path", d="M90 32 Q104 10 128 22 Q112 26 108 40 Z", c=HAIR, w=3),                       # tuft
        S("circle", x=71, y=108, r=8, c=BLUSH, o=0.5, w=0),                                       # cheeks
        S("circle", x=129, y=108, r=8, c=BLUSH, o=0.5, w=0),
    ]


def eyes(lx=80, ly=91, rx_=120, ry=91, rw=10, rh=12, px=0, py=0, pr=5):
    return [S("ellipse", x=lx, y=ly, rx=rw, ry=rh, c=WHITE, w=3), S("ellipse", x=rx_, y=ry, rx=rw, ry=rh, c=WHITE, w=3),
            S("circle", x=lx + px, y=ly + py, r=pr, c=PUPIL, w=0), S("circle", x=rx_ + px, y=ry + py, r=pr, c=PUPIL, w=0)]


def brows(l, r): return [S("line", pts=l, c=HAIR, w=6), S("line", pts=r, c=HAIR, w=6)]


def mouth_line(d): return S("path", d=d, c=MOUTH, fill=False, w=5)


def build():
    A = {}
    A["jake_neutral"] = {"shapes": base() + eyes() + brows([[68, 72], [92, 70]], [[108, 70], [132, 72]]) + [mouth_line("M84 117 Q100 126 116 117")]}
    A["jake_think"] = {"shapes": base() + eyes(px=5, py=-5) + brows([[68, 74], [92, 68]], [[108, 60], [132, 66]]) + [mouth_line("M90 119 Q102 115 112 121"),
        S("circle", x=150, y=52, r=4, c="#ffffff", w=2), S("circle", x=162, y=40, r=6, c="#ffffff", w=2),
        S("ellipse", x=176, y=20, rx=20, ry=15, c="#ffffff", w=3), S("text", s="?", x=176, y=22, size=24, c="#2b2433")]}
    A["jake_worried"] = {"shapes": base() + eyes(py=3, pr=4) + brows([[66, 80], [92, 68]], [[108, 68], [134, 80]]) +
        [mouth_line("M84 124 Q92 115 100 121 Q108 127 116 118"), S("path", d="M152 56 Q160 70 152 78 Q144 70 152 56 Z", c=SWEAT, w=2)]}
    A["jake_surprised"] = {"shapes": base() + eyes(rw=12, rh=15, pr=3) + brows([[66, 64], [92, 57]], [[108, 57], [134, 64]]) +
        [S("ellipse", x=100, y=122, rx=8, ry=11, c=MOUTH, w=3),
         S("line", pts=[[100, 14], [100, 2]], c="gold", w=5), S("line", pts=[[74, 20], [64, 8]], c="gold", w=5), S("line", pts=[[126, 20], [136, 8]], c="gold", w=5)]}
    A["jake_happy"] = {"shapes": base() +
        [S("path", d="M69 94 Q80 80 91 94", c=PUPIL, fill=False, w=6), S("path", d="M109 94 Q120 80 131 94", c=PUPIL, fill=False, w=6)] +
        brows([[68, 70], [92, 66]], [[108, 66], [132, 70]]) +
        [S("path", d="M78 112 Q100 142 122 112 Z", c=MOUTH, w=3), S("path", d="M84 114 Q100 122 116 114 L114 118 Q100 126 86 118 Z", c=WHITE, w=0)]}
    A["jake_confused"] = {"shapes": base() + eyes(px=-4, py=2) + brows([[68, 66], [92, 72]], [[108, 74], [132, 66]]) +
        [mouth_line("M84 122 q8 -8 16 0 t16 0"), S("text", s="?", x=164, y=48, size=40, c="gold"), S("text", s="?", x=38, y=40, size=26, c="accent")]}
    A["jake_blank"] = {"shapes": base() +
        [S("ellipse", x=80, y=93, rx=10, ry=6, c=WHITE, w=3), S("ellipse", x=120, y=93, rx=10, ry=6, c=WHITE, w=3),
         S("circle", x=80, y=94, r=3, c=PUPIL, w=0), S("circle", x=120, y=94, r=3, c=PUPIL, w=0)] +
        brows([[68, 76], [92, 78]], [[108, 78], [132, 76]]) + [mouth_line("M88 122 L112 122"),
        S("text", s="...", x=100, y=8, size=30, c="accent3")]}
    for a in A.values():
        # ONE soft silhouette shadow under the whole bust (offset 5,7 like the sticker look) instead of a shadow per shape:
        # per-shape shadows on eyes, brows, hair and cheeks looked misplaced (user review 2026-10-24)
        sil = [S("path", d="M27 207 Q27 157 69 147 L141 147 Q183 157 183 207 Z", c="#000000", o=.30, w=0, keep=True, noshadow=True),
               S("ellipse", x=105, y=95, rx=46, ry=50, c="#000000", o=.30, w=0, keep=True, noshadow=True)]
        for sh in a["shapes"]: sh["noshadow"] = True; sh["edge"] = True    # outline follows the background (dark shade on dark scenes, near-black on light), mouth is black
        a["shapes"] = sil + a["shapes"]
    for a in A.values():                      # keep: the engine's automatic contrast fix must never recolour Jake (skin, eyes, hair stay identical in every video)
        for sh in a["shapes"]:
            if str(sh.get("c", "")).startswith("#"): sh["keep"] = True    # fixed colours only; theme-role pieces (shirt, ?, ...) still adapt to the palette
    return A


def used_ids(script):
    txt = json.dumps(script.get("scenes") or [])
    return sorted(set(re.findall(r"jake_[a-z]+", txt)) & set(build()))


def inject(script):
    lib = build(); meta = script.setdefault("meta", {}); art = meta.setdefault("art", {})
    for i in used_ids(script): art[i] = lib[i]
    return sorted(i for i in art if i.startswith("jake_"))


def main():
    a = sys.argv[1:]
    if not a or a[0] == "--list": print(__doc__); print(sorted(build())); return
    f = a[0]; S_ = json.load(open(f)); ids = inject(S_)
    json.dump(S_, open(f, "w"), indent=1, ensure_ascii=False); open(f, "a").write("\n")
    print("jake drawings in meta.art:", ids)


if __name__ == "__main__":
    main()
