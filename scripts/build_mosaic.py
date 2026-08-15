#!/usr/bin/env python3

import argparse
import shlex
import subprocess
from pathlib import Path


def run(cmd):
    print("+", " ".join(shlex.quote(str(x)) for x in cmd))
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser(
        description="Build the MeetingToM 2x2 close-up mosaic."
    )

    ap.add_argument("--closeup1", required=True)
    ap.add_argument("--closeup2", required=True)
    ap.add_argument("--closeup3", required=True)
    ap.add_argument("--closeup4", required=True)

    ap.add_argument("--audio", default=None)
    ap.add_argument("--output", required=True)

    ap.add_argument("--tile_width", type=int, default=640)
    ap.add_argument("--tile_height", type=int, default=360)

    ap.add_argument("--crf", type=int, default=23)
    ap.add_argument("--preset", default="veryfast")
    ap.add_argument("--ffmpeg", default="ffmpeg")

    args = ap.parse_args()

    closeups = [
        Path(args.closeup1),
        Path(args.closeup2),
        Path(args.closeup3),
        Path(args.closeup4),
    ]

    for p in closeups:
        if not p.is_file():
            raise FileNotFoundError(p)

    audio = Path(args.audio) if args.audio else None
    if audio is not None and not audio.is_file():
        raise FileNotFoundError(audio)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    w = args.tile_width
    h = args.tile_height

    fc = (
        f"[0:v]scale={w}:{h}[v0];"
        f"[1:v]scale={w}:{h}[v1];"
        f"[2:v]scale={w}:{h}[v2];"
        f"[3:v]scale={w}:{h}[v3];"
        f"[v0][v1][v2][v3]"
        f"xstack=inputs=4:"
        f"layout=0_0|w0_0|0_h0|w0_h0:"
        f"fill=black[v]"
    )

    cmd = [args.ffmpeg, "-y"]

    for p in closeups:
        cmd += ["-i", str(p)]

    if audio is not None:
        cmd += ["-i", str(audio)]

    cmd += [
        "-filter_complex", fc,
        "-map", "[v]",
    ]

    if audio is not None:
        cmd += [
            "-map", "4:a:0",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
        ]
    else:
        cmd += ["-an"]

    cmd += [
        "-c:v", "libx264",
        "-crf", str(args.crf),
        "-preset", args.preset,
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(out),
    ]

    run(cmd)

    print("[OK]", out)


if __name__ == "__main__":
    main()
