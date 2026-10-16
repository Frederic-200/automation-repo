"""script.json + voice.json + style.json -> timeline.json (everything the engine and audio need).

    python3 timeline.py script.json WORK

Scene acts (problem | build | turn | payoff | button) are taken from the script or inferred.
Scene types default to the style's `worlds` list. Keyword hits get strengths automatically
(override per scene with "hits": [1.2, .8, ...]).
"""
import json, os, sys

FLIP = {"but", "until", "instead", "yet", "now", "so", "then"}
ACT_BRIGHT = {"payoff", "button"}


def infer_acts(scenes):
    n = len(scenes); acts = []
    turn_done = False
    for i, sc in enumerate(scenes):
        if sc.get("act"): a = sc["act"]
        elif n >= 4 and i == n - 1: a = "button"
        else:
            p = i / max(1, n - 1)
            first = sc["lines"][0].replace("*", "").split()[0].lower().strip(",.") if sc["lines"] else ""
            if not turn_done and i > 0 and first in FLIP: a = "turn"
            elif p < .34: a = "problem"
            elif p < .5 and not turn_done: a = "build"
            elif not turn_done: a = "turn"
            else: a = "payoff"
        if a == "turn": turn_done = True
        acts.append(a)
    return acts


def build(script, style, voice, fps=30):
    scenes_in = script["scenes"]; acts = infer_acts(scenes_in); n = len(scenes_in)
    worlds = style.get("worlds", ["shapes"])
    default_for = {"problem": 0, "build": 1, "turn": 2, "payoff": 3}
    dur = voice["duration"]; out = []
    starts = []
    for i, vs in enumerate(voice["scenes"]):
        if i == 0: starts.append(0.0); continue
        s = vs["lines"][0]["s"] - .14
        s = max(s, voice["scenes"][i - 1]["voice_end"] + .05)
        starts.append(round(s, 3))
    for i, (sc, vs) in enumerate(zip(scenes_in, voice["scenes"])):
        act = acts[i]
        typ = sc.get("type") or ("burst" if act == "button" else worlds[min(default_for.get(act, i), len(worlds) - 1)])
        words = [w for ln in vs["lines"] for w in ln["words"]]
        keys = [dict(w) for w in words if w["k"]]
        # merge consecutive keyword words into one key (one hit)
        merged = []
        for k in keys:
            if merged and k["s"] - merged[-1]["e"] < .08: merged[-1]["e"] = k["e"]; merged[-1]["w"] += " " + k["w"]
            else: merged.append(k)
        custom = sc.get("hits")
        for j, k in enumerate(merged):
            base = .85
            if act == "turn": base = 1.25 if j == 0 else 1.0
            if act in ACT_BRIGHT: base = 1.0
            if j == len(merged) - 1 and act in ("turn", "payoff", "button"): base = max(base, 1.2)
            k["str"] = float(custom[j]) if custom and j < len(custom) else base
        end = starts[i + 1] if i + 1 < n else dur
        out.append({"i": i, "type": typ, "act": act, "start": starts[i], "end": round(end, 3),
                    "bright": act in ACT_BRIGHT, "params": sc.get("params", {}),
                    "keys": merged, "lines": vs["lines"]})
    # single biggest hit gets the impact frame
    allk = [k for s in out for k in s["keys"]]
    if allk:
        big = max(allk, key=lambda k: (k["str"], k["s"])); big["str"] = max(big["str"], 1.45); big["impact"] = 1
    # pre-turn near-silence marker (audio dips music, visuals hold)
    hits = []
    for s in out:
        if s["i"]: hits.append({"t": s["start"], "s": .5, "tr": 1})
        for k in s["keys"]: hits.append({"t": k["s"], "s": k["str"], "impact": k.get("impact", 0)})
    if script.get("hook"): hits.append({"t": .04, "s": .8, "open": 1})   # opening punch at frame 0 (zoom + shake + rgb split)
    hits.sort(key=lambda h: h["t"])
    trans = style.get("transitions", ["flash"])
    for s in out:
        s["transition"] = s.get("params", {}).get("transition") or (trans[(s["i"] - 1) % len(trans)] if s["i"] else "none")
    return {"title": script.get("title", ""), "fps": fps, "W": 1080, "H": 1920, "duration": round(dur, 3),
            "frames": int(round(dur * fps)), "seed": script.get("seed", style.get("seed", 7)),
            "scenes": out, "hits": hits, "music": {"bpm": 0, "beat0": 0}, "hook": script.get("hook")}


if __name__ == "__main__":
    script = json.load(open(sys.argv[1])); work = sys.argv[2]
    style = json.load(open(os.path.join(work, "style.json")))
    voice = json.load(open(os.path.join(work, "voice.json")))
    tl = build(script, style, voice)
    json.dump(tl, open(os.path.join(work, "timeline.json"), "w"), indent=1)
    for s in tl["scenes"]:
        print(f"{s['i']} {s['act']:7s} {s['type']:10s} {s['start']:6.2f}-{s['end']:6.2f}  keys={[k['w'] for k in s['keys']]}  ->{s['transition']}")
