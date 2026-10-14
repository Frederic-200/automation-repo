"""Append the FredsDesk outro to a finished video with a 0.3 s whip transition.

    python3 append_outro.py MAIN.mp4 OUTRO.mp4 OUT.mp4

Video: xfade slideleft (0.3 s). Audio: main track fades out over the transition, outro SFX start with the transition.
"""
import json, subprocess, sys

main, outro, out = sys.argv[1:4]
T = .3
def dur(p): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip())
d0 = dur(main); off = d0 - T; delay = int(off * 1000)
fc = (f"[0:v]fps=30,format=yuv420p,setsar=1[v0];[1:v]fps=30,format=yuv420p,setsar=1[v1];[v0][v1]xfade=transition=slideleft:duration={T}:offset={off:.3f}[v];"
      f"[0:a]afade=t=out:st={off - .15:.3f}:d={T + .15}[a0];[1:a]volume=-1.5dB,adelay={delay}|{delay}[a1];[a0][a1]amix=inputs=2:normalize=0:duration=longest,volume=-1.8dB[a]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", main, "-i", outro, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out], check=True)
print("OK", out, round(dur(out), 2), "s")
