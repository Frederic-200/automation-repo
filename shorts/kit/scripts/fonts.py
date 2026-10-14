"""Fetch the style's fonts from @fontsource (OFL/Apache, commercial OK) and copy the needed
weights into <work>/fonts/. Returns [{"family","weight","file"}] for the engine to load.

    python3 fonts.py WORK "Anton:400" "Inter:800"
"""
import glob, json, os, re, shutil, subprocess, sys

CACHE = os.environ.get("VIDEO_KIT_CACHE", os.path.expanduser("~/.cache/video-kit"))
NODE = os.path.join(CACHE, "node")


def slug(family): return re.sub(r"[^a-z0-9]+", "-", family.lower()).strip("-")


def ensure_package(family):
    d = os.path.join(NODE, "node_modules", "@fontsource", slug(family))
    if not os.path.isdir(d):
        os.makedirs(NODE, exist_ok=True)
        if not os.path.exists(os.path.join(NODE, "package.json")):
            open(os.path.join(NODE, "package.json"), "w").write('{"name":"video-kit-cache","private":true}')
        r = subprocess.run(["npm", "i", "-s", "--no-audit", "--no-fund", f"@fontsource/{slug(family)}"],
                           cwd=NODE, capture_output=True, text=True)
        if r.returncode != 0 or not os.path.isdir(d):
            return None
    return d


def pick_file(pkg, family, weight):
    s = slug(family)
    # basic "latin" subset only ("latin-ext" lacks A-Z)
    files = [f for f in glob.glob(os.path.join(pkg, "files", "*.woff2"))
             if re.search(rf"/{re.escape(s)}-latin-\d{{3}}-normal\.woff2$", f)]
    best = None
    for f in files:
        m = re.search(r"-(\d{3})-normal\.woff2$", f)
        if not m: continue
        w = int(m.group(1)); d = abs(w - weight)
        if best is None or d < best[0]: best = (d, w, f)
    return (best[1], best[2]) if best else (None, None)


def ensure_fonts(work, specs):
    """specs: list of (family, weight). Falls back to Inter/Anton when a family can't be fetched."""
    out_dir = os.path.join(work, "fonts"); os.makedirs(out_dir, exist_ok=True)
    result, seen = [], set()
    for fam, wt in specs:
        if (fam, wt) in seen: continue
        seen.add((fam, wt))
        pkg = ensure_package(fam); w, f = pick_file(pkg, fam, int(wt)) if pkg else (None, None)
        if not f:
            print(f"[fonts] {fam} {wt} unavailable -> fallback", file=sys.stderr)
            fb = "Anton" if wt < 600 and fam != "Inter" else "Inter"
            pkg = ensure_package(fb); w, f = pick_file(pkg, fb, int(wt))
            if not f: continue
        dst = os.path.join(out_dir, os.path.basename(f)); shutil.copyfile(f, dst)
        # register under the REQUESTED family name so the engine never changes its CSS strings
        result.append({"family": fam, "weight": w, "file": "fonts/" + os.path.basename(f)})
    return result


if __name__ == "__main__":
    work = sys.argv[1]
    specs = [(s.split(":")[0], int(s.split(":")[1]) if ":" in s else 400) for s in sys.argv[2:]]
    print(json.dumps(ensure_fonts(work, specs), indent=1))
