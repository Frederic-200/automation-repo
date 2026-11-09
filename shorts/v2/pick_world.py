#!/usr/bin/env python3
"""Pick today's world + palette (+ voice, music, hook type, ending) from the v2 history, so consecutive videos never share a look.

    python3 shorts/v2/pick_world.py --date 2026-11-12 [--reroll 0] [--log shorts/v2/novelty_log.json]

Rules (checked again by validate_v2.py): world differs from the last 2 videos; palette not used by that world in the last 4 videos;
voice differs from yesterday; music mood differs from yesterday; hook type differs from the last 2; ending alternates loop/cliffhanger.
--reroll N changes the deterministic tie-break (used when the novelty test says "too close").
"""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
WORLDS = {"a": ["ember", "cobalt", "moss", "plum"], "b": ["earth", "harbor", "blush"], "c": ["indigo", "teal"]}
VOICES = ["am_fenrir", "af_heart"]; MUSIC = ["gentle", "upbeat", "lofi", "epic", "synthwave"]
HOOK_TYPES = ["curiosity_gap", "doing_it_wrong", "pov", "myth_bust", "number_shock", "comment_reply"]
ENDINGS = ["loop", "cliffhanger"]


def rank(*key): return int(hashlib.sha256(json.dumps(key).encode()).hexdigest()[:8], 16)


def pick(date, reroll=0, entries=()):
    E = list(entries); last = lambda k, n: [e.get(k) for e in E[-n:]]
    pool = lambda opts, bad, tag: sorted([o for o in opts if o not in bad] or opts, key=lambda o: rank(date, reroll, tag, o))[0]
    world = pool(list(WORLDS), last("world", 2), "world")
    recent_pal = [e.get("palette") for e in E[-4:] if e.get("world") == world]
    palette = pool(WORLDS[world], recent_pal, "pal")
    ends = last("ending", 1); ending = ENDINGS[(ENDINGS.index(ends[0]) + 1) % 2] if ends and ends[0] in ENDINGS else pool(ENDINGS, [], "end")
    return {"world": world, "palette": palette, "voice": pool(VOICES, last("voice", 1), "voice"), "music": pool(MUSIC, last("music", 1), "music"),
            "hook_type": pool(HOOK_TYPES, last("hook_type", 2), "hook"), "ending": ending}


if __name__ == "__main__":
    a = sys.argv[1:]; opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    logp = opt("--log", os.path.join(HERE, "novelty_log.json")); E = json.load(open(logp))["entries"] if os.path.exists(logp) else []
    print(json.dumps(pick(opt("--date", "1970-01-01"), int(opt("--reroll", 0)), E)))
