#!/usr/bin/env python3

import argparse
import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
MOSAIC_SCRIPT = SCRIPT_DIR / "build_mosaic.py"


def run(cmd):
    print("+", " ".join(shlex.quote(str(x)) for x in cmd))
    subprocess.run(cmd, check=True)


def load_records(path):
    records = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    return records


def resolve_video(ami_root, session_id, view):
    """
    Expected canonical AMI layout:

      AMI_ROOT/
        ES2002a/
          video/
            ES2002a.Closeup1.avi
            ES2002a.Closeup2.avi
            ES2002a.Closeup3.avi
            ES2002a.Closeup4.avi
            ES2002a.Corner.avi

    We intentionally prefer the non-_orig files.
    """

    ami_root = Path(ami_root)

    exact = (
        ami_root
        / session_id
        / "video"
        / f"{session_id}.{view}.avi"
    )

    if exact.is_file():
        return exact

    # Flexible fallback for differently nested AMI installations.
    matches = list(
        ami_root.glob(f"**/{session_id}.{view}.avi")
    )

    matches = [p for p in matches if "_orig" not in p.name]

    if len(matches) == 1:
        return matches[0]

    if not matches:
        raise FileNotFoundError(
            f"Cannot find {session_id}.{view}.avi "
            f"under {ami_root}"
        )

    raise RuntimeError(
        f"Ambiguous {view} video for {session_id}: "
        + ", ".join(str(p) for p in matches)
    )


def resolve_audio(ami_root, audio_root, session_id):
    """
    Resolve <session>.Mix-Headset.wav.

    Supports either:
      --audio_root /path/to/HeadsetAudio

    or audio stored inside the AMI directory.
    """

    filename = f"{session_id}.Mix-Headset.wav"

    roots = []

    if audio_root:
        roots.append(Path(audio_root))

    roots.append(Path(ami_root))

    candidates = []

    for root in roots:
        candidates.extend([
            root / filename,
            root / session_id / filename,
            root / session_id / "audio" / filename,
        ])

    for p in candidates:
        if p.is_file():
            return p

    # Flexible recursive fallback.
    for root in roots:
        matches = list(root.glob(f"**/{filename}"))

        if len(matches) == 1:
            return matches[0]

        if len(matches) > 1:
            raise RuntimeError(
                f"Ambiguous Mix-Headset audio for {session_id}: "
                + ", ".join(str(p) for p in matches)
            )

    raise FileNotFoundError(
        f"Cannot find {filename}. "
        f"Provide --audio_root if audio is stored separately."
    )


def cut_video_only(
    ffmpeg,
    video,
    start,
    duration,
    output,
    crf=23,
    preset="veryfast",
):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        ffmpeg,
        "-y",
        "-ss", str(start),
        "-i", str(video),
        "-t", str(duration),

        "-map", "0:v:0",
        "-an",

        "-c:v", "libx264",
        "-crf", str(crf),
        "-preset", preset,
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",

        str(output),
    ]

    run(cmd)


def cut_audio(
    ffmpeg,
    audio,
    start,
    duration,
    output,
):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        ffmpeg,
        "-y",
        "-ss", str(start),
        "-i", str(audio),
        "-t", str(duration),

        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",

        str(output),
    ]

    run(cmd)


def cut_video_with_audio(
    ffmpeg,
    video,
    audio,
    start,
    duration,
    output,
    crf=23,
    preset="veryfast",
):
    """
    Reconstruct a close-up clip carrying the shared
    Mix-Headset meeting audio.
    """

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        ffmpeg,
        "-y",

        "-ss", str(start),
        "-i", str(video),

        "-ss", str(start),
        "-i", str(audio),

        "-t", str(duration),

        "-map", "0:v:0",
        "-map", "1:a:0",

        "-c:v", "libx264",
        "-crf", str(crf),
        "-preset", preset,
        "-pix_fmt", "yuv420p",

        "-c:a", "aac",
        "-b:a", "128k",

        "-shortest",
        "-movflags", "+faststart",

        str(output),
    ]

    run(cmd)


def build_mosaic(
    closeups,
    audio,
    output,
    ffmpeg,
):
    cmd = [
        sys.executable,
        str(MOSAIC_SCRIPT),

        "--closeup1", str(closeups["Closeup1"]),
        "--closeup2", str(closeups["Closeup2"]),
        "--closeup3", str(closeups["Closeup3"]),
        "--closeup4", str(closeups["Closeup4"]),

        "--output", str(output),
        "--ffmpeg", ffmpeg,
    ]

    if audio is not None:
        cmd += ["--audio", str(audio)]

    run(cmd)


def reconstruct_state(
    rec,
    ami_root,
    audio_root,
    sample_root,
    ffmpeg,
):
    session_id = rec["session_id"]
    view = rec["target_view"]

    source_video = resolve_video(
        ami_root,
        session_id,
        view,
    )

    source_audio = resolve_audio(
        ami_root,
        audio_root,
        session_id,
    )

    media_dir = sample_root / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    window = rec["source_window"]

    cut_video_with_audio(
        ffmpeg,
        source_video,
        source_audio,
        window["start"],
        window["duration"],
        media_dir / "clip.mp4",
    )


def prepare_closeup_cuts(
    rec,
    ami_root,
    temp_dir,
    ffmpeg,
):
    session_id = rec["session_id"]

    start = rec["source_window"]["start"]
    duration = rec["source_window"]["duration"]

    outputs = {}

    for view in [
        "Closeup1",
        "Closeup2",
        "Closeup3",
        "Closeup4",
    ]:
        src = resolve_video(
            ami_root,
            session_id,
            view,
        )

        dst = temp_dir / f"{view}.mp4"

        cut_video_only(
            ffmpeg,
            src,
            start,
            duration,
            dst,
        )

        outputs[view] = dst

    return outputs


def prepare_audio_cut(
    rec,
    ami_root,
    audio_root,
    temp_dir,
    ffmpeg,
):
    session_id = rec["session_id"]

    src = resolve_audio(
        ami_root,
        audio_root,
        session_id,
    )

    dst = temp_dir / "Mix-Headset.wav"

    cut_audio(
        ffmpeg,
        src,
        rec["source_window"]["start"],
        rec["source_window"]["duration"],
        dst,
    )

    return dst


def reconstruct_you(
    rec,
    ami_root,
    audio_root,
    sample_root,
    ffmpeg,
    keep_temp,
):
    session_id = rec["session_id"]

    media_dir = sample_root / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    temp_dir = sample_root / "_tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    start = rec["source_window"]["start"]
    duration = rec["source_window"]["duration"]

    # Q1 = Corner + the same Mix-Headset audio source used by Q2.
    corner = resolve_video(
        ami_root,
        session_id,
        "Corner",
    )

    source_audio = resolve_audio(
        ami_root,
        audio_root,
        session_id,
    )

    cut_video_with_audio(
        ffmpeg,
        corner,
        source_audio,
        start,
        duration,
        media_dir / "Q1_corner.mp4",
    )

    # Q2 = 2x2 Closeup mosaic + Mix-Headset audio.
    closeups = prepare_closeup_cuts(
        rec,
        ami_root,
        temp_dir,
        ffmpeg,
    )

    audio = prepare_audio_cut(
        rec,
        ami_root,
        audio_root,
        temp_dir,
        ffmpeg,
    )

    build_mosaic(
        closeups,
        audio,
        media_dir / "Q2_mosaic.mp4",
        ffmpeg,
    )

    if not keep_temp:
        shutil.rmtree(temp_dir)


def reconstruct_consensus(
    rec,
    ami_root,
    audio_root,
    sample_root,
    ffmpeg,
    keep_temp,
):
    media_dir = sample_root / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    temp_dir = sample_root / "_tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    closeups = prepare_closeup_cuts(
        rec,
        ami_root,
        temp_dir,
        ffmpeg,
    )

    audio = prepare_audio_cut(
        rec,
        ami_root,
        audio_root,
        temp_dir,
        ffmpeg,
    )

    build_mosaic(
        closeups,
        audio,
        media_dir / "mosaic.mp4",
        ffmpeg,
    )

    if not keep_temp:
        shutil.rmtree(temp_dir)


def reconstruct_one(
    rec,
    ami_root,
    audio_root,
    output_dir,
    ffmpeg,
    keep_temp,
):
    task = rec["task"]
    bundle_name = rec["bundle_name"]

    sample_root = (
        Path(output_dir)
        / task
        / bundle_name
    )

    print()
    print("=" * 72)
    print("ID      :", rec["id"])
    print("TASK    :", task)
    print("SESSION :", rec["session_id"])
    print("OUTPUT  :", sample_root)

    if task == "state":
        reconstruct_state(
            rec,
            ami_root,
            audio_root,
            sample_root,
            ffmpeg,
        )

    elif task == "you":
        reconstruct_you(
            rec,
            ami_root,
            audio_root,
            sample_root,
            ffmpeg,
            keep_temp,
        )

    elif task == "consensus":
        reconstruct_consensus(
            rec,
            ami_root,
            audio_root,
            sample_root,
            ffmpeg,
            keep_temp,
        )

    else:
        raise ValueError(
            f"Unsupported task: {task}"
        )

    print("[OK]", rec["id"])


def main():
    ap = argparse.ArgumentParser(
        description=(
            "Reconstruct MeetingToM benchmark media "
            "from an authorized local copy of AMI."
        )
    )

    ap.add_argument(
        "--ami_root",
        required=True,
        help="Root containing AMI meeting directories.",
    )

    ap.add_argument(
        "--audio_root",
        default=None,
        help=(
            "Optional directory containing "
            "<session>.Mix-Headset.wav."
        ),
    )

    ap.add_argument(
        "--metadata",
        required=True,
        help="Path to metadata/reconstruction.jsonl",
    )

    ap.add_argument(
        "--output_dir",
        required=True,
    )

    group = ap.add_mutually_exclusive_group(
        required=True
    )

    group.add_argument(
        "--id",
        help="Reconstruct one benchmark instance.",
    )

    group.add_argument(
        "--all",
        action="store_true",
        help="Reconstruct all instances.",
    )

    ap.add_argument(
        "--ffmpeg",
        default="ffmpeg",
    )

    ap.add_argument(
        "--keep_temp",
        action="store_true",
    )

    args = ap.parse_args()

    if not MOSAIC_SCRIPT.is_file():
        raise FileNotFoundError(
            f"Missing {MOSAIC_SCRIPT}"
        )

    records = load_records(args.metadata)

    if args.id:
        selected = [
            r for r in records
            if r["id"] == args.id
        ]

        if len(selected) != 1:
            raise RuntimeError(
                f"Expected exactly one record for "
                f"{args.id!r}; found {len(selected)}"
            )
    else:
        selected = records

    print(
        f"Reconstructing {len(selected)} "
        f"MeetingToM instance(s)"
    )

    for rec in selected:
        reconstruct_one(
            rec,
            args.ami_root,
            args.audio_root,
            args.output_dir,
            args.ffmpeg,
            args.keep_temp,
        )


if __name__ == "__main__":
    main()
