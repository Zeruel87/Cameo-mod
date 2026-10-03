# Sixteen Tiberian Dawn owner-prefixed weapon identities

Baseline:8968ea789502f638c492f92c3ad15ae51243490c. Sixteen weapon headers and
23 Armament Weapon values migrate across eight canonical owners: Humvee, Heavy
Sniper, Officer, Havoc, Apache, Laser Turret, Venom and Recon Bike.
There are no weapon-body, inheritance, projectile, effect, class or numerical
changes. Havoc's unusual Armament@ra1_allies_alliedsniper key is unchanged.

Preflight found exactly23 raw active references, all accounted for. Destination
names are free; no weapon descendants or incoming trigger/fragment references
were found. Bundled archives and loose YAML/Lua contain no old-name references.
The fixture records all16 ordered raw/resolved payloads, eight complete actors,
exact slots, class contracts and two historical comparison-file hashes.

Three current converter selectors follow the new identities. Historical
comparison memberships use explicit current-to-old mappings; their JSON and
hashes are unchanged. BikeRockets in aggregate_archetype.py is an EXTERNAL source
selector and is intentionally unchanged, with a regression assertion. The old
GDISniperRifle historical untouched-set is not a live lookup and is also retained.
Mixed profiles and pre-existing role holds are not redesigned or marked resolved.

All2,910 source weapon payloads compare exactly after16 identity reversals.
All fields in the four changed GDI/Nod primary/derived ledgers are identical
after only weapon-name normalization. Five new regressions pass.61 focused tests
retain4 failures,2 errors and11 skips; all six failure/error identities are
already present in the prior combined baseline. Independent actual-diff review
found no blocker. Canonical source audits completed with the same8 gated
failure categories:inherits,basebuilder_crates,buildable_order,packs,
split_definitions,release_drift,doc_claims,doc_health. C1 remains20 and no
threshold changed. All33 ledgers have zero drift; no empty final audit reports.
All2,911 combined weapon payloads compare exactly after the16 identities.
Final isolated combined R18 completed1,962 tests:12 failures,8 errors,64 skips;
peak total system RAM66.90%, no95% guard stop. The full suite is not green.
Independent accounting verifies all1,965 discovered test identities, including
three methods under the pre-existing optional-DTA class skip; none missing/extra.
All20 failure/error identities match R17. Independent final review found no
remaining publication blocker for this frozen batch, not the whole roster.

The frozen combined configuration passed90 seconds of menu observation starting
2026-09-10 12:07:22 Jakarta: fresh menu-load proof, no new exception logs,
peak total system RAM66.85%, process closed. No rebuild or matchup test.

## Release continuity: existing differences are not repaired by renaming

The shipped flat-damage comparison uses playtest-20260709 and the existing
release audit metric. Both OfficerMachineGun and OfficerMachineGunAP remain
16,000 versus4,000 in the release (4x). Those old differences move into unmatched
names, not into a repaired balance state. The other12 available release values
are unchanged: Humvee pair6000, Heavy Sniper32000, Havoc sniper/rocket/grenade40000
and rifle8000, Apache gun4000/missile2000, Laser Turret12000, Venom8000, Bike16000.
The two Burning variants have no old release entry and are not zero-filled.
Raw D1=115,D2=59,D3=17,D4=406/335,D5=34. D1/D3 each fall by one and D5 by one
because old Officer names become unmatched. Historical accepted status is not
transferred to a new name. No raw audit count or threshold is relaxed.

This is not full-roster ownership completion or a balance approval. The draft
remains unmerged; external maps/replays using old identities need migration.
