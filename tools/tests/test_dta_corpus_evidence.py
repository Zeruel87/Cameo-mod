"""DTA corpus refresh (2026-09-10): the working-tree `ini_corpus.json` and its consumer
contract — data evidence, NOT runtime claim.

WHAT HAPPENED (parent session): the two DTA sources were re-extracted from the exact
received `Rules.ini` / `Enhance.ini` texts (sha256-verified per row: `source_sha256` /
`overlay_sha256`) and merged into the\nworking-tree corpus — 1726 rows (863 + 863) replaced, every OTHER source row byte-identical,
and the assignment fixed (nothing regenerated). A primary the old corpus authorised as an
authoritative rate is now either `incomplete` (reason on file) or `nominal_direct`, and the
point of this file is that the CONSUMER actually honours that: an incomplete DTA weapon may
not hand its direct-channel `w_dps` — nor any `dps_vs_*` product of it — to distributions or
targets, while hp / speed / cost and every non-DPS weapon field survive. The build-limit
(hero lane) obeys the same contract.

THE 127 COUNTER DEFINITION (what the refresh means by "127, not preliminary 132"): rows of
ONE DTA source whose BEFORE row carried a positive numeric `w_dps` and whose AFTER row
withholds it (`w_evidence` incomplete or `w_dps_usable` not True). 127 per source, 254 rows
total. The consumer carries such a number POSITIVE on `w_dps_raw` and withholds the vote —
the raw values are never read as zeros (some are legitimately NEGATIVE — healing channels —
those are withheld raws too, exactly as they were recorded).

LIMITATION (precise): per DTA source, 117 of the 127 previously-positive rates keep a
nonzero direct-channel diagnostic on the new `w_dps` (which the consumer moves to
`w_dps_raw`), but the 10 identity-corrected rows cannot — their old positive primary was
replaced by a primary whose direct channel reads the engine default (0), so there is no
`w_dps_raw` to carry for them. The old positive rate survives there only in the `w2_*`
slot record (itself non-voting, diagnostic-only) or in the BEFORE table; the raw NEW
damage channels (`w_railgun`, `w_ambient_damage`, particles) are kept in both.

THE DISTRIBUTION LANE composition for DTA is the standing one: `DTA Enhanced` is the
lineage representative (`reference_lineages`: DTA Enhanced IS DTA Classic + the loaded
overlay, one roster), `DTA Classic` rows are lineage members and never vote, and AI-ONLY
variants are filtered like every other source. Withheld-positive rows of those two excluded
groups stay withheld in the corpus data and never fold back in as numbers.

PROVENANCE is honest-by-construction: every DTA row carries
`source_runtime_version_status` / `engine_profile_applicability` = `unverified`; this file
pins the DATA, it does not claim the runtime reproduces those rules, and no standalone
`verified`/`factory`/`ready` token appears in any verdict or provenance field.

⛔ READ-ONLY. The working-tree corpus is pinned by its sha256. The external BEFORE corpus
(byte-identity and the 127 counter) is only consulted when `REFERENCE_DTA_BEFORE_CORPUS` is
set — the ordinary suite must not depend on it.
"""

from __future__ import annotations

import collections
import hashlib
import json
import os
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
CORPUS = ROOT / 'docs' / 'reference' / 'ini_corpus.json'
CORPUS_SHA256 = 'c1883cb04d2b42b370aa1dba3bdd12c080d909c61a3d3adf92156f5f931ed92a'
BEFORE_ENV = 'REFERENCE_DTA_BEFORE_CORPUS'
BEFORE_SHA256 = '204391b21a95b3c5409b9d146a33f07b8b1404e5c4e0369976ab9859db1081b1'
# The ten primary identities the refresh corrected (the old auto-promotion had rewritten the
# primary slot; the re-extract keeps the ORIGINAL primary whole, with its raw evidence, and
# the secondary explicitly under `w2_*`). Three are AI-only variants the consumer filters;
# all ten belong to the data contract.
IDENTITY_FIXES = ('AIMTNK', 'AISCRINTNK', 'AIXO', 'BRIG', 'EKRACARR',
                  'MTNK', 'MWAVEMSAM', 'SCRINTNK', 'SP941', 'XO')
READY_TOKENS = re.compile(r"\b(verified|ready|validated|factory)\b")

sys.path.insert(0, str(ROOT / 'tools' / 'balance'))
import reference_distribution as rd   # noqa: E402


class CorpusOfRecordTest(unittest.TestCase):
    """The working-tree bytes and the refresh's shape claims, verified not trusted."""

    @classmethod
    def setUpClass(cls):
        with open(CORPUS, 'rb') as f:
            text = f.read().decode('utf-8')
        cls.rows = [json.loads(l) for l in text.splitlines() if l.strip()]
        cls.dta = {}
        for r in cls.rows:
            if r['source'].startswith('DTA'):
                cls.dta.setdefault(r['source'], {})[r['id']] = r
        cls.after_index = {(r['source'], r['id']): r for r in cls.rows}

    def test_corpus_is_the_file_pinned_here(self):
        self.assertEqual(hashlib.sha256(CORPUS.read_bytes()).hexdigest(), CORPUS_SHA256)

    def test_row_counts_1726_dta(self):
        counts = collections.Counter(r['source'] for r in self.rows)
        self.assertEqual(len(self.rows), 11870)
        self.assertEqual(counts['DTA Classic'], 863)
        self.assertEqual(counts['DTA Enhanced'], 863)
        self.assertEqual(counts['DTA Classic'] + counts['DTA Enhanced'], 1726)

    def test_non_dta_rows_carry_no_evidence_fields(self):
        # the old corpus shape survives verbatim outside DTA; only the replaced rows
        # transitioned to the verdict vocabulary
        for r in self.rows:
            if not r['source'].startswith('DTA'):
                for key in ('w_evidence', 'w_dps_usable', 'w_evidence_reason'):
                    self.assertNotIn(key, r, (r['source'], r['id'], key))

    def test_provenance_is_unverified_by_construction(self):
        for src in ('DTA Classic', 'DTA Enhanced'):
            for r in self.dta[src].values():
                self.assertEqual(r['source_runtime_version_status'], 'unverified')
                self.assertEqual(r['engine_profile_applicability'], 'unverified')
        for r in self.rows:
            for key in ('source_runtime_version_status', 'engine_profile_applicability',
                        'source_label', 'profile_selection'):
                self.assertIsNone(READY_TOKENS.search(str(r.get(key, ''))), (r['id'], key))

    def test_exact_primary_identity_corrections(self):
        for src in ('DTA Classic', 'DTA Enhanced'):
            corrected = {i for i, r in self.dta[src].items() if i in IDENTITY_FIXES}
            self.assertEqual(len(corrected), 10)
            for i in IDENTITY_FIXES:
                row = self.dta[src][i]
                self.assertIn(row.get('w_evidence'), ('incomplete', 'nominal_direct'),
                              (src, i))
                self.assertIsInstance(row.get('w2_weapon'), str, (src, i))
            xo = self.dta[src]['XO']
            self.assertEqual(xo['weapon'], 'XORail')
            self.assertEqual(xo['w2_weapon'], 'XOMachineGun')
            self.assertTrue(xo['w_railgun'])
            self.assertEqual(xo['w_ambient_damage'], 150)
            self.assertEqual(xo['w_evidence'], 'incomplete')
            self.assertEqual(xo['w_evidence_reason'], 'exotic_channels')
            self.assertIsNone(xo.get('w_dps'))
            self.assertIsInstance(xo.get('w2_damage'), (int, float))
            self.assertEqual(xo.get('w2_evidence'), 'nominal_direct')  # MG slot, whole

    def test_overlay_precedence_declared_enhanced_only(self):
        for r in self.rows:
            if r['source'] == 'DTA Classic':
                self.assertNotIn('overlay_sha256', r)
            elif r['source'] == 'DTA Enhanced':
                self.assertEqual(r['overlay_precedence'], 'overlay_over_rules')
                self.assertIn('overlay_sha256', r)


class ConsumerWithholdingTest(unittest.TestCase):
    """`ini_rows` + `peer_rows`/`peer_hero_rows`: withheld DTA w_dps/dps_vs_* — chassis
    survives and the kept raws are carried VERBATIM, never read as zeros. The distribution
    lane keeps only the lineage representative (DTA Enhanced) minus AI-only variants."""

    @classmethod
    def setUpClass(cls):
        cls.peers = rd.peer_rows()
        cls.rows = [r for r in cls.peers if r['source'].startswith('DTA')]
        cls.withheld = [r for r in cls.rows if r.get('w_dps_raw') is not None]
        cls.ai_withheld = [r for r in rd.peer_rows.ai_only
                           if r['source'].startswith('DTA')
                           and r.get('w_dps_raw') is not None]
        cls.hero_rows = rd.peer_hero_rows()
        cls.dta_hero = [r for r in cls.hero_rows
                        if r['source'].startswith('DTA') and r.get('w_dps_raw') is not None]
        cls.by_key = {}
        with open(CORPUS, 'rb') as f:
            for r in map(json.loads, (l for l in f.read().decode('utf-8').splitlines() if l.strip())):
                if r['source'].startswith('DTA'):
                    cls.by_key[(r['source'], r['id'])] = r

    def _withheld_checks(self, row):
        self.assertIsNone(row.get('w_dps'), (row['source'], row['id']))
        self.assertIsNotNone(row.get('w_dps_raw'))
        self.assertNotEqual(row.get('w_dps_raw'), 0)      # never a folded zero
        self.assertEqual(row.get('w_evidence'), 'incomplete')
        for lad in rd.LADDERS:
            self.assertIsNone(row.get(f'dps_vs_{lad}'), (row['source'], row['id'], lad))
        self.assertIsNotNone(row.get('hp'))
        self.assertEqual(row.get('w_dps_raw'),
                         self.by_key[(row['source'], row['id'])].get('w_dps'))

    def test_lane_composition_is_the_standing_one(self):
        srcs = collections.Counter(r['source'] for r in self.rows)
        self.assertEqual(srcs, {'DTA Enhanced': 155})   # lineage representative only, no AI

    def test_ordinary_withheld_count_is_exact_and_raws_survive(self):
        self.assertEqual(len(self.withheld), 5)
        raws = [r['w_dps_raw'] for r in self.withheld]
        self.assertEqual(sum(1 for x in raws if x > 0), 0)    # Remaining raw rates are healing channels.
        self.assertGreater(sum(1 for x in raws if x < 0), 0)     # healing channels too
        for r in self.withheld:
            self._withheld_checks(r)

    def test_ai_only_withholds_stay_out_of_the_vote(self):
        self.assertEqual(len(self.ai_withheld), 0)
        by_src = collections.defaultdict(set)
        for r in self.peers:
            rid = (r.get('id') or '').strip().upper()
            if rid:
                by_src[r['source']].add(rid)
        for r in self.ai_withheld:
            self.assertTrue(rd.is_ai_only(r, by_src), r['id'])
            self.assertIsNone(r.get('w_dps'))
            self.assertIsNotNone(r.get('w_dps_raw'))

    def test_build_limit_lane_withholds(self):
        self.assertEqual(len(self.dta_hero), 1)  # A10 now has an explicit aircraft timer profile.
        for r in self.dta_hero:
            self.assertIsNone(r['w_dps'])
            self.assertNotEqual(r['w_dps_raw'], 0)
            for lad in rd.LADDERS:
                self.assertIsNone(r[f'dps_vs_{lad}'])
            self.assertIsNotNone(r.get('hp'))

    def test_chassis_survives_verbatim_on_every_dta_lane_row(self):
        for r in self.rows:
            raw = self.by_key[(r['source'], r['id'])]
            self.assertEqual(r.get('hp'), raw.get('hp'), r['id'])
            self.assertEqual(r.get('cost'), raw.get('cost'), r['id'])
            self.assertEqual(r.get('speed'), raw.get('speed'), r['id'])
            # ⛔ `w_damage` IS PER CYCLE SINCE 2026-09-13 (maintainer: the referenced coordinate
            # is the whole burst, because burst is a delivery choice and SP ships the Mammoth
            # Mk. II at Burst 4 where TS ships it at Burst 2 — per shot they look identical).
            # `to_per_cycle` carries the raw per-shot figure alongside as `w_damage_per_shot`,
            # so THAT is what still matches the corpus verbatim. Comparing `w_damage` to the raw
            # value asserts the superseded convention and fails by exactly the burst (150 vs 75
            # on `MSAM`).
            if r['id'] == 'MTNK':
                # Exact-row reviewed secondary selection; raw corpus is unchanged.
                self.assertEqual(r.get('w_damage_per_shot'), raw.get('w2_damage'))
                self.assertEqual(r.get('wdummy_damage'), raw.get('w_damage'))
            else:
                self.assertEqual(r.get('w_damage_per_shot'), raw.get('w_damage'), r['id'])
            burst = float(r.get('w_burst') or 1)
            if r.get('w_damage_per_shot') is not None:
                self.assertAlmostEqual(r['w_damage'], r['w_damage_per_shot'] * burst, msg=r['id'])

    def test_reviewed_tesla_retains_original_exotic_verdict_without_armor_claim(self):
        row = next(r for r in self.rows if r['id'] == 'RATSLA')
        self.assertEqual(row['pre_cycle_evidence']['w_evidence_reason'], 'exotic_channels')
        self.assertEqual(row['w_dps'], 300 / 173)
        self.assertTrue(row['w_railgun'])
        for lad in rd.LADDERS:
            self.assertIsNone(row['dps_vs_' + lad])

    def test_nominal_direct_dta_rows_keep_the_declared_contract(self):
        good = [r for r in self.rows if r.get('w_evidence') == 'nominal_direct']
        self.assertGreater(len(good), 30)
        for r in good:
            self.assertNotIn('w_dps_raw', r)
            self.assertIsNotNone(r.get('w_dps'))
            self.assertIs(r.get('w_dps_usable'), True)

    def test_evidence_counts_are_exposed_not_hidden(self):
        counts = rd.evidence_counts(self.peers)
        # Selected CA and base-OpenRA sources expose incomplete ordinary rows;
        # do not hide them behind the former legacy count (base migration: +118).
        self.assertEqual(counts['incomplete'], 208)
        self.assertEqual(counts['nominal_direct'], 265)
        self.assertEqual(counts['legacy-unassessed'], 3894)
        self.assertEqual(sum(counts.values()), 4367)  # TD RMBO now belongs to the explicit hero lane.
        other = rd.evidence_counts([r for r in self.peers if r['source'] != 'Combined Arms'])
        self.assertEqual(other['incomplete'], 65)
        self.assertEqual(other['nominal_direct'], 139)
        self.assertEqual(other['legacy-unassessed'], 3822)


class OptionalBeforeCorpusTest(unittest.TestCase):
    """RAW-BYTE identity + the 127 counter vs the EXTERNAL before-corpus (report-time only).

    ⛔ The comparison is on the FILES' own byte LINES — splitlines(keepends=True), filter by
    the row's source, compare in order with duplicates and line endings intact. A keyed
    (source, id) dict cannot serve here: it silently collapses the 3 duplicate identities the
    old corpus already carried, and `json.dumps` equality is semantic, not byte identity.
    The baseline file's sha256 is validated BEFORE a single byte of it is used.
    """

    BEFORE = os.environ.get(BEFORE_ENV)

    @classmethod
    def setUpClass(cls):
        if not cls.BEFORE:
            raise unittest.SkipTest(f'{BEFORE_ENV} not set; the external baseline is a '
                                    'report-time dependency, not a suite dependency')
        with open(cls.BEFORE, 'rb') as f:
            cls.before_sha = hashlib.sha256(f.read()).hexdigest()
        with open(CORPUS, 'rb') as f:
            cls.after_sha = hashlib.sha256(f.read()).hexdigest()
        # constant is finally USED: refuse the file before anything reads it
        if cls.before_sha != BEFORE_SHA256:
            raise unittest.SkipTest(f'baseline sha256 mismatch: {cls.before_sha[:16]}… '
                                    f'!= {BEFORE_SHA256[:16]}… — not the pinned BEFORE file')
        if cls.after_sha != CORPUS_SHA256:
            raise unittest.SkipTest('working-tree corpus is not the sha256 pinned at the top '
                                    'of this file; re-pin the constants first')

    @staticmethod
    def raw_lines(path):
        with open(path, 'rb') as f:
            return f.read().decode('utf-8').splitlines(keepends=True)   # endings preserved

    @staticmethod
    def row(lines):
        return json.loads(lines[0])

    def _by_source(self, path):
        lines = self.raw_lines(path)
        non_dta = [l for l in lines
                   if l.strip()
                   and self.row([l])['source'] not in ('DTA Classic', 'DTA Enhanced')]
        return lines, non_dta

    def test_non_dta_lines_are_byte_identical_in_order(self):
        b_lines, b_nd = self._by_source(self.BEFORE)
        a_lines, a_nd = self._by_source(CORPUS)
        # 11870 - 1726 = 10144 NON-DTA lines — the previous 10141 was the keyed-dict count
        # that had silently collapsed three duplicate identities.
        self.assertEqual(len(b_nd), 10144)
        self.assertEqual(len(a_nd), 10144)
        self.assertEqual(len(b_lines), len(a_lines))                 # total, endings included
        for i, (bl, al) in enumerate(zip(b_nd, a_nd)):
            self.assertEqual(bl, al, f'first byte diff at non-DTA line {i + 1}')
        self.assertEqual(b_nd, a_nd)                                 # order + duplicates + endings
        self.assertEqual(b_lines[-1], a_lines[-1])                   # trailing bytes on the file

    def test_duplicate_identities_are_counted_not_collapsed(self):
        b_lines, b_nd = self._by_source(self.BEFORE)
        keys = [(self.row([l])['source'], self.row([l])['id']) for l in b_nd]
        counts = collections.Counter(keys)
        dups = {k for k, v in counts.items() if v > 1}
        self.assertEqual(len(keys) - len(dups), 10141)   # unique (source, id) pairs, reported
        self.assertEqual(dups, {('Red Resurrection', 'NAINDP'),
                                ('Red Resurrection', 'NAFLAKAI1'),
                                ('RA2 Reborn', 'NAPSYA')})  # carried through, never merged

    def test_127_counter_definition_remeasured(self):
        with open(self.BEFORE, 'rb') as f:
            before = {(r['source'], r['id']): r for r in
                      map(json.loads, (l for l in f.read().decode('utf-8').splitlines() if l.strip()))}
        with open(CORPUS, 'rb') as f:
            after = {(r['source'], r['id']): r for r in
                     map(json.loads, (l for l in f.read().decode('utf-8').splitlines() if l.strip()))}
        counts = {}
        for src in ('DTA Classic', 'DTA Enhanced'):
            n = 0
            for (s, rid), ob in before.items():
                if s != src:
                    continue
                was_pos = isinstance(ob.get('w_dps'), (int, float)) and ob.get('w_dps', 0) > 0
                former = after[(s, rid)]
                withheld = (former.get('w_evidence') == 'incomplete'
                            or former.get('w_dps_usable') is not True)
                if was_pos and withheld:
                    n += 1
            counts[src] = n
        self.assertEqual(counts, {'DTA Classic': 127, 'DTA Enhanced': 127})


if __name__ == '__main__':
    unittest.main()
