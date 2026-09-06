# audit_doc_health — is the documentation structurally sound?

Documents scanned: **224**

`audit_doc_claims.py` checks whether the NUMBERS are still true. This checks whether the documents themselves are intact.

| code | what | count |
|---|---|--:|
| D1 | literal control characters | 0 |
| D2 | mojibake (UTF-8 read as cp1252) | 0 |
| D3 | markdown link to a missing file | 1 |
| D4 | same-file anchor with no heading | 0 |
| D5 | reference to a moved/removed document | 0 |
| D6 | duplicate section id in DESIGN.md | 0 |
| D7 | Contents index missing a section | 0 |
| D8 | citation names a different section's law | 0 |


## D1 — Control characters (0)

_clean_


## D2 — Mojibake (0)

_clean_


## D3 — Broken links (1)

- `docs/design/CLASS_MOVES.md` → `BASELINE_ACTOR_REVIEW.md`


## D4 — Broken anchors (0)

_clean_


## D5 — Stale document references (0)

_clean_


## D6 — Duplicate DESIGN section ids (0)

_clean_


## D7 — Contents index out of date (0)

_clean_


## D8 — Citation points at the wrong law (0)

_clean_


**FAIL — 1 finding(s).** Fix the document; none of these are cosmetic. D1/D2 are corruption, D6 makes a cited law ambiguous, D3–D5 send a reader to the wrong place, D7 means a document is hiding its own content from the person who was told to read it, and D8 means a citation resolves — to the wrong law.
