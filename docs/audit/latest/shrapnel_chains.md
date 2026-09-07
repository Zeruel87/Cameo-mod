# audit_shrapnel_chains - a FireShrapnel chain must END

| code | check | count | ratchet |  |
|---|---|---|---|---|
| S1a | MULTI-NODE CYCLE (A->B->A, a lost terminator) | 0 | 0 | PASS |
| S1b | SELF-CYCLE (A->A, chain lightning; review) | 0 | 0 | PASS |
| S2 | DANGLING (spawns a weapon that does not exist) | 0 | 0 | PASS |
| S3 | DEEP (> 6 bounces, review only) | 0 | - |  |


193 weapon(s) fire shrapnel; 193 chain(s) walked.


**PASS** - 0 multi-node cycle(s), 0 self-cycle(s), 0 dangling.
