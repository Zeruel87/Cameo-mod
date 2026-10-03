#region Copyright & License Information
/*
 * Copyright (c) The OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 */
#endregion

using NUnit.Framework;
using OpenRA.Mods.Cameo.Traits.BotModules;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	// CN3: the bridge-repair port keeps the donor's gates as pure helpers — a hut must be damaged at
	// least the configured minimum, not already under repair, and (when the switch is on) visible.
	[TestFixture]
	public sealed class BridgeRepairBotModuleTest
	{
		const DamageState Minimum = DamageState.Light;

		[Test]
		public void AHutBelowTheMinimumDamageIsNotATarget()
		{
			Assert.That(BridgeRepairBotModule.IsEligibleHut(DamageState.Undamaged, false, true, true, Minimum), Is.False);
			Assert.That(BridgeRepairBotModule.IsEligibleHut(DamageState.Light, false, true, true, Minimum), Is.True);
			Assert.That(BridgeRepairBotModule.IsEligibleHut(DamageState.Dead, false, true, true, Minimum), Is.True,
				"a destroyed bridge is exactly what the repairer is for (BridgeHut's Dead state)");
		}

		[Test]
		public void AHutAlreadyUnderRepairIsSkipped()
		{
			Assert.That(BridgeRepairBotModule.IsEligibleHut(DamageState.Heavy, true, true, true, Minimum), Is.False);
		}

		[Test]
		public void TheVisibilityGateAppliesOnlyWhenSwitchedOn()
		{
			Assert.That(BridgeRepairBotModule.IsEligibleHut(DamageState.Heavy, false, false, true, Minimum), Is.False,
				"an unseen hut is not a target while CheckRepairTargetsForVisibility holds");
			Assert.That(BridgeRepairBotModule.IsEligibleHut(DamageState.Heavy, false, false, false, Minimum), Is.True,
				"with the check off the same hut is eligible");
		}

		// Damaged huts justify a repairer up to one per hut (MaximumRepairers caps it); the owned-plus-
		// queued count comes off the top, so a bot already at its cap requests nothing.
		[Test]
		public void DemandScalesWithDamagedTargets()
		{
			Assert.That(BridgeRepairBotModule.DesiredRepairerCount(1, 0, 2), Is.EqualTo(1),
				"one damaged hut justifies one repairer");
			Assert.That(BridgeRepairBotModule.DesiredRepairerCount(3, 0, 2), Is.EqualTo(2),
				"several huts want up to the cap");
			Assert.That(BridgeRepairBotModule.DesiredRepairerCount(3, 1, 2), Is.EqualTo(1),
				"one already owned or queued counts against the cap");
		}

		[Test]
		public void DemandStopsAtTheCapAndWithoutTargets()
		{
			Assert.That(BridgeRepairBotModule.DesiredRepairerCount(3, 2, 2), Is.EqualTo(0),
				"at the cap nothing is requested");
			Assert.That(BridgeRepairBotModule.DesiredRepairerCount(0, 0, 2), Is.EqualTo(0),
				"no damaged huts means no demand");
		}

		[Test]
		public void DemandIsDefensiveAgainstBadConfigAndNegativeCounts()
		{
			Assert.That(BridgeRepairBotModule.DesiredRepairerCount(3, 0, 0), Is.EqualTo(0),
				"a zero MaximumRepairers disables production");
			Assert.That(BridgeRepairBotModule.DesiredRepairerCount(3, 0, -1), Is.EqualTo(0));
			Assert.That(BridgeRepairBotModule.DesiredRepairerCount(2, 5, 2), Is.EqualTo(0),
				"more repairers than the cap never goes negative");
		}
	}
}
