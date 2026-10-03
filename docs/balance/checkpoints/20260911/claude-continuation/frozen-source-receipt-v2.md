# Candidate historical-source Cameo channel reconstruction

**CANDIDATE ONLY.** This is a reproducible clean-commit source candidate, not recovered original channel evidence or a self-vote admission.

- Source commit candidate: `9471672b2e908661334804dbfe022ccc267d3192`
- Frozen snapshot SHA-256: `726ada6afec708f8c6e9798ecbfb2758c842195f66755c2d5e683432c4a86f95`
- Original pilot matrix SHA-256: `b1a2cc354baf71e1054d9ed94783bf937df16504406be6503e77b9fe4be0e721`
- Rebuilt matrix: `5148ea4e7844e64c3896e0bd3a2a42c2fc1bfc6be9f79b7ccb96096178258ffa` (4 mismatched armaments retained unresolved)
- Candidate output: `C:\Users\Blackrobe\Documents\agents\cameo-original-channel-reconstruction-20260912\baseline-candidate-v2.json` (59,534,275 bytes; gzip 2,389,440 bytes)

- Actors: **163**; records: **2306**; statuses: `{'RESOLVED': 1726, 'NOT_APPLICABLE': 410, 'NO_ARMAMENT': 21, 'RESOLVED_PRIMARY_TARGET': 16, 'UNRESOLVED': 133}`
- Unresolved actors: **16** (15 payload-unsupported actors plus Mortar Soldier’s explicit source/matrix mismatch)
- Unresolved reason prefixes: `{'Warhead@TeslaArc': 108, 'actor_slot_weapon_mismatch': 20, 'Warhead@Shrapnel': 5}`

## Provenance boundary

The snapshot metadata says it captures current local ledgers, not a clean commit. Its `worktree_head` identifies commit `9471672b`, but it does not prove that commit contains the dirty source bytes used for the ledgers. This run rebuilds armament and warhead metadata from a clean checkout at that commit, retains the four Mortar Soldier mismatches as unresolved, and leaves TeslaArc/FireShrapnel payloads unresolved. An independent reviewer must reconcile the dirty source state and substantive mapping before producing a `REVIEWED` admission receipt.

## Reproduction

Import the current adapter and run `build(matrix, Ruleset(source_root))` with `baseline-matrix-v2.json`; the matrix and helper/source SHA-256 manifests in `baseline-receipt-v2.json` identify the exact inputs. The compressed candidate is for transfer; decompress it before using it as JSON. No gameplay, engine build or runtime test was performed.
