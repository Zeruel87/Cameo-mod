#!/usr/bin/env python3
"""audit_chrome_scale_variants.py — a chrome sheet must be exactly the scale it is declared as.

    python tools/audit/audit_chrome_scale_variants.py

⛔ WHY THIS EXISTS. Discord bug report, 2026-09: *"UI scaling above 150% messes up faction icons
and some UI in game"* — reproduced at 1080p and at 2800x1600, but NOT at 1440p.

The cause is not the scaling code. `chrome.yaml` declares each collection's regions ONCE, in 1x
coordinates, and `ChromeProvider` multiplies them by a HARDCODED density to index the variant
sheet. Read at the pinned engine (`mod.config` ENGINE_VERSION 462fc1fc4):

    if (dpiScale > 2 && Image3x != null) { image = Image3x; density = 3; }
    else if (dpiScale > 1 && Image2x != null) { image = Image2x; density = 2; }
    ...
    new Sprite(sheet, density * mi, TextureChannel.RGBA, 1f / density);

⛔ **MEASURE THE ARTWORK, NOT THE CANVAS. The first version of this audit compared canvas sizes
and was WRONG.** Upstream OpenRA pads 3x artwork into a power-of-two canvas -- 3 x 256 = 768 is
not a power of two, so `mods/ra/uibits/glyphs-3x.png` is a 1024x1024 file holding 768x768 of art.
By canvas size that looks like a 4x sheet; by artwork it is exactly 3x and entirely correct. Every
one of upstream's twelve variant declarations looks "4x" by canvas and is fine.

So the check is: the artwork's bounding box must equal the collection's 1x REGION EXTENT times the
density. Measured that way, exactly one sheet in this mod is wrong:

    ^Flags  region extent 384x512   3x wants 1152x1536   flags_3x.png has 1536x2048  <- 4x, WRONG
    ^Glyphs region extent 254x256   3x wants  762x768    glyphs_3x.png has  768x768  <- ok

⭐ AND THE MISREAD EXPLAINS THE SYMPTOM EXACTLY. With the engine reading at 3x from a 4x sheet, a
region at 1x (x, y) is read from (3x, 3y) while its art actually sits at (4x, 4y) — so the error
is PROPORTIONAL TO DISTANCE FROM THE TOP-LEFT CORNER:

    gdi      at 0,0     -> 100% of the correct pixels   (3*0 == 4*0, so the corner looks fine)
    nod      at 0,16    ->  67%
    XCOM     at 352,224 ->   0%   — completely different artwork
    Warcraft at 160,496 ->   0%

which is why it reads as "some UI" rather than "all UI", and why nobody spotted it from the first
few icons. Only the 3x path is affected, so whether a given player sees it depends on which DPI
bucket their resolution and UI scale land in — that is the whole "1440p is fine, 1080p is not".

WHAT IT CHECKS, for every collection in chrome.yaml that declares Regions:
  1. the ARTWORK bounding box of each declared variant equals the 1x region extent x its density
     (canvas size is ignored — padding to a power of two is the upstream convention);
  2. every runtime texture canvas is power-of-two and at least big enough to hold that artwork;
  3. every region fits inside the 1x extent, since that is the coordinate space they are in.

⚠ Absence is fine and is the normal case — 71 collections here declare only `Image`. A missing
variant makes the engine fall back to a smaller sheet, which renders CORRECT pixels slightly
softer. A wrongly-LAID-OUT variant renders wrong pixels. Never "fix" a finding here by inventing a
file; re-lay the artwork at the right scale, or drop the declaration.

EXIT CODE: 1 on any wrongly-sized variant or out-of-bounds region.
"""
from __future__ import annotations

import pathlib
import re
import struct
import sys
import zlib

if hasattr(sys.stdout, "reconfigure"):          # Windows consoles default to cp1252
    sys.stdout.reconfigure(encoding="utf-8")

CHROME = pathlib.Path("mods/cameo/chrome.yaml")
UIBITS = pathlib.Path("mods/cameo/uibits")
DENSITY = {"Image": 1, "Image2x": 2, "Image3x": 3, "Image4x": 4}

# Antialiasing on a resized sheet bleeds a pixel or two past the ideal edge, and artwork need not
# reach the very last row. Neither is a defect; being a whole density step out is.
TOLERANCE = 0.25          # implied-density slack; a whole step off is the defect


def png_pixels(path: pathlib.Path):
    """(width, height, channels, rows) — minimal decoder; no image library in this container."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    pos, idat, w = 8, b"", None
    h = depth = ctype = None
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
    if w is None or depth != 8:
        return None
    ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(ctype)
    if ch is None:
        return None

    raw = zlib.decompress(idat)
    stride = w * ch
    prev = bytearray(stride)
    rows, p = [], 0
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
                b = prev[i]
                c = prev[i - ch] if i >= ch else 0
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                line[i] = (line[i] + (a if (pa <= pb and pa <= pc) else (b if pb <= pc else c))) & 255
        rows.append(line)
        prev = line
    return w, h, ch, rows


def artwork_extent(path: pathlib.Path):
    """How far the actual ARTWORK reaches. Canvas padding is upstream convention, not a defect."""
    got = png_pixels(path)
    if got is None:
        return None
    w, h, ch, rows = got
    if ch not in (2, 4):                       # no alpha: the whole canvas is artwork
        return w, h, w, h
    ai, maxx, maxy = ch - 1, -1, -1
    for y, line in enumerate(rows):
        for x in range(w):
            if line[x * ch + ai]:
                if x > maxx:
                    maxx = x
                if y > maxy:
                    maxy = y
    return w, h, maxx + 1, maxy + 1


def collections(text: str):
    """(name, {field: file}, one-level-resolved 1x region extent) per top-level node."""
    imgs_of, inherits_of, regions_of = {}, {}, {}
    for block in re.split(r"\n(?=\S)", text):
        name = block.split(":", 1)[0].strip()
        if not name or name.startswith("#"):
            continue
        imgs = dict(re.findall(r"^\t(Image(?:2x|3x)?):\s*(\S+)", block, re.M))
        if imgs:
            imgs_of[name] = imgs
        m = re.search(r"^\tInherits:\s*(\S+)", block, re.M)
        if m:
            inherits_of[name] = m.group(1)
        r = re.search(r"^\tRegions:\n((?:\t\t.*\n)*)", block, re.M)
        if r:
            mx = my = 0
            for line in r.group(1).splitlines():
                if ":" not in line:
                    continue
                nums = re.findall(r"-?\d+", line.split(":", 1)[1])
                if len(nums) >= 4:
                    x, y, w, h = (int(n) for n in nums[:4])
                    mx, my = max(mx, x + w), max(my, y + h)
            regions_of[name] = (mx, my)

    # roll every child's region extent up onto the template that owns the images
    extent = {}
    for child, parent in inherits_of.items():
        if child in regions_of and parent in imgs_of:
            px, py = extent.get(parent, (0, 0))
            cx, cy = regions_of[child]
            extent[parent] = (max(px, cx), max(py, cy))
    for name, ext in regions_of.items():
        if name in imgs_of:
            px, py = extent.get(name, (0, 0))
            extent[name] = (max(px, ext[0]), max(py, ext[1]))
    return imgs_of, extent


def main() -> int:
    if not CHROME.exists():
        print(f"⛔ **FAIL** — {CHROME} not found.")
        return 1

    imgs_of, extent = collections(CHROME.read_text(encoding="utf-8"))

    print("# audit_chrome_scale_variants — is each variant's ARTWORK laid out at its density?\n")
    print("⚠ Measures artwork against the BASE SHEET'S artwork, not canvas size and not the region\n"
          "extent. Upstream pads 3x art into a power-of-two canvas, so a 1024px file holding 768px\n"
          "of art is correct; and a base sheet may carry art outside any declared region.\n")

    bad, non_power_of_two, unread, checked = [], [], [], 0
    for name, imgs in sorted(imgs_of.items()):
        if "Image" not in imgs:
            continue
        base = artwork_extent(UIBITS / imgs["Image"])
        if base is None:
            unread.append((name, imgs["Image"]))
            continue
        bx, by = base[2], base[3]
        if not bx or not by:
            continue
        if base[0] & (base[0] - 1) or base[1] & (base[1] - 1):
            non_power_of_two.append((name, "Image", imgs["Image"], base[:2]))

        for field, density in (("Image2x", 2), ("Image3x", 3), ("Image4x", 4)):
            fn = imgs.get(field)
            if not fn or fn == imgs["Image"]:
                continue                        # same file = deliberate opt-out
            got = artwork_extent(UIBITS / fn)
            if got is None:
                unread.append((name, fn))
                continue
            checked += 1
            cw, chh, ax, ay = got
            if cw & (cw - 1) or chh & (chh - 1):
                non_power_of_two.append((name, field, fn, (cw, chh)))
            rx, ry = ax / bx, ay / by
            if abs(rx - density) > TOLERANCE or abs(ry - density) > TOLERANCE:
                bad.append((name, field, fn, density, (bx, by), (ax, ay), (rx, ry), (cw, chh)))

    print(f"Checked **{checked}** scale variants.\n")

    if bad:
        print("## ⛔ Artwork laid out at the wrong density\n")
        print("| collection | field | file | base artwork | expected | actual | implied density |")
        print("|---|---|---|--:|--:|--:|--:|")
        for name, field, fn, d, b, got, r, canvas in bad:
            print(f"| {name} | `{field}` | `{fn}` | {b[0]}x{b[1]} | {b[0]*d}x{b[1]*d} "
                  f"| **{got[0]}x{got[1]}** | **{r[0]:.2f}x / {r[1]:.2f}x** (declared {d}x) |")
        print()

    if non_power_of_two:
        print("## ⛔ Runtime texture canvas is not power-of-two\n")
        print("| collection | field | file | canvas |")
        print("|---|---|---|--:|")
        for name, field, fn, canvas in non_power_of_two:
            print(f"| {name} | `{field}` | `{fn}` | **{canvas[0]}x{canvas[1]}** |")
        print()

    if unread:
        print("## ⚠ Declared files that could not be read (advisory)\n")
        for name, fn in sorted(set(unread))[:20]:
            print(f"- `{name}` -> `{fn}`")
        print()

    if bad or non_power_of_two:
        print("**FAIL** — see `docs/audit/CHROME_SCALE_BUG.md`.")
        return 1
    print("**PASS** — every variant's artwork matches its declared density.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
