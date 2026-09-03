#!/usr/bin/env python3
"""gen_derived_stats.py — write the DERIVED turn rates into yaml.

    python tools/balance/gen_derived_stats.py            # dry run
    python tools/balance/gen_derived_stats.py --apply

Maintainer 2026-08-19: *"we have this rule that all turreted units have a turn rate of movement
speed / 5 and their turrets also rotate with the same turn rate ... the frontal facing units
without a turret should have a turn rate of speed/2.5."* The rules are DESIGN §307–311; they were
audited and never applied, so 168 actors are off-rule.

WHY GENERATE RATHER THAN COMPUTE AT RUNTIME (`DERIVED_STATS_IN_TRAITS.md` §2). The engine's
`ITurnSpeedModifier` / `ITurretTurnSpeedModifier` hooks are integer PERCENTAGE modifiers, so
expressing "TurnSpeed = Speed/5" through them loses the value: a Speed-100 unit wants 20, and from
a base of 512 that is 3%, which is 15 — a 25% error, worse at low speeds. Turn rate is a static
value with no runtime input, so computing it at runtime buys nothing and costs precision. It also
has to stay VISIBLE in yaml because `extract_stats` reads yaml — hide it in C# and pricing goes
blind to it.

THE RULES (whichever `audit_stat_formulas` reports, so the fixer and the checker can never
disagree — this parses that audit's own output rather than reimplementing its classification):

    F8   vehicles                    Mobile.TurnSpeed   = Speed / 5
    F9   turreted vehicles           Turreted.TurnSpeed = Mobile.TurnSpeed
    F10  turretless / frontal        Mobile.TurnSpeed   = 2 x Speed / 5   (artillery: Speed / 5)
    F17  fighters and bombers        Aircraft.TurnSpeed = Speed / 15      (frontal: 2x)
    F19  helicopters and spaceships  Aircraft.TurnSpeed = Speed / 5

⚠ A trait the actor inherits from a `^Template` has no node in the actor's own block, so the
value is written as a LOCAL OVERRIDE (`Mobile:` + `TurnSpeed:`) rather than edited in place.
That is deliberate: editing the shared template would move every other actor that inherits it.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):          # Windows consoles default to cp1252
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[2]

# Which audit section writes which trait's TurnSpeed.
SECTION_TRAIT = {"F8": "Mobile", "F9": "Turreted", "F10": "Mobile",
                 "F17": "Aircraft", "F19": "Aircraft"}

ROW_RE = re.compile(r"^\|\s*(?P<actor>[\w.]+)\s*\|.*?\|\s*expected\s+(?P<want>-?\d+)")
# F9 states no "expected" — it reads `Turreted 26 vs Mobile 13 | must match`, and the value
# to adopt is the MOBILE one.
F9_RE = re.compile(r"^\|\s*(?P<actor>[\w.]+)\s*\|\s*Turreted\s+-?\d+\s+vs\s+Mobile\s+(?P<want>-?\d+)")
SEC_RE = re.compile(r"^##\s+(?P<id>F\d+)\s")


def violations() -> list[tuple[str, str, int]]:
    """[(actor, trait, wanted TurnSpeed)] straight from audit_stat_formulas' own report."""
    out, section = [], None
    proc = subprocess.run([sys.executable, "tools/audit/audit_stat_formulas.py"],
                          cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                          errors="replace")
    for line in proc.stdout.splitlines():
        m = SEC_RE.match(line)
        if m:
            section = m.group("id")
            continue
        if section not in SECTION_TRAIT:
            continue
        r = F9_RE.match(line) if section == "F9" else ROW_RE.match(line)
        if r:
            out.append((r.group("actor"), SECTION_TRAIT[section], int(r.group("want"))))
    return out


def actor_files() -> dict[str, list[pathlib.Path]]:
    """{actor name: [rules files that define it]}, in manifest order.

    ⛔ ONLY the files in `manifest.rules`. Scanning every `*.yaml` under mods/cameo instead
    matched top-level keys in `sequences/*.yaml` and `fluent/*.yaml` that happen to share an
    actor's name, and the first version of this tool duly wrote `Mobile:`/`TurnSpeed:` into
    sequence and translation files. It never converged, which is the only reason it was caught:
    the writes were landing somewhere the resolver never reads.

    OpenRA applies `Rules:` in manifest order and later files override earlier ones, so the LAST
    definition is the one that decides the resolved value — that is the one to edit.
    """
    sys.path.insert(0, str(ROOT / "tools" / "audit"))
    from miniyaml import load_manifest                       # noqa: E402

    index: dict[str, list[pathlib.Path]] = {}
    for path in load_manifest(ROOT).rules:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            if line and not line[0].isspace() and line.rstrip().endswith(":"):
                name = line.rstrip()[:-1].strip()
                if name and not name.startswith("^"):
                    # ⚠ case-INSENSITIVE: OpenRA's actor lookup is, and Outpost2
                    # writes `EDEN_LYNX_ACIDCLOUD:` while the audits report it
                    # lowercase. Nine actors were unreachable without this.
                    index.setdefault(name.lower(), []).append(path)
    return index


def indent_of(s: str) -> int:
    return len(s) - len(s.lstrip("\t "))


def set_turnspeed(path: pathlib.Path, actor: str, trait: str, want: int) -> str:
    """Set `<trait>.TurnSpeed` on `actor` in `path`. Returns a short outcome word."""
    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    want_hdr = f"{actor}:".lower()
    start = next((i for i, l in enumerate(lines)
                  if l.rstrip().lower() == want_hdr), None)
    if start is None:
        return "no-actor"
    end = start + 1
    while end < len(lines) and (not lines[end].strip() or lines[end][:1] in ("\t", " ")):
        end += 1

    # the trait node, with or without an @InstanceName
    trait_re = re.compile(rf"^\t{re.escape(trait)}(@[\w.]+)?:\s*$")
    ti = next((i for i in range(start + 1, end) if trait_re.match(lines[i])), None)
    if ti is None:
        # ⚠ INSERT AFTER THE LAST `Inherits*:` LINE. A node declared BEFORE the inherits is
        # overwritten by the template it pulls in, so a value placed at the top of the block
        # silently loses — `ra2_allies_ifv` kept resolving to ^IFVBase's Turreted 60 no matter
        # how many times this tool 'updated' it, and the loop never converged.
        at = start + 1
        for k in range(start + 1, end):
            if lines[k].lstrip().startswith('Inherits'):
                at = k + 1
        lines[at:at] = [chr(9) + trait + ':', chr(9) + chr(9) + 'TurnSpeed: ' + str(want)]
        path.write_text(chr(10).join(lines), encoding='utf-8')
        return "added-trait"

    base = indent_of(lines[ti])
    j = ti + 1
    while j < end and (not lines[j].strip() or indent_of(lines[j]) > base):
        if lines[j].strip().startswith("TurnSpeed:"):
            lines[j] = f"{lines[j][:indent_of(lines[j])]}TurnSpeed: {want}"
            path.write_text("\n".join(lines), encoding="utf-8")
            return "updated"
        j += 1
    lines[ti + 1:ti + 1] = [f"{'	' * (base + 1)}TurnSpeed: {want}"]
    path.write_text("\n".join(lines), encoding="utf-8")
    return "added-field"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    # ⚠ ITERATE. F9 wants Turreted.TurnSpeed to MATCH Mobile.TurnSpeed, and F8 is busy changing
    # Mobile — so a single pass would copy the value F8 just replaced. Re-reading the audit after
    # each pass makes the two rules converge instead of fighting.
    total = 0
    for attempt in range(1, 5):
        rows = violations()
        if not rows:
            print(f"pass {attempt}: nothing left to derive")
            break
        index = actor_files()
        counts: dict[str, int] = {}
        missing: list[str] = []
        for actor, trait, want in rows:
            files = index.get(actor.lower())
            if not files:
                missing.append(actor)
                continue
            outcome = set_turnspeed(files[-1], actor, trait, want) if args.apply else "would-set"
            counts[outcome] = counts.get(outcome, 0) + 1
        total += sum(counts.values())
        print(f"pass {attempt}: {len(rows)} off-rule  ->  "
              + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())))
        if missing:
            print(f"          {len(missing)} actor(s) not found in any yaml: "
                  f"{', '.join(sorted(set(missing))[:6])}")
        if not args.apply:
            break
    print()
    print(f"{'APPLIED' if args.apply else 'DRY RUN'}: {total} derived turn rates written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
