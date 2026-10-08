#!/usr/bin/env python3
"""Check a theme JSON before building. Usage: python3 kdp/engine/validate.py kdp/themes/queue/*.json"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from chars import CHARACTERS   # noqa: E402
from props import PROPS        # noqa: E402

SCENES = {"meadow", "farm", "forest", "jungle", "town", "party", "snow", "ocean", "space"}
DOTS = {"star", "heart", "fish", "balloon", "apple", "house", "rocket", "egg"}
REQUIRED = ["slug", "title", "kdp_subtitle", "scene", "characters", "props", "words", "description",
            "keywords", "categories", "back_lines"]


def validate(t):
    e = []
    for k in REQUIRED:
        if k not in t or t[k] in ("", [], None):
            e.append(f"missing field: {k}")
    if e:
        return e
    if t["scene"] not in SCENES:
        e.append(f"scene '{t['scene']}' not in {sorted(SCENES)}")
    if not 3 <= len(t["characters"]) <= 8:
        e.append("characters: need 3-8")
    for c in t["characters"] + t.get("cover_characters", []):
        if c not in CHARACTERS:
            e.append(f"unknown character '{c}'")
    for pr in t["props"] + t.get("cover_props", []) + t.get("maze_goals", []):
        if pr not in PROPS and pr not in CHARACTERS:
            e.append(f"unknown prop '{pr}'")
    for d in t.get("dot_shapes", []):
        if d not in DOTS:
            e.append(f"unknown dot shape '{d}' (use {sorted(DOTS)})")
    if len(t["keywords"]) != 7:
        e.append("keywords: need exactly 7")
    for k in t["keywords"]:
        if len(k) > 50:
            e.append(f"keyword too long (>50 chars): {k}")
    if not 1 <= len(t["categories"]) <= 3:
        e.append("categories: need 1-3")
    if len(t["title"]) > 22:
        e.append("title: keep it 22 characters or fewer (it must fit the cover)")
    words = [w for w in t["words"] if w.isalpha() and w.isupper()]
    if len(words) < 6:
        e.append("words: need at least 6 UPPERCASE single words (letters only)")
    if len(t["description"]) > 3800:
        e.append("description too long")
    return e


if __name__ == "__main__":
    bad = 0
    for path in sys.argv[1:]:
        with open(path) as f:
            errs = validate(json.load(f))
        if errs:
            bad += 1
            print(f"{path}: INVALID")
            for x in errs:
                print("  -", x)
        else:
            print(f"{path}: OK")
    sys.exit(1 if bad else 0)
