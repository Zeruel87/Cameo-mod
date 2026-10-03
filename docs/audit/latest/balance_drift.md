# audit_balance_drift — yaml vs committed balance ledger

**1 ledger(s) drifted** — balance numbers were hand-edited in yaml, or a sanctioned apply run was not followed by re-extraction. Fix via the pipeline, never by hand:

## redalert2mod_asianalliance

```diff
       "versus_templates": [
-       "RA2FlakTrackGun",
+       "^Warhead_Flak_Medium",
+       "^Projectile_Flak_Medium",
+       "^Effect_Flak_Puff_RA2",
+       "^Effect_Watersplash_Small_RA2",
        "^Warhead_Flak_Medium_Flat"
```

