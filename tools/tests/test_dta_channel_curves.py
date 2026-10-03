"""Synthetic tests for the DTA source-basis channel adapter."""
import contextlib
import copy
import io
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "balance"))
import dta_channel_curves as curves  # noqa: E402


def armor_evidence(warhead="HE", values=None):
    values = values or {key: 100 for key in curves.DTA_ARMOR_KEYS.values()}
    return {"profiles": {warhead: {key: {"percent": value} for key, value in values.items()}}}


def payload_evidence():
    return {"retained_weapon_systems": {}, "particle_systems": {}}


def proof(status="MATCHED", reason=None):
    result = {"status": status}
    if reason:
        result["reason"] = reason
    return result


def channel(*, weapon="Gun", warhead="HE", damage="100", versus=None, fields=None):
    return {"source": None, "actor": None, "slot": None, "weapon": weapon,
            "warhead": warhead, "damage": damage,
            "resolved_versus": versus or {key: 100 for key in curves.DTA_ARMOR_KEYS.values()},
            "fields": fields if fields is not None else {"damage": damage}}


class DtaChannelCurveTests(unittest.TestCase):
    def test_ordinary_damage_uses_exact_dta_armor_profile_and_zero(self):
        values = {"none": 200, "wood": 100, "light": 0, "concrete": 50, "heavy": 25}
        row = channel(damage="100", versus=values)
        result = curves.reduce_weapon_channels([row], armor_evidence=armor_evidence(values=values),
                                               payload_evidence=payload_evidence(),
                                               proof=proof(), weapon="Gun")
        self.assertEqual(result["status"], "BASE_CHANNELS_RESOLVED")
        self.assertEqual(result["terms"]["None"]["direct"], 200)
        self.assertEqual(result["terms"]["Light"]["direct"], 0)
        self.assertEqual(result["terms"]["Heavy"]["direct"], 25)
        self.assertEqual(result["terms"]["None"]["B"], 0)

    def test_railgun_ambient_is_added_once_per_target_and_kept_separate(self):
        row = channel(weapon="XORail", warhead="RailShot", damage="0",
                      fields={"damage": "0", "ambientdamage": "150", "israilgun": "true"})
        result = curves.reduce_weapon_channels([row], armor_evidence=armor_evidence("RailShot"),
                                               payload_evidence=payload_evidence(),
                                               proof=proof(), weapon="XORail")
        self.assertEqual(result["status"], "BASE_CHANNELS_RESOLVED")
        self.assertEqual(result["terms"]["None"]["direct"], 0)
        self.assertEqual(result["terms"]["None"]["ambient"], 150)
        self.assertEqual(result["ambient_components"][0]["application"],
                         "once_per_collected_target")
        missing = channel(weapon="XORail", warhead="RailShot", damage="0",
                          fields={"damage": "0", "israilgun": "true"})
        self.assertIn("railgun_ambientdamage_missing",
                      curves.reduce_weapon_channels([missing], armor_evidence=armor_evidence("RailShot"),
                                                     payload_evidence=payload_evidence(), proof=proof(),
                                                     weapon="XORail")["reason"])

    def test_railgun_explicit_zero_ambient_is_valid(self):
        row = channel(weapon="PortaTesla", warhead="Super", damage="60",
                      fields={"damage": "60", "ambientdamage": "0", "israilgun": "true"})
        result = curves.reduce_weapon_channels([row], armor_evidence=armor_evidence("Super"),
                                               payload_evidence=payload_evidence(),
                                               proof=proof(), weapon="PortaTesla")
        self.assertEqual(result["status"], "BASE_CHANNELS_RESOLVED")
        self.assertEqual(result["terms"]["None"]["direct"], 60)
        self.assertEqual(result["terms"]["None"]["ambient"], 0)

    def test_particle_binding_spawner_and_suicide_are_fail_closed(self):
        payload = {"retained_weapon_systems": {"Gun": "SmokeSys"},
                   "particle_systems": {"SmokeSys": {"behavior": "Smoke",
                                                       "held_behavior": "Smoke",
                                                       "additional_hp_damage": 0}}}
        admitted = channel(fields={"damage": "100", "attachedparticlesystem": "SmokeSys"})
        result = curves.reduce_weapon_channels([admitted], armor_evidence=armor_evidence(),
                                               payload_evidence=payload, proof=proof(), weapon="Gun")
        self.assertEqual(result["status"], "BASE_CHANNELS_RESOLVED")
        self.assertEqual(result["channel_terms"][0]["particle_evidence"]["system"], "SmokeSys")
        unknown = channel(fields={"damage": "100", "attachedparticlesystem": "OtherSys"})
        self.assertIn("attached_particle_binding_mismatch",
                      curves.reduce_weapon_channels([unknown], armor_evidence=armor_evidence(),
                                                     payload_evidence=payload, proof=proof(), weapon="Gun")["reason"])
        for flag, reason in (("spawner", "spawner_payload_unresolved"),
                             ("suicide", "suicide_payload_unresolved")):
            flagged = channel(damage="0", fields={"damage": "0", flag: "yes"})
            result = curves.reduce_weapon_channels([flagged], armor_evidence=armor_evidence(),
                                                   payload_evidence=payload_evidence(),
                                                   proof=proof(), weapon="Gun")
            self.assertIn(reason, result["reason"])

    def test_missing_or_mismatched_proof_and_armor_withhold_totals(self):
        row = channel(damage="100", versus={"none": 100})
        result = curves.reduce_weapon_channels([row], armor_evidence=armor_evidence(),
                                               payload_evidence=payload_evidence(),
                                               proof=proof("UNRESOLVED", "proof mismatch"), weapon="Gun")
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIsNone(result["terms"])
        mismatched = channel(damage="100", versus={key: 99 for key in curves.DTA_ARMOR_KEYS.values()})
        result = curves.reduce_weapon_channels([mismatched], armor_evidence=armor_evidence(),
                                               payload_evidence=payload_evidence(),
                                               proof=proof(), weapon="Gun")
        self.assertIn("resolved_versus_profile_mismatch", result["reason"])
        self.assertIsNone(result["terms"])

    def test_duplicate_weapon_warhead_and_input_rows_are_not_summed(self):
        first = channel(damage="100")
        duplicate = copy.deepcopy(first)
        before = copy.deepcopy([first, duplicate])
        result = curves.reduce_weapon_channels([first, duplicate], armor_evidence=armor_evidence(),
                                               payload_evidence=payload_evidence(),
                                               proof=proof(), weapon="Gun")
        self.assertEqual(result["status"], "BASE_CHANNELS_RESOLVED")
        self.assertEqual(result["terms"]["None"]["direct"], 100)
        self.assertEqual(result["channel_terms"][0]["duplicate_count"], 2)
        self.assertEqual(result["duplicate_trace"][0]["status"], "COLLAPSED")
        conflicting = dict(first, damage="200")
        result = curves.reduce_weapon_channels([first, conflicting], armor_evidence=armor_evidence(),
                                               payload_evidence=payload_evidence(),
                                               proof=proof(), weapon="Gun")
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIn("nonidentical duplicate", result["reason"])
        self.assertIsNone(result["terms"])
        self.assertEqual([first, duplicate], before)

    def test_build_emits_only_dta_reference_weapon_and_cli_guarded_output(self):
        row = channel(weapon="M1Carbine", damage="15")
        matrix = {"rows": [{"actor": "cameo", "references": [
            {"source": "OpenRA Red Alert", "id": "RA", "selected_weapon_channels": [row]},
            {"source": "DTA Enhanced", "id": "DTA", "selected_weapon_channels": [row]},
        ]}]}
        result = curves.build(matrix, armor_evidence=armor_evidence(),
                              payload_evidence=payload_evidence(), proof=proof())
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["records"][0]["status"], "BASE_CHANNELS_RESOLVED")
        with tempfile.TemporaryDirectory() as directory:
            directory = pathlib.Path(directory)
            matrix_path = directory / "matrix.json"
            output = directory / "dta.json"
            markdown = directory / "dta.md"
            matrix_path.write_text(json.dumps(matrix), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(curves.main(["--matrix", str(matrix_path), "--out", str(output),
                                              "--markdown", str(markdown)]), 0)
            written = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(written["input_guard"]["unchanged"])
            self.assertEqual(written["input_guard"]["before"], written["input_guard"]["after"])
            self.assertIn("DTA source channel curve review",
                          markdown.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
