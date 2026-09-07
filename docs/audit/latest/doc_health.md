# audit_doc_health — is the documentation structurally sound?

Documents scanned: **257**

`audit_doc_claims.py` checks whether the NUMBERS are still true. This checks whether the documents themselves are intact.

| code | what | count |
|---|---|--:|
| D1 | literal control characters | 0 |
| D2 | mojibake (UTF-8 read as cp1252) | 0 |
| D3 | markdown link to a missing file | 0 |
| D4 | same-file anchor with no heading | 0 |
| D5 | reference to a moved/removed document | 0 |
| D6 | duplicate section id in DESIGN.md | 0 |
| D7 | Contents index missing a section | 0 |
| D8 | citation names a different section's law | 0 |


## D1 — Control characters (0)

_clean_


## D2 — Mojibake (0)

_clean_


## D3 — Broken links (0)

_clean_


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


**PASS** — no structural defects.
