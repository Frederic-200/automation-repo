#!/usr/bin/env python3
"""One still per scene (plus mid-scene and keyword moments) so the writer can LOOK at the backgrounds before committing.
    python3 shorts/bg_preview.py shorts/queue/<file>.json [outdir]
Prints the path of contact.png: open it with the Read tool and fix anything weak, unreadable or off-story."""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
f = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else os.path.join("/tmp", "bg_preview")
S = json.load(open(f)); rec = (S.get("meta") or {}).get("recipe") or {}
r = subprocess.run([sys.executable, os.path.join(HERE, "recipe_test.py"), f, out, json.dumps(rec) if rec else "full", "--preview"], capture_output=True, text=True)
print(r.stdout[-600:] + r.stderr[-600:])
print("CONTACT SHEET:", os.path.join(out, "contact.png"))
