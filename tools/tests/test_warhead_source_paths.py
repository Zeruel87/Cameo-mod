import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'reference'))
import aggregate_archetype as ag
import survey_platforms as sp
import propose_family_profiles as proposals


class SourcePaths(unittest.TestCase):
    def test_no_matching_role_cannot_be_relabelled_as_opposite_family(self):
        cache = {'cannon': [{'platform': 'vehicle_medium', 'source': 'test',
                             'versus': {'light': 100, 'medium': 50, 'heavy': 10}}]}
        self.assertIsNone(proposals.profile_for('CannonAP', 'Medium', cache))

    def test_registry_accepts_dta_labels_and_numeric_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            rules = pathlib.Path(directory) / 'Rules.ini'
            rules.write_text('[VehicleTypes]\n0=TANK\nA_01=JEEP\n;2=DISABLED\n'
                             '[BuildingTypes]\n......131072=GFACT\n'
                             '[Other]\n0=NOT_ACTOR\n')
            self.assertEqual(sp.type_registry(rules),
                             {'TANK': 'VEH', 'JEEP': 'VEH', 'GFACT': 'BLD'})

    def test_recorded_overlay_keeps_base_actor_and_override(self):
        with tempfile.TemporaryDirectory() as directory:
            base = pathlib.Path(directory) / 'Rules.ini'
            overlay = pathlib.Path(directory) / 'Enhance.ini'
            base.write_text('[OBLI]\nPrimary=Laser\nCost=1000\n[Laser]\nWarhead=AP\n')
            overlay.write_text('[OBLI]\nCost=1200\n')
            sources = {'dta_enhanced': {'path': str(overlay), 'base_path': str(base)}}
            path = ag.source_path('dta_enhanced', sources)
            resolved = ag.read_ini_resolved('dta_enhanced', path, sources)
            self.assertEqual(resolved['OBLI']['cost'], '1200')
            self.assertEqual(ag.trace_ini(resolved, 'OBLI'), [('Laser', 'AP')])
            base.unlink()
            with self.assertRaises(FileNotFoundError):
                ag.read_ini_resolved('dta_enhanced', path, sources)

    def test_recorded_missing_path_does_not_substitute_another_version(self):
        path = ag.source_path('dta_classic', {'dta_classic': {'path': 'missing-version.ini'}})
        self.assertEqual(path, pathlib.Path('missing-version.ini'))


if __name__ == '__main__':
    unittest.main()
