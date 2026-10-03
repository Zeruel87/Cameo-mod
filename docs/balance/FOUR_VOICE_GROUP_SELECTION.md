# Four-voice selection manifest

This is a review-only input contract for Aedis's equal-vote armor synthesis.
It does not join source records, normalize armor axes, calculate DPS, or write
YAML/Versus values. The caller must select every source record explicitly.

## Required group contract

Each group supplies:

```json
{
  "comparison_id": "ra1/medium-tank/base",
  "scenario": "vehicle",
  "state_key": "base",
  "voices": [
    {"voice": "Current Cameo", "dataset": "cameo", "record_index": 123},
    {"voice": "Combined Arms", "dataset": "ca", "record_index": 45},
    {"voice": "DTA Enhanced", "dataset": "dta", "record_index": 7,
     "status_alias": "DTA_BASE_CHANNELS_RESOLVED"},
    {"voice": "OpenRA Red Alert", "dataset": "ora", "record_index": 19}
  ]
}
```

The four rows must contain one `Current Cameo` voice and exactly three distinct
reference voices chosen from `Combined Arms`, `DTA Enhanced`, `OpenRA Red
Alert` and `OpenRA Tiberian Dawn`. Each selected dataset and zero-based
`record_index` is caller-owned. The rows are ordered deterministically as
Current Cameo followed by the selected reference names.

The group metadata is authoritative. If a raw record has `comparison_id`,
`scenario` or `state_key`, it must agree with the group. A caller may state an
explicit raw-label mapping with `record_comparison_id`, `record_scenario` or
`record_state_key` on that voice selection. Those fields document a reviewed
mapping; they do not infer one. A raw `source: Cameo` is accepted for the
`Current Cameo` voice. Other declared source/voice labels must match exactly.

Every selected record normally must have `status: RESOLVED` and a
mapping-valued `terms` field. The DTA adapter's explicit
`BASE_CHANNELS_RESOLVED` status may be admitted only when that DTA selection
also carries the whitelisted `status_alias: DTA_BASE_CHANNELS_RESOLVED`.
The projected row is marked `RESOLVED`, while its raw status and status basis
remain visible. This admits authored base-channel arithmetic without claiming
installed-client runtime applicability. Unresolved, missing, duplicate,
malformed or mismatched rows remain in the output as `UNRESOLVED` evidence.
Raw records, explicit identity fields and the original selection are retained
for review.

Do not create a cross-source group by matching actor names, weapon names,
reference IDs, slots, scenarios, states or list positions. Do not turn a
missing voice into a smaller-weight vote. Multiple channels must first be
reduced by an explicit caller selection within each source; the four-voice gate
then assigns 0.25 to each selected voice.

## Review flow

The implementation is `tools/balance/explicit_voice_group_assembler.py`.
Call `assemble_group` or `assemble_groups` with a dataset mapping whose values
are the already-loaded record lists. Pass each resolved group's `source_rows`
to `four_source_synthesis_gate.combine_group` with `voice_policy=True` and an
explicit `scenario_policy=True` when the Aedis armor ladder is intended.

The scenario policy is diagnostic only:

- infantry: None, Flak, Plate, with source Light mapped to Plate;
- vehicles and ships: Scout, Light, Medium, Heavy, Superheavy, with Light and
  Heavy direct, Medium interpolated, and one equal step extrapolated at each
  endpoint;
- aircraft: Fighter, Bomber, Helicopter, Spaceship, with Light and Heavy as
  direct endpoints and two equal intermediate steps.

## Reviewed manifests

**Current review:** the historical v6/v7/v8 successes establish channel arithmetic
only. `docs/audit/latest/astra_review_20260911/four_voice_comparison.json` retains
29 withheld votes because original per-armor self-vote reconstruction is not
verified. All 71 archived actor/derived-ledger inputs are recovered and match
the frozen snapshot; they do not contain the full original channel fields.
A separate reviewed `policy.current_cameo_channel_vote` reconstruction contract
may bind `baseline_sha256`, `dataset_sha256`, optional `dataset_schema` and a
`reconstruction_evidence` object of the form (the path is resolved under the
driver's explicit evidence root):

```json
{
  "path": "docs/reference/cameo_channel_reconstruction_20260911.json",
  "sha256": "<sha256 of that JSON file>"
}
```

The referenced portable JSON must have `schema: 1`, `review_status: "REVIEWED"`,
the exact baseline/dataset hashes (and dataset schema when supplied), nonempty
`scope`, `method` and `normalization` fields, a nonempty `source_hashes` mapping
whose values are SHA-256 digests, and a `source_state` object containing
`kind` (`clean_commit` or `dirty_worktree`), a 40-hex `commit`, a boolean `dirty`,
and `reconciled_to_snapshot: true`. When the immutable baseline supplies
`worktree_head`, the receipt's commit must also match that exact snapshot HEAD.
The driver resolves the path under its explicit evidence root, verifies the file
hash and identities, validates source-state fields and identity, and rejects
missing, malformed, stale, contradictory or path-escaping evidence. A
valid contract checks integrity and records independently supplied review
metadata; it does not rederive historical armor channels or certify their
substantive correctness. Never edit the frozen actor snapshot to add a new schema
field or substitute current channels for the original values.

The original vehicle pilot manifest is retained at
`docs/balance/four_voice_selection_pilot_20260911.json` and produces the
12-group receipt `docs/audit/latest/four_voice_pilot_v6_20260911.json`.

The extended manifest at
`docs/balance/four_voice_selection_pilot_infantry_20260911.json` adds nine
base infantry groups (RA Allies: rifle infantry and Ranger; RA Soviets: rifle
infantry, Grenadier and Shock Trooper; TD GDI: Minigunner and Grenadier; TD
Nod: Minigunner and Chemical Warrior). Together the manifests produce the
21-group receipt `docs/audit/latest/four_voice_pilot_v7_20260911.json`: all
21 groups are assembly-, channel-aggregation- and gate-resolved, with the
explicit infantry None/Flak/Plate policy recorded alongside the existing
vehicle ladder. Upgrade variants remain excluded by the hand-authored identity
guards.

The aircraft-target extension at
`docs/balance/four_voice_selection_pilot_aircraft_20260911.json` adds eight
base aircraft-target groups (three RA Allies, two RA Soviets, one TD GDI and
two TD Nod) and produces
`docs/audit/latest/four_voice_pilot_v8_20260911.json`. All 29 groups resolve
through assembly, channel aggregation and the gate; the eight aircraft groups
record the named Fighter/Bomber/Helicopter/Spaceship interpolation. Reference
rows retain their raw `small_aircraft` label through an explicit
`record_scenario` mapping, while DTA remains admitted only through its
base-channel alias.

The broad candidate matrix still contains 60 Current Cameo plus
three-reference candidates. It remains a source-coverage inventory rather than
a gate input because its rows do not carry the explicit group metadata and
reviewed affine terms required by this contract. That preparation limitation is
not evidence that the candidates are equivalent.
