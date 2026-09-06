# The faction reference matrix

> ⛔ ~~**A PLAN, NOT AN IMPLEMENTATION.** Nothing is wired.~~ **STRUCK 2026-09-04 — it is wired.**
> Routing is implemented and default-on in `assign_references.py`; the route map lives in
> `tools/balance/faction_routes.py`. **Read [PART IV](#part-iv--wired-and-what-the-wiring-measured-2026-09-04-later-session)
> first** — it carries what the wiring measured, and it corrects the faction ids used in Parts
> I–III, which do not exist in the tree.

**Maintainer ruling 2026-09-04, after reviewing that sheet:** *"most of the references are
bullshit… what does the Asian Alliance Militia have to do with the Combined Arms Infiltrator? …
instead of trying to match something completely unrelated we now try to map reference faction to
our cameo factions."*

⭐ **The diagnosis is right and it explains every bad row.** Matching searched all 15 sources for
any unit with a similar name or shape. A Cameo RA2 Soviet conscript and a Mental Omega Latin
Confederation militia can then compete for the same reference. **Faction routing removes the
question instead of answering it better:** an Asian Alliance unit may only draw on Mental Omega
China, so *"Animal Alligator"* was never a candidate in the first place.

⚠ The one row the maintainer accepted proves the principle: `ra2_soviets_conscript` ← RV/CnCR/MO
**Conscript**, *"exactly the same unit"* — same faction, same role, same name.

---

## §1 — ⛔ What blocks this today

| blocker | detail |
|---|---|
| **No faction column anywhere** | Neither `ORIGINAL_UNITS_RAW.md` (DOC1) nor `ORIGINAL_UNITS_PEER_OPENRA.md` (DOC5) records a faction. Both need re-extracting. |
| **DTA has no unit rows at all** | Required for all four TD/RA1 factions. The maintainer is providing the INIs — **ask again tomorrow.** |
| **RA2 Reborn + Red Resurrection carry NO unit stats** | They exist only in `versus_raw.json` as warhead armour profiles. The ruled 1/6 weighting cannot include them yet — in practice RA2 is **1/4**, not 1/6. |
| **Mental Omega and CnC Reloaded have no faction data** | They are hand-typed tables with `Unit · kind · HP · Cost · Spd · Weapon · Dmg · Rld · Rng`. ⛔ **This is the big one — MO is the sole source for every invented faction.** |

### ⭐ But faction IS recoverable from the OpenRA clones

Measured over each clone's buildable roster, reading `Buildable.Queue` and `Prerequisites`:

| source | buildable | faction-tagged | factions found |
|---|--:|--:|---|
| **Romanov's Vengeance** | 832 | **831 (100%)** | allies · soviets · yuri · uk · france · usa · iraq · cuba · baku |
| **Shattered Paradise** | 317 | **317 (100%)** | gdi · nod · cabal · **mutant** · scrin |
| **Combined Arms** | 503 | 101 (20%) | gdi · nod · td · ra · soviet · allies · yuri · scrin — ⚠ its tokens mix faction with unit names (`~vehicles.mtnk`), so the extractor needs a token whitelist, not a regex |
| **OpenE2140** | — | — | **ucs · ed** |

⭐ **Shattered Paradise's `mutant` is Cameo's Forgotten** — a direct faction counterpart that name matching would never have found.

---

## §2 — The ruled tiers

### TD + RA1 — one third each

| Cameo faction | reference factions | weight |
|---|---|---|
| `tiberiandawn_gdi` | DTA **GDI** · Combined Arms **GDI** · Cameo | 1/3 each |
| `tiberiandawn_nod` | DTA **Nod** · Combined Arms **Nod** · Cameo | 1/3 each |
| `redalert_allies` | DTA **Allied** · Combined Arms **Allies/RA** · Cameo | 1/3 each |
| `redalert_soviets` | DTA **Soviet** · Combined Arms **Soviet** · Cameo | 1/3 each |

⛔ **Blocked on the DTA INIs.** Until they arrive these four factions have Combined Arms + Cameo
only, i.e. 1/2 each rather than 1/3.
⚠ `redalert_japan` is **not** in this tier — it is a Cameo invention (§3).

### RA2 — one sixth each, ruled; one quarter, achievable

| Cameo faction | ruled sources | usable today |
|---|---|---|
| `redalert2_allies` | RV · MO · CnCR · RA2 Reborn · Red Resurrection · Cameo | RV **allies** · MO · CnCR · Cameo |
| `redalert2_soviets` | same six | RV **soviets** · MO · CnCR · Cameo |
| `redalert2_yuri` | same six | RV **yuri** · MO · CnCR · Cameo |

⚠ RV alone carries faction tags; MO and CnCR would contribute unrouted until they gain a faction
column.

### TS — one quarter each

| Cameo faction | reference factions |
|---|---|
| `tiberiansun_gdi` | CnCR · Shattered Paradise **gdi** · Crystallized Nexus · Cameo |
| `tiberiansun_nod` | CnCR · Shattered Paradise **nod** · Crystallized Nexus · Cameo |
| `tiberiansun_cabal` | CnCR · Shattered Paradise **cabal** · Crystallized Nexus · Cameo |
| `tiberiansun_forgotten` | CnCR · Shattered Paradise **mutant** ⭐ · Crystallized Nexus · Cameo |

---

## §3 — The invented factions: research

⭐ **The inspiration map already exists** — `BALANCE_SYNTHESIS.md` §3, written 2026-07-25. The work
is connecting each documented inspiration to a mod actually on disk.

| Cameo faction | documented inspiration | reference faction | on disk? |
|---|---|---|---|
| `redalert2mod_syndicate` (Latin Syndicate) | **MO Latin Confederation** — *"basically the same"* | MO **Latin Confederation** | ⚠ MO has no faction column |
| `redalert2mod_asianalliance` | **Generals China + MO China** + CA China refs | MO **China** · Generals Alpha **China** | ⚠ same; GA mod id unresolved |
| `redalert2mod_consortium` (Steel Consortium) | **MO Foehn Revolt** + Earth 2150 LC | MO **Foehn** | ⚠ same |
| `redalert2mod_futuretech` | Earth 2140/50 **UCS** + RA3 FutureTech | ⭐ **OpenE2140 `ucs`** | ⭐ **YES — on disk and faction-tagged** |
| `redalert2mod_schwarzermond` | Iron Sky + **Earth 2150 Lunar Corporation** | ⚠ Earth **2150** is not on disk; OpenE2140 is Earth **2140** (`ucs`/`ed`) | partial |
| `redalert2mod_naxis` | WW2 parody + Iron Sky | ⛔ no counterpart found in any source | **no** |
| `redalert2mod_tkm` | not in §3 | ⛔ unidentified — needs a maintainer answer | **no** |
| `redalert_japan` | RA3 Empire + WW2 Japan + Touhou | ⛔ no RA3 mod in the corpus | **no** |

### ⭐ The single best find

**FutureTech ← OpenE2140's `ucs`.** `BALANCE_SYNTHESIS` §3 names Earth 2140's UCS as its
inspiration, and OpenE2140 is cloned, resolving, and faction-tagged with exactly `ucs`. That is a
documented intent meeting available data — the only invented faction that can be routed today.

### ⚠ Three factions have no reference at all

`naxis`, `tkm` and `redalert_japan` have no counterpart in any of the 15 sources. **They should be
formula-only from a grounded class anchor** — the ruling already made for units with no reference,
rather than forcing a bad match, which is exactly what produced the rejected sheet.

---

## §4 — How auto-detection would then work

The goal: *"Asian Alliance is MO China, so their Lynx is the equivalent of the Qiling."*

With faction routing the search space collapses from 2,878 rows to one faction's roster — perhaps
30 units — and within it the existing cascade is enough:

1. **route** — `asianalliance_lynxtank` may only see MO China
2. **filter by type** — vehicles only
3. **filter by class** — MBT
4. **rank by the cascade** — name, then tier, then role/shape, then cost

MO China fields one MBT. The Qiling falls out **without needing a name match at all**, which is
precisely why the Lynx/Qiling and Rusher/Jaguar pairs are undiscoverable by today's matcher.

⚠ Where a faction fields two units of one class, the cascade still decides, and the MO wiki is the
tie-breaker the maintainer named for unclear roles.

---

## §5 — What has to happen, in order

1. ⛔ **Add a faction column to the peer extractor** and re-extract DOC5. RV and SP give 100%
   immediately; Combined Arms needs a token whitelist.
2. ⛔ **Get faction data for Mental Omega and CnC Reloaded.** They are hand tables. Without this
   every invented faction stays unroutable — **the biggest single blocker in this document.**
3. **Ask for the DTA INIs** (promised for 2026-09-05) and extract a full roster.
4. **Confirm the faction map** in §3, especially `tkm` and the three with no counterpart.
5. **Then** rewrite matching to route by faction, and regenerate the scout sheet to compare.

⚠ Until step 5, **no class should be signed on reference evidence.** The scout sheet stands
rejected.

---

# PART II — THE MATRIX (2026-09-04)

**Ruling:** *"Always have at least 2 reference factions from different games for each cameo
faction!"* — mirrors or not, no measurement first. Applied below.

⚠ **THE MIRROR PROBLEM IS WHY.** Two reference factions from the SAME game may be mirrors of each
other, and extracting both then yields no extra information — every Cameo unit would land on stats
identical to its counterpart. `OpenE2140`'s `ucs` and `ed` look exactly like this: both are named
*Mobile Air Base · Mobile Refinery · Mobile Defense Tower*. **A second GAME, not a second faction,
is what guarantees uniqueness.**

⚠ And the reference decides only **where a unit sits in its class's distribution.** The balance
formula still prices it. These are inputs to placement, not final stats.

## §6 — Every faction now available

| source | factions |
|---|---|
| Generals Alpha | **`prc`** (China) · **`gla`** (Global Liberation Army) · `usa` |
| Romanov's Vengeance | `allies` · `soviets` · `psicorps` · `bakupact` + 27 subfactions |
| Combined Arms | `gdi` · `nod` · `allies` · `soviet` · `yuri` · `scrin` · `talon` · `shadow` |
| Shattered Paradise | `gdi` · `nod` · `cab` · **`mut`** · `scr` |
| Crystallized Nexus | `gdi` · `nod` · `gdf` · `steel` · `zocom` |
| OpenE2140 | **`ucs`** · `ed` |
| OpenRA TD / TS / RA / D2K | `gdi` · `nod` / `gdi` · `nod` / `allies` · `soviet` / `atreides` · `harkonnen` · `ordos` |
| Valiant Shades | `allies` · `soviets` |
| OpenHV | `yi` · `sc` — ⚠ unidentified, Polish-named sci-fi, no obvious Cameo counterpart |

⛔ **A near-miss worth recording: Crystallized Nexus `steel` is STEEL TALONS**, a GDI division
(Titan, Wolverine, Juggernaut) — **not** Steel Consortium. `gdf` and `zocom` are likewise GDI
branches, and Combined Arms' `talon` is the same Steel Talons. Name similarity nearly produced
exactly the class of error this whole redesign exists to remove.

## §7 — The matrix

⭐ = confident · ⚠ = proposed, wants your ruling · ⛔ = no second game exists

### Tier 1 — TD and RA1 (ruled 1/3 each)

| Cameo faction | game A | game B | game C | status |
|---|---|---|---|---|
| `tiberiandawn_gdi` | **DTA** gdi | Combined Arms `gdi` | OpenRA TD `gdi` | ⭐ 3 games |
| `tiberiandawn_nod` | **DTA** nod | Combined Arms `nod` | OpenRA TD `nod` | ⭐ |
| `redalert_allies` | **DTA** allied | Combined Arms `allies` | OpenRA RA `allies` | ⭐ |
| `redalert_soviets` | **DTA** soviet | Combined Arms `soviet` | OpenRA RA `soviet` | ⭐ |

⛔ **DTA pending — ask the maintainer 2026-09-05.** Until then each has two games, which still
satisfies the rule.

### Tier 2 — RA2 (ruled 1/6, achievable 1/4)

| Cameo faction | game A | game B | game C | status |
|---|---|---|---|---|
| `redalert2_allies` | Romanov's Vengeance `allies` | Valiant Shades `allies` | MO / CnCR (unrouted) | ⭐ 2 games |
| `redalert2_soviets` | Romanov's Vengeance `soviets` | Valiant Shades `soviets` | MO / CnCR | ⭐ |
| `redalert2_yuri` | Romanov's Vengeance `psicorps` | Combined Arms `yuri` | MO / CnCR | ⭐ |

⚠ RV and *Yuri's Revenge on OpenRA* are ONE lineage and already collapsed — they do not count as
two games. Valiant Shades and Combined Arms are the genuine second voices.

### Tier 3 — TS (ruled 1/4 each)

| Cameo faction | game A | game B | game C | status |
|---|---|---|---|---|
| `tiberiansun_gdi` | Shattered Paradise `gdi` | Crystallized Nexus `gdi` | OpenRA TS `gdi` | ⭐ 3 games |
| `tiberiansun_nod` | Shattered Paradise `nod` | Crystallized Nexus `nod` | OpenRA TS `nod` | ⭐ |
| `tiberiansun_cabal` | Shattered Paradise `cab` | ⚠ Combined Arms `scrin`? | — | ⚠ needs a 2nd |
| `tiberiansun_forgotten` | ⭐ Shattered Paradise `mut` | ⚠ Crystallized Nexus `gdf`? | — | ⚠ needs a 2nd |

### Tier 4 — the invented RA2 factions

| Cameo faction | game A | game B | status |
|---|---|---|---|
| `redalert2mod_asianalliance` | MO **China** | ⭐ **Generals Alpha `prc`** | ⭐ exactly as ruled |
| `redalert2mod_syndicate` | MO **Latin Confederation** | ⭐ **Generals Alpha `gla`** | ⭐ GLA is guerrilla / black-market / explosives — the LC archetype |
| `redalert2mod_futuretech` | ⭐ **OpenE2140 `ucs`** | ⚠ Combined Arms `scrin`? | ⚠ needs a 2nd |
| `redalert2mod_naxis` | ⚠ OpenE2140 `ed` | ⛔ none | ⛔ and `ed` may mirror `ucs` |
| `redalert2mod_consortium` | MO **Foehn Revolt** | ⛔ none — `steel` is Steel Talons | ⛔ |
| `redalert2mod_schwarzermond` | ⛔ Earth **2150** LC not on disk | ⛔ none | ⛔ |
| `redalert2mod_tkm` | ⛔ unidentified | ⛔ | ⛔ |
| `redalert_japan` | ⛔ no RA3 mod in the corpus | ⛔ | ⛔ |

### Tier 5 — Dune

| Cameo faction | game A | game B | status |
|---|---|---|---|
| `d2k_ordos` | OpenRA D2K `ordos` | OpenRA Dune II `ordos` | ⭐ measured INDEPENDENT (16% agreement) — genuinely two games |
| `d2k_atreides` · `d2k_harkonnen` | same pair | | ⭐ |
| `d2k_ixian` | ⛔ House Ix is Emperor-only, not on disk | ⛔ | ⛔ |

## §8 — What is still open

1. ⛔ **MO and CnC Reloaded have no faction column** — hand tables. Every Tier-4 mapping above
   depends on it. **Biggest blocker.**
2. ⛔ **DTA** — ask 2026-09-05.
3. ⚠ **Five factions have no second game**: `consortium`, `schwarzermond`, `naxis`, `tkm`,
   `redalert_japan`, plus `d2k_ixian`. They are formula-only until one is found.
4. ⚠ **Three need a second choosing**: `tiberiansun_cabal`, `tiberiansun_forgotten`,
   `redalert2mod_futuretech`.

---

# PART III — rulings of 2026-09-04 (later session)

## §9 — ⭐ THE MIRROR-MERGE RULE

**Maintainer, on OpenHV's two near-identical factions:** *"since they are nearly identical we just
regard them as one big faction with twice the units as reference!"*

⭐ **This is the general answer to the mirror problem, and it is better than choosing.** Picking one
mirror throws away half the roster; using both as separate voices double-counts one design. Merging
them into a **single voice with twice the units** keeps every data point and counts the source once.

**Applied:** `sc` + `yi` become one **OpenHV** voice of **80 units**. Justified on identity too —
Steel Consortium fields energy weapons, shields *and* railguns, which is `yi`'s lightning and force
fields plus `sc`'s railguns and howitzers.

⚠ The two are measurably near-mirrors: identical composition (17 vehicles · 7 buildings · 6
aircraft · 5 defenses · 5 ships each), the same buildings, and swapped weapon flavour —
Lightning Tank against Railgun Tank, Drone Ship against Railgun Boat.

## §10 — The updated Tier-4 map

| Cameo faction | game A | game B | game C | status |
|---|---|---|---|---|
| `redalert2mod_asianalliance` | MO **China** | Generals Alpha **`prc`** | ⚠ **RotE China** | ⭐ ruled |
| `redalert2mod_syndicate` (Latin) | MO **Latin Confederation** | a **GLA** source | | ⭐ ruled |
| `redalert2mod_tkm` | ⭐ **GLA** — *"they look and feel like they are GLA"* | the other GLA source | ⛔ needs a third to stay distinct from Latin Syndicate | ⚠ |
| `redalert2mod_consortium` | MO **Foehn Revolt** | ⭐ **OpenHV (merged, 80 units)** | | ⭐ ruled |
| `redalert2mod_futuretech` | **OpenE2140 `ucs`** | ⛔ open — Scrin is now reserved | ⚠ |
| `redalert2mod_naxis` | ⭐ **OpenE2140 `ed`** — *"ED is a heavy tank faction so the same as Naxis"* | ⛔ open | ⚠ |
| `redalert2mod_schwarzermond` | ⛔ Earth 2150 not on disk | ⛔ open | ⛔ |

⛔ **Combined Arms `scrin` is RESERVED** for the upcoming Cameo Scrin faction and must not be spent
on Consortium or FutureTech.

⚠ **TKM and Latin Syndicate both draw on GLA**, so each needs a distinct partner or they converge:
Latin Syndicate has MO Latin Confederation; **TKM's second is still open.**

## §11 — ⛔ Sources the maintainer must supply

Neither can be fetched here — both are Westwood/Ares INI mods whose rules live inside MIX archives,
and every mod-hosting domain is blocked by this environment's egress proxy.

| mod | needed for | status |
|---|---|---|
| **DTA** | all four TD/RA1 factions | promised **2026-09-05** — ASK |
| **Rise of the East** | Asian Alliance (China) · TKM (GLA) | ⭐ newly identified — RA2/YR mod adding Generals' China and GLA, three subfactions each, v3.0 |

⚠ Also unresolved: the maintainer mentions a **Combined Arms fork** — *"the ymca mod … more chaotic
and less balanced … only try to use it for the scrin"*. Not identified from the name; needs the
real name or a link before it can be assessed.

---

# PART IV — WIRED, AND WHAT THE WIRING MEASURED (2026-09-04, later session)

⭐ **The banner at the top of this document is now false and is struck below.** Routing is
implemented, tested and default-on:

| what | where |
|---|---|
| the ruled route map, data-only | [`tools/balance/faction_routes.py`](../../tools/balance/faction_routes.py) |
| routing inside the assignment (clause 11) | `tools/balance/assign_references.py` |
| the layer for units with no counterpart | [`tools/balance/faction_extrapolate.py`](../../tools/balance/faction_extrapolate.py) |
| tests | `tools/tests/test_faction_routes.py` (19) · `test_faction_extrapolate.py` (20) |

```sh
python tools/balance/faction_routes.py            # the matrix with measured row counts
python tools/balance/faction_routes.py --check    # every ruled route resolves, or exit 1
python tools/balance/assign_references.py         # routed by default; --no-routing to compare
python tools/balance/faction_extrapolate.py --report
```

## §12 — ⛔ THE FACTION IDS IN PARTS I–III ARE NOT THE TREE'S

This document was written with `redalert2mod_asianalliance`, `tiberiandawn_gdi`,
`tiberiansun_forgotten`. The mod's own `InternalName`s — and every ACTOR PREFIX in every ledger —
are **`asianalliance`, `td_gdi`, `forgotten`**.

⚠ **Precisely, because the long names are not fiction:** `redalert2mod_asianalliance` is a real
name in this repo — it is the **ledger file** `docs/balance/redalert2mod_asianalliance.json` and
the ContentPack it came from. What it is NOT is the faction id, and routing has to key on the
faction id, because that is what an actor id carries.

⚠ **Get it wrong and it is the `RA2/YR` failure again, one layer up.** A ruling keyed on a name
that does not appear in an actor id routes nothing, silently, and looks complete while doing so.
`faction_routes.py` uses the tree's faction ids and `validate()` fails on any that are not
declared; `--check` is green.

## §13 — ⭐ THE MEASUREMENT THAT JUSTIFIES THE RULING

Of the **1,852** proposals the old matcher produced across the roster:

| | |
|---|--:|
| route-LEGAL (the reference is in a faction this Cameo faction is mapped to) | **144 — 7.8%** |
| route-ILLEGAL | **1,708 — 92.2%** |
| …of those, previously labelled **STRONG** on a name match | **599** |

⛔ **That is the "bullshit" rate, measured — and 599 of them carried the top confidence label.**
The name score was doing exactly what it was built to do and was answering the wrong question.

## §14 — What routing costs, stated plainly

| | routed | unrouted (the rejected behaviour) |
|---|--:|--:|
| Cameo actors in scope | 447 | 693 |
| assigned ≥1 reference | 325 | 596 |
| reaching the ≥2 reference floor | 53 | 454 |
| STRONG proposals | 140 | 721 |

⚠ **Routing is much stricter and that is the point**, but two costs are real and must not be
smoothed over: 246 in-scope actors are formula-only because their faction has no route at all, and
of those that are routed, most now have exactly ONE reference rather than two. The ≥2 floor is not
reachable for most factions until Mental Omega, CnC Reloaded and DTA land.

## §15 — ⭐ THE ROSTERS DO NOT LINE UP, AND THAT IS WORKABLE

**Maintainer, 2026-09-04:** *"not all reference factions have all the units from our factions or
they have additional units we don't have. It might even be that only a small portion of the units
could be mapped but that's still okay because we can use reasoning and our existing stats and the
unused extra reference units from their factions to somehow extrapolate something that roughly
makes sense."*

Measured, the mismatch runs in **both** directions: **557 reference rows go unused**, while `ordos`
has 25 Cameo units against **7** routed reference rows and `yuri` 19 against 15.

**The method, three steps, each measured rather than assumed** (`faction_extrapolate.py`):

1. **The exchange rate.** The pairs that DID match give the scale between the two rosters:
   `k = geometric mean over pairs of (cameo_stat / reference_stat)`, per stat and per route.
   That is "use our existing stats", in one number. **104 rates** are measured today across 27
   (faction, source) routes, each reported with its pair count `n` and its `spread`.
2. **The whole reference roster becomes Cameo-scale data.** Every routed reference row × `k` is a
   data point about the SHAPE of the population — including the units the reference faction fields
   and Cameo does not.
3. **A unit with no counterpart is placed by rank.** Its percentile inside its own (faction, type)
   Cameo population is read off the converted reference distribution. Cameo's roster decides the
   ORDER; the reference decides the SPREAD.

**Result: 361 of 447 routed Cameo units now have grounded placement** — 325 by a 1:1 pair, **36 by
rank placement**. The remaining 86 are in (faction, type) cells where the reference faction has
fewer than three usable rows — most of them navies that the reference factions simply do not field.

### ⛔ Four things this got wrong first, each now a guard and a test

1. **Pooling only the LEFTOVERS emptied the pool where it was needed most.** Infantry is where 1:1
   name matching succeeds, so almost no infantry row is left over — and infantry is 59 of the 122
   unpaired Cameo units. A distribution is made of all its members; a row does not leave it by
   having been matched. Fixed: the placement pools the **whole** routed roster.
2. **With no reference rows the placement is the IDENTITY and does not look like one.** Reading a
   unit's own percentile off its own roster returns its own value. `ordos` reported 20 such
   placements as coverage.
3. **Nearest-point placement collapses a small roster.** OpenE2140 `ed`'s four infantry rows put
   SIX Naxis infantry, spanning 20,000–96,000 HP, on one value. Fixed by interpolating between
   reference points in **log** space (the space every aggregate here already uses).
4. ⛔ **A reference faction can be uninformative for a whole type, and averaging hides it.**
   OpenE2140 `ed` fields Androids A01–A04 at HP 28/28/28/20 and speed 50/50/50/50. Placing Naxis's
   nine infantry against that would have **deleted a roster's variety while looking like
   evidence**. A reference population with fewer than three DISTINCT values now places nothing.

### ⚠ And one that is reported rather than fixed

`spread` is the geometric standard deviation of a rate's per-pair ratios. Where it is large, the
two rosters do not scale by one number at all — `ts_nod ← Crystallized Nexus` `w_dps` measures
**324×** on 3 pairs. That is a fact about the pairing, not a number to smooth away, so it is
printed next to every rate.

## §16 — ⏰ Sources the maintainer is supplying (ask 2026-09-05)

| source | needed for | status |
|---|---|---|
| **DTA** | all four TD/RA1 factions | promised 2026-09-05 |
| **Rise of the East** | Asian Alliance (China) · TKM (GLA) | promised |
| **Emperor: Battle for Dune** | ⭐ all Dune factions — **and it is the only source for `ixian` and `corrino`**, which were listed as permanently formula-only | ⭐ ruled 2026-09-04 |
| **Dune: Spice Wars** | the Dune tier's second modern voice | ⭐ ruled 2026-09-04 |
| **further Dune mods** | the Dune tier | maintainer has them locally |

⭐ **Emperor changes a "never" into a "pending".** `ixian` and `corrino` were both recorded as
having no counterpart in any source; Emperor fields House Ix and the Imperial/Sardaukar house. That
was a claim about the corpus, not about the world — the same shape as "not found is a claim about
your search".

⚠ **The Dune tier needs this most, and the numbers say so:** `ordos`'s entire exchange rate rests
on **4 pairs** against 7 reference rows.


---

> ⭐ **Picking this work up?** Read [`REFERENCE_PIPELINE_HANDOFF.md`](REFERENCE_PIPELINE_HANDOFF.md) first — it carries the
> design decisions, the sources still to ask the maintainer for, and every trap this build hit.

# PART V — THE PREREQUISITE HOP, AND WHERE THE ANCHORS CAN NOW BE FITTED (2026-09-05)

## §17 — ⛔ THE FACTION WAS ONE HOP AWAY, IN THE PREREQUISITE BUILDING

Found by asking why `heavy_sniper` — a **SIGNED** class — had both its members ground to nothing.
`ra1_soviets` routed to **zero** reference infantry, while OpenRA Red Alert plainly ships Soviet
infantry.

OpenRA gates most infantry on a BARRACKS, not on a faction:

```
E2 (Grenadier):  Prerequisites: ~barr, ~techlevel.infonly
BARR:            Prerequisites: anypower, ~structures.soviet, ~techlevel.infonly
```

The extractor read only the unit's own line, found no faction token, and returned nothing. It
already parsed `structures.soviet` → `soviet` correctly — it simply never followed the hop.

⭐ **`factions_of()` now resolves transitively through prerequisite ACTORS**, capped at
`PREREQ_DEPTH = 2`. The cap is deliberate: follow the chain further and it reaches infrastructure
both sides build (`anypower` → any power plant), and a faction attached through shared
infrastructure is worse than no faction at all. A direct gate still wins outright — an inherited
one is only consulted when the unit's own line says nothing.

| type | tagged before | tagged after |
|---|--:|--:|
| infantry | **25%** | **39%** |
| vehicle | 40% | **52%** |
| ship | 50% | **84%** |
| aircraft | 52% | **62%** |
| defense | 80% | 82% |
| building | 36% | 37% |

⚠ **Infantry was the worst-tagged type in the corpus** and it is the largest share of most
classes' populations — which is why the four infantry classes were all sitting at 61–67% grounded.

## §18 — Per-class grounding: `faction_extrapolate.py --by-class`

The report that says where an anchor can actually be fitted. **274 of 335** routed class members
are now grounded (246 by a 1:1 pair, 28 rank-placed), and the number that gates sign-off —
members carrying **≥2 references** — went **24 → 95** on the prerequisite hop alone.

⛔ **THREE ZEROES IN THAT TABLE ARE THE RULES WORKING, NOT HOLES.** Reading them as defects is the
trap the function documents against:

| class | members | why zero |
|---|--:|---|
| `support` | 105 | **all exempt** under matching-law clause 10 — MCV, engineer, harvester, transports, detectors never consume a reference |
| `commando` | 27 | **100% carry `build_limit`** |
| `epic_vehicle` | 24 | **100% carry `build_limit`** |

The population rule (maintainer, 2026-08-30) excludes one-offs from the corpus on BOTH sides:
*"Cameo's heroes and epic units must be excluded since they will be balanced separately."* So for
those two classes there is no peer row to match and no Cameo row to match it to. Zero is that
ruling executing.

⚠ **After this pass no class is left routed-but-ungrounded.** `heavy_sniper` was the last one and
it was the symptom that found the bug.

## §19 — ⛔ Mental Omega and CnC Reloaded: the faction data is NOT recoverable here

Checked directly rather than assumed, because it is the biggest blocker in this document:

* neither table has a faction column;
* neither is ORDERED by faction — rows are sorted by `kind`, then HP;
* there is **no raw MO or CnCR source anywhere in the tree** (`ORIGINAL_UNITS_RAW.md` is
  hand-typed; `synthesize_reference.py` reads it and does not generate it).

Deriving the factions from knowledge of the games would be exactly the *"inferred and invented data
that might be wrong"* the maintainer ruled against. **It is the same class as DTA: the maintainer
must supply the rules.** Until then MO and CnCR contribute unrouted rows, and the RA2 tier runs at
1/2 rather than the ruled 1/6.
