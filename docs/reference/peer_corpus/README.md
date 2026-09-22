# Selected structured peer evidence

The index explicitly replaces each selected source's legacy Doc5 slice. Combined Arms
and the four base OpenRA sources (TD, RA, TS, D2k) are enabled. Do not append selected
records to the corresponding old Markdown population. Other sources stay legacy.

The four base sources use clean OpenRA commit
`bbd36d9e6a2d7f0d3b24f102858af6dc8caf8a78`: 256 rows, including 122 armed rows
with incomplete evidence. Their retained HP/cost/speed/type values match the old
consumer exactly; ten old rows are removed by reviewed source/availability differences.
No new source population, certified factory/max state or applied stat target is added.
See [the source review](../../balance/review/BASE_OPENRA_STRUCTURED_EVIDENCE_20260910.md)
for the exact exclusions, source identity and consumer impact.

`base_rank_bbd36d9e.json` is a separate rank-axis projection, not an indexed input.
It records 80 evaluated base/max-rank pairs, 29 production-rank scenario holds
and 147 actors without a single rank track. Neither rank-only projections nor
empty rank inventories certify full factory/max-upgrade states or weapon DPS.
`base_scenarios_bbd36d9e.json` separately records 15 explicit prerequisite, terrain,
damage, deploy, tower, submergence and fresh-attack scenarios (315 input hashes). It is also
outside the consumer index. `tools/reference/peer_state_scenarios.py` accepts a
JSON array of named mod/actor scenarios; the reproducible inputs are in
`tools/tests/fixtures/base_peer_scenarios.json`. Omitted axes remain unknown.
These settled views neither establish purchase/reachability nor certify DPS.
Regenerate it externally with `tools/reference/extract_peer_rank_states.py
--source <clean-pinned-OpenRA-checkout> --output <external-new-file.json>`.

The CA payload was extracted read-only from clean commit
`ab9e477c3db818e91946d4cfdc86e71012966141`, with 48 unchanged source inputs. It contains
one schema-1 metadata record and 377 actor records, including all nested armament evidence.
Hashes identify the captured inputs and detect corruption; they do not establish source
authenticity, engine compatibility or gameplay correctness. All 288 armed rows still
carry incomplete evidence. Factory-ready and maximum-upgrade certification remain absent.

Selected production evidence now retains ordered raw Buildable, initial-level and experience
traits, recognized condition-grant declarations and queue/upgrade routes. 57 CA records declare
routes. HMMV records two routes to HMMV.TOW; that resolved variant cancels both.
Target existence does not prove activation or reachability. Routes must not be summed
as simultaneous actors or weapons. This is an input inventory, not an upgrade simulator.
Custom or differently named state providers require separate source-specific review.

The bounded initial-state review pilot covers exactly HARV, LST, HMMV and HMMV.TOW.
It additionally preserves top-level condition/prerequisite uses and authored
modifier-bearing traits. Modifier selection is heuristic, not complete provider
coverage. Counts are declaration occurrences, not unique conditions or proven
initial-state blockers. All expressions remain unevaluated; an empty collection
would not certify an unmodified state. Unknown/custom runtime providers, world and
player effects, delivery state and compatible upgrades still require review.
The required context includes owner/faction, prerequisites, purchased upgrades,
production level and the exact source-engine revision. The source's moving
`ca-engine/1.09` branch name is not proof of a particular historical binary.

HARV/LST have no direct weapon evidence but still carry conditional state; unarmed
does not imply factory-ready. The pilot leaves all377 prior record payloads
unchanged apart from its four added review inventories and exporter provenance.
No factory/max certification, new DPS, prices or applied game-stat targets result.

Regenerate with `tools/reference/extract_peer_units.py --mod ca --root <clean-checkout>
--json <new-output.jsonl> --expect-commit <full-commit>`, review the source/population and
evidence changes, then explicitly update the payload and index SHA-256 together. Do not
edit a generated payload manually. Git preserves its exact bytes. Invalid selected
evidence fails closed; deleting the index intentionally returns to legacy readers and
must therefore be reviewed as a semantic change, not a recovery workaround.
