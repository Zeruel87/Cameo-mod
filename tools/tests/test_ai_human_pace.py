"""HumanPaceBotModule is a producer-only IBotActionBudget implementation.

Human-likeness H1 (AI_SYNTHESIS.md §5): a shared action budget (sliding window
+ per-tick burst cap — the AlphaStar lesson needs both) and an attention budget
(at most N distinct decision points per tick; deferral is the stagger). The
module is deliberately NOT consulted by any order path yet — consumption is a
separate later lane, so any new IBotActionBudget reference outside the module
and its interface fails here.
"""
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/audit"))
from miniyaml import Ruleset

MODULE = ROOT / "OpenRA.Mods.Cameo/Traits/BotModules/HumanPaceBotModule.cs"
INTERFACE = ROOT / "OpenRA.Mods.CA/Traits/BotModules/IBotActionBudget.cs"
CODE_DIRS = [ROOT / "OpenRA.Mods.CA", ROOT / "OpenRA.Mods.Cameo"]
OWNED = {MODULE.resolve(), INTERFACE.resolve()}

# The consumption lane landed with INC-1/2/3 (#720): squad micro spends budget
# and ModularBot owns the pump. Any FURTHER consumer must be added deliberately.
LANDED_CONSUMERS = {
    (ROOT / "OpenRA.Mods.CA/Traits/BotModules/SquadManagerBotModuleCA.cs").resolve(),
    (ROOT / "OpenRA.Mods.Cameo/Traits/ModularBot.cs").resolve(),
}


class HumanPaceContractTests(unittest.TestCase):
    def test_module_is_registered_on_the_player_actor(self):
        rules = Ruleset(ROOT)
        player = rules.resolve("Player")
        self.assertIsNotNone(player, "ai.yaml Player actor missing")
        node = player.child("HumanPaceBotModule")
        self.assertIsNotNone(node, "HumanPaceBotModule is not registered on the Player actor")
        self.assertEqual("genericbot", node.child("RequiresCondition").value)

    def test_module_is_a_player_trait_not_a_world_trait(self):
        # ai.yaml defines BOTH actors; appending at file end lands under World.
        rules = Ruleset(ROOT)
        self.assertIsNone(
            rules.resolve("World").child("HumanPaceBotModule"),
            "HumanPaceBotModule is TraitLocation(Player) — it must not be on World")

    def test_module_implements_the_budget(self):
        source = MODULE.read_text(encoding="utf-8")
        decl = re.search(r"class HumanPaceBotModule\s*:\s*([^\n]+)", source).group(1)
        self.assertIn("IBotActionBudget", decl, "HumanPaceBotModule does not implement IBotActionBudget")

        # H1 needs all three mechanisms, not one: sustained window, burst cap,
        # attention slots.
        for member in ("TryConsumeActions", "TryConsumeAttention", "ActionsPerWindow",
                       "MaxActionsPerTick", "AttentionSlotsPerTick"):
            self.assertIn(member, source, f"missing H1 machinery: {member}")

        # A disabled limiter must not block — absence degrades, never breaks.
        self.assertIn("IsTraitDisabled", source)

    def test_producer_only_no_consumer_references_the_interface(self):
        offenders = []
        for directory in CODE_DIRS:
            for path in sorted(directory.rglob("*.cs")):
                if "obj" in path.parts or path.resolve() in OWNED or path.resolve() in LANDED_CONSUMERS:
                    continue
                for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    code = line.split("//", 1)[0]
                    if re.search(r"\bIBotActionBudget\b", code):
                        offenders.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()}")

        self.assertEqual(
            [], offenders,
            "IBotActionBudget consumers are the landed set in LANDED_CONSUMERS; "
            "any new consumer needs a deliberate review:\n" + "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()
