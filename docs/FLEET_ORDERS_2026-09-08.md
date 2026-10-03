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

---

## 9. ⭐ ROUND-FOUR LEARNINGS — 2026-09-08b. Read these before touching the reference tree.

The maintainer reviewed the map a fourth time and named ~30 defects. Two were STRUCTURAL and they
explain most of the rest. Both are fixed on master (`f21225b6a`); the lessons are yours.

### 9.1 A guard asked the CLASS question before the WEAPON question

`exempt()` marked an actor chassis-only if `class_membership` put it in `support` — and it files
armed transports and the GDI Vulcan there. So `td_gdi_boxer`, `td_gdi_apc`, `ra1_allies_alliedapc`
and `ra1_soviets_btr80` were reported chassis-only **while carrying live weapons**, and were
therefore never given a real reference.

⛔ **The weapon is the test, and it comes first.** A real support unit carries no armament at all,
so engineers, harvesters and MCVs still fall through the class rule underneath. This is the third
time a guard wrong in the RESTRICTIVE direction has deleted correct candidates — the V3 lost five
sources the same way. **When two tests disagree, the one that lets the actor through wins.**

### 9.2 A silent no-op read as bad judgement for a month

`apply_overrides` skipped a maintainer-ruled pairing whose peer id was absent from the routed pool
**without printing anything**. A typo, or a row that routing refuses, was indistinguishable from the
matcher choosing badly. It prints `OVERRIDE UNRESOLVED` now.

⛔ **Generalise it: never `continue` past a rule that did not fire.** If a table says X and X does
not happen, that is a finding about the DATA and it has to surface. Audit your own lane for this
shape — it is everywhere.

### 9.3 And one process failure that cost a whole verification round — mine

`assign_references.py` writes the JSON only under `--write`. I ran it without the flag, read the
committed file, and reported that all 30 corrections had failed to apply. They had applied
perfectly; **I was reading a file from the previous evening.** Check the mtime of any artifact you
are about to draw a conclusion from. `ls -l` costs nothing; a wrong conclusion costs an hour.

### 9.4 Three traps that keep producing "the matcher chose badly"

* **Two rows, one name.** CA ships `NSAM` and `SAM`, both named "SAM Site", with identical faction
  lists. It ships two "AA Gun" rows and two "Mammoth Tank" rows the same way. The NAME cannot
  separate them; the ID can. Always store and compare the id.
* **A source renames things wholesale.** DTA calls its rocket soldier "Bazooka", its disc artillery
  `DISCARTY`, and prefixes every RA-era actor with `RA` (`RAAPC`, `RASAM`, `RAPBOX`). No scorer
  finds those; only an alias or an override does. **ECHO owns the alias table and O1 is now 8.**
* **One peer row currently serves one Cameo actor.** That is why `BTR` cannot back both
  `flaktruck` and `btr80`, and why `VULC` cannot back both `boxer` and `alliedheavyaatank`. The
  maintainer has asked for exactly that in three places, so **the rule itself is under review** —
  do not work around it, and do not assume it will stay.

### 9.5 What the map looks like now, so you can tell if you break it

```
actors assigned       337      references          256
originals             66       expanded             74
originals under 3      3       priced by formula    23
O1 (audit ratchet 12)  8       confidence   STRONG 720 / FAIR 142 / SHAPE 0 / WEAK 0
```

Any change that moves `O1` up, or reintroduces a SHAPE or WEAK row, is a regression. The report now
also carries each actor's **class**, and its **range** and **DPS** now/target — the class column
matters because `docs/design/EXTRAPOLATION_PROGRAM.md` derives the virtual anchors from it, so a
wrong class is a finding BEFORE any anchor is signed.

---

## 10. ⛔⛔ STANDING PROTOCOL 2026-09-08 — IDENTITY FIRST, THEN ONE BRANCH YOU OWN

**Maintainer ruling, 2026-09-08.** Agents in this fleet keep losing track of who they are between
sessions, and every expensive failure this week traces back to it:

* `devin/nova/w24-lane2` — **57 commits**, last pushed 22 hours ago, now unmergeable.
* `devin/aurora/fix-anchor-readiness` — **never pushed to any remote**. It existed only in one local
  checkout, an order named it as if it were reachable, and it **blocked Astra for a day** on a
  branch nobody could see. The fix turned out to already be on master by another route.
* Four contradicting rosters in circulation, and a commit-author filter that matched nothing because
  every agent commits under the same shared identity.

So the protocol below is not bureaucracy. It is the fix for the single defect that has cost this
fleet the most time. **Sections 10.1 and 10.2 come before any other work, every session.**

---

### 10.1 STEP ONE — identify yourself. Before any other action, including reading the queue.

1. `cat .agent-id` in your worktree root.
2. **If it has a name, that name IS you for this entire session.** Do not pick a new one, do not
   "improve" it, do not adopt a name you saw in a document or a commit message.
3. **If it is missing or empty**, choose ONE unclaimed name from **EMBER · NOVA · AURORA · DAWN ·
   ECHO**. Find what is already taken with:
   ```
   git ls-remote origin 'refs/heads/devin/*'
   ```
   Names appearing there in the last 48 hours are in use. Pick one that is not.
4. Write it down so the next session inherits it:
   ```
   echo "<YOURNAME>" > .agent-id        # untracked, per-worktree, never committed
   ```
5. **State your name in the first line of every PR body**, in this exact form:
   `Agent: <YOURNAME> · worktree: <path> · branch: <branch>`

⛔ **You may never change your name mid-session, and never adopt another agent's name.** If two
agents believe they are the same one, both sets of work become unattributable and neither can be
reviewed. If you genuinely cannot tell who you are, say so in your PR and take a name that appears
nowhere in `git ls-remote`.

⛔ Your commit trailer is `Co-Authored-By: Devin AI <devin@cognition.ai>`. **Never sign as Claude.**
The git author is a shared repo identity, so the trailer is the only provenance signal there is, and
a wrong one pollutes history permanently.

---

### 10.2 STEP TWO — claim a lane by pushing a branch. First push wins.

Branch name, exactly: **`devin/<yourname>/lane<N>_<slug>`** — e.g. `devin/ember/lane2_aa_range_gen`.

```
git switch -c devin/<yourname>/lane<N>_<slug>      # in YOUR OWN worktree only
git commit --allow-empty -m "claim: lane<N> (<YOURNAME>)"
git push -u origin HEAD                            # <-- THIS is the claim
```

**Push the claim commit before you write a single line of code.** Git makes the claim atomic: if
your push succeeds, the lane is yours; if someone beat you to that branch name, pick the next
unclaimed lane and move on without arguing. There is no registry file to edit, because a registry
file is itself a merge conflict waiting to happen.

⛔ **A branch that is not pushed does not exist.** That is the whole lesson of
`devin/aurora/fix-anchor-readiness`. Push early, push often, and never describe local work to
another agent as though they can reach it.

---

### 10.3 THE BRANCH OWNERSHIP LAW — absolute

* You may **write** only on branches whose name contains **your own** agent name.
* You may **read** any branch, and you are **expected** to review other agents' branches (§10.5).
* You may **never** commit, push, force-push, rebase, amend or delete a branch belonging to another
  agent — not to help, not to fix an obvious typo, not because they seem inactive.
* If another agent's branch needs a change, **say so in your review**. Do not make it.
* ⛔ Never `git switch`, `git checkout <branch>`, `git reset --hard`, or `git stash` in the **shared
  main checkout**. Several humans and agents have live uncommitted WIP there. Work in your own
  worktree.
* ⛔ Never `git add -A`, `git add .`, or `git add --all`. Scoped `git add <files>` only, and
  `git commit -- <explicit paths>` so a stray staged file cannot ride along.
* ⛔ Never `git checkout -- .`

---

### 10.4 THE FIVE LANES

Chosen so that **no two lanes write the same file.** The "must not touch" list in each lane is what
makes that guarantee real — respect it and you cannot conflict with another agent by construction.

⛔ **Common to every lane:** `tools/balance/reference_distribution.py`,
`tools/balance/assign_references.py`, `tools/balance/faction_routes.py` and
`tools/balance/reference_targets.py` are **Claude-Local's, read-only to all five of you.** Five
agents colliding in that tree already cost a week.

#### LANE 1 — the two class templates (C46). **Highest value: it unblocks three other people.**

The classes `armed_troop_transport` and `mobile_bunker` are defined in `class_membership.py` and
`class_anchors.json` but have **zero members**, because the yaml templates do not exist. Astra's
anchor tooling reports `NO SOURCE` because of it, and the AA audit in Lane 3 cannot classify
anything until it is fixed.

⛔ **The reason a hand tag cannot substitute:** `extract_stats.py:967` rewrites
`design.class_anchor` to `None` on **every run**. `design.subtype` — the nearest `^...Template` the
actor inherits — is the **only durable membership signal**. Members are made by inheritance, not by
being listed anywhere.

**You own:** `mods/cameo/rules/defaults.yaml`, the member actors' rules files,
`tools/balance/class_membership.py`, `docs/balance/class_anchors.json`.
**Do not touch:** `extract_stats.py` (Lane 4), `gen_weapon_template.py` (Lane 2), anything in
`tools/audit/` (Lane 3).

1. Add `^ArmedTroopTransportTemplate` and `^MobileBunkerTemplate` to `defaults.yaml`, modelled on
   `^SupportVehicleTemplate` (line ~1595) and `^AntiAirVehicleTemplate` (line ~1820). Give each a
   `TooltipExtras` description and a sensible `Armor`/`RevealsShroud`, and give `^MobileBunkerTemplate`
   the `^OpenToppedVehicle` cargo behaviour the members already have.
2. Add `Inherits@Template:` to the members. **The 16 `mobile_bunker` members**, measured through the
   resolver on 2026-09-08 (buildable, `AttackOpenTopped`, ground vehicles only):
   `ra2_allies_battlefortress` `_chrono` `_empty` · `td_gdi_assaultapc` · `tkm_battlebus` ·
   `asianalliance_warturtle` · `forgotten_thumperbus` · `latinsyndicate_carteltruck` ·
   `naxis_oldtank` · `steelconsortium_poseidontank` · `forgotten_nomadbarracks` · `naxis_nokana` ·
   `tkm_bigshiee` · `naxis_shoekarn` · `asianalliance_dragonfly` · `latinsyndicate_narcohummer`.
   ⚠ **26 actors resolve `AttackOpenTopped`, not 16.** Ten of them are **3 aircraft**
   (`terran_pythean`, `ts_gdi_hammerhead`, `zerg_behemoth`) and **7 immobile bunkers/defenses**
   (`naxis_naxibunker`, `ra2_soviets_battlebunker`, `terran_bunker`, `tkm_bunker`,
   `latinsyndicate_bunkertower`, `latinsyndicate_combatbarracks`, `latinsyndicate_defensebureau`).
   **Exclude them.** A further 21 `ra2_*_driveby` civilian cars are open-topped and not buildable.
3. **`armed_troop_transport` members: land ONLY the 18 whose current class is `support` or `None`.**
   ⛔ **17 more actors pass the mechanical test but already carry a real combat class** — the six
   `ra2_allies_ifv*` variants, `ra1_soviets_flaktruck`, `ra2_soviets_flaktrack`,
   `td_gdi_humveemkii`, `td_nod_buggymkii`, `futuretech_salamanderifv`, `ixian_shockraider`,
   `ixian_stormraider`, `ordos_stealthraider`, `japan_armoredcar`, `naxis_kubelwagen`,
   `tkm_sandmarine`. **These are NOT yours to rule on. Leave them alone and list them in your PR.**
   The maintainer is reviewing them in the reference map right now.
4. Add `"mobilebunker": "mobile_bunker"` to the map in `class_membership.py`, and add
   `mobile_bunker` to `class_anchors.json` as the 29th class. ⛔ `verifier_actor: null` and **no
   `dps0`** — W24 is still moving (231 weapons still stack 2+ mains).
5. ⛔ **BOOT GATE.** `defaults.yaml` is engine content. Snapshot `%APPDATA%/OpenRA/Logs` **before**
   launching. `launch-game.cmd` must reach the main menu; proof is `perf.log` **containing**
   `MenuPostProcessEffect.PostWorldLoaded` and **no new `exception-*.log`** — not the last line of
   the log. Kill the process the moment the menu is proven; a live instance locks the next build.
   Launch via PowerShell `Start-Process`, never the Bash tool.
6. ⛔ Run `python tools/audit/audit_duplicate_inherits.py`. Adding a template to actors that already
   inherit one is exactly how the `Parent type X was already inherited` boot crash happens, it is
   ORDER-dependent, an `@suffix` does **not** legalise it, and grep cannot find it.

**Done when:** the game boots, `class_membership.py` reports non-zero members for both classes,
`audit_duplicate_inherits` is clean, and your PR lists the 17 contested actors you did not touch.

#### LANE 2 — generate the AA range (C44)

DESIGN.md's new **AA range law** (2026-09-08) says the 1.5× AA range bonus belongs to exactly three
classes — `scout_vehicle`, `armed_troop_transport`, `anti_air_vehicle` — and that the number is
**generated, never hand-typed**.

**You own:** `tools/balance/gen_weapon_template.py`, `tools/balance/splice_templates.py`, and the
generated weapon yaml.
**Do not touch:** `defaults.yaml` (Lane 1), `tools/audit/**` (Lane 3), `extract_stats.py` (Lane 4).

1. Add `AA_RANGE_MULT = 1.5` and make the generator **write** the AA twin's `Range` from its ground
   twin's.
2. ⚠ **§8c is the trap that will eat this lane.** *"A derive-unless-overridden default is invisible
   when something upstream always overrides."* `ScaledBullet` derived shell Inaccuracy and Speed
   from Range **for weeks and reached zero weapons**, because the templates also wrote literals and
   an explicit yaml value always wins. Your test must assert the **derived number on a real
   RESOLVED weapon** via `miniyaml.Ruleset.resolve_weapon` — never that the knob exists.
3. Always `splice_templates.py --all`, **never a subset** — a partial splice leaves drift.
4. Run `tools/audit/verify_generator_sync.py`; then `tools/audit/find_empty_warhead.py` **must print
   0** (deleting or regenerating a warhead orphans child bare overrides into an abstract warhead and
   the game NREs at boot; `--check-yaml` does not catch that class).
5. ⛔ **BOOT GATE**, same procedure as Lane 1.

⚠ Baseline measured 2026-09-08 — **re-measure, do not carry it forward:** 67 actors carry a live AA
armament; 36 at exactly 1.5×, 14 at exactly 1.0×, 14 elsewhere, 3 pure-AA. `scout_vehicle` is
already 10 of 10 compliant.

⛔ **You may not change any warhead, `Burst` or `BurstDelays` without explicit permission**, and
`Versus` lives **ONLY** in `^Warhead_*` templates. Range is not a warhead field; stay on range.

**Done when:** the game boots, `find_empty_warhead` prints 0, `verify_generator_sync` reports no
drift, and a test proves the derived range on a resolved weapon.

#### LANE 3 — `tools/audit/audit_aa_range.py` (C45)

**You own:** the new file, plus its one-line registration in `tools/audit/run_all.sh`.
**Do not touch:** anything else. This lane is deliberately the smallest blast radius in the fleet.

Report, per buildable actor with both a live ground and a live AA armament: its class, its
AA÷ground range ratio, and the verdict under the DESIGN.md law. **FAIL** when an allowed class is
not at 1.5×, when a disallowed class is above 1.0×, or when **any `mobile_bunker` carries an
air-capable armament** (today exactly one: `td_gdi_assaultapc` at 1.500×).

* Get the class from `class_membership.classify()`. ⛔ **Never** the raw `design.class_anchor` field.
* ⛔ **Never hand-parse yaml.** Read through `miniyaml.Ruleset.resolve_weapon`. A bespoke
  line-scanner once opened a dict on `Versus:` and never closed it, so `PercentageVersus:` rows in
  the same node overwrote the profile — every mean, spread and ratio came out internally consistent
  and **wrong**: it reported "0 of 125 obey the MEAN-100 law" when the truth was **123 of 125**.
* Register the count as a **LOWER-ONLY RATCHET**. ⛔ **Never raise a ratchet.** Ember's
  `vfi-signature-fix` is good work sitting unmerged precisely because it moves O1 from 8 to 13 over
  a ratchet of 12.
* ⚠ **Exclude the evidence the audit is built from** — four audits in one day once flagged their own
  definition file, their own previous report, their own fixtures, and a path that can never exist.
* ⚠ **A 0% or 100% row is a bug in the CHECK.** Claude-Local hit this again on 2026-09-08: an
  `AttackOpenTopped` scan returned **0 of 213** because it searched for a trait named `OpenTopped`
  and the trait is `AttackOpenTopped`. Break your check before you believe an extreme number.
* ⛔ Regenerate reports with **`bash tools/audit/run_all.sh` only** — PowerShell `>` writes UTF-16 —
  and only from a complete tree. Never read a background task's **notification** exit code; read the
  `exit=` line in the output file.

⚠ This lane's numbers only become fully correct after Lane 1 lands. **That is fine — build it now,
report the pre-Lane-1 numbers, and re-run after.** Do not wait, and do not do Lane 1's work.

**Done when:** the audit runs clean from `run_all.sh`, the ratchet is registered, and your PR shows
the before/after counts with a pinned SHA. Docs/tools-only — **no boot gate needed**.

#### LANE 4 — teach the extractor about cargo and fireports (C47)

The ledger records **no passenger capacity at all** — no `Cargo`, no `Passengers`, no `OpenTopped`.
That is why no audit can distinguish a transport from any other armed vehicle today.

**You own:** `tools/balance/extract_stats.py`.
**Do not touch:** the 33 ledger JSONs (see below), `class_membership.py` (Lane 1),
`gen_weapon_template.py` (Lane 2), `tools/audit/**` (Lane 3).

1. Record `cargo_capacity` and `open_topped` per actor, resolved through `miniyaml`.
2. ⛔ **DO NOT re-extract the ledgers in this lane.** A re-extract rewrites all 33 JSONs and would
   collide head-on with Lane 1's class changes. Implement, unit-test against fixtures, and **say in
   your PR that the re-extract is deferred to after Lane 1 lands.** Whoever runs it afterwards
   commits **yaml and ledger in the SAME commit** — `audit_balance_drift` goes red when they
   disagree, and it has gone red twice because someone landed yaml without re-extracting.
3. ⚠ **Do not "fix" `design.class_anchor` being reset to `None`.** That is deliberate. Subtype is
   the membership signal.

**Done when:** the new fields extract correctly for a handful of known actors (`td_gdi_apc`,
`td_gdi_assaultapc`, `ra1_allies_alliedapc`, `ra2_allies_battlefortress`), tests pass, and no ledger
file is modified. Tools-only — **no boot gate needed**.

#### LANE 5 — the merge backlog. Unglamorous, and the tree is rotting without it.

**14 branches are unmerged.** They rot a little more every day and several already conflict.

**You own:** only branches carrying **your own** agent name. **Do not touch:** anyone else's.

1. `git ls-remote origin 'refs/heads/devin/*'`, then for each of **your** branches:
   `git rev-list --count origin/master..<branch>`.
2. Rebase each onto current master, re-run the audits it touches, boot-gate if it touches engine
   content, and push. If a branch is superseded, **say so and propose deleting it** — do not delete
   another agent's branch yourself.
3. **`devin/nova/w24-lane2` is the big one: 57 commits.** ⛔ **Only NOVA may touch it.** If you are
   NOVA, this is your whole lane and it is worth more than any new task: it is W24 work, and W24 is
   the blocker under the anchors. If you are not NOVA, leave it entirely alone and pick another lane.
4. ⚠ **Ember's `devin/ember/vfi-signature-fix` must NOT be landed as-is** — it breaches ratchet O1
   (8 → 13, ceiling 12). Good work, wrong shape. It needs the regression fixed, not the ratchet
   raised.

**Done when:** every branch carrying your name is either rebased and green, or explicitly declared
superseded with a reason.

---

### 10.5 PEER REVIEW — you review each other. Do not wait for Claude-Local.

Round robin: **Lane 1 is reviewed by Lane 2's owner, 2 by 3, 3 by 4, 4 by 5, and 5 by Lane 1's.**
Every lane gets exactly one reviewer and every agent reviews exactly one lane, so nobody is a
bottleneck and nobody is unreviewed.

A review must state, in this order:

1. **what you ran** — the exact commands, with a pinned SHA next to every count, so a reader can
   tell a moving target from a disagreement;
2. **what you measured** — before and after;
3. **what you did NOT verify** — this is the most valuable line in any review and it is the one
   most often missing;
4. **one thing you think is wrong, risky, or under-tested.** If you genuinely cannot find one, say
   what you looked for and why you are confident.

⛔ **"Looks good to me" is not a review** and will be rejected. ⛔ **A review is read-only** — you
never push a fix to the branch you are reviewing (§10.3); you describe it and the owner applies it.

⭐ Two habits worth copying from Astra's review of PR #325: **they compiled the actual C# instead of
trusting the Python model** (Python ints do not overflow, so the model could never have found the
32-bit defect), and **they repeatedly said what they had not verified.** Both are rarer than they
should be.

⭐ **A file that CONFLICTS is safer than one that does not — the conflict is the warning.** Astra's
best finding on that PR was eight `signed_off: true` rows in `class_anchors.json` that merged
*cleanly* and would have silently signed anchors nobody approved.

---

### 10.6 Rules that apply in every lane, without exception

* ⛔⛔ **SUPERWEAPONS ARE NEVER PRICED AND NEVER CHANGED.** Maintainer, emphatically: *"exclude super
  weapons from this balance formula since they are all fixed HP! NEVER CHANGE THEM!!"*
* ⛔ **Never hand-edit a balance number.** `extract_stats` → ledger → `apply_balance --confirm`, and
  `--confirm` requires a maintainer order nobody in this fleet has.
* ⛔ **`Versus` lives ONLY in `^Warhead_*` templates.** No warhead / `Burst` / `BurstDelays` change
  without explicit permission.
* ⛔ **Never hand-parse yaml.** `miniyaml.Ruleset.resolve_weapon` / `.resolve`, always.
* ⛔ **Never raise a ratchet.** Lower only.
* ⛔ **Boot-gate every commit touching engine content.** Docs and tools are exempt.
* ⛔ **`engine/` IS NOT PART OF THIS REPO.** It is gitignored, `git ls-files engine` returns zero,
  and `make.cmd all` deletes anything you write there. Never edit it.
* ⛔ **Underscore-only naming.** No hyphens in ids, files or fluent keys.
* ⛔ **A result that contradicts a binding law is a contradiction, not a finding.** If the generator
  implements a law and `verify_generator_sync` reports 0 drift, "nothing conforms" means your
  measurement is broken. Check the measurement before writing it up.
* ⛔ **Before reporting something absent, prove your pool contains it.** This exact mistake produced
  four false reports in one day: 40 "lost" references that were all heroes filtered out of the pool
  (true count 0), 30 corrections reported as failed because the tool only writes under `--write`,
  and "no agents have pushed" when 17 branches had moved.

---

### 10.7 When you are blocked, do not stop and do not invent

1. Write the blocker on your PR: what you needed, what you tried, what you measured.
2. **Take the next unclaimed lane** and push its claim branch. Do not sit idle waiting for an answer.
3. If the blocker is a **decision** rather than a fact, put it to the maintainer as a question with
   **2–4 real options and a recommendation** — never as a bullet in a summary, and never resolve it
   yourself. They cannot read everything; a forced choice is what gets a considered answer.
4. **Do not treat a missing branch, a missing file or an unreachable reference as permission to
   proceed anyway.** Astra got this exactly right and it is the standard for everyone here.
