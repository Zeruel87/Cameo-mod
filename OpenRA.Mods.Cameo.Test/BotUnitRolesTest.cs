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

using System.Collections.Generic;
using NUnit.Framework;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Cameo.Traits.BotModules;

namespace OpenRA.Mods.Cameo.Test
{
	[TestFixture]
	public class BotUnitRolesTest
	{
		// The bands a real ruleset resolves to are irrelevant here: the tests pin
		// the classifier's behaviour at fixed cuts (hp 60th, speed 75th, cost 50th).
		const int HpCut = 500;
		const int SpeedCut = 80;
		const int CostCut = 700;

		static BotUnitRoles.RoleFacts Ground(int hp = 0, int speed = 0, int cost = 0, int range = 0) =>
			new() { Mobile = true, Attacks = true, Health = hp, Speed = speed, Cost = cost, MaxRange = range };

		static HashSet<string> Classify(BotUnitRoles.RoleFacts f) =>
			BotUnitRoles.ClassifyRoles(f, HpCut, SpeedCut, CostCut);

		[Test]
		public void FrontlineNeedsHitpointsBelowArtilleryRange()
		{
			var tank = Ground(hp: 800, speed: 60, cost: 900, range: 5 * 1024);
			Assert.That(Classify(tank), Is.EquivalentTo(new[] { BotUnitRole.Frontline }));

			// A durable platform at artillery range is artillery, not frontline.
			var gun = Ground(hp: 800, speed: 30, cost: 1200, range: BotTargetTags.ArtilleryMinRange + 1);
			var roles = Classify(gun);
			Assert.That(roles, Does.Contain(BotUnitRole.Artillery));
			Assert.That(roles, Does.Not.Contain(BotUnitRole.Frontline));
		}

		[Test]
		public void FastFragileAttackersAreSkirmishers()
		{
			var buggy = Ground(hp: 100, speed: 110, cost: 400, range: 5 * 1024);
			Assert.That(Classify(buggy), Is.EquivalentTo(new[] { BotUnitRole.Skirmisher }));
		}

		[Test]
		public void AntiAirAndAntiSpecialisationComeFromWeapons()
		{
			var aa = Ground(hp: 800, speed: 60, cost: 900, range: 5 * 1024);
			aa.CanHitAir = true;
			Assert.That(Classify(aa), Is.EquivalentTo(new[] { BotUnitRole.Frontline, BotUnitRole.AntiAir }));

			// Explicit type targeting covers what a shared armour ladder cannot say:
			// declaring Infantry but not Vehicle is anti-infantry even at equal Versus.
			var flak = Ground(hp: 200, speed: 60, cost: 400, range: 5 * 1024);
			flak.HitsInfantryType = true;
			var flakRoles = Classify(flak);
			Assert.That(flakRoles, Does.Contain(BotUnitRole.AntiInfantry));
			Assert.That(flakRoles, Does.Not.Contain(BotUnitRole.AntiArmour));

			// InvalidTargets: Infantry marks an anti-armour weapon (100mm cannons).
			var cannon = Ground(hp: 800, speed: 60, cost: 900, range: 5 * 1024);
			cannon.CantHitInfantry = true;
			cannon.HitsVehicleType = true;
			Assert.That(Classify(cannon), Does.Contain(BotUnitRole.AntiArmour));

			// The pooled-Versus signal: a specialist lead over the other class.
			var at = Ground(hp: 800, speed: 60, cost: 900, range: 5 * 1024);
			at.VersusVehicle = 150;
			at.VersusInfantry = 30;
			Assert.That(Classify(at), Does.Contain(BotUnitRole.AntiArmour));
		}

		[Test]
		public void AircraftSplitIntoGunshipFighterBomber()
		{
			var heli = new BotUnitRoles.RoleFacts { Aircraft = true, Attacks = true, VTOL = true, CanHitGround = true };
			Assert.That(Classify(heli), Is.EquivalentTo(new[] { BotUnitRole.Gunship }));

			var jet = new BotUnitRoles.RoleFacts { Aircraft = true, Attacks = true, CanHitAir = true };
			Assert.That(Classify(jet), Is.EquivalentTo(new[] { BotUnitRole.Fighter }));

			var bomber = new BotUnitRoles.RoleFacts { Aircraft = true, Attacks = true, CanHitGround = true };
			Assert.That(Classify(bomber), Is.EquivalentTo(new[] { BotUnitRole.Bomber }));
		}

		[Test]
		public void SupportTransportScoutAndBuildingTags()
		{
			var medic = new BotUnitRoles.RoleFacts { Mobile = true, CanHeal = true };
			Assert.That(Classify(medic), Is.EquivalentTo(new[] { BotUnitRole.Support }));

			var apc = Ground(hp: 500, speed: 60, cost: 500);
			apc.Cargo = true;
			var apcRoles = Classify(apc);
			Assert.That(apcRoles, Does.Contain(BotUnitRole.Transport));
			Assert.That(apcRoles, Does.Contain(BotUnitRole.Frontline));

			var zeppelin = new BotUnitRoles.RoleFacts { Aircraft = true, Cargo = true };
			Assert.That(Classify(zeppelin), Is.EquivalentTo(new[] { BotUnitRole.AirTransport }));

			// Scout: fast, cheap, reveals shroud — needs all three.
			var scout = new BotUnitRoles.RoleFacts { Mobile = true, Reveals = true, Speed = 120, Cost = 200 };
			Assert.That(Classify(scout), Is.EquivalentTo(new[] { BotUnitRole.Scout }));
			var pricey = new BotUnitRoles.RoleFacts { Mobile = true, Reveals = true, Speed = 120, Cost = 5000 };
			Assert.That(Classify(pricey), Is.Empty);

			// Buildings carry the strike tags, never squad roles.
			var reactor = new BotUnitRoles.RoleFacts { Building = true, PowerAmount = 100 };
			Assert.That(Classify(reactor), Is.EquivalentTo(new[] { BotUnitRole.Power }));
			var turret = new BotUnitRoles.RoleFacts { Building = true, Attacks = true };
			Assert.That(Classify(turret), Is.EquivalentTo(new[] { BotUnitRole.Defence }));
			var lab = new BotUnitRoles.RoleFacts { Building = true, GivesTech = true };
			Assert.That(Classify(lab), Is.EquivalentTo(new[] { BotUnitRole.Tech }));
		}

		[Test]
		public void PrimaryRoleClaimsSpecialistsBeforeFrontline()
		{
			// A mobile AA tank (frontline + anti_air) counts as anti_air.
			Assert.That(BotUnitRoles.PrimaryRole(new HashSet<string> { BotUnitRole.Frontline, BotUnitRole.AntiAir }),
				Is.EqualTo(BotUnitRole.AntiAir));

			// A dual-role Orca (fighter + gunship) counts as fighter — the gunship
			// share cannot be relieved by picking it.
			Assert.That(BotUnitRoles.PrimaryRole(new HashSet<string> { BotUnitRole.Fighter, BotUnitRole.Gunship }),
				Is.EqualTo(BotUnitRole.Fighter));

			Assert.That(BotUnitRoles.PrimaryRole(new HashSet<string> { BotUnitRole.Frontline }),
				Is.EqualTo(BotUnitRole.Frontline));

			// Unroled or non-combat roles yield no primary.
			Assert.That(BotUnitRoles.PrimaryRole(new HashSet<string>()), Is.Null);
			Assert.That(BotUnitRoles.PrimaryRole(null), Is.Null);
			Assert.That(BotUnitRoles.PrimaryRole(new HashSet<string> { "harvester" }), Is.Null);
		}
	}
}
