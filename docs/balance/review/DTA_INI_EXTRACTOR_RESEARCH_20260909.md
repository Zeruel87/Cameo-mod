# DTA and classic C&C reference extraction reliability

## Executive assessment

The current committed DTA corpus does not establish complete unit damage. Its extractor
can replace a zero-direct-damage primary weapon with the secondary, discarding evidence
needed to understand railguns and other effect-driven weapons. The X-O Power Suit is a
reproduced example, not a theoretical risk. Its reference report has a second, independent
problem: the explicitly assigned DTA hero row does not enter the ordinary report's peer
pool, so that report uses Combined Arms alone.

This is evidence of extraction and report limitations, not proof that Cameo's entire
balance formula is invalid. It does mean that weapon targets derived from incomplete
records must not be applied as if they were source-faithful. Preserving a numeric column
is less important than preserving whether the number represents direct damage, an entire
firing cycle, or merely one of several conditional channels.

**Status:** investigation in progress, refreshed against Cameo base
`50b7d001be845e0ac5a0812d2591e154148c94dc`. The original reproduction used
`86b41c007c980ce3d231cffc05f437d659a9e8ca`; local extractor fixes now retain unsupported
primary weapons rather than automatically substituting their secondary. The two DTA corpus
sections have now been refreshed with source hashes and unverified runtime semantics; all
other source lines remain byte-identical. Aedis supplied `DTA_INI.zip` at 00:46 Asia/Jakarta on 10 September;
exact-file inspection is underway. Selected game mode and executable/extension version
remain unverified. No claim here certifies all DTA actors against the game.

### Received source confirmation

The archive SHA-256 is
`17e6e5876da196f8fa7344ae2e8977de1c08363381f5b3a2aff1f4c7f277bed3`.
Its generated `INI/Rules.ini` hash is
`6329487eecaa12fb314c31eef3f21b17812ef15b1baa39f223c8205e2d4745d9`;
generated `INI/Enhance.ini` hash is
`40a8a48a14239d43cf8f87e96ec9540960c44cfc5a4285f5ae986f1361256cef`.
Do not merge generated files with their Base copies or blindly apply the old root
GlobalCode.ini. Those are distinct inputs, not evidence of one selected runtime ruleset.

`XORail` declares Damage=0, AmbientDamage=150, ROF=60 and IsRailgun=true.
`XOMachineGun` declares Damage=15 and ROF=5. Their raw channel rates are respectively
2.5 and 3 per native time unit before armor, **not a justified combined 5.5 DPS**.
The actor description assigns the gun to infantry and the rail to vehicles/buildings;
the rail can pierce the firing line. RailShot's medium modifier is 1500%, while GC's
is 450%. Elite XORailE is a separate upgraded state, excluded from factory-ready
comparison. These fields confirm the omitted rail channel but do not by themselves
establish real-time sustained damage.^9

## 1. Reproduced X-O calculation

The committed `docs/reference/ini_corpus.json` contains this DTA Enhanced `XO` evidence:

| field | stored value |
|---|---|
| build limit | 1 |
| direct primary identity | `XORail`, retained only as `w_dummy_primary` |
| selected exported weapon | `XOMachineGun` |
| exported direct damage | 15 |
| exported ROF | 5 |
| exported `w_dps` | 3.0 |
| secondary substituted | `w_from_secondary: true` |

The arithmetic is **15 / 5 = 3**. This is damage per native ROF unit, not a verified
real-time DPS or combined-weapon rate. The original railgun's direct/ambient/effect
fields are absent from this row. Its contribution cannot be reconstructed from the
remaining number. Nor can primary and secondary be assumed to fire simultaneously.

The current `reference_targets.py` report starts from `reference_distribution.peer_rows()`.
That ordinary pool excludes the DTA record because `build_limit` is present. Although
the assignment names both DTA Enhanced `XO` and Combined Arms `XO`, only CA survives
this report's join. The reproduced calculation is:

1. Current Cameo `td_gdi_exosuit` nominal input: **525**.
2. CA `XO` stored nominal input: **66**, projected through CA and Cameo population
   coordinates to **334.25682611676007**. This is not a direct unit conversion or a
   raw average of 66 and 525.
3. With one surviving reference voice and one Cameo voice:
   `sqrt(334.25682611676007 * 525) = 418.90909958044494`.

Thus the displayed **525 → 419** is a CA-only result with Cameo's equal vote. DTA does
not lower that target: DTA is absent. A hero's assigned comparison can be preserved
without inserting that hero into the ordinary population used to calculate percentiles.
Those are different operations and need separate tests.

## 2. Corpus-wide inventory, not a source-validation claim

The committed INI corpus has **11,870 rows** across nine source labels. DTA Classic and
DTA Enhanced contain **863 rows each**, or **1,726 source/actor records**. The same actor
in two modes is two records; neither this total nor the following counts is a count of
unique player-buildable combat units.

| check | Classic | Enhanced | interpretation |
|---|---:|---:|---|
| secondary replaced primary | 10 | 10 | original primary evidence was lost |
| exported primary burst greater than one | 88 | 86 | the stored rate still uses Damage/ROF |
| retained second-weapon identity | 80 | 82 | existence does not prove simultaneous firing |
| costed rows marked buildable | 215 | 252 | static extractor classification, not runtime reachability |

The fallback also occurs outside DTA: Rise of the East 19, RA2 0XX 2, Mental Omega 14,
CnC Reloaded 4, Red Resurrection 21, RA2 Reborn 1, and Twisted Insurrection 3. Along with
the 20 DTA records, that is **84 affected source/actor records**. These are audit candidates,
not 84 proven harmful weapons: some may genuinely be placeholders. Their names alone
cannot settle that distinction.

All DTA records with nonzero exported direct damage and ROF reproduce Damage/ROF. That
consistency proves what the script calculated, not that it calculated the correct engine
cycle. The original definitions must establish burst gaps, effect lifetimes, selected
slot, target eligibility, veterancy and any engine-extension rules.

## 3. What the engine evidence establishes

### Direct damage is not the whole shot

OpenTS is an independent reconstruction targeting Tiberian Sun 2.03, not an official EA
release and not the exact DTA executable. Its implementation is useful corroborating
evidence, but cannot certify a DTA-specific extension without version matching.[^1]

At OpenTS revision `0281b88e7e140436ff953be143d504e37d354e74`, `TechnoClass` uses
`AmbientDamage` when applying a railgun beam to gathered targets. The direct projectile
damage is a separate path. A zero direct `Damage` therefore cannot prove that a railgun
is non-damaging. The declared beam radius, warhead and target geometry also matter.[^2]

The documented firing sequence distinguishes projectile damage, railgun damage, fire
particles and sonic effects. Some effects can hold the weapon unavailable while alive,
including interactions with the other slot. A list of two weapons consequently does not
justify adding two independent full-time rates.[^3]

### ROF is not universally the complete cycle

The same reconstruction's `Rearm_Delay` distinguishes intermediate burst gaps from the
final reload and applies different branches to effect-driven weapons. Ordinary final
reloads can include house/veterancy effects and random padding. Even multiplying damage
by Burst and dividing by ROF is not generally a complete sustained-rate calculation.[^2]

A safe extractor should preserve the native timing fields and engine profile, then
calculate only the cycle whose assumptions it can establish. Where behavior remains
conditional, publish the alternatives or an explicit unavailable result, not one
unqualified DPS number.

### DTA and RA2 extensions need explicit profiles

DTA's own release history documents its adoption of Vinifera. Vinifera adds mechanics
including custom armor and warhead modifiers, so treating a contemporary DTA ruleset
as unmodified vanilla TS is insufficient.[^4][^5] Likewise, an RA2/Ares/Phobos source
must be matched to its own extension version before extension-specific tags are
interpreted. Similar INI syntax is not proof of identical runtime semantics.

For example, Phobos documents per-shot burst delays and extra warhead detonations
with independent damage overrides and probabilities. Those features cannot be
represented by one unqualified Damage/ROF column. This identifies cases a parser
must recognize or withhold; it does not establish that any particular archived mod
version uses them.[^6]

OpenTS also distinguishes damaging fire/gas particles from visual railgun particles:
the beam's damage is applied by the firing code, not inferred from a particle's
appearance. Particle lifetimes can affect weapon availability. A particle reference
therefore requires following its behavior and owner, not assuming that every particle
adds damage or that every visual effect is harmless.[^7]

### Case and duplicate handling are engine-dependent

The inspected OpenTS `INIClass` documents case-sensitive raw-byte lookup. A generic
claim that every Westwood-family INI is case-insensitive is unsupported. Preserve exact
spellings and report near-match ambiguities; apply folding only when the actual engine
profile establishes it. Likewise, source duplicates, overlays and repeated contextual
keys must remain distinguishable rather than disappearing into an unexplained dictionary
overwrite.[^8]

## 4. Recommended extraction contract

The extractor should retain three distinct layers:

1. **Raw evidence:** file hash, version, section/key, overlay order, explicit value,
   absence, and every referenced weapon/projectile/warhead/effect identity.
2. **Resolved native model:** engine-profile-specific defaults and inheritance,
   selected/elite/deployed modes, native units and unresolved dependencies.
3. **Derived metric:** calculation, assumptions, domain, supported features and
   completeness. Only eligible, complete metrics may enter numerical synthesis.

Do not overload `None` or zero. Zero is an explicit source value; absent is unknown;
unsupported is known to need an unimplemented mechanic; not applicable is a different
state again. Retain valid chassis fields even when damage is withheld.

Compatibility columns may remain for consumers, but they must identify their basis.
A legacy nominal single-weapon estimate is not a complete unit DPS. A new evidence
schema alone is insufficient if downstream consumers ignore its incompleteness flags;
the consumer gate and its regressions are part of the repair.

## 5. Actor-by-actor review procedure

For each Classic/Enhanced actor, enumerate its declared type, source section, production
requirements, mode, build limit and exclusion reason. Then follow every weapon slot,
projectile, warhead and effect dependency. Include non-buildable and special rows in
the audit inventory, but not automatically in combat distributions.

For each stat, compare the old exported value with the new source-backed value or
explicit hold. Every changed result needs a reason: overlay correction, missing slot,
effect channel, burst cycle, armor notation, variant classification, or parser failure.
The total reviewed, unchanged, corrected, excluded and unresolved counts must reconcile
with the entire source roster. No unresolved actor disappears from the denominator.

Select representative regression cases from distinct mechanics: direct single-shot,
burst, railgun, flame/particle, sonic, target-selected secondary, elite replacement,
deployed state, support/healing, aircraft ammunition and build-limited hero. Synthetic
fixtures test parser behavior; exact source hashes and actor comparisons test the real
data. Neither substitutes for the other.

## 6. Implementation and publication gates

### Exact-file actor comparison, 10 September

The bounded comparison resolves generated Rules alone and generated Rules with the
Enhance overlay separately. These names describe the inputs, not verified launch modes.
Both contain 863 actor records and exactly the same actor IDs as their corresponding
committed corpus rows. HP, cost, speed, secondary identity and the extractor's buildability
flag match for every actor. This supports preserving chassis values; it does not certify
weapon damage or actual scenario availability.^9

| measure | Rules only | Rules + Enhance |
|---|--:|--:|
| actor rows | 863 | 863 |
| ID additions / removals | 0 / 0 | 0 / 0 |
| chassis/secondary/buildability mismatches | 0 | 0 |
| primary identity corrections | 10 | 10 |
| extractor-buildable rows | 361 | 395 |
| armed rows | 294 | 294 |
| primary nominal-direct usable rows | 125 | 124 |
| previously positive summaries now withheld | 127 | 127 |
| armed/buildable rows with primary withheld | 74 / 148 | 92 / 170 |

The export-verified 127 replaces the preliminary audit's 132: it counts old positive
`w_dps` rows whose new primary evidence is `incomplete`. Raw diagnostic numbers may
remain present; the consumer gate, not deletion of those numbers, withholds their votes.
The last row means withheld count / armed-and-buildable population, not two separate
flags. Buildability is the extractor's limited predicate, and AI variants remain counted.
The overlay changes 40 buildability flags (37 enabled, 3 disabled), agreeing with the
stored mode rows; XO changes TechLevel -1 to 7.

The ten substitutions are MTNK/AIMTNK (90mmDummy replaced by 90mm), XO/AIXO (XORail
replaced by XOMachineGun), SCRINTNK/AISCRINTNK (PlasmaDummy replaced by ScrinPlasma),
BRIG (BRig5Inch replaced by BRig16Inch), EKRACARR (EkranoplanDroneLauncher replaced
by EkranoplanSCUD), SP941 (P941NukeDummy replaced by P941Nuke), and MWAVEMSAM
(Tri227mmMsl replaced by RedEYE2). A dummy-looking name is still not proof of inertness;
raw slots are retained pending an exact mechanism-specific treatment.

Mechanics counts overlap and are actor slots, not unique weapons: both variants have
10 rail-marked primaries and 2 secondaries; particle references occur in 57/59 primaries
and 2 secondaries; Burst > 1 occurs in 88/86 primaries and 41 secondaries. A withheld
numeric summary means unsupported modeling, **not zero damage**. The immediate repair
is source-identified evidence export plus consumer withholding, not invented damage or
chassis rebalance.

- Preserve both X-O weapon identities; stop calling a zero-damage primary a confirmed
  dummy without supporting mechanics evidence.
- Add bounded source/actor quality diagnostics before widening numeric extraction.
- Obtain the exact DTA base, Enhanced overlays, injected map/global rules, relevant art
  timing/particle definitions and engine-extension version.
- Re-extract with explicit precedence and compare all actors; never regenerate the
  committed corpus from guessed or different-version source files.
- Run extractor and consumer regressions, the full existing suite against the same
  baseline, ledger/structure checks where affected, and independent review.
- Publish code fixes separately from unverified rebalance conclusions. A later Japan
  pilot may use the corrected evidence only where its source and metric gates pass.

MCVs and harvesters remain reference-collection/manual-review only. No existing
Blackrobe-authored PR is modified by this investigation. Skirmish AI remains parked.

## Sources

[^1]: OpenTS Developers, [OpenTS project description](https://github.com/OpenTS-Developers/OpenTS), inspected 9 September 2026; reconstruction scope and limitations.
[^2]: OpenTS Developers, [`code/techno.cpp` at revision 0281b88e7e140436ff953be143d504e37d354e74](https://github.com/OpenTS-Developers/OpenTS/blob/0281b88e7e140436ff953be143d504e37d354e74/code/techno.cpp), `Rearm_Delay` and railgun target-damage code; read-only source inspection.
[^3]: OpenTS Developers, [Firing geometry and beam weapons](https://opents-developers.github.io/OpenTS/systems/firing-geometry/), source revision 0281b88e7e14; firing slots, effect holds and timing.
[^4]: Rampastring / DTA, [Dawn of the Tiberium Age version 9.5.0](https://www.moddb.com/news/dawn-of-the-tiberium-age-version-950), 14 May 2022; Vinifera adoption, not proof of the current corpus version.
[^5]: Vinifera Developers, [New Features and Enhancements](https://github.com/Vinifera-Developers/Vinifera/blob/develop/docs/New-Features-and-Enhancements.md), inspected 9 September 2026; extension-specific armor and damage modifiers.
[^6]: Phobos Developers, [New / Enhanced Logics](https://phobos.readthedocs.io/en/latest/New-or-Enhanced-Logics.html), sections “Burst delay customizations” and extra warheads, inspected 9 September 2026. Current documentation is not a version match for the archived reference corpus.
[^7]: OpenTS Developers, [Particle systems](https://opents-developers.github.io/OpenTS/systems/particle-systems/), behavior-specific fields and effect holds, inspected 9 September 2026.
[^8]: OpenTS Developers, [`code/ini.h` at revision 0281b88e7e140436ff953be143d504e37d354e74](https://github.com/OpenTS-Developers/OpenTS/blob/0281b88e7e140436ff953be143d504e37d354e74/code/ini.h), `INIClass` lookup contract. Reconstruction evidence, not universal proof about other engines.
[^9]: Aedis-supplied private `DTA_INI.zip`, received 10 September 2026 at 00:46 Asia/Jakarta; generated `INI/Rules.ini` sections XO, XORail, XORailE, XOMachineGun, RailShot, GC and SmallRailgunSys; `INI/Enhance.ini` section XO. Hashes above identify the inspected files, not a verified game release.

Local reproducibility sources: Cameo `tools/reference/extract_ini_units.py`,
`tools/balance/reference_distribution.py`, `tools/balance/reference_targets.py`,
`docs/reference/ini_corpus.json`, and `docs/balance/derived/reference_assignment.json`
at the base commit stated above. These are repository evidence, not independent game
measurements. The corpus does not currently provide the complete source needed for a
verified railgun DPS calculation.
