# audit_doc_health — is the documentation structurally sound?

Documents scanned: **471**

`audit_doc_claims.py` checks whether the NUMBERS are still true. This checks whether the documents themselves are intact.

| code | what | count |
|---|---|--:|
| D1 | literal control characters | 0 |
| D2 | mojibake (UTF-8 read as cp1252) | 1 |
| D3 | markdown link to a missing file | 0 |
| D4 | same-file anchor with no heading | 0 |
| D5 | reference to a moved/removed document | 0 |
| D6 | duplicate section id in DESIGN.md | 0 |
| D7 | Contents index missing a section | 1 |
| D8 | citation names a different section's law | 1 |


## D1 — Control characters (0)

_clean_


## D2 — Mojibake (1)

- `DEVELOPMENT_LOG.md` — 1 distinct sequence(s), e.g. ['Â§']


## D3 — Broken links (0)

_clean_


## D4 — Broken anchors (0)

_clean_


## D5 — Stale document references (0)

_clean_


## D6 — Duplicate DESIGN section ids (0)

_clean_


## D7 — Contents index out of date (1)

- `docs/LESSONS_LEARNED.md` — Contents omits ``launch-game.cmd` fails from Git Bash — GNU `find` shadows Windows `find.exe` (2026-10-02, EMBER)`


## D8 — Citation points at the wrong law (1)

- `DEVELOPMENT_LOG.md`:930 — cites §19.3 (One bot module per decision: merge dupli) but names `OpenRA`, which is §17 (Dune 2000 to OpenRA Sprite Conversion)


**FAIL — 3 finding(s).** Fix the document; none of these are cosmetic. D1/D2 are corruption, D6 makes a cited law ambiguous, D3–D5 send a reader to the wrong place, D7 means a document is hiding its own content from the person who was told to read it, and D8 means a citation resolves — to the wrong law.
