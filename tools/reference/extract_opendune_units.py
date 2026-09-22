#!/usr/bin/env python3
"""Extract raw Dune II unit stats from an OpenDUNE checkout into machine-readable JSON.

    python tools/reference/extract_opendune_units.py --source <checkout> --out <external.json>
    python tools/reference/extract_opendune_units.py --source <checkout> --out -        # stdout
    python tools/reference/extract_opendune_units.py --source <checkout> --dry-run

`--source` and `--out` are REQUIRED; there are no personal-path defaults. The
output must be stdout or a path OUTSIDE this repository and outside the
source tree; creation is EXCLUSIVE (an existing file is never overwritten —
identical content is a no-op, differing content is a refusal).

SCOPE AND HONESTY CONTRACT
--------------------------
* The source is the **OpenDUNE** reconstruction (GPL-2.0) of **Dune II 1.07**.
  It is NOT the OpenRA `d2` mod and NOT a retail-executable extraction; the
  numbers below are the reconstruction's declared tables.
* Native values only: hitpoints, buildCredits, movingSpeedFactor, fireDelay,
  fireDistance and damage are copied verbatim. There is **no**
  seconds/DPS/armor conversion, no Cameo routing, no pricing anywhere in this
  tool — `fireDelay` is native engine ticks, `fireDistance` native units, and
  Dune II 1.07 exposes no per-unit armor axis in this source at all (recorded
  as an unavailable axis, never invented).
* Downloaded source is parsed, NEVER executed: header expressions go through
  a bounded AST whitelist (integer literals, earlier enum names, a few
  arithmetic/bit operators, hard bounds) — calls, attributes, subscripts,
  powers and pathological shifts are refused and reported as issues.
* Buildability is deliberately NOT proven by `buildCredits > 0`. The static
  table's `availableHouse` is only the reconstruction's DEFAULT mask; the real
  per-scenario availability axis (`BuildUnits` in scenario files) is not in
  this source and is listed under `provenance.unavailable_axes`. No record is
  emitted as "buildable" — each carries the raw evidence and a classification.
* NO record is certified balance-eligible. Every record is a **reference
  collection candidate only** (`collection_candidate: true`,
  `balance_eligible: null`): the static table cannot prove scenario
  availability. The task-mandated exclusions stay explicit: harvester/MCV are
  `manual_review_only` (never balance-eligible), and the superweapon missile,
  projectiles, specials, sandworm and frigate are collection-only
  (`balance_eligible: false`, `collection_only: true`).
* Projectiles (`isBullet`) and the house-missile special are extracted as a
  SEPARATE class from normal units and are never counted as a buildable unit
  roster.
* Output is deterministic: no timestamps, sorted keys, stable ordering, so a
  re-run produces byte-identical JSON and its sha256 is reproducible.
* Commit verification is not just HEAD: each parsed file is compared against
  its `git show HEAD:` blob, the checkout's dirty state is recorded, and
  source hashes are taken BEFORE and AFTER the run to prove the raw sources
  were never modified.
* No copyrighted source text is copied into this repository — only this
  parser; the JSON corpus stays outside the repo. Tests use synthetic
  fixtures; real-source integration tests are opt-in via the
  `CAMEO_REFERENCE_RAW_SOURCES` environment variable, never a personal path.

Reads, per the task order: src/table/unitinfo.c (the 27-entry UnitInfo table),
src/unit.h (UnitType / ActionType / MovementType), src/house.h (HouseType /
HouseFlag), src/table/houseinfo.c (house roster + specialCountDown for the
superweapon axis, recorded collection-only) and src/structure.h for
FLAG_STRUCTURE_* dependency names. EXPLOSION_* and STR_* identifiers are kept
as raw source names on purpose — strings.h / explosion enum text is out of
scope and guessing their meaning would be fabrication.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
# Declared task provenance — VERIFIED against the checkout at run time and
# reported either way; never trusted silently.
DECLARED_COMMIT = "9781a1c2fd14dfa09611d3502456d7918d862e96"

UNIT_TABLE_REL = "src/table/unitinfo.c"
UNIT_TABLE_SYMBOL = "g_table_unitInfo"
UNIT_HEADER_REL = "src/unit.h"
HOUSE_HEADER_REL = "src/house.h"
HOUSE_TABLE_REL = "src/table/houseinfo.c"
HOUSE_TABLE_SYMBOL = "g_table_houseInfo"
STRUCTURE_HEADER_REL = "src/structure.h"

SCHEMA_VERSION = 1

# ── A tiny comment-annotated C-initializer scanner ───────────────────────────
# unitinfo.c / houseinfo.c are one `/* field */ value,` pair per line, with
# nested braces (objectInfo, its flags, the unit flags) and inline lists
# (actionsPlayer). A char-level scan stays robust without any C grammar.

_COMMENT_RE = re.compile(r"/\*(.*?)\*/", re.S)


def _strip_value(raw: str):
    """`"Carryall"` -> Carryall · `'H'` -> H · `value,` -> value."""
    raw = raw.strip()
    if raw.endswith(","):
        raw = raw[:-1].strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    return raw


def parse_initializer(text: str, issues: list):
    """Parse `/* name */ value` pairs inside nested braces.

    Returns the top-level entries as raw scanner nodes. Every node is a dict
    with optional `_label` (its `/* ... */` marker), `_children` (nested
    braces) and `_tokens` (bare tokens of an inline brace list). Unknown
    shapes (unbalanced brace, unterminated comment, token without a field
    comment) are recorded as issues, never fatal.
    """
    root: dict = {}
    stack: list = [root]
    pending_field = None      # comment awaiting its value token
    expect_label = None       # freshly pushed brace awaiting its `/* N */`

    def top():
        return stack[-1]

    def push_child():
        child = {"_label": None, "_children": [], "_tokens": []}
        top().setdefault("_children", []).append(child)
        stack.append(child)
        return child

    pos, n = 0, len(text)
    while pos < n:
        ch = text[pos]
        if ch == "/":
            m = _COMMENT_RE.match(text, pos)
            if not m:
                issues.append({"severity": "malformed_source",
                               "detail": "unterminated comment", "offset": pos})
                break
            comment = m.group(1).strip()
            pos = m.end()
            if expect_label is not None and expect_label["_label"] is None:
                expect_label["_label"] = comment
                expect_label = None
            else:
                pending_field = comment
            continue
        if ch == "{":
            child = push_child()
            if pending_field is not None:
                # A named inline brace list (`/* actionsPlayer */ { ... }`):
                # its name travels with the brace, and the tokens inside are
                # its value; no `/* label */` follows.
                child["_label"] = pending_field
                pending_field = None
            else:
                # An anonymous or labelled nested struct (`{ /* 0 */`,
                # `{ /* objectInfo */`): the next comment names it.
                expect_label = child
            pos += 1
            continue
        if ch == "}":
            if len(stack) <= 1:
                issues.append({"severity": "malformed_source",
                               "detail": "unbalanced closing brace", "offset": pos})
            else:
                stack.pop()
            expect_label = None
            pos += 1
            continue
        if ch in " \t\r\n,":
            pos += 1
            continue
        # A bare token: string literal, char literal, or identifier/number.
        if text[pos] in "\"'":
            quote = text[pos]
            end = text.find(quote, pos + 1)
            if end == -1:
                issues.append({"severity": "malformed_source",
                               "detail": "unterminated string literal", "offset": pos})
                break
            token = text[pos:end + 1]
            pos = end + 1
        else:
            end = pos
            while end < n and text[end] not in "{},\n":
                end += 1
            token = text[pos:end].rstrip()
            pos = end if end > pos else pos + 1
        token = _strip_value(token)
        node = top()
        if pending_field is not None:
            if pending_field in node:
                issues.append({"severity": "duplicate_field",
                               "detail": f"{pending_field!r} repeated; first value kept",
                               "field": pending_field})
            else:
                node[pending_field] = token
            pending_field = None
        else:
            node["_tokens"].append(token)
        expect_label = None

    if len(stack) > 1:
        issues.append({"severity": "malformed_source",
                       "detail": f"{len(stack) - 1} unclosed brace(s) at end of file"})
    return root.get("_children") or []


def simplify(node, issues):
    """Scanner node -> plain dict / list of plain dicts (labelled children merged)."""
    if not isinstance(node, dict):
        return node
    tokens = node.get("_tokens") or []
    children = node.get("_children") or []
    base = {k: v for k, v in node.items() if not k.startswith("_")}
    for child in children:
        sub = simplify(child, issues)
        label = child.get("_label")
        if label is not None:
            if label in base:
                issues.append({"severity": "duplicate_field",
                               "detail": f"nested block {label!r} repeated; "
                                         "first block kept",
                               "field": label})
            else:
                base[label] = sub
        else:
            base.setdefault("_anonymous", []).append(sub)
    if tokens and not base:
        return [simplify(t, issues) for t in tokens]
    if tokens:
        # A labelled inline list also carrying stray tokens: keep both.
        base["_inline_tokens"] = [simplify(t, issues) for t in tokens]
    return base


def parse_c_table(path: pathlib.Path, symbol: str, issues: list):
    """[plain dict per top-level `{ /* N */ ... }` entry] of `symbol[...] = { ... };`."""
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(re.escape(symbol) + r"\s*\[[^\]]*\]\s*=\s*\{", text)
    if not m:
        issues.append({"severity": "malformed_source",
                       "detail": f"no initializer for {symbol!r}",
                       "file": path.name})
        return []
    body = text[m.end():]
    close = body.rfind("};")
    if close != -1:
        body = body[:close]
    entries = []
    for entry in parse_initializer(body, issues):
        flat = simplify(entry, issues)
        if not isinstance(flat, dict):
            issues.append({"severity": "malformed_source",
                           "detail": f"entry is not a field dict: {type(flat).__name__}"})
            continue
        # The entry's own `/* 0 */` marker is its table index.
        if "_label" in entry and entry["_label"] is not None:
            flat.setdefault("_label", entry["_label"])
        entries.append(flat)
    return entries


# ── C header enum / flag parsing ─────────────────────────────────────────────

_ENUM_RE = re.compile(r"typedef\s+enum\s+(\w+)\s*\{(.*?)\}\s*\w*\s*;", re.S)


class EnumExpressionError(ValueError):
    """A header expression is outside the bounded whitelist — never executed."""


# ── Bounded AST evaluator for C enum expressions ─────────────────────────────
# Downloaded source must NEVER be executed. `eval` would have run anything a
# crafted header contains; this whitelist walks the AST and accepts only
# integer literals, previously-parsed enum names, and a few arithmetic/bit
# operators — with hard bounds so hostile expressions (recursive shifts,
# powers, attribute chains) fail fast instead of exhausting resources.

_MAX_EXPR_LEN = 256
_MAX_EXPR_NODES = 64
_MAX_DEPTH = 16
_SHIFT_BOUND = 32          # C bitflags never shift beyond int width
_INT_LIMIT = 1 << 62       # Dune II values are tiny; anything bigger is abuse

_ALLOWED_BINOPS = {ast.BitOr, ast.BitAnd, ast.Add, ast.Sub, ast.LShift, ast.RShift}


def _bounded(value, what):
    """Every produced value must fit the extraction range — applied to
    constants, names, unary results and binary intermediates alike."""
    if not -_INT_LIMIT <= value <= _INT_LIMIT:
        raise EnumExpressionError(f"{what} {value} out of bounds "
                                  f"(|v| > {_INT_LIMIT})")
    return value


def _eval_enum_node(node, visible, depth):
    if depth > _MAX_DEPTH:
        raise EnumExpressionError("expression too deeply nested")
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, int):
            raise EnumExpressionError(f"non-integer constant {node.value!r}")
        return _bounded(node.value, "constant")
    if isinstance(node, ast.Name):
        if node.id not in visible:
            raise EnumExpressionError(f"unknown name {node.id!r}")
        return _bounded(visible[node.id], f"name {node.id}")
    if isinstance(node, ast.BinOp):
        if type(node.op) not in _ALLOWED_BINOPS:
            raise EnumExpressionError(f"operator {type(node.op).__name__} not allowed")
        left = _eval_enum_node(node.left, visible, depth + 1)
        right = _eval_enum_node(node.right, visible, depth + 1)
        if isinstance(node.op, (ast.LShift, ast.RShift)) and not 0 <= right <= _SHIFT_BOUND:
            raise EnumExpressionError(f"shift amount {right} out of bounds")
        if type(node.op) is ast.BitOr:
            value = left | right
        elif type(node.op) is ast.BitAnd:
            value = left & right
        elif type(node.op) is ast.Add:
            value = left + right
        elif type(node.op) is ast.Sub:
            value = left - right
        elif type(node.op) is ast.LShift:
            value = left << right
        else:
            value = left >> right
        return _bounded(value, "binary result")
    if isinstance(node, ast.UnaryOp):
        if not isinstance(node.op, (ast.USub, ast.UAdd)):
            raise EnumExpressionError(f"unary {type(node.op).__name__} not allowed")
        value = _eval_enum_node(node.operand, visible, depth + 1)
        return _bounded(-value if isinstance(node.op, ast.USub) else value,
                        "unary result")
    # Calls, attributes, subscripts, comprehensions, lambdas, ... all land here.
    raise EnumExpressionError(f"{type(node).__name__} not allowed")


def eval_enum_expr(expr, visible, enum_name, member):
    """Evaluate one `= expr` header value under the whitelist; raises on abuse."""
    if len(expr) > _MAX_EXPR_LEN:
        raise EnumExpressionError(f"expression too long ({len(expr)} > {_MAX_EXPR_LEN})")
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise EnumExpressionError(f"syntax error: {exc.msg}") from exc
    nodes = list(ast.walk(tree))
    if len(nodes) > _MAX_EXPR_NODES:
        raise EnumExpressionError(f"expression too complex ({len(nodes)} nodes)")
    return _eval_enum_node(tree.body, visible, 0)


def parse_enums(path: pathlib.Path, issues: list):
    """{enum_name: {member: value}} for every typedef enum in a header.

    Values may be explicit (= 12), shifted (1 << NAME) or sequential; earlier
    members are visible to later expressions, which is how OpenDUNE's flag
    enums are built.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        issues.append({"severity": "source_missing", "detail": f"{path}: {exc}"})
        return {}
    enums = {}
    visible: dict = {}   # every member seen so far in this header; later
                         # enums shift against earlier ones (HouseFlag uses
                         # HouseType's members)
    for m in _ENUM_RE.finditer(text):
        name, body = m.group(1), m.group(2)
        members: dict = {}
        next_value = 0
        # Implicit-successor chain state. C gives an implicit member the value
        # of the previous member + 1: a chain is valid only while the PREVIOUS
        # member actually holds a value. A failed explicit value invalidates
        # the chain; a valid explicit value resets it. A withheld member keeps
        # the chain invalid (its successor's value is not derivable).
        chain_valid = True
        # Members may sit on one line or many; the separator is the comma
        # (values themselves are integer expressions, so a comma inside a
        # value does not occur). Block comments are blanked first.
        body_clean = re.sub(r"/\*.*?\*/", " ", body, flags=re.S)
        fragments = []
        for chunk in body_clean.splitlines():
            chunk = chunk.split("//")[0]
            fragments.extend(chunk.split(","))
        for frag in fragments:
            line = frag.strip().rstrip("; \t").strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, expr = line.split("=", 1)
                key, expr = key.strip(), expr.strip()
                try:
                    value = eval_enum_expr(expr, visible, name, key)
                except EnumExpressionError as exc:
                    issues.append({"severity": "unresolved_enum_value",
                                   "detail": f"{name}.{key} = {expr!r}: {exc}"})
                    # No value assigned; do NOT let an implicit successor
                    # continue from an unknown predecessor.
                    chain_valid = False
                    continue
                chain_valid = True
            else:
                key = line
                if not chain_valid:
                    issues.append({"severity": "implicit_successor_withheld",
                                   "detail": f"{name}.{key}: implicit value "
                                             "withheld — predecessor has no "
                                             "resolved value"})
                    chain_valid = False
                    continue
                value = next_value
            members[key] = value
            visible[key] = value
            next_value = value + 1
        enums[name] = members
    return enums


# ── Field helpers ────────────────────────────────────────────────────────────

def _int(value):
    try:
        return int(str(value), 0)
    except (TypeError, ValueError):
        return None


def _bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    low = str(value).strip().lower()
    if low == "true":
        return True
    if low == "false":
        return False
    return None


def expand_house_mask(tokens, house_flags, house_names, issues, context):
    """[FLAG_HOUSE_X per concrete house] whose bit is set in the OR of `tokens`.

    `availableHouse` may carry a composite name (FLAG_HOUSE_ALL); the record
    keeps the raw tokens AND this resolved per-house list, ordered by the
    HouseType enum — so the corpus never forces the reader to expand bitmasks
    by hand, and a composite that resolves to nothing is flagged.
    """
    concrete = [(name, value) for name, value in
                (("FLAG_" + h, house_flags.get("FLAG_" + h))  # HOUSE_X -> FLAG_HOUSE_X
                 for h in sorted(house_names, key=lambda n: house_names[n]))
                if isinstance(value, int)]
    mask = 0
    for token in tokens:
        value = house_flags.get(token)
        if isinstance(value, int):
            mask |= value
    resolved = [name for name, value in concrete if mask & value] if mask else []
    if tokens and not resolved:
        issues.append({"severity": "unresolved_flag",
                       "detail": f"{context}: mask {tokens!r} resolves to no "
                                 "concrete house"})
    return resolved


def split_flags(raw, table, issues, context):
    """`A | B | C` -> [resolved names]; unresolved tokens become issues."""
    if raw is None:
        return []
    names = []
    for token in re.split(r"[|+\s]+", str(raw)):
        token = token.strip()
        if not token:
            continue
        if token in table:
            names.append(token)
        else:
            issues.append({"severity": "unresolved_flag",
                           "detail": f"{context}: {token!r} not in flag table"})
    return names


# ── Classification (documented, conservative — nothing guessed) ──────────────

CLASSIFICATION_RULE = (
    "superweapon_missile if unit_type==UNIT_MISSILE_HOUSE; wildlife if "
    "name=='Sandworm'; starport_transport if name=='Frigate'; economy_unit if "
    "unit_type in (UNIT_HARVESTER, UNIT_MCV); projectile if unit_flags.isBullet; "
    "special if unit_flags.isNormalUnit==false; else unit"
)


def classify(name, unit_type_name, unit_flags):
    if unit_type_name == "UNIT_MISSILE_HOUSE":
        return "superweapon_missile"
    if name == "Sandworm":
        return "wildlife"
    if name == "Frigate":
        return "starport_transport"
    if unit_type_name in ("UNIT_HARVESTER", "UNIT_MCV"):
        return "economy_unit"
    if _bool(unit_flags.get("isBullet")):
        return "projectile"
    if _bool(unit_flags.get("isNormalUnit")) is False:
        return "special"
    return "unit"


def eligibility(record_class):
    """(balance_eligible, manual_review_only, collection_only) — nothing certified.

    NO record is ever certified balance-eligible: this extractor sees only the
    static table, whose availability axis is the DEFAULT mask (scenario files
    unavailable). A plain unit is therefore a *reference collection
    candidate* — `balance_eligible` stays null (explicitly not certified) —
    and only the task-mandated exclusions get an explicit False:
    harvester/MCV are manual_review_only; superweapon missile, projectiles,
    specials, sandworm and frigate are collection-only.
    """
    if record_class in ("economy_unit", "superweapon_missile", "projectile",
                        "special", "wildlife", "starport_transport"):
        return False, record_class == "economy_unit", True
    return None, False, False


# ── Provenance ───────────────────────────────────────────────────────────────

def sha256_of(path: pathlib.Path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(args, source: pathlib.Path):
    try:
        proc = subprocess.run(["git", *args], cwd=str(source),
                              capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        return None, f"git {args[0]} failed: {exc}"
    if proc.returncode != 0:
        return None, (f"git {args[0]} exit {proc.returncode}: "
                      f"{(proc.stderr or '').strip()[:200]}")
    return proc.stdout, None


def build_provenance(source: pathlib.Path, files, git_info):
    return {
        "source_game": "Dune II (reconstructed via OpenDUNE)",
        "source_kind": ("OpenDUNE source checkout, GPL-2.0 — a reconstruction of "
                        "Dune II 1.07; NOT the OpenRA d2 mod and NOT a "
                        "retail-executable extraction"),
        "checkout_root": str(source),
        "git": git_info,
        "license": "GPL-2.0 (OpenDUNE)",
        "files": files,
        "version_notes": [
            "OpenDUNE reconstructs Dune II 1.07 behaviour from the original game "
            "data; values below are the reconstruction's declared tables, not a "
            "retail binary dump.",
            "`available` and `availableCampaign` are 0 in the static table for "
            "every unit; runtime availability comes from scenario files at load "
            "time.",
        ],
        "unavailable_axes": [
            "per-scenario unit availability (scenario BuildUnits/availableHouse "
            "overrides) — scenario files are not in this source; the recorded "
            "`available_house_default` is the static-table DEFAULT mask",
            "no per-unit armor type or Versus axis exists in Dune II 1.07 / "
            "OpenDUNE unitinfo — the absence is native, not a parser gap",
            "starport dynamic prices (`g_starportAvailable`) are runtime state, "
            "not table data",
            "projectile flight behaviour and damage application live in engine "
            "code (unit.c), out of extraction scope",
            "STR_* string texts (strings.h) not resolved; identifiers kept raw",
            "time/range units are native engine ticks/units; no seconds or cell "
            "conversion is derived anywhere by design",
        ],
        "classification_rule": CLASSIFICATION_RULE,
        "eligibility_policy": (
            "no record is certified balance-eligible; every record is a "
            "reference collection candidate only; harvester/MCV manual_review_only; "
            "superweapon/projectile/special/wildlife/transport collection-only"),
    }


# ── Extraction ───────────────────────────────────────────────────────────────

SOURCE_FILES = (UNIT_TABLE_REL, UNIT_HEADER_REL, HOUSE_HEADER_REL,
                HOUSE_TABLE_REL, STRUCTURE_HEADER_REL)


def _git_bytes(args, source: pathlib.Path):
    try:
        proc = subprocess.run(["git", *args], cwd=str(source),
                              capture_output=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        return None, f"git {args[0]} failed: {exc}"
    if proc.returncode != 0:
        return None, (f"git {args[0]} exit {proc.returncode}: "
                      f"{(proc.stderr or b'').decode('utf-8', 'replace').strip()[:200]}")
    return proc.stdout, None


def verify_sources(source: pathlib.Path, issues: list):
    """Per-file before/after hashes + git state, captured AROUND the parse.

    Commit verification is not just HEAD: each parsed file is compared byte-
    for-byte against `git show HEAD:<path>` (so a dirty checkout can never
    masquerade as the declared commit), the whole-checkout dirty state is
    recorded, and hashes are re-taken after parsing to prove the run left the
    raw sources untouched.
    """
    files = []
    for rel in SOURCE_FILES:
        path = source / rel
        try:
            files.append({"path": rel, "sha256_before": sha256_of(path),
                          "bytes": path.stat().st_size})
        except OSError as exc:
            issues.append({"severity": "source_missing",
                           "detail": f"{rel}: {exc}"})
            return None, None
    git_info = {"declared_commit": DECLARED_COMMIT}
    if not (source / ".git").exists():
        git_info.update({"available": False,
                         "note": "no .git in checkout; commit identity unverified"})
        issues.append({"severity": "provenance_unverified",
                       "detail": "no .git in checkout; commit identity unverified"})
        return files, git_info
    git_info["available"] = True
    head, err = _git(["rev-parse", "HEAD"], source)
    if err:
        issues.append({"severity": "provenance_unverified", "detail": err})
        git_info["head"] = None
    else:
        git_info["head"] = head.strip()
        git_info["head_matches_declared"] = git_info["head"] == DECLARED_COMMIT
        if not git_info["head_matches_declared"]:
            issues.append({"severity": "commit_mismatch",
                           "detail": f"HEAD {git_info['head']} != declared "
                                     f"{DECLARED_COMMIT}"})
    status, err = _git(["status", "--porcelain"], source)
    if err:
        issues.append({"severity": "provenance_unverified", "detail": err})
        git_info["checkout_dirty"] = None
    else:
        dirty = [line for line in status.splitlines() if line.strip()]
        git_info["checkout_dirty"] = bool(dirty)
        git_info["checkout_dirty_entries"] = len(dirty)
        touched = {line.split(None, 1)[-1].strip() for line in dirty}
        parsed_dirty = sorted(rel for rel in SOURCE_FILES if rel in touched)
        git_info["parsed_files_dirty"] = parsed_dirty
        if parsed_dirty:
            issues.append({"severity": "checkout_dirty",
                           "detail": "parsed files differ from HEAD: "
                                     + ", ".join(parsed_dirty)})
    for entry in files:
        disk = (source / entry["path"]).read_bytes()
        blob, err = _git_bytes(["show", f"HEAD:{entry['path']}"], source)
        if err or blob is None:
            entry["matches_head"] = None
            issues.append({"severity": "provenance_unverified",
                           "detail": f"{entry['path']}: {err}"})
            continue
        # byte-faithful first; then line-ending normalized, because the
        # checkout may hold CRLF while the blob stores LF (git itself calls
        # that clean). Only a content difference survives as an issue.
        if disk == blob:
            entry["matches_head"] = True
        elif disk.replace(b"\r\n", b"\n") == blob.replace(b"\r\n", b"\n"):
            entry["matches_head"] = True
            entry["matches_head_after_newline_normalization"] = True
        else:
            entry["matches_head"] = False
            issues.append({"severity": "file_differs_from_head",
                           "detail": f"{entry['path']} on disk != HEAD blob"})
    return files, git_info


def finalize_source_verification(source: pathlib.Path, files, issues: list):
    """Re-hash after parsing; prove the run did not modify the raw sources."""
    for entry in files:
        try:
            entry["sha256_after"] = sha256_of(source / entry["path"])
        except OSError as exc:
            issues.append({"severity": "source_changed_during_run",
                           "detail": f"{entry['path']}: {exc}"})
            entry["sha256_after"] = None
            entry["unchanged_during_run"] = False
            continue
        entry["unchanged_during_run"] = entry["sha256_after"] == entry["sha256_before"]
        if not entry["unchanged_during_run"]:
            issues.append({"severity": "source_changed_during_run",
                           "detail": f"{entry['path']} changed during extraction"})


def extract(source: pathlib.Path, issues: list):
    unitinfo = source / UNIT_TABLE_REL
    unit_h = source / UNIT_HEADER_REL
    house_h = source / HOUSE_HEADER_REL
    houseinfo = source / HOUSE_TABLE_REL
    structure_h = source / STRUCTURE_HEADER_REL

    for path in (unitinfo, unit_h, house_h, houseinfo, structure_h):
        if not path.is_file():
            issues.append({"severity": "source_missing",
                           "detail": f"required source file missing: {path}"})
            return None

    files, git_info = verify_sources(source, issues)
    if files is None:
        return None
    provenance = build_provenance(source, files, git_info)

    enums_unit = parse_enums(unit_h, issues)
    enums_house = parse_enums(house_h, issues)
    enums_structure = parse_enums(structure_h, issues)

    unit_entries = parse_c_table(unitinfo, UNIT_TABLE_SYMBOL, issues)
    house_entries = parse_c_table(houseinfo, HOUSE_TABLE_SYMBOL, issues)

    unit_types = enums_unit.get("UnitType", {})
    index_to_unit = {value: name for name, value in unit_types.items()
                     if isinstance(value, int) and 0 <= value < 1000}
    house_flags = enums_house.get("HouseFlag", {})
    house_names = enums_house.get("HouseType", {})
    action_types = enums_unit.get("ActionType", {})
    movement_types = enums_unit.get("MovementType", {})

    def name_of(table, raw):
        value = _int(raw)
        for name, member in table.items():
            if member == value:
                return name
        return raw

    records = []
    for entry in unit_entries:
        label = entry.get("_label")
        index = _int(label) if label is not None else None
        obj = entry.get("objectInfo") if isinstance(entry.get("objectInfo"), dict) else {}
        obj_flags = obj.get("flags") if isinstance(obj.get("flags"), dict) else {}
        unit_flags = entry.get("flags") if isinstance(entry.get("flags"), dict) else {}
        unit_type_name = index_to_unit.get(index, f"INDEX_{index}")

        rec_issues = []
        if index is None:
            issues.append({"severity": "missing_field",
                           "detail": "unit entry without an index label"})
        if "hitpoints" not in obj:
            rec_issues.append("hitpoints_missing")
        if "buildCredits" not in obj:
            rec_issues.append("buildCredits_missing")

        available = split_flags(obj.get("availableHouse"), house_flags, issues,
                                f"{unit_type_name}.availableHouse")
        available_resolved = expand_house_mask(
            available, house_flags, house_names, issues,
            f"{unit_type_name}.availableHouse")
        structures = split_flags(obj.get("structuresRequired"),
                                 set(enums_structure.get("StructureFlag", {})),
                                 issues, f"{unit_type_name}.structuresRequired")
        actions = [name_of(action_types, a) for a in (obj.get("actionsPlayer") or [])]

        rec_class = classify(obj.get("name"), unit_type_name, unit_flags)
        eligible, review_only, collection_only = eligibility(rec_class)

        records.append({
            "index": index,
            "unit_type": unit_type_name,
            "name": obj.get("name"),
            "string_abbrev": obj.get("stringID_abbrev"),
            "string_full": obj.get("stringID_full"),
            "wsa": obj.get("wsa"),
            "hp": _int(obj.get("hitpoints")),
            "cost": _int(obj.get("buildCredits")),
            "build_time": _int(obj.get("buildTime")),
            "speed": _int(entry.get("movingSpeedFactor")),
            "speed_semantics": "movingSpeedFactor, 256 = full speed (native, unconverted)",
            "fire_delay": _int(entry.get("fireDelay")),
            "fire_delay_semantics": "native engine ticks (unconverted)",
            "damage": _int(entry.get("damage")),
            "range": _int(entry.get("fireDistance")),
            "range_semantics": "native fireDistance (unconverted)",
            "movement_type": name_of(movement_types, entry.get("movementType")),
            "turn_speed": _int(entry.get("turningSpeed")),
            "fog_uncover_radius": _int(obj.get("fogUncoverRadius")),
            "sort_priority": _int(obj.get("sortPriority")),
            "upgrade_level_required": _int(obj.get("upgradeLevelRequired")),
            "structures_required": structures,
            "available_house_default": available,
            "available_house_resolved": available_resolved,
            "available_axis_note": "static-table default; scenario overrides not in source",
            "actions_player": actions,
            "action_ai": name_of(action_types, entry.get("actionAI")),
            "priority_build": _int(obj.get("priorityBuild")),
            "priority_target": _int(obj.get("priorityTarget")),
            "bullet_type": name_of(index_to_unit, entry.get("bulletType")),
            "explosion_type": entry.get("explosionType"),
            "bullet_sound": _int(entry.get("bulletSound")),
            "object_flags": {k: _bool(v) for k, v in sorted(obj_flags.items())},
            "unit_flags": {k: _bool(v) for k, v in sorted(unit_flags.items())},
            "index_start": _int(entry.get("indexStart")),
            "index_end": _int(entry.get("indexEnd")),
            "dimension": _int(entry.get("dimension")),
            "display_mode": name_of(enums_unit.get("DisplayMode", {}),
                                    entry.get("displayMode")),
            "ground_sprite_id": _int(entry.get("groundSpriteID")),
            "turret_sprite_id": _int(entry.get("turretSpriteID")),
            "destroyed_sprite_id": _int(entry.get("destroyedSpriteID")),
            "animation_speed": _int(entry.get("animationSpeed")),
            "extraction_class": rec_class,
            "collection_candidate": True,
            "balance_eligible": eligible,
            "eligibility_note": (
                "null = NOT certified: static-table record, scenario "
                "availability axis unavailable; reference collection candidate "
                "only" if eligible is None else
                "false by task rule: manual_review_only" if review_only else
                "false by task rule: collection-only class"),
            "manual_review_only": review_only,
            "collection_only": collection_only,
            "issues": rec_issues,
        })

    houses = []
    house_names = enums_house.get("HouseType", {})
    for entry in house_entries:
        label = entry.get("_label")
        houses.append({
            "index": _int(label),
            "house_type_enum": next((n for n, v in house_names.items()
                                     if v == _int(label)), None),
            "name": entry.get("name"),
            "toughness": _int(entry.get("toughness")),
            "degrading_chance": _int(entry.get("degradingChance")),
            "degrading_amount": _int(entry.get("degradingAmount")),
            "minimap_color": _int(entry.get("minimapColor")),
            "special_countdown": _int(entry.get("specialCountDown")),
            "special_countdown_semantics": "native ticks (unconverted)",
            "starport_delivery_time": _int(entry.get("starportDeliveryTime")),
            "prefix_char": entry.get("prefixChar"),
            "special_weapon": entry.get("specialWeapon"),
            "special_weapon_note": ("HouseWeapon enum: 1=MISSILE, 2=FREMEN, "
                                    "3=SABOTEUR; the superweapon axis is "
                                    "collection-only, never balance-eligible"),
            "voice_filename": entry.get("voiceFilename"),
        })

    finalize_source_verification(source, files, issues)

    return {
        "provenance": provenance,
        "records": records,
        "houses": houses,
        "enums": {
            "UnitType": unit_types,
            "ActionType": action_types,
            "MovementType": movement_types,
            "DisplayMode": enums_unit.get("DisplayMode", {}),
            "HouseType": house_names,
            "HouseFlag": dict(house_flags),
        },
        "counts": {
            "unit_records": len(records),
            "house_records": len(houses),
            "declared_unit_max": unit_types.get("UNIT_MAX"),
        },
    }


# ── Output plumbing ──────────────────────────────────────────────────────────

def canonical_json(payload):
    return json.dumps(payload, sort_keys=True, indent=1, ensure_ascii=True) + "\n"


STDOUT_OUT = "-"


def validate_out(out: pathlib.Path, source: pathlib.Path):
    """The JSON may go to stdout or to an EXTERNAL file — nothing else.

    Refuses (exit 2): paths inside THIS repository (the corpus must never be
    committed), paths inside the SOURCE tree (raw originals stay untouched),
    and the source file/dir itself.
    """
    if out == pathlib.Path(STDOUT_OUT):
        return
    out = out.expanduser().resolve()
    repo = REPO_ROOT.resolve()
    if out == repo or repo in out.parents:
        raise SystemExit(f"refusing output inside this repository: {out}")
    source_root = (source.parent if source.is_file() else source).resolve()
    if out == source_root or source_root in out.parents:
        raise SystemExit(f"refusing output inside the source tree: {out}")
    if out == (source if source.is_file() else source_root):
        raise SystemExit("refusing output equal to the source")
    parent = out.parent
    if parent.exists() and not parent.is_dir():
        raise SystemExit(f"output parent is not a directory: {parent}")


def write_exclusive(out: pathlib.Path, text: str):
    """Create-or-refuse. Never truncates, never overwrites, race-safe.

    `O_EXCL` guarantees a single creator even under concurrent runs; a loser
    that arrives after creation compares content: identical -> already current
    (exit 0), differing -> refusal (exit 3). No force path exists by design.
    """
    data = text.encode("utf-8")
    try:
        fd = os.open(str(out), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        existing = out.read_bytes() if out.is_file() else None
        if existing == data:
            print(f"already current (not rewritten): {out}")
            return 0
        print(f"REFUSING: {out} already exists with DIFFERENT content "
              f"(existing bytes={len(existing) if existing is not None else '?'}, "
              f"new bytes={len(data)}); delete it explicitly first", file=sys.stderr)
        return 3
    except OSError as exc:
        print(f"cannot create {out}: {exc}", file=sys.stderr)
        return 2
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)   # bytes: text mode would translate \n to \r\n on Windows
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", type=pathlib.Path, required=True,
                    help="OpenDUNE checkout root (read-only; no default)")
    ap.add_argument("--out", type=pathlib.Path, required=True,
                    help=f"external JSON path outside repo and source tree, "
                         f"or '{STDOUT_OUT}' for stdout")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    source = args.source.expanduser().resolve()
    if not source.exists():
        print(f"source does not exist: {source}", file=sys.stderr)
        return 2
    out = args.out.expanduser()
    if out != pathlib.Path(STDOUT_OUT):
        out = out.resolve()
    validate_out(out, source)

    issues: list = []
    data = extract(source, issues)
    if data is None:
        for issue in issues:
            print(f"ISSUE [{issue.get('severity')}] {issue.get('detail')}",
                  file=sys.stderr)
        return 2

    payload = {
        "schema_version": SCHEMA_VERSION,
        "tool": "tools/reference/extract_opendune_units.py",
        "provenance": data["provenance"],
        "counts": data["counts"],
        "records": data["records"],
        "houses": data["houses"],
        "enums": data["enums"],
        "issues": sorted(issues, key=lambda i: (i.get("severity", ""),
                                                i.get("detail", ""))),
    }
    text = canonical_json(payload)

    if args.dry_run:
        print(f"dry run: {data['counts']} · {len(issues)} issues · "
              f"would write {out if out != pathlib.Path(STDOUT_OUT) else 'stdout'}")
        return 0

    if out == pathlib.Path(STDOUT_OUT):
        sys.stdout.write(text)
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    code = write_exclusive(out, text)

    classes: dict = {}
    for record in data["records"]:
        classes[record["extraction_class"]] = classes.get(record["extraction_class"], 0) + 1
    if not args.quiet:
        git_info = data["provenance"]["git"]
        print(f"source : {source}")
        print(f"commit : {git_info.get('head') or 'UNVERIFIED'}"
              f"{'' if git_info.get('head_matches_declared', True) else ' (MISMATCH vs declared)'}"
              f" · dirty={git_info.get('checkout_dirty')}")
        print(f"records: {data['counts']} · classes {classes}")
        print(f"issues : {len(issues)}")
        print(f"wrote  : {out}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
