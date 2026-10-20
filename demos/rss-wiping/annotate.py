#!/usr/bin/env python3
"""Label an existing continuous recording with its saved measured values."""

import argparse
import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np


def timestamp(seconds):
    centiseconds = round(seconds * 100)
    seconds, fraction = divmod(centiseconds, 100)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}.{fraction:02d}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((args.run / "manifest.json").read_text())
    rows = {row["step"]: row for row in
            (json.loads(line) for line in (args.run / "observations.jsonl").read_text().splitlines())}
    times = np.load(args.run / "video-times.npy")
    fps = manifest["video_fps"]
    width, height = manifest["camera"]["width"], manifest["camera"]["height"]
    header = (
        f"[Script Info]\nScriptType: v4.00+\nPlayResX: {width}\nPlayResY: {height}\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, "
        "Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Measured,DejaVu Sans,21,&H00FFFFFF,&H00FFFFFF,&H80000000,&H80000000,"
        "0,0,0,0,100,100,0,0,3,1,0,7,12,12,10,1\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    lines = [header]
    for frame, sim_time in enumerate(times):
        row = rows[round(float(sim_time) * manifest["control_hz"])]
        displacement = row["patch_centroid_slip_m"]
        slip = "n/a" if displacement is None else f"{1000 * displacement:.3f} mm"
        if displacement is not None and row["grip_command"] < 0.5:
            slip = "released"
        label = (
            f"RSS | {manifest['mode']} | sim {sim_time:.1f} s | {row['phase']}"
            f"\\NCleaned {100 * row['cleaned_fraction']:.1f}% | Bar force {row['bar_force_n']:.2f} N"
            f"\\NPatch displacement {slip} | Active pins {row['active_pins']}"
        )
        lines.append(
            f"Dialogue: 0,{timestamp(frame / fps)},{timestamp((frame + 1) / fps)},"
            f"Measured,,0,0,0,,{label}\n"
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="rss-labels-", dir=args.output.parent) as temporary:
        subtitles = Path(temporary).resolve() / "measurements.ass"
        subtitles.write_text("".join(lines))
        subprocess.run([
            "ffmpeg", "-nostdin", "-v", "error", "-i", str((args.run / "video.mp4").resolve()),
            "-vf", "subtitles=measurements.ass", "-an", "-c:v", "libx264",
            "-crf", "20", "-preset", "fast", "-threads", "2", "-movflags", "+faststart",
            str(args.output.resolve()),
        ], cwd=temporary, check=True)


if __name__ == "__main__":
    main()
