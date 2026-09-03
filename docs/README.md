# Cameo documentation — the map

**Picking up work? Start at [`HANDOFF.md`](HANDOFF.md).** Everything else is reference.

This file is the **sole reading-order definition** and the map of which document owns which
topic. If two documents disagree, the precedence below decides; fix the loser, never both.

**Above all of it: the artifact.** A document is a claim about the tree; the tree is the tree.
When they disagree, run the tool, then fix the document.

---

## The whole live set

Everything else under `docs/` is either **generated** (regenerate it, never hand-edit) or
**archived** in `history/` (what happened, never what is true now).

### Start here — 5 documents, read in this order

| # | document | what it is |
|---|---|---|
| 1 | [`../CLAUDE.md`](../CLAUDE.md) | the hard rules, loaded every session. Top authority. |
| 2 | [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md) | every trap someone already paid for |
| 3 | [`AGENT_WORKSPACE.md`](AGENT_WORKSPACE.md) | workflow, evidence rules, commit gate |
| 4 | [`HANDOFF.md`](HANDOFF.md) | **the entry point** — verified state + the priority queue |
| 5 | [`DESIGN.md`](DESIGN.md) | the binding contract. Read the sections your change touches. |

Then [`design/ROADMAP.md`](design/ROADMAP.md) (the granular queue) and
[`audit/SUMMARY.md`](audit/SUMMARY.md) (current bug counts).

`.windsurf/rules/start-protocol.md` and the `SessionStart` hook
(`tools/hooks/session_checklist.py`) enforce this order at the IDE and CLI level. If either
conflicts with this file, **this file wins** — and fix the copy.

Crashes and player-visible regressions always jump the queue.

### The balance program — 8 documents

| document | owns |
|---|---|
| [`design/BALANCE_PROGRAM_PLAN.md`](design/BALANCE_PROGRAM_PLAN.md) | **the board**: W1-W26, file-set ownership (§2), the binding order of operations (§0a), and the A-G phase map (§7) |
| [`design/BALANCE_PIPELINE.md`](design/BALANCE_PIPELINE.md) | the machinery: ledger to workbook to gated apply, and drift |
| [`design/FORMULA_V2.md`](design/FORMULA_V2.md) | the formula law: per-class, SUM, bands, uniqueness |
| [`design/BALANCE_SYNTHESIS.md`](design/BALANCE_SYNTHESIS.md) | the mod-synthesis methodology and its sources |
| [`design/BALANCE_PIPELINE_ESTIMATE.md`](design/BALANCE_PIPELINE_ESTIMATE.md) | effort estimate for the whole programme |
| [`design/BALANCE_PIPELINE_GAPS.md`](design/BALANCE_PIPELINE_GAPS.md) | what a one-click run still lacks, plus the verified residue of the 2026-08 outside review round |
| [`design/RTS_BALANCE_REFERENCE.md`](design/RTS_BALANCE_REFERENCE.md) | *(non-binding)* RTS and multiplayer balance dimensions a stat-consistency model cannot see |
| [`design/EFFECTIVE_DAMAGE.md`](design/EFFECTIVE_DAMAGE.md) | the area-integrated `effective_damage` metric |

### Weapons, warheads and defence — 9 documents

| document | owns |
|---|---|
| [`design/ARMOR_SYSTEM.md`](design/ARMOR_SYSTEM.md) | how a weapon's `Versus` table is CONSTRUCTED (the law) |
| [`design/ARMOR_LAYERS.md`](design/ARMOR_LAYERS.md) | the whole defence stack: shields, Integrity, plating, superweapon layering — the measured analysis behind DESIGN §12.0c-g |
| [`design/WEAPON_3WAY_SPLIT.md`](design/WEAPON_3WAY_SPLIT.md) | the warhead / projectile / effect split |
| [`design/WEAPON_TYPE_SYSTEM.md`](design/WEAPON_TYPE_SYSTEM.md) | weapon type classification |
| [`design/PROJECTILE_AND_EFFECT_LAYER.md`](design/PROJECTILE_AND_EFFECT_LAYER.md) | the two lower layers: templates, per-game sourcing, game-specific bases |
| [`design/AREADAMAGE_WARHEAD.md`](design/AREADAMAGE_WARHEAD.md) | the AreaDamage warhead — design, rebalance, unified node |
| [`design/WEAPON_HEAVINESS.md`](design/WEAPON_HEAVINESS.md) | the continuous heaviness scale and its research |
| [`design/SPREAD_FALLOFF_PLAN.md`](design/SPREAD_FALLOFF_PLAN.md) | per-type spread and damage-falloff profiles |
| [`design/INVENTED_WARHEAD_FAMILIES.md`](design/INVENTED_WARHEAD_FAMILIES.md) | *(generated)* the families with no cross-mod equivalent |

### Systems — 4 documents

| document | owns |
|---|---|
| [`design/PHYSICAL_STATE_SYSTEM.md`](design/PHYSICAL_STATE_SYSTEM.md) | the status-meter layer: heat, cryo, corrosion, EMP, sonic |
| [`design/EMP_INTEGRITY_SYSTEM.md`](design/EMP_INTEGRITY_SYSTEM.md) | EMP / Integrity auto-scaling |
| [`design/UPSTREAM_MODS.md`](design/UPSTREAM_MODS.md) | absorbing the other OpenRA mods — CA, Crystallized Nexus, Romanov's Vengeance, Shattered Paradise: the engine lineage, why the engine must NOT move to `ca-engine`, and the phased adoption plan |
| [`design/AI_ARCHITECTURE.md`](design/AI_ARCHITECTURE.md) | bot modules, per-ContentPack AI splitting, the dynamic personality manager, the master AI module, and the match-logging / offline-learning loop |

### Factions and content — 5 documents

| document | owns |
|---|---|
| [`FACTIONS.md`](FACTIONS.md) | the curated faction compendium: lore, playstyle, scoring |
| [`design/FACTION_IDENTITY.md`](design/FACTION_IDENTITY.md) | faction BALANCE bias — how units differ within a class |
| [`MIGRATION.md`](MIGRATION.md) | the ContentPack migration runbook |
| [`design/ORIGINAL_UNIT_STATS.md`](design/ORIGINAL_UNIT_STATS.md) | source-game unit stats — the relative-balance ground truth |
| [`design/ORIGINAL_UNITS_RAW.md`](design/ORIGINAL_UNITS_RAW.md) | *(generated)* every source unit, raw, in Cameo naming |

### Audit and evidence — 5 documents

| document | owns |
|---|---|
| [`audit/SUMMARY.md`](audit/SUMMARY.md) | current known-issue state by bug class |
| [`audit/doc_claims.yaml`](audit/doc_claims.yaml) | every number a DECISION rests on, with its re-measure command |
| [`audit/PERIODIC.md`](audit/PERIODIC.md) + [`audit/periodic.json`](audit/periodic.json) | recurring code-health audits and their cadence |
| [`audit/CONSISTENCY_REPORT.md`](audit/CONSISTENCY_REPORT.md) | verified on every run by `audit_consistency_report.py` — do not move it |
| [`audit/INCIDENT_TD_GDI_RELEASE_REGRESSION.md`](audit/INCIDENT_TD_GDI_RELEASE_REGRESSION.md) | a worked incident, kept as the template for the next one |

### Reference and notes — 6 documents

| document | owns |
|---|---|
| [`Cameo_Knowledge_Base_Manual.md`](Cameo_Knowledge_Base_Manual.md) | the engine / custom-trait / C# reference |
| [`reference/WARHEAD_REFERENCE.md`](reference/WARHEAD_REFERENCE.md) | *(measured)* the corpus: family profiles, versus archetypes, archetype tables |
| [`balance/anchor_decisions_log.md`](balance/anchor_decisions_log.md) | class-anchor decisions — maintainer-confirmed baselines + verifiers |
| [`balance/formula_v2_classes.md`](balance/formula_v2_classes.md) | per-class formula working logs |
| [`design/DECISIONS.md`](design/DECISIONS.md) | small settled decisions scoped to one system |
| [`design/RESEARCH_NOTES.md`](design/RESEARCH_NOTES.md) | source-game and mod research. Binds nothing. |

Plus [`design/VISION.md`](design/VISION.md) (north-star product intent, explicitly not a queue),
[`design/upgrades_intent.yaml`](design/upgrades_intent.yaml) (the upgrade intent registry),
[`balance/discrepancies.md`](balance/discrepancies.md) and
[`balance/README.md`](balance/README.md) (what the ledger is).

---

## Precedence (highest wins)

1. **[`../CLAUDE.md`](../CLAUDE.md)** — project instructions, loaded every session.
2. **Binding law** — [`DESIGN.md`](DESIGN.md), [`design/FORMULA_V2.md`](design/FORMULA_V2.md), [`design/ARMOR_SYSTEM.md`](design/ARMOR_SYSTEM.md), [`design/BALANCE_PIPELINE.md`](design/BALANCE_PIPELINE.md).
3. **Current state and queue** — [`HANDOFF.md`](HANDOFF.md), [`design/BALANCE_PROGRAM_PLAN.md`](design/BALANCE_PROGRAM_PLAN.md), [`design/ROADMAP.md`](design/ROADMAP.md).
4. **Reference and analysis** — everything else above.
5. **[`history/`](history/)** — archived. Never overrides anything current.

---

## Generated — do NOT hand-edit

| what | regenerate with |
|---|---|
| [`audit/latest/`](audit/latest/) — the current evidence set | `bash tools/audit/run_all.sh` |
| `balance/*.json` — the ledgers, source of truth for numbers | `python tools/balance/extract_stats.py` |
| `balance/derived/*.json` — derived sidecars | same |
| per-class rebalance proposals | `python tools/balance/propose_class_rebalance.py --class <name>` |
| [`factions/MATRIX.md`](factions/MATRIX.md) | `python tools/audit/gen_faction_matrix.py` |
| `balance/class_anchors.json` | maintained via `balance/anchor_decisions_log.md` |
| [`design/INVENTED_WARHEAD_FAMILIES.md`](design/INVENTED_WARHEAD_FAMILIES.md) + its json | `python tools/balance/design_invented_profiles.py --write` |
| [`audit/baseline/`](audit/baseline/) | historical snapshots — comparison only |

⚠ **`bash` only** for `run_all.sh` — a PowerShell `>` redirect writes UTF-16 and corrupts every
report (CLAUDE.md rule 8). `tools/audit/run_all.py` is a port for shells without `sh`; it reads
its audit list out of `run_all.sh`, so the two cannot drift apart.

⚠ **`audit/latest/` can only be regenerated from a COMPLETE tree** — one with `engine/` built and
a full (non-shallow) clone. Without them a dozen audits scan a smaller corpus, report fewer
findings and still say PASS, so a regenerate silently deletes real evidence
(`dead_warhead_fields` 27071 warhead nodes → 7014). Both runners now check first and divert to the untracked
`docs/audit/degraded/` instead, printing why; `--force-latest` overrides. Details and the
measured table: [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md). Refresh `latest/` **whole, from one
machine** — path separators alone make a cross-platform diff dirty.

⚠ **Do not drop a one-off artifact into `audit/latest/`.** That directory is regenerated
wholesale, so anything the suite does not produce is deleted on the next run — which is how
`latest/superweapon_audit.yaml` disappeared while three documents still linked to it.

⚠ **The active generated workbooks are TRACKED in git:**
`design/cameo_balance_by_faction.xlsx` and `design/cameo_balance_by_type.xlsx`.
`design/cameo_balance_v2.xlsx` is a frozen pre-split prototype; do not treat its
old formulas as the current balance law.

## Two gates keep this set honest

| audit | catches |
|---|---|
| `audit_doc_claims.py` | a NUMBER in prose that no longer matches the tree |
| `audit_doc_health.py` | control characters, mojibake, broken links and anchors, references to moved documents, duplicate DESIGN section ids, a `## Contents` index that has gone stale, and a citation that names one law while pointing at another |

Neither can check **prose contradicting prose** — a ruling written into one document while the
older statement still stands in another. The only defence is the discipline: **grep for the old
claim before you write the new one, and strike it everywhere it appears.**

## Things you cannot resolve from this repository

- **`memory <name>` citations** point at an external, per-agent memory store. **Provenance only, never authority.** Anything binding must be promoted into `DESIGN.md`.
- **Commit hashes older than 2026-08-10** do not resolve in a shallow checkout (cloud/CI). Run `git fetch --unshallow`, or verify against the artifact instead.
- **`engine/`** is `.gitignore`d and not part of this repository. See [`HANDOFF.md`](HANDOFF.md) §5.

## `history/` — archived, non-authoritative

Dated session logs, superseded handoffs, closed roadmap sections, finished programmes and
generated reports whose programme is over. They record *what happened*, never *what is true
now*. Anything still relevant was promoted into the live set above.

[`../DEVELOPMENT_LOG.md`](../DEVELOPMENT_LOG.md) (repo root) is the append-only multi-agent
development log — historical, but still actively appended to.
