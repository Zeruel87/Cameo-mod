"""Strict, explicitly selected structured peer evidence; no runtime certification.

The index selects exact sources to supersede Doc5. An installed but broken source
raises instead of silently reviving stale Markdown data. Unlisted files are inert.
Hashes check internal identity/integrity, not authenticity or gameplay behavior.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import re

SCHEMA = 1
INDEX = pathlib.Path("docs/reference/peer_corpus/index.json")
MAX_BYTES = 32 * 1024 * 1024
MAX_ROWS = 10000
# Explicitly reviewed migrations only; adding a source requires population and
# evidence review, not merely finding a checkout with a compatible manifest.
SUPPORTED_SOURCES = {
    "ca": "Combined Arms",
    "cnc": "OpenRA Tiberian Dawn",
    "ra": "OpenRA Red Alert",
    "ts": "OpenRA Tiberian Sun",
    "d2k": "OpenRA Dune 2000",
}
HASH = re.compile(r"[0-9a-f]{64}\Z")
ROW_PROVENANCE = (
    "extractor", "mode", "mod_id", "source_label", "checkout_head",
    "checkout_head_status", "checkout_dirty", "checkout_dirty_entries",
    "engine_pin", "expect_commit", "inputs_digest", "local_dependencies_digest",
    "source_runtime_applicability", "factory_state_certification", "max_state_certification",
)


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite peer evidence")
    if isinstance(value, dict):
        for item in value.values():
            _finite(item)
    elif isinstance(value, list):
        for item in value:
            _finite(item)


def _json(text):
    obj = json.loads(text, object_pairs_hook=_object)
    _finite(obj)
    return obj


def _bytes(path):
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("peer corpus exceeds bounded input size")
    return data


def _relative(name):
    if not isinstance(name, str) or not name or "\\" in name or ":" in name:
        raise ValueError("invalid relative evidence path")
    path = pathlib.PurePosixPath(name)
    if path.is_absolute() or any(x in (".", "..") for x in name.split("/")):
        raise ValueError("evidence path escapes its namespace")
    return name


def selections(root):
    root = pathlib.Path(root).resolve()
    index = root / INDEX
    if not index.exists():
        return []
    if not index.resolve().is_relative_to(root):
        raise ValueError("peer index escapes repository")
    doc = _json(_bytes(index))
    if not isinstance(doc, dict) or type(doc.get("schema")) is not int or doc["schema"] != SCHEMA:
        raise ValueError("unsupported peer index schema")
    items = doc.get("sources")
    if not isinstance(items, list) or not items or len(items) > 64:
        raise ValueError("peer index requires a bounded nonempty source list")
    seen, files, result = set(), set(), []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("invalid peer selection")
        source, mod = item.get("source"), item.get("mod_id")
        name = _relative(item.get("file"))
        if "/" in name or not name.endswith(".jsonl"):
            raise ValueError("peer source must name one JSONL file")
        if not isinstance(source, str) or not source.strip() or not isinstance(mod, str) or not mod:
            raise ValueError("peer source/mod identity missing")
        if SUPPORTED_SOURCES.get(mod) != source:
            raise ValueError("unsupported peer source/mod pair")
        if source.casefold() in seen or name.casefold() in files:
            raise ValueError("duplicate selected peer source or file")
        if not isinstance(item.get("sha256"), str) or not HASH.fullmatch(item["sha256"]):
            raise ValueError("peer payload hash missing")
        path = index.parent / name
        if not path.resolve().is_relative_to(index.parent.resolve()):
            raise ValueError("peer source escapes selected directory")
        seen.add(source.casefold())
        files.add(name.casefold())
        result.append((item, path))
    return result


def input_paths(root):
    """Only selected payloads affect consumer identity; the index is included."""
    root = pathlib.Path(root).resolve()
    chosen = selections(root)
    return [pathlib.Path(root) / INDEX, *(path for _, path in chosen)] if chosen else []


def _inventory_digest(entries, *, source_inputs):
    if not isinstance(entries, list) or not entries:
        raise ValueError("missing provenance hash inventory")
    table, seen = {}, set()
    for item in entries:
        if not isinstance(item, dict):
            raise ValueError("invalid provenance input")
        name = _relative(item.get("path"))
        if name.casefold() in seen:
            raise ValueError("duplicate provenance input")
        seen.add(name.casefold())
        digest = item.get("sha256_before" if source_inputs else "sha256")
        if not isinstance(digest, str) or not HASH.fullmatch(digest):
            raise ValueError("invalid provenance input hash")
        if source_inputs and (item.get("unchanged") is not True or item.get("sha256_after") != digest):
            raise ValueError("source inputs changed during extraction")
        table[name] = digest
    text = "".join(f"{name}\t{digest}\n" for name, digest in sorted(table.items()))
    return hashlib.sha256(text.encode()).hexdigest()


def read_source(path, selection):
    data = _bytes(pathlib.Path(path))
    if hashlib.sha256(data).hexdigest() != selection["sha256"]:
        raise ValueError("selected peer payload hash mismatch")
    records = [_json(line) for line in data.splitlines() if line.strip()]
    if not records or len(records) > MAX_ROWS + 1:
        raise ValueError("peer corpus has no metadata or too many rows")
    meta, *rows = records
    if not isinstance(meta, dict) or meta.get("record") != "meta" or type(meta.get("schema")) is not int or meta["schema"] != SCHEMA:
        raise ValueError("unsupported peer corpus schema/metadata")
    if type(meta.get("row_count")) is not int or meta["row_count"] != len(rows) or not rows:
        raise ValueError("peer corpus row count mismatch")
    anchor = meta.get("rifle")
    if not isinstance(anchor, dict) or type(anchor.get("hp")) not in (int, float) or anchor["hp"] <= 0:
        raise ValueError("invalid peer rifle anchor")
    if anchor.get("cost") is not None and (type(anchor["cost"]) not in (int, float) or anchor["cost"] <= 0):
        raise ValueError("invalid peer rifle cost")
    prov = meta.get("provenance")
    if not isinstance(prov, dict) or any(key not in prov for key in ROW_PROVENANCE):
        raise ValueError("peer provenance incomplete")
    if prov["source_label"] != selection["source"] or prov["mod_id"] != selection["mod_id"]:
        raise ValueError("peer source identity mismatch")
    if prov["checkout_head_status"] != "ok" or not re.fullmatch(r"[0-9a-f]{40}", prov.get("checkout_head") or ""):
        raise ValueError("peer checkout identity unverified")
    if prov["expect_commit"] != prov["checkout_head"] or prov["checkout_dirty"] is not False:
        raise ValueError("installed peer source must be pinned and clean")
    if prov["inputs_digest"] != _inventory_digest(meta.get("inputs"), source_inputs=True):
        raise ValueError("source input digest mismatch")
    if type(prov.get("input_count")) is not int or prov["input_count"] != len(meta["inputs"]):
        raise ValueError("source input count mismatch")
    if prov["local_dependencies_digest"] != _inventory_digest(prov.get("local_dependencies"), source_inputs=False):
        raise ValueError("local dependency digest mismatch")
    identities = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("record") != "unit":
            raise ValueError("peer corpus contains a non-unit row")
        rid = row.get("id")
        if not isinstance(rid, str) or not rid or rid.casefold() in identities:
            raise ValueError("duplicate or missing peer actor ID")
        identities.add(rid.casefold())
        for key in ("name", "type"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError(f"missing peer identity field: {key}")
        if type(row.get("hp")) not in (int, float) or row["hp"] <= 0:
            raise ValueError("invalid required peer hp")
        rp = row.get("provenance")
        if not isinstance(rp, dict) or any(rp.get(key) != prov[key] for key in ROW_PROVENANCE):
            raise ValueError("peer row provenance mismatch")
        numeric_keys = {"hp", "cost", "speed", "turn_speed", "limit", "w_dps",
                        "w_dps_raw", "w_damage", "w_range", "w_burst", "w_reload"}
        numeric_keys.update(key for key in row if key.startswith("eff_vs_"))
        for key in numeric_keys:
            value = row.get(key)
            if value is not None and (type(value) not in (int, float) or value < 0):
                raise ValueError(f"invalid peer numeric field: {key}")
        if "w_dps_usable" in row and type(row["w_dps_usable"]) is not bool:
            raise ValueError("invalid weapon evidence flag")
    return meta, rows


def load(root):
    """Exact source label -> (metadata, full structured unit rows)."""
    return {item["source"]: read_source(path, item) for item, path in selections(root)}
