#!/usr/bin/env python3
"""miniyaml.py — shared MiniYAML loader/merger/resolver for the Cameo audit suite.

Implements the subset of OpenRA MiniYAML semantics the audits need
(see docs/history/MASTER_REPORT_2026-07-08.md Appendix A):

- tab/space indentation, ``#`` comments (``\\#`` escapes), ``key: value`` pairs
- ``^Template`` definitions, ``Trait@Suffix`` instance keys, ``-Key`` removals
- multi-file top-level merging in mod.yaml include order (later merges into earlier)
- ``Inherits`` / ``Inherits@X`` resolution with removals applied in document order

The loader is validated against engine behavior observed via
``utility --check-yaml`` and known-resolved actors (see tools/audit/README.md).
"""

from __future__ import annotations

import pathlib
import re
import sys
from dataclasses import dataclass, field


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #

@dataclass
class Node:
    key: str
    value: str
    children: list["Node"] = field(default_factory=list)
    file: str = ""
    line: int = 0

    def child(self, key: str) -> "Node | None":
        """First child whose key (before any @suffix) equals ``key``."""
        for c in self.children:
            if c.key == key:
                return c
        return None

    def children_named(self, base: str) -> list["Node"]:
        """All children whose key is ``base`` or ``base@anything``."""
        out = []
        for c in self.children:
            if c.key == base or c.key.startswith(base + "@"):
                out.append(c)
        return out

    def get(self, *path: str) -> str | None:
        """Walk child keys; return the value at the end, or None."""
        node = self
        for p in path:
            node = node.child(p)
            if node is None:
                return None
        return node.value or None

    def deep_copy(self) -> "Node":
        return Node(self.key, self.value,
                    [c.deep_copy() for c in self.children], self.file, self.line)


_COMMENT_RE = re.compile(r"(?<!\\)#.*$")


def _strip_comment(text: str) -> str:
    out = _COMMENT_RE.sub("", text)
    return out.replace("\\#", "#").rstrip()


def load(path: str | pathlib.Path) -> list[Node]:
    """Parse one MiniYAML file into a list of top-level Nodes."""
    text = pathlib.Path(path).read_text(encoding="utf-8-sig", errors="replace")
    return load_text(text, str(path))


def load_text(text: str, source: str = "<memory>") -> list[Node]:
    """Parse an archive member or supplied text using the same MiniYAML reader."""
    root: list[Node] = []
    stack: list[tuple[int, Node | None]] = [(-1, None)]
    for lineno, raw in enumerate(text.lstrip("\ufeff").splitlines(), 1):
        stripped_full = _strip_comment(raw)
        if not stripped_full.strip():
            continue
        indent = len(stripped_full) - len(stripped_full.lstrip("\t "))
        body = stripped_full.strip()
        key, _, val = body.partition(":")
        node = Node(key.strip(), val.strip(), [], source, lineno)
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        (parent.children if parent else root).append(node)
        stack.append((indent, node))
    return root


# --------------------------------------------------------------------------- #
# Merging (engine MiniYaml.Merge semantics, close approximation)
# --------------------------------------------------------------------------- #

def _merge_into(base: list[Node], index: dict[str, Node], override: list[Node]) -> None:
    """Merge ``override`` nodes into ``base`` in place: same-key nodes merge
    recursively (override value wins when non-empty), ``-Key`` removes,
    new keys append (deep-copied so source trees are never aliased)."""
    for onode in override:
        if onode.key.startswith("-"):
            target = onode.key[1:]
            if any(n.key == target for n in base):
                base[:] = [n for n in base if n.key != target]
                index.pop(target, None)
            continue
        existing = index.get(onode.key)
        if existing is not None:
            if onode.value:
                existing.value = onode.value
            child_index = {c.key: c for c in existing.children}
            _merge_into(existing.children, child_index, onode.children)
            existing.file, existing.line = onode.file, onode.line
        else:
            copy = onode.deep_copy()
            base.append(copy)
            index[copy.key] = copy


def merge_children(base: list[Node], override: list[Node]) -> list[Node]:
    """Functional wrapper over _merge_into (returns a fresh merged list)."""
    result = [n.deep_copy() for n in base]
    index = {n.key: n for n in result}
    _merge_into(result, index, override)
    return result


# --------------------------------------------------------------------------- #
# Mod manifest / ruleset
# --------------------------------------------------------------------------- #

PACKAGE_PREFIXES = {
    "cameo": "mods/cameo",
    "ContentPacks": "mods/cameo/ContentPacks",
    "common": "engine/mods/common",
}


def resolve_ref(repo_root: pathlib.Path, ref: str, mod_id: str = "cameo") -> pathlib.Path:
    """Resolve a ``package|relative/path`` manifest reference to a filesystem path.

    ``mod_id`` exists so this resolver can be pointed at ANOTHER OpenRA mod's checkout —
    Combined Arms (`mods/ca`), Shattered Paradise (`mods/sp`) — to read their unit stats for the
    balance reference corpus. CLAUDE.md rule 8e forbids hand-parsing yaml, and an inheriting
    OpenRA actor cannot be read without a resolver, so reusing this one is the only correct way
    to get a peer mod's real HP/Cost/Speed. Defaults to "cameo", so every existing caller is
    unaffected."""
    if "|" in ref:
        pkg, rel = ref.split("|", 1)
        base = PACKAGE_PREFIXES.get(pkg)
        if base is None:
            # An unknown prefix in a FOREIGN mod is normal — every mod names its own packages.
            # Prefer a real `mods/<pkg>/` directory (this is how `common|` resolves inside an
            # OpenRA checkout, where common lives at mods/common rather than Cameo's
            # engine/mods/common), and fall back to the mod's own directory.
            if mod_id != "cameo":
                by_pkg = repo_root / "mods" / pkg / rel
                if by_pkg.exists():
                    return by_pkg
                return repo_root / "mods" / mod_id / rel
            raise KeyError(f"unknown package prefix {pkg!r} in {ref!r}")
        return repo_root / base / rel
    return repo_root / "mods" / mod_id / ref


@dataclass
class Manifest:
    rules: list[pathlib.Path] = field(default_factory=list)
    weapons: list[pathlib.Path] = field(default_factory=list)
    sequences: list[pathlib.Path] = field(default_factory=list)
    fluent: list[pathlib.Path] = field(default_factory=list)
    sources: list[pathlib.Path] = field(default_factory=list)


def load_manifest(repo_root: pathlib.Path, mod_id: str = "cameo") -> Manifest:
    """Read mods/<mod_id>/mod.yaml plus every Include:'d content.yaml, in order."""
    man = Manifest()
    seen_includes: set[pathlib.Path] = set()

    def absorb(doc: list[Node], base_dir: pathlib.Path) -> None:
        section_map = {
            "Rules": man.rules, "Weapons": man.weapons,
            "Sequences": man.sequences, "FluentMessages": man.fluent,
        }
        for top in doc:
            if top.key == "Include" and top.value:
                inc = resolve_ref(repo_root, top.value, mod_id) if "|" in top.value \
                    else base_dir / top.value
                if inc in seen_includes:
                    continue
                seen_includes.add(inc)
                if inc.exists():
                    man.sources.append(inc)
                    absorb(load(inc), inc.parent)
                continue
            target = section_map.get(top.key)
            if target is None:
                continue
            for entry in top.children:
                ref = entry.key if not entry.value else f"{entry.key}:{entry.value}"
                try:
                    p = resolve_ref(repo_root, ref, mod_id)
                except KeyError:
                    continue
                if p.exists():
                    target.append(p)

    mod_yaml = repo_root / "mods" / mod_id / "mod.yaml"
    man.sources.append(mod_yaml)
    absorb(load(mod_yaml), mod_yaml.parent)
    return man


class Ruleset:
    """Merged view of every live rules/weapons/sequences file, with an
    inheritance resolver and case-insensitive actor lookup."""

    def __init__(self, repo_root: str | pathlib.Path, mod_id: str = "cameo"):
        self.repo_root = pathlib.Path(repo_root)
        self.mod_id = mod_id
        self.manifest = load_manifest(self.repo_root, mod_id)
        self.actors = self._merge_files(self.manifest.rules)
        self.weapons = self._merge_files(self.manifest.weapons)
        self.sequences = self._merge_files(self.manifest.sequences)
        self._actor_ci = {k.lower(): k for k in self.actors}
        self._weapon_ci = {k.lower(): k for k in self.weapons}
        self._seq_ci = {k.lower(): k for k in self.sequences}
        self._resolve_cache: dict[str, Node] = {}

    @staticmethod
    def _merge_files(paths: list[pathlib.Path]) -> dict[str, Node]:
        merged: dict[str, Node] = {}
        for p in paths:
            for top in load(p):
                if top.key.startswith("-"):
                    merged.pop(top.key[1:], None)
                    continue
                if top.key in merged:
                    prev = merged[top.key]
                    prev.children = merge_children(prev.children, top.children)
                    if top.value:
                        prev.value = top.value
                else:
                    merged[top.key] = top.deep_copy()
        return merged

    # ---- lookups ---------------------------------------------------------- #

    def actor(self, name: str) -> Node | None:
        return self.actors.get(name) or self.actors.get(self._actor_ci.get(name.lower(), ""))

    def weapon(self, name: str) -> Node | None:
        return self.weapons.get(name) or self.weapons.get(self._weapon_ci.get(name.lower(), ""))

    def sequence_image(self, name: str) -> Node | None:
        return self.sequences.get(name) or self.sequences.get(self._seq_ci.get(name.lower(), ""))

    # ---- inheritance ------------------------------------------------------ #

    def inherits_of(self, node: Node) -> list[tuple[str, str]]:
        """[(inherit_key, target), ...] in document order."""
        out = []
        for c in node.children:
            if c.key == "Inherits" or c.key.startswith("Inherits@"):
                out.append((c.key, c.value))
        return out

    def resolve(self, name: str, _stack: tuple[str, ...] = ()) -> Node | None:
        """Fully resolve inheritance for an actor (or weapon via resolve_weapon)."""
        return self._resolve_generic(name, self.actor, _stack)

    def resolve_weapon(self, name: str, _stack: tuple[str, ...] = ()) -> Node | None:
        return self._resolve_generic(name, self.weapon, _stack, cache_prefix="w:")

    def _resolve_generic(self, name, lookup, _stack, cache_prefix=""):
        cache_key = cache_prefix + name.lower()
        if cache_key in self._resolve_cache:
            return self._resolve_cache[cache_key]
        node = lookup(name)
        if node is None:
            return None
        if name.lower() in {s.lower() for s in _stack}:
            # cycle guard fired: everything computed above this point is
            # TAINTED (missing this subtree) and must not be cached —
            # otherwise the partial result poisons later resolutions of
            # unrelated actors (order-dependent Wood/Concrete class bug,
            # found 2026-07-18 by the balance pipeline's fixed-point test).
            self._cycle_events = getattr(self, "_cycle_events", 0) + 1
            return None
        before = getattr(self, "_cycle_events", 0)
        acc: list[Node] = []
        index: dict[str, Node] = {}
        for child in node.children:
            if child.key == "Inherits" or child.key.startswith("Inherits@"):
                parent = self._resolve_generic(
                    child.value, lookup, _stack + (name,), cache_prefix)
                if parent is not None:
                    _merge_into(acc, index, parent.children)
                continue
            _merge_into(acc, index, [child])
        resolved = Node(node.key, node.value, acc, node.file, node.line)
        if getattr(self, "_cycle_events", 0) == before:
            self._resolve_cache[cache_key] = resolved
        return resolved

    def inherit_depth(self, name: str, _seen: frozenset = frozenset()) -> int:
        node = self.actor(name)
        if node is None or name.lower() in _seen:
            return 0
        depths = [0]
        for _, target in self.inherits_of(node):
            depths.append(1 + self.inherit_depth(target, _seen | {name.lower()}))
        return max(depths)


# --------------------------------------------------------------------------- #
# Fluent
# --------------------------------------------------------------------------- #

_FLUENT_MSG = re.compile(r"^([a-zA-Z0-9_.-]+)\s*=", re.M)
_FLUENT_ATTR = re.compile(r"^\s+\.([a-zA-Z0-9_-]+)\s*=", re.M)


def load_fluent_keys(paths: list[pathlib.Path]) -> set[str]:
    """All message ids plus ``id.attr`` pairs across the given .ftl files."""
    keys: set[str] = set()
    for p in paths:
        text = p.read_text(encoding="utf-8-sig", errors="replace")
        current = None
        for line in text.splitlines():
            m = re.match(r"^([a-zA-Z0-9_.-]+)\s*=", line)
            if m:
                current = m.group(1)
                keys.add(current)
                continue
            m = re.match(r"^\s+\.([a-zA-Z0-9_-]+)\s*=", line)
            if m and current:
                keys.add(f"{current}.{m.group(1)}")
    return keys


# --------------------------------------------------------------------------- #
# Repo root discovery + CLI self-test
# --------------------------------------------------------------------------- #

def find_repo_root(start: pathlib.Path | None = None) -> pathlib.Path:
    p = (start or pathlib.Path(__file__).resolve()).parent
    while p != p.parent:
        if (p / "mods/cameo/mod.yaml").exists():
            return p
        p = p.parent
    raise SystemExit("could not locate repo root (mods/cameo/mod.yaml)")


if __name__ == "__main__":
    root = find_repo_root()
    rs = Ruleset(root)
    print(f"rules files:     {len(rs.manifest.rules)}")
    print(f"weapons files:   {len(rs.manifest.weapons)}")
    print(f"sequences files: {len(rs.manifest.sequences)}")
    print(f"fluent files:    {len(rs.manifest.fluent)}")
    print(f"actors+templates:{len(rs.actors)}")
    print(f"weapons:         {len(rs.weapons)}")
    print(f"sequence images: {len(rs.sequences)}")
    for probe in sys.argv[1:]:
        node = rs.resolve(probe)
        if node is None:
            print(f"[probe] {probe}: NOT FOUND")
            continue
        print(f"[probe] {probe}: {len(node.children)} resolved traits")
        for c in node.children[:60]:
            print(f"    {c.key}: {c.value}")
