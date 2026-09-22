# HANDOFF — the reference / faction-routing pipeline

**Written 2026-09-05 by a CLOUD session (Claude Opus 5), for the LOCAL agent with file access.**
Verified against `ec7272b81`. Every number here has the command that produced it next to it.

> ⚠ **SCOPE, so this cannot become a second source of law.** This file holds the lane's
> PROCEDURE and its TRAPS (§8 is the valuable part — nine real bugs, each with the guard
> and test that now catches it). It does **not** hold rulings: **R1–R15 live in**
> [`REFERENCE_EXTRACTION_PLAN.md`](REFERENCE_EXTRACTION_PLAN.md), which is their single
> home per `docs/TASK_INDEX.md`. Where the two touch, the plan wins.
>
> ⚠ **§5's measured state is as of 2026-09-05 and has MOVED** — the INI corpus was wired
> in on 2026-09-06 (2,568 → 4,520 peer rows, 15 → 21 sources, every routed faction now
> clears the two-source floor). Re-measure with `python tools/balance/faction_routes.py`
> and `python tools/balance/faction_extrapolate.py --by-class` rather than quoting §5.

> ⚠ **THIS IS A TOPIC HANDOFF, NOT A SECOND ENTRY POINT.**
> [`../HANDOFF.md`](../HANDOFF.md) remains THE handoff and outranks this file everywhere they
> touch. `AGENT_WORKSPACE.md` forbids a second roadmap or handoff, and this is not one: it is the
> reference-pipeline chapter, scoped to one file-set. If it disagrees with `../HANDOFF.md`,
> `CLAUDE.md` or `DESIGN.md` — **they win, and fix this file.**

---

## §0 — READ THIS BEFORE YOU TOUCH ANYTHING

### 0.1 The gate is real and it is hook-enforced

`tools/hooks/read_first_guard.py` runs on **every** tool call and denies it until the seven Tier-1
documents have been OPENED this session. Reads and `git status`/`log`/`diff` are exempt, so the
gate is satisfiable. Open them in this order:

1. `CLAUDE.md`
2. `docs/LESSONS_LEARNED.md`
3. `docs/AGENT_WORKSPACE.md`
4. `docs/HANDOFF.md`
5. `docs/DESIGN.md`
6. `docs/design/ROADMAP.md`
7. `docs/audit/SUMMARY.md`

`docs/README.md` is the canonical definition of that order and wins over any copy of it,
**including this one.**

### 0.2 Then the topic set for THIS work, in this order

| # | document | why you need it |
|---|---|---|
| 1 | [`FACTION_REFERENCE_MATRIX.md`](FACTION_REFERENCE_MATRIX.md) | **the core.** Parts I–III are the rulings; **PART IV** is what the wiring measured; **PART V** is the prerequisite-hop fix and the per-class grounding table |
| 2 | [`REFERENCE_METHOD.md`](REFERENCE_METHOD.md) | the 10 relative values, the matching law (§9), the role step (§12), and **§13 which says routing supersedes open matching** |
| 3 | [`REFERENCE_DEDUP.md`](REFERENCE_DEDUP.md) | one roster = one vote, and why |
| 4 | [`BALANCE_PROGRAM_PLAN.md`](BALANCE_PROGRAM_PLAN.md) §0a, §2 | the binding order of operations and **file-set ownership** |
| 5 | [`FORMULA_V2.md`](FORMULA_V2.md) | what actually prices a unit. A reference never does |
| 6 | [`BALANCE_SYNTHESIS.md`](BALANCE_SYNTHESIS.md) §3 | the documented faction inspirations the matrix routes from |

⚠ **Read §13 of `REFERENCE_METHOD.md` before you read §9–§12 of it.** §9–§12 describe the matching
cascade as it was BEFORE routing. They are still correct about how two candidates are ranked, and
wrong if you read them as describing the candidate set.

---

## §1 — ⛔ THE DATA YOU MUST CHECK FOR FIRST, AND ASK FOR IF YOU DON'T HAVE IT

**This is the single highest-value thing you can do that I could not.** I am in a cloud container:
no `engine/` build, no `%APPDATA%/OpenRA/Logs`, no `~/Downloads`, and every mod-hosting domain is
blocked by the egress proxy. You have a filesystem. **Look before you assume, then ask.**

### 1.1 First, inventory what is actually on your disk

```sh
grep -n '"root"' tools/reference/extract_peer_units.py   # the 17 source checkouts it looks for
python -c "import sys;sys.path.insert(0,'tools/reference');\
import extract_peer_units as e;print('\n'.join(sorted(e.PEERS)))"
python tools/reference/extract_peer_units.py --dry-run    # resolves every root, writes nothing
ls ~/Downloads                                            # ⚠ ACTUALLY LIST IT. Do not assume empty
```

⚠ There is no `--list`; the flags are `--mod <id>` (repeatable) and `--dry-run`.

`PEERS` in `tools/reference/extract_peer_units.py` names, for each source, a list of candidate
roots (e.g. `/home/user/openra/openra`, `~/Documents/GitHub/OpenRA`, `../OpenRA`). A source whose
root is missing is skipped **silently apart from one line of output** — `Fractured Realms: rifle
actor e1 not present` is what a miss looks like. Re-run the extractor and read every line.

### 1.2 Then ASK THE MAINTAINER for these four. All are ruled in; all are missing.

Each is a maintainer ruling whose DATA does not exist here, recorded in
`tools/balance/faction_routes.PENDING` so the gap is visible rather than silently absent.

| source | unblocks | what to ask for, concretely |
|---|---|---|
| **DTA** (Dawn of the Tiberium Age) | all four TD/RA1 factions — the ruled 1/3 third voice | the `rules*.ini` / `art.ini` set, or the extracted MIX contents. It is an Ares/INI mod, so there is no OpenRA yaml to resolve. **Promised for 2026-09-05 — ASK TODAY.** |
| **Rise of the East** | `asianalliance` (China) and `tkm` (GLA) | same — RA2/YR Ares mod, v3.0, three subfactions per side |
| **Emperor: Battle for Dune** | ⭐ **every** Dune faction, and it is the **ONLY** source anywhere for `ixian` and `corrino` | unit stats per house incl. the sub-houses (Ix, Tleilaxu, Guild, Sardaukar/Imperial) |
| **Dune: Spice Wars** | the Dune tier's second modern voice | unit stats per faction |

⭐ **Emperor turns two permanent "never"s into "pending".** `ixian` and `corrino` were both
recorded as having no counterpart in any source. That was a claim about the corpus, not about the
world — the same shape as the `LESSONS_LEARNED.md` entry *"'Not found' is a claim about your
search"*. Both are now `UNROUTED` with a ⏰ note pointing at Emperor.

### 1.3 And ASK for the one that is NOT a missing file — it is missing STRUCTURE

⛔ **Mental Omega and CnC Reloaded have no faction data, and it is NOT recoverable from this
tree.** I checked all three ways before concluding it:

* neither table in `docs/design/ORIGINAL_UNITS_RAW.md` has a faction column;
* neither is ORDERED by faction — rows sort by `kind`, then HP;
* there is no raw MO or CnCR source anywhere in the repo. `ORIGINAL_UNITS_RAW.md` is **hand-typed**;
  `synthesize_reference.py` READS it and does not generate it.

⛔ **Do not derive the factions from your own knowledge of the games.** That is exactly the
*"inferred and invented data that might be wrong"* the maintainer ruled against, and it would
silently poison four invented factions at once. Ask for the MO/CnCR rules, or for a faction column
added to the hand tables.

**Why this is the biggest single blocker:** Mental Omega is **game A** for four Tier-4 factions —
`asianalliance` (China), `latinsyndicate` (Latin Confederation), `steelconsortium` (Foehn Revolt),
and it is ruled into the RA2 tier as well. Until it lands, the RA2 tier runs at **1/2** rather than
the ruled **1/6**, and each Tier-4 faction has exactly ONE reference source instead of two.

### 1.4 Ask about these open RULINGS too (not data — decisions only the maintainer can make)

| # | question | why it is blocked |
|---|---|---|
| 1 | **TKM's second reference source** | Both TKM and Latin Syndicate are ruled onto GLA. Latin Syndicate also holds MO Latin Confederation; TKM holds nothing else, so if both draw on Generals Alpha `gla` they converge — and the matching law says a reference unit may be used ONCE, so the greedy would split them arbitrarily. TKM is currently `UNROUTED` (formula-only) rather than guessed at. |
| 2 | **FutureTech's second game** | Combined Arms `scrin` is **RESERVED** for the upcoming Cameo Scrin faction and must not be spent here. |
| 3 | **Naxis's second game** | It has OpenE2140 `ed` only — and `ed` may mirror `ucs`, which is FutureTech's. |
| 4 | **`cabal` and `forgotten` second games** | Shattered Paradise `cab` / `mut` only. |
| 5 | **Schwarzer Mond** | Earth 2150 Lunar Corporation is the documented inspiration and is not on disk. OpenE2140 is Earth **2140**. |
| 6 | **`redalert_japan`** | RA3 Empire is the documented inspiration; no RA3 mod is in the corpus. |
| 7 | **the "ymca mod"** | maintainer named a Combined Arms fork — *"more chaotic and less balanced… only try to use it for the scrin"*. Not identifiable from that name. Ask for the real name or a link. |
| 8 | **the vision ladder** | Ruled: 500-unit increments, `scout_vehicle` highest for vehicles, `scout` highest for infantry, aircraft and ships above both. **Blocked because the air and naval classes do not exist yet** — see `MISSING_CLASSES.md`. |

---

## §2 — WHAT YOU CAN DO THAT I COULD NOT

Read this as your comparative advantage. Spend your session on these, not on things a cloud
session can already do.

| capability | what it unblocks |
|---|---|
| **the boot gate** | `launch-game.cmd` → main menu. **CLAUDE.md rule 1 makes this mandatory for every commit of engine content.** I could not satisfy it, so every yaml change I found went to `docs/patches/` instead of into the tree. |
| **`docs/patches/02_cabal_avatar_dreadnought.patch`** | ⏰ **WAITING FOR YOU.** Ruled, authored, verified as far as a boot-less session honestly can. Read `docs/patches/README.md` for the apply-verify-boot-commit sequence, and **delete the patch in the same commit that lands it.** |
| **`docs/patches/01_bulletchem_hydraspit.patch`** | same; six files that must land TOGETHER or a gate breaks. Its README section spells out why. |
| **a complete tree** (`engine/` built, non-shallow clone) | ⛔ `docs/audit/latest/` is a MIXTURE of two environments and is owed **one clean regenerate**. A dozen audits read `engine/` C# or full git history; without them they scan a smaller corpus, report FEWER findings and still say PASS (`dead_warhead_fields` 27071 → 7014). `run_all` diverts to `docs/audit/degraded/` from an incomplete tree. Run `bash tools/audit/run_all.sh` on a complete tree and commit `latest/` **whole**. |
| **`~/Downloads` and the local mod library** | the four sources in §1.2. `CLAUDE.md`'s "don't trust, verify" explicitly names `ls ~/Downloads`. |
| **`git fetch --unshallow`** | a cloud clone is shallow, so `git log` starts at 2026-08-10 and lies by omission. Check `git rev-parse --is-shallow-repository` before ANY `git log`/`blame`/"when did this change" reasoning. |
| **GitLab push** | see §7.3 — the GitLab remote is 3 commits behind and this container has no credentials for it. |

---

## §3 — WHAT WAS BUILT, AND HOW THE PIECES FIT

Three commits, on top of the pre-existing reference layer:

```
1bf71cc3a  reference: route by faction, and place the units that have no counterpart
68e843aa1  balance: re-extract the ledgers after merging master -- 5 had drifted
ec7272b81  reference: resolve a unit's faction through its prerequisite building
```

### 3.1 The pipeline, end to end

```
  mods/cameo/**.yaml
        │  extract_stats.py                    (NEVER hand-edit a balance number — rule 3)
        ▼
  docs/balance/*.json  ── the LEDGER (raw stats + provenance)
        │
        │      the 17 reference mod checkouts (PEERS)
        │              │  tools/reference/extract_peer_units.py
        │              ▼
        │      docs/design/ORIGINAL_UNITS_PEER_OPENRA.md   (Document 5, 2568 rows)
        │      docs/design/ORIGINAL_UNITS_RAW.md           (Document 1, hand-typed: MO, CnCR, …)
        │              │  reference_distribution.peer_rows()
        │              ▼
        │      2878 rows, 15 sources, AFTER lineage de-duplication
        │              │
        ▼              ▼
  ┌───────────────────────────────────────────────────────────────┐
  │ faction_routes.py   WHICH reference factions may a Cameo       │  ← data only, no imports
  │                     faction see?      (ROUTES / PENDING /      │
  │                      UNROUTED / OPEN_SECOND_GAME)              │
  └───────────────────────────────────────────────────────────────┘
        │
        ▼
  assign_references.py    the 1:1 pairs, routed, greedy, explainable
        │                 (clause 11 = routing; --no-routing to compare)
        ▼
  faction_extrapolate.py  exchange rate  →  converted roster  →  rank placement
        │                 for every unit that got NO pair
        ▼
  docs/balance/derived/_faction_extrapolation.json      ← evidence, never a shipped stat
  docs/balance/review/<class>_references.md             ← what the maintainer reviews
        │
        ▼
  class anchors  →  fit_class  →  W11 sign-off  →  targets in the ledger
        →  apply_balance --confirm  (MAINTAINER ORDER)  →  re-extract  →  drift  →  BOOT GATE
```

### 3.2 The four files that matter, and what each owns

| file | owns | never |
|---|---|---|
| `tools/balance/faction_routes.py` | the ruled route map. **Data only** — it imports nothing, exactly like `reference_lineages.py` | never put logic here; never let a second copy of a route list exist anywhere |
| `tools/balance/assign_references.py` | the 1:1 matching law, now with routing as **clause 11** | never generate a review sheet with `--no-routing` |
| `tools/balance/faction_extrapolate.py` | exchange rates, converted rosters, rank placement, `--by-class` | never treat a placement as a stat to apply |
| `tools/reference/extract_peer_units.py` | reading the 17 checkouts into Document 5, incl. the faction column | never hand-edit Document 5; regenerate it |

---

## §4 — THE DESIGN DECISIONS, AND WHY. DO NOT RE-LITIGATE THESE.

Each of these cost real work to arrive at. They are written down so the next session does not
re-derive them — which `CLAUDE.md` rule 8f says has already happened more than once.

### 4.1 Routing replaces open matching (maintainer, 2026-09-04)

> *"most of the references are bullshit… instead of trying to match something completely unrelated
> we now try to map reference faction to our cameo factions."*

⭐ **The measurement that justifies it:** of the **1,852** proposals the old matcher produced,
**1,708 (92.2%) were cross-faction — and 599 of those carried the STRONG label.** The name score
was working correctly and answering the wrong question.

**What routing costs, stated plainly** (`assign_references.py` vs `--no-routing`):

| | routed | unrouted |
|---|--:|--:|
| actors in scope | 447 | 693 |
| assigned ≥1 reference | 325 | 596 |
| reaching the ≥2 floor | 53 | 454 |
| STRONG proposals | 140 | 721 |

That is the trade the ruling makes: far fewer proposals, and the ones that remain are same-faction.

### 4.2 An untagged reference row is NEVER admitted

Half the corpus carries no faction. Admitting untagged rows "just in case" reinstates exactly the
cross-faction matching the ruling removed — one untagged Combined Arms row would be visible to
every Cameo faction at once. **A route is a claim about identity; a missing tag is the absence of
one.** (`faction_routes.allows()`.)

### 4.3 A faction with no route is FORMULA-ONLY, not fallback-matched

A fallback would put every unrouted faction back where the rejected sheet was, and do it invisibly
— the rows would look like ordinary proposals. So an unrouted unit LEAVES SCOPE and is recorded in
`assign.formula_only` with the reason. Currently 5 factions: `tkm`, `schwarzermond`, `japan`,
`ixian`, `corrino`.

### 4.4 The mirror-merge rule (maintainer, 2026-09-04)

> *"since they are nearly identical we just regard them as one big faction with twice the units as
> reference!"*

⭐ **This is the general answer to the mirror problem and it beats choosing.** Picking one mirror
throws away half the roster; counting both double-counts one design. OpenHV's `sc` + `yi` are ONE
voice. Mechanically that is **two faction tokens on one source route** — the source still offers at
most one reference per Cameo unit, so it still votes once.

### 4.5 The faction ids are the TREE's, not the matrix document's

`FACTION_REFERENCE_MATRIX.md` Parts I–III were written with `redalert2mod_asianalliance`,
`tiberiandawn_gdi`. The mod's `InternalName`s — and every ACTOR PREFIX in every ledger — are
`asianalliance`, `td_gdi`.

⚠ **The long names are not fiction:** `redalert2mod_asianalliance` is the LEDGER FILE
(`docs/balance/redalert2mod_asianalliance.json`) and the ContentPack. It is just not the faction
id, and routing must key on the faction id because that is what an actor id carries.
`faction_routes.validate()` fails on any id that is not declared.

### 4.6 The extrapolation layer: rosters do not line up 1:1 (maintainer, 2026-09-04)

> *"not all reference factions have all the units from our factions or they have additional units
> we don't have… we can use reasoning and our existing stats and the unused extra reference units
> from their factions to somehow extrapolate something that roughly makes sense."*

Measured, the mismatch runs **both** ways: **557 reference rows unused**, while `ordos` has 25
Cameo units against **7** routed reference rows.

**Three steps, each measured rather than assumed:**

1. **The exchange rate.** `k = geometric mean over the matched pairs of (cameo_stat /
   reference_stat)`, per stat and per route. That is "use our existing stats", in one number. It is
   per stat because HP and range do not scale together across mods; per route because two sources
   disagree. **104 rates** across 27 (faction, source) routes today.
2. **The whole routed reference roster × k becomes Cameo-scale data** — including the units the
   reference faction fields and Cameo does not.
3. **A unit with no counterpart is placed by RANK.** Its percentile inside its own (faction, type)
   Cameo population is read off the converted reference distribution. **Cameo's roster decides the
   ORDER; the reference decides the SPREAD.**

⚠ `spread` (the geometric SD of a rate's per-pair ratios) is **reported, never acted on**. Where it
is large the two rosters do not scale by one number at all — `ts_nod ← Crystallized Nexus` `w_dps`
measures **324×** on 3 pairs. An honest wide rate is more useful than a hidden one.

### 4.7 A reference is NEVER a price

Routing and extrapolation decide only **where a unit sits in its class's distribution**.
`formula.py` still prices it, `apply_balance --confirm` still needs a maintainer order, and the
band law in `BALANCE_PIPELINE.md` §8.1a still applies. Say this out loud if anyone proposes writing
a placement into yaml.

---

## §5 — THE MEASURED STATE, WITH THE COMMAND FOR EVERY NUMBER

```sh
python tools/balance/faction_routes.py                  # the matrix + measured row counts
python tools/balance/faction_routes.py --check          # exit 1 if any ruled route resolves to nothing
python tools/balance/assign_references.py               # routed (default)
python tools/balance/assign_references.py --no-routing  # ⛔ comparison only — the rejected behaviour
python tools/balance/assign_references.py --review scout
python tools/balance/faction_extrapolate.py --report    # roster mismatch, per faction
python tools/balance/faction_extrapolate.py --rates     # the 104 exchange rates + spread
python tools/balance/faction_extrapolate.py --by-class  # ⭐ where an anchor can be fitted
python tools/balance/faction_extrapolate.py --faction naxis
python tools/balance/anchor_readiness.py
python tools/balance/class_membership.py --gaps
```

### 5.1 Routing coverage

* **19 of 24** Cameo factions routed; 5 formula-only by ruling.
* **7 factions have only ONE route** and are listed in `OPEN_SECOND_GAME` so they cannot look
  finished — a test enforces that (`test_a_faction_with_one_route_is_declared_open_or_unrouted`).
* `--check` is **green**: every ruled route resolves against the de-duplicated corpus.

### 5.2 Grounding, per class (`--by-class`)

**274 of 335** routed class members are grounded — 246 by a 1:1 pair, 28 rank-placed.
Members carrying **≥2 references: 95** (was 24 before the prerequisite hop).

⛔ **THREE ZEROES IN THAT TABLE ARE THE RULES WORKING, NOT HOLES.** I nearly reported them as a
defect; check before you do.

| class | members | why zero |
|---|--:|---|
| `support` | 105 | **all exempt** under matching-law clause 10 (MCV, engineer, harvester, transports, detectors) |
| `commando` | 27 | **100% carry `build_limit`** |
| `epic_vehicle` | 24 | **100% carry `build_limit`** |

The population rule (maintainer, 2026-08-30) excludes one-offs from the corpus on BOTH sides:
*"Cameo's heroes and epic units must be excluded since they will be balanced separately."* So there
is no peer row to match AND no Cameo row to match it to.

⭐ **After the prerequisite-hop fix, NO class is left routed-but-ungrounded.**

### 5.3 Faction tagging in the corpus, after the fix

| type | before | after |
|---|--:|--:|
| infantry | 25% | **39%** |
| vehicle | 40% | **52%** |
| ship | 50% | **84%** |
| aircraft | 52% | **62%** |
| defense | 80% | 82% |
| building | 36% | 37% |

### 5.4 The bug that produced §5.3, because it is the template for the next one

Found by asking why `heavy_sniper` — a **SIGNED** class — had both members ground to nothing, and
why `ra1_soviets` routed to **zero** reference infantry while OpenRA Red Alert plainly ships Soviet
infantry.

```
E2 (Grenadier):  Prerequisites: ~barr, ~techlevel.infonly
BARR:            Prerequisites: anypower, ~structures.soviet, ~techlevel.infonly
```

OpenRA gates most infantry on a **barracks**, not a faction. `factions_of()` read only the unit's
own line and returned nothing. It already parsed `structures.soviet` → `soviet` correctly — it just
never followed the hop. It now resolves transitively through prerequisite ACTORS at
`PREREQ_DEPTH = 2`.

⚠ **The cap is deliberate.** Further along the chain sits infrastructure both sides build
(`anypower` → any power plant), and a faction attached through shared infrastructure is worse than
no faction at all. **A direct gate still wins outright** — an inherited one is only consulted when
the unit's own line says nothing.

---

## §6 — WHAT TO DO NEXT, IN ORDER

⚠ Apply `CLAUDE.md`'s **DRIFT TEST** to each of your own actions: *"does this move a NUMBER for one
unit, or does it move the SYSTEM?"* PRIORITY 0 is the class anchors and the unit templates.

1. **Ask for the §1.2 data and the §1.4 rulings.** Everything below is smaller than this.
2. **Land the two patches in `docs/patches/`** — you have the boot gate, I did not. Delete each
   patch in the commit that lands it.
3. **One clean `bash tools/audit/run_all.sh`** from a complete tree, and commit `latest/` WHOLE.
   Do not cherry-pick report files: Windows writes `mods\cameo\…` and Linux writes `mods/cameo/…`,
   so a cross-platform diff is dirty even between two complete trees.
4. **Regenerate the per-class review sheets.** Only `scout` exists today
   (`docs/balance/review/scout_references.md`). Do it class by class:
   `python tools/balance/assign_references.py --review <class>`. Review one class at a time — that
   is the ruled procedure (`REFERENCE_METHOD.md` §9.9) — and note that WEAK rows are struck into a
   §3 summary rather than presented for review, by maintainer ruling.
5. ⛔ **Do NOT sign any class on this evidence yet.** Most routed units hold ONE reference, not the
   ≥2 floor. That does not change until MO / CnCR / DTA land. **Never set `signed_off: true`
   without a maintainer order — signing is a maintainer act.**
6. **The anchor hygiene items that are already ruled and still open** (`anchor_readiness.py`):
   * `heavy_sniper → td_gdi_heavysniper` is **SIGNED and not a member of its own class** — it sits
     in `^SniperInfantryTemplate` so it classifies as `pure_sniper`, and
     `^HeavySniperInfantryTemplate` is one of the five dead templates (`CLASS_MOVES.md` §0);
   * `special_forces` is signed on an anchor at the **12th percentile of 16 members**;
   * `support` should be marked EXEMPT — **110 members, 105 of them buildable, and all 105
     exempt under clause 10.** It cannot be anchored from references at all, so leaving it in the
     sign-off queue is misleading. (`anchor_readiness` counts 110 because it includes
     non-buildables; `--by-class` counts 105. Both are right; say which you mean.)
   * three classes were signed on a single scored row.
7. **PRIORITY 0 item 2 — unit templates.** `python tools/audit/audit_class_templates.py`:
   97 defects (67 with no `Inherits@Template:`, 6 with more than one, 24 add-on only). The 67 group
   into **8 cohorts + 32 singles**, so it is ~40 rulings, not 67. **This is engine content — it
   needs your boot gate.**
8. **The vision ladder** (§1.4 #8) once the air/naval classes exist.

---

## §7 — REPOSITORY, BRANCH AND REMOTE STATE

### 7.1 Where the work is

| | |
|---|---|
| branches | `claude/bot_insurance_dynamic_trait` and `claude/docs-audit-reorganize-xgzwhr`, both at **`ec7272b81`** |
| PRs | **#325** (bot insurance + this work) and **#321** |
| merged in | `origin/master` through `4deaee086` |

### 7.2 ⛔ 132 branches I pushed to GitHub by mistake — please clean up

The maintainer asked me to restore **one** branch (`agent/introduce-scrin-faction`). I saw GitHub
holding **15** branches against GitLab's 148, concluded it was data loss, and pushed the difference.
**The conclusion was wrong:** those branches live in contributors' FORKS and are reachable through
their PRs — PR #252 (Scrin) has head `Blackrobe/Cameo-mod:agent/introduce-scrin-faction` and was
never broken.

Nothing was overwritten (identical SHAs, no PR affected), but the canonical repo's branch list went
**15 → 148** (132 + the one Scrin branch that was asked for). **Deleting a remote branch is blocked by a permission classifier in the cloud harness and
the GitHub MCP has no delete-branch tool, so I could not undo it.** You can:

```sh
# the exact list is the 132 branches on gitlab that were not on origin before 2026-09-05.
# verify each still points at the SHA that was pushed, THEN delete:
git push origin :refs/heads/<branch>
```

⚠ **Keep `agent/introduce-scrin-faction`** — that one was asked for.

### 7.3 GitLab

`https://gitlab.com/openra-cameo/cameo-mod` is a live second remote. **It is 3 commits behind
GitHub** because this container has no GitLab credentials.

⭐ **The durable fix, and it is free:** GitLab project → **Settings → Repository → Mirroring
repositories** → URL `https://github.com/cameo-mod/Cameo-mod.git`, direction **Push**, auth a
GitHub PAT with `repo` scope. Every push to GitLab then replays to GitHub within ~5 minutes.

⛔ Pull mirroring (GitHub → GitLab) is **Premium-only** on gitlab.com, so true two-way auto-sync is
not available on the free tier — and you would not want it: two mirrors pointing at each other
fight over any branch that moves on both sides. **Pick one writable side.**

⚠ Verified 2026-09-05: `git rev-list gitlab/<branch> --not origin/<branch>` = **0**. No GitLab
commit is missing from GitHub.

### 7.4 Two closed DRAFT PRs, if the maintainer asks about "missing" ones

Both are Blackrobe's, both have intact fork branches, both reopen with one call:

* **#244** "Fix damage-scaled physical state stacking" — `mergeable_state: clean`.
  ⚠ Its premise may be superseded: `HANDOFF.md` §3.0c records that
  `audit_physical_state_warheads` was demanding percentage twins the AreaDamage fold had already
  folded away, and that was fixed **in the audit, not the yaml** — the opposite direction to this
  PR. Check before reopening.
* **#275** "collapse misclassified weapon blends" — `mergeable_state: dirty`, i.e. it has a merge
  conflict against current master. Resolve first.

⚠ **The GitHub search API is unreliable on this repo** — `search_pull_requests` for "scrin"
returned **0 results** while PR #252 was open. **Enumerate with `list_pull_requests`, do not
search.** This is the `LESSONS_LEARNED.md` "'Not found' is a claim about your search" trap wearing a
different hat.

---

## §8 — TRAPS. EVERY ONE OF THESE WAS A REAL BUG IN THIS SESSION.

Each is now a guard plus a test. They are listed because the *shape* of each recurs.

| # | the trap | the guard |
|---|---|---|
| 1 | **A column that exists upstream and is dropped on read is indistinguishable from one never extracted.** `peer_rows()` had the faction column in the document and dropped it — exactly the bug `cost` had earlier. | `test_the_faction_column_survives_the_reader` |
| 2 | **An empty reference pool makes rank placement the IDENTITY, and it does not look like one.** Reading a unit's own percentile off its own roster returns its own value. `ordos` reported **20** such placements as coverage. | `test_an_empty_reference_places_nothing`, `test_placements_are_never_the_identity` |
| 3 | **Nearest-point placement collapses a small roster.** OpenE2140 `ed`'s four infantry rows put **six** Naxis infantry, spanning 20,000–96,000 HP, on one value. Fixed by interpolating in **log** space — the space every aggregate here already uses. | `test_does_not_collapse_distinct_percentiles` |
| 4 | ⛔ **A reference faction can be uninformative for a whole type, and averaging hides it.** OpenE2140 `ed` fields Androids A01–A04 at HP 28/28/28/20 and speed 50/50/50/50. Placing Naxis's nine infantry against that would have **deleted a roster's variety while looking like evidence.** | `MIN_DISTINCT`; `test_a_reference_with_no_spread_places_nothing` |
| 5 | **Pooling only the LEFTOVERS empties the pool where it is needed most.** Infantry is where 1:1 matching succeeds, so almost no infantry row is left over — and infantry was 59 of the 122 unpaired units. A distribution is made of all its members; a row does not leave it by having been matched. | `converted_pool()` pools the whole routed roster |
| 6 | **The rank placer happily placed MCVs, carryalls and drone miners** — 41 placements on actors the assignment had already exempted. Visible only because the REPORT applied the exemption and the placer did not, so the tool disagreed with itself. | `build()` uses the assignment's scope |
| 7 | **Unfiltered, the "extra" reference units are mostly the mod's ECONOMY.** 36 of Shattered Paradise's 48 unused `gdi` rows are buildings. It also removes the shared-content problem for free: the 9 rows tagged with ≥80% of their own source's factions (`C.A.B.A.L. Construction Yard` carries all five) are ALL buildings. | combat-types-only filter; `test_virtual_members_are_combat_types_only` |
| 8 | **`derived/` files are SIDECARS to a raw ledger of the same name.** A cross-cutting artifact needs the `_` prefix, as `_model.json` does. | `test_every_sidecar_has_a_raw_counterpart` |
| 9 | **A ruled label that does not match the pool's label does nothing, silently, for weeks.** This is the `RA2/YR` vs `RA2/YR (raw INI)` failure that forced `reference_lineages.py` into existence. A route is the same shape of claim. | `faction_routes.validate()`; two tests that inject a bad label and a bad token |

⚠ **One pre-existing failure you will see and should NOT chase:** `test_ledger_split` fails on
`reference_distributions.json has no raw ledger`. It predates all of this and is already recorded
in `BOOT_GATE_RUNBOOK.md`. Also, 6 test modules error with `ModuleNotFoundError: pytest` in a
container without pytest — an environment gap, not a defect.

---

## §9 — THINGS NOT TO DO

1. ⛔ **Never hand-edit a balance number.** `extract_stats` → ledger → `apply_balance --confirm`,
   and `--confirm` needs a maintainer order. (CLAUDE.md rule 3.)
2. ⛔ **Never `git add -A` / `.` / `--all`.** Several contributors have live WIP in this tree.
   (rule 2.)
3. ⛔ **Never generate a review sheet with `--no-routing`.** That flag exists ONLY so the two can be
   compared; it is the behaviour the maintainer rejected.
4. ⛔ **Never admit an untagged reference row** to make coverage look better. See §4.2.
5. ⛔ **Never invent faction data** for MO/CnCR from game knowledge. See §1.3.
6. ⛔ **Never add a second private copy of a route list, a source list or a class map.** Three
   drifted copies of the de-dup rulings (one carrying a live bug) and three of the template→class
   map are why `reference_lineages.py` and `class_membership.py` exist.
7. ⛔ **Never hand-parse yaml.** Read through `miniyaml.Ruleset.resolve_weapon` / `.resolve`, and
   pull Versus with `weapon_efficiency.versus_of(node)`. (rule 8e — a bespoke line-scanner once
   produced measurements that were internally consistent and completely wrong.)
8. ⛔ **Never `git checkout -- .`**, and never wide-add another agent's WIP. (rule 6.)
9. ⛔ **Never touch `engine/`** expecting it to persist — it is `.gitignore`d, has no `.git`, and
   `git ls-files engine` returns zero. The next `make all` deletes your edits. (rule 7.)
10. ⛔ **Never add `github.com/Zeruel87/Cameo-mod`** as a remote. Abandoned fork; enforced by
    `bash_guard.py` rule 1b. And the two `Zeruel87` appearances in the tree are **ART CREDIT** —
    the tileset categories and `credits.txt` — never sweep them.
11. ⛔ **`ScheduleWakeup`-style polling and "the suite exits 0" are not gates.** The commit gate is
    the boot gate: main menu reached, no NEW `exception-*.log`. And when reading a backgrounded
    run's exit code, write `echo "exit=$?" >> "$OUT"` and read THAT — a task notification reports
    the wrapper's status, which is why "the suite is green" was reported repeatedly while
    `run_all.sh` exited 1 every time.

---

## §10 — A FEW THINGS THAT ARE JUST USEFUL TO KNOW

* **`~self` vs `~!self`.** `~forgotten_mutant_wild` (self as its own prerequisite) = never
  buildable, spawn-only. `~!tkm_bigshiee` = "NOT self" = a build-limit one-off that IS legitimately
  buildable. **3 actors vs 562** — getting this backwards prices 562 units as unbuildable.
* **`AttackFrontal` vs `AttackTurreted`** is the frontal-facing discriminator, **not** the presence
  of `Turreted`. A unit can carry `Turreted` for weapon tracking and still attack frontally, and
  `Armament.Turret` defaults to `"primary"`. Getting this wrong produced two false "defect" reports
  about the Neo Cymek.
* **The dreadnought range inversion is a PLAYTEST RULING, not a defect** — maintainer:
  *"in our in game testing dreadnoughts were far too strong and it was mostly because of their
  range, and tank destroyers got slightly more range to counter them."* Pinned in `doc_claims.yaml`.
* **Gatling spin-up** is an exact 44-actor set: `^GatlingSpinUpTurretBehavior` + 2 descendants.
  `reload 0.95^10 = 0.599 → ReloadDelayTo 60`; `range 1.02^10 = 1.219 → RangeTo 122`. That is
  **1.67× sustained DPS at 1.22× range, with damage per shot unchanged.**
* **An armed building is a DEFENCE.** Buildings are excluded from the `overall` population and
  `defense` is its own population, so an armed structure typed `building` was voting on **nothing**.
  94 rows were affected; the defence population went 85 → 179 across 5 → 13 sources.
* **Crystallized Nexus `steel` is Steel TALONS**, a GDI division (Titan, Wolverine, Juggernaut) —
  **not** Steel Consortium. `gdf` and `zocom` are likewise GDI branches, and Combined Arms' `talon`
  is the same Steel Talons. Name similarity nearly produced exactly the error this whole redesign
  exists to remove.
* **Shattered Paradise's `mut` IS Cameo's Forgotten**, and `cab` IS CABAL — direct counterparts no
  name matcher would ever have found. That is routing paying for itself.
* **A memory is not a repository document.** Provenance only, never authority. If it carries a rule,
  a number or a decision others must follow, promote it into `DESIGN.md` /
  `LESSONS_LEARNED.md` / `doc_claims.yaml` in the same session. The live doc set holds **zero**
  `memory <name>` citations — keep it that way.

---

## §11 — THE COMMIT GATE, RESTATED BECAUSE YOU CAN ACTUALLY MEET IT

```sh
python -m unittest discover -s tools/tests -t tools/tests   # ~947 tests
python tools/audit/find_empty_warhead.py                    # must print 0
python tools/balance/verify_generator_sync.py
bash tools/audit/run_all.sh                                 # bash ONLY — PowerShell `>` writes UTF-16
python tools/balance/extract_stats.py --check               # 0 drifted
python tools/balance/faction_routes.py --check              # every ruled route resolves
```

…then **the boot gate**: `launch-game.cmd`, main menu reached (`perf.log` ends with
`MenuPostProcessEffect.PostWorldLoaded`), **no NEW `exception-*.log`** in `%APPDATA%/OpenRA/Logs`.
Snapshot the log list BEFORE launching. Menu proof is grepping `perf.log`, not eyeballing its last
line. If Smart App Control blocks the launch, use one of the four documented options in
`LESSONS_LEARNED.md` and **record the SAC state in the commit message**. Never silently skip it, and
never claim it passed when it did not.

⚠ **Re-extract before every commit that moves a balance number**, not at the end of the session.
`audit_balance_drift` has gone red three times because yaml commits landed without one — including
on master, five ledgers deep, which is what `68e843aa1` fixed.

Sign your own trailer with your **real** model name. Never copy one from a previous commit or from
`CLAUDE.md` — those are templates, and copying one makes a newer model misreport itself as an older
one.
