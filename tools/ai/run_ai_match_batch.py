#!/usr/bin/env python3
"""Run repeated headless AI-vs-AI matches and harvest match-log records.

This is the Stage D data tap of the AI architecture: the schema-2 records in
cameo-ai-matches.jsonl only become useful at volume, and volume needs a
harness — a script and a map rotation, not engine work.

Each matchup is a (faction x bot) vs (faction x bot) pairing on a generated
variant of the duel map. Per the 2026-09-28 maintainer ruling, the default
map is the shipped tournament map "A Nuclear Winter"
(mods/cameo/maps/_ra_a-nuclear-winter.oramap): the harness extracts it into
the support dir, adds the NonCombatant referee seat for the local client,
converts Multi0/Multi1 into map-side bot players (Playable: False + Bot: +
HomeLocation taken from the map's mpspawn actors), and cross-wires their
Enemies. --map can point at the legacy ai_duel_gate_20260928 template dir for
the old generated-fixture behavior.

The variant's map.yaml gets its two duelists patched (Bot/Faction) and their
starting forces written into the Actors: section — headless Launch.Map runs
a Local server, so no lobby bot seating exists and the duelists are map-side
players (Playable: False + Bot:), which SpawnStartingUnits cannot serve; the
harness therefore resolves each faction's StartingUnits group from the mod
yaml and pre-places it.

The local client occupies the map's declared-NonCombatant "Referee" slot —
lobby clients ignore PlayerReference.NonCombatant, so the match writer checks
the declared flag and keeps it out of every bot's opponents/allies. The
referee's "empty" start class loses its conquest objective on the first tick,
so it never blocks game-over. Launch.Benchmark exits the process on GameOver;
ConquestVictoryConditions decides on elimination and the map's locked
TimeLimitManager is the stalemate failsafe (a timed-out duel records both
bots "lost" — an honest draw, not an engine-invented winner).

--team-size N turns each side into an N-player team (2v2+): --bot-a/--bot-b take a
comma-separated bot type per seat (a single name duplicates across both
slots) and the default map becomes the shipped doubles map
mods/cameo/maps/_ra_doubles.oramap, whose consecutive Multi pairs are the
teams (Multi0+Multi1 vs Multi2+Multi3). The engine resolves map-side stances
per ORDERED pair, so each member declares its teammate in Allies: and BOTH
enemy refs in Enemies: (the map's own Creeps hostility is preserved). A 2v2
match appends four schema-2 records sharing one game_uid; the team verdict
is "any member record won" — a teammate eliminated early still records lost.

The fixture locks `gamespeed` to `maximum` (1 ms timestep): bot tests run
uncapped at whatever tick rate the CPU sustains, so decisive matches resolve
many times sooner in wall time. At maximum one in-game minute is 60,000 ticks,
so the fixture offers TimeLimitOptions 0/1/2/3/4/6/9 (tick for tick the
insane-era 0/10/20/30/40/60/90) and the default is 3 = 180,000 ticks: the
ENGINE ends a stalemate at that depth and the match is recorded (both sides
`lost`: a timed-out stalemate has no winner),
where a 30-minute cap (1.8M ticks) left the harness to kill it with no record.
The stall detector
(debug.log goes quiet after its first write this run — arming skips the load
phase) kills hung matches in ~2 minutes while a generous wall bound protects
slow-but-live ones. Run
bot batches serially and prefer an idle machine for consistent timings.

On a shared box a bigger hazard is external kills: another agent's
taskkill/Stop-Process sweep terminates every OpenRA.exe by name, which
surfaces as a bare "exit=N" mid-match — no exception log, no appended
records. Those matches get one automatic retry (--retries); real crashes
write exception-*.log and are never retried. Per-match results also append
to <support>/batch_results.jsonl as they land, so a batch whose driver is
itself swept still leaves usable evidence.

The batch fingerprints its arms once at start (LC7): the mod commit and its
dirty state, the engine VERSION, a sha256 over engine/bin/OpenRA*.dll, a
sha256 over the resolved AI yaml set (mods/**/ai.yaml + mods/**/ai/*.yaml),
the map source, and the batch spec. The fingerprint is recomputed before
every match attempt and any drift aborts the batch — a mid-batch checkout or
rebuild (the auto-sync service landing new yaml under stale DLLs killed
league-3 this way) silently changes the A/B arms otherwise.
--allow-fingerprint-drift records the drift and keeps running.

Usage:
    python tools/ai/run_ai_match_batch.py [options]

    --factions td_gdi,td_nod        factions for the matrix (default: td_gdi,td_nod)
    --bot-a hard --bot-b classic   bot types per side (default: hard — the Frankenstein
                                    candidate — vs the omniscient classic reference bot)
    --repeats 4                     matches per matchup (spawn sides alternate)
    --swap-bots                     also alternate which bot takes which spawn —
                                    the A/B acceptance requires both spawns
    --team-size 2 --bot-a hard,hard --bot-b classic,classic
                                    2v2: one bot type per team slot (a single
                                    name duplicates); teams seat on consecutive
                                    Multi pairs (default map _ra_doubles.oramap)
    --map PATH                      duel map (default: _ra_a-nuclear-winter.oramap)
    --time-limit 30                 per-match cap in minutes (engine options only)
    --support-dir PATH              batch support dir (default: %TEMP%/ai-match-batch-<ts>)
    --dry-run                       print the matrix + variants, launch nothing
    --allow-fingerprint-drift       log mid-batch arm changes and continue
                                    (default: abort — a changed arm voids the A/B)

Exit codes: 0 = batch complete, 2 = no usable records collected, 1 = failure.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

# OpenAL Soft AVs in alcOpenDevice on this host since the .NET 10 / bleed
# update; the null driver gives headless matches a silent device. Same
# workaround as tools/tests/_bootstrap.py — an explicit override still wins.
os.environ.setdefault("ALSOFT_DRIVERS", "null")

TEMPLATE_MAP = REPO_ROOT / "mods" / "cameo" / "maps" / "ai_duel_gate_20260928"

# Maintainer ruling 2026-09-28: all bot-vs-bot testing runs on the real
# tournament duel map "A Nuclear Winter" — generated shell fixtures are only
# kept for the bespoke per-gate maps. Default --map points at the shipped
# .oramap; variants are extracted copies patched in the support dir, so the
# packaged map itself is never touched.
DEFAULT_MAP = REPO_ROOT / "mods" / "cameo" / "maps" / "_ra_a-nuclear-winter.oramap"

# --team-size 2 default: the shipped 4-player doubles map — consecutive Multi
# pairs are the teams (Multi0+Multi1 vs Multi2+Multi3 on its four mpspawns).
DEFAULT_TEAM_MAP = REPO_ROOT / "mods" / "cameo" / "maps" / "_ra_doubles.oramap"

MATCH_LOG = "cameo-ai-matches.jsonl"
CONFIG_KEYS = {"MOD_ID", "ENGINE_DIRECTORY"}
BENCHMARK_PREFIX = "ai-duel-batch-"

# The mod.yaml MapFolders entry for user maps resolves through this literal
# directory name inside the support dir.
USER_MAP_DIR = os.path.join("maps", "cameo", "{DEV_VERSION}")

# The fixture's TimeLimitManager.TimeLimitOptions (rules.yaml): the engine only accepts
# these minute values. At maximum speed 1 min = 60,000 ticks, so they equal the
# insane-era 0/10/20/30/40/60/90 caps tick for tick.
VALID_TIME_LIMITS = {0, 1, 2, 3, 4, 6, 9}
TICKS_PER_MINUTE = 60 * 1000  # maximum: Timestep 1 ms


def fail(message: str, record=None) -> None:
    print(f"ASSERTION FAILED: {message}")
    if record is not None:
        print(f"Offending record: {json.dumps(record, sort_keys=True)}")
    raise SystemExit(1)


def read_config(path: pathlib.Path, values: dict[str, str]) -> None:
    if not path.is_file():
        return

    assignment = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")
    for line in path.read_text(encoding="utf-8").splitlines():
        match = assignment.match(line)
        if not match or match.group(1) not in CONFIG_KEYS:
            continue

        value = match.group(2)
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[match.group(1)] = value


def load_config() -> tuple[str, pathlib.Path]:
    values: dict[str, str] = {}
    read_config(REPO_ROOT / "mod.config", values)
    read_config(REPO_ROOT / "user.config", values)

    mod_id = values.get("MOD_ID")
    engine_directory = values.get("ENGINE_DIRECTORY")
    if not mod_id:
        fail("mod.config/user.config did not define MOD_ID")
    if not engine_directory:
        fail("mod.config/user.config did not define ENGINE_DIRECTORY")

    engine = pathlib.Path(engine_directory)
    if not engine.is_absolute():
        engine = REPO_ROOT / engine
    return mod_id, engine.resolve()


def build_matchups(
    factions: list[str],
    bots_a: list[str],
    bots_b: list[str],
    repeats: int,
    swap_bots: bool = False,
    team_size: int = 1,
) -> list[dict]:
    """One unordered faction pair per matchup; repeats alternate spawn sides.

    Spawn side is a real axis (corner map geometry is asymmetric), so repeat
    parity swaps which faction occupies slot A/B. With --swap-bots the bot
    assignment alternates too — required for the A/B acceptance runs, where a
    bot must win from BOTH spawns, not just the lucky one. Mirrors (same
    faction both sides) are included: mirror records are honest 1v1 data.

    team_size=2 (2v2): each side is a team of `team_size` members sharing the
    side's faction. `team_a`/`team_b` are the occupants of the consecutive
    Multi seat pairs `slots_a`/`slots_b` — the same alternation as 1v1 applies
    to the PAIR: repeat parity swaps which faction's team sits on pair (0,1),
    and --swap-bots alternates which bot team sits on pair (0,1) (the
    swap-both-spawns acceptance, per team). Member m of a team binds
    `Multi{slots[m]}`.
    """
    matchups = []
    for index, (fa, fb) in enumerate(itertools.combinations_with_replacement(factions, 2)):
        for repeat in range(repeats):
            if repeat % 2 == 0:
                a, b = fa, fb
            else:
                a, b = fb, fa
            ba, bb = (bots_a, bots_b) if not (swap_bots and repeat % 2 == 1) else (bots_b, bots_a)
            if team_size >= 2:
                matchups.append(
                    {
                        "index": index,
                        "repeat": repeat,
                        "team_size": team_size,
                        "team_a": [{"bot": bot, "faction": a} for bot in ba],
                        "team_b": [{"bot": bot, "faction": b} for bot in bb],
                        "slots_a": list(range(team_size)),
                        "slots_b": list(range(team_size, 2 * team_size)),
                        "variant": f"ai_{team_size}v{team_size}_{a}_{'_'.join(ba)}__vs__{b}_{'_'.join(bb)}".replace(" ", "_"),
                    }
                )
            else:
                matchups.append(
                    {
                        "index": index,
                        "repeat": repeat,
                        "side_a": {"faction": a, "bot": ba[0]},
                        "side_b": {"faction": b, "bot": bb[0]},
                        "variant": f"ai_duel_{a}_{ba[0]}_vs_{b}_{bb[0]}".replace(" ", "_"),
                    }
                )
    return matchups


def patch_player_block(text: str, ref: str, bot: str, faction: str) -> str:
    """Rewrite the Bot/Faction lines inside one PlayerReference block and
    return (text, home_location).

    The template is ours and keeps sentinel values (Bot: hard,
    Faction: td_gdi/td_nod), so a block-scoped first-match replace is exact —
    and every patch asserts the expected line existed exactly once.
    """
    marker = f"\tPlayerReference@{ref}:"
    start = text.find(marker)
    if start < 0:
        fail(f"template map is missing {marker}")
    end = text.find("\n\tPlayerReference@", start + len(marker))
    block_end = len(text) if end < 0 else end
    block = text[start:block_end]

    home_match = re.search(r"^\t\tHomeLocation: (\d+),(\d+)$", block, re.MULTILINE)
    if not home_match:
        fail(f"{marker} block is missing HomeLocation", block)
    home = (int(home_match.group(1)), int(home_match.group(2)))

    for key, value in (("Bot", bot), ("Faction", faction)):
        pattern = re.compile(rf"^\t\t{key}: .+$", re.MULTILINE)
        found = pattern.findall(block)
        if len(found) != 1:
            fail(f"{marker} block does not contain exactly one '{key}:' line", block)
        block = pattern.sub(f"\t\t{key}: {value}", block, count=1)

    return text[:start] + block + text[block_end:], home


# The StartingUnitsInfo TraitInfos live on World across rules/*.yaml and the
# ContentPacks — the same source the engine resolves, scanned read-only.
UNIT_GROUP_SEARCH = (
    REPO_ROOT / "mods" / "cameo" / "rules",
    REPO_ROOT / "mods" / "cameo" / "ContentPacks",
)
UNIT_GROUP_RE = re.compile(r"^\s*StartingUnits@\w+:\n((?:(?!\s*StartingUnits@)[ \t]+[^\n]*\n)*)", re.MULTILINE)

# Support actors ring the base actor, mirroring SpawnStartingUnits' annulus
# on a controlled flat fixture. Minimum distance 4 keeps the MCV deploy
# footprint clear — a tighter ring once left a bot unable to deploy.
SUPPORT_RING = [(4, 0), (0, 4), (-4, 0), (0, -4), (4, 3), (-4, 3), (4, -3), (-4, -3),
                (3, 4), (-3, 4), (3, -4), (-3, -4)]

_group_cache: dict[tuple[str, str], tuple[str, list[str]] | None] = {}


def starting_unit_group(faction: str, cls: str) -> tuple[str, list[str]] | None:
    """Resolve (base_actor, support_actors) for a faction+class from the mod's
    StartingUnits blocks. Multiple groups per class are engine-randomized; the
    harness deterministically picks the first in scan order (fixtures do not
    need coverage of every variant)."""
    key = (faction, cls)
    if key in _group_cache:
        return _group_cache[key]

    files = sorted(UNIT_GROUP_SEARCH[0].glob("*.yaml"))
    files += sorted(UNIT_GROUP_SEARCH[1].rglob("*.yaml"))
    found = None
    for path in files:
        for match in UNIT_GROUP_RE.finditer(path.read_text(encoding="utf-8", errors="replace")):
            block = match.group(1)
            cls_match = re.search(r"^\s*Class:\s*(\S+)\s*$", block, re.MULTILINE)
            fac_match = re.search(r"^\s*Factions:\s*(.+)$", block, re.MULTILINE)
            if not cls_match or not fac_match or cls_match.group(1) != cls:
                continue
            if faction not in (f.strip() for f in fac_match.group(1).split(",")):
                continue
            base = re.search(r"^\s*BaseActor:\s*(\S+)\s*$", block, re.MULTILINE)
            supports = re.search(r"^\s*SupportActors:\s*(.+)$", block, re.MULTILINE)
            found = (
                base.group(1) if base else None,
                [s.strip() for s in supports.group(1).split(",") if s.strip()] if supports else [],
            )
            break
        if found is not None:
            break

    _group_cache[key] = found
    return found


ACTOR_SENTINEL = "\t# AI_DUEL_BOT_UNITS"


def render_side_actors(ref: str, faction: str, home: tuple[int, int]) -> str:
    """Map Actors nodes owning the faction's starting force to the map-side
    bot. Prefer 'light' (MCV + escorts — a real skirmish start); fall back to
    'none' (MCV only); fail loudly when a faction has neither."""
    group = starting_unit_group(faction, "light") or starting_unit_group(faction, "none")
    if group is None or group[0] is None:
        fail(f"faction {faction} has no StartingUnits group for class light or none")

    base, supports = group
    lines = [
        f"\t{ref}_base: {base}",
        "\t\tOwner: " + ref,
        f"\t\tLocation: {home[0]},{home[1]}",
    ]
    for index, actor in enumerate(supports[: len(SUPPORT_RING)]):
        dx, dy = SUPPORT_RING[index]
        lines += [
            f"\t{ref}_u{index}: {actor}",
            "\t\tOwner: " + ref,
            f"\t\tLocation: {home[0] + dx},{home[1] + dy}",
        ]
    return "\n".join(lines) + "\n"


def inject_starting_actors(text: str, sides: list[tuple[str, str, tuple[int, int]]]) -> str:
    """Replace the AI_DUEL_BOT_UNITS sentinel with generated Actors nodes."""
    if text.count(ACTOR_SENTINEL) != 1:
        fail("template map.yaml must contain exactly one AI_DUEL_BOT_UNITS sentinel")
    rendered = "".join(render_side_actors(ref, faction, home) for ref, faction, home in sides)
    return text.replace(ACTOR_SENTINEL, rendered.rstrip("\n"))


def mp_spawn_cells(map_text: str) -> list[tuple[int, int]]:
    """mpspawn actor locations in file order — the lobby binds Multi slots in
    the same order, so entry 0 is Multi0's home cell, entry 1 is Multi1's."""
    cells = []
    for match in re.finditer(
        r"^\t\w+: mpspawn\n\t\tOwner: \w+\n\t\tLocation: (\d+),(\d+)$",
        map_text, re.MULTILINE,
    ):
        cells.append((int(match.group(1)), int(match.group(2))))
    if len(cells) < 2:
        fail("real-map mode needs a map with at least two mpspawn actors")
    return cells


def split_spawn_sides(cells: list[tuple[int, int]], team_size: int) -> list[tuple[int, int]]:
    """Return spawn cells reordered so indices 0..team_size-1 are one geographic
    half of the map and team_size..2*team_size-1 are the other.

    Slots bind teams by index (slots_a = range(n)), but shipped maps interleave
    mpspawn file order across sides — on order-of-battle-rich that spawned a
    hard bot inside the classic half (maintainer report 2026-10-02). Splitting
    by the two farthest-apart seeds and ranking every cell by signed
    nearer-seed distance gives a deterministic, orientation-free split that
    also works when the side count is odd or the halves differ in size."""
    cells = cells[: 2 * team_size]
    far = (-1, 0, 1)
    for i in range(len(cells)):
        for j in range(i + 1, len(cells)):
            d = (cells[i][0] - cells[j][0]) ** 2 + (cells[i][1] - cells[j][1]) ** 2
            if d > far[0]:
                far = (d, i, j)

    s0, s1 = cells[far[1]], cells[far[2]]
    ranked = sorted(
        cells,
        key=lambda c: (c[0] - s0[0]) ** 2 + (c[1] - s0[1]) ** 2 - (c[0] - s1[0]) ** 2 - (c[1] - s1[1]) ** 2,
    )
    side_a, side_b = ranked[:team_size], ranked[team_size:]
    return sorted(side_a) + sorted(side_b)


REFEREE_BLOCK = """\tPlayerReference@Referee:
\t\tName: Referee
\t\tPlayable: True
\t\tRequired: True
\t\tAllowBots: False
\t\tNonCombatant: True
\t\tFaction: td_gdi
\t\tLockFaction: True
\t\tStartingUnitsClass: empty
"""


def _append_merge_relation(block: str, key: str, refs: list[str]) -> str:
    """Append-merge refs into a block's `\t\t{key}:` line (Enemies:/Allies:).

    Existing entries keep their position (a shipped map's `Enemies: Creeps`
    stays first) and are never duplicated; absent keys get a new line.
    """
    pattern = re.compile(rf"^\t\t{key}: .+$", re.MULTILINE)
    declared = pattern.search(block)
    existing = [e.strip() for e in declared.group(0).split(":", 1)[1].split(",")] if declared else []
    additions = [r for r in refs if r not in existing]
    if declared:
        if additions:
            block = pattern.sub(lambda _: declared.group(0) + ", " + ", ".join(additions), block, count=1)
    elif refs:
        block += f"\t\t{key}: {', '.join(refs)}\n"
    return block


def patch_mp_block(
    text: str,
    ref: str,
    bot: str,
    faction: str,
    home: tuple[int, int],
    other_refs,
    ally_refs=(),
) -> str:
    """Convert a Playable Multi slot into a map-side bot duelist.

    Multi refs on shipped maps carry `Playable: True` + `Faction: Random` and
    no Bot/HomeLocation — the bot's home comes from an mpspawn actor instead.
    We write everything the map-side bot branch honors and declare every
    stance explicitly while keeping the map's declared Creeps hostility.

    `other_refs` (a ref name or a list of them) are append-merged into
    `Enemies:`; `ally_refs` into `Allies:`. The engine resolves map-side
    stances per ORDERED pair (CreateMapPlayers.SetupPlayerMasks), so team
    play needs both directions declared on every member: each teammate gets
    `Allies: <mate>` and each side's members list BOTH enemy refs.
    """
    if isinstance(other_refs, str):
        other_refs = [other_refs]
    marker = f"\tPlayerReference@{ref}:"
    start = text.find(marker)
    if start < 0:
        fail(f"map is missing {marker}")

    # The block ends at the next player OR the next top-level key (e.g.
    # Actors:) — whichever comes first. The last PlayerReference otherwise
    # slices to EOF and swallows every section that follows Players:.
    candidates = []
    next_ref = text.find("\n\tPlayerReference@", start + len(marker))
    if next_ref >= 0:
        candidates.append(next_ref)
    next_key = re.search(r"\n\S", text[start + len(marker):])
    if next_key:
        candidates.append(start + len(marker) + next_key.start())
    block_end = min(candidates) if candidates else len(text)

    block = text[start:block_end].rstrip("\n") + "\n"

    for key, value in (("Playable", "False"), ("Bot", bot), ("Faction", faction)):
        pattern = re.compile(rf"^\t\t{key}: .+$", re.MULTILINE)
        if pattern.search(block):
            block = pattern.sub(f"\t\t{key}: {value}", block, count=1)
        else:
            block += f"\t\t{key}: {value}\n"

    block += f"\t\tHomeLocation: {home[0]},{home[1]}\n"

    block = _append_merge_relation(block, "Enemies", list(other_refs))
    block = _append_merge_relation(block, "Allies", list(ally_refs))

    return text[:start] + block + text[block_end:]


def write_variant_from_oramap(oramap: pathlib.Path, dest: pathlib.Path, matchup: dict, time_limit: int) -> None:
    """Extract a shipped .oramap into a variant dir and convert its Multi slots
    into map-side bot duelists. The referee seat is added for the local client;
    the duel gate's rules.yaml supplies the locked maximum speed, time cap and
    restored MustBeDestroyed bases that real elimination needs."""
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    with zipfile.ZipFile(oramap) as archive:
        archive.extractall(dest)

    map_yaml = dest / "map.yaml"
    text = map_yaml.read_text(encoding="utf-8")

    spawns = mp_spawn_cells(text)
    team_size = matchup.get("team_size", 1)
    if team_size >= 2:
        if len(spawns) < 2 * team_size:
            fail(f"team-size {team_size} needs a map with at least {2 * team_size} mpspawn actors, got {len(spawns)}")
        spawns = split_spawn_sides(spawns, team_size) + spawns[2 * team_size :]
        for i in range(2 * team_size):
            ref = f"Multi{i}"
            if text.count(f"	PlayerReference@{ref}:") != 1:
                fail(f"team-size {team_size} expects exactly one PlayerReference@{ref} block")
    if not re.search(r"^Rules: ", text, re.MULTILINE):
        categories = re.search(r"^Categories: .+$", text, re.MULTILINE)
        if not categories:
            fail("map.yaml has no Categories line to anchor the Rules key")
        text = text[:categories.end()] + "\n\nRules: rules.yaml" + text[categories.end():]

    marker = "\tPlayerReference@Multi0:"
    if text.count(marker) != 1:
        fail("real-map mode expects exactly one PlayerReference@Multi0 block")
    text = text.replace(marker, REFEREE_BLOCK + marker, 1)

    if team_size >= 2:
        slots_a = matchup["slots_a"]
        slots_b = matchup["slots_b"]
        sides = []
        for slots, team, enemy_slots in (
            (slots_a, matchup["team_a"], slots_b),
            (slots_b, matchup["team_b"], slots_a),
        ):
            enemy_refs = [f"Multi{s}" for s in enemy_slots]
            for member_index, slot in enumerate(slots):
                ref = f"Multi{slot}"
                member = team[member_index]
                text = patch_mp_block(
                    text, ref, member["bot"], member["faction"], spawns[slot],
                    enemy_refs,
                    ally_refs=[f"Multi{s}" for s in slots if s != slot],
                )
                sides.append((ref, member["faction"], spawns[slot]))
    else:
        text = patch_mp_block(text, "Multi0", matchup["side_a"]["bot"], matchup["side_a"]["faction"], spawns[0], "Multi1")
        text = patch_mp_block(text, "Multi1", matchup["side_b"]["bot"], matchup["side_b"]["faction"], spawns[1], "Multi0")

        sides = [
            ("Multi0", matchup["side_a"]["faction"], spawns[0]),
            ("Multi1", matchup["side_b"]["faction"], spawns[1]),
        ]
    rendered = "".join(render_side_actors(ref, faction, home) for ref, faction, home in sides)
    text = text.rstrip("\n") + "\n" + rendered
    text += f"\n# ai-match-batch variant: {dest.name}\n"
    map_yaml.write_text(text, encoding="utf-8")

    shutil.copyfile(TEMPLATE_MAP / "rules.yaml", dest / "rules.yaml")
    rules_yaml = dest / "rules.yaml"
    rules = rules_yaml.read_text(encoding="utf-8")
    patched, count = re.subn(r"TimeLimitDefault: \d+", f"TimeLimitDefault: {time_limit}", rules)
    if count != 1:
        fail("variant rules.yaml is missing exactly one TimeLimitDefault line")
    rules_yaml.write_text(patched, encoding="utf-8")


def write_variant(template: Path, dest: pathlib.Path, matchup: dict, time_limit: int) -> None:
    if template.suffix == ".oramap":
        write_variant_from_oramap(template, dest, matchup, time_limit)
        return

    if matchup.get("team_size", 1) != 1:
        fail("the legacy template dir only supports --team-size 1 (it has BotA/BotB, no Multi slots)")
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(template, dest)

    map_yaml = dest / "map.yaml"
    text = map_yaml.read_text(encoding="utf-8")
    text, home_a = patch_player_block(text, "BotA", matchup["side_a"]["bot"], matchup["side_a"]["faction"])
    text, home_b = patch_player_block(text, "BotB", matchup["side_b"]["bot"], matchup["side_b"]["faction"])
    text = inject_starting_actors(
        text,
        [
            ("BotA", matchup["side_a"]["faction"], home_a),
            ("BotB", matchup["side_b"]["faction"], home_b),
        ],
    )
    # Map.ComputeUID hashes file bytes: two variants with identical patched
    # content share one uid, so MapCache merges them into a single preview and
    # Launch.Map's name lookup can only find whichever dir enumerated last.
    # A per-destination comment salt keeps every variant's uid unique.
    text += f"\n# ai-match-batch variant: {dest.name}\n"
    map_yaml.write_text(text, encoding="utf-8")

    rules_yaml = dest / "rules.yaml"
    rules = rules_yaml.read_text(encoding="utf-8")
    patched, count = re.subn(r"TimeLimitDefault: \d+", f"TimeLimitDefault: {time_limit}", rules)
    if count != 1:
        fail("variant rules.yaml is missing exactly one TimeLimitDefault line")
    rules_yaml.write_text(patched, encoding="utf-8")


def output_tail(output: str) -> str:
    lines = output.splitlines()
    return "\n".join(lines[-40:]) if len(lines) > 40 else output


def run_match(
    executable: pathlib.Path,
    engine: pathlib.Path,
    args: list[str],
    timeout: int,
    stall_log: pathlib.Path | None = None,
    stall_timeout: int = 120,
) -> tuple[int, str, str]:
    """Returns (exit_code, output, status).

    status is one of:
      "ok"       — the process exited 0 (match resolved, records written)
      "timeout"  — the wall bound was hit and we terminated it
      "stalled"  — stall_log went quiet for stall_timeout seconds; the world
                   is hung, not slow, so we terminated it
      "exit=N"   — the process exited nonzero on its own. The engine's own
                   exits are 0 (Success) and -1 (fatal error + exception
                   log); a bare nonzero exit — especially code 1, the
                   TerminateProcess signature — means an external kill
                   (e.g. another agent's taskkill/Stop-Process sweep
                   targeting every OpenRA.exe by name).

    A fixture match that is alive writes to debug.log continuously (AI module
    timing lines every ~300 ticks), so a quiet stall_log means a hang. The
    detector arms only after the first log write newer than spawn: mod
    loading can legitimately take a minute under CPU contention, and the log
    file is shared across matches in a batch — the previous match's mtime
    must not arm the next match's window.
    """
    # BELOW_NORMAL priority (Windows): an uncapped match uses every cycle it gets; the maintainer's desktop and input
    # must stay responsive (2026-10-01: 7 instances froze the mouse). The game still gets all otherwise-idle CPU.
    priority = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0) if os.name == "nt" else 0
    process = subprocess.Popen(
        [str(executable), *args],
        cwd=engine,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=priority,
    )

    output_parts = []

    def drain():
        for line in process.stdout:
            output_parts.append(line)

    pump = threading.Thread(target=drain, daemon=True)
    pump.start()

    timed_out = False
    stalled = False
    deadline = time.monotonic() + timeout
    spawn_time = time.time()
    last_write = spawn_time
    log_seen = False
    while process.poll() is None:
        time.sleep(5)
        if stall_log is not None:
            try:
                mtime = stall_log.stat().st_mtime
            except OSError:
                mtime = 0
            if mtime > spawn_time:
                log_seen = True
                last_write = max(last_write, mtime)
            if log_seen and time.time() - last_write > stall_timeout:
                stalled = True
                break
        if time.monotonic() > deadline:
            timed_out = True
            break

    if stalled or timed_out:
        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    pump.join(timeout=10)
    if timed_out:
        status = "timeout"
    elif stalled:
        status = "stalled"
    elif process.returncode == 0:
        status = "ok"
    else:
        status = f"exit={process.returncode}"
    return process.returncode, "".join(output_parts), status


def read_appended_records(log_path: pathlib.Path, before_length: int) -> list[dict]:
    if not log_path.is_file() or log_path.stat().st_size <= before_length:
        return []
    appended = log_path.read_bytes()[before_length:].decode("utf-8")
    records = []
    for line in appended.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


SPAWN_INDEX_BY_SLOT = {"Multi0": 0, "Multi1": 1, "Multi2": 2, "Multi3": 3, "BotA": 0, "BotB": 1}


def ab_scoreboard(results: list[dict]) -> dict:
    """Head-to-head table keyed by ordered (bot_type, enemy_bot_type) pairs.

    Each duel writes one record per side; both perspectives land in their
    own ordered row, so the board stays symmetric. Exact duplicates (same
    record_id) are skipped. Values are {"won", "lost", "spawn"} - the spawn
    axis keeps the A/B honest about start-position asymmetry.
    """
    seen_records: set[str] = set()
    board: dict[tuple[str, str], dict] = {}
    for result in results:
        for record in result.get("bot_outcomes") or []:
            record_id = str(record.get("record_id") or "")
            if not record_id or record_id in seen_records:
                continue
            seen_records.add(record_id)
            player = record
            opponent = record.get("opponent") or {}
            outcome = player.get("outcome")
            if outcome not in ("won", "lost"):
                continue
            key = (str(player.get("bot_type")), str(opponent.get("bot_type")))
            cell = board.setdefault(key, {"won": 0, "lost": 0, "spawn": {}})
            cell["won" if outcome == "won" else "lost"] += 1
            spawn = player.get("spawn")
            if spawn is not None:
                side = cell["spawn"].setdefault(str(spawn), [0, 0])
                side[0 if outcome == "won" else 1] += 1
    return {f"{a} vs {b}": cell for (a, b), cell in sorted(board.items())}


def team_scoreboard(results: list[dict]) -> dict:
    """Team-mode head-to-head: group records by match uid, then by TEAM.

    A 2v2 match appends four records sharing one game_uid
    (`record_id.rsplit("|", 1)[0]`). Each record's team is
    {player.name} ∪ {allies[].name}; its board key is the sorted "+"-joined
    member bot_types ("hard+hard"). Team verdict mirrors
    ConquestVictoryConditions: the team won iff ANY member record reads
    "won" (a teammate eliminated early still records "lost"). Each match
    lands in both ordered pairings — same symmetric convention as
    ab_scoreboard — and the spawn sub-table keys the team's sorted
    member-spawn pair ("0,1").
    """
    seen_records: set[str] = set()
    matches: dict[str, list[dict]] = {}
    for result in results:
        for record in result.get("bot_outcomes") or []:
            record_id = str(record.get("record_id") or "")
            if not record_id or record_id in seen_records:
                continue
            seen_records.add(record_id)
            matches.setdefault(record_id.rsplit("|", 1)[0], []).append(record)

    board: dict[str, dict] = {}
    for rows in matches.values():
        by_members: dict[frozenset, dict] = {}
        for row in rows:
            allies = row.get("allies") or []
            members = frozenset(
                {str(row.get("record_id") or "").rsplit("|", 1)[1]}
                | {str(a.get("name")) for a in allies}
            )
            team = by_members.get(members)
            if team is None:
                bots = sorted(
                    [str(row.get("bot_type"))] + [str(a.get("bot_type")) for a in allies]
                )
                team = {"key": "+".join(bots), "won": False, "spawns": set()}
                by_members[members] = team
            if row.get("outcome") == "won":
                team["won"] = True
            if row.get("spawn") is not None:
                team["spawns"].add(str(row["spawn"]))
        teams = list(by_members.values())
        if len(teams) != 2:
            continue
        for mine, theirs in ((teams[0], teams[1]), (teams[1], teams[0])):
            cell = board.setdefault(f"{mine['key']} vs {theirs['key']}",
                                    {"won": 0, "lost": 0, "spawn": {}})
            cell["won" if mine["won"] else "lost"] += 1
            spawn_key = ",".join(sorted(mine["spawns"]))
            if spawn_key:
                slot = cell["spawn"].setdefault(spawn_key, [0, 0])
                slot[0 if mine["won"] else 1] += 1
    return {key: board[key] for key in sorted(board)}


# ---------------------------------------------------------------------------
# LC7 — the A/B fingerprint
#
# A batch's "arms" are not just the bot names on the command line: the mod
# checkout, the built DLLs, the resolved AI yaml, the map source and the
# batch spec all decide what is actually being compared. A mid-batch change —
# the auto-sync service fast-forwarding the checkout, a rebuild landing in
# engine/bin, a map edit — silently swaps the arms (league-3 lost 15 matches
# to new yaml meeting stale DLLs). The fingerprint is therefore computed once
# at batch start and recomputed before EVERY match attempt; any drift aborts
# the batch unless --allow-fingerprint-drift was passed.
# ---------------------------------------------------------------------------

FINGERPRINT_GIT_PATHS = (
    "mods",
    "OpenRA.Mods.CA",
    "OpenRA.Mods.Cameo",
    "OpenRA.Mods.Fransbot",
    "tools/ai",
)


def _git(repo_root: pathlib.Path, *args: str) -> str | None:
    """stdout of a git call against the mod checkout, or None when git or the
    repository itself is unavailable (no git binary, non-git tree, timeout)."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout if proc.returncode == 0 else None


def _hash_files(base: pathlib.Path, files: list[pathlib.Path]) -> str:
    """One sha256 over (relative name, bytes) per file in sorted order — set
    membership and contents both move the digest; an empty set hashes clean."""
    digest = hashlib.sha256()
    for path in sorted(files, key=lambda p: p.relative_to(base).as_posix()):
        digest.update(path.relative_to(base).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _mod_dlls_sha256(engine: pathlib.Path) -> str | None:
    """sha256 over the sorted engine/bin/OpenRA*.dll set — catches a mid-batch
    `dotnet build` changing behavior without changing any commit."""
    bin_dir = engine / "bin"
    if not bin_dir.is_dir():
        return None
    return _hash_files(bin_dir, [p for p in bin_dir.glob("OpenRA*.dll") if p.is_file()])


def _ai_yaml_sha256(mods_root: pathlib.Path) -> tuple[str, int]:
    """(digest, file count) over the AI yaml the engine resolves: the union of
    mods/**/ai.yaml and mods/**/ai/*.yaml. An empty set is still a valid
    digest (hash of nothing) — only the count distinguishes it."""
    files: list[pathlib.Path] = []
    if mods_root.is_dir():
        files = [
            p for p in set(mods_root.rglob("ai.yaml")) | set(mods_root.glob("**/ai/*.yaml"))
            if p.is_file()
        ]
    return _hash_files(mods_root, files), len(files)


def _mod_yaml_sha256(mods_root: pathlib.Path) -> tuple[str, int]:
    """(digest, file count) over EVERY mods/**/*.yaml — the rules side of the
    arms. A weapon/rules edit mid-batch changes what the match actually plays
    just as much as an ai.yaml change, and the boolean mod_dirty flag cannot
    tell two different dirty states apart. An empty set is still a valid
    digest — only the count distinguishes it."""
    files: list[pathlib.Path] = []
    if mods_root.is_dir():
        files = [p for p in mods_root.rglob("*.yaml") if p.is_file()]
    return _hash_files(mods_root, files), len(files)


def _map_sha256(map_source: pathlib.Path) -> str | None:
    """A .oramap file hashes its bytes; a template dir hashes every file in it."""
    if map_source.is_file():
        return hashlib.sha256(map_source.read_bytes()).hexdigest()
    if map_source.is_dir():
        return _hash_files(map_source, [p for p in map_source.rglob("*") if p.is_file()])
    return None


def compute_fingerprint(
    map_source: pathlib.Path,
    engine: pathlib.Path,
    config: dict,
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict:
    """The batch's arms as one dict. Null-tolerant: a component that cannot be
    read (no git, no engine, no map) records None rather than failing."""
    commit = (_git(repo_root, "rev-parse", "HEAD") or "").strip() or None
    status = _git(repo_root, "status", "--porcelain", "--", *FINGERPRINT_GIT_PATHS)
    version_file = engine / "VERSION"
    engine_version = None
    if version_file.is_file():
        # The engine writes VERSION as UTF-16 (BOM'd) on Windows; a utf-8
        # read yields NUL-separated mojibake. Decode by BOM, fall back plain.
        raw = version_file.read_bytes()
        if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
            engine_version = raw.decode("utf-16", errors="replace").strip() or None
        else:
            engine_version = raw.decode("utf-8", errors="replace").strip() or None
    ai_sha, ai_count = _ai_yaml_sha256(repo_root / "mods")
    mod_sha, mod_count = _mod_yaml_sha256(repo_root / "mods")
    return {
        "mod_commit": commit,
        "mod_dirty": None if status is None else bool(status.strip()),
        "engine_version": engine_version,
        "mod_dlls_sha256": _mod_dlls_sha256(engine),
        "ai_yaml_sha256": ai_sha,
        "ai_yaml_files": ai_count,
        "mod_yaml_sha256": mod_sha,
        "mod_yaml_files": mod_count,
        "map_sha256": _map_sha256(map_source),
        "config": config,
    }


def fingerprint_id(components: dict) -> str:
    """Compact handle for a fingerprint: first 12 hex of the sha256 over the
    canonical json of its components."""
    canonical = json.dumps(components, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]


def fingerprint_drift(baseline: dict, current: dict) -> dict:
    """{component: {"was", "now"}} for every component that moved — an empty
    dict means identical arms."""
    return {
        key: {"was": baseline.get(key), "now": current.get(key)}
        for key in sorted(set(baseline) | set(current))
        if baseline.get(key) != current.get(key)
    }


def _short_hash(value: str | None) -> str:
    return value[:12] if value else "null"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--factions", default="td_gdi,td_nod", help="comma-separated faction internal names")
    parser.add_argument("--bot-a", default="hard", help="bot type for side A (default: hard — the Frankenstein candidate); "
                            "with --team-size N a comma-separated list (hard,classic,...) — one name fills all slots")
    parser.add_argument("--bot-b", default="classic", help="bot type for side B (default: classic — the omniscient pre-wave reference bot); "
                            "with --team-size N a comma-separated list — one name fills all slots")
    parser.add_argument("--team-size", type=int, choices=range(1, 9), default=1,
                        help="members per side: 1 = duel (default), 2 = 2v2 — each team's seats are "
                             "consecutive Multi pairs on a 4-player map (default _ra_doubles.oramap)")
    parser.add_argument("--repeats", type=int, default=4, help="matches per matchup; sides alternate (default: 4)")
    parser.add_argument("--map", dest="map_path", type=pathlib.Path, default=DEFAULT_MAP,
                        help="duel map: the shipped .oramap (default: A Nuclear Winter) "
                             "or the legacy ai_duel_gate template dir")
    parser.add_argument("--swap-bots", action="store_true",
                        help="alternate which bot occupies which spawn per repeat — "
                             "the A/B acceptance requires both spawns covered")
    parser.add_argument("--time-limit", type=int, default=3, choices=sorted(VALID_TIME_LIMITS))
    parser.add_argument("--support-dir", type=pathlib.Path, default=None)
    parser.add_argument("--template", type=pathlib.Path, default=TEMPLATE_MAP,
                        help="template map dir (default: the A Nuclear Winter duel fixture)")
    parser.add_argument("--retries", type=int, default=1,
                        help="extra attempts per match that dies without an exception log "
                             "(external kill signature); crashes with an exception are not retried")
    # Real maps sustain ~25tps vs the flat fixture's ~100 — module-timing
    # writes land 60-120s apart and the old 120s default false-killed a live
    # match. 400s still catches a true hang inside any sane time-limit.
    parser.add_argument("--stall-timeout", type=int, default=400,
                        help="seconds of debug.log silence before a live match counts as hung")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-fingerprint-drift", action="store_true",
                        help="log arm drift between attempts and keep running "
                             "(default: abort the batch — a changed arm voids the A/B)")
    parser.add_argument("--keep-variants", action="store_true", help="do not delete variant map dirs on success")
    parser.add_argument("--render", choices=("fast", "default"), default="fast",
                        help="fast (default): VSync off + a 640x480 window. The engine renders once after EVERY logic tick, "
                             "so with VSync on a match is held to the monitor refresh (~50 ticks/s measured 2026-10-01). "
                             "Rendering never touches the simulation (bot logic is tick-based), so results are unchanged; "
                             "'default' keeps the player's settings")
    args = parser.parse_args()

    factions = [f.strip() for f in args.factions.split(",") if f.strip()]
    if len(factions) < 1:
        fail("--factions needs at least one faction id")
    if args.repeats < 1:
        fail("--repeats must be >= 1")

    def parse_team(raw: str, flag: str) -> list[str]:
        bots = [b.strip() for b in raw.split(",") if b.strip()]
        if len(bots) == 1:
            bots = bots * args.team_size
        if len(bots) != args.team_size:
            fail(f"{flag} needs exactly {args.team_size} comma-separated bot type(s) "
                 f"for --team-size {args.team_size} (got {raw!r})")
        return bots

    bots_a = parse_team(args.bot_a, "--bot-a")
    bots_b = parse_team(args.bot_b, "--bot-b")

    map_arg = args.map_path
    if args.team_size == 2 and map_arg == DEFAULT_MAP:
        map_arg = DEFAULT_TEAM_MAP
    map_source = map_arg.resolve()
    if not map_source.exists():
        fail(f"map source missing: {map_source}")
    if map_source.is_dir() and map_source != TEMPLATE_MAP:
        fail(f"only the bundled template dir is supported for directory maps: {TEMPLATE_MAP}")

    mod_id, engine = load_config()
    executable = engine / "bin" / "OpenRA.exe"
    if not executable.is_file():
        fail(f"OpenRA executable is missing: {executable}; run make.cmd all first")

    support = args.support_dir or pathlib.Path(tempfile.gettempdir()) / f"ai-match-batch-{int(time.time())}"
    support = support.resolve()
    variants_root = support / USER_MAP_DIR
    logs_dir = support / "Logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / MATCH_LOG

    matchups = build_matchups(factions, bots_a, bots_b, args.repeats,
                              swap_bots=args.swap_bots, team_size=args.team_size)

    # LC7: fingerprint the arms once, before any variant is written; every
    # match attempt below recomputes it and aborts on drift. team_size and the
    # parsed bot lists are part of the arms — a team-size change IS an arm change.
    batch_config = {
        "bot_a": args.bot_a,
        "bot_b": args.bot_b,
        "team_size": args.team_size,
        "bots_a": bots_a,
        "bots_b": bots_b,
        "factions": factions,
        "repeats": args.repeats,
        "swap_bots": args.swap_bots,
        "time_limit": args.time_limit,
    }
    batch_fingerprint = compute_fingerprint(map_source, engine, batch_config)
    batch_fp_id = fingerprint_id(batch_fingerprint)

    # One variant dir per distinct matchup (repeats reuse it).
    variants = {}
    for m in matchups:
        if args.team_size >= 2:
            variants.setdefault(
                m["variant"],
                {"team_size": m["team_size"], "team_a": m["team_a"], "team_b": m["team_b"],
                 "slots_a": m["slots_a"], "slots_b": m["slots_b"]},
            )
        else:
            variants.setdefault(
                m["variant"],
                {"a": m["side_a"], "b": m["side_b"]},
            )

    print(f"batch: {len(matchups)} match(es) across {len(variants)} variant(s), support={support}")
    print(
        f"fingerprint {batch_fp_id}: "
        f"commit={batch_fingerprint['mod_commit'] or 'null'} "
        f"dirty={batch_fingerprint['mod_dirty']} "
        f"engine={batch_fingerprint['engine_version'] or 'null'} "
        f"dlls={_short_hash(batch_fingerprint['mod_dlls_sha256'])} "
        f"ai_yaml={_short_hash(batch_fingerprint['ai_yaml_sha256'])} ({batch_fingerprint['ai_yaml_files']} files) "
        f"yaml={_short_hash(batch_fingerprint['mod_yaml_sha256'])} ({batch_fingerprint['mod_yaml_files']} files) "
        f"map={_short_hash(batch_fingerprint['map_sha256'])}"
    )
    for name, v in variants.items():
        if args.team_size >= 2:
            print(
                f"  variant {name}: "
                f"{v['team_a'][0]['faction']}({'+'.join(m['bot'] for m in v['team_a'])})@{'/'.join(map(str, v['slots_a']))} vs "
                f"{v['team_b'][0]['faction']}({'+'.join(m['bot'] for m in v['team_b'])})@{'/'.join(map(str, v['slots_b']))}"
            )
        else:
            print(f"  variant {name}: {v['a']['faction']}({v['a']['bot']}) vs {v['b']['faction']}({v['b']['bot']})")

    if args.dry_run:
        for m in matchups:
            print(f"  match {m['index']}.{m['repeat']}: {m['variant']}")
        return 0

    for name, v in variants.items():
        if args.team_size >= 2:
            write_variant(map_source, variants_root / name, v, args.time_limit)
        else:
            write_variant(map_source, variants_root / name, {"side_a": v["a"], "side_b": v["b"]}, args.time_limit)

    exceptions_before = {p.name for p in logs_dir.glob("exception-*.log")} if logs_dir.is_dir() else set()

    # The fixture locks gamespeed to maximum (1 ms timestep) and scales its minute
    # options so the engine cap equals the insane-era depth (3 min = 180,000 ticks):
    # the engine ends a stalemate and records it. The wall bound allows that
    # depth at a pessimistic sustained 20 tps; the stall detector in run_match ends
    # genuinely hung matches in ~2 minutes regardless.
    cap_ticks = args.time_limit * TICKS_PER_MINUTE
    timeout = cap_ticks // 20 + 300

    results = []
    progress_path = support / "batch_results.jsonl"
    drift_aborted = None
    for run, m in enumerate(matchups, 1):
        before = log_path.stat().st_size if log_path.is_file() else 0
        launch_args = [
            f"Game.Mod={mod_id}",
            "Sound.Device=none",
            "Engine.EngineDir=..",
            f"Engine.ModSearchPaths={REPO_ROOT / 'mods'},{engine / 'mods'}",
            f"Engine.SupportDir={support}",
            f"Launch.Map={m['variant']}",
            f"Launch.Benchmark={BENCHMARK_PREFIX}",
        ]
        # Opt-in verbose squad/formation telemetry (CAMEO_BOT_DEBUG=1); default
        # off so support-dir logs stay identical to the reference batches.
        if os.environ.get("CAMEO_BOT_DEBUG"):
            launch_args.append("Debug.BotDebug=true")
        if getattr(args, "render", "fast") == "fast":
            launch_args += ["Graphics.VSync=False", "Graphics.Mode=Windowed", "Graphics.WindowedSize=640,480"]

        attempt = 0
        drift = None
        current_fingerprint = batch_fingerprint
        while True:
            attempt += 1
            # LC7: re-fingerprint before EVERY attempt — a rebuild or sync
            # landing mid-retry is still drift. Any changed component aborts
            # the batch rather than launching under different arms.
            current_fingerprint = compute_fingerprint(map_source, engine, batch_config)
            drift = fingerprint_drift(batch_fingerprint, current_fingerprint)
            if drift:
                if not args.allow_fingerprint_drift:
                    break
                print(f"    fingerprint drift ({', '.join(drift)}) — continuing per --allow-fingerprint-drift",
                      flush=True)
            exc_before = {p.name for p in logs_dir.glob("exception-*.log")}
            print(f"[{run}/{len(matchups)}] {m['variant']} (repeat {m['repeat']}, attempt {attempt}) ...", flush=True)
            started = time.time()
            exit_code, output, status = run_match(
                executable, engine, launch_args, timeout,
                stall_log=logs_dir / "debug.log",
                stall_timeout=args.stall_timeout,
            )
            elapsed = int(time.time() - started)
            records = read_appended_records(log_path, before)
            new_exc = sorted(p.name for p in logs_dir.glob("exception-*.log") if p.name not in exc_before)

            # A nonzero exit with no exception log and no appended records is
            # the external-kill signature (TerminateProcess → exit 1; the
            # engine itself only ever returns 0 or -1-with-exception). Retry
            # those; a real crash writes exception-*.log and would just fail
            # the same way again. A clean `ok` exit with no records is the
            # phantom class: the process ended without a resolved world
            # (lobby abort under contention, early clean exit) and is not a
            # datapoint either — retry it the same bounded number of times.
            # A match that truly ran records both bots at GameOver; zero
            # appended records means nothing was played to judge.
            no_data = not records and not new_exc
            if not ((status.startswith("exit=") or status == "ok") and no_data and attempt <= args.retries):
                break
            print(f"    -> {status} in {elapsed}s, no records/exception — external kill or phantom abort? retry {attempt}/{args.retries}",
                  flush=True)
            print(f"    OpenRA output tail:\n{output_tail(output)}", flush=True)
            # The abort signature lives in the client's own log, not stdout:
            # a host-level event drops the loopback socket mid-match, e.g.
            # "An established connection was aborted by the software in your
            # host machine".
            client_log = logs_dir / "client.log"
            if client_log.is_file():
                tail = client_log.read_text(encoding="utf-8", errors="replace")[-2000:].strip()
                if tail:
                    print(f"    client.log tail:\n{tail}", flush=True)

        # Arms moved between batch start and this attempt: record the drift as
        # the match result, then stop the batch — no result gathered under
        # changed arms is a valid A/B datapoint.
        if drift and not args.allow_fingerprint_drift:
            print(f"[{run}/{len(matchups)}] {m['variant']} — FINGERPRINT DRIFT, batch aborted: "
                  f"{', '.join(drift)}", flush=True)
            for key, change in drift.items():
                print(f"    {key}: {json.dumps(change['was'], sort_keys=True)} -> "
                      f"{json.dumps(change['now'], sort_keys=True)}", flush=True)
            result = {
                "variant": m["variant"],
                "status": "fingerprint_drift",
                "fingerprint": fingerprint_id(current_fingerprint),
                "fingerprint_drift": drift,
                "attempts": attempt - 1,
                "records": 0,
            }
            results.append(result)
            with progress_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(result) + "\n")
            drift_aborted = drift
            break

        # A no-data run that exhausted its retries is still not a datapoint:
        # count it separately so a deterministic abort is visible in
        # batch_summary.json / run_league instead of reading as clean.
        if status == "ok" and not records:
            status = "norecord"

        outcome = sorted(
            (r.get("player", {}).get("faction"), r.get("player", {}).get("outcome"))
            for r in records
        )
        result = {
            "variant": m["variant"],
            "status": status,
            "fingerprint": fingerprint_id(current_fingerprint),
            "exit_code": exit_code,
            "attempts": attempt,
            "wall_seconds": elapsed,
            "records": len(records),
            "outcomes": outcome,
            "bot_outcomes": [
                {
                    "record_id": r.get("record_id"),
                    "bot_type": (r.get("player") or {}).get("bot_type"),
                    "outcome": (r.get("player") or {}).get("outcome"),
                    # player.spawn is the lobby SpawnPoint — 0 for map-side
                    # duelists. The physical spawn is the slot binding:
                    # Multi0/BotA -> index 0, Multi1/BotB -> index 1.
                    "spawn": SPAWN_INDEX_BY_SLOT.get((r.get("player") or {}).get("name"),
                                                   (r.get("player") or {}).get("spawn")),
                    "opponent": {"bot_type": ((r.get("opponents") or [{}])[0] or {}).get("bot_type")},
                    # Full relationship lists (2v2: one ally, two opponents).
                    "allies": [
                        {"name": a.get("name"), "bot_type": a.get("bot_type"), "outcome": a.get("outcome")}
                        for a in (r.get("allies") or [])
                    ],
                    "opponents": [
                        {"name": o.get("name"), "bot_type": o.get("bot_type"), "outcome": o.get("outcome")}
                        for o in (r.get("opponents") or [])
                    ],
                }
                for r in records
            ],
        }
        if new_exc:
            result["new_exceptions"] = new_exc
        results.append(result)
        # Durable per-match progress: a batch killed mid-run (the batch
        # process itself is as sweepable as the matches) still leaves this
        # evidence for postmortem and resume-by-rerun.
        with progress_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")
        print(f"    -> {status} in {elapsed}s, {len(records)} record(s): {outcome}", flush=True)
        if status != "ok":
            print(f"    OpenRA output tail:\n{output_tail(output)}")

    new_exceptions = sorted(p.name for p in logs_dir.glob("exception-*.log") if p.name not in exceptions_before)
    scoreboard = ab_scoreboard(results)
    team_board = team_scoreboard(results) if args.team_size > 1 else None
    summary = {
        "support_dir": str(support),
        "fingerprint": batch_fingerprint,
        "fingerprint_id": batch_fp_id,
        "matches": len(matchups),
        "completed": sum(1 for r in results if r["status"] == "ok"),
        "timed_out": sum(1 for r in results if r["status"] == "timeout"),
        "stalled": sum(1 for r in results if r["status"] == "stalled"),
        "died": sum(1 for r in results if r["status"].startswith("exit=")),
        "norecord": sum(1 for r in results if r["status"] == "norecord"),
        "retried": sum(1 for r in results if r["attempts"] > 1),
        "new_exceptions": new_exceptions,
        "scoreboard": scoreboard,
        "results": results,
    }
    if team_board is not None:
        summary["team_scoreboard"] = team_board
    if drift_aborted is not None:
        summary["aborted"] = "fingerprint_drift"
        summary["fingerprint_drift"] = drift_aborted
    (support / "batch_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(
        f"\nbatch done: {summary['completed']}/{summary['matches']} clean, "
        f"{summary['timed_out']} timeout, {summary['stalled']} stalled, "
        f"{summary['died']} died, {summary['norecord']} norecord ({summary['retried']} retried), "
        f"exceptions={new_exceptions or 'none'}"
    )
    if drift_aborted is not None:
        print(f"batch ABORTED on fingerprint drift ({', '.join(drift_aborted)}) — "
              f"the arms changed mid-batch; see batch_summary.json 'fingerprint_drift'")
    # For 2v2 the per-record 1v1 board would pair each bot against only its
    # first listed opponent — a degenerate reading; only the team board is
    # printed (ab_scoreboard still lands in batch_summary.json as "scoreboard").
    if scoreboard and args.team_size == 1:
        print("\nA/B scoreboard (decided 1v1s, deduplicated by game):")
        for pairing, cell in scoreboard.items():
            spawn_note = ", ".join(f"spawn {s}: {w}-{l}" for s, (w, l) in sorted(cell["spawn"].items()))
            print(f"  {pairing}: {cell['won']}-{cell['lost']}" + (f"  ({spawn_note})" if spawn_note else ""))
    if team_board:
        print("\nTeam scoreboard (decided matches, deduplicated by game):")
        for pairing, cell in team_board.items():
            spawn_note = ", ".join(f"seats {s}: {w}-{l}" for s, (w, l) in sorted(cell["spawn"].items()))
            print(f"  {pairing}: {cell['won']}-{cell['lost']}" + (f"  ({spawn_note})" if spawn_note else ""))
    print(f"records appended to {log_path}; aggregate with tools/ai/aggregate_ai_matches.py")
    print(f"win-rate + Wilson interval per bot type: tools/ai/ab_summary.py {support}")

    if not args.keep_variants:
        for name in variants:
            shutil.rmtree(variants_root / name, ignore_errors=True)

    if drift_aborted is not None:
        return 1
    if new_exceptions:
        return 1
    if not any(r["records"] for r in results):
        return 2
    return 0 if all(r["status"] == "ok" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
