# The extrapolation program — from mapped originals to a priced roster

**Maintainer's method, 2026-09-08, written down so it can be checked and executed.**
This is the plan that turns the reference map into the first applied balance numbers. Everything
in `docs/design/BALANCE_PROGRAM_PLAN.md` §0a still binds: weapon STRUCTURE before pricing.

---

## 0. The maintainer's proposal, in their words

> *"imagine that we will map all the existing units from TD and RA1 and then we extrapolate
> everything we cannot map, then we add RA1 Japan to the reference list and extrapolate our existing
> Japanese units from our 4 existing factions. And from those we will try to create the base band.
> Virtual baseline actors (at 100% and verifiers at 250% price) from our TD, RA1 and Japan factions.
> Then I'm sure we have all the units we need to fill out classes with the necessary data! And with
> that data established we can also more easily add the remaining factions to the reference?"*

**This is correct, it fixes a real problem, and one part of it is already built and unused.**
Two measurements settle it.

### 0.1 It is feasible — 26 of the 27 classes have members in those factions

Measured 2026-09-08 through `class_membership.classify()` over all 33 ledgers (700 classified rows):

```
class              TD+RA1  JP   all      class              TD+RA1  JP   all
anti_air_vehicle        3   1    14      light_tank              4   1    16
archer                  0   1     4      line_breaker            3   0    33
artillery               7   1    35      mbt                     8   2    51
artillery_tank          2   1    14      melee                   4   1    49
closecombat             1   0     5      missile_vehicle         4   0    14
commando                6   1    30      mortar                  1   0     5
dreadnought             0   0     5  ⛔  pure_sniper             2   0    16
epic_vehicle            4   2    24      rocket_trooper          6   0    45
fire_support            4   2    31      scout                   5   0    33
flying_infantry         0   1    11      scout_vehicle           5   2    52
grenadier               4   0     7      special_forces          4   1    16
heavy_infantry          5   2    41      support                14   2   115
heavy_sniper            2   0     3      tank_destroyer          1   0     5
high_tech_tank          6   2    26
```

**`dreadnought` is the only class with no member in TD, RA1 or Japan** — its five members are
StarCraft/naval. Every other class can be anchored from the factions the maintainer named. Japan
carries `archer` and `flying_infantry` on its own, which is a second reason to fold it in early
rather than treat it purely as a test.

⚠ Two earlier attempts at this measurement returned all-zeros and 8-zeros. Both were bugs in the
CHECK, not findings: membership is DERIVED from `design.subtype` when no explicit `class_anchor`
tag exists, so reading the tag alone reports `commando: 0` for a class with 30 members. Use
`class_membership.classify()`, never the raw field.

### 0.2 The virtual-anchor mechanism ALREADY EXISTS

```
tools/balance/fit_class.py --class <name> --spec hp,speed,range_wdist,damage,reload,cost0
    "virtual anchor ... a round-number model unit that need not exist in game (Tiger-style baseline)"
```

It has been in the tree since before this program was proposed, and **nothing uses it.** ⛔ Do not
design or build a virtual-anchor mechanism. `docs/TASK_INDEX.md` exists because this exact thing
was re-designed once already. What is missing is not the mechanism — it is the *inputs*.

---

## 1. Why a virtual anchor is the right answer, not a workaround

The existing real-actor anchors are vulnerable to actor drift, which is one source of the deadlock.

> **Measurement correction 2026-09-09** (supersedes the raw-fit metrics block that stood
> here — its "satisfying identity 0 of 27" line came from a superseded raw fit check; see
> [ASTRA_REVIEW.md, 2026-09-09 pass](../audit/ASTRA_REVIEW.md)): the stored-fit registry
> holds **28 class entries — 26 carry no stored `cost0`/`o0`/`p0`/`q0` at all, and 2
> (`line_breaker`, `mbt`) carry complete legacy raw values**. Absence is NOT a failed
> identity: the final per-stat normalized identity cannot be judged by comparing raw
> `o0`/`p0`/`q0` to `cost0`. This stored-fit check does not refresh live off-spec counts,
> fitted models or residual distributions. Two standing clarifications: frozen, approved **virtual**
> specs are independent of actor stats (that independence is the point of Phase E), while
> the diagnostic current-ledger medians remain unapproved and not frozen. This is a
> factual measurement correction, not a change to any gate, owner or approval.

A real actor can drift from its anchor specification when its yaml changes. Recomputing or
refitting actor-dependent anchor inputs can then reprice the class; stored fits do not refresh
automatically. `mbt`'s spec says `hp0` 240,000 while `naxis_tiger` ships 100,000; the class
has been waiting on a "restat the baseline actor" step that has never run.

A virtual anchor cannot drift, because no yaml points at it. It is a round-number model unit
derived from evidence, and the evidence is exactly the thing three review rounds have been
hardening: the reference consensus for units that provably exist in every source.

**That is the whole argument. The originals are the best-evidenced numbers in the project, and the
anchor should be made of them rather than of whichever actor someone picked in July.**

---

## 2. The program, in five phases

Each phase has an owner, an artifact, and a gate. **No phase starts before its predecessor's gate.**

### Phase A — the original mappings, approved faction by faction

Owner: **Claude-Local** (TD, RA1) · **Astra** (RA2, TS — see §4).

One short report per faction: `td_gdi`, `td_nod`, `ra1_allies`, `ra1_soviets`. Originals only,
expansions listed separately and NOT part of the approval. The maintainer approves or rejects each
faction on its own, and the next phase starts for a faction the moment its originals are approved —
the four run in sequence, not behind the slowest.

GATE: maintainer approval, per faction, recorded in this document's §5 table.

### Phase B — the faction calibration, on the approved originals only

Owner: **Astra**. ⚠ `tools/balance/faction_extrapolate.py` (504 lines) **already implements the
exchange-rate method**: `k = geometric mean over pairs of (cameo_stat / reference_stat)`, per route
and per stat, with unpaired reference rows becoming virtual members at Cameo scale. Read it, run
`--report`, and write down what it does NOT yet do. Do not rebuild it.

For each approved faction and each stat (hp, speed, range, cost), compute `k` from the approved
STRONG/FAIR pairs only. One factor per faction per stat, with the pair count and the spread
attached — a `k` from three pairs is not the same evidence as a `k` from twenty, and the report
must say which.

GATE: every `k` has ≥3 backing pairs, or is marked `THIN` and excluded from Phase C.

### Phase C — extrapolate the expanded units of those four factions

Owner: **Astra**. Place each expanded unit at **class anchor × tech tier × faction factor**, and let
the formula fit the placed stats and price. **Clarification, Aedis 2026-09-09:** initial reference
placement includes price; the final fit may adjust stats, price, or both on their permitted grids
to approach zero delta. The old classic-original price freeze is superseded; MCVs and harvesters
remain collection/manual-review only. See [the dated ruling record](../balance/review/AEDIS_OVERNIGHT_RULINGS_20260909.md).
This is the first real test of the method, and
it is deliberately run on factions where we CAN check the answer: an expansion sitting next to
approved originals is easy for a human to sanity-check.

GATE: maintainer eyeballs one faction's expanded roster and says the numbers are not absurd.

### Phase D — Japan

Owner: **Astra**. Japan has no single original-game roster counterpart. **Source correction,
2026-09-09:** the current ordinary pipeline has 14 proxy-paired and 24 rank-placed Japanese actors
through Mental Omega / RA2 Reborn. These proxies do not establish direct counterparts. Aedis now
also requests RA3 Empire and Japanese RA2-mod evidence. Run the Phase B/C machinery with explicit
provenance for reference-backed, role-analogue, and extrapolated inputs; where `k` comes from the
four classic factions rather than Japanese evidence, label that distinction.

⚠ Japan is also *evidence*, not only a test — it carries `archer` and `flying_infantry` members that
TD and RA1 do not. Once its roster is placed, it feeds Phase E.

GATE: maintainer reviews the Japanese roster. A plausible roster is a pilot result, **not proof
for every expansion unit**. Test reconstruction of withheld known references and representative
counter/matchup behavior before generalizing. Formula fit alone does not verify gameplay balance.

### Phase E — the virtual anchors, and the first applied numbers

Owner: **Astra**, signed by the **maintainer**.

For each of the 26 covered classes, derive the virtual anchor from that class's TD/RA1/Japan
members after Phases A–D:

1. **`hp0`, `speed0`, `range0_wdist`, `cost0`** — from the class's members in those factions,
   preferring reference-backed originals, rounded onto the nice-number grid (`docs/DESIGN.md`, the
   nice-number law; damage on the **10** grid, `formula.DAMAGE_STEP`, regridded from 100 on 2026-09-11).
2. **The identity `o0 = p0 = q0 = cost0` must hold by construction.** It is a virtual unit — if the
   identity does not hold, the spec is wrong, not the actor. This is the single cleanest advantage
   over a real anchor and it must be asserted, not hoped for.
3. **The verifier at 250%.** A model unit at 2× hp, 2× dps, 2.5× cost. ⛔ Baseline and verifier must
   share the TechTier bucket AND `K`, or the 2.5× identity breaks — this has bitten before.
4. Feed it straight to `fit_class.py --class X --spec hp,speed,range_wdist,damage,reload,cost0` and
   report the residual distribution against the class's real members.
5. ⛔ **`dps0` is still excluded** while W24 moves (231 weapons still stack 2+ mains). The spec's
   `damage,reload` fields are the model unit's own, not a target for any real weapon.

⛔ **`dreadnought` has no member in these factions.** Do not invent one. Report it as the single
class that needs a different source and let the maintainer decide — probably after RA2/TS mapping
gives it naval evidence.

GATE: maintainer signs. Then, and only then, `extract_stats` → ledger → `apply_balance --confirm`
on the signed classes.

---

## 3. Why this also makes the remaining factions easier — the maintainer's last point, confirmed

Yes, and the mechanism is worth stating precisely. Once the anchors are virtual and evidence-backed:

* a new faction does not need its own anchor argument — it needs one `k` per stat, which is a much
  smaller and much more checkable claim;
* an actor with no trustworthy reference counterpart is placed by class
  anchor × tier × a `k` borrowed from a sibling faction, which is exactly Phase D;
* the anchors stop moving when someone edits a unit, so adding a faction can no longer reprice an
  existing one.

That last property is the real prize. Refitting an actor-derived baseline after restatting
`naxis_tiger` can reprice all 51 `mbt` members. After Phase E, actor changes alone would not
change the frozen, approved virtual specification.

---

## 4. Astra's part, and whether it is possible without the game folders

**It is.** The reference corpus is committed: `docs/reference/ini_corpus.json` (11,870 rows) and
`docs/design/ORIGINAL_UNITS_PEER_OPENRA.md` (2,583 rows). Nothing in the TD/RA1 mapping process
touched a local game install — every input is in the repo. Astra can run the identical pipeline
(`assign_references.py` → `reference_targets.py` → `build_reference_report.py`) for RA2 and TS.

**Maintainer's ruling 2026-09-08: Astra owns the RA2 and TS reference maps.** Same tools, different
factions, no collision with Claude-Local's TD/RA1 work.

⛔ **Read-only on the reference producers.** Astra reports mappings and hands over patches;
Claude-Local lands changes to `assign_references.py`, `reference_distribution.py`,
`faction_routes.py`, `reference_targets.py`. Five agents colliding in that tree is what cost a week.

RA2 has the most sources (Romanov's Vengeance, Mental Omega, CnC Reloaded, Rise of the East, RA2
Reborn, Valiant Shades). ⚠ **Whether Romanov's Vengeance is the RA2 authority is an OPEN maintainer
question** — it carries 729 buildable units, more than RA2 + YR ever shipped, and it is 104 of the
119 unclaimed "originals". `audit_original_coverage` currently exempts it from the O2 ratchet. That
exemption is a placeholder and must be DELETED once ruled, never raised.

---

## 5. Approval ledger

Filled in as the maintainer approves. Nothing downstream of a row may start until it says APPROVED.

| faction | originals report | approved | phase B `k` | phase C expanded | notes |
|---|---|---|---|---|---|
| `td_gdi` | — | ☐ | ☐ | ☐ | |
| `td_nod` | — | ☐ | ☐ | ☐ | |
| `ra1_allies` | — | ☐ | ☐ | ☐ | |
| `ra1_soviets` | — | ☐ | ☐ | ☐ | ⚠ the `ra1_soviets` RENAME is rejected; do not confuse it with the mapping |
| `japan` | proxy evidence; no single original roster | ☐ | ☐ | ☐ | Phase D; also supplies `archer` + `flying_infantry` evidence |
| `ra2_allies` | Astra | ☐ | ☐ | ☐ | |
| `ra2_soviets` | Astra | ☐ | ☐ | ☐ | |
| `ts_gdi` | Astra | ☐ | ☐ | ☐ | |
| `ts_nod` | Astra | ☐ | ☐ | ☐ | |

---

## 6. What would make this plan wrong

Stated up front so it can be checked rather than discovered late:

1. **If the four original factions are not representative of the game's power band**, every anchor
   derived from them is centred wrong. Test: compare each class's TD/RA1/Japan member stats against
   the class's full membership BEFORE signing. A class whose TD/RA1 members sit in one tail is a
   class whose virtual anchor will be biased, and it must be flagged, not signed.
2. **If `k` is computed from too few pairs**, a faction factor is noise with a decimal point. Hence
   the Phase B gate at ≥3 pairs.
3. **If W24 moves a class's weapons after its anchor is signed**, the `K` that priced it changes.
   Hence `dps0` stays out and the anchors are HP/speed/range/cost only.
4. **If the reference consensus itself is wrong**, everything downstream inherits it. That is what
   the faction-by-faction approval in Phase A is for, and it is why shape-only matches were deleted
   entirely rather than kept as weak evidence.
