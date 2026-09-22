# TD naval reference eligibility and ownership review

Status: reviewed candidate inventory, **not approved assignments or stat targets**.
Uses reference evidence from PR339 and canonical actor IDs from PR340. Actual
`faction_routes.allows()` calls were checked after source-ID registration; current
assignment ownership was checked in `derived/reference_assignment.json`.

| Cameo actor | Source candidate | Eligible faction | Current owner | Evidence limit |
|---|---|---|---|---|
| td_gdi_supercarrier | DTA CARRIER | GDI | unused | Nominal launcher channel, not fleet DPS |
| td_gdi_supercarrier | CA CV | GDI | unused | Legacy-unassessed; carrier state unresolved |
| td_gdi_missileboat | DTA MCRUISE | GDI | unused | Weapon evidence withheld: burst_unfolded |
| td_gdi_missileboat | CA PT2 | GDI | unused | Legacy-unassessed; role review needed |
| td_gdi_landingcraft | DTA GLST | GDI | unused | Unarmed transport; chassis comparison only |
| td_gdi_railgunbattleship | CA CA | GDI or Nod | ra1_allies_cruiser | Already used; not a railgun equivalent |
| td_nod_attacksubmarine | CA SS2 | Nod | unused | Stronger identity candidate; legacy-unassessed |
| td_nod_attacksubmarine | DTA TORPBOAT | Nod | unused | Surface boat mismatch; burst_unfolded |
| td_nod_ballisticmissilesubmarine | CA ISUB | Nod | unused | Named role candidate; legacy-unassessed |
| td_nod_lasercorvette | DTA LASCOR | Nod | unused | Nominal-direct, not complete DPS certification |
| td_nod_transportsubmarine | DTA NLST | Nod | unused | Surface hovercraft mismatch; chassis only |

Unused means absent from the current stored assignment, not guaranteed available
under a future whole-roster rematch. CA's untagged LST is refused by routing.
DTA MSUB is Soviet-tagged and refused for TD Nod. OpenRA Tiberian Dawn's current
normalized corpus has no ship rows; this alone does not identify an extractor bug.

## Decisions not to guess

- Do not steal CA CA from the existing RA1 Allied Cruiser assignment. No close
  railgun-battleship counterpart has been established in the available candidates.
- A surface torpedo boat is not an exact attack submarine; a hovercraft is not
  an exact transport submarine. Preserve those mismatches for maintainer review.
- A carrier's launcher damage is not the damage output of its aircraft. Do not
  sum auxiliary, upgraded or mutually exclusive weapon slots to fill missing DPS.
- Multiple source names are not proof of independent balance lineages. Continue
  the existing lineage rules rather than counting every eligible row as a vote.

## Updated integration snapshot (06:56 Jakarta)

After structured CA input and naming integration, the normal assignment generator
produces these diagnostic proposals (not manual selections or live YAML changes):

| Cameo actor | Automatically proposed references |
|---|---|
| td_gdi_supercarrier | CA CV; DTA Enhanced CARRIER |
| td_gdi_missileboat | CA MSUB |
| td_nod_attacksubmarine | CA SS2 |
| td_nod_ballisticmissilesubmarine | CA MSUB |
| td_nod_lasercorvette | DTA Enhanced LASCOR |

The other three naval actors have no assignments. CA CA remains assigned to
`ra1_allies_cruiser`. Therefore the earlier table's unused-owner column describes
the initial snapshot, not this regenerated output. All five reviewed CA candidates
(CA/CV/PT2/SS2/ISUB) now explicitly report `incomplete`, replacing legacy-unassessed
metadata through the structured reader. No weapon DPS has become certified.

In particular, CA MSUB proposed for the surface missile boat is an unresolved role
mismatch. An automatic name/shape score is not sufficient approval of a reference.
Keep these proposals diagnostic and do not apply derived unit-stat targets.

## Required next step

Do not approve/apply the generated assignments until factory-state/weapon evidence
and unresolved role choices are reviewed. DTA uses `extract_ini_units.py`; CA uses
`extract_peer_units.py`. PR339's structured reader now replaces the selected CA
Doc5 slice while preserving incomplete statuses. Validate source states before exposing
new weapon-stat targets to consumers. Chassis-only proposals remain distinguishable
from full-unit balancing recommendations.

The initial OpenCode candidate draft was independently challenged and corrected:
its direct-equivalence, lineage and extraction-certification claims were too strong.
No game configuration or hand-picked reference assignment was changed by this review;
the integration generator's new diagnostic output is disclosed above.
