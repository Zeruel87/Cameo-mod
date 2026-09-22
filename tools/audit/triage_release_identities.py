#!/usr/bin/env python3
"""triage_release_identities.py - C19 diagnostic: classify the D4 unmatched ids.

`audit_release_drift` reports 335 baseline ids (playtest-20260709) that no
longer exist under their original name in the measured snapshot, so the drift
gate is blind to them. Two of them (E1Droppod, E2Droppod) still exist verbatim
in the active Ruleset - the snapshot metric just excludes them (no measurable
main warheads), so "unmatched" does NOT mean deleted. This tool partitions the
raw unmatched set into exactly one row per id:

  ACTIVE_UNMEASURED  the exact name still exists in the active Ruleset, still
                     resolves cleanly, and is excluded from the snapshot metric
                     only because it has no eligible main. Says nothing about
                     damage - not "zero damage", not "deleted". If resolving
                     the name RAISES (or returns None), the row is UNRESOLVED
                     with reason `resolution_failed` - a broken weapon is never
                     dressed up as a harmless metric-only exclusion.
  RENAMED_CANDIDATE  an EXACT literal top-level header rename (-OldName:/+NewName:)
                     is proven in one of the --rename-commit commits, in a
                     KNOWN WEAPON LAYOUT file only (mods/cameo/weapons/*.yaml
                     or mods/cameo/ContentPacks/**/yaml/weapons.yaml - actor,
                     rules, chrome and sequence yamls are never evidence), the
                     final target is present in the current measured snapshot,
                     and the target is not itself a release baseline name
                     (that would be a double assignment - ambiguous instead).
                     ⚠ Historical rename evidence restores the IDENTITY LINK
                     only. It is not gameplay equivalence, not damage
                     equivalence, and NEVER licenses an accepted-drift ruling.
  UNRESOLVED         no safe evidence, or ambiguity. Fan-in is computed over
                     ALL raw edges, including edges of sources already
                     rejected as one-to-many: A->X, B->X and B->Y makes A
                     ambiguous too, not an approved unique link. Never labelled
                     DELETED/MERGED: absence from the tree alone is not proof
                     of deletion.

Evidence rules (hard):
  * Only adjacent literal top-level `-OldName:`/`+NewName:` pairs inside a diff
    hunk that contains exactly one removed and one added top-level header.
    Field edits, `^`-templates, `-Key:` cancellations and multi-header hunks
    are never evidence. Names are never inferred from fuzzy similarity.
  * Rename chains are NOT followed by default; --follow-rename-chains opts
    into the strict chain mode defined below.

Chain mode (--follow-rename-chains, default OFF):
  With the flag, a first-hop target that is itself unmatched may be followed
  through further EXACT adjacent rename edges from the supplied commits:
    * only edges the existing parser already produced - never fuzzy, never
      non-adjacent, never multi-header hunks;
    * the global fan-in / one-to-many / cycle rejections still apply, over
      ALL raw edges including edges of already-rejected sources; every node
      consults the rejected-evidence map FIRST - rejected evidence is never
      routed around;
    * one unambiguous provenance tuple (commit, path) per hop: duplicate
      identical records are harmless, the same old->new pair bound to
      distinct commits or paths is ambiguity - never "pick the first";
    * successive hop commits must be DISTINCT and strictly proper ancestors
      (git merge-base --is-ancestor, cached per ordered pair, fail-closed
      with exit 2 on any git error), independent of ref input order - same
      commit, reverse chronology or incomparable branches reject;
    * traversal is bounded and cycle-checked; no string similarity anywhere;
      any post-origin node present in the measured baseline population
      rejects; still-active intermediates reject even when excluded from
      the snapshot;
    * the terminal must be active and resolve cleanly, and be measured in
      the current snapshot; anything else is UNRESOLVED with a precise
      reason, the partial traversed chain (`evidence_chain`) and, when the
      chain walks into rejected evidence, a separate `rejection_evidence`
      field;
    * two release ids may not both claim one terminal - converging paths
      downgrade BOTH rows.
  ⚠ Collision coverage is ONLY the measured baseline population plus the
  PROVIDED historical evidence - not exhaustive history, not full
  historical-namespace proof, not identity certification. Confidence stays
  RENAMED_CANDIDATE: never harmless, never equivalent, never accepted drift.
  * Draft rename maps (e.g. tools/rename/rename_map_weapons.yaml) are plans,
    not evidence - only committed git hunks count.

Every git invocation is bound to the repository with `git -C <repo>` so the
external CWD can never point the tool at another repo, and commit refs are
resolved through `git rev-parse --verify --end-of-options` into validated
40-hex immutable hashes before any other use.

⚠ MEASUREMENT BASIS: the snapshot and Ruleset are read from the CURRENT
WORKING TREE, not from gitHEAD. The report carries a `worktree_dirty` flag and
a caveat; a dirty worktree means the measured values are NOT certified by
gitHEAD, and dirty-tree values never certify gitHEAD.

Read-only: prints one JSON document to stdout, writes nothing, changes no
ratchet in audit_release_drift.py and no baseline/reference file. Exit code is
0 whenever the triage ran (UNRESOLVED rows are information, not failures);
unknown refs, non-ancestor commits and git failures are refused with exit 2.

Usage: python tools/audit/triage_release_identities.py \
         [--rename-commit <commit>]...      # e.g. 7a296c96d bcb1a8f05
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import miniyaml
from audit_release_drift import load_baseline
from gen_release_baseline import snapshot

# A top-level yaml header is a bare `Name:` in column 0. Current ids are
# underscore-only per DESIGN, but the legacy release corpus also carries
# dotted/hyphenated names (e.g. EMPDisable.anim, TSCABAL_EMP_Disable.end):
# interior dots/hyphens are accepted literally, still with no leading
# whitespace, no leading -/^, no inline value.
TOP_HEADER = re.compile(r"^([A-Za-z0-9_][A-Za-z0-9_.-]*):$")
FULL_HASH = re.compile(r"^[0-9a-f]{40}$")

# Known weapon layouts. Anything else (actor rules, chrome, sequences, audio,
# maps, docs) is never weapon-rename evidence, however convincing it looks.
ROOT_WEAPONS_PREFIX = "mods/cameo/weapons/"
PACK_WEAPONS_PREFIX = "mods/cameo/ContentPacks/"
PACK_WEAPONS_SUFFIX = "/yaml/weapons.yaml"

# Non-content lines that can appear inside a git show body; never diff payload.
DIFF_META_PREFIXES = (
    "index ", "old mode ", "new mode ", "deleted file mode ", "new file mode ",
    "rename from ", "rename to ", "copy from ", "copy to ",
    "similarity index ", "dissimilarity index ", "\\ No newline",
)

STATUS_ACTIVE = "ACTIVE_UNMEASURED"
STATUS_RENAMED = "RENAMED_CANDIDATE"
STATUS_UNRESOLVED = "UNRESOLVED"


def _git(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def _refuse(msg: str) -> None:
    """Hard refusal: message on stderr, process exit code 2."""
    print(f"triage: {msg}", file=sys.stderr)
    raise SystemExit(2)


def _first_err(cp: subprocess.CompletedProcess) -> str:
    return ((cp.stderr or "").strip().splitlines() or ["<no stderr>"])[0]


def _validated_hash(commit: str) -> str:
    if not FULL_HASH.match(commit):
        _refuse(f"refusing non-immutable commit value {commit!r} - expected a "
                "full 40-hex hash")
    return commit


def is_weapon_yaml(path: str) -> bool:
    """True only for the two documented weapon layouts.

    mods/cameo/weapons/<name>.yaml (exactly one level) and
    mods/cameo/ContentPacks/<pack>[/<faction>]/yaml/weapons.yaml.
    Conservative by design: no broad alias proof is invented.
    """
    p = str(path).replace("\\", "/")
    if p.startswith(ROOT_WEAPONS_PREFIX) and p.endswith(".yaml"):
        rest = p[len(ROOT_WEAPONS_PREFIX):]
        return bool(rest) and "/" not in rest
    if p.startswith(PACK_WEAPONS_PREFIX) and p.endswith(PACK_WEAPONS_SUFFIX):
        rest = p[len(PACK_WEAPONS_PREFIX):-len(PACK_WEAPONS_SUFFIX)]
        return bool(rest)
    return False


def resolve_commit(ref: str, repo: pathlib.Path | str, run=_git) -> str:
    """Turn any commit-ish into the full immutable commit hash git resolves.

    Refuses anything git cannot resolve as a commit (exit 2) - a typo or an
    unknown ref must never silently yield empty evidence. `--end-of-options`
    keeps a hostile/odd ref from being parsed as a flag.
    """
    cp = run(["git", "-C", str(repo), "rev-parse", "--verify",
              "--end-of-options", f"{ref}^{{commit}}"])
    if cp.returncode != 0:
        _refuse(f"refusing unknown commit '{ref}' - git cannot resolve it as "
                f"a commit ({_first_err(cp)})")
    return _validated_hash(cp.stdout.strip())


def head_commit(repo: pathlib.Path | str, run=_git) -> str:
    """Validated 40-hex HEAD of the bound repo; failure is fatal (exit 2)."""
    cp = run(["git", "-C", str(repo), "rev-parse", "--verify",
              "--end-of-options", "HEAD"])
    if cp.returncode != 0:
        _refuse(f"cannot resolve HEAD for {repo} ({_first_err(cp)})")
    return _validated_hash(cp.stdout.strip())


def worktree_dirty(repo: pathlib.Path | str, run=_git) -> bool:
    """Whole-worktree dirty flag backing the measurement-basis caveat."""
    cp = run(["git", "-C", str(repo), "status", "--porcelain"])
    if cp.returncode != 0:
        _refuse(f"git status failed for {repo} ({_first_err(cp)})")
    return bool(cp.stdout.strip())


def require_ancestor(commit: str, repo: pathlib.Path | str, run=_git) -> None:
    """Refuse commits that are not ancestors of the current HEAD (exit 2)."""
    _validated_hash(commit)
    cp = run(["git", "-C", str(repo), "merge-base", "--is-ancestor",
              commit, "HEAD"])
    if cp.returncode != 0:
        _refuse(f"refusing commit {commit} - not an ancestor of the current "
                "HEAD, so its hunks do not describe this tree's history")


def parse_rename_pairs(diff_text: str) -> list[dict]:
    """Extract exact top-level rename pairs from `git show` output.

    Per hunk: record an {path, old, new} item ONLY if the path is a known
    weapon layout, the hunk contains exactly one removed and one added
    top-level header, and those two lines are adjacent in the diff. Everything
    else (field edits, templates, cancellations, multiple headers, non-weapon
    yaml such as actor/rules/chrome/sequence files, non-yaml files) yields
    nothing. Old/new are bare ids without the trailing colon.
    """
    pairs: list[dict] = []
    path: str | None = None
    hunk: list[str] = []

    def headers(marker: str) -> list[tuple[int, str]]:
        out = []
        for i, line in enumerate(hunk):
            if not line.startswith(marker):
                continue
            m = TOP_HEADER.match(line[1:])
            if m:
                out.append((i, m.group(1)))
        return out

    def flush() -> None:
        if path is None or not is_weapon_yaml(path) or not hunk:
            return
        removed = headers("-")
        added = headers("+")
        if len(removed) == 1 and len(added) == 1 and removed[0][0] + 1 == added[0][0]:
            pairs.append({"path": path, "old": removed[0][1],
                          "new": added[0][1]})

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            flush()
            # take the b/ side so renames of files themselves still resolve
            path = line.split(" b/", 1)[-1] if " b/" in line else None
            hunk = []
        elif line.startswith("@@"):
            flush()
            hunk = []
        elif line.startswith(DIFF_META_PREFIXES) or line.startswith("--- ") \
                or line.startswith("+++ "):
            continue
        elif line[:1] in ("-", "+", " ") and path is not None:
            hunk.append(line)
    flush()
    return pairs


def extract_commit_pairs(commit: str, repo: pathlib.Path | str,
                         run=_git) -> list[dict]:
    """Exact rename evidence from one commit's weapon-yaml hunks under mods/cameo."""
    _validated_hash(commit)
    cp = run(["git", "-C", str(repo), "show", "--no-color", "--format=",
              "--unified=0", commit, "--", "mods/cameo"])
    if cp.returncode != 0:
        _refuse(f"git show failed for {commit} ({_first_err(cp)})")
    return parse_rename_pairs(cp.stdout)


def resolve_evidence(evidences: list[dict]) -> tuple[dict, dict]:
    """Fold raw pair evidence into {old: edge} plus {old: rejection}.

    Rejects ambiguous mappings up front - one-to-many (the same old name bound
    to different targets) and many-to-one (two old names claiming one target,
    a merge without proof) - and any cycle among the surviving edges. Fan-in
    is computed over ALL raw edges, including edges of sources already
    rejected as one-to-many: A->X, B->X, B->Y rejects A as well. Rejections
    preserve their raw source evidence for review.
    """
    edges: dict[str, dict] = {}
    rejected: dict[str, dict] = {}
    raw_by_old: dict[str, list[dict]] = {}
    for e in evidences:
        raw_by_old.setdefault(e["old"], []).append(e)
    for old, items in raw_by_old.items():
        if len({e["new"] for e in items}) > 1:
            rejected[old] = {"reason": "ambiguous_multiple_targets",
                             "evidence": items}
    raw_by_new: dict[str, set[str]] = {}
    for e in evidences:
        raw_by_new.setdefault(e["new"], set()).add(e["old"])
    for new, olds in raw_by_new.items():
        if len(olds) > 1:
            for old in olds:
                if old not in rejected:
                    rejected[old] = {"reason": "ambiguous_shared_target",
                                     "evidence": raw_by_old[old]}
    for old, items in raw_by_old.items():
        if old in rejected:
            continue
        if items[0]["new"] == old:
            rejected[old] = {"reason": "ambiguous_cycle", "evidence": items}
        else:
            edges[old] = dict(items[0])
    for old in list(edges):
        walk: list[str] = []
        seen: set[str] = set()
        node = old
        while node in edges and node not in seen:
            seen.add(node)
            walk.append(node)
            node = edges[node]["new"]
        if node in seen:
            for cycle_node in walk[walk.index(node):]:
                if cycle_node in edges:
                    rejected[cycle_node] = {
                        "reason": "ambiguous_cycle",
                        "evidence": [edges[cycle_node]]}
                    del edges[cycle_node]
    return edges, rejected


def _hop_view(edge: dict) -> dict:
    return {k: edge[k] for k in ("commit", "path", "old", "new")}


def resolve_evidence_strict(evidences: list[dict]) -> tuple[dict, dict]:
    """Chain-mode fold: resolve_evidence + per-hop provenance unambiguity.

    A surviving edge (old -> new) must carry exactly ONE distinct provenance
    tuple (commit, path). Duplicate identical records are harmless; the same
    pair bound to distinct commits or paths is ambiguity - never "pick the
    convenient first". Fan-in / one-to-many / cycle rejections are unchanged
    and still computed over ALL raw edges, including edges of rejected
    sources.
    """
    edges, rejected = resolve_evidence(evidences)
    raw_by_old: dict[str, list[dict]] = {}
    for e in evidences:
        raw_by_old.setdefault(e["old"], []).append(e)
    for old in list(edges):
        provs = {(e["commit"], e["path"]) for e in raw_by_old[old]}
        if len(provs) > 1:
            rejected[old] = {"reason": "ambiguous_multiple_provenance",
                             "evidence": raw_by_old[old]}
            del edges[old]
    return edges, rejected


class AncestryChecker:
    """Cached `git merge-base --is-ancestor`, fail-closed on git error.

    Returncode 0 = strictly ancestral, 1 = not ancestral, anything else is a
    git failure and refuses with exit 2 - a broken git must never silently
    classify as "no ancestry"/"no evidence". Hop commits are validated 40-hex
    hashes. Results are cached per ordered pair; no history scan is run.
    """

    def __init__(self, repo: pathlib.Path | str, run=_git):
        self.repo = str(repo)
        self._run = run
        self._cache: dict[tuple[str, str], bool] = {}

    def strictly_ancestral(self, earlier: str, later: str) -> bool:
        """True iff `earlier` is a PROPER ancestor of `later` (never itself)."""
        _validated_hash(earlier)
        _validated_hash(later)
        if earlier == later:
            return False  # proper ancestor: a commit is never its own ancestor
        key = (earlier, later)
        if key in self._cache:
            return self._cache[key]
        cp = self._run(["git", "-C", self.repo, "merge-base", "--is-ancestor",
                        earlier, later])
        if cp.returncode == 0:
            result = True
        elif cp.returncode == 1:
            result = False
        else:
            _refuse(f"git merge-base --is-ancestor failed for "
                    f"{earlier[:12]}..{later[:12]} ({_first_err(cp)})")
        self._cache[key] = result
        return result


def resolve_chain(origin: str, edges: dict, rejected: dict, base: dict,
                  active_names: set[str], ancestry) -> dict:
    """Walk exact adjacent edges from `origin` (chain mode only).

    Returns {"ok", "terminal", "hops", "reason", "rejection_evidence"}.
    Every node consults the SAME conservative evidence maps - an intermediate
    whose own outgoing evidence sits in `rejected` is never routed around.
    Traversal is bounded by a seen-set (cycles/repeated nodes reject),
    successive hop commits must be DISTINCT and strictly ancestral
    (independent of ref input order), post-origin baseline-population nodes
    reject, and still-active intermediates reject. No string guessing.
    On failure `hops` includes the failing edge (full traversed chain).
    """
    hops: list[dict] = []
    seen = {origin}
    node = origin
    while True:
        # Rejected evidence is consulted BEFORE any outgoing edge is
        # considered, at every node - a rejected node is never routed around.
        if node in rejected:
            return {"ok": False, "terminal": None, "hops": hops,
                    "reason": rejected[node]["reason"],
                    "rejection_evidence": rejected[node]["evidence"]}
        edge = edges.get(node)
        if edge is None:
            return {"ok": True, "terminal": node, "hops": hops,
                    "reason": None, "rejection_evidence": None}
        nxt = edge["new"]
        failure = None
        if hops and edge["commit"] == hops[-1]["commit"]:
            failure = "chain_same_commit"
        elif hops and not ancestry.strictly_ancestral(hops[-1]["commit"],
                                                      edge["commit"]):
            failure = "chain_not_ancestrally_ordered"
        elif nxt in seen:
            failure = "chain_cycle"
        elif nxt in base:
            failure = ("intermediate_in_baseline_collision"
                       if (nxt in edges or nxt in rejected)
                       else "target_in_baseline_collision")
        elif nxt in edges and nxt in active_names:
            failure = "intermediate_still_active"
        if failure:
            return {"ok": False, "terminal": None, "hops": hops + [edge],
                    "reason": failure, "rejection_evidence": None}
        hops.append(edge)
        seen.add(nxt)
        node = nxt


def _reject_converging_terminals(rows: list[dict], counts: dict) -> None:
    """Two release ids must not both claim one candidate terminal.

    Chain mode's final global guard: if two rows classified RENAMED_CANDIDATE
    converge on the same terminal, BOTH are downgraded to UNRESOLVED with the
    full traversed chains kept visible. The edge-level fan-in rule already
    rejects shared direct targets; this closes the chain-level merge case.
    """
    by_terminal: dict[str, list[str]] = {}
    for row in rows:
        if row["status"] == STATUS_RENAMED:
            by_terminal.setdefault(row["renamed_to"], []).append(row["id"])
    for terminal, origins in by_terminal.items():
        if len(origins) < 2:
            continue
        for row in rows:
            if (row["status"] == STATUS_RENAMED and row["id"] in origins
                    and row["renamed_to"] == terminal):
                row["chain_terminal"] = row.pop("renamed_to")
                for key in ("current_flat", "current_mains", "ratio"):
                    row.pop(key, None)
                row["status"] = STATUS_UNRESOLVED
                row["reason"] = "ambiguous_converging_terminal"
                row["converging_origins"] = sorted(origins)
                counts[STATUS_RENAMED] -= 1
                counts[STATUS_UNRESOLVED] += 1


def classify(raw_ids: list[str], base: dict, now: dict,
             active_names: set[str], edges: dict, rejected: dict,
             active_resolver, follow_chains=False, ancestry=None
             ) -> tuple[list[dict], dict]:
    """Exactly one classification row per raw unmatched id; counts sum to raw.

    `active_resolver(name)` re-resolves an active name through the Ruleset:
    an exception or a None return means the weapon is BROKEN, so the row is
    UNRESOLVED/resolution_failed - never a harmless metric-only claim.
    With `follow_chains=True` (opt-in), first-hop targets that are themselves
    unmatched are followed through `resolve_chain` (needs `ancestry`);
    the default one-hop path is untouched.
    """
    if follow_chains and ancestry is None:
        raise ValueError("follow_chains=True requires an AncestryChecker")
    rows: list[dict] = []
    counts = {STATUS_ACTIVE: 0, STATUS_RENAMED: 0, STATUS_UNRESOLVED: 0}
    for name in raw_ids:
        was = base.get(name, {})
        row: dict = {
            "id": name,
            "baseline_flat": was.get("flat"),
            "baseline_mains": was.get("mains"),
        }
        if name in active_names:
            try:
                resolved = active_resolver(name)
            except Exception as exc:  # noqa: BLE001 - any failure is a refusal
                row["status"] = STATUS_UNRESOLVED
                row["reason"] = "resolution_failed"
                row["error"] = f"{type(exc).__name__}: {exc}"
            else:
                if resolved is None:
                    row["status"] = STATUS_UNRESOLVED
                    row["reason"] = "resolution_failed"
                    row["error"] = ("resolve_weapon returned None - "
                                    "unresolvable inheritance or cycle")
                else:
                    row["status"] = STATUS_ACTIVE
                    row["reason"] = ("exists_in_active_ruleset_but_excluded_"
                                     "from_snapshot_metric")
        elif name in edges:
            if not follow_chains:
                edge = edges[name]
                target = edge["new"]
                if target in base:
                    row["status"] = STATUS_UNRESOLVED
                    row["reason"] = "target_in_baseline_collision"
                    row["evidence"] = {k: edge[k] for k in ("commit", "path", "old", "new")}
                elif target not in now:
                    row["status"] = STATUS_UNRESOLVED
                    row["reason"] = "target_not_measured"
                    row["evidence"] = {k: edge[k] for k in ("commit", "path", "old", "new")}
                else:
                    cur = now[target]
                    baseline_flat = was.get("flat") or 0
                    row.update({
                        "status": STATUS_RENAMED,
                        "renamed_to": target,
                        "current_flat": cur["flat"],
                        "current_mains": cur["mains"],
                        "ratio": (round(cur["flat"] / baseline_flat, 4)
                                  if baseline_flat else None),
                        "evidence": {k: edge[k] for k in ("commit", "path", "old", "new")},
                    })
            else:
                walked = resolve_chain(name, edges, rejected, base,
                                       active_names, ancestry)
                chain_view = [_hop_view(h) for h in walked["hops"]]
                if not walked["ok"]:
                    row["status"] = STATUS_UNRESOLVED
                    row["reason"] = walked["reason"]
                    if chain_view:
                        row["evidence_chain"] = chain_view
                        row["evidence"] = chain_view[0]
                    if walked["rejection_evidence"] is not None:
                        row["rejection_evidence"] = walked["rejection_evidence"]
                else:
                    terminal = walked["terminal"]
                    row["evidence_chain"] = chain_view
                    row["evidence"] = chain_view[0]
                    if terminal not in active_names:
                        row["status"] = STATUS_UNRESOLVED
                        row["reason"] = "terminal_not_active"
                        row["chain_terminal"] = terminal
                    else:
                        try:
                            resolved = active_resolver(terminal)
                        except Exception as exc:  # noqa: BLE001 - refusal
                            row["status"] = STATUS_UNRESOLVED
                            row["reason"] = "terminal_resolution_failed"
                            row["chain_terminal"] = terminal
                            row["error"] = f"{type(exc).__name__}: {exc}"
                        else:
                            if resolved is None:
                                row["status"] = STATUS_UNRESOLVED
                                row["reason"] = "terminal_resolution_failed"
                                row["chain_terminal"] = terminal
                                row["error"] = (
                                    "resolve_weapon returned None - "
                                    "unresolvable inheritance or cycle")
                            elif terminal not in now:
                                row["status"] = STATUS_UNRESOLVED
                                row["reason"] = "target_not_measured"
                                row["chain_terminal"] = terminal
                            else:
                                cur = now[terminal]
                                baseline_flat = was.get("flat") or 0
                                row.update({
                                    "status": STATUS_RENAMED,
                                    "renamed_to": terminal,
                                    "current_flat": cur["flat"],
                                    "current_mains": cur["mains"],
                                    "ratio": (round(cur["flat"] / baseline_flat, 4)
                                              if baseline_flat else None),
                                })
        elif name in rejected:
            row["status"] = STATUS_UNRESOLVED
            row["reason"] = rejected[name]["reason"]
            row["evidence"] = rejected[name]["evidence"]
        else:
            row["status"] = STATUS_UNRESOLVED
            row["reason"] = "no_rename_evidence"
        counts[row["status"]] += 1
        rows.append(row)
    if follow_chains:
        _reject_converging_terminals(rows, counts)
    return rows, counts


def build_report(repo: pathlib.Path, rename_refs: list[str],
                 run=_git, follow_chains=False) -> dict:
    """Assemble the full stdout JSON document."""
    head = head_commit(repo, run)
    dirty = worktree_dirty(repo, run)
    meta, base = load_baseline(repo)
    now = snapshot(repo)
    rs = miniyaml.Ruleset(repo)
    raw_ids = sorted(n for n in base if n not in now)

    commit_evidence: list[dict] = []
    evidences: list[dict] = []
    for ref in rename_refs:
        commit = resolve_commit(ref, repo, run)
        require_ancestor(commit, repo, run)
        pairs = extract_commit_pairs(commit, repo, run)
        commit_evidence.append({"ref": ref, "commit": commit, "pairs": len(pairs)})
        for pair in pairs:
            evidences.append({"commit": commit, **pair})
    if follow_chains:
        edges, rejected = resolve_evidence_strict(evidences)
        ancestry = AncestryChecker(repo, run)
    else:
        edges, rejected = resolve_evidence(evidences)
        ancestry = None
    rows, counts = classify(raw_ids, base, now, set(rs.weapons), edges,
                            rejected, rs.resolve_weapon,
                            follow_chains=follow_chains, ancestry=ancestry)

    report = {
        "what": "C19 diagnostic triage of audit_release_drift D4 unmatched "
                "ids. Read-only; identity evidence only - a RENAMED_CANDIDATE "
                "is NOT damage equivalence, NOT accepted drift, NOT deletion "
                "proof.",
        "measurement_basis": "working_tree",
        "worktree_dirty": dirty,
        "caveat": "Snapshot and active-Ruleset measurements are taken from the "
                  "CURRENT WORKING TREE, not from gitHEAD. A dirty worktree "
                  "means the measured values are not certified by gitHEAD, and "
                  "dirty-tree values never certify gitHEAD. Historical rename "
                  "evidence never licenses accepted drift.",
        "gitHEAD": head,
        "releasecommit": meta["_release_commit"],
        "release_tag": meta["_release_tag"],
        "raw_unmatched": len(raw_ids),
        "classified": counts,
        "classified_sum": sum(counts.values()),
        "rename_commits": commit_evidence,
        "rows": rows,
    }
    if follow_chains:
        report["follow_rename_chains"] = True
        report["chain_collision_coverage"] = (
            "Chain mode consults ONLY the measured baseline population and "
            "the historical evidence supplied via --rename-commit. It is not "
            "exhaustive history, not full historical namespace proof, and "
            "not identity certification; RENAMED_CANDIDATE is never accepted "
            "drift.")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rename-commit", action="append", default=[],
                    metavar="COMMIT",
                    help="commit holding exact top-level weapon renames "
                         "(repeatable; e.g. 7a296c96d, bcb1a8f05)")
    ap.add_argument("--follow-rename-chains", action="store_true",
                    default=False,
                    help="opt-in: follow exact adjacent one-hop rename edges "
                         "through unmatched intermediates (strict chronology, "
                         "provenance, fan-in and cycle rejection; the terminal "
                         "must be measured, active and resolve cleanly)")
    args = ap.parse_args()

    repo = pathlib.Path(__file__).resolve().parents[2]
    report = build_report(repo, args.rename_commit,
                          follow_chains=args.follow_rename_chains)
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
