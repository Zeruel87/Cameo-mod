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

using System.Collections.Frozen;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Linq;
using NUnit.Framework;
using OpenRA.Mods.Cameo.Traits.BotModules;
using Candidate = OpenRA.Mods.Cameo.Traits.BotModules.BotRoleSetsInfo.RoleCandidate;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public class BotRoleSetsTest
	{
		static readonly Dictionary<string, string[]> None = [];

		static Candidate Actor(string name, string[] traits, string[] roles = null, bool buildable = true) =>
			new(name, traits.ToHashSet(), (roles ?? []).ToFrozenSet(), buildable);

		static Dictionary<string, HashSet<string>> Resolve(IEnumerable<Candidate> actors,
			Dictionary<string, string[]> has, Dictionary<string, string[]> not = null,
			Dictionary<string, string[]> exclude = null, bool onlyBuildable = true) =>
			BotRoleSetsInfo.ResolveMembers(actors, has, not ?? None, exclude ?? None, onlyBuildable);

		[Test]
		public void DerivationNeedsEveryHasTraitAndNoNotTrait()
		{
			var actors = new[]
			{
				Actor("harv", ["Harvester", "Mobile"]),
				Actor("slave", ["Harvester", "Infantry"]),
				Actor("tank", ["Mobile"]),
			};

			var m = Resolve(actors, new() { ["harvester"] = ["Harvester"] }, new() { ["harvester"] = ["Infantry"] });

			Assert.That(m["harvester"], Is.EquivalentTo(new[] { "harv" }));
		}

		[Test]
		public void ExcludeBlocksDerivationButNotAnExplicitRole()
		{
			var actors = new[]
			{
				Actor("a", ["Harvester"]),
				Actor("b", ["Harvester"], roles: ["harvester"]),
			};

			var m = Resolve(actors, new() { ["harvester"] = ["Harvester"] },
				exclude: new() { ["harvester"] = ["a", "b"] });

			Assert.That(m["harvester"], Is.EquivalentTo(new[] { "b" }));
		}

		[Test]
		public void UnbuildableActorsAreNotDerivedButExplicitRolesStillCount()
		{
			var actors = new[]
			{
				Actor("husk", ["Harvester"], buildable: false),
				Actor("scripted", ["Mobile"], roles: ["guerrilla"], buildable: false),
			};

			var m = Resolve(actors, new() { ["harvester"] = ["Harvester"] });

			Assert.That(m.ContainsKey("harvester"), Is.False);
			Assert.That(m["guerrilla"], Is.EquivalentTo(new[] { "scripted" }));

			var all = Resolve(actors, new() { ["harvester"] = ["Harvester"] }, onlyBuildable: false);
			Assert.That(all["harvester"], Is.EquivalentTo(new[] { "husk" }));
		}

		static Candidate WithField(string name, string[] traits, string key, params string[] values) =>
			new(name, traits.ToHashSet(), FrozenSet<string>.Empty, true,
				new Dictionary<string, IReadOnlySet<string>> { [key] = values.ToHashSet() });

		[Test]
		public void OnlyMatchesWhenEveryValueIsListedAndAnyWhenOneIs()
		{
			var only = BotRoleSetsInfo.FieldPredicate.Parse("Building.TerrainTypes only Water");
			var any = BotRoleSetsInfo.FieldPredicate.Parse("Building.TerrainTypes any water");

			Assert.That(only.Matches(new HashSet<string> { "Water" }), Is.True);
			Assert.That(only.Matches(new HashSet<string> { "Clear", "Water" }), Is.False, "land-and-water is not water-only");
			Assert.That(any.Matches(new HashSet<string> { "Clear", "Water" }), Is.True, "values compare case-insensitively");
			Assert.That(only.Matches(new HashSet<string>()), Is.False, "no values never matches");
			Assert.That(any.Matches(null), Is.False);
		}

		[Test]
		public void MalformedPredicatesAreRejected()
		{
			Assert.Throws<YamlException>(() => BotRoleSetsInfo.FieldPredicate.Parse("TerrainTypes only Water"));
			Assert.Throws<YamlException>(() => BotRoleSetsInfo.FieldPredicate.Parse("Building.TerrainTypes some Water"));
			Assert.Throws<YamlException>(() => BotRoleSetsInfo.FieldPredicate.Parse("Building.TerrainTypes only"));
		}

		[Test]
		public void DeriveNotFieldDropsWaterOnlyRefineriesButKeepsLandAndWaterOnes()
		{
			const string Key = "Building.TerrainTypes";
			var actors = new[]
			{
				WithField("ore_refinery", ["Refinery"], Key, "Clear", "Road"),
				WithField("oil_refinery", ["Refinery"], Key, "Water"),
				WithField("amphibious_refinery", ["Refinery"], Key, "Clear", "Water"),
			};

			var not = new Dictionary<string, BotRoleSetsInfo.FieldPredicate[]>
			{
				["refinery"] = [BotRoleSetsInfo.FieldPredicate.Parse("Building.TerrainTypes only Water")]
			};

			var m = BotRoleSetsInfo.ResolveMembers(actors, new Dictionary<string, string[]> { ["refinery"] = ["Refinery"] },
				None, None, true, null, not);

			Assert.That(m["refinery"], Is.EquivalentTo(new[] { "ore_refinery", "amphibious_refinery" }));
		}

		[Test]
		public void ARoleCanBeDerivedFromFieldPredicatesAlone()
		{
			const string Key = "Mobile.Locomotor";
			var actors = new[]
			{
				WithField("boat", ["Mobile"], Key, "naval"),
				WithField("tank", ["Mobile"], Key, "tracked"),
			};

			var has = new Dictionary<string, BotRoleSetsInfo.FieldPredicate[]>
			{
				["naval"] = [BotRoleSetsInfo.FieldPredicate.Parse("Mobile.Locomotor any naval|lcraft")]
			};

			var m = BotRoleSetsInfo.ResolveMembers(actors, None, None, None, true, has);

			Assert.That(m["naval"], Is.EquivalentTo(new[] { "boat" }));
		}

		static Candidate WithFields(string name, string[] traits, Dictionary<string, string[]> fields) =>
			WithFields(name, traits, fields, FrozenSet<string>.Empty);

		static Candidate WithFields(string name, string[] traits, Dictionary<string, string[]> fields, ISet<string> roles) =>
			new(name, traits.ToHashSet(), roles.ToFrozenSet(), true,
				fields.ToDictionary(kv => kv.Key, kv => (IReadOnlySet<string>)kv.Value.ToHashSet()));

		// CA-5 doctrine split (AI_ARCHITECTURE 12.4 + maintainer ruling 2026-09-30):
		// gunship = CanHover (loiters) + ground weapon — a dual-purpose helicopter
		// is a gunship even when it can also hit air. fighter = non-hovering with a
		// DEDICATED AA armament (Weapons.AirArmament any dedicated — ValidTargets
		// that may only hit air, like firehawk's missiles); a multirole gun that
		// also hits ground/water is merely `auxiliary` and stays out of fighter.
		// A hovering pure-A2A unit keeps its role through an explicit BotRoles tag.
		// bomber = non-hovering ground striker; auxiliary-AA bombers stay bombers
		// and their defensive guns do not drag them into fighter squads.
		// Transports/scouts derive into none of the three.
		[Test]
		public void AirDoctrineRolesSplitByWeaponTargetsAndHover()
		{
			const string VT = "Aircraft.CanHover";
			const string WT = "Weapons.ValidTargets";
			const string AA = "Weapons.AirArmament";
			var actors = new[]
			{
				// td_gdi_firehawk: dedicated AA missiles + bombs.
				WithFields("fighter_a", ["Aircraft", "AttackBase"], new() { [VT] = ["False"], [WT] = ["Air", "Ground"], [AA] = ["dedicated"] }),
				WithFields("gunship_a", ["Aircraft", "AttackBase"], new() { [VT] = ["True"], [WT] = ["Ground"], [AA] = new string[0] }),
				WithFields("multirole_heli", ["Aircraft", "AttackBase"], new() { [VT] = ["True"], [WT] = ["Air", "Ground"], [AA] = ["auxiliary"] }),
				WithFields("hover_a2a", ["Aircraft", "AttackBase"], new() { [VT] = ["True"], [WT] = ["Air"], [AA] = ["dedicated"] }, new HashSet<string> { "fighter" }),
				WithFields("bomber_a", ["Aircraft", "AttackBase"], new() { [VT] = ["False"], [WT] = ["Ground"], [AA] = new string[0] }),
				// japan_japanesebomber: bombs + auxiliary chaingun - defensive only.
				WithFields("auxaa_bomber", ["Aircraft", "AttackBase"], new() { [VT] = ["False"], [WT] = ["Ground", "Air"], [AA] = ["auxiliary"] }),
				WithFields("transport_a", ["Aircraft", "AttackBase"], new() { [VT] = ["True"], [WT] = new string[0], [AA] = new string[0] }),
				WithFields("scout_a", ["Aircraft"], new() { [VT] = ["False"], [WT] = new string[0], [AA] = new string[0] }),
			};

			var has = new Dictionary<string, string[]>
			{
				["fighter"] = ["Aircraft", "AttackBase"],
				["gunship"] = ["Aircraft", "AttackBase"],
				["bomber"] = ["Aircraft", "AttackBase"],
			};
			var hasF = new Dictionary<string, BotRoleSetsInfo.FieldPredicate[]>
			{
				["fighter"] = [BotRoleSetsInfo.FieldPredicate.Parse("Weapons.AirArmament any dedicated")],
				["gunship"] = [
					BotRoleSetsInfo.FieldPredicate.Parse("Aircraft.CanHover any True"),
					BotRoleSetsInfo.FieldPredicate.Parse("Weapons.ValidTargets any Ground")],
				["bomber"] = [BotRoleSetsInfo.FieldPredicate.Parse("Weapons.ValidTargets any Ground")],
			};
			var notF = new Dictionary<string, BotRoleSetsInfo.FieldPredicate[]>
			{
				["fighter"] = [BotRoleSetsInfo.FieldPredicate.Parse("Aircraft.CanHover any True")],
				["bomber"] = [
					BotRoleSetsInfo.FieldPredicate.Parse("Aircraft.CanHover any True"),
					BotRoleSetsInfo.FieldPredicate.Parse("Weapons.AirArmament any dedicated")],
			};

			var m = BotRoleSetsInfo.ResolveMembers(actors, has, None, None, true, hasF, notF);

			Assert.That(m["fighter"], Is.EquivalentTo(new[] { "fighter_a", "hover_a2a" }));
			Assert.That(m["gunship"], Is.EquivalentTo(new[] { "gunship_a", "multirole_heli" }));
			Assert.That(m["bomber"], Is.EquivalentTo(new[] { "bomber_a", "auxaa_bomber" }));
		}

		[Test]
		public void UnionKeepsTheFieldsOwnSetType()
		{
			var current = new[] { "a" };
			var added = new[] { "b" };

			Assert.That(BotRoleSetsInfo.Union(typeof(FrozenSet<string>), current, added), Is.InstanceOf<FrozenSet<string>>());
			Assert.That(BotRoleSetsInfo.Union(typeof(HashSet<string>), current, added), Is.InstanceOf<HashSet<string>>());
			Assert.That(BotRoleSetsInfo.Union(typeof(ImmutableHashSet<string>), current, added), Is.InstanceOf<ImmutableHashSet<string>>());
			Assert.That((IEnumerable<string>)BotRoleSetsInfo.Union(typeof(FrozenSet<string>), current, added),
				Is.EquivalentTo(new[] { "a", "b" }));
		}

		[Test]
		public void UnionRejectsAFieldThatIsNotAStringSet()
		{
			Assert.Throws<YamlException>(() => BotRoleSetsInfo.Union(typeof(List<string>), ["a"], ["b"]));
		}
	}
}
