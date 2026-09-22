"""THE list of reference sources that are one roster — data only, so every consumer shares it.

PRIOR ART: this is the consolidation of three hand-written lists that had drifted apart —
`synthesize_reference.SUPERSEDED` / `.NEAR_DUPLICATES` and `reference_distribution.LINEAGE_MEMBERS`.
It adds no new judgement; it holds the maintainer's rulings in one place so they cannot disagree.
`lineage_dedup.py` MEASURES lineages and checks this file against the corpus; it does not replace
it, because a ruling and a measurement are different things and both are needed.

⛔ WHY A DATA-ONLY MODULE. `lineage_dedup` imports `synthesize_reference` for its parsers, so
`synthesize_reference` cannot import `lineage_dedup` back. Keeping the rulings here — with no
imports of its own — is what lets all three consumers read the same list.

MAINTAINER ORDER 2026-09-03: *"All data needs to be unique and then used as a geometric mean for
the design."* A source that votes twice weights its lineage twice, and the geometric mean has no
defence against that. Measured impact of the RA2 lineage alone, before this was applied at the
rifle layer: it casts a MEDIAN 50% of all votes on the 128 multi-source units it touches and an
outright majority on 45 of them; giving it one vote moves the synthesized HP target by more than
10% on 52% of those units, up to 1.77x.
"""

# lineage representative -> the source labels that are the same roster and must not vote separately
#
# ⚠ EVERY LABEL MUST BE THE LABEL AS THE POOL SEES IT. The list this replaces carried `"RA2/YR"`
# while the parser labels that source `"RA2/YR (raw INI)"`, so the member never matched and voted
# all along — in the one list whose own comment warned that this would happen.
# `lineage_dedup.py` now fails the check when a label here is absent from the corpus.
RULED_LINEAGES = {
    # 2026-08-30. "RV is the OpenRA implementation of RA2 and YR so it already covers everything
    # from the original RA2 and YR games ... there is no benefit in duplicating it."
    # Measured at 91-100% agreement between the five members (`lineage_dedup.py`).
    # ⚠ RV itself measures as a REBALANCE of the lineage, not a copy — it is the sole dissenter on
    # 45% of the units the others agree on. Electing it adopts RV's numbers over vanilla's
    # consensus. That is the maintainer's call and it stands; it is recorded because it is not a
    # no-op.
    "Romanov's Vengeance": {
        "RA2 vanilla", "Yuri's Revenge", "RA2/YR (raw INI)",
        "OpenRA RA2 official", "Yuri's Revenge on OpenRA",
    },
    # 2026-09-03, applying the standing "one vote per balance lineage" rule to a lineage the
    # measurement found and no ruling covered: 96% of shared units within 10%, 100% within 25%,
    # geo-SD 1.05 — 25 of 27 agree to three decimals. OpenRA TS is elected on the RA2 precedent
    # (the live, resolvable codebase over a hand-extracted table).
    # ⚠ This changes nothing in the chassis layer, where only the representative is present; it
    # takes the Westwood TS table out of the RIFLE layer, where both were voting.
    "OpenRA Tiberian Sun": {"Tiberian Sun"},
    # 2026-09-06. DTA Enhanced IS DTA Classic plus `Enhance.ini`, which is how the game loads it,
    # so the two are one roster and were voting twice from the moment the INI corpus was wired in.
    # Measured on the 863 shared ids: identical hp 88%, cost 84%, speed 92%, damage 80%, range 85%,
    # median ratio exactly 1.000 on every stat — the same agreement profile as the RA2 lineage.
    # ⭐ ENHANCED is elected on the game's OWN default: DTA ships the ruleset as a lobby dropdown
    # (`Items=Classic,Enhanced`, `DefaultIndex=1`), so Enhanced is what a player actually gets.
    # Maintainer ruling 2026-09-06. ⚠ Not a no-op — it adopts the overlay's ~10-20% rebalanced
    # rows for td_gdi, td_nod, ra1_allies and ra1_soviets, whose routes move with it.
    "DTA Enhanced": {"DTA Classic"},
}

# One extraction of one mod superseded by a better extraction of the SAME mod. Not a lineage —
# these are literally the same source twice, and they agree exactly (Apocalypse 6.4x in both).
SUPERSEDED_EXTRACTS = {"Romanov's Veng.": "Romanov's Vengeance"}

# Reported, never merged: same underlying game, different extraction, and MEASURABLY not a copy.
# ⭐ These are the maintainer's own example — "the original TD and RA1 rules and the OpenRA rules
# are identical and just scaled" — and the corpus says otherwise, so they keep their votes:
#   Tiberian Dawn ~ OpenRA Tiberian Dawn : 41% within 10% (Mammoth 12.0 vs 17.4x, Commando 2 vs 3)
#   Red Alert 1   ~ OpenRA Red Alert     : 35% within 10% (Tesla Tank 2.2 vs 8.0x, MAD 6 vs 18x)
# OpenRA rebalances TD and RA1 as it ports them; it does not rebalance TS. Scale is not the issue
# in either case — both pairs sit at a median offset of exactly 1.00x once normalised to rifle.
NEAR_DUPLICATES = [
    ("Tiberian Dawn", "OpenRA Tiberian Dawn"),
    ("Red Alert 1", "OpenRA Red Alert"),
    ("OpenRA Dune 2000", "OpenRA Dune II"),
]


def superseded_map(present=None):
    """{source label: the label that supersedes it}, lineages and extracts together.

    `present` — when given, a source is dropped only if the thing superseding it is actually in
    the corpus. Dropping a member whose representative is absent deletes the lineage's only vote.
    """
    out = dict(SUPERSEDED_EXTRACTS)
    for rep, members in RULED_LINEAGES.items():
        for member in members:
            out[member] = rep
    if present is not None:
        out = {k: v for k, v in out.items() if v in present}
    return out


def all_labels():
    """Every source label these rulings name — what `lineage_dedup` checks against the corpus."""
    labels = set(SUPERSEDED_EXTRACTS) | set(SUPERSEDED_EXTRACTS.values())
    for rep, members in RULED_LINEAGES.items():
        labels |= members | {rep}
    return labels
