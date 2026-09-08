# FLEET ORDERS — 2026-09-08 · land what you have built

Issued by Claude-Local (Opus 5), coordinator, at the maintainer's order. **These supersede
`Cameo-mod-fleet/ORDERS_2026-09-07_reference_reset.md` for every lane named below.** Codex/Astra
has its own document: `docs/BLACKROBE_ASTRA_ORDERS_2026-09-07.md` — read §3 of it for the ownership
map, which binds you too.

---

## 0. THE ONE MEASUREMENT THAT SHOULD CHANGE HOW YOU WORK

```
unmerged agent branches:            39
unmerged commits sitting in them:  ~200
merged to master by the fleet:       0
```

**You are producing work faster than it lands, and unlanded work rots.** Four branches were
byte-identical duplicates of each other. Two agents wrote competing proposals for the same 268
units and neither shipped. An `anchor_readiness.py` crash fix has been sitting on a branch while
another agent was told to edit that file.

So the default changes. **Small branch, one subject, land it, delete it.** A branch that cannot be
described in one sentence is too big. If a branch has been open more than two days, it is now your
top priority to finish or abandon it — say which, do not leave it.

⛔ Only Claude-Local merges to master. That has not changed. What changed is that I am now
actively landing, in order, and **a branch that conflicts goes to the back of the queue.** Rebase
onto `origin/master` before you tell me a branch is ready.

### What I landed today, so you can rebase on it

| branch | result |
|---|---|
| `devin/ember/w24-lane1` | LANDED — 22 weapons collapsed, boot-gated |
| `devin/dawn/w24-lane3` | LANDED — 69 more collapsed, ledgers re-extracted, boot-gated |

`audit_three_way_split` moved **322 → 231** on those two alone. That is the front moving for the
first time in a week, and it happened by landing, not by writing.

---

## 1. ⛔⛔ SUPERWEAPONS — unchanged and absolute

> *"exclude super weapons from this balance formula since they are all fixed HP! NEVER CHANGE
> THEM!! SO EXCLUDE THEM BEFORE ANYTHING IS CHANGED ON ACCIDENT!!!"* — maintainer, 2026-09-07

32 actors gated on `~techlevel.superweapons` / `_swlimit`, every recorded HP exactly 1,000,000.
Two locks: `reference_distribution.cameo_rows()` drops them; `apply_balance` refuses the edit.
Do not weaken either. ⚠ The `apply_balance` lock had a bug that made it refuse EVERY faction — fixed
in `545ff414a`. If you see a `SUPERWEAPON` refusal on a tree with no pending edits, you are on old
code; pull.

---

## 2. NOVA — W24 lane 2, and it is the biggest single thing left

**57 commits, 66 files, and it now conflicts with master in 5 paths** because lane 1 and lane 3
landed under you:

```
DEVELOPMENT_LOG.md                                        (additive, keep both sides)
docs/balance/derived/redalert2_soviets.json               (regenerate, do not hand-merge)
docs/balance/derived/tiberiansun_forgotten.json           (regenerate)
docs/balance/redalert2_soviets.json                       (regenerate)
mods/cameo/ContentPacks/RedAlert2/Soviets/yaml/weapons.yaml   ⛔ THE REAL ONE
```

1. **Rebase `devin/nova/w24-lane2` onto `origin/master` now.** Every hour you wait, lane 3's
   collapses drift further from yours.
2. The ledgers are GENERATED. Do not resolve them by hand — resolve the yaml, then run
   `python tools/balance/extract_stats.py` and commit the regenerated ledgers **in the same commit
   as the yaml**. ⚠ Lane 3 did not do this and `audit_balance_drift` went red across 10 ledgers;
   I re-extracted to land it. That is the rule, not a nicety.
3. **`RedAlert2/Soviets/weapons.yaml` needs a real decision, not a merge tool.** Establish, weapon
   by weapon, whether your collapse and master's current content are the same weapon at a different
   value. If they are, master's shipped value wins unless you can show the collapse preserved
   resolved behaviour. Put the list in the PR body.
4. Then `devin/nova/w24-naxi-pilot` (2 commits) — it conflicts with lane 2 on
   `Naxis/yaml/weapons.yaml`, so it **must land after** lane 2, rebased.
5. VERIFY before you tell me it is ready: `find_empty_warhead.py` = **0**,
   `audit_balance_drift` **clean**, `audit_three_way_split` **lower than 231**, and a boot to the
   main menu with no new exception log.

⛔ Do not open a new W24 lane until lane 2 and naxi-pilot are landed. Four parallel lanes into one
weapon tree is what produced these conflicts.

### NOVA, second: your seven small branches

`areadamage-sweep-class2d` · `deadfield-sweep-scales` · `stamp-stale-maps` are CLEAN against master
(1 commit each). Rebase, verify, and tell me — I will land them today. `doc-id-sweep`,
`roadmap-bell-shipped`, `rename-naxis`, `rename-naxis-v2` conflict; `rename-naxis-v2` has **8**
conflicts and is superseded by `rename-naxis` — collapse them into one before you touch anything
else. ⚠ And see §6 on renames.

---

## 3. EMBER — CA over-tagging is still the biggest lever, and it is still not done

Unchanged and still yours, because nothing else unblocks as much:

**Combined Arms' median row is admissible to FIVE Cameo factions. Every other source's median is
ONE**, and 154 of 346 CA rows exceed six. That one fact caused most of what the maintainer rejected
in three review rounds: a Soviet Tesla Trooper for Nod's laser trooper, Nod's SAM for the Soviet SAM
site, an RA1 Allied IFV for a GDI APC, and `allows("td_gdi", TITN)` returning **False** — CA denying
GDI its own walker.

1. You are still the sole owner of `tools/reference/extract_peer_units.py`.
2. Find out whether the over-tagging is CA's own data or our parent/child `Side:` expansion unioning
   every leaf faction into every row. **Report the before/after tag-count distribution**, not a pass.
3. ⚠ `DOT_SUFFIX_CLAIMS` in `faction_routes.py` already reads CA's `STNK.Nod` / `SYRD.gdi` id
   suffixes and covers ~12 rows. Build on it; do not duplicate it; do not add non-faction suffixes
   (`.ATOMIC`, `.LASER`, `.UPG`) or `.TD`, which both TD factions share.
4. Known still-wrong and waiting on you: `ra1_soviets_sovietsamsite` holds CA's `NSAM` (Nod's), and
   `ra1_allies_alliedheavyaatank` holds CA's `HFTK` Heavy Flame Tank.
5. VERIFY: `python tools/audit/audit_original_coverage.py` — O1 must not rise above 12, and report
   the CA histogram.

### EMBER, second: six branches that are CLEAN and unlanded

`lane5-classes` · `ra6-collapse` · `td-teamupgrade` · `x3-aa-rename` · `naming-asianalliance` ·
`rename-asianalliance` all merge clean. Two of them are near-duplicates of each other (78 of 83/79
files shared) — **collapse `naming-asianalliance` and `rename-asianalliance` into one branch and
tell me which one to take.** Then tell me the others are ready and I will land them.

---

## 4. AURORA — stop, consolidate, then one job

You have **14 unmerged branches**, more than anyone, including three versions of `rv-untagged-fix`
and two of `lane4-templates` and two of `pool-hygiene`. That is not throughput.

1. **Consolidation first, before any new work.** For each of these groups, keep ONE branch and say
   which: `rv-untagged-fix` / `-v2` / `-v3`; `lane4-templates` / `-v2`; `pool-hygiene` /
   `pool-hygiene-clean`. `regen-starcraft-wc2` is **byte-identical** to `devin/regen/conversion` —
   one of you did not do the work you think you did; sort out which and drop the other.
2. ⛔ **`pool-hygiene-clean` must NOT be wired, and here is the measurement:**
   ```
   corpus rows 11870 | reference_distribution.ini_rows() keeps 2473 | your filter keeps 3172
   rows your filter would REMOVE that the pipeline keeps:   0
   rows it would ADD BACK:                                699  (295 build-limited, 404 with no cost)
   ```
   `ini_rows()` already applies your exact rule and applies it more strictly. Your filter is a
   LOOSENING. **Nothing is wrong with the code; the order I gave you was wrong** — I wrote it from
   your docstring instead of measuring. Keep the branch, do not wire it.
3. **THE JOB: implement the hero-only reference lane.** The maintainer ruled it on 2026-09-07 and
   it is the reason `RMBO` is still unclaimed:
   * heroes (`build_limit` present) stay OUT of every ordinary distribution — the population rule
     is unchanged, and the 3,000,000 HP epic must never re-enter the vehicle ceiling;
   * but the ASSIGNMENT may see them, so a Cameo hero matches a peer hero. **83 Cameo hero/epic
     combat rows and 295 peer heroes are in scope.**
   * shape: a hero FLAG carried on the row, never a drop. `peer_rows()` keeps its exclusion for the
     distributions; `assign_references` gains a hero-to-hero-only rule.
   * ACCEPTANCE: `td_gdi_commando` claims OpenTD's `RMBO`; `ra1_allies_chronotank` claims OpenRA
     RA's `CTNK`; **no non-hero mapping changes at all** — diff the assignment before and after and
     show that the only new rows are hero rows.
   * ⛔ Codex is specifying the LEDGER side of this (its task C39). Coordinate through me; do not
     both edit `reference_distribution.py`.
4. `fix-anchor-readiness` conflicts in `anchor_readiness.py`, which is **Codex's file**. Hand me the
   diff; do not land it yourself.

---

## 5. DAWN — the INI corpus, and only that

1. `w24-lane3` is landed. Thank you — 69 collapses. ⚠ One correction: it changed 10 weapon files and
   **no ledgers**, so `audit_balance_drift` went red across 10 ledgers and I re-extracted to land
   it. **Yaml and ledger go in the same commit.** Next time it will bounce.
2. `untagged-dune-mo` and `ini-side-aliases` are the **same 7-file set** on two branches. Collapse
   them into one, rebase (both conflict in 3 paths), and tell me.
3. Then your actual lane, unchanged: **make buildability visible in the INI corpus.** DTA ships both
   a buildable MLRS/Rocket Launcher and a non-buildable crate `MSAM`; the matcher currently cannot
   prefer the real one. That is a DATA job, not a matcher job. CnC Reloaded, Mental Omega, Twisted
   Insurrection and Rise of the East all ship map-only and campaign-only actors, and none of them
   uses OpenRA's `~disabled` marker — **derive the equivalent from the data**, never a name
   blocklist, which rots the moment a mod adds a unit.
4. ⛔ You do not own `tools/reference/extract_peer_units.py`. EMBER does. Hand EMBER patches.
5. ⛔⛔ `extract_peer_units.py --mod <x>` **rewrites the whole corpus** with only that mod's rows —
   it ran a 2,583-row file down to 57. Use `tools/reference/splice_peer_section.py`, which refuses
   to write when any other source's row count moves.

---

## 6. ECHO — the alias table, and it is now a short finite list

`audit_original_coverage` O1 is down to **9**. Every one is a Cameo original that some source ships
under another name:

```
ra1_allies_blackhawk · ra1_allies_camopillbox · ra2_allies_engineer · ra2_allies_grizzlytank
ra2_soviets_engineer · ra2_soviets_sentrygun · td_gdi_rocketsoldier · td_nod_rocketsoldier
ts_nod_lightinfantry
```

1. Build the alias table from the ORIGINALS only, where the answer is knowable: all three sources
   must have the unit, so any source that failed to match is naming it something else. DTA calls its
   rocket soldier "Bazooka".
2. ⛔ **An alias is for ONE unit under two names, NEVER for two different units.** Do not add
   `mlrs -> ssmlauncher`; Cameo ships both and they are different vehicles.
3. ⚠ One more that id-matching cannot reach: `td_nod_apacheattackhelicopter` holds CA's `APCH` and
   DTA's `APACHE` but misses OpenRA TD's `HELI`. Same aircraft, third name.
4. VERIFY: O1 falls below 9 and **no STRONG mapping changes to a different unit.**

---

## 7. Rules that bit someone this week

* **Yaml and ledger in the SAME commit.** Re-extract at the point of change
  (`python tools/balance/extract_stats.py`), not at the end of a session.
* **Boot-gate every commit of engine content** — snapshot `%APPDATA%/OpenRA/Logs` BEFORE launching;
  proof is `MenuPostProcessEffect.PostWorldLoaded` in `perf.log` and **no new `exception-*.log`**.
  Kill the process the moment the menu is proven — a live instance locks the next build.
* **Scoped `git add <paths>` only**, never `-A` / `.` / `--all`. `git commit` also needs an explicit
  `-- <paths>` pathspec or it commits the whole index including someone else's staged WIP.
* **Worktree, never `git checkout -b` in the shared main checkout** — it moves every other agent's
  working directory. `git worktree add C:/tmp/<you>-<lane> -b <branch> origin/master`.
* **Never raise a ratchet.** Re-baselining on a genuinely widened measurement is allowed, but you
  must PROVE the measurement widened: measure the old subset and show it is unchanged.
* **Sign your own trailer** — `Co-Authored-By: Devin AI <devin@cognition.ai>`. Never the Claude one.
* **Never hand-parse yaml.** Read through `miniyaml.Ruleset.resolve_weapon` / `.resolve`.
* ⚠ **The `ra1_soviets` rename is REJECTED** — the maintainer ruled all 32 ids got worse. Do not
  land it, and do not build on `devin/aurora/naming-ra1_allies` / `devin/dawn/ra1-soviets-wip`
  (the same commit, 287 files) without separating the rejected rename out first.

---

## 8. How to tell me a branch is ready

One message, this shape, and I will land it the same day:

```
BRANCH: devin/nova/w24-lane2   (rebased onto origin/master today)
SUBJECT: 31 RA2 Soviet weapons collapsed to one main
GATES:  find_empty_warhead 0 · balance_drift clean · three_way_split 231 -> 200 · boot OK, no new exception log
RISK:   RedAlert2/Soviets/weapons.yaml overlapped lane1; resolved in favour of master's shipped values on 4 weapons (listed)
```

If a gate is red, say so and say why — a red gate reported honestly costs an hour; a red gate
discovered after landing costs a day.
