#!/usr/bin/env python3
"""splice_templates.py — regenerate the named weapon families and replace their
`^Warhead_<Family>_<Level>` blocks in mods/cameo/weapons/weapons.yaml in place.

Line-based, structure-preserving: each old block (header + its indented body) is
swapped for the regenerated one; blank separators and all other content are kept.
After splicing, `verify_generator_sync.py` should report drift = 0.

§12.0j family bases (`^Warhead_<Family>`, no level) are PLACED, not just replaced: each one
always sits directly after its family's last levelled template, so a family stays in one
place. A plain append put the CannonAP pilot 22,000 lines from its family and below the
`DO NOT INHERIT BELOW THIS LINE` divider. The rule is idempotent (a base already in place is
removed and put back at the same spot).

Usage: python tools/balance/splice_templates.py laser railgun tesla teslacharged prism
       python tools/balance/splice_templates.py --all      # every family the generator emits
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
F = ROOT / "mods" / "cameo" / "weapons" / "weapons.yaml"
GEN = Path(__file__).with_name("gen_weapon_template.py")


def parse_blocks(text):
    """{header_without_colon: [header line, indented body lines...]}"""
    blocks, lines, i = {}, text.split("\n"), 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("^Warhead_") and ln.rstrip().endswith(":"):
            name = ln.rstrip()[:-1]
            body = [ln]
            i += 1
            while i < len(lines) and lines[i] and lines[i][0] in " \t":
                body.append(lines[i])
                i += 1
            blocks[name] = body
        else:
            i += 1
    return blocks


LEVEL_SUFFIXES = ("Light", "Medium", "Heavy", "Super", "Trace")


def family_from(name: str) -> str:
    """'^Warhead_Family_Level' -> 'Family'; a level-less base '^Warhead_Family' -> 'Family'."""
    parts = name.split("_")
    if len(parts) == 2:
        return parts[1]
    return "_".join(parts[1:-1]) if len(parts) >= 3 else name


def base_names(all_gen):
    """The generated §12.0j bases: level-less headers that have a levelled sibling."""
    return {n for n in all_gen
            if n.rsplit("_", 1)[-1] not in LEVEL_SUFFIXES
            and any(f"{n}_{s}" in all_gen for s in LEVEL_SUFFIXES)}


def _block_end(lines, i):
    """Index just past the block whose header is at `i` (header + indented body)."""
    i += 1
    while i < len(lines) and lines[i] and lines[i][0] in " \t":
        i += 1
    return i


def remove_blocks(lines, names):
    """`lines` without the named blocks, each taken with the blank separator before it."""
    out, i = [], 0
    while i < len(lines):
        head = lines[i].rstrip()
        if head.startswith("^Warhead_") and head.endswith(":") and head[:-1] in names:
            if out and out[-1] == "":
                out.pop()
            i = _block_end(lines, i)
        else:
            out.append(lines[i])
            i += 1
    return out


def place_base(lines, name, block):
    """Insert `block` right after the last `<name>_<Level>` template; False if there is none.

    ⚠ The base follows its FAMILY, wherever the family sits. 21 families' levelled templates
    were themselves appended below the divider by earlier splices (measured 2026-09-26) and
    are live-inherited from there; moving them is a separate, position-only cleanup, and a
    base must not be split off from the templates it retires."""
    heads = {f"{name}_{s}:" for s in LEVEL_SUFFIXES}
    last = max((i for i, ln in enumerate(lines) if ln.rstrip() in heads), default=None)
    if last is None:
        return False
    end = _block_end(lines, last)
    lines[end:end] = [""] + block
    return True


def main():
    fams = sys.argv[1:]
    if not fams:
        sys.exit("usage: splice_templates.py <family> ... | --all")
    # The generator emits EVERY family when given no family filter, so `--all` is
    # simply the empty filter. Kept explicit rather than implicit: a bare
    # `splice_templates.py` rewriting all 88 templates by accident is not a mistake
    # anyone should be able to make by hitting return.
    if fams == ["--all"]:
        fams = []
    wanted = {f.lower() for f in fams}
    # Always run the full generator so shield_uniqueness sees the whole set and
    # produces correct final Shield values; then keep only the requested blocks.
    out = subprocess.run([sys.executable, str(GEN)], capture_output=True, text=True)
    if out.returncode:
        sys.exit("generator failed:\n" + out.stderr)
    all_gen = parse_blocks(out.stdout)
    if wanted:
        gen = {n: b for n, b in all_gen.items()
               if family_from(n).lower() in wanted}
    else:
        gen = all_gen

    # READ WITH newline="" OR THE LINE-ENDING DETECTION BELOW IS A NO-OP. read_text applies
    # universal-newline translation, so a CRLF file arrives already normalised and the CRLF
    # check never fires; write_text then translates back to os.linesep, so on Windows this
    # tool rewrote EVERY line of weapons.yaml whatever the file actually used.
    #
    # MEASURED, because the obvious conclusion is wrong: the COMMITTED diff was never at risk.
    # .gitattributes carries "*.yaml eol=lf" and "* text=lf", so git normalises on add and
    # shows the same 12 changed lines whichever ending is on disk -- verified by writing CRLF
    # and re-running git diff. What the rewrite actually costs is the WORKING TREE: a plain
    # (non-git) diff reports all 19,882 lines, byte-comparing tools see a fully changed file,
    # editors churn, and git prints a warning on every touch. That is a detour, not a
    # corruption -- but it is free to avoid, and the protection is one .gitattributes edit away
    # from disappearing for any path the patterns stop covering.
    with F.open(encoding="utf-8", newline="") as fh:
        text = fh.read()
    newline = "\r\n" if "\r\n" in text else "\n"
    flines = text.split(newline)
    bases = {n: b for n, b in gen.items() if n in base_names(all_gen)}
    gen = {n: b for n, b in gen.items() if n not in bases}
    flines = remove_blocks(flines, set(bases))
    result, replaced, i = [], [], 0
    while i < len(flines):
        ln = flines[i]
        if ln.startswith("^Warhead_") and ln.rstrip().endswith(":") and ln.rstrip()[:-1] in gen:
            name = ln.rstrip()[:-1]
            i += 1
            while i < len(flines) and flines[i] and flines[i][0] in " \t":
                i += 1  # skip old block body
            result.extend(gen[name])
            replaced.append(name)
        else:
            result.append(ln)
            i += 1
    missing = sorted(set(gen) - set(replaced))
    if missing:
        for m in missing:
            result.append("")
            result.extend(gen[m])
        replaced += missing
    for name, block in bases.items():
        if not place_base(result, name, block):
            result.append("")
            result.extend(block)
        replaced.append(name)
    with F.open("w", encoding="utf-8", newline="") as fh:
        fh.write(newline.join(result))
    print(f"spliced {len(replaced)} blocks: {', '.join(replaced)}")


if __name__ == "__main__":
    main()
