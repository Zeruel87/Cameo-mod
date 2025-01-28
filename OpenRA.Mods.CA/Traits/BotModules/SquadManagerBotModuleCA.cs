#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Mods.CA.Traits.BotModules.Squads;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Activities;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.AS.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;
using static OpenRA.GameInformation;

namespace OpenRA.Mods.CA.Traits
{
	[Desc("Manages AI squads.")]
	public class SquadManagerBotModuleCAInfo : ConditionalTraitInfo
	{
		[Desc("Actor types that are valid for naval squads.")]
		public readonly HashSet<string> NavalUnitsTypes = new HashSet<string>();

		[Desc("Actor types that are excluded from ground attacks.")]
		public readonly HashSet<string> AirUnitsTypes = new HashSet<string>();

		[Desc("Actor types that should generally be excluded from attack squads.")]
		public readonly HashSet<string> ExcludeFromSquadsTypes = new HashSet<string>();

		[Desc("Actor types that are considered construction yards (base builders).")]
		public readonly HashSet<string> ConstructionYardTypes = new HashSet<string>();

		[Desc("Enemy building types around which to scan for targets for naval squads.")]
		public readonly HashSet<string> NavalProductionTypes = new HashSet<string>();

		/*
		[Desc("Own actor types that are prioritized when defending.")]
		public readonly HashSet<string> ProtectionTypes = new HashSet<string>();
		*/

		[Desc("Minimum number of units AI must have before attacking.")]
		public readonly int SquadSize = 8;

		[Desc("Random number of up to this many units is added to squad size when creating an attack squad.")]
		public readonly int SquadSizeRandomBonus = 30;

		[Desc("Maximum number of units AI can have idle.")]
		public readonly int MaxIdleUnits = 36;

		[ActorReference]
		[Desc("Units that form a guerrilla squad.")]
		public readonly HashSet<string> GuerrillaTypes = new();

		[Desc("Possibility of units in GuerrillaTypes to join Guerrilla.")]
		public readonly int JoinGuerrilla = 50;

		[Desc("Max number of units AI has in guerrilla squad")]
		public readonly int MaxGuerrillaSize = 10;

		[Desc("Delay (in ticks) between giving out orders to units.")]
		public readonly int AssignRolesInterval = 50;

		[Desc("Delay (in ticks) between issuing a protection order.")]
		public readonly int ProtectInterval = 50;

		[Desc("Delay (in ticks) between updating squads.")]
		public readonly int AttackForceInterval = 75;

		[Desc("Minimum delay (in ticks) between creating squads.")]
		public readonly int MinimumAttackForceDelay = 0;

		[Desc("Radius in cells around the base that should be scanned for units to be protected.")]
		public readonly int ProtectUnitScanRadius = 15;

		[Desc("Maximum distance in cells from center of the base when checking for MCV deployment location.",
			"Only applies if RestrictMCVDeploymentFallbackToBase is enabled and there's at least one construction yard.")]
		public readonly int MaxBaseRadius = 20;

		[Desc("Radius in cells that squads should scan for enemies around their position while idle.")]
		public readonly int IdleScanRadius = 10;

		[Desc("Radius in cells that squads should scan for danger around their position to make flee decisions.")]
		public readonly int DangerScanRadius = 10;

		[Desc("Radius in cells that attack squads should scan for enemies around their position when trying to attack.")]
		public readonly int AttackScanRadius = 12;

		[Desc("Radius in cells that protecting squads should scan for enemies around their position.")]
		public readonly int ProtectionScanRadius = 8;

		[Desc("Radius in cells that naval squads should scan for targets.")]
		public readonly int NavalScanRadius = 8;

		[Desc("Enemy target types to never target.")]
		public readonly BitSet<TargetableType> IgnoredEnemyTargetTypes = default(BitSet<TargetableType>);

		// CA additions
		[Desc("Minimum value of units AI must have before attacking.")]
		public readonly int SquadValue = 0;

		[Desc("Random number of up to this value units is added to squad valuee when creating an attack squad.")]
		public readonly int SquadValueRandomBonus = 0;

		[Desc("Percent change for ground squads to attack a random priority target rather than the closest enemy.")]
		public readonly int HighValueTargetPriority = 0;

		[Desc("Actor types to prioritise based on HighValueTargetPriority.")]
		public readonly HashSet<string> HighValueTargetTypes = new HashSet<string>();

		[Desc("Percent change for air squads (that can attack aircraft) to prioritise enemy aircraft.")]
		public readonly int AirToAirPriority = 85;

		[Desc("Limit target types for specific air unit squads.")]
		public readonly Dictionary<string, BitSet<TargetableType>> AirSquadTargetTypes = null;

		[Desc("Enemy building types around which to scan for targets for naval squads.")]
		public readonly HashSet<string> StaticAntiAirTypes = new HashSet<string>();

		[Desc("Air threats to prioritise above all others.")]
		public readonly HashSet<string> BigAirThreats = new HashSet<string>();

		[Desc("Locomotor used by pathfinding leader for squads")]
		public readonly HashSet<string> SuggestedGroundLeaderLocomotor = new();

		[Desc("Locomotor used by pathfinding leader for squads")]
		public readonly HashSet<string> SuggestedNavyLeaderLocomotor = new();

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			base.RulesetLoaded(rules, ai);

			if (DangerScanRadius <= 0)
				throw new YamlException("DangerScanRadius must be greater than zero.");
		}

		public override object Create(ActorInitializer init) { return new SquadManagerBotModuleCA(init.Self, this); }
	}

	public class SquadManagerBotModuleCA : ConditionalTrait<SquadManagerBotModuleCAInfo>, IBotEnabled, IBotTick, IBotRespondToAttack, IBotPositionsUpdated, IGameSaveTraitData, INotifyActorDisposing
	{
		public CPos GetRandomBaseCenter()
		{
			var randomConstructionYard = constructionYardBuildings.Actors.RandomOrDefault(World.LocalRandom);

			return randomConstructionYard?.Location ?? initialBaseCenter;
		}

		public readonly World World;
		public readonly Player Player;

		public readonly Predicate<Actor> unitCannotBeOrdered;
		readonly List<UnitWposWrapper> unitsHangingAroundTheBase = new();

		// Units that the bot already knows about. Any unit not on this list needs to be given a role.
		readonly List<Actor> activeUnits = new();

		public List<SquadCA> Squads = new();
		readonly ActorIndex.OwnerAndNamesAndTrait<BuildingInfo> constructionYardBuildings;

		IBot bot;
		IBotPositionsUpdated[] notifyPositionsUpdated;
		IBotNotifyIdleBaseUnits[] notifyIdleBaseUnits;
		IBotAircraftBuilder[] aircraftBuilders;

		CPos initialBaseCenter;
		Actor airStrikeTarget;
		public CPos[] airStrikeGrid;

		int rushTicks;
		int assignRolesTicks;
		int attackForceTicks;
		int protectionForceTicks;
		int minAttackForceDelayTicks;

		int protectOwnTicks;
		Actor protectOwnFrom;

		int desiredAttackForceValue;
		int desiredAttackForceSize;

		BotLimits botLimits;
		int initialAttackDelay;

		public SquadManagerBotModuleCA(Actor self, SquadManagerBotModuleCAInfo info)
			: base(info)
		{
			World = self.World;
			Player = self.Owner;
			
			unitCannotBeOrdered = a => a == null || a.Owner != Player || a.IsDead || !a.IsInWorld || a.CurrentActivity is Enter;
			constructionYardBuildings = new ActorIndex.OwnerAndNamesAndTrait<BuildingInfo>(World, info.ConstructionYardTypes, Player);
		}

		bool IsValidEnemyUnit(Actor a)
		{
			if (a == null || a.IsDead || Player.RelationshipWith(a.Owner) != PlayerRelationship.Enemy || a.Info.HasTraitInfo<HuskInfo>() || a.Info.HasTraitInfo<CarrierSlaveInfo>())
				return false;

			var targetTypes = a.GetEnabledTargetTypes();
			return !targetTypes.IsEmpty && !targetTypes.Overlaps(Info.IgnoredEnemyTargetTypes);
		}

		// Use for proactive targeting.
		public bool IsPreferredEnemyUnit(Actor a)
		{
			return IsValidEnemyUnit(a) && !a.Info.HasTraitInfo<AircraftInfo>();
		}

		public bool IsPreferredEnemyBuilding(Actor a)
		{
			return IsValidEnemyUnit(a) && a.Info.HasTraitInfo<BuildingInfo>();
		}

		public bool IsPreferredEnemyAircraft(Actor a)
		{
			return IsValidEnemyUnit(a) && a.Info.HasTraitInfo<AircraftInfo>() && a.Info.HasTraitInfo<AttackBaseInfo>();
		}

		public bool IsHighValueTarget(Actor a)
		{
			return IsValidEnemyUnit(a) && Info.HighValueTargetTypes.Contains(a.Info.Name);
		}

		public bool IsAirSquadTargetType(Actor a, SquadCA owner)
		{
			if (a == null || a.IsDead)
				return false;

			var airSquadUnitType = owner.Units[0].Actor.Info.Name;
			if (owner.SquadManager.Info.AirSquadTargetTypes.ContainsKey(airSquadUnitType))
			{
				var targetTypes = a.GetEnabledTargetTypes();

				if (targetTypes.IsEmpty || !targetTypes.Overlaps(owner.SquadManager.Info.AirSquadTargetTypes[airSquadUnitType]))
					return false;
			}

			return true;
		}

		public bool IsNotHiddenUnit(Actor a)
		{
			return a.CanBeViewedByPlayer(Player);
		}

		public bool IsValidAllyUnit(Actor a)
		{
			if (a == null || a.IsDead || Player.RelationshipWith(a.Owner) != PlayerRelationship.Ally || a.Info.HasTraitInfo<HuskInfo>() || a.Info.HasTraitInfo<CarrierSlaveInfo>())
				return false;

			return true;
		}

		public CPos[] AirstrikeGrid(Actor self)
		{
			var map = self.World.Map;
			var dangerRadius = Info.DangerScanRadius;

			var columnCount = (map.MapSize.X + dangerRadius - 1) / dangerRadius;
			var rowCount = (map.MapSize.Y + dangerRadius - 1) / dangerRadius;

			var checkIndices = Exts.MakeArray(columnCount * rowCount, i => new MPos((i % columnCount) * dangerRadius + dangerRadius / 2, (i / columnCount) * dangerRadius + dangerRadius / 2).ToCPos(map));

			return checkIndices;
		}

		protected override void Created(Actor self)
		{
			notifyPositionsUpdated = self.Owner.PlayerActor.TraitsImplementing<IBotPositionsUpdated>().ToArray();
			notifyIdleBaseUnits = self.Owner.PlayerActor.TraitsImplementing<IBotNotifyIdleBaseUnits>().ToArray();
			aircraftBuilders = self.Owner.PlayerActor.TraitsImplementing<IBotAircraftBuilder>().ToArray();
			airStrikeGrid = AirstrikeGrid(self);
		}

		protected override void TraitEnabled(Actor self)
		{
			botLimits = self.Owner.PlayerActor.TraitsImplementing<BotLimits>().FirstEnabledTraitOrDefault();

			if (botLimits != null)
				initialAttackDelay = botLimits.Info.InitialAttackDelay;

			// Avoid all AIs reevaluating assignments on the same tick, randomize their initial evaluation delay.
			assignRolesTicks = World.LocalRandom.Next(0, Info.AssignRolesInterval);
			attackForceTicks = World.LocalRandom.Next(0, Info.AttackForceInterval);
			protectionForceTicks = World.LocalRandom.Next(0, Info.ProtectInterval);
			minAttackForceDelayTicks = World.LocalRandom.Next(0, Info.MinimumAttackForceDelay) + initialAttackDelay;
		}

		void IBotEnabled.BotEnabled(IBot bot)
		{
			this.bot = bot;
		}

		void IBotTick.BotTick(IBot bot)
		{
			AssignRolesToIdleUnits(bot);
		}

		internal Actor FindClosestEnemy(Actor sourceActor)
		{
			var units = World.Actors.Where(IsPreferredEnemyUnit);
			return units.Where(IsNotHiddenUnit).ClosestToIgnoringPath(sourceActor.CenterPosition) ?? units.Where(IsPreferredEnemyBuilding).ClosestToIgnoringPath(sourceActor.CenterPosition) ?? units.ClosestToIgnoringPath(sourceActor.CenterPosition);
		}

		internal Actor FindHighValueTarget(WPos pos)
		{
			var units = World.Actors.Where(IsHighValueTarget);
			return units.RandomOrDefault(World.LocalRandom);
		}

		internal Actor FindClosestEnemy(Actor sourceActor, WDist radius)
		{
			return World.FindActorsInCircle(sourceActor.CenterPosition, radius).Where(a => IsPreferredEnemyUnit(a) && IsNotHiddenUnit(a)).ClosestToIgnoringPath(sourceActor);
		}

		void CleanSquads()
		{
			Squads.RemoveAll(s => !s.IsValid);
			foreach (var s in Squads)
			{
				s.Units.RemoveAll(u => unitCannotBeOrdered(u.Actor));

				if (s.Type == SquadCAType.Air)
				{
					s.NewUnits.RemoveWhere(unitCannotBeOrdered);
					s.RearmingUnits.RemoveWhere(unitCannotBeOrdered);
					s.WaitingUnits.RemoveWhere(unitCannotBeOrdered);
				}
			}
		}

		// HACK: Use of this function requires that there is one squad of this type.
		SquadCA GetSquadOfType(SquadCAType type)
		{
			return Squads.FirstOrDefault(s => s.Type == type);
		}

		IEnumerable<SquadCA> GetSquadsOfType(SquadCAType type)
		{
			return Squads.Where(s => s.Type == type);
		}

		SquadCA RegisterNewSquad(IBot bot, SquadCAType type, Actor target = null)
		{
			var ret = new SquadCA(bot, this, type, target);
			Squads.Add(ret);
			return ret;
		}

		public void DismissSquad(SquadCA squad)
		{
			unitsHangingAroundTheBase.AddRange(squad.Units);

			squad.Units.Clear();
		}

		void AssignRolesToIdleUnits(IBot bot)
		{
			CleanSquads();

			activeUnits.RemoveAll(unitCannotBeOrdered);
			unitsHangingAroundTheBase.RemoveAll(u => unitCannotBeOrdered(u.Actor));
			foreach (var n in notifyIdleBaseUnits)
				n.UpdatedIdleBaseUnits(unitsHangingAroundTheBase);

			if (--attackForceTicks <= 0)
			{
				attackForceTicks = Info.AttackForceInterval;
				foreach (var s in Squads)
				{
					s.Units.RemoveAll(u => unitCannotBeOrdered(u.Actor));
					s.Update();
				}
			}

			if (--assignRolesTicks <= 0)
			{
				assignRolesTicks = Info.AssignRolesInterval;
				unitsHangingAroundTheBase.RemoveAll(u => unitCannotBeOrdered(u.Actor));
				activeUnits.RemoveAll(unitCannotBeOrdered);
				FindNewUnits(bot);
			}

			if (--minAttackForceDelayTicks <= 0)
			{
				minAttackForceDelayTicks = Info.MinimumAttackForceDelay;
				unitsHangingAroundTheBase.RemoveAll(u => unitCannotBeOrdered(u.Actor));
				CreateAttackForce(bot);
			}

			if (--protectOwnTicks <= 0 && protectOwnFrom != null)
				ProtectOwn(protectOwnFrom);
		}

		public void SetAirStrikeTarget(Actor target)
		{
			airStrikeTarget = target;
		}

		public Actor PopAirStrikeTarget()
		{
			var target = airStrikeTarget;
			airStrikeTarget = null;
			return target;
		}

		void FindNewUnits(IBot bot)
		{
			var newUnits = World.ActorsHavingTrait<IPositionable>()
				.Where(a => a.Owner == Player &&
					!Info.ExcludeFromSquadsTypes.Contains(a.Info.Name) &&
					!activeUnits.Contains(a));

			var guerrillaForce = GetSquadOfType(SquadCAType.Assault);
			var guerrillaUpdate = guerrillaForce == null || (guerrillaForce.Units.Count <= Info.MaxGuerrillaSize && (World.LocalRandom.Next(100) >= Info.JoinGuerrilla));

			foreach (var a in newUnits)
			{
				if (Info.GuerrillaTypes.Contains(a.Info.Name) && guerrillaUpdate)
				{
					guerrillaForce ??= RegisterNewSquad(bot, SquadCAType.Assault);

					guerrillaForce.Units.Add(new UnitWposWrapper(a));
					AIUtils.BotDebug("AI ({0}): Added {1} to squad {2}", Player.ClientIndex, a, guerrillaForce.Type);
				}
				else if (Info.AirUnitsTypes.Contains(a.Info.Name))
				{
					var airSquads = Squads.Where(s => s.Type == SquadCAType.Air);
					var matchingAirSquadFound = false;

					foreach (var airSquad in airSquads)
					{
						if (airSquad.Units.Any(u => u.Actor.Info.Name == a.Info.Name))
						{
							airSquad.Units.Add(new UnitWposWrapper(a));
							airSquad.NewUnits.Add(a);
							matchingAirSquadFound = true;
							break;
						}
					}

					if (!matchingAirSquadFound)
					{
						var newAirSquad = RegisterNewSquad(bot, SquadCAType.Air);
						newAirSquad.Units.Add(new UnitWposWrapper(a));
						newAirSquad.NewUnits.Add(a);
					}
				}
				else if (Info.NavalUnitsTypes.Contains(a.Info.Name))
				{
					var navalSquads = Squads.Where(s => s.Type == SquadCAType.Naval);
					var matchingNavalSquadFound = false;

					foreach (var navalSquad in navalSquads)
					{
						if (navalSquad.Units.Any(u => u.Actor.Info.Name == a.Info.Name))
						{
							navalSquad.Units.Add(new UnitWposWrapper(a));
							matchingNavalSquadFound = true;
							break;
						}
					}

					if (!matchingNavalSquadFound)
					{
						var newNavalSquad = RegisterNewSquad(bot, SquadCAType.Naval);
						newNavalSquad.Units.Add(new UnitWposWrapper(a));
					}
				}
				else
					unitsHangingAroundTheBase.Add(new UnitWposWrapper(a));

				activeUnits.Add(a);
			}

			// Notifying here rather than inside the loop, should be fine and saves a bunch of notification calls
			foreach (var n in notifyIdleBaseUnits)
				n.UpdatedIdleBaseUnits(unitsHangingAroundTheBase);
		}

		void CreateAttackForce(IBot bot)
		{
			// Create an attack force when we have enough units around our base.
			// (don't bother leaving any behind for defense)
			var idleUnitsValue = 0;

			if (Info.SquadValue > 0)
			{
				foreach (var a in unitsHangingAroundTheBase)
				{
					var valued = a.Actor.Info.TraitInfoOrDefault<ValuedInfo>();
					if (valued != null)
						idleUnitsValue += valued.Cost;
				}
			}

			if (unitsHangingAroundTheBase.Count >= Info.MaxIdleUnits || (idleUnitsValue >= desiredAttackForceValue && unitsHangingAroundTheBase.Count >= desiredAttackForceSize))
			{
				var attackForce = RegisterNewSquad(bot, SquadCAType.Rush);

				attackForce.Units.AddRange(unitsHangingAroundTheBase);
				AIUtils.BotDebug("AI ({0}): Added {1} units to squad {2}", Player.ClientIndex, unitsHangingAroundTheBase.Count, attackForce.Type);
				unitsHangingAroundTheBase.Clear();
				foreach (var n in notifyIdleBaseUnits)
					n.UpdatedIdleBaseUnits(unitsHangingAroundTheBase);

				SetNextDesiredAttackForce();
			}
		}

		void SetNextDesiredAttackForce()
		{
			desiredAttackForceSize = Info.SquadSize + World.LocalRandom.Next(Info.SquadSizeRandomBonus);
			desiredAttackForceValue = 0;

			if (Info.SquadValue > 0)
				desiredAttackForceValue = Info.SquadValue + World.LocalRandom.Next(Info.SquadValueRandomBonus);
		}

		void ProtectOwn(Actor attacker)
		{
			protectOwnFrom = null;
			protectOwnTicks = Info.ProtectInterval;

			var protectSq = GetSquadOfType(SquadCAType.Protection);
			if (protectSq == null)
				protectSq = RegisterNewSquad(bot, SquadCAType.Protection, attacker);

			if (!protectSq.IsValid)
			{
				var ownUnits = World.FindActorsInCircle(World.Map.CenterOfCell(GetRandomBaseCenter()), WDist.FromCells(Info.ProtectUnitScanRadius))
					.Where(unit => unit.Owner == Player && !Info.ExcludeFromSquadsTypes.Contains(unit.Info.Name) && unit.Info.HasTraitInfo<AttackBaseInfo>() && !unit.Info.HasTraitInfo<BuildingInfo>()
						&& !unit.Info.HasTraitInfo<HarvesterInfo>() && !unit.Info.HasTraitInfo<AircraftInfo>());

				foreach (var a in ownUnits)
					protectSq.Units.Add(new UnitWposWrapper(a));
			}

			if (protectSq.IsValid && !protectSq.IsTargetValid)
				protectSq.TargetActor = attacker;
		}

		void IBotPositionsUpdated.UpdatedBaseCenter(CPos newLocation)
		{
			initialBaseCenter = newLocation;
		}

		void IBotPositionsUpdated.UpdatedDefenseCenter(CPos newLocation) { }

		void IBotRespondToAttack.RespondToAttack(IBot bot, Actor self, AttackInfo e)
		{
			if (!IsPreferredEnemyUnit(e.Attacker))
				return;

			// Protected priority assets, MCVs, harvesters and buildings
			// TODO: Use *CommonNames, instead of hard-coding trait(info)s.
			if (self.Info.HasTraitInfo<HarvesterInfo>() || self.Info.HasTraitInfo<BuildingInfo>() || self.Info.HasTraitInfo<BaseBuildingInfo>())
			{
				foreach (var n in notifyPositionsUpdated)
					n.UpdatedDefenseCenter(e.Attacker.Location);

				ProtectOwn(e.Attacker);
			}
		}

		List<MiniYamlNode> IGameSaveTraitData.IssueTraitData(Actor self)
		{
			if (IsTraitDisabled)
				return null;

			return new List<MiniYamlNode>()
			{
				new("Squads", "", Squads.ConvertAll(s => new MiniYamlNode("Squad", s.Serialize()))),
				new("InitialBaseCenter", FieldSaver.FormatValue(initialBaseCenter)),
				new("UnitsHangingAroundTheBase", FieldSaver.FormatValue(unitsHangingAroundTheBase
					.Where(u => !unitCannotBeOrdered(u.Actor))
					.Select(u => u.Actor.ActorID)
					.ToArray())),
				new("ActiveUnits", FieldSaver.FormatValue(activeUnits
					.Where(a => !unitCannotBeOrdered(a))
					.Select(a => a.ActorID)
					.ToArray())),
				new("RushTicks", FieldSaver.FormatValue(rushTicks)),
				new("AssignRolesTicks", FieldSaver.FormatValue(assignRolesTicks)),
				new("protectionForceTicks", FieldSaver.FormatValue(protectionForceTicks)),
				new("AttackForceTicks", FieldSaver.FormatValue(attackForceTicks)),
				new("MinAttackForceDelayTicks", FieldSaver.FormatValue(minAttackForceDelayTicks)),
			};
		}

		void IGameSaveTraitData.ResolveTraitData(Actor self, MiniYaml data)
		{
			if (self.World.IsReplay)
				return;

			var nodes = data.ToDictionary();

			if (nodes.TryGetValue("InitialBaseCenter", out var initialBaseCenterNode))
				initialBaseCenter = FieldLoader.GetValue<CPos>("InitialBaseCenter", initialBaseCenterNode.Value);

			if (nodes.TryGetValue("UnitsHangingAroundTheBase", out var unitsHangingAroundTheBaseNode))
			{
				unitsHangingAroundTheBase.Clear();
				foreach (var a in FieldLoader.GetValue<uint[]>("UnitsHangingAroundTheBase", unitsHangingAroundTheBaseNode.Value)
					.Select(a => self.World.GetActorById(a)).Where(a => a != null))
				{
					unitsHangingAroundTheBase.Add(new UnitWposWrapper(a));
				}
			}

			if (nodes.TryGetValue("ActiveUnits", out var activeUnitsNode))
			{
				activeUnits.Clear();
				activeUnits.AddRange(FieldLoader.GetValue<uint[]>("ActiveUnits", activeUnitsNode.Value)
					.Select(a => self.World.GetActorById(a)).Where(a => a != null));
			}

			if (nodes.TryGetValue("RushTicks", out var rushTicksNode))
				rushTicks = FieldLoader.GetValue<int>("RushTicks", rushTicksNode.Value);

			if (nodes.TryGetValue("AssignRolesTicks", out var assignRolesTicksNode))
				assignRolesTicks = FieldLoader.GetValue<int>("AssignRolesTicks", assignRolesTicksNode.Value);

			if (nodes.TryGetValue("protectionForceTicks", out var protectionForceTicksNode))
				protectionForceTicks = FieldLoader.GetValue<int>("protectionForceTicks", protectionForceTicksNode.Value);

			if (nodes.TryGetValue("AttackForceTicks", out var attackForceTicksNode))
				attackForceTicks = FieldLoader.GetValue<int>("AttackForceTicks", attackForceTicksNode.Value);

			if (nodes.TryGetValue("MinAttackForceDelayTicks", out var minAttackForceDelayTicksNode))
				minAttackForceDelayTicks = FieldLoader.GetValue<int>("MinAttackForceDelayTicks", minAttackForceDelayTicksNode.Value);

			if (nodes.TryGetValue("Squads", out var squadsNode))
			{
				Squads.Clear();
				foreach (var n in squadsNode.Nodes)
					Squads.Add(SquadCA.Deserialize(bot, this, n.Value));
			}
		}

		public bool CanBuildMoreOfAircraft(ActorInfo actorInfo)
		{
			foreach (var aircraftBuilder in aircraftBuilders)
			{
				if (!aircraftBuilder.IsTraitEnabled())
					continue;

				if (aircraftBuilder.CanBuildMoreOfAircraft(actorInfo))
					return true;
			}

			return false;
		}

		void INotifyActorDisposing.Disposing(Actor self)
		{
			constructionYardBuildings.Dispose();
		}
	}
}
