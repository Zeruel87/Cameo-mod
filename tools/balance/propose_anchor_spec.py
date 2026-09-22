#!/usr/bin/env python3
"""Read-only anchor dossiers: current-stat diagnostics, never signable targets.

--class writes Markdown to stdout. --all writes one file per class under --out
(default docs/balance/anchors). Existing different dossiers are never overwritten.
Reference synthesis reuses the fleet producer; no reference producer is modified.
"""
import argparse
import hashlib
import json
import math
import pathlib
import re
import sys
import subprocess

import anchor_readiness as readiness
import derive_virtual_anchor as virtual
import fit_class
import firepower
import formula
import reference_distribution as rd
import reference_targets as rt
import diagnostic_output

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/audit"))
import miniyaml
import extract_stats
import audit_three_way_split

SPEC_KEYS = dict(hp="hp0", speed="speed0", range_wdist="range0_wdist", cost="cost0")
REFERENCE_KEYS = dict(hp="hp", speed="speed", range_wdist="w_range", cost="cost", dps="w_dps")


def source_provenance(root):
    """Hash the active YAML, synthesis inputs and the code that shapes displayed
    evidence (membership, tier chain, firepower), not unrelated dormant content."""
    manifest = miniyaml.load_manifest(root)
    paths = set(manifest.sources + manifest.rules + manifest.weapons)
    def hashes(items):
        return {str(path.relative_to(root)).replace("\\", "/"):
                hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(items)}
    yaml_hashes = hashes(paths)
    # Fingerprint the whole resolved input set without repeating hundreds of paths per dossier.
    # class_membership drives displayed membership; tier_chain and firepower drive DPS/K/tier;
    # audit_three_way_split.main_warheads drives the displayed W24 stacked-main count.
    data_paths = [rd.INI_CORPUS, rd.INI_ARMOR, rd.syn.DOC1,
                  root / "docs/design/ORIGINAL_UNITS_PEER_OPENRA.md",
                  root / "docs/reference/cameo_baselines/pre_reference_20260910.json",
                  root / "docs/reference/cameo_baselines/pre_reference_heroes_20260910.json"]
    data_paths.extend(rd.peer_corpus.input_paths(root))
    data_paths.extend(root / module.RELATIVE for module in
                      (rd.peer_range_evidence, rd.peer_nominal_evidence, rd.ini_weapon_selection, rd.ini_range_evidence, rd.ini_cycle_evidence, rd.peer_base_state)
                      if (root / module.RELATIVE).exists())
    modules = [pathlib.Path(module.__file__) for module in
               (virtual, fit_class, formula, readiness, audit_three_way_split, extract_stats,
                miniyaml, rd, rt, rt.fr, rd.reference_lineages, rd.peer_corpus, rd.syn,
                rd.peer_range_evidence, rd.peer_nominal_evidence, rd.ini_weapon_selection, rd.ini_range_evidence, rd.ini_cycle_evidence, rd.peer_base_state,
                virtual.class_membership, fit_class.tier_chain, firepower)]
    modules.extend([pathlib.Path(__file__), pathlib.Path(diagnostic_output.__file__)])
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True,
                              capture_output=True, check=True).stdout.strip()
    return dict(revision=revision, active_yaml_files=len(yaml_hashes),
                active_yaml_sha256=hashlib.sha256(json.dumps(yaml_hashes, sort_keys=True).encode()).hexdigest(),
                reference_input_sha256=hashes(data_paths), code_sha256=hashes(modules))


def cell(value):
    if value is None:
        return "unavailable"
    if isinstance(value, (int, float)):
        return f"{value:g}"
    return str(value).replace("|", "\\|").replace("\n", " ")


def resolve_live(rules, actor, records, cache=None):
    """One shared Ruleset extraction per actor across anchor, verifier and membership."""
    record = records.get(actor)
    if record is None:
        return None
    if cache is not None and actor in cache:
        return cache[actor]
    live = extract_stats.extract_actor(rules, actor, record[0])
    if cache is not None:
        cache[actor] = live
    return live


def member_live(actor, records, rules, cache=None):
    """Live resolved-YAML axes for one member; explicit issue, never a fallback labeled live."""
    if records.get(actor) is None:
        return dict(values={}, issue="missing from ledger")
    live = resolve_live(rules, actor, records, cache)
    return dict(values=virtual.stat_values(live) if live else {},
                issue=None if live else "unresolved or non-balance actor")


def gap_cells(live, baseline):
    """Signed gaps (live - baseline) and percentage; the percentage needs a finite positive baseline."""
    def finite(value):
        try:
            return math.isfinite(value)
        except TypeError:
            return False
    if not (finite(live) and finite(baseline)):
        return "unavailable", "unavailable"
    percent = f"{100 * (live / baseline - 1):+.1f}%" if baseline > 0 else "unavailable"
    return f"{live - baseline:+g}", percent


def live_row(member, live_by_actor):
    """Membership display row for one member; absence of live evidence is explicit."""
    row = (live_by_actor or {}).get(member["actor"])
    if row is None:
        return dict(values={}, issue="no live evidence resolved for this member")
    return row


def live_cost(member, live_by_actor):
    return live_row(member, live_by_actor)["values"].get("cost")


def accepted_refs(actor, assignments):
    return {source: ref for source, ref in assignments.get(actor, {}).items()
            if ref.get("confidence") in ("STRONG", "FAIR") and ref.get("id")}


def hero_reference_evidence(members, assignments):
    """Hero-only projections; never add heroes to ordinary distributions."""
    path = ROOT / 'docs/reference/cameo_baselines/pre_reference_heroes_20260910.json'
    if not path.exists():
        return {}
    context = rt.hero_cameo_context()
    selected = [m for m in members if m['actor'] in context.cameo_votes]
    if not selected:
        return {}
    peers = [r for r in rd.peer_hero_rows() if r.get('hero') is True]
    index = {}
    for r in peers:
        index.setdefault((r['source'], r['id']), []).append(r)
    dist = rd.build_distributions(peers)
    rt.add_cost_distribution(dist, peers)
    result = {}
    for member in selected:
        actor = member['actor']
        rows, errors = [], []
        refs = accepted_refs(actor, assignments)
        for source, ref in refs.items():
            matches = index.get((source, ref['id']), [])
            if len(matches) == 1:
                rows.append(matches[0])
            else:
                errors.append(f"{source}/{ref['id']}: {len(matches)} exact hero rows")
        record = dict(assigned=refs, used=[dict(source=r['source'], id=r['id']) for r in rows],
                      hero_references=[], errors=errors, targets={}, lane='frozen hero-only')
        for field, stat in REFERENCE_KEYS.items():
            _, value, count = rt.target_for(rows, context.cameo_votes[actor], stat, dist, context)
            record['targets'][field] = dict(value=value, sources=count)
        result[actor] = record
    return result


def reference_evidence(members, assignments):
    """Strict ID join: never substitute a same-name peer or a rejected confidence."""
    peers = rd.peer_rows()
    # Inspect hero evidence without ever adding it to ordinary distributions.
    hero_index = {}
    for peer in rd.peer_hero_rows():
        hero_index.setdefault((peer["source"], peer.get("id")), []).append(peer)
    index = {}
    for peer in peers:
        index.setdefault((peer["source"], peer.get("id")), []).append(peer)
    attached, errors, hero_refs = {}, {}, {}
    for member in members:
        actor = member["actor"]
        rows = []
        for source, ref in assignments.get(actor, {}).items():
            if ref.get("confidence") in ("STRONG", "FAIR") and not ref.get("id"):
                errors.setdefault(actor, []).append(f"{source}: accepted assignment lacks exact ID")
        for source, ref in accepted_refs(actor, assignments).items():
            matches = index.get((source, ref["id"]), [])
            if len(matches) != 1:
                heroes = hero_index.get((source, ref["id"]), [])
                if not matches and len(heroes) == 1:
                    hero_refs.setdefault(actor, []).append(dict(source=source, id=ref["id"]))
                    errors.setdefault(actor, []).append(f"{source}/{ref['id']}: hero-only evidence; ordinary synthesis withheld")
                else:
                    errors.setdefault(actor, []).append(
                        f"{source}/{ref['id']}: {len(matches)} ordinary / {len(heroes)} hero exact rows; unresolved")
            else:
                rows.append(matches[0])
        attached[actor] = rows
    attached = {actor: [row for row in rows if row["source"] in accepted_refs(actor, assignments)]
                for actor, rows in rt.expand_families(attached, peers).items()}
    dist = rd.build_distributions(peers)
    rt.add_cost_distribution(dist, peers)
    cameo = rd.cameo_rows()
    cdist = rt.cameo_context()
    by_actor = {row["id"]: row for row in cameo}
    result = {}
    for member in members:
        actor = member["actor"]
        refs = accepted_refs(actor, assignments)
        rows = attached[actor]
        record = dict(assigned=refs, used=[dict(source=r["source"], id=r.get("id")) for r in rows],
                      hero_references=hero_refs.get(actor, []), errors=errors.get(actor, []), targets={})
        if actor not in by_actor:
            record["errors"].append("absent from ordinary reference population; hero/eligibility lane requires review")
        elif refs and not record["errors"]:
            for field, stat in REFERENCE_KEYS.items():
                _, target, count = rt.target_for(rows, by_actor[actor], stat, dist, cdist)
                record["targets"][field] = dict(value=target, sources=count)
        result[actor] = record
    result.update(hero_reference_evidence(members, assignments))
    return result


def actor_snapshot(actor, records, rules, sidecars=None, live_cache=None):
    """Fresh resolved YAML and ledger side by side; no edits/extraction writes."""
    if not actor:
        return dict(actor=None, ledger={}, live={}, error="not nominated")
    record = records.get(actor)
    if record is None:
        return dict(actor=actor, ledger={}, live={}, error="missing ledger actor")
    section, unit = record
    live = resolve_live(rules, actor, records, live_cache)
    derived = (sidecars or {}).get(actor, {})
    raw, _ = fit_class.unit_inputs(unit, derived)
    weighted, fallbacks = fit_class.unit_inputs(unit, derived, use_k=True)
    tier_known = ((unit.get("design") or {}).get("tech_tier") is not None
                  or derived.get("tier_multiplier") is not None)
    metrics = dict(nominal_dps_per_tick=raw[3] if raw else None,
                   tech_tier=raw[6] if raw and tier_known else None,
                   aggregate_K=weighted[3] / raw[3] if raw and weighted and not fallbacks else None,
                   K_fallbacks=fallbacks,
                   basis="ledger and derived sidecar; nominal or K-weighted DPS per tick, not measured gameplay")
    return dict(actor=actor, ledger=virtual.stat_values(unit),
                live=virtual.stat_values(live) if live else {},
                metrics=metrics,
                error=None if live else "unresolved or non-balance actor")


def render(cls, entry, candidate, members, assignments, references, snapshots, debt, gate_error, provenance,
           excluded_members=(), live_by_actor=None):
    """Fixed seven-section dossier. All recommendation authority remains external."""
    fields = candidate["fields"]
    selected = ", ".join(cell(f) for f in candidate.get("selected_factions") or [])
    # full_count is fit-eligible class members (load_members already dropped the
    # rest), NOT the section-4 row count which also displays excluded members.
    pool_note = (f"Source pool: selected factions {selected or 'none'} — "
                 f"{candidate.get('source_count', 0)} of {candidate.get('full_count', 0)} fit-eligible "
                 "class members are in the selected factions. The reference preference and members "
                 "missing a stat give each axis its own contributing set, named below.")
    lines = [f"# `{cls}` — NOT READY / UNAPPROVED", "",
             "Diagnostic only: current ledger medians are not approved reference-consensus targets.",
             "Faction approval/calibration, weapon structure and maintainer sign-off remain required.", "",
             "## 1. The proposal", "", pool_note, "",
             "| axis | diagnostic candidate | ruled spec | evidence count | fit-eligible class percentile | contributing actors | basis |",
             "|---|--:|--:|--:|--:|---|---|"]
    for field in virtual.FIELDS:
        evidence = fields.get(field, {})
        preference = evidence.get("reference_preference",
                                  "applied" if evidence.get("reference_backed") else "none")
        basis = {"applied": "reference-backed ledger medians",
                 "vacated by missing stat":
                     "ledger medians / no reference-backed member has this stat; "
                     "using available selected-faction members",
                 }.get(preference, "ledger medians / no reference preference")
        if evidence.get("grid_step"):
            # The median and the snapped candidate differ whenever the pool is not
            # already on the grid; the reviewer must see which one they are reading.
            basis += f", snapped to step {evidence['grid_step']:g}"
        actors = ", ".join(str(actor) for actor in evidence.get("actors") or []) or None
        lines.append("| " + " | ".join(map(cell, [SPEC_KEYS[field], evidence.get("value"),
            (entry.get("spec") or {}).get(SPEC_KEYS[field]), evidence.get("count"), evidence.get("percentile"),
            actors, basis])) + " |")
    lines += ["", "Status: " + "; ".join(candidate["status"])]
    if candidate.get("no_source"):
        lines.append(f"NO SOURCE means {candidate['no_source']}.")
    lines += ["", "## 2. DPS is deferred", "",
              "No DPS target is proposed while W24 moves. No synthetic damage/reload is assumed; "
              "there is no combat verifier or fit command to approve from this dossier.", "",
              "## 3. Anchor and verifier actors", "",
              "| role / actor | source | HP | speed | ground-domain range | cost |",
              "|---|---|--:|--:|--:|--:|"]
    for role, snapshot in snapshots.items():
        for source in ("ledger", "live"):
            lines.append("| " + " | ".join(map(cell, [f"{role}: {snapshot['actor']}", source] +
                [snapshot[source].get(f) for f in virtual.FIELDS])) + " |")
        if snapshot["error"]:
            lines += ["", f"{role}: {snapshot['error']}"]
    anchor, verifier = snapshots["anchor"]["live"], snapshots["verifier"]["live"]
    ratios = {f: verifier.get(f) / anchor[f] if anchor.get(f) and verifier.get(f) is not None else None
              for f in virtual.FIELDS}
    lines += ["", "Verifier / anchor ratios (HP, speed, range, cost): " + " / ".join(cell(ratios[f]) for f in virtual.FIELDS),
              "", "| role | ledger nominal DPS/tick | measured tier factor | derived aggregate K | K fallbacks |",
              "|---|--:|--:|--:|--:|"]
    for role, snapshot in snapshots.items():
        metrics = snapshot.get("metrics", {})
        lines.append("| " + " | ".join(map(cell, [role] + [metrics.get(field) for field in
            ("nominal_dps_per_tick", "tech_tier", "aggregate_K", "K_fallbacks")])) + " |")
    for label, field in (("TechTier", "tech_tier"), ("aggregate K", "aggregate_K")):
        a, b = (snapshots[role].get("metrics", {}).get(field) for role in ("anchor", "verifier"))
        verdict = "unavailable" if a is None or b is None else (
            "equal" if math.isclose(a, b, rel_tol=1e-9) else "DIFFERENT — verifier identity not applicable")
        lines += ["", f"Shared {label}: {verdict}."]
    lines += ["", "The 2x HP / 2x DPS / 2.5x cost identity is NOT established by stat ratios alone. "
              "K is a derived aggregate, not a measured matchup result; any missing sidecar is unavailable. "
              "The synthetic verifier remains withheld.", "",
              "## 4. Membership", "",
              "Every classified member with its LIVE resolved-YAML stats as it ships today, sorted by live "
              "cost, unavailable last. The ledger-based diagnostic candidate in section 1 is NOT recalculated "
              "from these rows. REF means STRONG/FAIR assignment, not an approved faction or a completed "
              "consensus. FORMULA means no accepted assignment. Rows marked excluded fail fitting eligibility "
              "(buildable=False and no explicit balance_include); they are displayed but never added to the "
              "candidate calculation. Unresolved members stay unavailable with their issue, never a fallback "
              "labeled live.", "",
              "| actor | faction | evidence | HP | speed | range | cost | basis |",
              "|---|---|---|--:|--:|--:|--:|---|"]
    classified = sorted(list(members) + list(excluded_members),
        key=lambda m: (live_cost(m, live_by_actor) is None, live_cost(m, live_by_actor) or 0, m["actor"]))
    excluded_actors = {member["actor"] for member in excluded_members}
    for member in classified:
        row = live_row(member, live_by_actor)
        marks = []
        if member["actor"] in excluded_actors:
            marks.append("excluded from fit (buildable=False and no explicit balance_include)")
        if row.get("issue"):
            marks.append(f"live unavailable: {row['issue']}")
        lines.append("| " + " | ".join(map(cell, [member["actor"], member.get("faction"),
            "REF" if accepted_refs(member["actor"], assignments) else "FORMULA"] +
            [row["values"].get(f) for f in virtual.FIELDS] +
            ["; ".join(marks) or "live resolved YAML"])) + " |")
    lines += ["", f"Classified ledger rows excluded by fitting eligibility: {len(excluded_members)}.",
              "", "## 5. Reference consensus", "",
              "Read-only R4 sensitivity through reference_targets.target_for's with-Cameo result; "
              "n counts external sources, plus Cameo's additional equal vote. Source families keep one vote each. "
              "Hero actors use their separate frozen hero-only population; they never enter ordinary distributions. Raw cross-game stats are not averaged. These numbers do NOT replace the candidate or constitute calibration.", "",
              "| actor | exact source IDs used | HP target | speed target | range target | cost target | nominal damage/tick | issues |",
              "|---|---|--:|--:|--:|--:|--:|---|"]
    for member in members:
        actor = member["actor"]
        if not accepted_refs(actor, assignments) and not references[actor]["errors"]:
            continue
        evidence = references[actor]
        targets = [evidence["targets"].get(f, {}) for f in REFERENCE_KEYS]
        lines.append("| " + " | ".join(map(cell, [actor,
            "; ".join(f"{r['source']}/{r['id']}" for r in evidence["used"] + evidence.get("hero_references", []))] +
            [f"{cell(t.get('value'))} (n={t.get('sources', 0)})" for t in targets] +
            ["; ".join(evidence["errors"]) or "unapproved"])) + " |")
    lines += ["", "## 6. Disagreements and gates", "",
              "Anchor versus ruled spec (anchor actor only; the ruled spec is NOT applied to the verifier "
              "or to members):", "",
              "| axis | anchor live | ruled spec | signed gap | gap % |",
              "|---|--:|--:|--:|--:|"]
    for field in virtual.FIELDS:
        ruled = (entry.get("spec") or {}).get(SPEC_KEYS[field])
        signed, percent = gap_cells(snapshots["anchor"]["live"].get(field), ruled)
        lines.append("| " + " | ".join(map(cell, [field, snapshots["anchor"]["live"].get(field),
            ruled, signed, percent])) + " |")
    lines += ["", "Live resolved YAML versus the diagnostic candidate (unchanged, ledger-based):", "",
              "| actor / axis | ledger | resolved YAML | candidate | live / candidate gap |",
              "|---|--:|--:|--:|--:|"]
    for snapshot in snapshots.values():
        if not snapshot["actor"]:
            continue
        for field in virtual.FIELDS:
            target = fields.get(field, {}).get("value")
            live = snapshot["live"].get(field)
            gap = f"{100 * (live / target - 1):+.1f}%" if live is not None and target else "unavailable"
            lines.append("| " + " | ".join(map(cell, [f"{snapshot['actor']} / {field}",
                snapshot["ledger"].get(field), live, target, gap])) + " |")
    lines += ["", "Ledger versus live discrepancies for classified members (signed gaps, live minus "
              "ledger, and percentage gaps; "
              "the percentage needs a finite positive ledger baseline; differing or unavailable axes only):", "",
              "| actor / axis | ledger | live | signed gap | gap % |",
              "|---|--:|--:|--:|--:|"]
    for member in classified:
        row = live_row(member, live_by_actor)
        for field in virtual.FIELDS:
            ledger, live = member.get(field), row["values"].get(field)
            if ledger == live:
                continue
            signed, percent = gap_cells(live, ledger)
            if row.get("issue"):
                percent = f"{percent} — {row['issue']}"
            lines.append("| " + " | ".join(map(cell, [f"{member['actor']} / {field}",
                ledger, live, signed, percent])) + " |")
    lines += ["", f"W24: {'UNAVAILABLE — ' + gate_error if gate_error else str(len(debt)) + ' class members with stacked mains (raw, no exemptions)' }."]
    for actor, weapon, count in debt:
        lines.append(f"- `{actor}` / `{weapon}`: {count} mains")
    lines += ["", "A zero stacked-main count is not full weapon clearance. Pending class migrations are not "
              "silently applied; an empty class stays NO SOURCE. Limited actors need hero-lane evidence, "
              "not admission into ordinary distributions.", "",
              "## 7. What would make this wrong", "",
              "These candidates are wrong if the selected current-stat pool is unrepresentative, its reference "
              "assignments are rejected, or its ledger differs from resolved YAML; approval and calibration "
              "must resolve those questions before any number is applied.", "",
              "Evidence hashes (inputs, not approval):", "", "```json",
              json.dumps(provenance, sort_keys=True, indent=2), "```", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--class", dest="cls")
    mode.add_argument("--all", action="store_true")
    parser.add_argument("--out", type=pathlib.Path, default=ROOT / "docs/balance/anchors")
    parser.add_argument("--factions", nargs="+", help="Restrict dossier members and baseline pool to these ledger factions or aliases")
    args = parser.parse_args(argv)
    faction_scope = tuple(virtual.FACTION_ALIASES.get(f, f) for f in args.factions) if args.factions else None
    ledger = ROOT / "docs/balance"
    registry = (ledger / "class_anchors.json").read_bytes()
    anchors = json.loads(registry.decode("utf-8"))
    classes = sorted(k for k, v in anchors.items() if not k.startswith("_") and isinstance(v, dict))
    if any(not re.fullmatch(r"[a-z][a-z0-9_]*", cls) for cls in classes):
        parser.error("invalid class identifier in anchor registry")
    if args.cls and args.cls not in classes:
        parser.error(f"unknown class: {args.cls}")
    output = args.out.resolve()
    # The only in-repository write surface is the dedicated dossier directory.
    if args.all and output.is_relative_to(ROOT.resolve()) and output != (ledger / "anchors").resolve():
        parser.error("in-repository output must be docs/balance/anchors")
    members, assignments, provenance = virtual.load_evidence(ledger)
    if faction_scope and not set(faction_scope) <= {m["faction"] for m in members}:
        parser.error("unknown or empty faction in dossier scope")
    if provenance.get("ledger_sha256", {}).get("class_anchors.json") != hashlib.sha256(registry).hexdigest():
        parser.error("class_anchors.json changed between registry read and evidence collection; "
                     "no output written")
    input_provenance = dict(provenance)
    source_before = source_provenance(ROOT)
    provenance.update(source_before)
    selected = [args.cls] if args.cls else classes
    selected_members = [m for m in members if m["cls"] in selected
                        and (faction_scope is None or m["faction"] in faction_scope)]
    references = reference_evidence(selected_members, assignments)
    all_rows = readiness.load_units()
    records = {actor: (section, rec) for _, section, actor, rec in all_rows}
    sidecars = {}
    for faction in {faction for faction, _, _, _ in all_rows}:
        path = ledger / "derived" / f"{faction}.json"
        if path.exists():
            doc = json.loads(path.read_text(encoding="utf-8"))
            for section in doc.get("sections", {}).values():
                sidecars.update(section)
    units = {actor: rec for actor, (_, rec) in records.items()}
    gate, gate_error = readiness.three_way_split_gate(units,
        {actor: readiness.class_membership.classify(rec.get("design") or {})[0]
         for actor, rec in units.items()})
    rules = miniyaml.Ruleset(ROOT)
    results = {}
    live_cache = {}
    factions = {actor: faction for faction, _, actor, _ in all_rows}
    for cls in selected:
        entry = anchors[cls]
        candidate = virtual.derive(cls, members, assignments, factions=faction_scope or virtual.DEFAULT_FACTIONS)
        snapshots = {role: actor_snapshot(entry.get(role + "_actor"), records, rules, sidecars, live_cache)
                     for role in ("anchor", "verifier")}
        cls_members = [m for m in selected_members if m["cls"] == cls]
        excluded = [dict(actor=actor, faction=factions.get(actor), **virtual.stat_values(unit))
                    for actor, unit in units.items()
                    if readiness.class_membership.classify(unit.get("design") or {})[0] == cls
                    and not fit_class.eligible_virtual_member(unit)
                    and (faction_scope is None or factions.get(actor) in faction_scope)]
        live_by_actor = {member["actor"]: member_live(member["actor"], records, rules, live_cache)
                         for member in cls_members + excluded}
        results[cls] = render(cls, entry, candidate, cls_members,
            assignments, references, snapshots, gate[0].get(cls, []) if gate else [], gate_error, provenance,
            excluded_members=excluded, live_by_actor=live_by_actor)
    if virtual.input_fingerprints(ledger) != input_provenance or source_provenance(ROOT) != source_before:
        parser.error("input evidence changed during dossier generation; no output written")
    if args.all:
        paths = {output / f"{cls}.md": text for cls, text in results.items()}
        try:
            diagnostic_output.write_outputs(ROOT, paths)
        except (OSError, ValueError) as exc:
            parser.error(str(exc))
        print(f"Wrote {len(paths)} unapproved diagnostic dossiers to {output}")
    else:
        print(results[args.cls], end="")
    return 1 if gate_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
