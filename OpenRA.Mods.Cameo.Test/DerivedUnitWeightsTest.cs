#region Copyright & License Information
/*
 * Copyright (c) The OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;
using NUnit.Framework;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Cameo.Traits.BotModules;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public class DerivedUnitWeightsTest
	{
		// Minimal IBotUnitRoles: a unit counts toward its stored roles through the real
		// PrimaryRole precedence, exactly like the shipping BotUnitRoles provider.
		sealed class FakeRoles : IBotUnitRoles
		{
			readonly Dictionary<string, HashSet<string>> actorRoles = new(StringComparer.Ordinal);

			public FakeRoles(params (string Actor, string Role)[] entries)
			{
				var members = new Dictionary<string, HashSet<string>>(StringComparer.Ordinal);
				foreach (var (actor, role) in entries)
				{
					if (!actorRoles.TryGetValue(actor, out var set))
						actorRoles[actor] = set = new HashSet<string>(StringComparer.Ordinal);
					set.Add(role);

					if (!members.TryGetValue(role, out var m))
						members[role] = m = new HashSet<string>(StringComparer.Ordinal);
					m.Add(actor);
				}

				RoleMembers = members;
			}

			public IReadOnlyDictionary<string, HashSet<string>> RoleMembers { get; }
			public IReadOnlyDictionary<string, HashSet<string>> ActorRoles => actorRoles;
			public string PrimaryRoleOf(string actorName) =>
				actorRoles.TryGetValue(actorName, out var roles) ? BotUnitRoles.PrimaryRole(roles) : null;
		}

		static BotUnitProfile Profile(params BotWeaponProfile[] weapons) =>
			new("unit", 0, 0, null, 0, false, false,
				new BitSet<TargetableType>(), weapons);

		static BotWeaponProfile Weapon(double damagePerTick, Dictionary<string, int> versus) =>
			new(damagePerTick, new WDist(1024), new BitSet<TargetableType>(), new BitSet<TargetableType>(), versus);

		[Test]
		public void RoleShareSplitsByRelativeStrength()
		{
			// frontline 40: tank (10) vs heavy (30) split the share 1:3 around mean 20.
			var yaml = new Dictionary<string, int> { { "tank", 1 }, { "heavy", 1 }, { "scout", 1 } };
			var mix = new Dictionary<string, int> { { BotUnitRole.Frontline, 40 } };
			var roles = new FakeRoles(("tank", BotUnitRole.Frontline), ("heavy", BotUnitRole.Frontline), ("scout", BotUnitRole.Scout));
			var strength = new Dictionary<string, double> { { "tank", 10 }, { "heavy", 30 }, { "scout", 8 } };

			var table = DerivedUnitWeights.Derive(yaml, mix, 5, roles, n => strength[n]);

			Assert.That(table["tank"], Is.EqualTo(20), "40 x 10/20");
			Assert.That(table["heavy"], Is.EqualTo(60), "40 x 30/20");

			// Scout is unnamed in the mix: RoleMixRoleFloorPct 5, alone in its role -> 5 x 8/8.
			Assert.That(table["scout"], Is.EqualTo(5));
		}

		[Test]
		public void UnroledUnitsKeepTheirYamlWeightVerbatim()
		{
			// The yaml rows stay the membership gate AND the override channel: units the
			// provider cannot place in a combat role keep their hand-written share.
			var yaml = new Dictionary<string, int> { { "tank", 1 }, { "harvesterish", 7 } };
			var mix = new Dictionary<string, int> { { BotUnitRole.Frontline, 30 } };
			var roles = new FakeRoles(("tank", BotUnitRole.Frontline));

			var table = DerivedUnitWeights.Derive(yaml, mix, 5, roles, _ => 4.0);

			Assert.That(table["tank"], Is.EqualTo(30), "sole frontline member gets the whole share");
			Assert.That(table["harvesterish"], Is.EqualTo(7), "unroled row untouched");
			Assert.That(table.Keys, Is.EquivalentTo(yaml.Keys), "same key set: gate preserved");
		}

		[Test]
		public void DerivedWeightNeverDropsBelowOne()
		{
			// A weak member of a floor-share role rounds to 0 -> the max(1, ...) floor binds.
			var yaml = new Dictionary<string, int> { { "weak", 3 }, { "strong", 3 } };
			var mix = new Dictionary<string, int> { { BotUnitRole.Skirmisher, 1 } };
			var roles = new FakeRoles(("weak", BotUnitRole.Skirmisher), ("strong", BotUnitRole.Skirmisher));
			var strength = new Dictionary<string, double> { { "weak", 1 }, { "strong", 99 } };

			var table = DerivedUnitWeights.Derive(yaml, mix, 5, roles, n => strength[n]);

			Assert.That(table["weak"], Is.EqualTo(1));
			Assert.That(table["strong"], Is.EqualTo(2), "1 x 99/50 = 1.98 rounds to 2");
		}

		[Test]
		public void SelectIsByteIdenticalWhenOff()
		{
			// Flag off returns the yaml dictionary itself — the pre-derivation path.
			var yaml = new Dictionary<string, int> { { "tank", 1 } };
			var mix = new Dictionary<string, int> { { BotUnitRole.Frontline, 40 } };
			var roles = new FakeRoles(("tank", BotUnitRole.Frontline));

			var table = new DerivedUnitWeights().Select(false, null, yaml, mix, 5, roles, _ => 9.0);

			Assert.That(table, Is.SameAs(yaml));
		}

		[Test]
		public void SelectFallsBackToYamlWithoutMixOrProvider()
		{
			var yaml = new Dictionary<string, int> { { "tank", 1 } };
			var mix = new Dictionary<string, int> { { BotUnitRole.Frontline, 40 } };
			var roles = new FakeRoles(("tank", BotUnitRole.Frontline));
			var weights = new DerivedUnitWeights();

			Assert.That(weights.Select(true, null, yaml, null, 5, roles, _ => 9.0), Is.SameAs(yaml), "no RoleMix");
			Assert.That(weights.Select(true, null, yaml, new Dictionary<string, int>(), 5, roles, _ => 9.0), Is.SameAs(yaml), "empty RoleMix");
			Assert.That(weights.Select(true, null, yaml, mix, 5, null, _ => 9.0), Is.SameAs(yaml), "no provider");
		}

		[Test]
		public void CompositionWinsOverDerived()
		{
			var yaml = new Dictionary<string, int> { { "tank", 1 } };
			var composition = new Dictionary<string, int> { { "tank", 9 } };
			var mix = new Dictionary<string, int> { { BotUnitRole.Frontline, 40 } };
			var roles = new FakeRoles(("tank", BotUnitRole.Frontline));
			var weights = new DerivedUnitWeights();

			Assert.That(weights.Select(true, composition, yaml, mix, 5, roles, _ => 9.0), Is.SameAs(composition));
			Assert.That(weights.Select(false, composition, yaml, mix, 5, roles, _ => 9.0), Is.SameAs(composition),
				"a composition wins flag-off too — the pre-derivation behaviour");
		}

		[Test]
		public void SelectCachesOnTheMixReference()
		{
			var yaml = new Dictionary<string, int> { { "tank", 1 } };
			var mixA = new Dictionary<string, int> { { BotUnitRole.Frontline, 40 } };
			var mixB = new Dictionary<string, int> { { BotUnitRole.Frontline, 80 } };
			var roles = new FakeRoles(("tank", BotUnitRole.Frontline));
			var weights = new DerivedUnitWeights();

			var first = weights.Select(true, null, yaml, mixA, 5, roles, _ => 9.0);
			Assert.That(weights.Select(true, null, yaml, mixA, 5, roles, _ => 9999.0), Is.SameAs(first),
				"same mix dictionary serves the cached table");

			// A personality switch swaps the manager — hence the RoleMix reference — and rebuilds.
			var second = weights.Select(true, null, yaml, mixB, 5, roles, _ => 9.0);
			Assert.That(second, Is.Not.SameAs(first));
			Assert.That(second["tank"], Is.EqualTo(80));
		}

		[Test]
		public void StrengthIsBestVersusWeightedDamage()
		{
			// mean(Versus 50,150) = 100 -> 2.0 x 100/100 = 2; mean(Versus 200) -> 9 x 2 = 18 wins.
			var profile = Profile(
				Weapon(2.0, new Dictionary<string, int> { { "a", 50 }, { "b", 150 } }),
				Weapon(9.0, new Dictionary<string, int> { { "a", 200 } }));
			Assert.That(DerivedUnitWeights.Strength(profile), Is.EqualTo(18.0));

			// No Versus overrides reads 100 — the DamageWarhead default.
			Assert.That(DerivedUnitWeights.Strength(Profile(Weapon(3.0, new Dictionary<string, int>()))), Is.EqualTo(3.0));
		}

		[Test]
		public void StrengthFloorsAtOne()
		{
			Assert.That(DerivedUnitWeights.Strength(Profile()), Is.EqualTo(1.0), "weaponless");
			Assert.That(DerivedUnitWeights.Strength(null), Is.EqualTo(1.0), "missing profile");
			Assert.That(DerivedUnitWeights.Strength(Profile(Weapon(0.2, new Dictionary<string, int> { { "a", 50 } }))),
				Is.EqualTo(1.0), "0.2 x 0.5 = 0.1 floors to 1");
		}
	}
}
