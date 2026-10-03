"""extract_ra3_units.py — bounded Red Alert 3 base-roster extractor (Aedis Japan reference request).

TASK (Astra-ordered, 2026-09-09): evidence collection ONLY. Read the official EA source
checkout (github.com/ElectronicArts/CnC_Modding_Support, `Red Alert 3/Xml`), follow the
ACTIVE include graph rooted at `StaticGameObjects.xml` (the base-game roster: the three
MP factions Allied / Soviet / Japan), and emit raw numeric stats + references as one
deterministic external JSON. The raw source stays external to this repo; nothing here is
routed, assigned or applied to any balance number.

Hard bounds (all enforced, none negotiable):
  * no execution of source data, no expression evaluation, no network access;
  * no guessed English names, no DPS derivation, no time-unit conversion, no derived
    stats — every value is copied verbatim from the source or explicitly unverified;
  * unsupported xai merge semantics, unresolved DATA/ART dependencies and macro
    references (`=$...`) produce explicit UNVERIFIED statuses, never a false value;
  * path escapes, include cycles and ambiguous case collisions are rejected/diagnosed;
  * the output destination is EXTERNAL ONLY: targets inside this repository or inside
    the EA checkout are refused, and creation is exclusive (O_CREAT|O_EXCL) so a
    racing writer cannot slip in — identical reruns are idempotent, differing ones
    are refused;
  * inheritance breaks (missing/ambiguous parent, cycle) propagate into the record's
    eligibility: never auto-balance eligible even when every local field is complete;
  * a same key/module id declared twice at the same inheritance depth is AMBIGUOUS,
    never last-wins; unsupported xai joinActions are unverified even when no
    inherited predecessor exists;
  * MCV / harvester / core-type units are `manual_review_only`, never auto-balance
    eligible; props, campaign units, buildings, eggs and neutral/system objects are
    excluded from the ordinary unit count and reported as exclusions;
  * transformed/variant modes (`_Naval`/`_Ground`/`_Ambush` equivalents, MCV
    ReplacementTemplate) stay DISTINCT records, linked to their base.

Provenance: every record carries the source revision (git HEAD, verified locally), the
declaring file's sha256 and its include chain. The EA-preserved source is NOT verified to
equal the final retail patch — that limitation is part of the output itself.

Resolution model (kept deliberately small — this is NOT a general SAGE XML engine):
  * attributes: leaf-most declaration in the inheritFrom chain wins;
  * singleton child elements (DisplayName, Body, ObjectResourceInfo, GameDependency,
    EquivalentTo): leaf-most declaration wins;
  * keyed list elements (ArmorSet by Armor, LocomotorSet by Locomotor): per-key
    leaf-most wins, unique ancestor keys survive;
  * modules (id-tagged elements one level under Behaviors/Draws/ClientBehaviors, or
    direct GameObject children): per (tag, id) leaf-most wins; Weapon /
    ReplacementTemplate refs are read from the winning module only;
  * `xai:joinAction="Remove"` removes the inherited value; any OTHER joinAction value
    (observed in the wild: "Append", an uppercase "REMOVE") is UNSUPPORTED — every
    field that would depend on that merge is marked unverified, never guessed, and
    this holds even when no inherited predecessor exists;
  * a key or module id declared TWICE at the SAME inheritance depth is AMBIGUOUS,
    never silently last-wins;
  * a broken inheritFrom chain (missing/ambiguous parent or cycle) makes the record
    ineligible for auto-balancing regardless of locally sufficient fields;
  * no joinAction is treated as Replace (recorded as an assumption).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter

SCHEMA_ID = "cameo_reference_ra3_units/1.0"
EA_NS = "uri:ea.com:eala:asset"
XAI_NS = "uri:ea.com:eala:asset:instance"
XI_NS = "http://www.w3.org/2001/XInclude"

DEFAULT_ENTRY = "StaticGameObjects.xml"

TEMPLATE_LIBRARIES = {
    "weapon": ("GlobalData/Weapon.xml", "WeaponTemplate"),
    "armor": ("GlobalData/Armor.xml", "ArmorTemplate"),
    "locomotor": ("GlobalData/Locomotor.xml", "LocomotorTemplate"),
}

# Faction directory (under the Xml root) -> Side attribute value.
FACTION_DIRS = {"allied": "Allies", "soviet": "Soviet", "japan": "Japan"}

SUPPORTED_JOIN_ACTIONS = {"Replace", "Remove"}
NO_JOIN_ACTION_ASSUMPTION = "Replace"

NUMERIC_RE = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)$")
MACRO_PREFIX_RE = re.compile(r"^=\$")
MANUAL_REVIEW_ID_RE = re.compile(r"(MCV|MINER|HARVESTER|CORE)", re.IGNORECASE)
MANUAL_REVIEW_KINDOF = {"MCV", "HARVESTER"}
CAMPAIGN_ID_RE = re.compile(r"_S\d+$")

EA_SOURCE_CAVEAT = (
    "EA-preserved source (ElectronicArts/CnC_Modding_Support); released for preservation "
    "under GPL-3.0-or-later with additional terms. NOT verified to be the final retail "
    "patch; the shipped build may differ. Values are verbatim from this revision only."
)

LICENSE_SPDX = "GPL-3.0-or-later + additional terms (see LICENSE.md in the EA source)"

DOWNSTREAM_VALIDATION_REASON = (
    "collection_only_artifact: the classification above is a STATIC include-graph "
    "candidate only; every field here is raw evidence and explicit downstream "
    "validation is required before any balance use. Nothing in this output is "
    "auto-balance eligible, not even fully-populated records."
)


# ---------------------------------------------------------------------------
# namespace-safe helpers
# ---------------------------------------------------------------------------

def localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def ns_of(tag: str | None) -> str | None:
    if tag and tag.startswith("{"):
        return tag[1:].rsplit("}", 1)[0]
    return None


def attr_get(el: ET.Element, name: str) -> str | None:
    """Attribute lookup ignoring any namespace qualifier."""
    for k, v in el.attrib.items():
        if localname(k) == name:
            return v
    return None


def join_action(el: ET.Element) -> str | None:
    """The element's own xai:joinAction (matched by namespace URI, not prefix)."""
    for k, v in el.attrib.items():
        if k == "{%s}joinAction" % XAI_NS:
            return v
    return None


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def norm_key(rel: str) -> str:
    return rel.replace("\\", "/").lower()


# ---------------------------------------------------------------------------
# path index — case-insensitive, collision-detecting
# ---------------------------------------------------------------------------

def _clean_rel(rel: str) -> bool:
    cleaned = os.path.normpath(rel.replace("\\", "/")).replace("\\", "/")
    if os.path.isabs(cleaned) or cleaned in ("..",) or cleaned.startswith("../"):
        return False
    return True


class PathIndex:
    """Index of one XML root. Resolution is case-insensitive (EA include casing is
    portable across filesystems); two DIFFERENT actual paths collapsing onto one key
    are an ambiguous case collision and are rejected. `files` may be injected (tests)
    to simulate case collisions a real filesystem cannot host."""

    def __init__(self, root: str, files: dict[str, list[str]] | None = None):
        self.root = os.path.abspath(root)
        if files is None:
            files = {}
            for dirpath, _, filenames in os.walk(self.root):
                for fn in filenames:
                    rel = os.path.relpath(os.path.join(dirpath, fn), self.root)
                    rel = rel.replace("\\", "/")
                    files.setdefault(norm_key(rel), []).append(rel)
            for v in files.values():
                v.sort()
        self.files = files
        self.case_collisions = {k: v for k, v in files.items() if len(v) > 1}

    def lookup(self, rel: str) -> str | None:
        key = norm_key(rel)
        if key in self.case_collisions:
            return None
        actual = self.files.get(key)
        return actual[0] if actual else None


# ---------------------------------------------------------------------------
# include-source resolution
# ---------------------------------------------------------------------------

def resolve_source(source: str, cur_dir_rel: str) -> tuple[str, str | None]:
    """Classify an EA include reference.

    returns (kind, relpath_or_None) with kind one of:
      "data" | "relative" | "art" | "unsupported_scheme" | "path_escape"
    """
    src = source.strip()
    lowered = src.lower()
    if lowered.startswith("data:"):
        candidate = src[5:]
        kind = "data"
    elif lowered.startswith("art:"):
        return "art", src[4:]
    elif re.match(r"^[A-Za-z0-9]+:", src):
        return "unsupported_scheme", src
    else:
        candidate = src
        kind = "relative"
    rel = candidate.replace("\\", "/")
    if kind == "relative" and cur_dir_rel:
        rel = cur_dir_rel + "/" + rel
    if not _clean_rel(rel):
        return "path_escape", rel
    return kind, rel


# ---------------------------------------------------------------------------
# the include graph walk
# ---------------------------------------------------------------------------

class FileRecord:
    __slots__ = ("rel", "sha256", "tree", "error", "includes", "xi_includes",
                 "gameobjects", "parse_ok", "include_chain")

    def __init__(self, rel: str, sha256: str | None):
        self.rel = rel
        self.sha256 = sha256
        self.tree: ET.ElementTree | None = None
        self.error: str | None = None
        self.includes: list[dict] = []
        self.xi_includes = 0
        self.gameobjects: list[ET.Element] = []
        self.parse_ok = False
        self.include_chain: list[str] = []


def walk_graph(index: PathIndex, entry_rels: list[str],
               diagnostics: list[dict]) -> dict[str, FileRecord]:
    files: dict[str, FileRecord] = {}
    stack: list[str] = []

    def load(relkey: str, via: str | None) -> None:
        if relkey in stack:
            diagnostics.append({
                "code": "include_cycle", "file": relkey, "via": via,
                "detail": "include forms a cycle on the active DFS path",
            })
            return
        if relkey in files:
            return
        actual = index.lookup(relkey)
        if actual is None:
            if relkey in index.case_collisions:
                diagnostics.append({
                    "code": "case_collision", "file": via, "detail": relkey,
                    "files": index.case_collisions[relkey],
                })
            else:
                diagnostics.append({
                    "code": "missing_entry" if via is None else "missing_include",
                    "file": via, "detail": relkey,
                })
            return
        stack.append(relkey)
        try:
            rec = FileRecord(actual, sha256_file(os.path.join(index.root, actual)))
            files[relkey] = rec
            try:
                rec.tree = ET.parse(os.path.join(index.root, actual))
                rec.parse_ok = True
            except ET.ParseError as exc:
                rec.error = "xml_parse_error: %s" % exc
                diagnostics.append({"code": "xml_parse_error", "file": actual,
                                    "detail": str(exc)})
            if rec.tree is not None:
                scan_file(rec, index, diagnostics, load)
        finally:
            stack.pop()

    for entry in entry_rels:
        load(norm_key(entry), None)
    return files


def scan_file(rec: FileRecord, index: PathIndex, diagnostics: list[dict],
              load) -> None:
    root = rec.tree.getroot()
    if root.tag not in ("{%s}AssetDeclaration" % EA_NS, "AssetDeclaration"):
        diagnostics.append({"code": "unexpected_root_element", "file": rec.rel,
                            "detail": root.tag})
    cur_dir = os.path.dirname(rec.rel).replace("\\", "/")
    inc_root = None
    for child in root:
        if localname(child.tag) == "Includes":
            inc_root = child
            break
    if inc_root is not None:
        for inc in inc_root:
            if ns_of(inc.tag) == XI_NS:
                continue  # counted below with the rest of the document
            if localname(inc.tag) != "Include":
                continue
            entry = {"type": attr_get(inc, "type"), "source": attr_get(inc, "source")}
            src = entry["source"]
            if src is None:
                diagnostics.append({"code": "include_without_source", "file": rec.rel})
                entry["status"] = "missing_source"
                rec.includes.append(entry)
                continue
            kind, rel = resolve_source(src, cur_dir)
            entry["kind"] = kind
            if kind == "art":
                entry["status"] = "art_dependency_unresolved"
                diagnostics.append({"code": "art_dependency_unresolved",
                                    "file": rec.rel, "detail": src})
            elif kind in ("path_escape", "unsupported_scheme"):
                entry["status"] = "rejected_" + kind
                diagnostics.append({"code": kind, "file": rec.rel, "detail": src})
            else:
                entry["target"] = rel
                actual = index.lookup(rel)
                if actual is None:
                    if norm_key(rel) in index.case_collisions:
                        entry["status"] = "ambiguous_case_collision"
                        diagnostics.append({
                            "code": "case_collision", "file": rec.rel,
                            "detail": "%s -> %s" % (src,
                                                    index.case_collisions[norm_key(rel)]),
                        })
                    else:
                        entry["status"] = "missing_include"
                        diagnostics.append({"code": "missing_include",
                                            "file": rec.rel, "detail": src})
                else:
                    entry["status"] = "ok"
                    entry["resolved"] = actual
                    load(norm_key(actual), rec.rel)
            rec.includes.append(entry)
    for el in root.iter():
        if ns_of(el.tag) == XI_NS:
            rec.xi_includes += 1
    if rec.xi_includes:
        diagnostics.append({"code": "xi_include_unresolved", "file": rec.rel,
                            "detail": "%d xi:include fragment(s) not resolved "
                                      "(xpointer fragment injection is out of scope)"
                                      % rec.xi_includes})
    for go in root:
        if localname(go.tag) == "GameObject":
            rec.gameobjects.append(go)


def compute_include_chains(files: dict[str, FileRecord],
                           entry_rels: list[str]) -> None:
    """Deterministic BFS chain (entry -> ... -> file, inclusive) for every visited file."""
    seen: dict[str, list[str]] = {}
    queue: list[tuple[str, list[str]]] = []
    for e in entry_rels:
        k = norm_key(e)
        if k in files:
            queue.append((k, [files[k].rel]))
    while queue:
        k, chain = queue.pop(0)
        if k in seen:
            continue
        seen[k] = chain
        files[k].include_chain = chain
        rec = files[k]
        for inc in sorted(rec.includes, key=lambda i: (i.get("source") or "")):
            if inc.get("status") == "ok":
                nk = norm_key(inc["resolved"])
                if nk not in seen:
                    queue.append((nk, chain + [files[nk].rel]))


# ---------------------------------------------------------------------------
# object table + inheritance
# ---------------------------------------------------------------------------

class ObjectDecl:
    __slots__ = ("object_id", "file", "sha256", "element", "include_chain", "inherit")

    def __init__(self, object_id, file, sha256, element, include_chain, inherit):
        self.object_id = object_id
        self.file = file
        self.sha256 = sha256
        self.element = element
        self.include_chain = include_chain
        self.inherit = inherit


class ObjectTable:
    def __init__(self) -> None:
        self.by_id: dict[str, list[ObjectDecl]] = {}
        self.order: list[ObjectDecl] = []

    def add(self, decl: ObjectDecl) -> None:
        self.by_id.setdefault(decl.object_id.lower(), []).append(decl)
        self.order.append(decl)


def collect_objects(files: dict[str, FileRecord], diagnostics: list[dict]) -> ObjectTable:
    table = ObjectTable()
    for relkey in sorted(files):
        rec = files[relkey]
        if not rec.parse_ok:
            continue
        for el in rec.gameobjects:
            oid = attr_get(el, "id")
            if oid is None or not oid.strip():
                diagnostics.append({"code": "missing_object_id", "file": rec.rel})
                continue
            inherit = attr_get(el, "inheritFrom")
            if inherit is not None and inherit.startswith("^"):
                diagnostics.append({"code": "caret_inherit_prefix", "file": rec.rel,
                                    "detail": oid})
                inherit = inherit[1:]
            table.add(ObjectDecl(oid, rec.rel, rec.sha256, el, rec.include_chain,
                                 inherit))
    for oid_l, decls in table.by_id.items():
        if len(decls) > 1:
            diagnostics.append({
                "code": "duplicate_object_id", "detail": oid_l,
                "files": sorted(d.file for d in decls),
            })
    return table


def inherit_chain(decl: ObjectDecl, table: ObjectTable, diagnostics: list[dict]
                  ) -> tuple[list[ObjectDecl], dict | None]:
    """Returns (chain, break_info). break_info is None only when the whole inheritFrom
    chain resolves; otherwise {"cause": cycle|missing_parent|ambiguous_parent, ...}.
    A broken chain never silently degrades to "the visible prefix is the truth"."""
    chain = [decl]
    seen = {decl.object_id.lower()}
    cur = decl
    while cur.inherit:
        parent_id = cur.inherit.lower()
        if parent_id in seen:
            diagnostics.append({"code": "inheritance_cycle", "detail": decl.object_id})
            return chain, {"cause": "cycle", "detail": decl.object_id}
        decls = table.by_id.get(parent_id)
        if not decls:
            detail = "%s -> %s" % (decl.object_id, cur.inherit)
            diagnostics.append({"code": "unresolvable_inherit_from", "detail": detail})
            return chain, {"cause": "missing_parent", "detail": detail}
        if len(decls) > 1:
            detail = "%s -> %s" % (decl.object_id, cur.inherit)
            diagnostics.append({
                "code": "ambiguous_inherit_target", "detail": detail,
                "files": sorted(d.file for d in decls),
            })
            return chain, {"cause": "ambiguous_parent", "detail": detail,
                           "files": sorted(d.file for d in decls)}
        cur = decls[0]
        chain.append(cur)
        seen.add(parent_id)
    return chain, None


# ---------------------------------------------------------------------------
# field resolution
# ---------------------------------------------------------------------------

STATUS_OK = "verbatim"
STATUS_LOCAL = "local"
STATUS_INHERITED = "inherited"
STATUS_UNAVAILABLE = "unavailable_not_declared"
STATUS_REMOVED = "removed_by_override"
STATUS_MERGE_UNSUPPORTED = "unverified_unsupported_merge"
STATUS_AMBIGUOUS_DUPLICATE = "unverified_ambiguous_duplicate_key"
STATUS_MACRO = "unverified_macro_reference_not_evaluated"
STATUS_NONNUMERIC = "unverified_unsupported_expression"
STATUS_AMBIGUOUS_DUPLICATE = "unverified_ambiguous_duplicate_key"


def _has_unverified(rec: dict, skip_account_macro: bool = False) -> bool:
    """True when any status key on the record carries an unverified value. Status
    presence of raw fields is never claimed as semantic completeness; this walker is
    the honest count of how much of the record is NOT fully verified.
    skip_account_macro: the BuildCost Account string is recorded raw by design and is
    not a stat — it is counted separately, never lumped with stat fields."""
    stack: list = [rec]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                if isinstance(v, str) and v.startswith("unverified_"):
                    if skip_account_macro and k == "account_status":
                        continue
                    return True
                stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)
    return False


def _has_cost_account_macro(rec: dict) -> bool:
    for cost in rec.get("build_cost", {}).get("build_costs", []):
        if cost.get("account_status") == STATUS_MACRO:
            return True
    return False


class Resolution:
    """One resolved field: element/attr handle + status + where it came from."""

    __slots__ = ("value", "status", "resolution")

    def __init__(self, value, status: str, resolution: str):
        self.value = value
        self.status = status
        self.resolution = resolution


def _decls_for_tag(chain: list[ObjectDecl], tag: str) -> list[tuple[int, ET.Element]]:
    found = []
    for depth, decl in enumerate(chain):
        for el in decl.element:
            if localname(el.tag) == tag:
                found.append((depth, el))
    return found


def resolve_singleton(chain: list[ObjectDecl], tag: str) -> Resolution:
    """Leaf-most declaration wins; Remove drops the inherited value; ANY unsupported
    joinAction is unverified — with or without a displaced predecessor (the merge
    semantics are unknown either way, so the value is never claimed as resolved)."""
    decls = _decls_for_tag(chain, tag)
    if not decls:
        return Resolution(None, STATUS_UNAVAILABLE, "none")
    depth, el = decls[0]
    ja = join_action(el)
    if ja is not None and ja not in SUPPORTED_JOIN_ACTIONS:
        return Resolution(el, STATUS_MERGE_UNSUPPORTED,
                          "joinAction=%s@%s" % (ja, chain[depth].object_id))
    if ja == "Remove":
        return Resolution(None, STATUS_REMOVED,
                          "joinAction=Remove@%s" % chain[depth].object_id)
    return Resolution(el, STATUS_LOCAL if depth == 0 else STATUS_INHERITED,
                      chain[depth].object_id)


def resolve_list_by_key(chain: list[ObjectDecl], tag: str, key_attrs: list[str],
                        diagnostics: list[dict] | None = None
                        ) -> list[tuple[str, Resolution]]:
    """Per-key leaf-most wins; unique ancestor keys survive. A key declared TWICE at
    the SAME depth is AMBIGUOUS (never last-wins) and every consumer of it stays
    unverified."""
    per_key: dict[str, tuple[int, ET.Element, ObjectDecl]] = {}
    ambiguous: set[str] = set()
    displaced: set[str] = set()
    for depth, decl in enumerate(chain):
        for el in decl.element:
            if localname(el.tag) != tag:
                continue
            key = "|".join((attr_get(el, a) or "") for a in key_attrs)
            existing = per_key.get(key)
            if existing is not None and depth > existing[0]:
                displaced.add(key)
                continue
            if existing is not None:
                ambiguous.add(key)  # same-depth duplicate: never last-wins
            per_key[key] = (depth, el, decl)
    out = []
    for key in sorted(per_key):
        depth, el, decl = per_key[key]
        if key in ambiguous:
            if diagnostics is not None:
                diagnostics.append({"code": "ambiguous_duplicate_key", "object": decl.object_id,
                                    "detail": "%s key=%r declared twice at the same "
                                              "inheritance depth; resolved as ambiguous"
                                              % (tag, key)})
            out.append((key, Resolution(None, STATUS_AMBIGUOUS_DUPLICATE, decl.object_id)))
            continue
        ja = join_action(el)
        if ja is not None and ja not in SUPPORTED_JOIN_ACTIONS:
            out.append((key, Resolution(el, STATUS_MERGE_UNSUPPORTED,
                                        "joinAction=%s@%s" % (ja, decl.object_id))))
        elif ja == "Remove":
            out.append((key, Resolution(None, STATUS_REMOVED,
                                        "joinAction=Remove@%s" % decl.object_id)))
        else:
            out.append((key, Resolution(el, STATUS_LOCAL if depth == 0 else STATUS_INHERITED,
                                        decl.object_id)))
    return out


def resolve_attr(chain: list[ObjectDecl], name: str) -> Resolution:
    for depth, decl in enumerate(chain):
        val = attr_get(decl.element, name)
        if val is not None:
            return Resolution(val, STATUS_LOCAL if depth == 0 else STATUS_INHERITED,
                              decl.object_id)
    return Resolution(None, STATUS_UNAVAILABLE, "none")


# ---------------------------------------------------------------------------
# module-level extraction (weapons, replacement templates)
# ---------------------------------------------------------------------------

MODULE_CONTAINER_TAGS = {"Behaviors", "ClientBehaviors", "Draws"}


def _module_decls(chain: list[ObjectDecl]) -> list[tuple[int, str, str, ET.Element, ObjectDecl]]:
    """(depth, tag, module_id, element, decl) for id-tagged module elements: direct
    GameObject children plus one level inside the known container groups."""
    out = []
    for depth, decl in enumerate(chain):
        for child in decl.element:
            tag = localname(child.tag)
            mid = attr_get(child, "id")
            if mid is not None:
                out.append((depth, tag, mid, child, decl))
            elif tag in MODULE_CONTAINER_TAGS:
                for sub in child:
                    out.append((depth, localname(sub.tag), attr_get(sub, "id") or "",
                                sub, decl))
    return out


def merge_modules(chain: list[ObjectDecl], diagnostics: list[dict] | None = None
                  ) -> list[tuple[tuple[str, str], Resolution]]:
    """Per (tag, id) leaf-most wins. A module id declared TWICE at the SAME depth is
    AMBIGUOUS (never last-wins). ANY unsupported joinAction is unverified, with or
    without a displaced predecessor."""
    per_key: dict[tuple[str, str], tuple[int, ET.Element, ObjectDecl]] = {}
    ambiguous: set[tuple[str, str]] = set()
    displaced: set[tuple[str, str]] = set()
    for depth, tag, mid, el, decl in _module_decls(chain):
        key = (tag, mid)
        if key in per_key:
            if depth > per_key[key][0]:
                displaced.add(key)
                continue
            ambiguous.add(key)  # same-depth duplicate: never last-wins
        per_key[key] = (depth, el, decl)
    out = []
    for key in sorted(per_key):
        depth, el, decl = per_key[key]
        if key in ambiguous:
            if diagnostics is not None:
                diagnostics.append({"code": "ambiguous_duplicate_key",
                                    "object": decl.object_id,
                                    "detail": "module %s id=%r declared twice at the "
                                              "same inheritance depth; resolved as "
                                              "ambiguous" % (key[0], key[1])})
            out.append((key, Resolution(el, STATUS_AMBIGUOUS_DUPLICATE, decl.object_id)))
            continue
        ja = join_action(el)
        if ja is not None and ja not in SUPPORTED_JOIN_ACTIONS:
            out.append((key, Resolution(el, STATUS_MERGE_UNSUPPORTED,
                                        "joinAction=%s@%s" % (ja, decl.object_id))))
        elif ja == "Remove":
            out.append((key, Resolution(None, STATUS_REMOVED,
                                        "joinAction=Remove@%s" % decl.object_id)))
        else:
            out.append((key, Resolution(el, STATUS_LOCAL if depth == 0 else STATUS_INHERITED,
                                        decl.object_id)))
    return out


def descendant_by_localname(el: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in el.iter() if localname(c.tag) == name]


def _weapon_slot_ancestor(module_el: ET.Element, weapon_el: ET.Element) -> ET.Element | None:
    parents: dict[int, ET.Element] = {}
    for p in module_el.iter():
        for c in p:
            parents[id(c)] = p
    cur: ET.Element | None = weapon_el
    while cur is not None and id(cur) in parents:
        cur = parents[id(cur)]
        if cur is not None and localname(cur.tag).startswith("WeaponSlot"):
            return cur
    return None


# ---------------------------------------------------------------------------
# raw value handling
# ---------------------------------------------------------------------------

def numeric_or_status(raw: str | None) -> tuple[float | None, str]:
    if raw is None:
        return None, STATUS_UNAVAILABLE
    if NUMERIC_RE.match(raw.strip()):
        return float(raw.strip()), STATUS_OK
    if MACRO_PREFIX_RE.match(raw.strip()):
        return None, STATUS_MACRO
    return None, STATUS_NONNUMERIC


def raw_field(res: Resolution) -> dict:
    value, status = numeric_or_status(res.value)
    if status == STATUS_UNAVAILABLE:
        resolution = "none"
    else:
        resolution = res.resolution
    return {"raw": res.value, "value": value, "status": status,
            "resolution": resolution}


def template_status(template_id: str | None,
                    library: dict[str, str] | None) -> dict:
    if template_id is None:
        return {"resolved": None}
    if library is None:
        return {"resolved": None, "note": "template library unavailable"}
    return {"resolved": template_id.lower() in library}


# ---------------------------------------------------------------------------
# per-object record extraction
# ---------------------------------------------------------------------------

def extract_object(decl: ObjectDecl, chain: list[ObjectDecl],
                   libraries: dict[str, dict[str, str]], source_revision: str | None,
                   license_sha: str | None, diagnostics: list[dict],
                   worktree_clean: bool | None = None) -> dict:
    oid = decl.object_id
    rec: dict = {
        "id": oid,
        "classification": None,
        "auto_balance_eligible": None,
        "static_candidate": None,
        "downstream_validation_required": None,
        "manual_review_reason": None,
    }

    # ---- plain attributes --------------------------------------------------
    rec["side"] = _res_json(resolve_attr(chain, "Side"))
    rec["editor_sorting"] = _res_json(resolve_attr(chain, "EditorSorting"))
    rec["command_set"] = _res_json(resolve_attr(chain, "CommandSet"))
    rec["production_queue_type"] = _res_json(resolve_attr(chain, "ProductionQueueType"))
    rec["build_time"] = raw_field(resolve_attr(chain, "BuildTime"))

    # ---- kind flags ----------------------------------------------------------
    ko = resolve_attr(chain, "KindOf")
    tokens = (ko.value or "").split()
    flags, flagged = [], []
    for tok in tokens:
        if tok.startswith(("+", "-")):
            flagged.append({"token": tok,
                            "note": "modifier-prefixed kindOf token; merge semantics "
                                    "unverified"})
        elif MACRO_PREFIX_RE.match(tok):
            flagged.append({"token": tok, "note": "macro reference; not evaluated"})
        else:
            flags.append(tok)
    rec["kindof_flags"] = {"value": flags, "status": ko.status,
                           "resolution": ko.resolution}
    rec["kindof_tokens_raw"] = tokens
    rec["kindof_tokens_flagged"] = flagged
    for tok in flagged:
        diagnostics.append({"code": "kindof_flagged_token", "object": oid,
                            "detail": "%s: %s" % (tok["note"], tok["token"])})

    # ---- localization keys (raw, never translated) ---------------------------
    dn = resolve_singleton(chain, "DisplayName")
    rec["display_name_key"] = {
        "value": dn.value.text if dn.value is not None else None,
        "status": dn.status, "resolution": dn.resolution,
    }
    rec["description_key"] = _res_json(resolve_attr(chain, "Description"))
    rec["type_description_key"] = _res_json(resolve_attr(chain, "TypeDescription"))
    rec["editor_name"] = _res_json(resolve_attr(chain, "EditorName"))

    # ---- body (hp) -------------------------------------------------------------
    body = resolve_singleton(chain, "Body")
    body_entry: dict = {"status": body.status, "resolution": body.resolution}
    if body.value is not None and body.status not in (STATUS_UNAVAILABLE,
                                                      STATUS_REMOVED):
        inner = [c for c in body.value]
        if len(inner) == 1:
            mod = inner[0]
            body_entry["module_type"] = localname(mod.tag)
            mh = raw_field(Resolution(attr_get(mod, "MaxHealth"), body.status,
                                      body.resolution))
            body_entry["max_health"] = mh
        elif not inner:
            body_entry["module_type"] = None
            body_entry["max_health"] = {"raw": None, "value": None,
                                        "status": STATUS_UNAVAILABLE}
        else:
            body_entry["module_type"] = sorted(localname(c.tag) for c in inner)
            body_entry["max_health"] = {"raw": None, "value": None,
                                        "status": STATUS_NONNUMERIC}
            diagnostics.append({"code": "body_multiple_children", "object": oid})
    rec["body"] = body_entry

    # ---- build cost --------------------------------------------------------------
    ori = resolve_singleton(chain, "ObjectResourceInfo")
    cost_entry: dict = {"status": ori.status, "resolution": ori.resolution,
                        "build_costs": []}
    if ori.value is not None and ori.status not in (STATUS_UNAVAILABLE,
                                                    STATUS_REMOVED):
        for bc in descendant_by_localname(ori.value, "BuildCost"):
            acct = attr_get(bc, "Account")
            amt_raw = attr_get(bc, "Amount")
            amt_value, amt_status = numeric_or_status(amt_raw)
            cost_entry["build_costs"].append({
                "account_raw": acct,
                "account_status": (STATUS_MACRO if acct and MACRO_PREFIX_RE.match(acct.strip())
                                   else (STATUS_OK if acct else STATUS_UNAVAILABLE)),
                "amount_raw": amt_raw, "amount_value": amt_value,
                "amount_status": amt_status,
            })
    rec["build_cost"] = cost_entry

    # ---- locomotors ----------------------------------------------------------------
    locs = []
    for _key, res in resolve_list_by_key(chain, "LocomotorSet",
                                         ["Locomotor", "Condition"], diagnostics):
        if res.value is None:
            locs.append({"status": res.status, "resolution": res.resolution})
            continue
        loc_id = attr_get(res.value, "Locomotor")
        cond = attr_get(res.value, "Condition")
        sp = raw_field(Resolution(attr_get(res.value, "Speed"), res.status,
                                  res.resolution))
        entry = {
            "locomotor": loc_id, "condition": cond, "speed": sp,
            "status": res.status, "resolution": res.resolution,
            "locomotor_template": template_status(loc_id, libraries.get("locomotor")),
        }
        if sp["status"] in (STATUS_MACRO, STATUS_NONNUMERIC):
            diagnostics.append({"code": "locomotor_speed_unverified", "object": oid,
                                "detail": "%s raw=%r" % (loc_id, sp["raw"])})
        locs.append(entry)
    rec["locomotors"] = locs

    # ---- armor refs ------------------------------------------------------------------
    armors = []
    for _key, res in resolve_list_by_key(chain, "ArmorSet", ["Armor"], diagnostics):
        if res.value is None:
            armors.append({"status": res.status, "resolution": res.resolution})
            continue
        armor_id = attr_get(res.value, "Armor")
        cond = attr_get(res.value, "Conditions")
        armors.append({
            "armor": armor_id,
            "conditions_raw": cond,
            "conditions": cond.split() if cond else [],
            "damage_fx": attr_get(res.value, "DamageFX"),
            "status": res.status, "resolution": res.resolution,
            "armor_template": template_status(armor_id, libraries.get("armor")),
        })
    rec["armor_refs"] = armors

    # ---- dependencies ------------------------------------------------------------------
    gd = resolve_singleton(chain, "GameDependency")
    dep_entry: dict = {"status": gd.status, "resolution": gd.resolution,
                       "needed_upgrades": [], "other_dependency_keys": []}
    if gd.value is not None and gd.status not in (STATUS_UNAVAILABLE, STATUS_REMOVED):
        for child in gd.value:
            tag = localname(child.tag)
            if tag == "NeededUpgrade":
                if child.text and child.text.strip():
                    dep_entry["needed_upgrades"].append(child.text.strip())
            else:
                dep_entry["other_dependency_keys"].append(tag)
    rec["dependencies"] = dep_entry

    # ---- variant links -------------------------------------------------------------------
    eq = resolve_singleton(chain, "EquivalentTo")
    rec["equivalent_to"] = {
        "value": eq.value.text if eq.value is not None else None,
        "status": eq.status, "resolution": eq.resolution,
    }
    rec["inherits_from"] = decl.inherit

    # ---- weapons (references + conditions only; NO weapon stats) ---------------------------
    weapons = []
    replaces_into = []
    for (tag, mid), res in merge_modules(chain, diagnostics):
        if res.value is None:
            continue
        for w in descendant_by_localname(res.value, "Weapon"):
            template = attr_get(w, "Template")
            if template is None:
                continue
            slot_parent_el = _weapon_slot_ancestor(res.value, w)
            statuses = {}
            for k_json, k_attr in (("forbidden_object_status", "ForbiddenObjectStatus"),
                                   ("required_object_status", "RequiredObjectStatus"),
                                   ("upgrade_created", "UpgradeCreated")):
                v_r = attr_get(w, k_attr)
                if v_r is not None:
                    statuses[k_json] = v_r
            weapons.append({
                "template": template,
                "ordering": attr_get(w, "Ordering"),
                "slot": {"tag": localname(slot_parent_el.tag) if slot_parent_el is not None else None,
                         "id": attr_get(slot_parent_el, "ID") if slot_parent_el is not None else None},
                "conditions": statuses,
                "conditions_raw": {localname(k): v for k, v in w.attrib.items()
                                   if localname(k) not in ("Template", "Ordering", "id")
                                   and not k.startswith("{%s}" % XAI_NS)},
                "module": {"tag": tag, "id": mid},
                "status": res.status, "resolution": res.resolution,
                "weapon_template": template_status(template, libraries.get("weapon")),
            })
            if template_status(template, libraries.get("weapon"))["resolved"] is False:
                diagnostics.append({"code": "weapon_template_ref_unresolved",
                                    "object": oid, "detail": template})
        for rt in descendant_by_localname(res.value, "ReplacementTemplate"):
            if rt.text and rt.text.strip():
                replaces_into.append({
                    "value": rt.text.strip(), "module": {"tag": tag, "id": mid},
                    "status": res.status, "resolution": res.resolution,
                })
    rec["weapon_refs"] = weapons
    rec["replaces_into"] = replaces_into

    # ---- provenance --------------------------------------------------------------------------
    rec["provenance"] = {
        "source_revision": source_revision,
        "source_worktree_clean": worktree_clean,
        "declaring_file": decl.file,
        "declaring_file_sha256": decl.sha256,
        "include_chain": list(decl.include_chain),
        "inherit_chain": [c.object_id for c in chain],
        "license": LICENSE_SPDX,
        "license_file_sha256": license_sha,
        "ea_source_caveat": EA_SOURCE_CAVEAT,
    }
    return rec


def _res_json(res: Resolution) -> dict:
    return {"value": res.value, "status": res.status, "resolution": res.resolution}


# ---------------------------------------------------------------------------
# classification
# ---------------------------------------------------------------------------

def classify(rec: dict, decl: ObjectDecl) -> tuple[str, str | None, str | None]:
    """Returns (category, exclusion_reason, manual_review_reason)."""
    oid = decl.object_id
    parts = decl.file.split("/")
    dir_top = parts[0].lower() if parts else ""
    sub = parts[1].lower() if len(parts) > 1 else ""
    in_units_dir = sub == "units" and dir_top in FACTION_DIRS
    side = rec["side"]["value"]
    sorting = rec["editor_sorting"]["value"]

    if oid.startswith("Base"):
        return "excluded", "base_template", None
    if sorting == "CAMPAIGN_UNITS" or CAMPAIGN_ID_RE.search(oid):
        return "excluded", "campaign_variant", None
    if in_units_dir and side in FACTION_DIRS.values():
        if sorting == "UNIT":
            flags = rec["kindof_flags"]["value"]
            reasons = []
            for flag in sorted(MANUAL_REVIEW_KINDOF):
                if flag in flags:
                    reasons.append("kindof:%s" % flag)
            m = MANUAL_REVIEW_ID_RE.search(oid)
            if m:
                reasons.append("id_pattern:%s" % m.group(1).lower())
            if reasons:
                return "manual_review_only", None, "; ".join(reasons)
            return "unit", None, None
        if sorting in ("STRUCTURE", "MISC_MAN_MADE"):
            return "excluded", "building_or_structure", None
        if sorting == "SYSTEM":
            return "excluded", "system_object", None
        return "excluded", "no_resolved_editorsorting", None
    if sorting in ("UNIT", "CAMPAIGN_UNITS"):
        return "excluded", "outside_faction_units_dir", None
    if sub == "structures":
        return "excluded", "building_or_structure", None
    if sub == "eggs":
        return "excluded", "egg", None
    if sub in ("props", "crates"):
        return "excluded", "prop_or_neutral_or_system", None
    if dir_top in ("props", "crates", "neutral", "system", "baseobjects"):
        return "excluded", "prop_or_neutral_or_system", None
    return "excluded", "unclassified_dir:%s" % (dir_top or "root"), None


def _unavailable_fields(rec: dict) -> list[dict]:
    out = []
    if rec["display_name_key"]["value"] is None and \
            rec["display_name_key"]["status"] != STATUS_REMOVED:
        out.append({"field": "display_name_key",
                    "reason": rec["display_name_key"]["status"]})
    body = rec["body"]
    mh = body.get("max_health") or {}
    if body["status"] == STATUS_UNAVAILABLE:
        out.append({"field": "hp", "reason": "body_not_declared"})
    elif body["status"] in (STATUS_REMOVED, STATUS_MERGE_UNSUPPORTED):
        out.append({"field": "hp", "reason": body["status"]})
    elif mh.get("status") != STATUS_OK:
        out.append({"field": "hp", "reason": mh.get("status")})
    if not rec["build_cost"]["build_costs"] or all(
            c["amount_status"] != STATUS_OK for c in rec["build_cost"]["build_costs"]):
        reason = rec["build_cost"]["status"] if not rec["build_cost"]["build_costs"] \
            else "amount_" + rec["build_cost"]["build_costs"][0]["amount_status"]
        out.append({"field": "build_cost", "reason": reason})
    if rec["build_time"]["status"] not in (STATUS_OK,):
        out.append({"field": "build_time", "reason": rec["build_time"]["status"]})
    return out


def _excluded_row(rec: dict, decl: ObjectDecl) -> dict:
    parts = decl.file.split("/")
    return {
        "id": decl.object_id,
        "declaring_file": decl.file,
        "category_dir": parts[0] if parts else "",
        "side": rec["side"]["value"],
        "editor_sorting": rec["editor_sorting"]["value"],
        "exclusion_reason": rec.get("exclusion_reason"),
        "provenance": rec.get("provenance"),
    }


# ---------------------------------------------------------------------------
# template libraries
# ---------------------------------------------------------------------------

def load_template_libraries(index: PathIndex, diagnostics: list[dict]
                            ) -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    libraries: dict[str, dict[str, str]] = {}
    lib_files: dict[str, str] = {}
    for lib, (rel, decl_tag) in TEMPLATE_LIBRARIES.items():
        actual = index.lookup(rel)
        if actual is None:
            diagnostics.append({"code": "template_library_missing", "detail": rel})
            continue
        try:
            lroot = ET.parse(os.path.join(index.root, actual)).getroot()
        except ET.ParseError as exc:
            diagnostics.append({"code": "template_library_parse_error",
                                "detail": "%s: %s" % (rel, exc)})
            continue
        ids: dict[str, str] = {}
        for el in lroot.iter():
            if localname(el.tag) == decl_tag:
                tid = attr_get(el, "id")
                if tid:
                    ids.setdefault(tid.lower(), tid)
        libraries[lib] = ids
        lib_files[lib] = actual
    return libraries, lib_files


# ---------------------------------------------------------------------------
# main driver
# ---------------------------------------------------------------------------

def git_evidence(root: str) -> dict:
    """Local git evidence for the source checkout: HEAD sha, toplevel and worktree
    cleanliness (porcelain status). No network, no fetching, no source execution.
    A dirty worktree is recorded, never certified."""
    out: dict = {"head": None, "toplevel": None, "clean": None,
                 "dirty_entries": None, "dirty_sample": None, "error": None}
    try:
        out["head"] = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"],
                                     capture_output=True, text=True, timeout=30,
                                     check=True).stdout.strip() or None
    except Exception as exc:
        out["error"] = "rev-parse HEAD failed: %s" % exc
        return out
    try:
        out["toplevel"] = subprocess.run(["git", "-C", root, "rev-parse", "--show-toplevel"],
                                         capture_output=True, text=True, timeout=30,
                                         check=True).stdout.strip() or None
    except Exception as exc:
        out["error"] = "show-toplevel failed: %s" % exc
    try:
        st = subprocess.run(["git", "-C", root, "status", "--porcelain"],
                            capture_output=True, text=True, timeout=60, check=True)
        lines = sorted(l for l in st.stdout.splitlines() if l.strip())
        out["dirty_entries"] = len(lines)
        out["dirty_sample"] = lines[:10]
        out["clean"] = not lines
    except Exception as exc:
        out["error"] = (out["error"] or "") + " status failed: %s" % exc
        out["clean"] = None
    return out


def build_document(source_root: str, entry_rels: list[str],
                   diagnostics: list[dict] | None = None,
                   index_files: dict[str, list[str]] | None = None) -> dict:
    diagnostics = diagnostics if diagnostics is not None else []
    index = PathIndex(source_root, files=index_files)
    for key, actuals in sorted(index.case_collisions.items()):
        diagnostics.append({"code": "case_collision_index", "detail": key,
                            "files": actuals})
    files = walk_graph(index, entry_rels, diagnostics)
    compute_include_chains(files, entry_rels)
    table = collect_objects(files, diagnostics)

    libraries, lib_files = load_template_libraries(index, diagnostics)

    evidence = git_evidence(source_root)
    revision = evidence["head"]
    toplevel = evidence["toplevel"]
    worktree_clean = evidence["clean"]
    license_sha = None
    if toplevel:
        lic = os.path.join(toplevel, "LICENSE.md")
        if os.path.exists(lic):
            license_sha = sha256_file(lic)
    if revision is None:
        diagnostics.append({"code": "source_revision_unknown",
                            "detail": evidence["error"] or "not a git checkout"})
    elif worktree_clean is None:
        diagnostics.append({"code": "source_status_unknown",
                            "detail": evidence["error"] or "git status failed"})
    elif worktree_clean is False:
        diagnostics.append({
            "code": "dirty_source_worktree",
            "detail": "%d modified/untracked entries; revision NOT certified as clean"
                      % evidence["dirty_entries"],
            "sample": evidence["dirty_sample"],
        })

    records: list[dict] = []
    excluded: list[dict] = []
    for decl in table.order:
        if len(table.by_id[decl.object_id.lower()]) > 1:
            rec = extract_object(decl, [decl], libraries, revision, license_sha,
                                 diagnostics, worktree_clean)
            rec["classification"] = "excluded"
            rec["exclusion_reason"] = "ambiguous_duplicate_id"
            rec["manual_review_reason"] = "ambiguous_duplicate_id"
            rec["auto_balance_eligible"] = False
            rec["static_candidate"] = False
            rec["downstream_validation_required"] = DOWNSTREAM_VALIDATION_REASON
            excluded.append(_excluded_row(rec, decl))
            continue
        chain, brk = inherit_chain(decl, table, diagnostics)
        rec = extract_object(decl, chain, libraries, revision, license_sha,
                             diagnostics, worktree_clean)
        if brk is not None:
            rec["inheritance_status"] = {
                "status": "unverified_broken_inheritance",
                "cause": brk["cause"], "detail": brk["detail"],
            }
            if brk.get("files"):
                rec["inheritance_status"]["files"] = brk["files"]
        category, reason, mr = classify(rec, decl)
        if brk is not None and category == "unit":
            # a broken inheritFrom chain demotes even a locally complete unit
            category = "manual_review_only"
            reason = None
            mr = ((mr + "; ") if mr else "") + "broken_inheritance:%s" % brk["cause"]
        rec["classification"] = category
        rec["exclusion_reason"] = reason
        rec["manual_review_reason"] = mr
        # UNIFORM RULE: a collection-only artifact is never balance authority.
        # `auto_balance_eligible` is FALSE for every record — the classification
        # stays on the record as a STATIC CANDIDATE, and each record names the
        # downstream validation explicitly required before any balance use. (This
        # closes the overclaim where unit status implied clearance despite
        # unresolved modules/fragments inside the record.)
        rec["auto_balance_eligible"] = False
        rec["static_candidate"] = category == "unit"
        rec["downstream_validation_required"] = DOWNSTREAM_VALIDATION_REASON
        if category == "excluded":
            excluded.append(_excluded_row(rec, decl))
        else:
            unavailable = _unavailable_fields(rec)
            if unavailable:
                rec["unavailable_fields"] = unavailable
            records.append(rec)

    records.sort(key=lambda r: (r["id"].lower(), r["provenance"]["declaring_file"]))
    excluded.sort(key=lambda r: (r["id"].lower(), r["declaring_file"]))
    diagnostics.sort(key=lambda d: json.dumps(d, sort_keys=True))

    counts = Counter(r["classification"] for r in records)
    excl_by_reason = Counter(r["exclusion_reason"] for r in excluded)
    by_faction = Counter()
    for r in records:
        by_faction["%s/%s" % (r["classification"], r["side"]["value"])] += 1

    return {
        "schema": SCHEMA_ID,
        "generated_by": "tools/reference/extract_ra3_units.py",
        "deterministic": True,
        "source": {
            "root": os.path.abspath(source_root),
            "entry_includes": list(entry_rels),
            "revision": revision,
            "worktree_clean": worktree_clean,
            "dirty_entries": evidence["dirty_entries"],
            "revision_verified": bool(revision) and worktree_clean is True,
            "license": LICENSE_SPDX,
            "license_file_sha256": license_sha,
            "ea_source_caveat": EA_SOURCE_CAVEAT,
            "raw_source_kept_external": True,
            "test_fixtures_synthetic_only": True,
        },
        "resolution_model": {
            "attributes": "leaf-most declaration in the inheritFrom chain wins",
            "singleton_elements": "leaf-most declaration wins; no joinAction treated "
                                  "as %s (assumption); an unsupported joinAction is "
                                  "unverified even without a displaced predecessor"
                                  % NO_JOIN_ACTION_ASSUMPTION,
            "keyed_lists": "ArmorSet keyed by Armor, LocomotorSet keyed by "
                           "Locomotor+Condition; per-key leaf-most wins, unique "
                           "ancestor keys survive; the same key twice at the same "
                           "depth is ambiguous (never last-wins)",
            "modules": "id-tagged elements under Behaviors/Draws/ClientBehaviors (or "
                       "direct GameObject children); (tag, id) leaf-most wins; a "
                       "module id twice at the same depth is ambiguous; "
                       "Weapon/ReplacementTemplate read from the winning module only",
            "inheritance_breaks": "a missing/ambiguous inheritFrom parent or an "
                                  "inheritance cycle makes the record ineligible "
                                  "for auto-balancing even when its local fields "
                                  "are complete",
            "join_action_supported": sorted(SUPPORTED_JOIN_ACTIONS),
            "join_action_unsupported_observed": ["Append", "REMOVE"],
            "unsupported_semantics": "marked unverified, never guessed",
        },
        "template_libraries": {
            "files": lib_files,
            "usage": "existence check of referenced template ids only; no template "
                     "stats are extracted",
        },
        "counts": {
            "files_visited": len(files),
            "gameobjects_seen": len(table.order),
            "unit_records": counts.get("unit", 0),
            "manual_review_only_records": counts.get("manual_review_only", 0),
            "excluded_records": len(excluded),
            "by_faction": dict(sorted(by_faction.items())),
            "exclusions_by_reason": dict(sorted(excl_by_reason.items(),
                                                key=lambda kv: str(kv[0]))),
            "uncertain_semantics": {
                "roster_records_with_unverified_stat_fields": sum(
                    1 for r in records if _has_unverified(r, skip_account_macro=True)),
                "roster_records_with_unresolved_cost_account_macro": sum(
                    1 for r in records if _has_cost_account_macro(r)),
                "diagnostic_code_counts": dict(sorted(
                    Counter(d["code"] for d in diagnostics).items())),
            },
        },
        "limitations": [
            EA_SOURCE_CAVEAT,
            "Scope: only the ACTIVE StaticGameObjects.xml include graph is walked. "
            "Campaign unit directories (Units_Campaign, Units_SinglePlayerCampaign), "
            "dlcontent/EP1 and map-specific XML are NOT part of that graph and are "
            "NOT globbed into the roster.",
            "No 'core'-flagged GameObject exists in the base graph; the manual-review "
            "class here is MCV (KindOf MCV / id) and harvester (KindOf HARVESTER / "
            "Miner id) only, so the 'cores' part of the ruling is reported as "
            "empty-in-this-source rather than silently dropped.",
            "Revision verification asserts HEAD == the expected commit AND a clean "
            "worktree; a dirty EA checkout is extracted but NEVER certified.",
            "auto_balance_eligible is uniformly FALSE for this collection-only "
            "artifact — classifications are static candidates and every record names "
            "the downstream validation explicitly required; unresolved weapon "
            "modules / xi:include fragments are diagnostics, never clearance.",
            "A record whose inheritFrom chain is broken (missing/ambiguous parent or "
            "a cycle) is forced out of auto-balance eligibility even when its local "
            "fields are complete; per-stat presence is not semantic completeness.",
            "xi:include xpointer fragment injection is NOT resolved; any field supplied "
            "only through such a fragment stays unavailable/unverified.",
            "ART: dependencies (models/particles) are outside this repository; they are "
            "reported as unresolved diagnostics, never resolved.",
            "Macro references ('=$...') are recorded raw and never evaluated.",
            "No DPS, no time-unit conversion, no derived stats, no English display names.",
            "Weapon/armor/locomotor template libraries are used for id existence checks "
            "only; no weapon or armor stats are extracted.",
            "Module merge semantics beyond (tag, id) child-replaces-parent are unverified.",
        ],
        "diagnostics": diagnostics,
        "units": records,
        "excluded_objects": excluded,
    }


# ---------------------------------------------------------------------------
# output
# ---------------------------------------------------------------------------

def render_document(doc: dict) -> bytes:
    payload = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=True) + "\n"
    return payload.encode("utf-8")


def _is_inside(root_dir: str, target: str) -> bool:
    """True when target is root_dir itself or lies beneath it, using REAL PATHS:
    symlinks/junctions that point into a protected root are caught even when the
    lexical path looks external. Cross-drive comparisons are simply outside."""
    try:
        root_real = os.path.normcase(os.path.realpath(os.path.abspath(root_dir)))
        target_real = os.path.normcase(os.path.realpath(os.path.abspath(target)))
        if root_real == target_real:
            return True
        rel = os.path.relpath(target_real, root_real)
    except ValueError:  # different drives on Windows
        return False
    if os.path.isabs(rel) or rel == ".." or rel.startswith("../") or rel.startswith(".." + os.sep):
        return False
    return True


_TOPLEVEL_CACHE: dict[str, str | None] = {}


def _git_toplevel(root: str) -> str | None:
    """rev-parse --show-toplevel only (no status walk); memoized."""
    key = os.path.normcase(os.path.abspath(root))
    if key not in _TOPLEVEL_CACHE:
        try:
            _TOPLEVEL_CACHE[key] = subprocess.run(
                ["git", "-C", root, "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, timeout=30, check=True,
            ).stdout.strip() or None
        except Exception:
            _TOPLEVEL_CACHE[key] = None
    return _TOPLEVEL_CACHE[key]


def default_protected_roots(doc: dict) -> list[str]:
    """MANDATORY guards for the public write_output — they cannot be emptied away:
    the repository this process runs in, plus the EA source checkout (root and its
    git toplevel, when known from the document)."""
    roots: list[str] = []
    cwd_tl = _git_toplevel(os.getcwd())
    if cwd_tl:
        roots.append(cwd_tl)
    src_root = (doc.get("source") or {}).get("root")
    if src_root:
        roots.append(os.path.abspath(src_root))
        src_tl = _git_toplevel(src_root)
        if src_tl:
            roots.append(src_tl)
    return roots


def _create_exclusive(path: str) -> int:
    """O_CREAT|O_EXCL open — two racing writers cannot both create the file."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    return os.open(path, flags, 0o644)


def _compare_existing(target: str, data: bytes) -> None:
    with open(target, "rb") as fh:
        existing = fh.read()
    if existing != data:
        raise SystemExit(
            "REFUSING overwrite: %s exists with DIFFERENT content (existing "
            "sha256 %s, new sha256 %s). Deterministic reruns must be "
            "byte-identical; delete the file or choose another output path."
            % (target, hashlib.sha256(existing).hexdigest(),
               hashlib.sha256(data).hexdigest()))


def write_output(doc: dict, output_path: str,
                 forbid_inside: tuple[str, ...] | list[str] | None = None) -> None:
    """Write to an EXTERNAL destination only. The MANDATORY guards
    (`default_protected_roots` — the running repo and the EA checkout) always apply
    and can never be emptied away; an explicit list only ADDS guards. Targets are
    compared by REAL PATH, so symlinks/junctions into a protected root cannot
    bypass. Creation is exclusive (O_CREAT|O_EXCL), so a racing writer cannot slip
    in between the existence check and the write; the race loser falls back to the
    byte-compare rule: identical content is an idempotent success, different
    content is refused."""
    data = render_document(doc)
    target = os.path.abspath(output_path)
    guards = list(default_protected_roots(doc))
    for guard in (forbid_inside or ()):
        guards.append(guard)
    for guard in guards:
        if guard and _is_inside(guard, target):
            raise SystemExit(
                "REFUSING output inside protected tree %r: %r is not an external "
                "destination. The output must live outside this repository and "
                "outside the EA source checkout."
                % (os.path.abspath(guard), target))
    parent = os.path.dirname(target)
    os.makedirs(parent, exist_ok=True)
    if os.path.exists(target):
        _compare_existing(target, data)
        return
    try:
        fd = _create_exclusive(target)
    except FileExistsError:
        # lost a creation race: the winner must have written identical bytes
        _compare_existing(target, data)
        return
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Bounded Red Alert 3 base-roster extractor (evidence collection only).")
    ap.add_argument("--source-root", required=True,
                    help="EA checkout root containing 'Red Alert 3/Xml', or the Xml "
                         "root itself")
    ap.add_argument("--output", required=True,
                    help="EXTERNAL JSON output path — must be OUTSIDE this "
                         "repository and the EA checkout; creation is exclusive "
                         "and differing reruns are refused")
    ap.add_argument("--entry", default=DEFAULT_ENTRY,
                    help="entry include file (default %s)" % DEFAULT_ENTRY)
    ap.add_argument("--expect-commit", default=None,
                    help="refuse to run if the checkout HEAD differs")
    args = ap.parse_args(argv)

    root = args.source_root
    if os.path.isdir(os.path.join(root, "Red Alert 3", "Xml")):
        root = os.path.join(root, "Red Alert 3", "Xml")
    if not os.path.exists(os.path.join(root, args.entry)):
        raise SystemExit("entry %r not found under %r" % (args.entry, root))

    evidence = git_evidence(root)
    if args.expect_commit and evidence["head"] != args.expect_commit:
        raise SystemExit("commit mismatch: expected %s, checkout HEAD is %s"
                         % (args.expect_commit, evidence["head"]))

    # protected roots: the EA checkout (Xml root + its git toplevel) and the repo
    # the tool is invoked from — the output must be external to all of them
    forbid = [os.path.abspath(root)]
    if evidence["toplevel"]:
        forbid.append(evidence["toplevel"])
    cwd_toplevel = git_evidence(os.getcwd())["toplevel"]
    if cwd_toplevel:
        forbid.append(cwd_toplevel)

    doc = build_document(root, [args.entry])
    write_output(doc, args.output, forbid_inside=forbid)
    counts = doc["counts"]
    print("units=%d manual_review_only=%d excluded=%d files=%d diagnostics=%d "
          "revision_verified=%s"
          % (counts["unit_records"], counts["manual_review_only_records"],
             counts["excluded_records"], counts["files_visited"],
             len(doc["diagnostics"]), doc["source"]["revision_verified"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
