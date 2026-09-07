# Formula v2 validation — class `support`

anchor: `SPEC(5000,50,0,0,1,500)` (cost0 500, O0 110.00, P0 10.00, Q0 0.00)

**Not combat-priced:** an estimator is zero (O0/P0/Q0 must all be non-zero for `cost0 * (O/O0+P/P0+Q/Q0)/3`). Ability-priced classes like `support` carry dps0 = 0 by design and are validated by their special-K ledger, not this formula.
