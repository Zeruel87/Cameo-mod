#!/usr/bin/env python
"""Build a clean single-speaker RVC training dataset of StarCraft Overmind lines.

The original StarCraft Zerg campaign stores its spoken transmissions as plain
WAVs inside each mission's `staredit\\wav\\` folder (exposed directly in the
free/Remastered CASC under `SD\\campaign\\Zerg\\ZergNN\\...`). The Overmind's
lines all carry the speaker code `zad` in the filename
(e.g. `z1b03zad.wav` = Zerg mission 1, line 03, speaker `zad`), so filtering on
`*zad.wav` yields a pure Overmind set with no manual culling.

This script takes the raw extracted WAVs, keeps only the Overmind clips, trims
dead air, downmixes to mono, resamples, loudness-normalises, and writes them to
a flat dataset folder ready to drop into RVC training.

Usage (from repo root):
    python tools/prep_overmind_dataset.py
    python tools/prep_overmind_dataset.py --src docs/zerg-voice-src/SD/campaign/Zerg --out docs/overmind-voice/dataset
    python tools/prep_overmind_dataset.py --pattern "*zad.wav" --target-sr 44100

Requires ffmpeg + ffprobe on PATH (you have Gyan.FFmpeg via winget).
"""

import argparse
import fnmatch
import os
import shutil
import subprocess
import sys

# --- silence trim (both ends) + loudnorm. The areverse trick trims trailing
#     silence by reversing, trimming the new leading silence, and reversing back.
SILENCE_THRESHOLD = "-50dB"
SILENCE_PAD = "0.05"   # keep 50ms so words aren't clipped


def build_filter(normalize):
    trim = (
        f"silenceremove=start_periods=1:start_threshold={SILENCE_THRESHOLD}:start_silence={SILENCE_PAD},"
        "areverse,"
        f"silenceremove=start_periods=1:start_threshold={SILENCE_THRESHOLD}:start_silence={SILENCE_PAD},"
        "areverse"
    )
    if normalize:
        # I=-16 leaves headroom for training; final in-game packaging uses I=-14.
        return trim + ",loudnorm=I=-16:TP=-1.5:LRA=11"
    return trim


def which_or_die(exe):
    path = shutil.which(exe)
    if not path:
        sys.exit(f"ERROR: '{exe}' not found on PATH. Install ffmpeg (winget install Gyan.FFmpeg).")
    return path


def duration_seconds(ffprobe, path):
    try:
        out = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, check=True,
        )
        return float(out.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        return 0.0


def find_clips(src, pattern):
    matches = []
    for root, _dirs, files in os.walk(src):
        for name in files:
            if fnmatch.fnmatch(name.lower(), pattern.lower()):
                matches.append(os.path.join(root, name))
    return sorted(matches)


def flat_name(src, path):
    # Encode the mission folder into the name so clips from different missions
    # don't collide: .../Zerg03/staredit/wav/z3b01zad.wav -> Zerg03_z3b01zad.wav
    rel = os.path.relpath(path, src)
    parts = rel.replace("\\", "/").split("/")
    mission = next((p for p in parts if p.lower().startswith("zerg")), "")
    base = os.path.splitext(os.path.basename(path))[0]
    stem = f"{mission}_{base}" if mission and not base.lower().startswith(mission.lower()) else base
    return stem + ".wav"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", default="docs/zerg-voice-src/SD/campaign/Zerg", help="folder of raw extracted campaign WAVs")
    ap.add_argument("--out", default="docs/overmind-voice/dataset", help="output dataset folder")
    ap.add_argument("--pattern", default="*zad.wav", help="filename glob to keep (Overmind speaker code)")
    ap.add_argument("--target-sr", type=int, default=44100, help="output sample rate (Hz)")
    ap.add_argument("--no-normalize", action="store_true", help="skip loudnorm (trim + mono only)")
    ap.add_argument("--long-warn", type=float, default=15.0, help="warn about clips longer than N seconds")
    args = ap.parse_args()

    ffmpeg = which_or_die("ffmpeg")
    ffprobe = which_or_die("ffprobe")

    if not os.path.isdir(args.src):
        sys.exit(
            f"Source folder '{args.src}' does not exist yet.\n"
            "Extract SD\\campaign\\Zerg\\ from CascView into it first, then re-run."
        )

    clips = find_clips(args.src, args.pattern)
    if not clips:
        sys.exit(
            f"No files matching '{args.pattern}' under '{args.src}'.\n"
            "Did the extraction land? Check the folder and the speaker-code pattern."
        )

    os.makedirs(args.out, exist_ok=True)
    afilter = build_filter(not args.no_normalize)

    total_in = 0.0
    total_out = 0.0
    long_clips = []
    print(f"Found {len(clips)} Overmind clip(s) matching '{args.pattern}'. Processing -> {args.out}\n")
    for i, src_path in enumerate(clips, 1):
        out_path = os.path.join(args.out, flat_name(args.src, src_path))
        total_in += duration_seconds(ffprobe, src_path)
        cmd = [
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-i", src_path,
            "-af", afilter,
            "-ac", "1", "-ar", str(args.target_sr),
            "-c:a", "pcm_s16le",
            out_path,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"  [{i}/{len(clips)}] FAILED {os.path.basename(src_path)}: {res.stderr.strip()[:200]}")
            continue
        d = duration_seconds(ffprobe, out_path)
        total_out += d
        if d > args.long_warn:
            long_clips.append((os.path.basename(out_path), d))
        print(f"  [{i}/{len(clips)}] {os.path.basename(out_path)}  ({d:.1f}s)")

    print("\n--- summary ---")
    print(f"  clips written : {len(clips)}")
    print(f"  raw duration  : {total_in/60:.1f} min")
    print(f"  trimmed total : {total_out/60:.1f} min  <- this is your RVC training-data budget")
    if total_out < 5 * 60:
        print("  NOTE: under ~5 min. RVC can train on this but quality improves with more.")
        print("        Consider also extracting Overmind 'zad' lines from SD\\campaign\\Protoss\\.")
    if long_clips:
        print(f"  {len(long_clips)} clip(s) over {args.long_warn:.0f}s (fine for RVC, but you may split them):")
        for n, d in long_clips:
            print(f"    - {n}  ({d:.1f}s)")
    print(f"\nDataset ready: {os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()
