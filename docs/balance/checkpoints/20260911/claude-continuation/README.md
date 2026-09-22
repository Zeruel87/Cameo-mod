# Portable continuation inputs

Read [project status](../../../PROJECT_STATUS_20260911.md) for ownership, current
results and Claude's CL-01 assignment. CL-01 can begin from committed YAML and
reports without extracting this packet. This archive supports the separate
GP-02 source comparison and preserves inputs previously available only on
Blackrobe's PC.

`inputs.zip` contains 75 JSON files: the four exact input datasets referenced by
the corrected `astra_review_20260911/four_voice_comparison.json`, and all 71
original ledger inputs named by the immutable Cameo baseline. The accompanying
`inputs.manifest.json` lists every original SHA-256 and the archive SHA-256.
The archive preserves the original bytes, including line endings. It contains
generated project data, not downloaded game assets or complete reference repos.

The frozen actor/hero snapshot hashes were captured from CRLF file bytes, while
their existing Git blobs are normalized LF. This checkpoint adds explicit CRLF
checkout attributes for those two files, making the required hashes stable on
other platforms without rewriting either immutable snapshot blob or its values.
Use a Git checkout for the commands below rather than copying raw snapshot text
from the GitHub page.

From the repository root, extract to a new sibling directory:

```powershell
python -m zipfile -e docs/balance/checkpoints/20260911/claude-continuation/inputs.zip ../cameo-handoff-inputs-20260911
```

Use a fresh destination if that directory already contains another task's work.
To reproduce the diagnostic on another PC, pass the extracted input paths
explicitly; the tool's older local defaults are not portable:

```powershell
python tools/balance/assemble_four_voice_pilot.py --manifest docs/balance/four_voice_selection_pilot_aircraft_20260911.json --cameo ../cameo-handoff-inputs-20260911/comparison/cameo.json --reference ../cameo-handoff-inputs-20260911/comparison/reference.json --dta ../cameo-handoff-inputs-20260911/comparison/dta.json --coverage-matrix ../cameo-handoff-inputs-20260911/comparison/coverage_matrix.json --frozen-input-root ../cameo-handoff-inputs-20260911/frozen-ledgers --out ../cameo-handoff-inputs-20260911/reproduced-comparison.json --markdown ../cameo-handoff-inputs-20260911/reproduced-comparison.md
```

Expected result: all 71 archived inputs match, the candidate inventory has 163
actors, and the 29 selected groups remain withheld with
`original_channel_reconstruction_not_verified`. Successful execution is not a
passed balance gate. These archived scalar ledgers do not capture every original
per-armor target mask or Versus value. Do not edit the permanent baseline or
declare the later Cameo dataset to be its frozen channel vote.

Historical receipts retain their generation paths and captured-byte hashes.
Use the commit SHA for the shared code version and this manifest for portable
input identity; a different local checkout path is expected. The corrected
receipts under `astra_review_20260911` supersede earlier report iterations,
which remain in the checkpoint for provenance.

## Frozen-source reconstruction candidate

The packet also carries a separate **candidate** generated after inspecting the
recorded source commit `9471672b2e908661334804dbfe022ccc267d3192`:

- `frozen-source-matrix-v2.json.gz` contains the 163-actor roster with armament
  and warhead metadata rebuilt from that clean commit. Four Mortar Soldier
  slot/weapon mismatches are retained as explicit unresolved selections.
- `frozen-source-candidate-v2.json.gz` contains 2,306 per-slot/scenario records:
  1,726 `RESOLVED`, 410 `NOT_APPLICABLE`, 21 `NO_ARMAMENT`, 16
  `RESOLVED_PRIMARY_TARGET` and 133 `UNRESOLVED` (108 TeslaArc, five
  FireShrapnel and 20 Mortar mismatch scenario records).
- `frozen-source-receipt-v2.json` and `.md` contain the source, matrix, adapter,
  helper and output hashes plus the full provenance boundary.

The immutable snapshot says it captured local ledgers from a dirty worktree, so
its `worktree_head` identifies a reproducible commit candidate but does not prove
that the clean commit contains the exact dirty source bytes used for those
ledgers. This candidate therefore remains `CANDIDATE`; it is not recovered
historical evidence, does not satisfy the version-1 `REVIEWED` reconstruction
contract, and must not unlock the 29 withheld groups. Review the source-state
reconciliation and substantive channel mapping before creating any admission
receipt.
