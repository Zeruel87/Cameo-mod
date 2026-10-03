#!/usr/bin/env python
"""Decode Westwood IMA-ADPCM .aud (OpenRA fmt 99) -> 16-bit mono WAV.

Mirrors the engine decoder exactly (OpenRA.Mods.Cnc/FileFormats/AudReader.cs +
Mods.Common/FileFormats/ImaAdpcmReader.cs): low nibble decoded first, then high
nibble (guarded by base < outputSize), ADPCM index/sample carried continuously
across 0xDEAF chunks.

Used to turn an existing token-named voice set (e.g. ebfd_*.aud) into WAV source
for RVC "voice reskinning". Non-destructive: writes new files to --out only.

    python tools/aud_to_wav.py --src mods/cameo/bits/notifications --glob "ebfd_*.aud" --out docs/overmind-voice/ebfd_demo_src

Note: only fmt 99 (IMA-ADPCM) is handled. fmt 1 (Westwood ADPCM) and RIFF/WAVE
files (some sets are WAV-renamed-to-.aud) are detected and reported, not decoded.
"""

import argparse
import fnmatch
import os
import struct
import sys
import wave

INDEX_ADJUST = [-1, -1, -1, -1, 2, 4, 6, 8]
STEP_TABLE = [
    7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34, 37, 41, 45,
    50, 55, 60, 66, 73, 80, 88, 97, 107, 118, 130, 143, 157, 173, 190, 209, 230,
    253, 279, 307, 337, 371, 408, 449, 494, 544, 598, 658, 724, 796, 876, 963,
    1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327,
    3660, 4026, 4428, 4871, 5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442,
    11487, 12635, 13899, 15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767,
]


def _decode_sample(code, index, current):
    sb = (code & 8) != 0
    m = code & 7
    step = STEP_TABLE[index]
    delta = step * m // 4 + step // 8
    if sb:
        delta = -delta
    current += delta
    if current > 32767:
        current = 32767
    elif current < -32768:
        current = -32768
    index += INDEX_ADJUST[m]
    if index < 0:
        index = 0
    elif index > 88:
        index = 88
    return current, index


def decode_aud(path):
    b = open(path, "rb").read()
    # RIFF (WAV-renamed-to-.aud) or too-short -> not an IMA AUD
    if b[:4] == b"RIFF":
        return None, None, "riff-wav"
    sample_rate, data_size, output_size = struct.unpack_from("<Hii", b, 0)
    fmt = b[11]
    if fmt != 99:
        return None, None, f"fmt-{fmt}"

    pos = 12
    index = 0
    current = 0
    base = 0
    out = bytearray()
    while data_size > 0 and pos + 8 <= len(b):
        comp, _osz, magic = struct.unpack_from("<HHI", b, pos)
        pos += 8
        if magic != 0xDEAF:
            return None, None, "bad-chunk"
        for byte in b[pos:pos + comp]:
            current, index = _decode_sample(byte, index, current)
            out += struct.pack("<h", current)
            base += 2
            if base < output_size:
                current, index = _decode_sample(byte >> 4, index, current)
                out += struct.pack("<h", current)
                base += 2
        pos += comp
        data_size -= 8 + comp
    return sample_rate, bytes(out), "ok"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True, help="folder containing .aud files")
    ap.add_argument("--glob", default="*.aud", help="filename pattern (e.g. 'ebfd_*.aud')")
    ap.add_argument("--out", required=True, help="output folder for WAVs")
    args = ap.parse_args()

    if not os.path.isdir(args.src):
        sys.exit(f"src not found: {args.src}")
    files = sorted(f for f in os.listdir(args.src) if fnmatch.fnmatch(f.lower(), args.glob.lower()))
    if not files:
        sys.exit(f"no files matching {args.glob} in {args.src}")
    os.makedirs(args.out, exist_ok=True)

    print(f"Decoding {len(files)} file(s) matching '{args.glob}' -> {args.out}\n")
    ok = skipped = 0
    for i, name in enumerate(files, 1):
        sr, pcm, status = decode_aud(os.path.join(args.src, name))
        token = os.path.splitext(name)[0]
        if status != "ok":
            print(f"  [{i}/{len(files)}] SKIP {name} ({status})")
            skipped += 1
            continue
        dst = os.path.join(args.out, token + ".wav")
        w = wave.open(dst, "wb")
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm)
        w.close()
        print(f"  [{i}/{len(files)}] {token}.wav  ({len(pcm)/2/sr:.1f}s @ {sr}Hz)")
        ok += 1
    print(f"\nDone. {ok} decoded, {skipped} skipped -> {os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()
