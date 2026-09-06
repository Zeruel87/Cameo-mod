# Reference extraction & faction mapping — the plan

**Owner: Claude-Local.** Lane: `tools/reference/**`,
`tools/balance/{assign_references,faction_routes,faction_extrapolate}.py`, `docs/balance/review/**`,
`docs/reference/**`. No other agent should edit these while this runs.

This is the build order for turning the reference corpus into per-class targets. It supersedes
nothing — it *implements* `REFERENCE_METHOD.md` and the maintainer rulings of 2026-09-05 recorded
in §0 below.

---

## §0 — Maintainer rulings, 2026-09-05. Do not re-litigate these.

| # | ruling |
|---|---|
| R1 | **Class anchors become VIRTUAL.** No class is anchored to a real actor any more. An anchor is a pure number at the **100% point of the price band** (the band is `FORMULA_V2.md` §3's 50–250% envelope of `C₀`). |
| R2 | **The verifier goes virtual too**, and is replaced by a stronger check: a new audit resolves **every** unit in a class through `miniyaml` and asserts the formula reproduces its price. This is strictly stronger than the single 2.5×`C₀` tripwire unit it replaces. |
| R3 | **Faction mapping is a unique SET, members may repeat.** No two Cameo factions share the same combination, but one reference faction may appear in several combinations. The existing law that a reference *unit* is spent once is unchanged. |
| R4 | **Equal thirds, and current Cameo yaml is always one of the voices** — `Cameo TD GDI = DTA GDI × Combined Arms GDI × current Cameo TD GDI`, each 1/3, synthesised by geometric mean. |
| R5 | **Faction profiles are computed per TYPE and overall** — infantry, vehicle, aircraft, naval, defense, and everything-combined — each compared against **the same group in the faction's own source game**, and each reported as an **independent separate value**. Geometric mean. |
| R6 | **Collect every stat we can get.** Some will turn out to be junk; that is a later triage, not a reason to narrow the extraction now. |
| R7 | **Variance is reported three ways**: coefficient of variation, min/max spread, and percentile position of the faction's mean within its own game. |
| R8 | **Armor extrapolation: interpolate between the peer's OWN declared rungs.** Every value a peer actually declares is a fixed anchor on its ladder; rungs between two anchors are interpolated; beyond the outermost anchor the value is held flat. A peer that declares only ONE rung on a ladder votes flat and is **downgraded to low confidence**. ⛔ Never distribute using Cameo's own §12.0i curve — that would make the "independent" reference partly a measurement of ourselves. |
| R9 | **Derived corpus is committed under `docs/reference/`; raw game data stays outside the repo** in `Cameo-mod-reference/`. |
| R10 | **Sequencing: the C&C family is built FIRST** — TD, RA1, TS, RA2 and the RA2-modded factions, from the references we have. Warcraft, StarCraft and Dune factions come later, each from **their own** reference pool (StarCraft mods, WC2 mods, Emperor: Battle for Dune, Spice Wars, the custom D2k mods). Measured and safe: of the **22 classes in use, ZERO are deferred-only** — every class a Warcraft/StarCraft/Dune unit sits in also has C&C members, and C&C members dominate all 16 mixed classes (`mbt` 33:8, `support` 30:4, `fire_support` 26:4). Deferred factions keep global-formula pricing meanwhile; waiting does not make them more wrong. ⛔ **The protection this depends on: anchor values are FROZEN design numbers. Re-fitting an anchor is an explicit maintainer act and must NEVER happen as a side effect of adding a reference source** — a re-fit moves every already-balanced faction underneath itself. ⚠ `archer` (2 C&C members) and `heavy_infantry` (1) are too thin to anchor on C&C evidence alone; leave them formula-only until their own references land. |
| R11 | **Cameo 1.0 release gate: EVERY faction must be written with the new balance formula, and EVERY faction must have reference data to choose from.** No faction ships 1.0 on formula-only pricing. The per-reference-faction calculated values are what populate each unit class relative to the baseline — so a faction with no reference has nothing to position against. This makes the deferred reference sources (Emperor, Spice Wars, StarCraft, WC2, the custom D2k mods) **release-blocking for 1.0**, not optional enrichment. |
| R12 | **DTA Enhanced represents DTA; Classic is a superseded lineage member.** They are one roster — Enhanced is Classic plus `Enhance.ini` — and measured 80–92% identical on the 863 shared ids with a median ratio of exactly 1.000. Enhanced is elected on the game's own default (`Items=Classic,Enhanced`, `DefaultIndex=1`). ⚠ Not a no-op: `td_gdi`, `td_nod`, `ra1_allies` and `ra1_soviets` move onto the overlay's ~10–20% rebalanced rows. |
| R13 | **Rise of the East is exclusive-only**, like Mental Omega and CnC Reloaded. Its 36% `asianalliance`/`tkm` overlap was inside the honest C&C band, so this is a cheap improvement rather than a rot fix: RotE has large per-country pools, so exclusivity costs ~4 rows a faction and takes the overlap to **0%**. |
| R14 | **The universal-pool carve-out.** A unit owned by EVERY routed country of its source is either shared infrastructure or a universal COMBAT unit; the mobile ones are readmitted, the structures are not. Found by asking what R13 actually removed: not harvesters — Rise of the East's Soviet Mammoth Tank, Asian Emperor Overlord Tank, Allied Juggernaut and Yuri Specter Squad, i.e. the top of the HP and cost range. ⚠ "Universal" means ALL routed countries; owned by SOME is the case the partition exists for and stays removed (Mental Omega's 61-unit non-Foehn pool; CnC Reloaded's Core Defender, 19 of 21 countries but not Nod). Overlap among the five CnCR-fed factions is 16–23%, against 81% before any exclusivity. |
| R15 | **A source's own NAMING beats a permissive `Owner=`, and a name claim is EXCLUSIVE.** CnC Reloaded ships a complete CABAL faction — 55 units named `CABAL's ...` plus the Core Defender pair, every one owned by `RobotCountry` — but gives 43 of them to all 21 countries, so ownership alone would discard the faction. A modder writes "CABAL's Refinery" on purpose and copies an `Owner=` line out of habit. A claimed unit goes to its claimant and to **nobody else**: CABAL's Cyborg Commando stops being a reference for `ra2_allies` and `ts_gdi`. `cabal` is routed to CnCR RobotCountry and goes **44 → 156 rows**, clearing the two-source floor it was the only routed faction to fail. ⛔ I had recorded that CnCR shipped no CABAL faction; that came from sampling DEVOUT and ASCENDED, seeing all-21 ownership, and generalising from two units. |

---

## §1 — What we are extracting from

**Two families of source, and they need different extractors.**

**A. INI mods** (Ares/Westwood engines) — already extracted, in
`Cameo-mod-reference/extraction/`, 8183 unit rows:

| source | units | costed | armor rows |
|---|--:|--:|--:|
| Rise of the East 3.0.0c | 2445 | 1666 | — |
| RA2 0XX 1.0.8 | 2104 | 486 | 684 |
| Mental Omega 3.3.6 | 1706 | 786 | — |
| CnC Reloaded 2.7.0 | 1306 | 816 | 355 |
| Red Resurrection 2213 | 1048 | 491 | 480 |
| DTA (Classic + Enhanced overlay) | 869 + 112 | 417 + 85 | `Modifier.*` |
| RA2 Reborn 1.0.31 | 697 | 366 | 176 |

**B. OpenRA peer mods** — 16 declared in `tools/reference/extract_peer_units.py:PEERS`:
`ca` (Combined Arms), `cn` (Crystallized Nexus), `sp` (Shattered Paradise), `rv` (Romanov's
Vengeance), `hv` (Hard Vacuum / OpenHV), `e2140` (OpenE2140), `gen` (Generals Alpha), `fnw`,
`ra2vsh` (Valiant Shades), plus the upstream `ra`, `ra2`, `yr`, `ts`, `cnc`, `d2`, `d2k`.

✅ **A1/A2 DONE 2026-09-05** — `extract_peer_units.py` now runs. **9 of 16 peers resolve, 1946 units**:
Combined Arms 382, Romanov's Vengeance 729, Shattered Paradise 306, Generals Alpha 153,
Crystallized Nexus 97, OpenRA TD 56, RA 94, TS 73, D2k 56 — the last four from the
`cameo-engine` clone, which already ships `mods/{cnc,ra,ts,d2k}`.

⏳ Still missing 7, ranked by the armor map's own assessment: **Valiant Shades** (AS-lineage,
highest confidence, tied with RV), **OpenHV**, **OpenE2140**, OpenRA RA2, Yuri's Revenge on
OpenRA, Fractured Realms, Dune II (declares NO `Versus` — unit stats only). Non-blocking.

---

## §2 — The build order

### Phase A — extraction

| # | task | notes |
|---|---|---|
| **A1** | ✅ DONE — **Port `mod_id` into `tools/audit/miniyaml.py`** | ⛔ BLOCKER. `Ruleset.__init__` takes one arg; `extract_peer_units.py` calls it with two. The change exists on `origin/claude/docs-audit-reorganize-xgzwhr` (27 insertions, `mod_id: str = "cameo"` default, so every existing caller is unaffected). Devin landed the tooling without it. |
| **A2** | ✅ DONE — Resolve all 16 peers on disk; report which are missing | `--dry-run`. A missing root is skipped near-silently — read every line. |
| **A3** | ✅ DONE — INI extractor → the same schema as the OpenRA extractor | RA2/YR 11-slot `Verses=`, TS 5-slot, DTA `Modifier.*`. |
| **A4** | ✅ DONE — Every stat, both families (R6) | core (HP/cost/speed/range/DPS/armor) + build/economy + combat detail + vision/utility. |
| **A5** | ✅ DONE — Every `Versus` / `Verses` / `Modifier.*` row | ⚠ In OpenRA yaml `Versus` is a **node with an EMPTY value whose children are the rows**. `node.get("Versus")` returns empty and yields the false result "0 peers expose Versus". Use `weapon_efficiency.versus_of`. |
| **A6** | ✅ DONE — Armor normalisation per R8 | onto the four ladders in `docs/reference/peer_armor_map.yaml`; confidence gates voting; only `high`/`medium` vote. |
| **A7** | ✅ DONE — Convert the two UTF-16 reference files to UTF-8 | `PEER_ARMOR_VOCABULARIES.md`, `peer_armor_map.yaml` — PowerShell `>` wrote them; every grep silently under-reads them. |

### Phase B — statistics (R5, R7)

| # | task |
|---|---|
| **B1** | ✅ DONE — Per-source, per-faction rosters, split by type: infantry / vehicle / aircraft / naval / defense |
| **B2** | ✅ DONE — Faction "average actor": geometric mean per type **and** overall |
| **B3** | ✅ DONE — The same aggregate for the **whole source game**, per type — the comparison group |
| **B4** | ✅ DONE — Faction profile = B2 ÷ B3, per type and overall, each an independent value |
| **B5** | ✅ DONE — Variance: CV, min/max spread, percentile position — faction vs its own game |

### Phase C — the mapping matrix

| # | task |
|---|---|
| **C1** | ✅ DONE — For each of the 29 real Cameo factions, assign its reference combination (R3, R4) |
| **C2** | ✅ DONE — Record it as reviewable data next to `faction_routes.py`, with the reason per pairing |
| **C3** | ✅ DONE — Verify every Cameo faction reaches the ≥2-reference floor, or is explicitly `UNROUTED` (formula-only) |

### Phase A/B/C — CLOSED 2026-09-06 by wiring the corpus into the distribution layer

`ini_corpus.json` existed from 2026-09-05 but nothing READ it: `reference_distribution.peer_rows()`
parsed two markdown documents only, so `faction_routes.py --check` reported all fifteen INI routes
as *"source not in the de-duplicated corpus"* and `allows()` admitted zero rows for them. The
loader is `reference_distribution.ini_rows()`. Corpus **2,568 -> 4,523 peer rows, 15 -> 21 sources**;
Cameo actors with a reference signature **324 -> 374**.

Four things that had to be settled to land it, each measured rather than assumed:

| what | finding |
|---|---|
| **DOC1 vs the extraction** | `ORIGINAL_UNITS_RAW.md`'s hand-typed Mental Omega / CnC Reloaded tables are the same data, less of it, with typos: median HP ratio 1.000 but MO's Lionheart Bomber reads 10,000 HP against `[LIONH] Strength=800`. DOC1 now stands down per source, automatically, for anything the extractor covers — it currently supplies **zero** rows. The one signature lost (`terran_ghost`) matched an MO row for a unit MO does not have. |
| **`cost > 0` is not a buildability test** | these mods price internal dummies at 1 credit. CnC Reloaded's `TSCARRYALL_DUMMY` is a costed **10,000,000 HP** row against a real ceiling of 6,000. `TechLevel = -1` + `Selectable/IsSelectableCombatant = no` are the engine's own flags and fix every tail (RotE 15,000 -> 2,000, RA2 0XX 9,999 -> 3,000). They also drop the elite/upgraded DUPLICATE actors these mods ship, which were double-counting their own base unit. |
| **route tokens were never case-folded** | `peer_factions()` lowercases the corpus; the INI routes are written in each source's own casing. All fifteen matched nothing while `--check` printed the token it wanted next to the same token, lowercased, in the same line. |
| **"exclusive" means different things per source** | CnC Reloaded has real per-faction pools (nod 86, gdi 61, soviet 42, allies 41, yuri 32). **Mental Omega has almost none — 3 to 7 per country** — because it models four SIDES; country exclusivity cut `japan` to 6 units. Exclusivity is now a declared PARTITION per source, and `faction_routes` and `faction_profile` share one copy of it. Worst Cameo-faction roster overlap **97% -> 49%**. |

### Phase D — virtual anchors (R1, R2)

| # | task |
|---|---|
| **D1** | Migrate `docs/balance/class_anchors.json`: drop `anchor_actor` / `verifier_actor`, keep `spec` as the definition at 100% of the band |
| **D2** | Write the resolver-check audit: resolve **every** unit in a class, assert the formula reproduces its price |
| **D3** | Update `FORMULA_V2.md` §2 — it currently rules that every class has a *living baseline unit in game*, which R1 replaces |

---

## §3 — Traps already paid for. Do not rediscover these.

1. **`git grep` skips several of our weapons yaml as binary** (non-UTF-8 bytes), and **`miniyaml`
   silently under-parses the same files.** For any presence check use
   `git show <rev>:<file> | grep -a`. This nearly deleted 30 live weapon nodes.
2. **A mod's loose `rulesmd.ini` can be vanilla Yuri's Revenge byte-for-byte** — Mental Omega's is
   (md5 `cf7eb658327aff1fe7e6c4e7400eb87f`). Check every extraction against that hash.
3. **`extract_mix_ini.py` sniffs only the first 4096 bytes**, so a rules file with a comment banner
   reports "0 INI blobs found". Judge blobs by full content.
4. **`Versus` is an empty-valued node** — see A5.
5. **A claim about the corpus is not a claim about the world.** "MO and CnC Reloaded are not
   recoverable" was recorded as fact in `REFERENCE_PIPELINE_HANDOFF.md` §1.3; both were on disk.
