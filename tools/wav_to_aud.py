#!/usr/bin/env python
"""Convert WAV -> Westwood IMA-ADPCM .aud (the format OpenRA/Cameo notifications need).

OpenRA's notification path only plays `.aud` (the manifest `.wav` is Asset-Browser
only). This encoder matches the engine's decoder exactly
(OpenRA.Mods.Cnc/FileFormats/AudReader.cs + Mods.Common/FileFormats/ImaAdpcmReader.cs):

  Header (12 bytes): u16 sampleRate, i32 dataSize, i32 outputSize,
                     u8 flags (2 = 16-bit mono), u8 format (99 = IMA-ADPCM)
  Then chunks:       u16 compressedSize, u16 outputSize, u32 0x0000DEAF, data[]

The ADPCM variant is Westwood's (delta = step*m/4 + step/8, integer division;
index/current carried continuously across chunks). The encoder brute-forces the
best 4-bit code per sample against that exact decoder, so it stays in lockstep
and reconstructs cleanly.

Pipeline per file: ffmpeg (loudnorm to match other voice sets + resample to mono
22050/16-bit) -> raw PCM -> ADPCM encode -> .aud.

Usage (from repo root):
    python tools/wav_to_aud.py --src docs/overmind-voice/rvc_out --out docs/overmind-voice/aud
    python tools/wav_to_aud.py --src one.wav --out docs/overmind-voice/aud --no-normalize
"""

import argparse
import os
import shutil
import struct
import subprocess
import sys

INDEX_ADJUST = [-1, -1, -1, -1, 2, 4, 6, 8]
STEP_TABLE = [
    7, 8, 9, 10, 11, 12, 13, 14, 16,
    17, 19, 21, 23, 25, 28, 31, 34, 37,
    41, 45, 50, 55, 60, 66, 73, 80, 88,
    97, 107, 118, 130, 143, 157, 173, 190, 209,
    230, 253, 279, 307, 337, 371, 408, 449, 494,
    544, 598, 658, 724, 796, 876, 963, 1060, 1166,
    1282, 1411, 1552, 1707, 1878, 2066, 2272, 2499, 2749,
    3024, 3327, 3660, 4026, 4428, 4871, 5358, 5894, 6484,
    7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899, 15289,
    16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767,
]

AUD_SAMPLE_RATE = 22050     # classic Westwood AUD rate; matches existing Cameo sets
CHUNK_COMPRESSED = 2048     # compressed bytes per chunk (-> 8192 PCM bytes out)
DEAF = 0x0000DEAF


def _decode(code, index, current):
    """Exact mirror of ImaAdpcmReader.DecodeImaAdpcmSample."""
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


def _encode_sample(target, index, current):
    """Pick the 4-bit code whose decode lands closest to target; return (code, current, index)."""
    best_err = None
    best = None
    for code in range(16):
        c2, i2 = _decode(code, index, current)
        err = abs(c2 - target)
        if best_err is None or err < best_err:
            best_err = err
            best = (code, c2, i2)
    return best


def encode_adpcm(samples):
    """samples: list[int16] -> (adpcm_bytes, n_samples). State carried across all samples."""
    # need an even sample count: every byte packs two nibbles, both consumed by the decoder
    if len(samples) % 2 == 1:
        samples = samples + [samples[-1]]
    index = 0
    current = 0
    out = bytearray()
    for i in range(0, len(samples), 2):
        code_lo, current, index = _encode_sample(samples[i], index, current)
        code_hi, current, index = _encode_sample(samples[i + 1], index, current)
        out.append(((code_hi & 0xF) << 4) | (code_lo & 0xF))
    return bytes(out), len(samples)


def write_aud(adpcm, n_samples, path):
    output_size = n_samples * 2  # 16-bit PCM bytes the decoder will produce

    chunks = bytearray()
    for off in range(0, len(adpcm), CHUNK_COMPRESSED):
        data = adpcm[off:off + CHUNK_COMPRESSED]
        comp = len(data)
        out_bytes = comp * 4  # each compressed byte -> 2 samples -> 4 PCM bytes
        chunks += struct.pack("<HHI", comp, out_bytes, DEAF)
        chunks += data

    data_size = len(chunks)  # total chunk-section bytes (headers + data), as engine expects
    header = struct.pack("<HiiBB", AUD_SAMPLE_RATE, data_size, output_size, 0x02, 99)

    with open(path, "wb") as f:
        f.write(header)
        f.write(chunks)


def ffmpeg_to_pcm(ffmpeg, src, normalize):
    af = "loudnorm=I=-14:TP=-1.5:LRA=11" if normalize else "anull"
    cmd = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-i", src,
        "-af", af,
        "-ac", "1", "-ar", str(AUD_SAMPLE_RATE),
        "-f", "s16le", "-acodec", "pcm_s16le", "-",
    ]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.decode(errors="replace").strip()[:300])
    raw = res.stdout
    return list(struct.unpack("<%dh" % (len(raw) // 2), raw[: len(raw) // 2 * 2]))


def collect(src):
    if os.path.isfile(src):
        return [src]
    return sorted(
        os.path.join(src, f) for f in os.listdir(src) if f.lower().endswith(".wav")
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True, help="WAV file or folder of WAVs")
    ap.add_argument("--out", required=True, help="output folder for .aud files")
    ap.add_argument("--no-normalize", action="store_true", help="skip loudnorm")
    args = ap.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        sys.exit("ERROR: ffmpeg not on PATH.")

    files = collect(args.src)
    if not files:
        sys.exit(f"No .wav found at {args.src}")
    os.makedirs(args.out, exist_ok=True)

    print(f"Encoding {len(files)} file(s) -> {args.out}  (IMA-ADPCM .aud, {AUD_SAMPLE_RATE} Hz mono)\n")
    for i, src in enumerate(files, 1):
        token = os.path.splitext(os.path.basename(src))[0]
        dst = os.path.join(args.out, token + ".aud")
        try:
            samples = ffmpeg_to_pcm(ffmpeg, src, not args.no_normalize)
            if not samples:
                print(f"  [{i}/{len(files)}] SKIP {token} (empty)")
                continue
            adpcm, n = encode_adpcm(samples)
            write_aud(adpcm, n, dst)
            print(f"  [{i}/{len(files)}] {token}.aud  ({n/AUD_SAMPLE_RATE:.1f}s, {os.path.getsize(dst)} bytes)")
        except Exception as e:
            print(f"  [{i}/{len(files)}] FAILED {token}: {e}")

    print(f"\nDone -> {os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()
