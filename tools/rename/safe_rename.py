#!/usr/bin/env python3
"""Safe rename applicator with dry-run support and validation.

Replaces actor IDs (whole-word, boundary-safe) across all YAML/FTL/Lua files
under mods/cameo, loose map files, and .oramap zips. Protects audio voice
set lines. Optionally renames asset files via git mv.

Key safety features:
  - Two-pass replacement: Fluent key references first (e.g. old_key.description
    -> new_key.description), then standalone IDs. This ensures YAML
    Buildable.Description fields are always updated alongside FTL keys.
  - Pre-flight validation: warns if old names don't exist in the codebase.
  - Post-rename validation: scans for dangling references to old names and
    reports them as ERRORS. Refuses to apply unless --force is given.
  - FTL attribute awareness: handles key.attribute patterns in YAML/FTL.

Usage:
  python tools/rename/safe_rename.py tools/rename/rename_map_<faction>.yaml [--dry-run] [--no-files] [--force]
"""

from __future__ import annotations

import argparse
import io
import pathlib
import re
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
MOD = ROOT / "mods/cameo"


def load_map(path: pathlib.Path) -> tuple[dict[str, str], dict[str, str]]:
    actors: dict[str, str] = {}
    files: dict[str, str] = {}
    section = None
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s == "actors:":
            section = actors
            continue
        if s == "files:":
            section = files
            continue
        if section is not None and ": " in s:
            old, _, new = s.partition(": ")
            section[old.strip()] = new.strip()
    return actors, files


def build_replacer(actors: dict[str, str]):
    """Build a two-pass replacer.

    Pass 1: Replace standalone identifiers (boundary excludes [A-Za-z0-9_.]).
            This handles actor IDs, weapon names, trait references, etc.

    Pass 2: Replace Fluent key references in the form `old_key.attribute`
            where `.attribute` is a Fluent attribute like `.description`
            or `.name`. The key part is replaced, the attribute suffix is
            preserved. This fixes YAML Buildable.Description fields that
            reference FTL keys.

    Matching is case-insensitive, but the replacement keeps the exact case
    written in the rename map so mixed-case OpenRA ids stay canonical.
    """
    lower = {k.lower(): v.lower() for k, v in actors.items()}
    exact = {k.lower(): v for k, v in actors.items()}
    if not lower:
        def sub(text: str) -> tuple[str, int]:
            return text, 0
        return sub
    alts = sorted(lower, key=len, reverse=True)

    # Pass 1: standalone identifiers (dot is a boundary)
    rx1 = re.compile(
        r"(?<![A-Za-z0-9_.])(" + "|".join(re.escape(a) for a in alts) +
        r")(?![A-Za-z0-9_.])", re.IGNORECASE)

    # Pass 2: Fluent key references — old_key followed by .attribute
    # The attribute suffix is typically .description, .name, .tooltip, etc.
    # We only match if the old_key is immediately followed by a dot and
    # a lowercase letter (Fluent attribute convention).
    rx2 = re.compile(
        r"(?<![A-Za-z0-9_.])(" + "|".join(re.escape(a) for a in alts) +
        r")(\.[a-z][A-Za-z0-9_]*)", re.IGNORECASE)

    def sub(text: str) -> tuple[str, int]:
        n = 0

        def repl1(mo: re.Match) -> str:
            nonlocal n
            n += 1
            return exact[mo.group(1).lower()]

        def repl2(mo: re.Match) -> str:
            nonlocal n
            n += 1
            return exact[mo.group(1).lower()] + mo.group(2)

        # Pass 2 first (more specific), then Pass 1
        text, n2 = rx2.subn(repl2, text)
        text, n1 = rx1.subn(repl1, text)
        n = n1 + n2
        return text, n
    return sub


VOICE_LINE = re.compile(r"^\s*VoiceSets?:", re.IGNORECASE)


def audio_voice_keys() -> set[str]:
    keys: set[str] = set()
    for p in (MOD / "audio").glob("*.yaml"):
        for line in p.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            if line and not line[0] in "\t #" and line.rstrip().endswith(":"):
                keys.add(line.rstrip()[:-1].lower())
    return keys


def collect_all_text() -> str:
    """Collect all searchable text for pre-flight validation."""
    chunks: list[str] = []
    for pat in ("**/*.yaml", "**/*.ftl", "**/*.lua"):
        for p in MOD.glob(pat):
            if p.is_file() and (MOD / "audio") not in p.parents:
                try:
                    chunks.append(p.read_text(encoding="utf-8-sig", errors="replace"))
                except Exception:
                    pass
    # Also scan .oramap contents
    for zpath in sorted(MOD.glob("maps/**/*.oramap")):
        try:
            with zipfile.ZipFile(zpath) as zf:
                for info in zf.infolist():
                    if info.filename.lower().endswith((".yaml", ".lua", ".txt")):
                        chunks.append(zf.read(info.filename).decode("utf-8-sig", errors="replace"))
        except Exception:
            pass
    return "\n".join(chunks)


def validate_prerename(actors: dict[str, str], all_text: str) -> list[str]:
    """Check that old names actually exist in the codebase."""
    warnings: list[str] = []
    for old in sorted(actors):
        if old.lower() not in all_text.lower():
            warnings.append(f"WARN: old name '{old}' not found in any file")
    return warnings


def validate_postrename(actors: dict[str, str], all_text: str) -> list[str]:
    """Scan for dangling references to old names after replacement.

    Checks both standalone identifiers (Pass 1 pattern) and Fluent key
    references (Pass 2 pattern — old_key.attribute). This catches the
    exact class of bug that caused the RA1 Soviet regression where
    FTL keys were renamed but YAML Buildable.Description references
    were not.
    """
    errors: list[str] = []
    for old in sorted(actors, key=len, reverse=True):
        # Pass 1: standalone identifier
        rx1 = re.compile(
            r"(?<![A-Za-z0-9_.])" + re.escape(old) +
            r"(?![A-Za-z0-9_.])", re.IGNORECASE)
        # Pass 2: Fluent key reference (old_key.attribute)
        rx2 = re.compile(
            r"(?<![A-Za-z0-9_.])" + re.escape(old) +
            r"(\.[a-z][A-Za-z0-9_]*)", re.IGNORECASE)
        for rx, label in [(rx1, "standalone"), (rx2, "fluent-key")]:
            m = rx.search(all_text)
            if m:
                idx = m.start()
                start = max(0, idx - 30)
                end = min(len(all_text), idx + len(old) + 30)
                context = all_text[start:end].replace("\n", " ").strip()
                errors.append(f"ERROR: old name '{old}' ({label}) still found: ...{context}...")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe rename applicator with validation")
    parser.add_argument("map_path", type=pathlib.Path)
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    parser.add_argument("--no-files", action="store_true", help="Skip asset file renames")
    parser.add_argument("--force", action="store_true",
                        help="Apply even if post-rename validation finds errors")
    args = parser.parse_args()

    actors, files = load_map(args.map_path)
    sub = build_replacer(actors)
    print(f"map: {len(actors)} actor ids, {len(files)} files")
    if not actors:
        print("No actor renames in map. Nothing to do.")
        return 0

    # Pre-flight: check for voice set clashes
    voices = audio_voice_keys()
    clashes = sorted(a for a in actors if a.lower() in voices)
    if clashes:
        print(f"NOTE: these ids also name audio voice sets; audio files and "
              f"VoiceSet lines are protected: {', '.join(clashes)}")

    # Pre-flight validation: check old names exist
    print("\n--- Pre-flight validation ---")
    all_text_before = collect_all_text()
    pre_warnings = validate_prerename(actors, all_text_before)
    if pre_warnings:
        for w in pre_warnings:
            print(f"  {w}")
        print(f"  ({len(pre_warnings)} warnings)")
    else:
        print("  All old names found in codebase. OK.")

    # Pre-write validation: simulate replacement and check for dangling refs
    print("\n--- Pre-write validation (simulated) ---")
    simulated, _ = sub(all_text_before)
    pre_errors = validate_postrename(actors, simulated)
    if pre_errors:
        print(f"  FOUND {len(pre_errors)} ERRORS — old names still referenced after rename:")
        for e in pre_errors[:20]:
            print(f"  {e}")
        if len(pre_errors) > 20:
            print(f"  ... and {len(pre_errors) - 20} more")
        print("\n  These references will NOT be updated by the rename.")
        print("  Fix them manually or add them to the rename map.")
        if not args.force:
            print("  Use --force to apply anyway.")
            return 1
    else:
        print("  No dangling references found. OK.")

    # ---- text replacement across the tree --------------------------------- #
    n_files = n_hits = 0
    targets: list[pathlib.Path] = []
    for pat in ("**/*.yaml", "**/*.ftl", "**/*.lua"):
        targets += [p for p in MOD.glob(pat) if p.is_file()]
    for p in sorted(set(targets)):
        if (MOD / "audio") in p.parents:
            continue
        text = p.read_text(encoding="utf-8-sig", errors="replace")
        if VOICE_LINE.search(text):
            out_lines, n = [], 0
            for line in text.split("\n"):
                if VOICE_LINE.match(line):
                    out_lines.append(line)
                    continue
                repl, k = sub(line)
                out_lines.append(repl)
                n += k
            new = "\n".join(out_lines)
        else:
            new, n = sub(text)
        # Also replace filename strings from files: map in YAML files
        fn = 0
        if p.suffix == ".yaml" and files:
            for old_f, new_f in files.items():
                rx_f = re.compile(r"(?<![A-Za-z0-9_.])" + re.escape(old_f)
                                + r"(?![A-Za-z0-9_.])")
                new, k = rx_f.subn(new_f, new)
                fn += k
        if n or fn:
            rel = p.relative_to(MOD)
            parts = []
            if n: parts.append(f"{n} id replacements")
            if fn: parts.append(f"{fn} filename replacements")
            print(f"  {rel}: {', '.join(parts)}")
            if not args.dry_run:
                p.write_text(new, encoding="utf-8", newline="\n")
            n_files += 1
            n_hits += n + fn
    print(f"text: {n_hits} replacements in {n_files} files")

    # (Pre-write validation already done above — no need to repeat here)

    # ---- .oramap zips ------------------------------------------------------ #
    n_maps = 0
    for zpath in sorted(MOD.glob("maps/**/*.oramap")):
        with zipfile.ZipFile(zpath) as zf:
            members = {i.filename: zf.read(i.filename) for i in zf.infolist()}
        changed = False
        for name, data in list(members.items()):
            if not name.lower().endswith((".yaml", ".lua", ".txt")):
                continue
            try:
                text = data.decode("utf-8-sig")
            except UnicodeDecodeError:
                continue
            out_lines, n = [], 0
            for line in text.split("\n"):
                if VOICE_LINE.match(line):
                    out_lines.append(line)
                    continue
                repl, k = sub(line)
                out_lines.append(repl)
                n += k
            new_text = "\n".join(out_lines)
            # Also replace filename strings in yaml members
            fn = 0
            if name.lower().endswith((".yaml", ".lua")) and files:
                for old_f, new_f in files.items():
                    rx_f = re.compile(r"(?<![A-Za-z0-9_.])" + re.escape(old_f)
                                    + r"(?![A-Za-z0-9_.])")
                    new_text, k = rx_f.subn(new_f, new_text)
                    fn += k
            if n or fn:
                members[name] = new_text.encode("utf-8")
                changed = True
                print(f"  map {zpath.relative_to(MOD)} / {name}: {n} id + {fn} filename replacements")
        if changed:
            if not args.dry_run:
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    for name, data in members.items():
                        zf.writestr(name, data)
                zpath.write_bytes(buf.getvalue())
            n_maps += 1
    print(f"maps: {n_maps} .oramap files rewritten")

    # ---- loose map yaml files --------------------------------------------- #
    n_loose = 0
    for p in sorted(MOD.glob("maps/**/map.yaml")):
        text = p.read_text(encoding="utf-8-sig", errors="replace")
        new, n = sub(text)
        fn = 0
        if files:
            for old_f, new_f in files.items():
                rx_f = re.compile(r"(?<![A-Za-z0-9_.])" + re.escape(old_f)
                                + r"(?![A-Za-z0-9_.])")
                new, k = rx_f.subn(new_f, new)
                fn += k
        if n or fn:
            rel = p.relative_to(MOD)
            print(f"  loose map {rel}: {n} id + {fn} filename replacements")
            if not args.dry_run:
                p.write_text(new, encoding="utf-8", newline="\n")
            n_loose += 1
    print(f"loose maps: {n_loose} files rewritten")

    # ---- asset file renames ------------------------------------------------ #
    if not args.no_files and files:
        bits = MOD / "bits"
        on_disk: dict[str, pathlib.Path] = {}
        for p in bits.rglob("*"):
            if p.is_file():
                on_disk.setdefault(p.name.lower(), p)
        n_mv = 0
        for old, new in sorted(files.items()):
            if old.lower() == new.lower():
                continue
            src = on_disk.get(old.lower())
            if src is None:
                print(f"  WARN: {old} not found on disk")
                continue
            dst = src.with_name(new)
            print(f"  git mv {src.relative_to(MOD)} -> {dst.relative_to(MOD)}")
            if not args.dry_run:
                subprocess.run(["git", "mv", str(src), str(dst)], cwd=ROOT, check=True)
            n_mv += 1
        print(f"assets: {n_mv} files git-mv'd")

    if args.dry_run:
        print("\n[DRY RUN] No files were modified. Re-run without --dry-run to apply.")
    else:
        # Post-rename validation on actual files
        print("\n--- Post-rename validation ---")
        all_text_after = collect_all_text()
        post_errors = validate_postrename(actors, all_text_after)
        if post_errors:
            print(f"  FOUND {len(post_errors)} ERRORS — old names still referenced:")
            for e in post_errors[:20]:
                print(f"  {e}")
            if len(post_errors) > 20:
                print(f"  ... and {len(post_errors) - 20} more")
            print("\n  WARNING: Some references were not updated. Manual fix needed.")
            return 1
        else:
            print("  All references updated. OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
