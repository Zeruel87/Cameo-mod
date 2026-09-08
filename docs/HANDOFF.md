# Cameo — THE HANDOFF

## ⛔⛔ 2026-09-07 — READ THIS FIRST: the reference map, and one absolute rule

**SUPERWEAPONS ARE NEVER PRICED, RESTATTED OR TOUCHED** (maintainer, verbatim: *"NEVER CHANGE
THEM!! SO EXCLUDE THEM BEFORE ANYTHING IS CHANGED ON ACCIDENT!!!"*). 32 actors are gated on
`~techlevel.superweapons`; every one whose HP is recorded holds exactly **1,000,000**, which is a
deliberate constant, not a balance figure. Two locks, both landed in `9ad611a6d`:
`reference_distribution.cameo_rows()` drops them from the priced population, and `apply_balance`
**refuses** any ledger edit that touches one. Do not weaken either.

### Where the reference map stands (master `8589e8eb8`)

The maintainer reviewed it three times and rejected it twice. Every reference is now
**name-backed** — shape-only matches are refused outright, after a sniper drew a Velociraptor and
an officer a Triceratops. 63 originals · 77 expanded · 235 references · 4 originals still short.

**The one lesson that generalises**, stated three ways because it recurred every single time:

> The matcher was never choosing badly. **The correct candidate was invisible, or the wrong one
> was recorded despite the scorer already knowing it was bad.** Of ten mappings the maintainer
> called junk: 8 SHAPE, 2 WEAK, **zero STRONG**. Of the ones they called correct: 20 STRONG of 21.
> When a mapping looks stupid, ask what was excluded — not what was chosen.

Defects fixed today, each worth knowing because each was invisible:

| | |
|---|---|
| Armed structures in a `buildings` section were not in the population at all | 38 actors, incl. every TD defence |
| AI-only variants were eligible references (suffix **and** prefix forms) | 122 rows; they are deliberately CHEAPER |
| `~disabled` rows were eligible | OpenRA's dinosaurs, ants, Visceroid — and its `HIND` |
| A direct `Queue:` gate was diluted by a shared prerequisite (`anyhq`) | 15 TD rows incl. Light/Medium Tank |
| An EXPANSION outbid an ORIGINAL for its own reference | `firerocketsoldier` scores **0.867** vs `sovietrocketsoldier`'s **0.850** — the expansion is literally the closer string, so no scorer tuning fixes it. Originals now claim first. |
| `variant_rank` was a whack-a-mole list — held "flame", not "fire" | inverted: a closed list of FACTION words, not an open list of variant words |
| Containment guard measured the Cameo string, not the peer's | `Ant` matched inside `dragunov**ant**imaterialsniper` |
| Sources agree on IDS after renaming, and nothing read it | CA ships `1TNK` as "Scout Tank"; DTA prefixes RA-era actors `RA` (`RAPBOX`) |
| CA states ownership in a DOT SUFFIX (`STNK.Nod`) | its Queue/Prereq tags are useless — see below |
| The report hid variant FAMILIES | a 6-row mapping displayed as one arbitrary pick |

### ⛔ THE BIGGEST REMAINING LEVER — Combined Arms over-tagging

**CA's median row is admissible to FIVE Cameo factions. Every other source's median is ONE**, and
154 of 346 CA rows exceed six. That single fact produced most of what was rejected in both
reviews: a Soviet Tesla Trooper for Nod's laser trooper, Nod's SAM for the Soviet SAM site, an RA1
Allied IFV for a GDI APC, and `allows("td_gdi", TITN)` returning **False** — CA denying GDI its own
walker. **EMBER owns this.** Until it is fixed, `REFERENCE_OVERRIDES` and `FAMILY_EXTRA` in
`tools/balance/` are papering over it with named rows.

### ⭐ 2026-09-08 — the fleet stopped writing and started landing

`docs/FLEET_ORDERS_2026-09-08.md` is the live fleet order set; Codex/Astra's is
`docs/BLACKROBE_ASTRA_ORDERS_2026-09-07.md` (read its §13 addendum first).

The measurement that drove it: **39 unmerged agent branches, ~200 unmerged commits, and zero
merged to master by the fleet.** Four branches were byte-identical duplicates; two agents wrote
competing proposals for the same 268 units and neither shipped.

Landed today, both boot-gated:

| | |
|---|---|
| `devin/ember/w24-lane1` | 22 weapons collapsed to one main |
| `devin/dawn/w24-lane3` | 69 more, ledgers re-extracted on landing |
| **`audit_three_way_split`** | **322 → 231** |

⚠ Lane 3 arrived having changed 10 weapon files and no ledgers, so `audit_balance_drift` went red
across 10 of them. Fixed by `extract_stats.py`, never by hand. **Yaml and ledger in the SAME
commit** is now a standing fleet rule.

Next in the W24 queue: `devin/nova/w24-lane2` (57 commits, conflicts in
`RedAlert2/Soviets/weapons.yaml` — a real per-weapon decision, not a merge tool), then
`devin/nova/w24-naxi-pilot`, which must follow it.

### ✅ CLOSED — THE ANTI-AIR CONVENTION. Ruled by the maintainer 2026-09-08.

**The law is now in `docs/DESIGN.md` ("The AA range law", which REPLACES the dual-weapon AA law of
2026-07-11). Read it there — this is a pointer, not a second copy.** In summary:

1. **Three classes only** may carry an AA armament longer-ranged than its ground twin —
   `scout_vehicle`, `armed_troop_transport`, `anti_air_vehicle` — at **1.5×**. `anti_air_vehicle`
   SURVIVES; it is the only vehicle template carrying `AutoTargetPriority@AIR` (defaults.yaml:1829),
   and that, not the range, is its mechanical identity.
2. **Every other class uses one range for both domains.** The maintainer's Mammoth instinct was
   already shipped: every mammoth's cannon and missile pod share a range (6412/6412, 6141/6141,
   6340/6340); no `high_tech_tank` gets the bonus.
3. **`mobile_bunker` is a new (29th) class**, populated by all 16 buildable actors with a resolved
   `AttackOpenTopped`, and it may carry **no air-capable armament at all** — its anti-air is the
   infantry riding inside. Ten of the sixteen are the former `line_breaker` Battle-Fortress family;
   the 22 that stay `line_breaker` are flame tanks, disruptors and brawlers.
4. The 1.5× is **generated** by `gen_weapon_template.py` (`AA_RANGE_MULT`), never hand-typed, and
   enforced by `audit_aa_range.py` as a **LOWER-ONLY ratchet**.

⛔ **AND THE ENGINE ANSWER, so nobody re-derives it.** The maintainer asked whether one weapon could
serve both domains with an air-only range multiplier on the template. **It cannot, mod-side.**
`Armament.MaxRange()` (Armament.cs:215) takes no target; `IRangeModifier.GetRangeModifier()`
(TraitsInterfaces.cs:480) takes no target; `RangeMultiplier` scales every armament on the actor.
Per-target range is resolved one level up in `AttackBase.GetMaximumRangeVersusTarget`
(AttackBase.cs:336), which skips armaments whose weapon is not valid against the target. **The twin
armament IS the mechanism — not duplication to be collapsed.** `Armament` is defined only in
`OpenRA.Mods.Common` (not AS, not CA) and `MaxRange()` is `virtual`, so a Cameo shadow is possible
in principle, but the call site that knows the target lives in `AttackBase`. Feasibility and cost of
that fork are queued to Astra as **C43** — analysis only, no engine change on its strength.

**Implementation queue (C44–C49, full detail in `docs/BLACKROBE_ASTRA_ORDERS_2026-09-07.md` §15):**
generate the 1.5× · write `audit_aa_range.py` · land `^ArmedTroopTransportTemplate` +
`^MobileBunkerTemplate` (BOOT GATE — `defaults.yaml` is engine content) · teach `extract_stats` to
record cargo/fireports · fix the AA detector to cross-check resolved `ValidTargets` · resolve the
three pure-AA units that price at DPS 0.

⚠ **Baseline, measured 2026-09-08, re-measure before acting:** 67 actors carry a live AA armament —
36 at exactly 1.5×, 14 at exactly 1.0×, 14 elsewhere, 3 pure-AA. `scout_vehicle` is already 10 of 10
compliant. Roughly 13 actors need moving, and exactly one `mobile_bunker` (`td_gdi_assaultapc`,
1.500×) must lose its AA gun.

⚠ **The AA detector is a NAME heuristic** (`@AA` slot / `_AA` weapon), not a `ValidTargets` check.
It catches `TSMammothTusk2II_AA` and misses the functionally identical `TSMammothTusk2`. Every
number above inherits that limitation. C48 fixes it.

⛔ **C32 IS CLOSED.** `devin/aurora/fix-anchor-readiness` was never pushed to any remote — it exists
only as a local branch in one checkout — and its `anchor_readiness.py` fix is already on master by
another route (zero `intentional_composite` references; the tool runs clean, exit 0). Astra was
blocked on a branch that no one could reach, and was right to refuse to bypass the gate rather than
treat the absence as permission. The reservation is released; master is the approved starting point.
The same local branch also carries 32 files of LANE-4/LANE-5 classification work that still needs
triage with Aurora — that is separate and unresolved.

<!-- superseded discussion below, kept for provenance -->
### (superseded) the open question as it stood before the ruling

The maintainer asked: *"how can we make it consistent? giving the 1.5x range should be only for
pure anti air vehicles. And if it is a troop transport then those don't count right?"* — and then
paused it deliberately for a clearer head. **Nothing is blocked by it.** Measured state:

```
PURE AA (every armament anti-air):  3 actors        <- the category is nearly empty
Ground gun AND a free AA gun:      63 actors across nine classes
  support 15 (1.50x)  scout_vehicle 10 (1.50x)  anti_air_vehicle 10 (1.50x)
  unclassified 19 (1.00x)  light_tank 2  epic_vehicle 2  line_breaker 1  flying_infantry 1
41 of the 63 sit at EXACTLY 1.50x range; median damage ratio is 1.00
```

**The finding that decides it: 10 of the 11 `anti_air_vehicle` units also carry a ground gun.** A
rule reserving 1.5x for "pure AA vehicles" would apply to ONE actor and strip the bonus from the AA
class itself.

**Two questions were tangled together, and only one mattered:**

* **PRICING — settled and shipped.** An AA armament is free for all 63, excluded from the ground
  DPS everywhere, exactly as the `anti_air_vehicle` anchor already ruled ("priced only on the
  ground weapon"). The anchors derive from ground weapons alone. The pipeline is not waiting.
* **DESIGN — open, and optional.** Whether a troop transport *should* have AA at all is a roster
  feel question. It changes yaml, not the formula.

⚠ The real inconsistency is not the transports: it is the **19 unclassified actors at 1.00x** —
an AA gun with no range bonus. They fall inside the unclassified sweep the maintainer already
deferred until TD/RA1 and Japan are done.

Claude-Local's recommendation on the table: change nothing; record the convention as a GLOBAL rule
(an AA armament is free, same damage, 1.5x range, never priced — it is not a class property), and
revisit the 19 outliers with the unclassified sweep.

### ⭐ 2026-09-08 — SIX MEASUREMENT DEFECTS, ALL THE SAME SHAPE

Every one was a simplifying assumption where the ledger already held the answer. Found by the
maintainer reading the published table, one after another:

| defect | was | is |
|---|---|---|
| `exempt()` asked the CLASS question before the WEAPON question | armed APCs and the Vulcan "chassis-only" | armed is never chassis-only |
| `cameo_rows` took `arms[0]` — yaml order, not importance | `td_nod_lighttankmkii` DPS 0 (its point-defense laser) | 495 of 822 armed actors carry 2+ armaments; 86 reported the wrong one |
| `max()` over armaments | Sheridan 16,000 | simultaneous baseline armaments SUM |
| `live or arms` fallback | siege chopper summed 10 mutually-exclusive barrels to 986,818 | falls back to the strongest single armament |
| `BurstDelay` hardcoded to 5 | right for 78 of 1,017 burst weapons | reads `burstdelays` (3:256, 2:172, 4:160...) |
| the AA test read the SLOT only | `td_gdi_apc`'s `Armament@SECONDARY` firing `APCGun_AA` was invisible | reads slot AND weapon; 41 -> 63 actors |

⛔ And the meta-lesson, because it repeated four times in one day: **a filtered pool made me report
things as missing.** The A10 and X-O "did not exist" (build-limited rows were dropped), 40
references were "lost" (I compared against the non-hero pool), and `assign_references.py` writes
only under `--write` — I read the previous evening's file and reported 30 corrections as failed
when every one had applied. **Check the mtime; check which pool.**

### ⭐ Landed 2026-09-08

* **W24: 322 -> 231 stacks.** EMBER's lane 1 (22 weapons) and DAWN's lane 3 (69) merged and
  boot-gated. Lane 3 arrived with `audit_balance_drift` red across 10 ledgers — yaml changed, no
  re-extract — fixed with `extract_stats.py`. **Yaml and ledger in the SAME commit** is now a
  standing fleet rule.
* **The hero lane** (AURORA), with the `BuildLimit=0` reading corrected: zero is NOT a limit,
  125 corpus rows carry it, and the proposed "fix" would have deleted 110 legitimate actors.
  `td_gdi_commando` claims `RMBO`; `ra1_allies_tanya` claims `E7`/`TANYA`/`E7`.
* **`armed_troop_transport`**, a 28th class. Anchor 50000/100/6000/1200, dps0 400 — four APCs
  across four packs on the same number. ⚠ INERT until `^ArmedTroopTransportTemplate` exists:
  `extract_stats` rewrites `design.class_anchor` to None every run, so SUBTYPE is the only durable
  membership signal.
* **Map: 261 references, O1 8 (ratchet 12), STRONG 756 / FAIR 148 / SHAPE 0 / WEAK 0.**

### ⛔ NOT landed, and why

* `devin/ember/vfi-signature-fix` — good work (references 904 -> 956, and Romanov's Vengeance cut
  730 -> 200 rows costing ZERO live references) but it pushed **O1 from 8 to 13, over the ratchet
  of 12**, stranding `minelayer`, `phasetransport`, `nukedemotruck`, `sovietoretruck` and two more.
  Back to EMBER with the list. **Never raise a ratchet to land a branch.**
* `devin/aurora/ini-pool-hygiene` — the `BuildLimit=0` change above. Rejected with evidence.
* `devin/nova/w24-lane2` — 57 commits, rotted from 5 conflicts to **36** while NOVA stayed silent.
  It is the only agent that has not pushed since 2026-09-07.

### ⭐⭐ 2026-09-08 — THE EXTRAPOLATION PROGRAM IS THE PLAN NOW

`docs/design/EXTRAPOLATION_PROGRAM.md` — the maintainer's method, written down with the two
measurements that prove it works. Anchors stop being real actors and become VIRTUAL ones derived
from the reference-mapped originals of TD, RA1 and Japan.

Two findings that settle it:

* **26 of 27 classes have members in TD/RA1/Japan.** Only `dreadnought` has none (its five members
  are StarCraft/naval). Measured through `class_membership.classify()` over 700 classified rows.
  ⚠ Two earlier attempts returned all-zeros and 8-zeros — both bugs in the CHECK, because membership
  is DERIVED from `design.subtype` when no explicit tag exists.
* **The virtual-anchor mechanism ALREADY EXISTS and nothing uses it**: `fit_class.py --spec
  hp,speed,range_wdist,damage,reload,cost0`, *"a round-number model unit that need not exist in
  game"*. `faction_extrapolate.py` (504 lines) likewise already implements the exchange rate. What
  is missing is the INPUTS, not the mechanism.

Why it is right, not a workaround: 23 of 27 real anchors are off their ruled spec, 0 of 27 satisfy
`o0=p0=q0=cost0`, and restatting one actor silently reprices its whole class. A virtual anchor
cannot drift. Phases A–E, owners and gates are in the program document; the approval ledger is §5.

Maintainer rulings, 2026-09-08:
* **Fogged bot observation SHIPS** (AI §9 decision #1, open since the document was written).
* **Astra owns the RA2 + TS reference maps** — every input is committed, no game install needed.
* **Originals are approved faction by faction**, and extrapolation starts per faction on approval.
* **Astra ships CODE.** `docs/BLACKROBE_ASTRA_ORDERS_2026-09-07.md` §14.

### Priority queue

1. **CA over-tagging** (EMBER) — unblocks ~8 known-wrong mappings at once.
2. **Heroes are invisible on BOTH sides — that, not a missing filter, is why `RMBO` is
   unclaimed.** ⚠ This CORRECTS what this file said earlier on 2026-09-07, and the correction
   matters more than the item. Aurora's `filter_candidate_eligibility.py`
   (`devin/aurora/pool-hygiene-clean`) must **not** be wired as written: measured against the live
   pipeline it removes **0** rows that `reference_distribution.ini_rows()` keeps, and would add
   **699** back (295 build-limited one-offs, 404 with no cost at all). `ini_rows()` already applies
   its exact rule — `cost` AND no `build_limit` AND `buildable` — and applies it more strictly.
   Wiring the side file would LOOSEN the pool, not clean it.
   The real cause is the POPULATION RULE itself (maintainer, 2026-08-30): `cameo_rows()` drops
   every actor carrying a `build_limit`, so **83 Cameo hero/epic combat rows** — Tanya, Boris,
   Volkov, both TD Commandos, Havoc, Kerrigan, Zeratul, Jim Raynor, Chrono Tank, MAD Tank — never
   enter the reference map at all. OpenTD's `RMBO` sits in the peer pool and always did; there is
   simply no Cameo actor left in scope that can claim it, and the same is true of OpenRA RA's
   `CTNK`.
   ⭐ **RULED 2026-09-07 — the HERO-ONLY REFERENCE LANE.** Heroes stay OUT of every ordinary
   distribution (the population rule is unchanged, and the 3,000,000 HP epic never re-enters the
   vehicle ceiling), but a Cameo hero MAY match a peer hero, so `td_gdi_commando` claims `RMBO`
   and `ra1_allies_chronotank` claims `CTNK`. References only — **no hero is ever priced by the
   ordinary formula.** Implementation is the fleet's: a hero flag carried on the row rather than a
   drop, `peer_rows()` keeping its exclusion for distributions, and `assign_references` matching
   hero-to-hero only. 83 Cameo actors and 295 peer heroes are in scope.
3. **Aliases for the 9 short originals** (ECHO) — each is one synonym; DTA calls its rocket
   soldier "Bazooka" and its AA gun "Anti-aircraft Gun". Finite and checkable.
4. **Sign the 27 class anchors** (CODEX) — 0 of 27 signed, and `apply_balance` therefore refuses
   every faction. This, not writer safety, is what blocks the whole pipeline.
5. **Then: the faction-calibration method for expansions** — anchor on originals, derive the rest
   (class anchor × tech tier × faction factor). Maintainer wants **Japan** as the first test,
   precisely because it has no reference data.

### Open questions the maintainer has not answered

* **Is Romanov's Vengeance the RA2 authority?** It carries 729 buildable units; RA2 + YR never
  shipped that many. It is 104 of 119 unclaimed "originals", and O2 currently reports it without
  gating on it. That exemption must be DELETED when ruled, never raised.
* **TD naval** — GDI and Nod ships exist in DTA and CA and Cameo has none mapped.
* Missing actors the maintainer named: **RMBO / E7 (Tanya)**, CA's Chinook, Specter, Venom.

---


**2026-08-25 update (Devin AI):** The volcanic shellmap (`shellmap_v3.oramap`) camera was too tight (6-cell radius), hiding the scripted attack waves. The `attack.lua` camera radius has been widened to 45 cells. The boot-blocking stale removal `-Warhead@CannonHE_MediumPercentage` in `weapons/outpost2.yaml` is resolved in `a92ae850`, and boot-gate passes with no new exceptions. See `DEVELOPMENT_LOG.md` § "Volcanic shellmap camera radius fix" for evidence and verification.

**This is the single entry point for anyone picking up work on Cameo — human or agent.**
Written 2026-08-23, re-verified against master at `e60aab63`. It supersedes every previous handoff document;
those are archived under [`history/handoffs/`](history/handoffs/) and must not be resumed from.

| you want to… | go to |
|---|---|
| know what to do next | §3 below, then [`design/ROADMAP.md`](design/ROADMAP.md) |
| know the balance program's state and who owns what | [`design/BALANCE_PROGRAM_PLAN.md`](design/BALANCE_PROGRAM_PLAN.md) §0, §0a, §1, §2 |
| know a binding rule before editing yaml | [`DESIGN.md`](DESIGN.md) |
| avoid a trap someone already hit | [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md) |
| know how the bots are meant to work, and what is only designed | [`design/AI_ARCHITECTURE.md`](design/AI_ARCHITECTURE.md) |
| know the current bug counts | [`audit/SUMMARY.md`](audit/SUMMARY.md) |
| find which document owns a topic | [`README.md`](README.md) |
| **you are the Blackrobe GPT-6 Astra Agent** | ⭐ [`BLACKROBE_ASTRA_BRIEF.md`](BLACKROBE_ASTRA_BRIEF.md) — your complete single-prompt instruction set |

---

## ⛔ 2026-09-07 — the reference map, and what it cost to make it trustworthy

**master `57d7d7858`.** The maintainer reviewed a TD/RA1 reference map and rejected it:
`ra1_allies_rifleinfantry` was mapped to a **Cryo Trooper** when all three sources ship an E1.
Seven silent defects, each individually sufficient — full list in
`memory: cameo-reference-defect-cascade`, the essentials here.

⭐ **THE LESSON.** The matcher was never choosing badly. **The correct candidate was deleted
from the pool before matching**, and the greedy picked the best of what remained. Every wrong
pairing looked like a scoring bug and was a visibility bug.

⛔ **A "verification" that reads a crashed run's output verifies nothing.** `factions_of` lost
its `vfi` parameter in a merge, so every OpenRA extraction raised TypeError and was swallowed
per-mod; my splice then copied the unchanged file back and I reported the fix working.

**THE ACCEPTANCE TEST** (maintainer, verbatim): *"All the original units are in OpenRA. DTA, CA
and Cameo all expand the roster... those that exist in OpenRA and OpenTD MUST ALWAYS HAVE 3
REFERENCES."* Encoded as `audit_original_coverage.py`. **O2 — an original nobody claimed — is
the check that matters**; a voice count cannot see it.

**OPEN QUESTION, unanswered:** Romanov's Vengeance carries **729 buildable units**. RA2+YR never
shipped that many, so RV expands the roster like CA and DTA do. `OpenRA RA2 official` (86) and
`Yuri's Revenge on OpenRA` (124) match the real rosters. Which is the RA2 authority?

**NEXT, in order:**
1. Work the O2 list — **every Tiberian Dawn defense is unclaimed** (Obelisk, Guard Tower,
   Advanced Guard Tower, Turret, SAM), plus RA1's Tesla/Chrono tank and Demolition Truck.
2. Settle the RA2 authority, then re-baseline O1/O2.
3. The regen conversion (892 nodes, delegated, `devin/regen/conversion`) — **Claude-Local flips
   `defaults.yaml` LAST and merges whole**, or master double-heals.
4. The faction identity modifier to break byte-identical mirrors — magnitude not yet set.

⚠ **No balance number has been written to yaml.** Nothing is applied until the map is right.

## ⭐ AGENT ASSIGNMENTS — who is doing what (2026-09-06)

| agent | lane |
|---|---|
| **Blackrobe GPT-6 Astra** | ⭐ **FINISH THE BALANCE PIPELINE** (Tasks A–G) **and inherit the AI bot modules** (Task H — Devin Cloud ran out of quota mid-merge). Full brief: [`BLACKROBE_ASTRA_BRIEF.md`](BLACKROBE_ASTRA_BRIEF.md). Branch `astra/balance-pipeline`, never master. Has **full authority including `apply_balance --confirm`**, conditional on one commit per decision and a review dossier at `audit/ASTRA_REVIEW.md`. |
| **Aurora** | `ra1_allies` + `ra2_allies` + `ts_gdi` — **128 items**, incl. the 16 Allies sprites wearing Soviet names → `../Cameo-mod-fleet/TASK_2026-09-06_aurora.md` |
| **Ember** | `asianalliance` — **100 items**; first action is to rebase and push the finished `.asian` branch → `TASK_2026-09-06_ember.md` |
| **Nova** | `ra1_soviets` — **94 items**, incl. the fluent-key leak and the 19 doubled filenames → `TASK_2026-09-06_nova.md` |
| **Dawn** | `latinsyndicate` + `steelconsortium` + `wc2_*` + `zerg` — **79 items** → `TASK_2026-09-06_dawn.md` |
| **Echo** | `ixian` + `ordos` + `d2k` + `japan` — **68 items** + the mod's last hyphen → `TASK_2026-09-06_echo.md` |
| **Blaze** | `atreides` + `corrino` + `harkonnen` + `futuretech` + `yuri` — **32 items**, incl. **14 of the 15 actor-id renames left in the whole mod** → `TASK_2026-09-06_blaze.md` |
| **Claude-Local (Opus 5)** | rulings, review, squash-merges to master, and the gates |

⚠ **Nobody merges to master except Claude-Local.** Agents commit freely on their own branch
and report a completed work item; Claude reviews and squash-merges one meaningful commit. The
maintainer must be able to read master — 107 commits in one day, 49 of them touching only
`DEVELOPMENT_LOG.md`, is not reviewable.

### ⛔ 2026-09-07 — four bugs shipped past every gate; three new audits + one hook rule

**The maintainer found the worst one by playing**: the mutalisk's fire shrapnel bounced
forever. Root cause for two of the four, and it is now `CLAUDE.md` rule 8g:

> **`-Key@X:` in a child CANCELS what an ANCESTOR defines.** It looks dead precisely
> because the node it sits in does not define X.

`d818aec40` deleted 2248 of them as "stale": multi-main weapons **461 → 1103**, and 14
deleted `-Warhead@shrapnel:` terminators made the spore loop forever. **Nothing
crashed** — a boot gate proves the rules PARSE, never that they are RIGHT. Reverted in
`ad6fc66b8`, ledger re-extracted in `a6525d6fb`.

| new gate | catches | ratchet |
|---|---|---|
| `audit_shrapnel_chains.py` | a FireShrapnel chain that never ends | S1a **0**; S1b **0** — 44 self-cycles were the same damage; fixed in `7b63045fd` |
| `audit_map_actors.py` | a map placing an actor the rules do not define (boot gate is blind: it fails when the map is STARTED) | M1 **0** |
| `bash_guard.py` rule 4 | deleting a `-Key@...` without `RESOLVE-VERIFIED` in the message | — |

Also fixed: `audit_naming_damage`'s regex could not see a doubled id (reported N1 4 /
N2 0 against the true 25 / 16 — an exact zero is always suspect), and the boot-gate
hook read the MAIN checkout's index from every worktree, which would have waved
through engine content committed from a worktree. Both now have self-tests.

✅ **RESOLVED 2026-09-07 — they were not old debt, and they are fixed.**
`ad7c5e232` (labelled a *rename*) also stripped **236 removal nodes** out of
`RedAlert/Soviets/yaml/weapons.yaml`, and the tesla fragments' `-Warhead@TeslaArc:`
terminators were among them. Restoring all 236 (`7b63045fd`) took **S1b 44 → 0**;
the ratchet is now 0. Every FireShrapnel chain in the mod terminates: 193 weapons,
193 chains, zero cycles of either kind. No in-game test needed.

⚠ **I was wrong about these twice, and the second time is the instructive one.** First
I called them benign chain lightning — reasoned from field names, not the code. Then I
called them pre-existing debt because *"all 44 predate `d818aec40`"*. That was literally
true and still the wrong conclusion: **the bisect stopped at the first commit that showed
the problem instead of walking back until it disappeared.** One commit further back was
the actual cause. When bisecting, walk back until the symptom is GONE, not until it
first appears.

Full write-up for agents: `../Cameo-mod-fleet/BRIEF_2026-09-07_what_broke_and_the_new_gates.md`.

### ⭐ Naming — the real state, measured 2026-09-06 (replaces every earlier count)

`python tools/audit/audit_naming_damage.py` is the source of truth and is now in
`run_all.sh`. Six pathologies, six **lower-only** ratchets, all currently PASS:

| code | pathology | count | lane |
|---|---|---|---|
| N1 | a filename carries one actor id **twice** | 25 | Nova 19, Aurora 4, Dawn 2 |
| N2 | a filename carries **two factions'** ids | 16 | Aurora — all 16 are RA1-Allies sprites wearing Soviet names |
| N3 | a **fluent key** became an actor id | 5 | Nova |
| N4 | the faction named **twice** (`ra1_allies_alliedaagun`) | 345 | split per faction |
| N5 | dotted id that is not a sanctioned `.husk` | 161 | split per faction |
| N6 | a hyphen (rule 9) | 1 | Echo |

**Three earlier numbers were wrong and are retired:**

* the **526-actor backlog** was a doubled game prefix in one config table — seven of eight
  factions jumped **0% → 100%** when it was fixed;
* the **144 dotted renames** undercounted; the real figure is **161**, and separately
  **234 `.husk` ids are LEGAL** (`DESIGN.md` line 71 sanctions dotted `.husk` variants), so
  the raw 398 must never be quoted as backlog;
* **`.nax` / `.nax2` are DONE** — 0 remain. Nova landed them.

Actor-id work left in `gen_rename_maps` is **15 actors total**: `atreides` 21/23,
`corrino` 22/25, `harkonnen` 27/35, `ixian` 60/65. Every other faction reads 100%.

⚠ **A 100% row there is not proof a faction is clean.** That report sees only
faction-exclusive **buildable** actors, and `startswith(prefix)` is satisfied by
`ra1_soviets_sovietairfield` too. `asianalliance` reads 73/73 while holding 27 dotted and
73 redundant-word ids. Use `audit_naming_damage.py` for the real number.

⛔ **`gen_rename_maps.py --files` is opt-in and `--out` is mandatory practice.** Six defects
were found in its file half on 2026-09-06 (commit `c9437f4f8`); a regenerate proposed **842
file renames, 92 corrupt**, now **44, none corrupt**. Without `--out` a run **overwrites every
`tools/rename/rename_map_*.yaml`**, including hand-corrected ones. See `LESSONS_LEARNED.md`
"Fix the TOOL, not its output".

### AI bot modules — state as of 2026-09-06

Devin Cloud designed the module architecture and stopped mid-merge when its quota ran out.
**The design is landed, not lost:**

* **PR #324 is MERGED** — [`design/AI_ARCHITECTURE.md`](design/AI_ARCHITECTURE.md) **§10** (the
  per-module build plan, the shared snapshot, the one synced piece, and the 7-phase build
  order) and **§11** (the reconciliation of the first five-agent research round, with rejected
  claims and what falsifies each).
* **PR #323 is OPEN and CONFLICTING** — Observer Combat Effectiveness graph, +233/−12, and it
  touches C#, so it needs a `dotnet build` and a boot gate, not just a merge. **Assigned to
  Astra, Task H.1.**
* ⚠ `gh` defaults to the wrong remote in this checkout — always pass
  `--repo cameo-mod/Cameo-mod`.
* Next implementation step is **phase 1: record-only match logging.** Phases 1–2 carry no
  gameplay effect and may run while the balance pipeline is still moving; **phase 6 (fog) is
  deliberately last** because it weakens the bots and invalidates any tuning done before it.

⚠ **If you are a Devin agent, your task file is `../Cameo-mod-fleet/TASK_2026-09-06_<you>.md`**
and the index is `TASKS_ACTIVE.md`. Each task file is self-contained: your complete item list,
the method, the faction-specific traps, the gates, and the report format. Read
`BRIEF_2026-09-06_naming_damage.md` once for context before you start.

⚠ **Agent-to-agent chatter lives OUTSIDE the repository**, in `../Cameo-mod-fleet/`.
`DEVELOPMENT_LOG.md` keeps one entry per COMPLETED work item plus lessons learned — nothing else.

## ⭐⭐ START HERE 2026-09-07 — why the balance pipeline has not moved, and the fix

```
$ python tools/balance/apply_balance.py --faction d2k_atreides
DRY RUN: 0 values would change
```

**The pipeline is not blocked by tooling, by W11, or by sign-off. It is idle because nobody
has written a target number into the ledger.** `apply_balance` writes ledger → yaml; the
ledger holds today's values; applying it is therefore a no-op *by construction*.

`anchor_readiness.py` reports **0 of 27 classes signable**, 26 failing "the anchor does not
describe its members" (median pricing error 15%–106%) — and explains itself in one line:
*"the anchor actor is still PRE-RESTAT, so its percentile is measured on stats the design
already intends to replace."*

Meanwhile **all 27 classes already carry a complete spec** in `docs/balance/class_anchors.json`
(`cost0`, `dps0`, `hp0`, `range0_wdist`, `speed0`) that has never been used. `mbt`'s spec is
hp0 **240,000**; the actual unit has **100,000**. The numbers were designed and never written
anywhere the pipeline reads.

⭐ **MAINTAINER ORDER, 2026-09-07 — do this first:**

1. Write the 27 anchor specs into the ledger on **`hp0` / `speed0` / `range0_wdist` / `cost0`
   only**. ⛔ **NOT `dps0`** — it depends on weapon structure and therefore on W24, and would
   be written twice.
2. `python tools/balance/apply_balance.py --faction <f> --confirm`
3. Boot-gate, re-extract, then re-read `anchor_readiness.py`.

This is the first real balance change the project will have made, and it breaks the apparent
circularity (sign-off needs a restat; the restat needs numbers in the ledger — which is a
LEDGER edit, explicitly sanctioned by CLAUDE.md rule 3, not a hand edit of yaml).

⚠ The four non-DPS axes depend on nothing but the unit, so **W24 is not a prerequisite for
this.** The two can run in parallel: the restat writes `docs/balance/*.json` → actor yaml,
W24 writes `**/weapons.yaml`, and `extract_stats.load_existing_design()` preserves authored
`design.*` across re-extraction.

## ⛔⛔ TOP OF THE QUEUE 2026-09-07 — revert the ra1_soviets rename

**All 32 actor renames `ad7c5e232` applied made the id LONGER and WORSE. Not one
improvement in the set.** Full write-up and the revert procedure:
[`design/RA1_SOVIETS_RENAME_REVERT.md`](design/RA1_SOVIETS_RENAME_REVERT.md).

```
ra1_soviets_barracks              -> ra1_soviets_sovietbarracks
ra1_soviets_constructionyard      -> ra1_soviets_sovietconstructionyard
ra1_soviets_attackdog             -> ra1_soviets_actordogname      (a FLUENT KEY)
ra1_soviets_doctrine_conscription -> ..._doctrine_conscriptiondoctrine
ra1_soviets_upgrade_hammertank    -> ..._upgrade_hammertankupgrade
```

The tech markers are **duplicated** — `doctrine_X` became `doctrine_Xdoctrine`. That is
what a mechanical rename looks like when nobody reads three lines of the proposal.

**The cause is already fixed** (`c9437f4f8` defects C and E), so the corrected generator
now proposes the ORIGINAL ids — the revert target is what the tool produces, not a
judgement call. It has already cost: 7 broken `.oramap` files including both shellmaps
(two tester crashes), 236 deleted removal nodes, and 69 of the 345 N4 findings.

⛔ **Do not batch this with another rename.** It touches both shellmaps; boot gate is
mandatory.

**The rule it earns: a rename that makes an id LONGER is a regression until proven
otherwise.** A batch that raises N4 has failed, whatever its compliance percentage says.

## ⭐ NEW WORK SPECIFIED 2026-09-07 — two maintainer orders, neither built

Both are written up in full, with the state verified rather than assumed. Neither is a
naming-lane task; both are self-contained and neither outranks the balance pipeline.

### 1. Paired effect+sound templates — [`design/EFFECT_SOUND_TEMPLATES.md`](design/EFFECT_SOUND_TEMPLATES.md)

One inherit must carry the visual **and** its sound, named after the source game and the
effect's own file name (`^d2k_big_explosion`), so the two can never drift apart.

Measured: **6987** CreateEffect warheads, only **4008** carry both halves, and **68**
sprites are each used with more than one sound. The reported symptom is located exactly —
`D2K_Rocket_Trooper` pairs the visual `d2k_tiny_explosion` with the sound
`xplobig4.aud` (a BIG explosion sound on a TINY sprite), and its four variants have four
different pairings, one of them borrowing a RA/TD sound for a D2k visual. Those five
weapons are the acceptance test.

### 2. Colour-picker preview for every faction — [`design/COLORPICKER_PREVIEW.md`](design/COLORPICKER_PREVIEW.md)

⚠ **The believed state was wrong.** TD/RA/Japan were not "done": `fact.colorpicker`,
`rafact.colorpicker` and `rafactj.colorpicker` exist but are **dead — nothing references
them**, there is **no `FactionPreviewActors` block anywhere**, and every faction currently
previews a Soviet mammoth tank.

The engine already has `FactionPreviewActors` (zero C# needed), but using it as-is means
~31 clone actors. The better build is a **`RenderSprites` shadow in `OpenRA.Mods.Cameo`**
honouring `ActorPreviewType.ColorPicker`, so any actor is its own preview — **route
confirmed open**, since neither AS nor CA defines `RenderSprites`. No engine fork.

## 0. The one rule that makes all the others work

**Don't trust — verify.** Before you assert that anything is done, pending, blocked or missing:
grep the data, `ls` the file, run the tool, boot-gate the tree. When a summary (a ROADMAP line,
a status table, an older handoff, this file) disagrees with the artifact, **the artifact wins —
and then you fix the stale summary in the same commit.**

This is not a slogan. The 2026-08-23 documentation pass found, by running the tools:

* five pinned numeric claims had drifted from the tree, and one gate (`audit_balance_drift`) was
  RED while the committed report said "clean" — the report was three commits stale;
* `docs/audit/latest/` held **two** copies of every report under different names, because the
  repo had two audit runners with different filename conventions;
* `DESIGN.md` used the section id **§12.0a twice**, for two different binding laws;
* the retired 2000-step damage grid was still taught as law in eight documents, one skill and
  one audit script, four days after `formula.DAMAGE_STEP` became 100;
* eight board statuses in `BALANCE_PROGRAM_PLAN.md` contradicted that same file's own per-item
  headings.

None of that was visible by reading. All of it was one command away.

### Verify a claim, not a hash

Cloud and CI checkouts of this repo are **shallow** — `git log` starts at 2026-08-10, so
`git show <older-hash>` fails on most hashes the docs cite. That is a property of the checkout,
not of the history: the commits exist upstream. Either run `git fetch --unshallow` first, or
(better) verify the claim against the artifact — which is what §0 asks for anyway.

### Two more things you cannot resolve from the repository

* **`memory <name>` citations.** 36 references across the design docs point at an external,
  per-agent memory store. Nobody else can open them. Treat every one as **provenance only,
  never as authority** — if a memory carried a binding rule, that rule needs to be promoted
  into `DESIGN.md` before it counts.
* **`engine/` is not in this repository.** It is `.gitignore`d, has no `.git`, and
  `git ls-files engine` returns zero. Editing `engine/**` produces work that cannot be
  committed here and is deleted by the next `make all`. See §5.

---

## 1. Where the project actually is (verified 2026-08-23)

**The mission.** Cameo is a crossover RTS spanning the classic RTS games. The architectural goal
is **dynamic faction loading** — load only the factions the lobby picked, instead of everything
at boot (historical peak: 12 GB RAM, unplayable on 8 GB machines). Every faction therefore
becomes a self-contained ContentPack. Runbook: [`MIGRATION.md`](MIGRATION.md).

**Health.** Green, with one red that needs a maintainer decision rather than work.

| | |
|---|---|
| crash-class content (B8) | **0** |
| empty warhead types (boot NRE class) | **0** of 2765 weapons |
| dangling weapon refs / dangling inherit targets | **0** / **0** |
| `tools/tests` | **286 tests, all green** |
| cross-document consistency audit | 73 passed, 0 failed |
| balance-ledger drift | **0** — master re-extracted in `31e649b8` |
| pinned doc claims | **19 of 19 match** |
| generator sync | drift **0** across 136 shared templates |
| documentation structure (`audit_doc_health`, D1–D8) | **0** findings |
| heaviness bell | **0 inversions, 0 mean drift** across 48 families; 2 flat (`Sonic`, `Magic`) at ratchet 2 |
| `audit_doc_health` | ✅ **PASS** — the D8 self-flag was fixed 2026-08-23 |
| `environment.py` | ✅ reports a complete tree — the CA path was fixed 2026-08-23 |
| **suite exit code** | **1**, and legitimately so — 8 gating audits report real content defects (§3.3's backlog). The 5 SCHEDULED scans that also reddened it are now ADVISORY. See §3.0c |
| physical-state warheads | ✅ **PASS** — the audit demanded percentage TWINS the AreaDamage fold folded away; six false failures, fixed in the audit not the yaml |
| `audit_test_coverage` | 269 untested vs baseline 224 — **advisory**, and recorded debt. `T3_BASELINE` deliberately NOT raised |

⚠ The counts above were re-measured at `519175ae`; the per-class counts in
[`audit/SUMMARY.md`](audit/SUMMARY.md) come from the last full suite run and carry the
mixed-environment caveat described there.

**The active front is the weapon rebuild, and pricing is deliberately NOT running yet.**
`BALANCE_PROGRAM_PLAN.md` §0a is the binding order, and the reason is measurable: a price is a
function of `K`, `K` is built from a weapon's warhead set and their `Versus` profiles, and both
are still scheduled to change across most of the roster. Pricing now means pricing inputs that
are about to be replaced.

```
W24  one damage warhead per weapon          184 directly fired weapons still carry 2+
 └─> W23  retrofit the legacy templates      1596 direct inheritors
 │        (2026-09-07 raw counts; 234 direct + indirect reachable stacks)
 │        (its old "33-collision" blocker
 │         is DISSOLVED — W24 removes it)
 └─> A5   retire the remaining inline-Versus weapons onto templates
      └─> class anchors → fit_class per class → W11 maintainer sign-off
           → targets written into the ledger → apply_balance --confirm → boot gate
```

⚠ **`apply_balance --confirm` is a NO-OP until targets are written into the ledger, and that
needs W11's sign-off.** Signed-off class anchors today: **0**. So no price in the tree is final,
and "run `--confirm`" is never the next step on its own.

Independent of that chain (different file sets, safe in parallel): the physical-state meter
items **W7, W9, W10**, and the superweapon track **W12**.

---

## 2. Before you touch anything

Read, in this order. This is the canonical order; [`README.md`](README.md) is its definition and
wins over any copy of it.

1. [`CLAUDE.md`](../CLAUDE.md) — the hard rules, loaded every session.
2. [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md) — the traps, each one paid for.
3. [`AGENT_WORKSPACE.md`](AGENT_WORKSPACE.md) — workflow, evidence rules, commit gate.
4. **this file** — current state and the queue.
5. [`DESIGN.md`](DESIGN.md) — the binding contract. Read the sections your change touches.
6. [`design/ROADMAP.md`](design/ROADMAP.md) — the granular queue.
7. [`audit/SUMMARY.md`](audit/SUMMARY.md) — current counts by bug class.

Then the topic doc for your task, from the table in [`README.md`](README.md).

### The ten hard rules, in one place

Rules 1–2 are enforced by hooks in `.claude/settings.json`.

1. **Boot-gate every commit of engine content.** `launch-game.cmd` must reach the main menu:
   `perf.log` ends with `MenuPostProcessEffect.PostWorldLoaded`, and no NEW `exception-*.log`
   in `%APPDATA%/OpenRA/Logs`. Snapshot the log list **before** launching. Menu proof is
   grepping `perf.log`, not eyeballing its last line.
2. **Scoped `git add <files>` only — never `-A`, `.` or `--all`.** Other contributors have live
   uncommitted work in this tree.
3. **Never hand-edit a balance number.** Use the pipeline: `extract_stats` → ledger →
   `apply_balance --confirm`. `--confirm` requires a maintainer order.
4. **`Versus` lives ONLY in `^Warhead_*` templates.** Never change a warhead, `Burst` or
   `BurstDelays` without explicit permission.
5. **Weapon 3-way split:** preserve resolved behaviour (`Damage` verbatim, projectile fields),
   `find_empty_warhead.py` = 0, boot-gate per batch. Verify with
   `tools/audit/review_resolve_diff.py` (resolve before and after).
6. **One owner per file-set.** Check a file's mtime and `git log -3 <file>` for a live agent
   before editing. Re-verify others' commits before building on them. Never
   `git checkout -- .` or wide-add someone else's work.
7. **Rebuild C# before booting** if `OpenRA.Mods.Cameo/` or `engine/` changed. Stale DLLs crash
   the boot with `Cannot locate type: …Info`. See §5 for the engine pipeline.
8. **Audit reports regenerate via `bash tools/audit/run_all.sh` only** — a PowerShell `>`
   redirect writes UTF-16 and corrupts them.
9. **Underscore-only naming** — no hyphens in ids, files or fluent keys. (The single
   deliberate exception is the `cameo-content` installer mod, which must match the engine's
   `*-content` convention.)
10. **Sign the commit trailer with your OWN identity and your REAL model name** —
    `Co-Authored-By: Claude <model> <noreply@anthropic.com>`. The git author is a shared repo
    identity, so the trailer is the only provenance signal. **Never copy a trailer from a
    previous commit or from CLAUDE.md** — those are templates, and copying one makes a newer
    model misreport itself as an older one. A non-Claude agent signs as itself
    (`Co-Authored-By: Devin AI <devin@cognition.ai>`) and never appends the Claude trailer.

### The gate before every commit

```sh
python -m unittest discover -s tools/tests -t tools/tests   # all green (227 as of 2026-08-23)
python tools/audit/find_empty_warhead.py                    # 0
python tools/balance/verify_generator_sync.py               # ⛔ drift = 10 today; only
                                                            # ^Warhead_Sniper_Light is accepted
bash tools/audit/run_all.sh                                 # bash ONLY
python tools/balance/extract_stats.py --check               # 0 drifted
```

…then the boot gate (rule 1). If Windows Smart App Control blocks the launch, use one of the
four documented options in `LESSONS_LEARNED.md` § Smart App Control and **record the SAC state
in the commit message**. Never silently skip the gate, and never claim it passed when it did not.

`utility.cmd cameo --check-yaml` is a **separate lint tool**, not a boot-gate substitute. It
takes 10+ minutes; run it once you have finished a batch and expect 0 errors and 0 warnings —
not repeatedly.

---

## 3. The queue, in priority order

Crashes and player-visible regressions jump everything below.

### 3.A — MULTI-AGENT COORDINATION (read this FIRST if you are an AI agent)

**As of 2026-08-25, there are 5 Devin AI agents running locally.** Each agent MUST:
1. Pick a unique name from the list below (or claim a new one in `DEVELOPMENT_LOG.md`).
2. Read `DEVELOPMENT_LOG.md` §"Active claims" BEFORE editing any file.
3. Claim a file-set by adding an entry to `DEVELOPMENT_LOG.md` §"Active claims" BEFORE editing.
4. NEVER edit a file that another agent has claimed or that is in the locked list.
5. After every step: update `DEVELOPMENT_LOG.md` with what you did, why, and what's next.
6. Before committing: run verification (find_empty_warhead, audit_warhead_split,
   review_resolve_diff, audit_doc_claims) and boot-gate (`launch-game.cmd`).
7. Use scoped `git add <files>` only — never `git add -A` or `git add .`.

#### Agent roster and current assignments

> ⭐ **THIS IS THE ONLY AUTHORITATIVE ROSTER.** Three other ownership tables exist
> lower in this file (D2k faction completion, §3.C, §3.6); all three are marked
> SUPERSEDED and contradict this one. Claim file-sets from HERE and nowhere else.

> **⚠ FLEET HIERARCHY (maintainer order 2026-09-05):** *"Claude AI is now your big
> boss and controls all other AI Agents so you must always listen to him and do
> EXACTLY as he says!"* — **Claude (Opus 5, local) is the fleet coordinator.** All
> agents take direction from Claude. Aurora remains D2k coordinator **under Claude's
> authority.** Claude has not yet issued consolidated fleet-wide orders in his
> coordinator capacity; until he does, agents continue their established roles below.

| Agent name | Status | Current task | Files claimed |
|---|---|---|---|
| **Claude** (Opus 5, local) | **Fleet coordinator** (maintainer order 2026-09-05) | ✅ Reference-pipeline tooling landed (`85bcf3f33`). ✅ 7 reference mods extracted (8183 unit rows). ✅ Master fast-forwarded 113 commits. **AWAITING: issue consolidated fleet-wide orders. Rule on 4 open items: (1) ordos_laserturret "unique and special" mechanical spec, (2) heaviness bell — refold existing level templates now or later?, (3) composite registry re-curation priority, (4) CannonTesla family under single-warhead ruling.** | `tools/reference/**`, `tools/balance/{assign_references,faction_routes,faction_extrapolate}.py`, `docs/balance/review/**` |
| **Devin-Dawn** (was Devin-Prime) | Active (awaiting) | D2k/Corrino pack skeleton created (`f07d8d35e`); full Corrino build pending WC2 hero blocker and phases 1-2. TSLaser90mm family work on hold. **WC2 blocker is RESOLVED — proceed with Corrino Phase 3.** | `ContentPacks/D2k/Corrino/`, `mods/cameo/weapons/tiberiansun.yaml` |
| **Devin-Aurora** (SWE-1.7 Max / GLM-5.2 High) | Active — **D2k coordinator under Claude** | D2k Phase 0/1/2/3 coordinator. ✅ Ruling 7 EXECUTED: Factions: atreides (37 blocks) + Factions: ordos (72 blocks). ✅ Ruling 3 EXECUTED: Ordos Selectable + 3 sequence migrations. ✅ Ruling 5 EXECUTED: meter_dilution fix. ✅ Ruling 9 COMPLETE for my lane: 2 Atreides + 41 Ordos + 3 Shared weapons migrated; 13 Atreides + 4 Ordos sequences migrated. ✅ Ruling 10 EXECUTED: 0 Ixian cross-pack refs in Ordos. ✅ Ruling 13 W24: d2k_grenade re-collapsed correctly (`f901513a7`) — VERBATIM 10000, Concussion_Medium survivor. HMG collapse done by maintainer (`a16ee55fc`). ✅ **ra1_soviets rename** (`ad7c5e232`): 106/106 actors compliant, 105/105 icons, 181 asset git-mv, 8 .oramap repacked, boot-gate PASS. ✅ **Split-definition cleanup** (`a662a68f5`): 30 identical duplicate blocks deleted from legacy `weapons/d2k.yaml`; W2 201/213, W3 18/21, W4 58/61 (all below ratchet); boot-gate PASS. ⛔ **W24 collapse attempt on D2K_Rocket_Trooper_AA + AGOnly was WRONG — reverted.** The maintainer's `d818aec40` showed the correct approach is NOT to collapse but to remove stale `-Warhead@` markers and fix empty-type warheads. **AWAITING Claude ruling on how to handle multi-warhead weapons under the ONE-WARHEAD law. Do NOT collapse any more weapons without explicit Claude/maintainer instruction.** | `mods/cameo/ContentPacks/D2k/Atreides/`, `mods/cameo/ContentPacks/D2k/Ordos/`, `mods/cameo/ContentPacks/D2k/Shared/yaml/weapons.yaml`, `mods/cameo/bits/d2k/` |
| **Devin-Cyrus** (was Devin-Forge) | **RESOLVED** — WC2 hero pass committed by maintainer | WC2 hero weapon rework. Maintainer committed Cyrus's unfinished work as `d11b90720` (2026-08-25): 8 hero weapons + 8 hero actors across Humans and Orcs. Hellscream + elite verified: actors, weapons, sequences, icon all present. **Cyrus: stand down, this is done.** | `mods/cameo/ContentPacks/Warcraft2/Humans/`, `Warcraft2/Orcs/` |
| **Devin-Ember** (SWE-1.7 Max) | Active — **W24 broadcast lane (RedAlert)** | Per Claude's night orders: ra2_allies rename was PHANTOM (FACTION_SLUG bug, fixed in-tree). Executed 6/8 assigned broadcast collapses — VERBATIM, delivery-matched survivors, resolver-diffed clean, `find_empty_warhead`=0, count 72→64 — **held UNCOMMITTED** until the maintainer's `-Warhead@` sweep + ra1_soviets revert settle (hunks interleave in the same files). Flagged: SCUDIrak/V2ExplodeIrak are dead children of the LIVE `SCUD` broadcast (cross-lane, needs Claude ruling). X3 AA rename map intact (`rename_map_x3_aa.yaml`) but its tree edits were wiped — re-apply pending. Log: `60509d3a7`. | `ContentPacks/RedAlert/{Allies,Shared,Japan}/yaml/weapons.yaml` (6 collapsed weapons only) |
| **Devin-Echo** (SWE-1.7 Max) | Active — **review CABAL + Ixian** | Phase 2 Atreides done (`f07d8d35e`); auditing D2k weapons. **ORDER: 1. Review CABAL file after cabal_avatar patch landed (`e1552421f`). 2. Re-verify D2k/Ixian before Phase 4.** | `mods/cameo/ContentPacks/D2k/Atreides/`, `D2k/Ordos/`, `D2k/Ixian/`, `TiberianSun/CABAL/` |
| **Devin-Blaze** | Active — **D2k Shared consolidation** (maintainer priority) | Phase 1 Harkonnen complete (`afdaae46c`); Phase 4 shared/global. **ORDER: move remaining shared D2k content into `ContentPacks/D2k/Shared/`. Clean up legacy `d2k.yaml`/`rules/d2k.yaml` dead blocks. Verify no dangling refs.** | `mods/cameo/ContentPacks/D2k/Harkonnen/`, `ContentPacks/D2k/Shared/`, legacy `mods/cameo/weapons/d2k.yaml`, `mods/cameo/rules/d2k.yaml` |
| **Devin-Nova** (Devin CLI, SWE-1.7 Max) | Active — verifier/generator lane | Committed `7557c983d` (AreaDamageWarhead C# NRE fix), `b905d7679` (BulletChem generator spec), `85bcf3f33` (Claude's reference-pipeline tooling). **Relayed heaviness bell ruling.** ORDER: composite-registry re-curation (fixes `three_way_split` crash on `wc2deathknightFire` stale digest). `gen_weapon_template.py` REFLECTOR 75→74 sync. Help Ember. | `OpenRA.Mods.Cameo/Warheads/AreaDamageWarhead.cs`, `tools/balance/gen_weapon_template.py` |
| **Claude-Cloud** (Anthropic, cloud container) | Active — **rebase your branches** | Patches landed locally by Aurora. ORDER: rebase `claude/*` against current branch; extract specific files only, do NOT merge wholesale. | `claude/*` branches |


---

## ⭐ STANDING ORDERS — issued by Claude-Local, 2026-09-05 (maintainer put me in coordination)

The maintainer has asked me to coordinate this team and to review work as it completes.
These orders supersede any conflicting instruction in a SUPERSEDED table lower in this file.

### How we work (read once, then follow it)

1. **Your lane is exclusive.** Every incident today came from two agents needing one file —
   not from missing review. If your task needs a file outside your lane, **do not edit it**:
   post the request in `DEVELOPMENT_LOG.md` and I will reassign or arbitrate.
2. **You do NOT wait for me to commit.** Seven agents queued behind one reviewer has a
   throughput of one. Verify with the mechanical gates and commit:
   `find_empty_warhead.py` = 0, `audit_duplicate_inherits.py` exit 0,
   `audit_warhead_split.py` at or below its ratchet, `audit_balance_drift` clean,
   **and the boot gate** (`launch-game.cmd` reaching the main menu, no new `exception-*.log`).
   Scoped `git add <files>` only. Sign with your OWN `Co-Authored-By:`.
3. **When you finish, say so in `DEVELOPMENT_LOG.md` and paste the OUTPUT of your verify
   commands, not a summary of it.** I re-run them independently. I am not being pedantic:
   today produced four confidently-wrong claims, including two of my own
   ("MO is not recoverable", "CnC Reloaded is unextractable"). Claims here decay in hours.
4. **Never re-extract or hand-edit a balance number.** `extract_stats.py` -> ledger ->
   `apply_balance --confirm` (maintainer order only).
5. ⛔ **`git grep` and `miniyaml` BOTH silently under-read our weapons yaml** — several files
   carry non-UTF-8 bytes, so `git grep` skips them as binary and a miniyaml node count comes
   back short. For any presence/absence check use `git show <rev>:<file> | grep -a`.
   This nearly cost 30 live weapon nodes during the master merge.

### Ownership, de-conflicted (this replaces the overlapping claims)

Three stale tables in this file assigned D2k/Harkonnen to **two** agents and named **two**
different coordinators. Resolved against §3.A and against who has actually been committing:

| agent | lane — EXCLUSIVE | explicitly NOT yours |
|---|---|---|
| **Devin-Dawn** | `ContentPacks/D2k/Corrino/**`, `mods/cameo/weapons/tiberiansun.yaml` | Harkonnen, Atreides |
| **Devin-Aurora** | `ContentPacks/D2k/Atreides/**`, `ContentPacks/D2k/Ordos/**`, `bits/d2k/**`, `D2k/Shared/yaml/weapons.yaml` | the rest of `D2k/Shared/` (Blaze), Ixian (Echo) |
| **Devin-Cyrus** | `ContentPacks/Warcraft2/Humans/**`, `Warcraft2/Orcs/**` | **D2k/Harkonnen — that is Blaze's, despite the stale tables** |
| **Devin-Echo** | `ContentPacks/D2k/Ixian/**`, `TiberianSun/CABAL/**` | Atreides, Ordos (Aurora's) |
| **Devin-Blaze** | `ContentPacks/D2k/Harkonnen/**`, `D2k/Shared/**` except `yaml/weapons.yaml`, legacy `weapons/d2k.yaml`, `rules/d2k.yaml` | — |
| **Devin-Nova** | `OpenRA.Mods.Cameo/Warheads/**`, `tools/balance/gen_weapon_template.py`, `mods/cameo/weapons/weapons.yaml` | — |
| **Devin-Ember** | `ContentPacks/RedAlert/{Allies,Shared,Japan}/yaml/weapons.yaml` — assigned broadcast collapses only | other agents' in-flight sweeps in those files |
| **Claude-Local** | `tools/reference/**`, `tools/balance/{assign_references,faction_routes,faction_extrapolate}.py`, `docs/balance/review/**` | all `ContentPacks/**`, all `mods/cameo/weapons/**` |

### Orders, in priority order

**~~P0 — Devin-Cyrus: COMMIT THE WC2 HERO PASS~~ — RESOLVED (2026-09-06, Aurora verification)**
The WC2 hero pass was committed by the maintainer as `d11b90720` on 2026-08-25
("Picks up Devin-Cyrus's unfinished work"). Verified: hellscream + elite actors,
weapons, sequences, and icon all present. Dawn is **unblocked** for Corrino Phase 3.

**~~P0 — Devin-Nova: two correctness items~~ — RESOLVED (2026-09-06)**
1. ✅ **`weapons.yaml.rej` — DELETED.** `Test-Path` = False. REFLECTOR 75 stands, gen_sync drift = 0.
2. ✅ **`^Warhead_CannonTesla_*` — KEEP BOTH.** Nova's forensic (`a636756e5`) proved
   CannonTesla is a distinct generator-defined BLEND (50% Tesla + CannonAP), not a
   duplicate. Resolved rows differ from `^Warhead_Tesla_*` throughout. Sole consumer
   `RA2120mm_tesla` is coherent authored content. `audit_family_uniqueness` passes.
   The 0-reference `_Medium`/`_Heavy` levels are unused levels like any leveled family.

**P1 — Devin-Ember: own the red gates.** Run `bash tools/audit/run_all.sh` on a complete tree
and triage. `audit_doc_claims` is now **fully green (19/19)** — `ledgers_drifted` is 0 after the D2k re-extract, and `meters_filling_before_death` (269) and `multi_main_fired_weapons` (192) both match the committed tree. `audit_doc_health` D1 control chars in `DEVELOPMENT_LOG.md` are CLEAN (Aurora cleaned them 2026-09-06). Remaining D1 findings are 4 non-UTF-8 files in Claude-Local's reference docs (`scout_references.md`, `FACTION_REFERENCE_MATRIX.md`, `RTS_BALANCE_REFERENCE.md`, `WARHEAD_REFERENCE.md`) — route to Claude. ⚠ Read the `exit=` line in the output file; never trust
a background task's notification code.

**P1 — Devin-Blaze, Devin-Aurora, Devin-Echo, Devin-Dawn: D2k faction completion** — the
maintainer's standing priority. Stay strictly in the lanes above. ~~Dawn is gated on Cyrus (P0)~~ — **Cyrus P0 RESOLVED, Dawn is UNBLOCKED for Corrino Phase 3.**

⛔ **Maintainer ruling for everyone, 2026-09-05:** the EBFD sprites were to be added as **NEW
actors only**; the **Ordos Face Dancer was the sole approved update to an existing actor.** An
audit found six pre-existing actors had their art changed — `combat_tank.harkonnen` was
repointed from `DATA.R16` to `harkonnen_assaulttank.png` with **no new actor created**, and its
husk followed. Ruled: **revert `combat_tank.harkonnen` + husk to `DATA.R16`** and wire
`harkonnen_assaulttank.png` to a genuinely new T2 Harkonnen heavy when the balance pipeline can
price it. `harkonnen_devestator.png` also carries a typo (devEstator). **Blaze owns this.**

**P2 — nobody claim these yet:** the heaviness-bell rollout stays OFF until W24 closes
(maintainer, today). Do NOT create new leveled families; do NOT flip `USE_BELL`.

### What I am doing, so nobody duplicates it

The reference/faction-routing lane. **Order item 3 is delivered:** 7 reference mods extracted to
`Cameo-mod-reference/extraction/` — 8183 unit rows, 1695 armor profiles (Rise of the East,
RA20XX, Mental Omega, CnC Reloaded, Red Resurrection, DTA Classic+Enhanced, RA2 Reborn). The
`REFERENCE_PIPELINE_HANDOFF.md` §1.3 claim that MO/CnCR data is "not recoverable" was wrong.
Next: an INI->corpus extractor so those rows reach `assign_references.py`, then per-class review
sheets. I also fast-forwarded `master` 113 commits — the UnitsToBuild merge-order blocker is gone.

#### Locked files (DO NOT TOUCH — another agent owns these)

- `mods/cameo/weapons/weapons.yaml` — template generator/family work; needs explicit sign-off. **Maintainer's Versus tweaks (HAZMAT/COMPOSITE/BLAST/REFLECTOR adjustments) are committed and final — do NOT revert.**
- `mods/cameo/weapons/tiberiansun.yaml` — Devin-Dawn owns TSLaser90mm family work.
- `mods/cameo/weapons/tiberiandawn.yaml` — may be open in an IDE tab.
- `mods/cameo/ContentPacks/TiberianDawn/GDI/yaml/weapons.yaml` — may be open in an IDE tab.
- `mods/cameo/ContentPacks/RedAlert/Shared/yaml/weapons.yaml` — Devin-Dawn owns ATMine.
- `mods/cameo/ContentPacks/RedAlert/Soviets/yaml/weapons.yaml` — **maintainer edit in progress** (KotinCannonNuclearShell cleanup). Aurora fixed `^Warhead_CannonTesla_Light` → `^Warhead_Tesla_Light` ref here.
- `mods/cameo/ContentPacks/RedAlert2/Soviets/yaml/weapons.yaml` — Aurora fixed missing `^Warhead_CannonTesla_Light` template ref (changed to `^Warhead_Tesla_Light`). **Do NOT revert this fix.**
- `mods/cameo/ContentPacks/D2k/Ordos/yaml/weapons.yaml` — Devin-Echo owns D2K_APC_Rocket. **Maintainer added `ordos_laserturret` and `ordos_chemturret` actor definitions to `buildings.yaml` — these are final.**
- `mods/cameo/ContentPacks/D2k/Ixian/yaml/weapons.yaml` — Devin-Echo owns MongooseRocket/facedancer_grenade. **Uncommitted WIP — re-verify before Phase 4.**
- `mods/cameo/ContentPacks/Warcraft2/Humans/yaml/weapons.yaml` — Devin-Cyrus owns Alleria fix.
- `mods/cameo/ContentPacks/Warcraft2/Orcs/yaml/weapons.yaml` — Devin-Cyrus owns Hellscream.
- `mods/cameo/ContentPacks/TiberianSun/CABAL/yaml/weapons.yaml` — Devin-Echo owns CABAL collapses. **Aurora removed orphaned `-Warhead@MissileHE_Light:` at line 2026 (CabalManticoreMissilesAA) to unblock boot.**
- `mods/cameo/ContentPacks/RedAlert/Japan/yaml/weapons.yaml` — **Aurora removed orphaned `-Warhead@Bullet_Light:` at line 1621 (HovercraftPlasmaCannon) to unblock boot.**
- `mods/cameo/ContentPacks/RedAlert2Mod/SchwarzerMond/yaml/weapons.yaml` — **maintainer W24 collapses committed and verified (Bullet_Light+Bullet_Medium → Bullet_Medium). Do NOT revert.**

#### Unassigned tasks for the next available agent (Devin-Blaze or anyone free)

1. **~~StarCraft Protoss/Zerg bullet collapses~~** — **NO CANDIDATES FOUND.**
   Re-scanned 2026-09-05 by Devin-Aurora: zero weapons with 2+ same-family
   damage mains and positive Damage values in any StarCraft weapons.yaml.

2. **~~RedAlert2Mod/Naxis bullet collapses~~** — **DONE** by Devin-Aurora.

2b. **~~RedAlert (RA1) Allies + Soviets same-family collapses~~** — **DONE** by Devin-Aurora.

3. **~~RedAlert2Mod/Consortium missile/cannon collapses~~** — **NO CANDIDATES FOUND.**
   Re-scanned 2026-09-05 by Devin-Aurora: zero W24 candidates in Consortium.

4. **~~Audit/RedAlert2 dead-code cleanup~~** — **DONE.** `mods/cameo/weapons/redalert2.yaml`
   is marked DEPRECATED (line 4), load entry commented out in `mod.yaml` line 307.
   Verified dead: 0 unique templates, 0 unique weapons (Devin-Aurora 2026-08-25).

5. **W23 retrofit candidates** — **ALL DONE** (see `docs/audit/latest/phase_b_survey.md`):
   - ~~`ordos_laserturret` (D2k/Ordos)~~ — **DONE** by Devin-Aurora (`9cdfa40dd`). Converted from `^LaserWeapon` to `^Warhead_Laser_Heavy` + `^Projectile_Laser_Heavy` + `^Effect_Laser_Heavy`. Damage 10000 preserved verbatim.
   - ~~`HydraSpit` (StarCraft/Zerg)~~ — **DONE** by Devin-Aurora (`8748c68e4`). Converted from 4 old families (^LightChemicalWeapon, ^LightMissile, ^SmallArms, ^ArrowWeapon) to single ^Warhead_BulletChem_Light. Damage 18000 preserved verbatim. Generator spec landed by Nova (`b905d7679`).

**W24 safe pool status (2026-09-05): EXHAUSTED.** `plan_warhead_collapse.py` reports 193 directly actor-armed multi-main weapons, but the 85 HIGH-confidence weapons still carry mixed old families and compatibility warheads (e.g. `CommandoM16`, `DuelistTankCannon`). The plan explicitly warns that numeric-sum preservation does not preserve armor profile, geometry, relationships, or damage types, so these are design-review items, not safe mechanical collapses. `phase_b_survey` now shows 0 remaining concrete old-family weapons (both `ordos_laserturret` and `HydraSpit` DONE) and `find_mechanical_phase_a` reports 0 clean single-inherit candidates. The front moves to maintainer sign-off / ownership.

**⚠ NEW MAINTAINER RULING (2026-09-05, relayed by Devin-Nova):** *"we will only have a single warhead per type and no more light, medium and heavy! it will all be done with the heaviness bell curve!"* — The Light/Medium/Heavy level system is a TRANSITION state, not the target. The target: one `^Warhead_<Family>` per type, level behavior derived by the `Heaviness` bell transform. Do NOT create NEW leveled families. W23/W24 collapse queues still apply. The BulletChem family (commit `8748c68e4`) predates this ruling; whether it stays leveled or is refolded under heaviness is a later-wave decision.

6. **D2k faction completion** (Atreides/Harkonnen/Corrino) — see §3.7 below.
   This is the maintainer's priority task. All three factions are selectable but
   need unique weapons, full tech trees, and faction-specific actors.

---

### 3.7 — Dune 2000 faction completion: Atreides, Harkonnen, Corrino (2026-08-25)

⭐ **PRIORITY TASK — maintainer order 2026-08-25.** The three remaining D2k factions
must be fully built out so they are selectable and playable. Currently:

| faction | state | units | buildings | infantry | aircraft | weapons | upgrades | selectable |
|---|---|---|---|---|---|---|---|---|
| **Atreides** | FEATURE-COMPLETE (Aurora) | 11 vehicles (MCV, harvester, combat, sonic, missile, siege, sandbike, APC, repair, minotaurus, mongoose) | 15 (full set) | 4 (lightinfantry, rockettrooper, fremen, engineer) | 3 (ornithopter, airdrone, advanced carryall) | `weapons.yaml` active (155 lines, `876226947`) | 5 | **yes** (FactionCA active, StartingUnits set) |
| **Harkonnen** | complete in `afdaae46c` | 5+ (MCV, harvester, combat, missile, devastator, MCV) | full set | 3 (lightinfantry, rockettrooper, engineer) | 1 (carryall) | `weapons.yaml` active | 5+ | **yes** (FactionCA active, StartingUnits set) |
| **Corrino** | complete in `af3ff5f9d` | 5 (MCV, harvester, combat, buggy, BMP) | 13 | 3 (lightinfantry, engineer, sardaukar_bazooka) | 2 (carryall, transport) | active | 5 | **yes** (FactionCA active, StartingUnits set) |
| Ixian (reference) | complete | 16 | 18 | 6 | 11 | 32KB | 9 | yes |
| Ordos (reference) | complete | 17 | 16+ | 9 | 13 | 28KB | 11 | yes |

**Phase 0 boot-gate:** passed. The canonical rollout plan and agent instructions are in §3.B below. The table above is a snapshot; §3.B is the authoritative task queue.

**Reference templates:** use Ixian and Ordos as the structural pattern. Every
faction needs: `content.yaml`, `yaml/faction.yaml` (with `FactionCA@<Name>` and
`StartingUnits@<name>` entries), `yaml/buildings.yaml`, `yaml/infantry.yaml`,
`yaml/vehicles.yaml`, `yaml/aircraft.yaml`, `yaml/weapons.yaml`, `yaml/upgrades.yaml`,
`yaml/sequences.yaml`, `yaml/ai.yaml`, `translations/en.ftl`.

**D2k Shared content** (`ContentPacks/D2k/Shared/yaml/`): buildings (concrete slabs,
walls, oil derrick), vehicles (siege_tank, sandworm), infantry (light_inf, trooper,
fremen_creep, engineer). These are shared across all D2k factions — do NOT duplicate
them in faction packs. Reference them via `ProvidesPrerequisite` and `Buildable:
Prerequisites: ~d2k_barracks` etc.

#### Agent assignments for D2k faction completion


> ⛔ **SUPERSEDED — this ownership table is STALE. The single authoritative roster is
> §3.A "Agent roster and current assignments".** It is kept only as provenance; it
> contradicts §3.A on who owns D2k/Harkonnen and on who the coordinator is. Do NOT
> claim a file-set from this table.

| agent | faction | file-set | scope of work |
|---|---|---|---|
| **Devin-Aurora** (this agent) | **Atreides** (stub) | `mods/cameo/ContentPacks/D2k/Atreides/**` | Nearly everything needs to be built. Add: full building set (barracks, light factory, repair pad, outpost, gun turret, rocket turret, high tech factory, research center, starport, palace), infantry (light_inf, trooper, engineer, Fremen, kinjal), vehicles (MCV, spice harvester, combat tank, missile tank, sonic tank, trike/raider), aircraft (ornithopter, carryall), weapons, upgrades, sequences. Uncomment `FactionCA@Atreides` and set `Selectable: true`. Port Atreides-specific units/weapons/sequences from legacy `mods/cameo/weapons/d2k.yaml` and `mods/cameo/sequences/d2k.yaml`. |
| **Devin-Cyrus** | **Harkonnen** (partial) | `mods/cameo/ContentPacks/D2k/Harkonnen/**` | Buildings exist (16, full set). Add: infantry (light_inf, trooper, engineer, sardaukar), aircraft (carryall, gunship), upgrades (at least 5-8), more vehicles (siege tank via Shared, flame tank), weapons for new units, sequences for new units. Set `FactionCA@Harkonnen: Selectable: true` (currently false). Port remaining Harkonnen units from legacy `d2k.yaml` / `rules/d2k.yaml` / `sequences/d2k.yaml`. |
| **Devin-Dawn** | **Corrino** (new) | `mods/cameo/ContentPacks/D2k/Corrino/**` (create from scratch) | Create the entire faction directory + all yaml files. Copy the Ordos pack skeleton. Corrino is the Imperial faction: Sardaukar elite infantry, combat tank, missile tank, siege tank, carryall, palace with Death Hand support power. Register in `mod.yaml` (add `Include: ContentPacks/D2k/Corrino/content.yaml`). Set `FactionCA@Corrino: Selectable: true`. Add `StartingUnits@corrino` entries (already exist in Ixian faction.yaml as a placeholder using ixian MCV — replace with corrino MCV once created). |
| **Devin-Blaze** | **D2k Shared + legacy consolidation** | `mods/cameo/ContentPacks/D2k/Shared/yaml/**`, `mods/cameo/weapons/d2k.yaml`, `mods/cameo/rules/d2k.yaml` | Move all D2k units/weapons/sequences used by multiple factions into `ContentPacks/D2k/Shared/yaml/`. Update `Shared/content.yaml`. Remove or comment out dead blocks from legacy `d2k.yaml` and `rules/d2k.yaml` once content has moved. Verify no `Parent type ... not found` or dangling refs. |
| **Devin-Echo** | **coordinator** | verification & ledger sync | Maintain the plan in `DEVELOPMENT_LOG.md` and `HANDOFF.md`. Run `extract_stats`, `audit_doc_claims`, `audit_warhead_split`, and `find_empty_warhead` after each phase. Boot-gate the integrated tree. Commit each pack in a scoped batch. |

#### D2k faction unit rosters (from Dune 2000 source game)

**Atreides** (noble, air superiority, Fremen allies):
- Buildings: construction yard, wind trap, barracks, refinery, silo, light factory,
  heavy factory, repair pad, outpost, gun turret, rocket turret, high tech factory,
  research center, starport, palace
- Infantry: light infantry, trooper (rocket), engineer, Fremen, kinjal soldier
- Vehicles: MCV, spice harvester, combat tank, missile tank, sonic tank, trike/raider
- Aircraft: ornithopter (air superiority), carryall, gunship
- Upgrades: upgrade_conyard, upgrade_barracks, upgrade_lightfactory,
  upgrade_heavyfactory, upgrade_radar, upgrade_hightech
- Support powers: Ornithopter Airstrike, Fremen Guerilla

**Harkonnen** (brute force, atomic weapons):
- Buildings: already has 16 (full set) — verify completeness
- Infantry: light infantry, trooper, engineer, sardaukar (elite)
- Vehicles: MCV (has), combat tank (has), missile tank (has), devastator (has),
  siege tank (Shared), flame tank
- Aircraft: carryall, gunship
- Upgrades: upgrade_conyard, upgrade_barracks, upgrade_lightfactory,
  upgrade_heavyfactory, upgrade_radar, upgrade_hightech
- Support powers: Death Hand Missile

**Corrino** (imperial, Sardaukar):
- Buildings: construction yard, wind trap, barracks, refinery, silo, light factory,
  heavy factory, repair pad, outpost, gun turret, rocket turret, high tech factory,
  research center, starport, palace
- Infantry: light infantry, trooper, engineer, Sardaukar (elite imperial guard)
- Vehicles: MCV, spice harvester, combat tank, missile tank, siege tank (Shared)
- Aircraft: carryall
- Upgrades: upgrade_conyard, upgrade_barracks, upgrade_lightfactory,
  upgrade_heavyfactory, upgrade_radar, upgrade_hightech
- Support powers: Imperial Sardaukar reinforcement

#### Build order for all agents (parallel-safe)

1. **Phase 1 — scaffolding (Devin-Cyrus first, then all parallel):**
   - Devin-Cyrus: create `Corrino/` directory + `content.yaml` + register in `mod.yaml`.
   - All agents: create your faction's `faction.yaml` with `FactionCA` (Selectable: true)
     and `StartingUnits` entries.
   - Boot-gate after scaffolding to verify no crash.

2. **Phase 2 — buildings (parallel):**
   - Each agent builds their faction's `buildings.yaml`.
   - Use Ixian/Ordos buildings as the structural template (inherit `^D2KBuilding`,
     `^D2kUpgradeable`, `^D2KPaletteRender`, etc.).
   - Gate with `Prerequisites: ~<faction>_constructionyard` etc.
   - Boot-gate after buildings.

3. **Phase 3 — infantry + vehicles (parallel):**
   - Each agent builds their faction's `infantry.yaml` and `vehicles.yaml`.
   - Use D2k Shared infantry (light_inf, trooper, engineer) as the base — faction
     variants inherit from Shared or from `^D2KInfantry`.
   - Vehicles inherit from `^D2KTank`, `^CombatTank`, `^MainBattleTankTemplate`, etc.
   - Boot-gate after infantry + vehicles.

4. **Phase 4 — aircraft + weapons (parallel):**
   - Each agent builds their faction's `aircraft.yaml` and `weapons.yaml`.
   - Use the 3-way weapon split (`^Warhead_*`, `^Projectile_*`, `^Effect_*`).
   - Boot-gate after aircraft + weapons.

5. **Phase 5 — upgrades + sequences + AI (parallel):**
   - Each agent builds their faction's `upgrades.yaml` and `sequences.yaml`.
   - Devin-Cyrus wires AI build lists and regenerates the faction matrix.
   - Boot-gate after upgrades + sequences + AI.

6. **Phase 6 — final verification:**
   - All agents: `find_empty_warhead.py = 0`, `audit_doc_claims` green,
     `extract_stats --check` 0 drifted.
   - Boot-gate with all three factions selectable.
   - Regenerate `docs/factions/MATRIX.md`.
   - Update `DEVELOPMENT_LOG.md` with completion summary.

#### Critical rules for faction creation

- **Do NOT edit another agent's faction files.** Each agent owns exactly one
  faction's file-set. Devin-Blaze owns D2k/Shared only. Devin-Cyrus owns
  registration/AI files only.
- **Use the 3-way weapon split** for all new weapons (`^Warhead_*`, `^Projectile_*`,
  `^Effect_*`). No inline `Versus` — it lives only in `^Warhead_*` templates.
- **Use `^D2KPaletteRender`** for D2k sprites (palette: `d2kunit` or `playerd2k`).
- **Sequence files** must use `Filename: DATA.R16` with `Scale: 1.5` and
  `Remap: 54F94B` for D2k sprites (see existing Atreides/Harkonnen sequences).
- **Boot-gate after every phase.** The game must reach the main menu with no new
  `exception-*.log` files.
- **Scoped `git add` only.** Each agent commits only their own faction's files.
- **Naming convention:** `<faction>_<unitname>` (e.g. `atreides_lightinfantry`,
  `harkonnen_sardaukar`, `corrino_combattank`). Shared units keep their base
  name (e.g. `light_inf`, `siege_tank`).
- **Balance numbers** must go through the pipeline (`extract_stats` → ledger →
  `apply_balance --confirm`). Do NOT hand-edit balance values. For initial
  creation, use the same damage/HP/cost values as the equivalent Ixian/Ordos unit.

### 3.B — D2k Faction Rollout: Atreides / Harkonnen / Corrino (NEW — 2026-08-25)

**Coordinating agent:** Devin-Aurora (this session).
**Goal:** make Atreides, Harkonnen, and Corrino fully playable, self-contained Dune factions with **completely unique tech trees and no shared units/assets** with each other or with the existing Ixian/Ordos factions. This supersedes the older draft in `DEVELOPMENT_LOG.md` §"D2k faction rollout plan" because the user has now supplied harvester sprites and explicitly required uniqueness and asset isolation.

**New assets already in the repo (Phase 0):**
- `mods/cameo/bits/d2k/atreides_harvester.png` — 32-frame strip, 98×98 px/frame: 8 idle facings + 3 frames × 8 facings harvesting.
- `mods/cameo/bits/d2k/harkonnen_harvester.png` — 192-frame strip, 200×150 px/frame: 8 frames × 8 facings move, 64 one-frame idle facings, 8 frames × 8 facings harvest.
- No absolute local paths are recorded in any repository document.

**Agent assignments and detailed instructions:**

| Phase | Owner | File-set | What to build | Acceptance |
|---|---|---|---|---|
| **0 — Foundation** | **Devin-Aurora** (committed `f07d8d35e`) | `ContentPacks/D2k/Atreides/`, `ContentPacks/D2k/Harkonnen/`, `mods/cameo/bits/d2k/` | Wire the maintainer-supplied harvester PNGs (`atreides_harvester.png` and `harkonnen_harvester.png`) as `atreides_spiceharvester` and `harkonnen_spiceharvester` (actors + sequences + refinery `FreeActor`). Create `Atreides/yaml/weapons.yaml` and `Atreides/yaml/promotions.yaml` and load them from `Atreides/content.yaml`. Fix Atreides `^D2KVehicleHusk`/`^UpgradeTemplate` parents and `IconPalette` indentation. Do **not** enable `Selectable` yet. | `launch-game.cmd` reaches main menu with no new `exception-*.log`; commit `f07d8d35e`. |
| **1 — Harkonnen** | **Devin-Blaze** (committed `afdaae46c`) | `ContentPacks/D2k/Harkonnen/` | Complete Harkonnen as a brute-force, heavy-vehicle faction. Infantry (`harkonnen_lightinfantry`, `harkonnen_rockettrooper`, `harkonnen_engineer`), aircraft (`harkonnen_carryall`), vehicles, buildings, upgrades, sequences, StartingUnits (MCV/Light/Heavy). Replace remaining `ordos_*`/`ixian_*`/generic art refs as new `harkonnen_*` assets arrive. | Boot-gate passed; `utility.cmd cameo --check-yaml` follow-up for final lint. |
| **2 — Atreides** | **Devin-Aurora** (committed `f07d8d35e`) | `ContentPacks/D2k/Atreides/` | Complete Atreides as a noble/air/Fremen faction. Full building set, 4 infantry, 5 vehicles, ornithopter, 5 upgrades, sequences, StartingUnits (MCV/Light/Heavy). Theme: air superiority, faster construction, Fremen. | Same as phase 1. |
| **3 — Corrino** | **Devin-Cyrus** → **Devin-Aurora** (completed `af3ff5f9d` + `d519ceaf6`) | `ContentPacks/D2k/Corrino/` | Corrino is imperial/Sardaukar: 3 infantry, 5 vehicles (MCV, harvester, combat tank, buggy, BMP), 2 aircraft, 13 buildings, 5 upgrades, weapons, sequences, StartingUnits, translations. | Boot-gate passed; Phase 4 shared/global pass now active. |
| **4 — Shared/global pass** | **Devin-Aurora** + **Devin-Blaze** + **Devin-Echo** (IN PROGRESS) | `ContentPacks/D2k/Shared/yaml/`, `mods/cameo/weapons/d2k.yaml`, `mods/cameo/rules/d2k.yaml` | Add shared templates, fix cross-faction prerequisites, walls/turrets/superweapons/promotions. Remove dead legacy blocks from `mods/cameo/weapons/d2k.yaml` and `mods/cameo/rules/d2k.yaml`. Run `find_empty_warhead.py`, `review_resolve_diff`, `audit_warhead_split`, `extract_stats --check`, full `run_all.py`, and boot-gate. | All audits green; `multi_main_fired_weapons` not inflated. |

**Hard constraints for every phase owner:**
1. **Unique and isolated.** Every actor, weapon, sequence, icon, and building in a new faction is prefixed with the faction name and lives inside that faction's pack. No references to `ordos_*`, `ixian_*`, or generic shared actors except through intentionally shared `^D2K*` templates in `ContentPacks/D2k/Shared/yaml/templates.yaml`.
2. **Assets in the repo only.** All new `.png`/`.shp` files go under `mods/cameo/bits/d2k/<faction>/` (or `ContentPacks/D2k/<Faction>/files/` if the `mod.yaml` package is updated). No absolute local paths in docs.
3. **W24 weapons.** Every new weapon has one main damage warhead. Run `find_empty_warhead.py`, `audit_warhead_split.py`, and `review_resolve_diff.py` per batch.
4. **Harvester rule.** Every refinery spawns `<faction>_spiceharvester` via `FreeActor`/`FreeActorWithDelivery`.
5. **Do not flip `Selectable: true` prematurely.** A faction is only selectable when it has a full minimum viable tech tree: con yard, wind trap, refinery, harvester, barracks, light vehicle factory, MCV, one anti-ground unit, and `StartingUnits`.
6. **Boot-gate and scoped commits.** `launch-game.cmd` before every commit; `git add <files>` only; never `-A`.

#### How to coordinate after every step

1. **Before editing**: check `DEVELOPMENT_LOG.md` §"Active claims" for file ownership.
2. **After editing**: add an entry to `DEVELOPMENT_LOG.md` with:
   - Your agent name
   - What file(s) you edited
   - What weapons you converted
   - Why you made each decision (which rule, which pattern, which precedent)
   - Verification results (find_empty_warhead, audit_warhead_split, review_resolve_diff)
   - What's next
3. **Before committing**: verify no other agent has uncommitted work in your file set
   (`git status --short` + `git diff --name-only`).
4. **After committing**: update your claim in `DEVELOPMENT_LOG.md` to say "COMMITTED"
   with the commit hash.

#### Devin-Prime handoff message (2026-08-25)

I am **Devin-Prime**, the agent that handled W24 A14. My work is currently in handoff. The
A14 changes are verified and staged in the history, but the working tree also contains
uncommitted work from other agents (D2k/Ordos `D2K_APC_Rocket`, `redalert2mod.yaml`, `d2k.yaml`,
Warcraft2 hero weapons, the rename map, and the `BROADCAST_BASELINE` 876 ratchet). **Do not**
`git add -A`; wait for each owning agent to finish and then commit in scoped batches.

If you are the next agent and your file-set is free, the safest next picks are in the
"Unassigned tasks" list above — especially the **StarCraft Protoss/Zerg bullet collapses** or
**RedAlert2Mod/Naxis** — because they are not currently claimed. If you touch a claimed or
locked file, first read `DEVELOPMENT_LOG.md` "Agent identity & handoff" and the latest
`git status --short` to see who owns it.

My single emergency exception: I had to repair `ContentPacks/Warcraft2/Humans/yaml/weapons.yaml`
because the new `wc2_orcs_zuljin_spear` inherited a missing `wc2_humans_alleria_arrow`, which
caused `OpenRA.YamlException: Parent type ... not found` and blocked the boot-gate. Devin-Forge
owns Warcraft2 and has since refined the Alleria numbers; I will not modify that file set again.

#### The established W24 bullet-collapse pattern (follow this exactly)

When a weapon has `Bullet_Light` + `Bullet_Medium` as two damage mains:
1. Drop `Inherits@wh: ^Warhead_Bullet_Light` (or `Inherits@wh2: ^Warhead_Bullet_Light`).
2. Repoint the remaining `Inherits@wh2: ^Warhead_Bullet_Medium` to `Inherits@wh`.
3. Remove the `Warhead@Bullet_Light:` block.
4. Sum the damage: `Warhead@Bullet_Medium: Damage: <Light + Medium>`.
5. Preserve any local `PercentageScale` on the surviving warhead — if the old
   Bullet_Light had a different `PercentageScale`, preserve the effective percentage
   (ask the formula: `actual_percent = Damage / 10000` regardless of `PercentageScale`).
6. Check children: if a child inherits this weapon, verify it doesn't override the
   old `Warhead@Bullet_Light` key (orphaned old key = double damage bug).
7. Run `review_resolve_diff.py` against HEAD — only the damage multiset should change.
8. Run `find_empty_warhead.py` — must be 0.
9. Boot-gate before committing.

### 3.C - D2k Atreides / Harkonnen / Corrino (legacy draft - superseded by §3.B)

**Coordinating agent:** Devin-Echo. See full plan and per-agent instructions in `DEVELOPMENT_LOG.md` §"D2k faction rollout plan — Atreides / Harkonnen / Corrino".


> ⛔ **SUPERSEDED — this ownership table is STALE. The single authoritative roster is
> §3.A "Agent roster and current assignments".** It is kept only as provenance; it
> contradicts §3.A on who owns D2k/Harkonnen and on who the coordinator is. Do NOT
> claim a file-set from this table.

| Agent | Pack | Key deliverable | Verification before commit |
|---|---|---|---|
| **Devin-Aurora** | `ContentPacks/D2k/Atreides/` | playable Atreides pack: `weapons.yaml`, unit/sequence/weapon port from legacy `d2k.yaml`/`rules/d2k.yaml`, `Atreides/files/icons/atreides_harvester.png` wired | `review_resolve_diff`, `find_empty_warhead=0`, `extract_stats --check=0`, boot-gate |
| **Devin-Cyrus** | `ContentPacks/D2k/Harkonnen/` | playable Harkonnen pack: complete actors/sequences, `Harkonnen/files/icons/harkonnen_harvester.png` wired | same |
| **Devin-Dawn** | `ContentPacks/D2k/Corrino/` | new Corrino pack created from Ordos skeleton, added to `mod.yaml`, units/sequences ported | same |
| **Devin-Blaze** | `ContentPacks/D2k/Shared/`, legacy `d2k.yaml`, `rules/d2k.yaml` | consolidate shared D2k content, remove dead blocks from `mods/cameo/weapons/d2k.yaml` and `mods/cameo/rules/d2k.yaml` | `audit_duplicate_inherits.py`, `find_orphan_old_keys.py`, boot-gate |
| **Devin-Echo** | coordinator | keep `DEVELOPMENT_LOG`/`HANDOFF` current, run audits, boot-gate final integration, commit scoped batches | full `run_all.py` + boot-gate |

**Rollout order:** Phase 0 inventory → Phase 1 pack content (parallel) → Phase 2 shared consolidation → Phase 3 integration/audits/commits.

### 3.0 — DO THIS FIRST

**a. ✅ RULED 2026-08-23 — the nine "broken ladders" were never broken. Nothing to do.**

`audit_level_ladder` required a family's effective damage to rise Light → Medium → Heavy → Super,
and **no law ever said so.** §12.0d makes the level a TILT, §12.0h makes `Damage` a separate free
knob, and 145 `^Warhead_*` templates carry only a placeholder `Damage: 2000` — the template holds
the SHAPE, the weapon holds the MAGNITUDE. The audit is retired and replaced by
`tools/audit/audit_heaviness_bell.py`.

⭐ **DESIGN §12.0i IS NOW COMPLETE (2026-08-24) — every constant ruled, nothing open.** The
2026-08-23 version of it is superseded in three places:

| | 2026-08-23 | ruled 2026-08-24 |
|---|---|---|
| x-axis | §12.0d's three coarse buckets, then a per-ladder 0..2 | **one global 13-slot scale**, step 1/6, every ladder centred on 1.000, one deliberate three-way tie (`Flak`=`Medium`=`Steel`=1.0) |
| peak | `centre_of_mass + SHIFT*(h-1)`, `SHIFT` 0.25 | **`mu = (h + centre_of_mass)/2`**; `SHIFT` deleted |
| swing | `LO` 0.80 (1.25x) | **`LO` 0.667 (1.50x)** = `1/TILT_RATIO`, so the continuous model keeps the differentiation the discrete tilt already ships |
| `sigma` | unruled, assumed 1.0 | **0.75** |

`audit_heaviness_bell.py` runs the ruled model over 48 families at h ∈ {0, 0.5, 1, 1.5, 2}: **0
ladder orderings changed, 0 weighted-mean drift**, 2 flat families at the ratchet.

⛔ Two 2026-08-23 conclusions are RETRACTED, both from the same cause — measurements taken before
§12.0d's rank restore was implemented in the audit. A tier-anchored peak was rejected for
"inverting 26 of 42 families"; with the restore it inverts **nothing**. And "ship it inert at h=1"
was unachievable under the family-anchored peak (all 48 families reshaped at h=1, worst row 13.5%),
which is why the peak formula changed rather than the requirement.

⭐ **Step 5 is the next action** — implement the bell in `gen_weapon_template.py` (replacing
`class_tilt`), then in `AreaDamageWarhead`. **DONE 2026-08-24:**
- The generator bell is in `tools/balance/gen_weapon_template.py`, OFF by default
  (`USE_BELL` controlled by `CAMEO_HEAVINESS_BELL=1`).
- The `AreaDamageWarhead` C# transform is in `OpenRA.Mods.Cameo/Warheads/HeavinessBell.cs`, wired
  at `RulesetLoaded`. `Heaviness` defaults to `0` (today's behaviour); non-zero values tilt `Versus`
  and `PercentageVersus` through the bell at load time.
- The continuous **Spread** scale is intentionally NOT wired yet — the mapping from `h` to
  `LEVEL_RADIUS_SCALE` (Light 2/3, Medium 1, Heavy 4/3, Super 5/3, Trace 1/2) is a separate design
  ruling and must not be guessed.

The acceptance test is `tools/balance/preview_bell.py` (tilt-to-tilt on the same base, the only
valid comparison): 130 of 136 profiles move, mean 8.3% row change, **0 ladder inversions**, worst
single row 32.0% on `Chemical_Medium`.

**Status 2026-08-24:** `AreaDamageWarhead` now applies the bell to both `Versus`/`PercentageVersus`
AND `Spread` (via `effectiveSpread`) when `Heaviness != 0`. `Spread` scales linearly
`2/3 -> 1 -> 4/3` as `h` goes `0 -> 1 -> 2` (Light/Medium/Heavy), which is the data-driven
interpolation of `LEVEL_RADIUS_SCALE`. `Trace`/`Super` are outside the ruled `h` range and remain
unhandled. No yaml sets `Heaviness` yet, so the change is inert. Both of `WEAPON_HEAVINESS.md` §9.6's original blockers are gone: #1 was retired by the
2026-08-23 ruling, and #2 (every family inside the 2x–8x spread band) had already been finished on
2026-08-22 without the document noticing — `audit_versus_profile` reports 46 in band at
`SPREAD_OFFENDERS_BASELINE = 0`.

⛔ **RETRACTED:** an earlier version of this section listed two permanent "known inversions" and a
gap in §9.4 needing new gradients authored. Both were artifacts of the audit skipping §12.0d's rank
restore. With the restore the bell changes **zero** ladder orderings (without it, 127 across 60
family/ladder pairs). Nothing needs authoring.

⛔ **STILL OPEN, and the reason to start a fresh session on it:** the maintainer wants every armor
to have its OWN unique continuous x — the interim per-ladder form is unique within a ladder but
collides across them (four armors on 0.0, four on 2.0). A global scale means ranking armors ACROSS
ladders, which §12.0d says the tilt is designed to change. Stated in full as an OPEN block in
DESIGN §12.0i. **Do not change the axis before it is ruled.**

**b. Three tooling defects formerly live on master — VERIFIED FIXED 2026-08-24. Fixes were reported in flight on 2026-08-23 from a
Windows session — the fixes landed; this section is now a verified-fixed record.**

| defect | effect | fix |
|---|---|---|
| `tools/audit/environment.py` now points at repo-root `OpenRA.Mods.CA` (fixed) | `OpenRA.Mods.CA` is **vendored at the repo root**, not under `engine/`, `incomplete()` now returns empty on a built tree and `latest/` is writable | `python tools/audit/environment.py` reports `complete environment` |
| `tools/audit/audit_unique_traits.py` `SOURCE_ROOTS` now uses repo-root `OpenRA.Mods.CA` | now scans all 139 trait types; CA path verified correct | `grep SOURCE_ROOTS` confirms the vendored path |
| `audit_doc_health` D8 no longer flags its own fixtures | `tools/tests/test_audit_doc_health.py` excludes `tools/tests/` and `tools/audit/audit_doc_health.py` from the D8 scan | `python tools/audit/audit_doc_health.py` **PASS** (0 D8 findings) |

`audit_dead_warhead_fields.py` and `audit_code_duplication.py` already had the CA path right, and
a sweep of `tools/**/*.py` finds no third instance — those two are the whole set.

⭐ Both of the second and third defects were introduced by the change that added the gate, and both
were "verified" before landing. How, is in [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md): a grep whose
filter excluded exactly the lines that would have disproved it, and a tracked-file scan run while
the new file was still untracked.

**c. `docs/audit/latest/` regenerated 2026-08-24 from a complete tree.**

Regenerated with `python tools/audit/run_all.py` (bash unavailable on this Windows shell) from a
complete tree (`engine/` built, `OpenRA.Mods.CA` at repo root, not shallow). The suite exited 1 on
the same pre-existing gating failures (`inherits`, `upgrades`, `sequences`, `fluent`,
`basebuilder_crates`, `buildable_order`, `weapon_suffixes`, `impact_glow_preservation`); the report
set is now a single-environment snapshot.

`run_all` now writes to `docs/audit/latest/` because `environment.py` no longer mis-reports
incomplete. The note below about `bash tools/audit/run_all.sh` is the canonical command; the Python
port `run_all.py` is equivalent and was used here. On a machine with `engine/` built:

```sh
git fetch --unshallow          # if the clone is shallow
bash tools/audit/run_all.sh    # writes latest/ only from a complete tree
```

Commit the result **whole**. Do not cherry-pick report files: Windows writes `mods\cameo\…` and
Linux writes `mods/cameo/…`, so a cross-platform diff is dirty even between two complete trees.

⚠ The suite also rewrites TRACKED files **outside** `audit/latest/` — `docs/factions/MATRIX.md`
and `tools/rename/rename_map_*.yaml` (`gen_rename_maps.py` writes those as a side effect of the
naming report). So `git status` after a suite run is not expected to be clean, and those files
belong in the same commit.

⚠ **Previous items here are DONE.** The 9 drifted balance ledgers (`31e649b8`), the 4 drifted doc
claims (`audit_doc_claims` is **19 of 19**), and the memory-citation promotion — **zero**
`memory <name>` pointers remain in the live document set; the two load-bearing ones were inlined
into `weapon_classes.yaml`'s header and `BALANCE_PROGRAM_PLAN.md` §7.

```sh
python tools/audit/audit_heaviness_bell.py  # WARN 2 flat, 0 inversions, 0 drift
python tools/audit/audit_doc_health.py     # PASS
python tools/audit/environment.py          # should print "complete" on a built tree
```

### 3.0c — What the suite's exit code does and does not mean (2026-08-24)

⛔ **Do not re-read a background task's notification exit code as the script's.** It reports the
wrapper (`cmd; echo "exit=$?"`), which is 0 whenever the trailing `echo` succeeds — i.e. always.
That is how "the suite is green" was reported repeatedly while `run_all.sh` was exiting 1 on every
run. Write `echo "exit=$?" >> "$OUT"` into the redirected file and read THAT line.

⛔ **AND THE COMMIT GATE WAS NEVER "the suite exits 0".** CLAUDE.md's gate is: boot to the main
menu with no new `exception-*.log`. An earlier draft of this section claimed a suite-green gate had
"been dead for a week" — there is no such gate, and saying so overstated the finding.

**What is actually red, measured audit by audit rather than by grepping reports for "FAIL":**
**13** audits exit non-zero, and every one of them predates this work.

* **5 are SCHEDULED scans** from [`audit/periodic.json`](audit/periodic.json) on 14–30 day cadences
  — `code_duplication`, `test_coverage`, `recent_changes`, `error_handling`, `security` — which were
  being run as per-commit gates. `test_coverage` alone drifted 223 → 235 → 249 → 257 → 270 untested
  modules against a baseline of 224 from 2026-08-16. **These are now advisory.**
* **8 are gating audits reporting REAL content defects** — `inherits`, `upgrades`, `sequences`,
  `fluent`, `basebuilder_crates`, `buildable_order`, `weapon_suffixes`,
  `impact_glow_preservation`. These are §3.3's bounded-bug backlog, and the advisory change neither
  fixes nor hides them: **the suite still exits 1, correctly.**

⚠ So "make the suite green" is a real work item, not a switch — it means clearing §3.3. What the
advisory change bought is narrower and still worth having: a *scheduled scan's* findings no longer
mix into the same signal as a content defect.

**Maintainer ruling: those five are ADVISORY.** They run and write full reports; they do not set
the suite's exit code. `run_all.sh` carries a second `for a in …; do` loop with `|| true`, and
`run_all.py` finds it by the `# ADVISORY audits` marker comment — by marker, not by index, so a
loop inserted between them cannot be mistaken for it. The calendar is still enforced by
`python tools/audit/audit_periodic_freshness.py` with no flag, and each script still exits 1 on
its own findings so CI can gate on one deliberately. `T3_BASELINE` was **not** raised.

The sixth was a real gate enforcing a retired design — `audit_physical_state_warheads` demanded
`Warhead@{Flame,Chemical}_{Level}_Percentage` twins that the AreaDamage fold folded into the main
warhead. Fixed in the audit. Full account in [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md), "An audit
is not evidence of a law".

⚠ **Found while verifying, and worth knowing:** `run_all.py` parses its audit list out of
`run_all.sh` so the two cannot drift — but `run_all.sh` is checked out CRLF, so a continuation is
`\` + CRLF and the parser stripped only `\` + LF. Every continuation survived as its own audit
name: **73 entries where 59 are real**, and the fallback runner tried `audit_\.py` fourteen times
and reported fourteen phantom FAILEDs. Latent for as long as the file has had continuations,
because nobody ever diffed the fallback against the canonical path. Fixed, with a regression test
in `tools/tests/test_audit_run_all_parser.py`.

### 3.0e — ⛔ The balance ledgers are stale on master (found 2026-08-28)

`python tools/balance/run_pipeline.py` — the new orchestrator — came back FAIL on its
first real run against `4643c3ee`:

| stage | result |
|---|--:|
| drift — yaml vs committed ledger | **FAIL: 22 of 33 raw ledgers stale, 5 model** |
| multiplier modifiers integer | PASS |
| generator reproduces every family | PASS — drift 0 across 139 templates |
| empty warhead types | PASS — 0 of 2839 |

`CLAUDE.md` rule 3 already warns that `audit_balance_drift` "only helps if someone
LOOKS", and that it had gone red twice for exactly this. **This is the third time.**
The last commit to re-extract was #293; something after it moved yaml without running
step 1.

**The remedy is one command**, and it belongs to whoever lands the next balance commit
rather than to a drive-by — the weapon-consolidation flow already re-extracts, and a
single commit that skipped it left 22 ledgers stale:

```sh
python tools/balance/extract_stats.py     # or: run_pipeline.py --extract
```

then commit the ledgers together with the yaml that moved them.

⚠ Do not read this as licence to hand-edit a ledger number. Re-extraction regenerates
the ledger *from* yaml — the sanctioned direction. Editing a ledger to make drift go
away inverts the pipeline and is exactly what rule 3 forbids.

### 3.0d — Read before proposing pipeline architecture

[`design/BALANCE_PIPELINE_GAPS.md`](design/BALANCE_PIPELINE_GAPS.md) records what a single
deterministic command still lacks — no orchestrator among 50+ scripts, no exception registry, no
constraint reporting, no determinism check — and the verified residue of an outside review round
that produced a great deal of confident, contradictory material about this repository.

⭐ Its one transferable lesson: **a review of a repository snapshot is a review of a date.** Five
reviewers disagreed about whether the balance documents existed; all five were reading the tree
as it stood before the 83→43 compaction, and every path they called missing had simply moved.
Establish which commit an outside report saw before acting on it — `git log --all -- <path>`
separates "moved" from "never existed", and the substance of a stale report is often still good.

### 3.1 — The weapon rebuild (the main line)

⛔ **Set B (`mods/cameo/weapons/**`, `mods/cameo/ContentPacks/**/weapons.yaml`) is NOT free.**
Devin is working W2 in it — `IN PROGRESS (Devin, 2026-08-21)`, HeatRayBeam1-4 split, 28
`^LightFlameWeapon` matches left. Check `git log -3 <file>` and the file mtime before touching
anything in that set, and coordinate rather than assuming the 2026-08-15 lock release still
holds.

| step | what | how you know it moved |
|---|---|---|
| **W24** | collapse each fired weapon to ONE damage warhead (DESIGN §11b) | `multi_main_fired_weapons` is 192, down from 927; 299 remain when indirect weapon-graph reachability is included |
| **W23** | retrofit the legacy templates onto `^Warhead_*` families | from the 2026-08-23 baseline: `unconverted_template_inheritors` goes DOWN from 1162; `warhead_family_reach` goes UP from 1245 |
| **A5** | retire the remaining inline-`Versus` weapons onto templates | rule 4 — `Versus` only in `^Warhead_*` |

Method for one W24 cluster, in order (this is the procedure that has worked for seven clusters
and is written out in full in `BALANCE_PROGRAM_PLAN.md` §1b):

1. **Resolve and INLINE first**, remove inherits second, clean up third. Never reorder an
   `Inherits` block "cosmetically" — position is semantic (see the trap list below).
2. Collapse the mains into one warhead at the SUMMED damage; keep the percentage twin
   consistent (`formula.percentage_twin`, **not** `damage // 2000`).
3. Preserve every effect the weapon had: physical state, trail, ground/air/water effects,
   smudges, `Report:`.
4. `tools/audit/review_resolve_diff.py` — before/after resolve must show only the intended
   change.
5. `find_empty_warhead.py` = 0 · `audit_warhead_split` at or below baseline ·
   `audit_physical_state_warheads` PASS · `audit_balance_drift` clean.
6. Boot-gate. Then commit yaml **and** ledgers, and lower the baseline in
   `audit_warhead_split.py` if it moved.

### 3.2 — Independent of the main line (safe in parallel)

| item | set | note |
|---|---|---|
| **W7** Sonic → `Resonance` meter | D (`rules/defaults.yaml`) | ⚠ set D is ONE file — serialise W7/W9/W10, never two at once |
| **W9** `^Poisonable` → `Poison` meter | D | same |
| **W10** `^Blindable` → `Blind` meter | D | unblocked, W6 shipped |
| **WC2 heroes** | `mods/cameo/ContentPacks/Warcraft2/Humans/**`, `Orcs/**` | **IN PROGRESS (Devin, 2026-08-25)** — porting 4 hero units + weapons + icons from `wcameo(1)` with new `wc2_<faction>_<actor>` naming. Weapons done; actors, sequences, icons in progress. Check `git log -3` and mtime before touching this set. |
| **W12** superweapons as a separate track | — | maintainer-led; superweapons are not unit-priced |
| **Adopt the Sonic family** | B | `^Warhead_Sonic_*` bakes the mark but **nothing inherits it**, so it is inert. Needs a maintainer warhead order (rule 4). Law: an effect upgrade ADDS `^Warhead_Sonic_*`, it never replaces the base damage TYPE. |

### 3.2b — Absorbing the other OpenRA mods (measured 2026-08-23)

Plan and every number: [`design/UPSTREAM_MODS.md`](design/UPSTREAM_MODS.md).
Re-measure with `python tools/audit/audit_upstream_adoption.py` (in `run_all.sh`).

**Settled, do not re-derive.** The engine must NEVER move to `ca-engine` (it would discard 2 581
commits and delete `OpenRA.Mods.AS`); CA mod code comes FORWARD onto Cameo's engine. Measured from
the point where `cameo-engine` last took upstream OpenRA (`b0b0544d4a`, **2026-05-11**): Cameo is
1 975 commits of its own past it and only **70 behind `openra/bleed`**. RV and SP pin ANCESTORS of
`cameo-engine`, so they need **no engine work at all**. CN's own work is 170 enumerable commits on
newer bleed, so its engine patches ARE cherry-pickable. Generals Alpha needs no engine work either
— of the 49 commits its pin has that we lack, 41 are upstream bleed and 8 are maintenance.

⛔ **`mtr/rv-engine` is STILL MAINTAINED** (tip 2026-07-25) — Generals Alpha pins it. The RV *mod*
is dormant; the engine branch Cameo descends from is not. Any plan resting on "the RV engine is
dead" is resting on a false premise.

**`openra/bleed` is tracked as a sixth upstream** — the only one that is not a mod, because
absorbing it means MOVING THE ENGINE (the `cameo-engine` pipeline: merge → push → `ENGINE_VERSION`
in `mod.config` → `make.cmd all` → **recreate `engine/glsl/` shaders** → boot-gate), not copying
types. The 70-commit gap holds .NET 10, ARM packaging with x86/Mono dropped, a large Gustas
rendering/perf batch, several pathfinding fixes, and one real feature: **the Tiberian Sun Firestorm
Defense**. Not a free update — schedule it a session of its own.
`python tools/audit/audit_engine_freshness.py` reports the gap every suite run (it does not fetch;
`git -C ~/Documents/GitHub/cameo-engine fetch upstream mtr --no-tags` first).

**What is actually left, by TYPE** (Cameo resolves 1 101 yaml-visible names across 7 assemblies):

| mod | already here | duplicate under another name | real candidates | live in its own yaml |
|---|--:|--:|--:|--:|
| Generals Alpha | 2 of 23 | 1 | 20 | **20** |
| RV | 11 of 26 | 8 | 7 | 6 |
| SP | 7 of 46 | 7 | 32 | 31 |
| CN | 5 of 107 | 2 | 100 | 90 |
| CA | 182 of 348 | 35 | 131 | 119 |

⭐ **Start with Generals Alpha.** Smallest assembly, highest signal — 20 of 20 candidates are used
by its own rules, and they group into whole mechanics: a 9-type supply-dock economy Cameo has no
equivalent of, cash hacking, `LaysMinefield` (self-replenishing, NOT our ordered `Minelayer`),
`ConditionIconOverlay`, `PilotChamber`, `FakePower`. And it exposes a dead tag we already carry:
CA's `CashHackable` sits on two actors here while **no assembly Cameo loads has the power that
reads it** — adopting a `CashHackPower` (CA's or GenSDK's) is a one-file fix.

⛔ **A new NAME is not a new MECHANIC.** RV's `Temporal` + `AffectedByTemporal` are CA's
`WarpDamage` + `Warpable`, already wired to `ChronoBeam`. Both were ported, built clean and
reverted in one session. Read the DESTINATION — the actor, then its weapon — before porting
anything. Full account in [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md).

⚠ Order: Generals Alpha, then RV + SP (frozen, 37 live candidates), then CN, then CA. **Which mechanics Cameo wants is
a maintainer call** — §5 of the plan: 86 of the 142 CA trait types already vendored here are
unused, so wiring beats adopting.

### 3.3 — Bounded bug work (good for a short session)

From [`audit/SUMMARY.md`](audit/SUMMARY.md), smallest first:

1. **2 missing sequence images** (`audit/latest/sequences.md`) — player-visible, tiny.
2. **6 G1 garrison weapons** — armed garrison-capable infantry with no garrison weapon.
3. **1 unresolved fluent ref** — shows a raw key in-game.
4. **1 basebuilder faction without a crate** (28 of 29 covered).
5. **89 D1 duplicate-`Inherits` keys** — each one silently DROPS a template. This is the same
   family as the `Parent type X was already inherited` boot crash; triage before it bites.
6. **47 prerequisite-order violations** across 841 buildable combat actors.

### 3.4 — Documentation and tooling debt this pass left behind

* **`tools/audit/audit_damage_grid.py` is re-derived (2026-08-25) but NOT yet wired into
  `run_all.sh`.** It now imports `formula.DAMAGE_STEP` (100) and `formula.percentage_twin`
  instead of the retired 2000-step literals, so the ~300 false off-grid findings are gone
  (off-grid 83, unequal mains 215, basis-point percentage twin **0**, 50% twin 353 — all
  existing legacy debt). It carries a ratchet baseline per check and exits 1 only on a
  REGRESSION (count above baseline), so wiring it cannot block on the existing pile. The
  percentage-twin check is narrow on purpose: basis-point `AreaDamagePercentage` nodes
  (denominator 10000) are checked against `percentage_twin`; legacy whole-percent twins
  (denominator 100, deliberately left by W18) and folded `PercentageScale` dials (a free
  per-family dial, not a twin) are skipped. **Wiring is deferred until the W24 burn-down
  settles** — W24 is actively collapsing multi-main weapons and the fold is replacing
  separate twins, so the counts are moving targets and a gate could trip on in-flight
  conversions. Run on demand: `python tools/audit/audit_damage_grid.py`. It is the last
  of the three audits `audit_recent_changes` R2 flagged as unregistered (the other two
  are now in the suite).
* **`gen_sync` drift is 10, not 1** — and this one is real work, not bookkeeping. The accepted
  entry is `^Warhead_Sniper_Light` (a template the generator does not emit). The other **nine**
  are live disagreements introduced by the 2026-08-20 W24 chemical split, which edited the
  chemical warhead templates in `weapons.yaml` without updating the generator:
  `^Warhead_ChemCannon_{Light,Medium,Heavy}` and `^Warhead_ChemMissile_{Light,Medium,Heavy}`
  differ on `DamageTypes` (`TiberiumDeath` in the file vs `ExplosionDeath` from the generator)
  and on `Corrosion` (20/33 vs 50); `^Warhead_Chemical_{Light,Medium,Heavy}` differ on shape
  (`PhysicalStates:` map in the file vs `PhysicalStateName`/`PhysicalStateScale` from the
  generator). Decide which side is right per template, make the generator emit it, and then
  restate the expected drift in `BALANCE_PROGRAM_PLAN.md` §3 — the gate there still says
  "drift = 1", so it currently reads as passing when it is not.
* **`docs/design/invented_family_profiles.json` is stale, and regenerating it MOVES DATA.**
  Running `tools/balance/design_invented_profiles.py --write` today rewrites one family's
  `sharpness_intended`/`sharpness_shipped` (3.322 → 3.492) and its whole Versus row, because
  the inputs it derives from have moved since the JSON was committed. That is a balance change,
  not a documentation change — it needs the set-A owner and a boot gate, so this pass
  deliberately left it alone. (The count in the sheet is now derived from `len(DESIGNS)`
  instead of a hard-coded word, so it can no longer go stale on its own. To be clear: the
  sheet's "seven" is CORRECT — `Toxic` is the eighth family in the JSON but is **measured**
  from Cameo's own 28 gas weapons, not designed, so it is deliberately outside the table.)
* **`noid_resolved.json`** sits at the repo root as tracked UTF-16 with 79 209 null bytes — a
  PowerShell-redirect artifact. It is maintainer WIP, so it was left alone; it should be
  regenerated as UTF-8 or removed.
* **Comment-only mojibake** (`â€"` for an em dash) exists in a handful of `mods/cameo/**` yaml
  files. Cosmetic, comments only, another file-set's ownership — listed here so the next
  encoding sweep knows where to look.
* **36 `memory <name>` citations** across the design docs cannot be resolved by anyone but the
  agent that wrote them. Promote anything binding into `DESIGN.md`.

---

### 3.5 — Keeping the documentation from rotting again

Two audits now guard the docs themselves, and both run in `run_all.sh`:

| audit | catches |
|---|---|
| `audit_doc_claims.py` | a NUMBER in prose that no longer matches the tree. 19 claims registered in [`audit/doc_claims.yaml`](audit/doc_claims.yaml), each with the command that re-measures it. **When a claim legitimately changes, update `value` AND every file listed under its `docs:` key in the same commit.** |
| `audit_doc_health.py` | the documents being structurally broken: control characters, mojibake, a link to a missing file, an in-page `#anchor` link with no matching heading, a reference to a document that moved, two DESIGN sections sharing one id |

Neither existed before 2026-08-23, and every defect they check for was found by hand that
day. Add a claim to the registry the moment a decision starts resting on a number.

What they still cannot check is **prose contradicting prose** — a ruling written into one
document while the older statement stands in another. The only defence is the discipline:
**grep for the old claim before you write the new one, and strike it everywhere it appears.**

---

### 3.6 — Multi-agent coordination (2026-08-25)

⛔ **There are 5+ Devin agents running locally on the same branch.** Each must claim a
unique name, register in `DEVELOPMENT_LOG.md` → "Agent registry", and own a disjoint
file-set. **Before editing any weapon file, check its mtime and the registry.** If
another agent claimed it in the last 30 minutes, do not touch it.

**Agent registry** (maintained in `DEVELOPMENT_LOG.md` → "Agent registry", mirrored here):


> ⛔ **SUPERSEDED — this ownership table is STALE. The single authoritative roster is
> §3.A "Agent roster and current assignments".** It is kept only as provenance; it
> contradicts §3.A on who owns D2k/Harkonnen and on who the coordinator is. Do NOT
> claim a file-set from this table.

| name | identity | current file-set | current task |
|---|---|---|---|
| **Devin-Aether** | this session | `tools/audit/audit_damage_grid.py`, `mods/cameo/ContentPacks/TiberianSun/CABAL/`, `mods/cameo/ContentPacks/D2k/Ordos/` | W24 same-family collapses in CABAL/D2k-Ordos; audit tooling |
| **Devin-Dawn** | prior sessions (A10–A14 committer) | `mods/cameo/weapons/tiberiansun.yaml`, `mods/cameo/ContentPacks/RedAlert2Mod/TKM/`, `RedAlert2Mod/AsianAlliance/`, `RedAlert/Japan/`, `TiberianSun/GDI/`, `TiberianSun/Nod/`, `RedAlert/Shared/` | W24 bullet/missile collapses across multiple packs; ATMine rework |
| **Devin-Blaze** | active 2026-08-25 13:50 | `mods/cameo/weapons/d2k.yaml`, `mods/cameo/weapons/redalert2mod.yaml` | W24 bullet collapse for `LMG`, `light_inf_lmg`, `d2k_shotgun`, `naxis_sssoldier_smg` |
| **Devin-Cyrus** | active 2026-08-25 13:48 | `mods/cameo/ContentPacks/Warcraft2/Humans/`, `Warcraft2/Orcs/` | WC2 hero weapon rework (Alleria FirepowerMultiplier, Hellscream slice) |
| **Devin-Echo** | this session (SWE-1.7 Max, `devin@cognition.ai`) | `mods/cameo/ContentPacks/D2k/Ixian/`, `mods/cameo/ContentPacks/D2k/Ordos/`, `mods/cameo/ContentPacks/TiberianSun/CABAL/` | W24 A15: collapse `MongooseRocket`, `facedancer_grenade`, `D2K_APC_Rocket` to existing D2k 3-way families; analyze CABAL `CabalArtilleryWalkerShellUpgraded` / `CabalMothershipRockets` for design sign-off.

**Rules for all agents:**
1. Pick a unique name (`Devin-<word>`) and register in `DEVELOPMENT_LOG.md` before editing.
2. Own ONE file-set at a time. Do not edit files in another agent's set.
3. Shared bookkeeping files (`docs/audit/doc_claims.yaml`, `docs/HANDOFF.md`,
   `docs/audit/SUMMARY.md`, `docs/design/BALANCE_PROGRAM_PLAN.md`,
   `tools/audit/audit_warhead_split.py`) are **communal** — edit them only as part of
   your own batch commit, and re-read them before editing (they change every few minutes).
4. After every commit, post a summary to `DEVELOPMENT_LOG.md` with your agent name,
   what you changed, and why.
5. Before starting a new batch, re-read `DEVELOPMENT_LOG.md` → "Active claims" and
   verify no other agent claimed your target files.
6. **Never `git add -A` or `git add .`** — scoped adds only. Another agent's WIP is
   always in the tree.
7. Boot-gate before every weapon commit. If another agent's uncommitted WIP is in the
   tree, wait for them to commit before boot-gating (the boot tests the whole tree).

**Current locks (do not touch — verified 2026-08-25 13:52):**
- `mods/cameo/weapons/d2k.yaml` — Devin-Blaze (active 13:50)
- `mods/cameo/weapons/redalert2mod.yaml` — Devin-Blaze (active 13:50)
- `mods/cameo/ContentPacks/Warcraft2/Humans/yaml/weapons.yaml` — Devin-Cyrus (active 13:48)
- `mods/cameo/ContentPacks/Warcraft2/Orcs/yaml/weapons.yaml` — Devin-Cyrus (active 13:48)
- `mods/cameo/weapons/weapons.yaml` — template generator/family work; do not edit
  without explicit generator/weapon-family sign-off.
- `mods/cameo/weapons/tiberiansun.yaml` — Devin-Dawn (recently active; check mtime)

**Free file-sets for the next W24 clusters (not locked, not claimed):**
1. `mods/cameo/ContentPacks/StarCraft/*/yaml/weapons.yaml` — StarCraft weapons
   (mixed Phase B; many need maintainer sign-off or a clear new family).
2. `mods/cameo/ContentPacks/D2k/Ixian/yaml/weapons.yaml` — D2k Ixian weapons
   (same-family candidates exist: `RaiderGuns` has a risky child — check first).
3. `mods/cameo/ContentPacks/D2k/Harkonnen/yaml/weapons.yaml` — D2k Harkonnen.
4. `mods/cameo/ContentPacks/TiberianSun/Forgotten/yaml/weapons.yaml` — TS Forgotten
   (A11 completed; verify no new multi-main appeared).
5. `mods/cameo/ContentPacks/RedAlert2Mod/` (excluding TKM/AsianAlliance, which are
   Devin-Dawn's) — FutureTech, Consortium, etc.

**Trap: dead-code overrides in `mods/cameo/weapons/redalert2.yaml`** — several weapons
are shadowed by later definitions in `ContentPacks/RedAlert2/Shared/`. Before converting
any weapon, resolve it with `cameo_model.py` and confirm the resolved file is the one
you are editing. Known shadowed: `RA2CRM60H`, `RA2SCUD`, `RA2MultiHoverMissile`, etc.

---

## 4. The traps that keep costing people time

Each of these is written up in full in [`LESSONS_LEARNED.md`](LESSONS_LEARNED.md). This is the
index — read the entry before working in that area.

| trap | one-line form |
|---|---|
| `Inherits` POSITION is semantic | the LAST node wins, and `Inherits` is a node. Appended at the BOTTOM, the parent silently overrides the definition's own values. Tools that add an inherit must insert at the TOP. |
| `Parent type X was already inherited` | reaching the same parent twice along ONE chain is a boot crash. The `@suffix` does **not** make it legal — the guard is keyed on the parent TYPE. Order-dependent. Grep cannot find it; `audit_duplicate_inherits.py` reports all instances in one pass. |
| Empty warhead type | `Warhead@X:` with no type = boot NRE, and `--check-yaml` does not catch it. `find_empty_warhead.py` does. |
| Removal markers | `-Key:` crashes if the key no longer exists in the resolved chain. Strip stale removals — nested ones too — before boot-gating a conversion. |
| Child weapons after a parent conversion | children that override the OLD warhead key create an orphaned second warhead → **double damage**. Sweep children after converting any parent. |
| Dead yaml files | `mods/cameo/**/*.yaml` includes files `mod.yaml` does NOT load. Audits must read `Ruleset(ROOT).manifest.rules`, never a glob. A dead file is not evidence about what ships. |
| A missing `Versus` row | is not "no opinion" — an empty match returns 100, so a plated unit LOSES its armor. Every plating gets a row in EVERY template. |
| An armor upgrade must never increase incoming damage | DESIGN §12.0e law 4. Guard: `audit_armor_upgrade_harm.py`. |
| Bulk renames | never do a bare-identifier substitution: the same literal is a weapon, an actor, a condition and a sprite in this tree. Match the exact YAML field with a full-token comparison. |
| Loose `*_extracted/` map folders | `.oramap` is a zip; the packaged file is what ships and silently shadows loose edits. Repack in the same session, then validate with `--check-yaml`. |
| UTF-16 audit reports | a PowerShell `>` redirect corrupts them. `run_all.sh` only. |

---

## 5. Changing the engine

**First check whether a mod-side SHADOW avoids the whole procedure.**
`ObjectCreator.FindType` takes the first assembly in `mod.yaml`'s `Assemblies` list that holds
the name, and the order is **AS, CA, Cameo, Cnc, D2k, Common** — so an `OpenRA.Mods.Cameo` type
of the same name wins with zero yaml changes. Precedents: `ColorPickerColorShift`,
`PlayerColorShift`, `SelectionDecorations`. **Prove a shadow works** by giving the Cameo Info a
field the engine type lacks and booting with that field set — `--docs` lists both types and
proves nothing.

If you really need an engine change:

1. Edit C# only in the **separate `cameo-engine` clone** of `github.com/cameo-mod/OpenRA`
   (branch `cameo-engine`). Never in `engine/` here.
2. Commit and push to `origin/cameo-engine`; check `git status` for stray nested-clone entries.
3. `git rev-parse cameo-engine` for the **full 40-character** hash. Never hand-type or truncate.
4. Set `ENGINE_VERSION="<hash>"` in **`mod.config`** (not `mod.yaml`).
5. `make.cmd all` — the version mismatch makes the SDK delete `engine/`, refetch and rebuild.
6. Verify `engine/VERSION` matches and the build has 0 errors. **Recreate any `engine/glsl/`
   shaders** — the fetch wipes them (e.g. `postprocess_nuclearflash.frag`).
7. Boot-gate, then commit `mod.config` together with the doc updates.

---

## 5b. The shape of the documentation set

**44 live documents.** Everything else under `docs/` is generated (regenerate it) or archived in
`history/` (what happened, never what is true now). [`README.md`](README.md) lists the whole live
set in one table — if a document is not in that table, it is not live.

The set was 83 documents on 2026-08-23. It came down by **merging overlapping documents**, not by
deleting content: every merged file's body was carried across verbatim under its own heading with
its original path recorded. The clusters that collapsed:

| now | was |
|---|---|
| `design/ARMOR_LAYERS.md` | 5 files — pseudo-armor, shield normalisation, 2 plating docs, superweapon layering |
| `design/PROJECTILE_AND_EFFECT_LAYER.md` | 3 — projectile templates, per-game sourcing, game-specific bases |
| `design/RESEARCH_NOTES.md` | 5 — SP research, mission win/lose, CABAL rebuild, SM artwork, tier-chain |
| `design/DECISIONS.md` | 3 — hex shields, vehicle queue split, derived stats in traits |
| `design/WEAPON_HEAVINESS.md` | 2 — the research and the continuous scale |
| `design/AREADAMAGE_WARHEAD.md` | 2 — the rebalance and the unified node |
| `reference/WARHEAD_REFERENCE.md` | 3 — family profiles, versus archetypes, archetype tables |
| `balance/formula_v2_classes.md` | 4 per-class logs + the delta audit |
| `design/BALANCE_PROGRAM_PLAN.md` §7 | `BALANCE_MEGAPLAN.md`, which had spent two weeks disagreeing with §0a about order |

13 stale generated per-class proposals were deleted rather than merged — they regenerate with
`propose_class_rebalance.py --class <name>`, and the committed copies no longer matched the tree.
Ten finished or dormant working notes moved to `history/`.

**If you are about to add a document, don't.** Add a section to the one that already owns the
topic — the table in `README.md` says which. A new file is justified only when no existing
document owns the subject, and then it goes in that table in the same commit.

---

## 6. What this handoff replaces

Every document below is archived, banner-stamped, and **must not be resumed from**. They are
kept for provenance and for the technique notes inside them.

| archived | was |
|---|---|
| [`history/handoffs/AI_AGENT_HANDOFF_2026-07-25.md`](history/handoffs/AI_AGENT_HANDOFF_2026-07-25.md) | session log for the 2026-07-24 yaml-lint incident |
| [`history/handoffs/SESSION_CHECKPOINT_2026-08-03.md`](history/handoffs/SESSION_CHECKPOINT_2026-08-03.md) | compaction anchor on a long-merged branch |
| [`history/handoffs/AREADAMAGE_HANDOFF_2026-08-04.md`](history/handoffs/AREADAMAGE_HANDOFF_2026-08-04.md) | the AreaDamage conversion (complete) |
| [`history/handoffs/AI_HANDOFF_2026-08-05.md`](history/handoffs/AI_HANDOFF_2026-08-05.md) | the weapon-work must-read CLAUDE.md used to point at |
| [`history/handoffs/CLAUDE_HANDOFF_2026-08-11.md`](history/handoffs/CLAUDE_HANDOFF_2026-08-11.md) | agent letter; became W15–W19 on the board |
| [`history/handoffs/DEVIN_HANDOFF_SP_RESEARCH_2026-08-11.md`](history/handoffs/DEVIN_HANDOFF_SP_RESEARCH_2026-08-11.md) | Shattered Paradise parity research |
| [`history/handoffs/DEVIN_REPLY_2026-08-11.md`](history/handoffs/DEVIN_REPLY_2026-08-11.md) | agent letter; its pipeline fixes shipped |
| [`history/MEGAPLAN_2026-08-08.md`](history/MEGAPLAN_2026-08-08.md) | thin program index, superseded twice over |
| [`history/ROADMAP_ARCHIVE_2026-07.md`](history/ROADMAP_ARCHIVE_2026-07.md) | 14 fully-closed ROADMAP sections |
| [`history/audits/`](history/audits/) | two one-off dated infantry audits |

**The rule that keeps this file from becoming one of them:** a handoff records STATE, and state
rots. When you finish a session, update **this** file — do not write a new dated one. If a
statement here disagrees with the tree, the tree is right; fix the sentence.
