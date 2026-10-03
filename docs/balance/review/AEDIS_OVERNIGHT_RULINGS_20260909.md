# Aedis reference-pilot rulings — 9 September 2026

Recorded by Codex / GPT-6 Astra for Blackrobe from AedisToru's DM replies.
Times are Asia/Jakarta. This records design direction, not completed implementation,
anchor approval, gameplay validation, or permission to merge.

## Reference placement and fitting

- **22:12:** prepare a first Japan pilot with reference-grounded TD GDI/Nod and
  RA1 Allies/Soviets as relative counterparts. The shared reference map includes
  future transport/bunker classes; pending membership must not be claimed as live.
- **22:33:** Japan should loosely draw on RA3 Empire of the Rising Sun and Japanese
  factions in RA2 mods. Role analogues are not direct original-game counterparts.
- **22:37, clarified 22:47–22:48:** classic original prices may change. First place
  stats **and price** from reference evidence within the class band, then fit using
  Cameo's formula. Small changes to stats, price, or both are allowed on the permitted
  increments to bring delta close to zero. This supersedes the old price freeze in
  `FORMULA_V2.md`, not the stat grids, class bands, or weapon-operation safeguards.
- HP in 1,000 steps was given as an example, not an explicit replacement of every
  class-specific HP policy in that DM. The existing **7 September ruling in
  `docs/DESIGN.md` already sets HP to 1,000 steps for every type**; use that rule,
  not older class tables or the stale infantry-only wording in `FORMULA_V2.md`.
  The latter is corrected in this batch. Regeneration conversion is separate.

The initial projection, the rounded candidate, the fitted candidate, and runtime
validation are separate evidence stages. A low formula delta alone does not prove
counterplay, timing, faction identity, or matchup balance. The read-only Japan class
ratio experiment is only a sensitivity diagnostic, not this completed pilot.

## Protected economic units

**22:33:** collect reference data for MCVs and harvesters, but do not change them
automatically. MCV HP/speed should be broadly comparable with modest faction variation;
all changes need manual review. Harvesters need their separate balance formula and
manual review. Combat-unit fitting must not silently include either group.

## Concrete follow-up requests

- **22:33:** map the Soviet V1 Rocket Truck to Combined Arms Katyusha and rename its
  player-facing identity to Katyusha. Preserve compatibility when deciding whether
  the internal actor ID also needs migration.
- **22:34:** extract original/reference unit evidence for Emperor: Battle for Dune,
  Dune II, and Dune: Spice Wars. Do not duplicate the existing OpenRA Dune 2000 source.
- **22:43:** investigate DTA X-O Power Suit railgun and chaingun extraction, show the
  actual arithmetic and CA contribution. Do not assume two weapon definitions fire
  together, or that missing direct Damage proves a harmless dummy weapon.
- **22:44:** incorporate the repository's RTS design/balance research in pipeline
  decisions. Research is contextual evidence; the owning design rulings still win.
- **22:50:** suggest ways to make the pipeline coherent. Astra recommended explicit
  stage boundaries, central stat-grid policy, per-actor source/weapon provenance,
  visible missing evidence, and a separate gameplay-validation stage.
- **22:53, accepted 23:07–23:08:** implement the proposed safeguards one by one:
  separate source-relative targets from fitted proposals; preserve counter/tier and
  representative time-to-kill relationships; freeze a pilot's baseline; distinguish
  direct counterparts, role analogues, extrapolation and source disagreement; then
  validate withheld references and a small set of runtime matchups. Acceptance of
  these checks is not approval of any particular resulting unit-stat change.
- **22:57–22:58:** research DTA actor extraction and harden the shared classic C&C/RA2
  INI extractor. Unsupported mechanics must be visible, not silently reduced to a
  seemingly complete number. A universal correctness claim is not achievable without
  matching the source version and engine extensions.
- **23:02:** exact DTA INI files will be provided later. Continue other work; retain
  exact DTA re-extraction as pending rather than substituting an unrelated release.
- **23:29:** review counterpart coverage and faction identity, starting with Nod
  Buggy Mk II versus GDI Humvee Mk II. Check alleged missing DTA/CA equivalents;
  do not assume a single-source projection preserves GDI-heavier/Nod-faster identity.
  Findings are in [the focused comparison](BUGGY_HUMVEE_REFERENCE_REVIEW_20260909.md).
- **23:33:** prioritize W24 remaining structure blockers before applying damage.
  Preserve projectile operation and effects; use appropriate delivery/element blends
  rather than mechanically collapsing unlike profiles. Propose missing families only
  when existing ones cannot represent the intended role sufficiently closely.

## Sequencing and completion criteria

### 10 September follow-up

- **00:08:** extend the weapon-evidence review to OpenRA-based reference mods.
  Reference comparisons must use factory-ready units without purchased upgrades or
  elite rank. Separately describe maximum achievable upgrade power and its change
  from base; mutually exclusive modes must not be summed as simultaneous weapons.
  This is a requested capability, not a claim that every source's activation rules
  or complete upgrade ceiling have been verified. Astra acknowledged at 00:09.
- **00:14:** review continuous heaviness before further W24 migration: one base
  family, increasing percentage magnitude and splash, and a heavyward armor shift.
  Existing Light/Medium/Heavy definitions are eventual migration targets, not to be
  deleted before their consumers and runtime/tool parity are verified.
- **00:40:** implement the identified fixes and work toward activation. Astra's
  00:49 acknowledgement states the working pricing interpretation: no extra
  heaviness surcharge, but actual damage and splash effects enter normal pricing.
- **00:46:** received `DTA_INI.zip`; exact-source inspection is no longer blocked
  on file delivery. Runtime version and selected mode still require provenance.
- **00:51:** continuous interpolation confirmed ("a combination of all the above
  but definitely interpolated"). At 00:59 Astra stated existing percentage endpoints
  would be provisional compatibility anchors, not newly approved numeric targets.
  Runtime/tool parity and a scoped pilot precede wider activation.
- **01:19:** pricing interpretation explicitly confirmed: percentage damage and
  splash enter the normal formula, and preserving the unweighted Versus total
  does not preserve roster-weighted effectiveness or price. No separate heaviness
  surcharge is required; the actual transformed profile must be priced.
- **01:22:** Astra asked whether Shield uniqueness should apply between new family
  bases while old level definitions remain visible compatibility duplicates, using
  the existing Medium Shield value for the first pilot. This is an unanswered
  migration question at that time.
- **02:10:** Aedis approved that Shield proposal and requested expedited migration
  alongside W24. New bases must be unique; old compatibility duplicates remain
  visible. Astra acknowledged at 02:14 and started the scoped CannonAP activation
  on the separate heaviness branch.

At 23:20 Astra acknowledged the five safeguards and described a reviewed first batch
within the remaining overnight window, not completion of the entire cross-game
validation programme. Finish parser safety and the bounded Katyusha correction;
then produce a source/target-separated, input-frozen Japan proposal workflow with
explicit confidence and withheld-reference checks. Representative matchup evaluation
follows only where complete weapon/armor/activation evidence exists. Missing source
files or unsupported mechanics remain named holds in the handoff.

## Execution boundaries from Blackrobe

New Cameo work and new PRs are authorized during the overnight response window ending
10 September 2026 at 06:00 Asia/Jakarta. Existing Blackrobe-authored PRs, especially
Scrin, must not be modified. No merges or direct master publication. Skirmish AI stays
parked. Source acquisition does not authorize execution of downloaded game code.
