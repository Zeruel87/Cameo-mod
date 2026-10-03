"""CombatAnalysisBotModule is a producer-only IBotThreatAnalysis implementation.

Ports CN's CombatAnalysisBotModule (crystallized-nexus 30cf70a): per-role threat
weights with decay plus a nemesis player, fed by IBotRespondToAttack. The module
is deliberately NOT wired into target scoring — BotSituation.cs /
SquadManagerBotModuleCA consumption is a separate later lane, so any new
IBotThreatAnalysis reference outside the module and its interface fails here.
"""
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/audit"))
from miniyaml import Ruleset

MODULE = ROOT / "OpenRA.Mods.Cameo/Traits/BotModules/CombatAnalysisBotModule.cs"
INTERFACE = ROOT / "OpenRA.Mods.CA/Traits/BotModules/IBotThreatAnalysis.cs"
CODE_DIRS = [ROOT / "OpenRA.Mods.CA", ROOT / "OpenRA.Mods.Cameo"]
OWNED = {MODULE.resolve(), INTERFACE.resolve()}

# The consumption lane landed with INC-1/2/3 (#720): BotSituation reads the
# analysis. Any FURTHER consumer must be added here deliberately.
LANDED_CONSUMERS = {
    (ROOT / "OpenRA.Mods.Cameo/Traits/BotModules/BotSituation.cs").resolve(),
}


class CombatAnalysisContractTests(unittest.TestCase):
    def test_module_is_registered_on_the_player_actor(self):
        rules = Ruleset(ROOT)
        player = rules.resolve("Player")
        self.assertIsNotNone(player, "ai.yaml Player actor missing")
        node = player.child("CombatAnalysisBotModule")
        self.assertIsNotNone(node, "CombatAnalysisBotModule is not registered on the Player actor")
        self.assertEqual("genericbot", node.child("RequiresCondition").value)

    def test_module_is_a_player_trait_not_a_world_trait(self):
        # ai.yaml defines BOTH actors; appending at file end lands under World.
        rules = Ruleset(ROOT)
        self.assertIsNone(
            rules.resolve("World").child("CombatAnalysisBotModule"),
            "CombatAnalysisBotModule is TraitLocation(Player) — it must not be on World")

    def test_role_names_match_demand_suffixes(self):
        iface = INTERFACE.read_text(encoding="utf-8")
        for role, demand in [("AntiAir", "antiair"), ("AntiArmour", "antiarmour"), ("AntiInfantry", "antiinfantry")]:
            self.assertIn(f'const string {role} = "{demand}"', iface)

        rules = Ruleset(ROOT)
        player = rules.resolve("Player")
        for demand in ("antiair", "antiarmour", "antiinfantry"):
            self.assertIsNotNone(
                player.child(f"ProvidesPrerequisite@demand{demand}"),
                f"threat role {demand} has no matching demand.* prerequisite provider")

    def test_module_implements_the_interface_and_ticks(self):
        source = MODULE.read_text(encoding="utf-8")
        decl = re.search(r"class CombatAnalysisBotModule\s*:\s*([^\n]+)", source).group(1)
        for contract in ("IBotThreatAnalysis", "IBotRespondToAttack", "IBotTick"):
            self.assertIn(contract, decl, f"CombatAnalysisBotModule does not implement {contract}")

        # The port must keep CN's three behaviours: per-role decaying weights,
        # a nemesis player, and per-attacker nemesis throttling.
        self.assertIn("nemesisScores[attacker]", source)
        self.assertIn("weights[role] = Math.Min(100f", source)
        self.assertIn("weights[key] * decay", source)

    def test_producer_only_no_consumer_references_the_interface(self):
        offenders = []
        for directory in CODE_DIRS:
            for path in sorted(directory.rglob("*.cs")):
                if "obj" in path.parts or path.resolve() in OWNED or path.resolve() in LANDED_CONSUMERS:
                    continue
                for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    code = line.split("//", 1)[0]
                    if re.search(r"\bIBotThreatAnalysis\b", code):
                        offenders.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()}")

        self.assertEqual(
            [], offenders,
            "IBotThreatAnalysis consumers are the landed set in LANDED_CONSUMERS; "
            "any new consumer needs a deliberate review:\n" + "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()
