#!/usr/bin/env python3
"""generate_chrome_scales.py — one master sheet in, every DPI variant out.

    python tools/art/generate_chrome_scales.py --list
    python tools/art/generate_chrome_scales.py flags --check
    python tools/art/generate_chrome_scales.py flags --write

⛔ WHY THIS EXISTS. `chrome.yaml` declares each collection's regions ONCE in 1x coordinates, and
`ChromeProvider` multiplies them by a density to index the variant sheet. Every variant therefore
has to be laid out at EXACTLY its density, and the only thing keeping four separate PNGs in that
relationship used to be somebody remembering. It was not remembered: `flags_3x.png` was authored at
4x, sat that way through a release, was fixed once in 2026-06 and reverted the same day. See
`docs/audit/CHROME_SCALE_BUG.md`.

⭐ THE FIX IS TO STOP MAINTAINING FOUR FILES. Edit the **highest-resolution master only**; this tool
derives the rest by uniform resize, which is correct BY CONSTRUCTION — a sheet's layout is
proportional, so scaling the whole canvas scales every icon's position and size together. There is
no offset to get wrong and no icon that can drift.

⚠ THE MASTER IS NOT A CHROME VARIANT. If the master is 4x, `--write` emits 1x/2x/3x from it. The
engine's ladder stops at 3x, so the generated 3x sheet is what ships; `flags_4x.png` is the editable
art source and is intentionally not declared in chrome.yaml.

⚠ RESAMPLING. Pillow (LANCZOS) is used when importable, otherwise a pure-Python area-average box
filter, and the tool PRINTS which. Both are correct; Pillow is sharper and much faster. 4x -> 2x and
4x -> 1x are exact integer ratios and effectively lossless; 4x -> 3x is a 0.75 resample, which is
why an artist may still prefer a native 3x export — `--check` will accept either.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import struct
import sys
import zlib

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

STAMP = pathlib.Path("tools/art/chrome_masters.json")
CHROME = pathlib.Path("mods/cameo/chrome.yaml")
UIBITS = pathlib.Path("mods/cameo/uibits")
FIELD_DENSITY = {"Image": 1, "Image2x": 2, "Image3x": 3, "Image4x": 4}


# --------------------------------------------------------------------------- PNG, without Pillow

def _read_png(path: pathlib.Path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG")
    pos, idat, w, h, depth, ctype = 8, b"", None, None, None, None
    while pos + 8 <= len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, ctype = struct.unpack(">IIBB", body[:10])
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
        pos += 12 + ln
    if depth != 8 or ctype != 6:
        raise ValueError(f"{path}: need 8-bit RGBA (depth 8, colour type 6), got {depth}/{ctype}")

    raw, stride, ch = zlib.decompress(idat), w * 4, 4
    prev, rows, p = bytearray(stride), [], 0
    for _ in range(h):
        f = raw[p]; p += 1
        line = bytearray(raw[p:p + stride]); p += stride
        if f == 1:
            for i in range(ch, stride):
                line[i] = (line[i] + line[i - ch]) & 255
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                b, c = prev[i], (prev[i - ch] if i >= ch else 0)
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                line[i] = (line[i] + (a if (pa <= pb and pa <= pc) else (b if pb <= pc else c))) & 255
        rows.append(line)
        prev = line
    return w, h, rows


def _write_png(path: pathlib.Path, w: int, h: int, rows) -> None:
    raw = b"".join(b"\x00" + bytes(r) for r in rows)

    def chunk(tag, body):
        return (struct.pack(">I", len(body)) + tag + body
                + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))

    path.write_bytes(b"\x89PNG\r\n\x1a\n"
                     + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw, 9))
                     + chunk(b"IEND", b""))


def _box_resize(w, h, rows, nw, nh):
    """Area-average downscale. Correct for any ratio; slower and softer than LANCZOS."""
    out = []
    for oy in range(nh):
        y0, y1 = oy * h // nh, max(oy * h // nh + 1, (oy + 1) * h // nh)
        line = bytearray(nw * 4)
        for ox in range(nw):
            x0, x1 = ox * w // nw, max(ox * w // nw + 1, (ox + 1) * w // nw)
            r = g = b = a = n = 0
            for yy in range(y0, y1):
                src = rows[yy]
                for xx in range(x0, x1):
                    i = xx * 4
                    r += src[i]; g += src[i + 1]; b += src[i + 2]; a += src[i + 3]
                    n += 1
            o = ox * 4
            line[o] = r // n; line[o + 1] = g // n; line[o + 2] = b // n; line[o + 3] = a // n
        out.append(line)
    return out


def power_of_two_canvas(width: int, height: int) -> tuple[int, int]:
    """The engine uploads sheets as textures and rejects non-power-of-two canvases."""
    def ceil_power_of_two(value: int) -> int:
        return 1 << (value - 1).bit_length()

    return ceil_power_of_two(width), ceil_power_of_two(height)


def resize(src: pathlib.Path, dst: pathlib.Path, nw: int, nh: int) -> str:
    cw, ch = power_of_two_canvas(nw, nh)
    try:
        from PIL import Image
    except ImportError:
        w, h, rows = _read_png(src)
        scaled = _box_resize(w, h, rows, nw, nh)
        padded = [row + bytearray((cw - nw) * 4) for row in scaled]
        padded.extend(bytearray(cw * 4) for _ in range(ch - nh))
        _write_png(dst, cw, ch, padded)
        return "pure-python box filter"
    with Image.open(src) as im:
        scaled = im.convert("RGBA").resize((nw, nh), Image.LANCZOS)
        canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        canvas.paste(scaled, (0, 0))
        canvas.save(dst, "PNG", optimize=True)
    return "Pillow LANCZOS"


# --------------------------------------------------------------------------- chrome.yaml

def variants() -> dict[str, dict[str, str]]:
    """{collection: {field: filename}} for every collection declaring a scale variant."""
    out = {}
    for block in re.split(r"\n(?=\S)", CHROME.read_text(encoding="utf-8")):
        name = block.split(":", 1)[0].strip()
        imgs = dict(re.findall(r"^\t(Image(?:2x|3x|4x)?):\s*(\S+)", block, re.M))
        if len(imgs) > 1:
            out[name.lstrip("^")] = imgs
    return out


def png_size(path: pathlib.Path):
    try:
        d = path.read_bytes()[:24]
    except OSError:
        return None
    return struct.unpack(">II", d[16:24]) if d[:8] == b"\x89PNG\r\n\x1a\n" else None


def artwork(path: pathlib.Path):
    """(canvas_w, canvas_h, art_w, art_h) — where the non-transparent pixels actually end.

    ⚠ CANVAS IS NOT SCALE. Upstream OpenRA and Combined Arms both pad 3x artwork into a
    power-of-two canvas (3 x 256 = 768 -> a 1024 file), so a sheet's canvas ratio says nothing
    about its density. Every judgement in this tool is made on ARTWORK.
    """
    try:
        w, h, rows = _read_png(path)
    except (OSError, ValueError):
        return None
    mx = my = -1
    for y, line in enumerate(rows):
        for x in range(w):
            if line[x * 4 + 3]:
                if x > mx:
                    mx = x
                if y > my:
                    my = y
    return w, h, mx + 1, my + 1


# --------------------------------------------------------------------------- the freshness stamp

def sha(path: pathlib.Path) -> str | None:
    """Content hash. ⚠ NOT mtime — a checkout, a stash pop or a rebase rewrites mtimes without
    changing a pixel, and `git` does not preserve them at all. Only content can answer 'did the
    master change since these were derived?'."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def read_stamp() -> dict:
    try:
        return json.loads(STAMP.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def write_stamp(collection: str, master: pathlib.Path, emitted: list[pathlib.Path]) -> None:
    """Record what was derived from what. This is the ONLY state the freshness audit needs, and it
    is deliberately outside `mods/` — it is tooling metadata, not engine content, so it can be
    committed without a boot gate while the PNGs it describes cannot."""
    data = read_stamp()
    data[collection] = {
        "master": master.name,
        "master_sha256": sha(master),
        "derived": {d.name: sha(d) for d in sorted(emitted, key=lambda q: q.name)},
    }
    STAMP.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\n  stamped {STAMP} — `audit_chrome_master_freshness.py` now guards this set")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("collection", nargs="?", help="collection name, e.g. flags")
    ap.add_argument("--list", action="store_true", help="show every collection and its variants")
    ap.add_argument("--check", action="store_true", help="report what would change, write nothing")
    ap.add_argument("--write", action="store_true", help="generate the derived sheets")
    ap.add_argument("--master", metavar="FILE",
                    help="the art master to derive from, relative to mods/cameo/uibits. Use this "
                         "when the master is NOT declared in chrome.yaml — which is the normal "
                         "case: a 4x master is an ART SOURCE, and the engine's ladder stops at 3x, "
                         "so it never appears in the yaml at all.")
    ap.add_argument("--stamp", action="store_true",
                    help="record the CURRENT files as the generated set, without regenerating "
                         "anything. Use it once to seed the freshness stamp for sheets that were "
                         "already derived correctly (and whose PNGs therefore must not be "
                         "rewritten in a tree that cannot boot-gate them).")
    ap.add_argument("--emit", metavar="N[,N...]",
                    help="densities to emit from the master regardless of what chrome.yaml "
                         "declares, e.g. --emit 1,2,3. Filenames follow the convention "
                         "<stem>.png for 1x and <stem>_<N>x.png above it.")
    args = ap.parse_args()

    decl = variants()

    if args.list or not args.collection:
        print("# chrome collections with scale variants\n")
        print("| collection | field | file | size | implied |")
        print("|---|---|---|--:|--:|")
        for name, imgs in sorted(decl.items()):
            base = png_size(UIBITS / imgs.get("Image", ""))
            for f in ("Image", "Image2x", "Image3x", "Image4x"):
                if f not in imgs:
                    continue
                s = png_size(UIBITS / imgs[f])
                imp = f"{s[0]/base[0]:.2f}x" if s and base and base[0] else "?"
                print(f"| {name} | `{f}` | `{imgs[f]}` | {s[0]}x{s[1]} | {imp} |" if s
                      else f"| {name} | `{f}` | `{imgs[f]}` | MISSING | — |")
        print("\nRun with a collection name and --check to see what would be generated.")
        return 0

    # Collection names are matched case-insensitively: the yaml templates are `^Flags` / `^Glyphs`
    # but nobody types the capital.
    lookup = {k.lower(): k for k in decl}
    if args.collection and args.collection.lower() in lookup:
        args.collection = lookup[args.collection.lower()]

    if args.collection not in decl:
        print(f"⛔ no collection `{args.collection}` with variants. Known: "
              + ", ".join(sorted(decl)))
        return 1

    imgs = decl[args.collection]
    base_path = UIBITS / imgs.get("Image", "")
    base = artwork(base_path)
    if base is None:
        print(f"⛔ base sheet `{base_path}` is missing or not 8-bit RGBA.")
        return 1
    bw, bh, bax, bay = base

    # Which declared file is really the highest-resolution artwork? Judged on artwork, not canvas
    # and not the field name — `Image3x` in this mod holds 4x artwork, which is the whole bug.
    best, best_density = None, 0.0
    rows_out = []
    for field in ("Image", "Image2x", "Image3x", "Image4x"):
        if field not in imgs:
            continue
        got = artwork(UIBITS / imgs[field])
        if got is None:
            rows_out.append((field, imgs[field], "MISSING", "—", "—"))
            continue
        cw, chh, ax, ay = got
        d = ax / bax
        rows_out.append((field, imgs[field], f"{cw}x{chh}", f"{ax}x{ay}", f"{d:.2f}x"))
        if d > best_density:
            best, best_density = field, d

    print(f"# {args.collection}\n")
    print("| field | file | canvas | artwork | implied density |")
    print("|---|---|--:|--:|--:|")
    for r in rows_out:
        print(f"| `{r[0]}` | `{r[1]}` | {r[2]} | {r[3]} | {r[4]} |")
    print()

    if args.master:
        master = UIBITS / args.master
        got = artwork(master)
        if got is None:
            print(f"⛔ master `{master}` is missing or not 8-bit RGBA.")
            return 1
        best_density = got[2] / bax
        print(f"Master: **`{args.master}`** (supplied) — artwork {got[2]}x{got[3]}, "
              f"{best_density:.2f}x the base.\n")
    else:
        master = UIBITS / imgs[best]
        print(f"Master: **`{imgs[best]}`** — highest ARTWORK density, {best_density:.2f}x "
              f"(treating it as {int(round(best_density))}x).\n")

    master_density = int(round(best_density))
    ms = png_size(master)

    # ⛔ THE BUG THIS TOOL EXISTS FOR, REPORTED AS A FAILURE RATHER THAN AS SILENCE.
    # When the master was auto-detected it sits in a DECLARED slot, and that slot carries a density
    # the engine will multiply the 1x regions by. If the artwork density and the slot density
    # disagree, the collection is broken in game — and the derived-sheet comparison below would say
    # "nothing to do", because it measures the other sheets against the master and never asks
    # whether the master belongs where it is declared. That silence is the same class of mistake as
    # the bug itself: trusting the field name instead of measuring.
    if not args.master and best is not None and FIELD_DENSITY[best] != master_density:
        slot = FIELD_DENSITY[best]
        stem = re.sub(r"(_\dx)?\.png$", "", imgs[best])
        print(f"⛔ **Broken collection.** `{imgs[best]}` is declared as `{best}` (density {slot}x) "
              f"but its artwork is laid out at **{master_density}x**. `ChromeProvider` multiplies "
              f"the 1x regions in `chrome.yaml` by {slot}, so every icon is indexed at the wrong "
              f"place — wrongly in proportion to its distance from the top-left corner.\n\n"
              f"There is also NO true {slot}x sheet to generate, because the {slot}x slot is where "
              f"this master is sitting. Give it its own name and derive the ladder from it:\n\n"
              f"    git mv mods/cameo/uibits/{imgs[best]} mods/cameo/uibits/{stem}_{master_density}x.png\n"
              f"    python tools/art/generate_chrome_scales.py {args.collection} \\\n"
              f"        --master {stem}_{master_density}x.png --emit "
              + ",".join(str(d) for d in range(1, master_density)) + " --write\n\n"
              f"See `docs/audit/CHROME_SCALE_BUG.md`.")
        return 1

    # ⛔ Uniform resize only reproduces the right layout if the master's canvas is the base canvas
    # times its density. A PADDED master (upstream's convention) breaks that: scaling it gives the
    # right artwork ratio in an oddly-sized canvas. Refuse rather than emit something surprising.
    #
    # ⚠ But only refuse GENERATION. A padded sheet is the upstream convention and `glyphs_3x.png`
    # is one, so failing a plain --check on it would report a healthy collection as broken — the
    # same false positive that my first diagnosis of this bug made by reading canvases.
    if ms != (bw * master_density, bh * master_density):
        generating = bool(args.emit or args.write)
        verb = "**Refusing.**" if generating else "**Not a generation source.**"
        print(f"⛔ {verb} The master's canvas is {ms[0]}x{ms[1]}, but {master_density}x of "
              f"the base canvas ({bw}x{bh}) is {bw*master_density}x{bh*master_density}. That means "
              f"the master is PADDED — the upstream convention — and a uniform resize would produce "
              f"correct artwork inside an oddly-sized canvas.\n\n"
              f"Nothing is wrong with a padded sheet; it just cannot be used as a generation "
              f"source. Export the derived sheets from the art source instead, or supply an "
              f"unpadded master.\n")
        if generating:
            return 1

    if args.emit:
        stem = re.sub(r"(_\dx)?\.png$", "", args.master or imgs[best])
        stem = re.sub(r"_\dx$", "", stem)
        print("| density | file | would be | action |")
        print("|---|---|--:|---|")
        emit = []
        for d in sorted({int(x) for x in args.emit.split(",") if x.strip()}):
            if d >= master_density:
                print(f"| {d}x | — | — | skipped: not below the {master_density}x master |")
                continue
            fn = f"{stem}.png" if d == 1 else f"{stem}_{d}x.png"
            dst = UIBITS / fn
            # ⛔ NEVER write over the master. This mod's 4x master is NAMED `flags_3x.png`, so
            # `--emit 3` would replace the highest-resolution source with its own downscale and
            # the original would be gone. It happened once while testing this tool.
            if dst.resolve() == master.resolve():
                print(f"| {d}x | `{fn}` | — | ⛔ REFUSED: that is the master itself |")
                continue
            want = (bw * d, bh * d)
            cur = png_size(dst)
            print(f"| {d}x | `{fn}` | {want[0]}x{want[1]} "
                  f"| {'overwrite' if cur else 'create'} |")
            emit.append((dst, want))
        if args.stamp and not args.write:
            # ⭐ SEED THE STAMP WITHOUT TOUCHING A PIXEL. The sheets in this tree were already
            # derived correctly and are engine content, so rewriting them to record a hash would
            # need a boot gate for no gain. --stamp records what is on disk as the generated set.
            missing = [d.name for d, _ in emit if not d.exists()]
            if missing:
                print(f"\n⛔ cannot stamp: {', '.join(missing)} do not exist yet. "
                      f"Generate them with --write first.")
                return 1
            write_stamp(args.collection, master, [d for d, _ in emit])
            return 0
        if not args.write:
            print(f"\n{len(emit)} file(s) would be written. Re-run with `--write`.")
            return 0
        for dst, (nw, nh) in emit:
            how = resize(master, dst, nw, nh)
            cw, ch = png_size(dst)
            layout = (f"{nw}x{nh}" if (cw, ch) == (nw, nh)
                      else f"{nw}x{nh} artwork on {cw}x{ch} canvas")
            print(f"\n  wrote {dst}  {layout}  ({how})")
        write_stamp(args.collection, master, [d for d, _ in emit])
        print("\n⚠ Generated files are engine content: run "
              "`python tools/audit/audit_chrome_scale_variants.py`, then BOOT GATE before "
              "committing (CLAUDE.md rule 1).")
        return 0

    print("| target | file | current artwork | would be | action |")
    print("|---|---|--:|--:|---|")
    jobs = []
    for field, density in sorted(FIELD_DENSITY.items(), key=lambda kv: kv[1]):
        if field == best or field not in imgs:
            continue
        want_canvas = (bw * density, bh * density)
        want_art = (bax * density, bay * density)
        got = artwork(UIBITS / imgs[field])
        cur = f"{got[2]}x{got[3]}" if got else "—"
        # ⚠ A FLAT ±2px TOLERANCE CALLS CORRECTLY GENERATED SHEETS BROKEN. Resampling bleeds
        # alpha outward, so a downscaled sheet's bounding box lands a few pixels off the exact
        # ratio — the shipped 2x flags sheet measures 771 where 387 x 2 = 774, and --check told
        # you to regenerate a file this very tool had just produced. Scale the tolerance: 0.5% is
        # still two orders of magnitude tighter than the 33% error this tool exists to catch.
        tol = (max(2, want_art[0] // 200), max(2, want_art[1] // 200))
        ok = (got is not None
              and abs(got[2] - want_art[0]) <= tol[0]
              and abs(got[3] - want_art[1]) <= tol[1])
        print(f"| {field} | `{imgs[field]}` | {cur} | {want_art[0]}x{want_art[1]} "
              f"| {'ok' if ok else ('**regenerate**' if got else '**create**')} |")
        if not ok:
            jobs.append((field, UIBITS / imgs[field], want_canvas))

    if not jobs:
        print("\n**Nothing to do** — every derived sheet already matches the master.")
        return 0

    if not args.write:
        print(f"\n{len(jobs)} sheet(s) would change. Re-run with `--write` to generate them.")
        print("⚠ Generated files are engine content: boot-gate before committing (CLAUDE.md rule 1).")
        return 0

    for field, dst, (nw, nh) in jobs:
        how = resize(master, dst, nw, nh)
        cw, ch = png_size(dst)
        layout = (f"{nw}x{nh}" if (cw, ch) == (nw, nh)
                  else f"{nw}x{nh} artwork on {cw}x{ch} canvas")
        print(f"\n  wrote {dst}  {layout}  ({how})")
    print("\n⚠ Now run `python tools/audit/audit_chrome_scale_variants.py`, then BOOT GATE before "
          "committing — these are engine content.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
