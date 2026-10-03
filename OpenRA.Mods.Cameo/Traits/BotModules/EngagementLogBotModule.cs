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
using System.Linq;
using System.Text;
using OpenRA.Mods.CA.Traits;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	[TraitLocation(SystemActors.Player)]
	[Desc("EL-0 (AI_ARCHITECTURE 12.30, DESIGN 19.13): RECORD-ONLY engagement log. Clusters this bot's combat events (own actors hit by an",
		"enemy via IBotRespondToAttack, enemies it damages via INotifyAppliedDamage) into engagements and writes one scored line per closed",
		"fight plus an army posture line every PostureIntervalTicks to cameo-ai-engagements.jsonl. It issues no orders, grants no",
		"conditions and keeps no state another module reads; its writer only appends at game over on the host, outside replays.")]
	public class EngagementLogBotModuleInfo : ConditionalTraitInfo
	{
		public override object Create(ActorInitializer init) { return new EngagementLogBotModule(init.Self, this); }
	}

	public class EngagementLogBotModule : ConditionalTrait<EngagementLogBotModuleInfo>, IBotTick, IBotRespondToAttack, INotifyAppliedDamage
	{
		/// <summary>The per-type facts the log needs, read once per actor type from the rules.</summary>
		sealed class UnitFlags
		{
			public int Value;
			public bool Building, Armed, Defence, Harvester, Mobile, Combat, BaseBuilding;
			public int RangeCells;
			public string Name;
			public BotUnitProfile Profile;
		}

		sealed class OwnUnit
		{
			public Actor Actor;
			public uint Id;
			public int X, Y;
			public UnitFlags F;
			public bool Artillery;
		}

		readonly struct ScanHit
		{
			public readonly uint Id;
			public readonly int X, Y;
			public readonly UnitFlags F;

			public ScanHit(uint id, int x, int y, UnitFlags f) { Id = id; X = x; Y = y; F = f; }
		}

		readonly OpenRA.Player player;
		readonly World world;
		readonly EngagementTracker tracker = new(EngagementConstants.RadiusCells, EngagementConstants.QuietTicks);
		readonly Dictionary<ActorInfo, UnitFlags> flagsCache = new();
		readonly List<OwnUnit> ownUnits = new();
		readonly Dictionary<uint, PositionRing> rings = new();
		readonly HashSet<uint> ringsSeen = new();
		readonly List<(int X, int Y)> ownBases = new();
		readonly Dictionary<uint, (int X, int Y)> enemyBases = new();
		readonly Dictionary<uint, (int X, int Y, int Tick)> buildingsUnderAttack = new();
		readonly Dictionary<int, List<(Actor Actor, int Value)>> truthActors = new();

		AiEngagementLogWriter sink;
		IBotUnitRoles roles;
		bool resolved;
		bool loggable;
		int nextSampleTick;
		int nextBaseRefreshTick;
		int nextEnemyBaseRefreshTick;
		int nextPostureTick = EngagementConstants.PostureIntervalTicks;
		int postureCount;

		public EngagementLogBotModule(Actor self, EngagementLogBotModuleInfo info)
			: base(info)
		{
			player = self.Owner;
			world = self.World;
		}

		bool Ready()
		{
			if (IsTraitDisabled)
				return false;

			if (!resolved)
			{
				resolved = true;
				loggable = player.IsBot && !player.NonCombatant && !player.PlayerReference.NonCombatant;
				sink = loggable ? world.WorldActor.TraitOrDefault<AiEngagementLogWriter>() : null;
				if (sink != null && sink.Active)
					sink.RegisterFlush(CloseAllAtMatchEnd);
			}

			return sink != null && sink.Active && player.WinState == WinState.Undefined;
		}

		// ── hooks ──────────────────────────────────────────────────────────────────────────────────────────────────

		void IBotRespondToAttack.RespondToAttack(IBot bot, Actor self, AttackInfo e)
		{
			if (!Ready() || e.Attacker == null || e.Attacker.Disposed || e.Damage == null || e.Damage.Value <= 0 || !self.IsInWorld)
				return;
			if (e.Attacker.Owner == null || e.Attacker.Owner.NonCombatant || player.RelationshipWith(e.Attacker.Owner) != PlayerRelationship.Enemy)
				return;

			var tick = world.WorldTick;
			var loc = self.Location;
			var state = Locate(tick, loc.X, loc.Y);
			var f = FlagsOf(self.Info);
			var dead = e.DamageState == DamageState.Dead;

			state.OwnHurtEvents++;
			if (state.FirstOwnHurtTick < 0)
				state.FirstOwnHurtTick = tick;

			NoteEnemyDefence(state, e.Attacker);

			if (f.Building)
			{
				buildingsUnderAttack[self.ActorID] = (loc.X, loc.Y, tick);
				TrackBuilding(state, self, true, f, e);
				if (dead)
					state.OwnBuildingsLost++;
				return;
			}

			if (!dead)
				return;

			state.OwnLostUnits++;
			state.OwnLostUnitValue += f.Value;
			var role = Roles()?.PrimaryRoleOf(f.Name) ?? "unclassified";
			state.LostByRole[role] = state.LostByRole.GetValueOrDefault(role) + f.Value;
			foreach (var d in state.Defences)
				if (EngagementGeometry.Dist2(loc.X, loc.Y, d.X, d.Y) <= (long)d.RangeCells * d.RangeCells)
				{
					state.IntoDefencesValue += f.Value;
					break;
				}
		}

		void INotifyAppliedDamage.AppliedDamage(Actor self, Actor damaged, AttackInfo e)
		{
			if (!Ready() || damaged == null || damaged.Disposed || !damaged.IsInWorld || e.Damage == null || e.Damage.Value <= 0)
				return;
			if (damaged.Owner == null || damaged.Owner.NonCombatant || player.RelationshipWith(damaged.Owner) != PlayerRelationship.Enemy)
				return;

			var tick = world.WorldTick;
			var loc = damaged.Location;
			var state = Locate(tick, loc.X, loc.Y);
			var f = FlagsOf(damaged.Info);
			var dead = e.DamageState == DamageState.Dead;

			state.OwnDealtEvents++;
			if (state.FirstOwnMobileDealtTick < 0 && e.Attacker != null && !e.Attacker.Disposed)
			{
				var af = FlagsOf(e.Attacker.Info);
				if (af.Mobile && af.Combat)
					state.FirstOwnMobileDealtTick = tick;
			}

			if (f.Defence)
				NoteEnemyDefence(state, damaged);

			if (f.Building)
			{
				TrackBuilding(state, damaged, false, f, e);
				if (f.BaseBuilding)
					enemyBases[damaged.ActorID] = (loc.X, loc.Y);
			}

			if (!dead)
				return;

			if (f.Defence)
			{
				state.EnemyKilledDefences++;
				state.EnemyKilledDefenceValue += f.Value;
			}
			else if (f.Building)
			{
				state.EnemyBuildingsKilled++;
				state.EnemyKilledBuildingValue += f.Value;
			}
			else if (f.Harvester)
			{
				state.EnemyHarvestersKilled++;
				state.EnemyKilledHarvesterValue += f.Value;
			}
			else
			{
				state.EnemyKilledUnits++;
				state.EnemyKilledUnitValue += f.Value;
			}
		}

		void IBotTick.BotTick(IBot bot)
		{
			if (!Ready())
				return;

			var tick = world.WorldTick;
			if (tick >= nextSampleTick)
			{
				nextSampleTick = tick + EngagementConstants.SampleIntervalTicks;
				SampleOwnUnits(tick);
				UpdateDirectEntry();
			}

			if (tracker.Open.Count > 0)
				CloseDue(tick);

			if (tick >= nextPostureTick)
			{
				nextPostureTick = tick + EngagementConstants.PostureIntervalTicks;
				WritePosture(tick);
			}
		}

		// ── segmentation ───────────────────────────────────────────────────────────────────────────────────────────

		EngagementState Locate(int tick, int x, int y)
		{
			var state = tracker.Locate(tick, x, y, out var created);
			if (created)
				Begin(state, tick, x, y);
			return state;
		}

		void Begin(EngagementState s, int tick, int x, int y)
		{
			// Approach vector: where the own units now in the fight stood ~150 ticks ago, from the ring buffers (no world query).
			foreach (var u in ownUnits)
			{
				if (!u.F.Mobile || !u.F.Combat || EngagementGeometry.Dist2(u.X, u.Y, x, y) > EngagementConstants.RadiusCells * EngagementConstants.RadiusCells)
					continue;

				if (rings.TryGetValue(u.Id, out var ring) && ring.TryOlder(tick, EngagementConstants.ApproachWindowTicks, out var ox, out var oy))
				{
					s.ApproachDx += u.X - ox;
					s.ApproachDy += u.Y - oy;
					s.ApproachUnits++;
				}
			}

			s.ArmyDistAtStartCells = ArmyCentroid(out var ax, out var ay, out _, out _) ? EngagementGeometry.DistCells(ax, ay, x, y) : -1;
			s.SeenStart = BuildSeen(tick, x, y, s);
			s.SeenStart.ArmyDistCells = s.ArmyDistAtStartCells;
			BeginTruth(s, tick, x, y);
		}

		void CloseDue(int tick)
		{
			foreach (var s in tracker.CollectQuiet(tick))
				Close(s, tick, "quiet");

			if (tracker.Open.Count == 0)
				return;

			List<EngagementState> gone = null;
			foreach (var s in tracker.Open)
			{
				if (tick - s.LastEventTick < EngagementConstants.SideGoneQuietTicks || tick < s.NextSideCheckTick)
					continue;

				s.NextSideCheckTick = tick + EngagementConstants.SideGoneQuietTicks;
				if (SideGone(s, tick))
				{
					gone ??= new List<EngagementState>();
					gone.Add(s);
				}
			}

			if (gone == null)
				return;

			foreach (var s in gone)
			{
				tracker.Close(s);
				Close(s, tick, "side_gone");
			}
		}

		void CloseAllAtMatchEnd(int tick)
		{
			foreach (var s in tracker.CloseAll())
				Close(s, tick, "match_end");
		}

		bool SideGone(EngagementState s, int tick)
		{
			var r2 = EngagementConstants.RadiusCells * EngagementConstants.RadiusCells;
			var cx = s.CentroidX;
			var cy = s.CentroidY;
			var ownLeft = false;
			foreach (var u in ownUnits)
				if (EngagementGeometry.Dist2(u.X, u.Y, cx, cy) <= r2) { ownLeft = true; break; }

			if (!ownLeft)
				return true;

			foreach (var h in SeenScan(cx, cy, EngagementConstants.RadiusCells))
				if (h.F.Armed)
					return false;

			return true;
		}

		// ── own state ──────────────────────────────────────────────────────────────────────────────────────────────

		// One pass over own armed actors every SampleIntervalTicks (not per tick): the unit/defence snapshot, the ring buffers.
		void SampleOwnUnits(int tick)
		{
			ownUnits.Clear();
			ringsSeen.Clear();
			foreach (var a in world.ActorsHavingTrait<AttackBase>(t => !t.IsTraitDisabled))
			{
				if (a.Owner != player || !a.IsInWorld || a.IsDead)
					continue;

				var f = FlagsOf(a.Info);
				var loc = a.Location;
				ownUnits.Add(new OwnUnit
				{
					Actor = a,
					Id = a.ActorID,
					X = loc.X,
					Y = loc.Y,
					F = f,
					Artillery = f.Mobile && f.Combat && Roles()?.PrimaryRoleOf(f.Name) == BotUnitRole.Artillery,
				});

				if (!f.Mobile || !f.Combat)
					continue;

				if (!rings.TryGetValue(a.ActorID, out var ring))
					rings[a.ActorID] = ring = new PositionRing();
				ring.Add(tick, loc.X, loc.Y);
				ringsSeen.Add(a.ActorID);
			}

			if (rings.Count != ringsSeen.Count)
				foreach (var id in rings.Keys.Where(id => !ringsSeen.Contains(id)).ToList())
					rings.Remove(id);

			if (tick >= nextBaseRefreshTick)
			{
				nextBaseRefreshTick = tick + EngagementConstants.PostureIntervalTicks;
				ownBases.Clear();
				foreach (var b in world.ActorsHavingTrait<BaseBuilding>())
					if (b.Owner == player && b.IsInWorld && !b.IsDead)
						ownBases.Add((b.Location.X, b.Location.Y));
			}

			if (tick >= nextEnemyBaseRefreshTick)
			{
				nextEnemyBaseRefreshTick = tick + EngagementConstants.EnemyBaseRefreshTicks;
				RefreshEnemyBases();
			}

			foreach (var id in buildingsUnderAttack.Where(kv => tick - kv.Value.Tick > EngagementConstants.UnderAttackWindowTicks).Select(kv => kv.Key).ToList())
				buildingsUnderAttack.Remove(id);
		}

		// Enemy construction yards as SEEN: the player's own frozen-actor layer (visible or remembered), never the live world.
		void RefreshEnemyBases()
		{
			var layer = player.FrozenActorLayer;
			if (layer == null)
				return;

			foreach (var fa in layer.FrozenActorsInRegion(world.Map.AllCells, false))
			{
				if (!fa.IsValid || fa.Owner == null || player.RelationshipWith(fa.Owner) != PlayerRelationship.Enemy)
					continue;

				if (FlagsOf(fa.Info).BaseBuilding)
				{
					var cell = world.Map.CellContaining(fa.CenterPosition);
					enemyBases[fa.ID] = (cell.X, cell.Y);
				}
			}
		}

		// A first own non-artillery direct-fire unit inside a seen defence's range: remember the defence value destroyed up to then.
		void UpdateDirectEntry()
		{
			foreach (var s in tracker.Open)
			{
				if (s.DefenceKilledBeforeDirectEntry >= 0 || s.Defences.Count == 0)
					continue;

				foreach (var u in ownUnits)
				{
					if (!u.F.Mobile || !u.F.Combat || u.Artillery)
						continue;

					var inRange = false;
					foreach (var d in s.Defences)
						if (EngagementGeometry.Dist2(u.X, u.Y, d.X, d.Y) <= (long)d.RangeCells * d.RangeCells) { inRange = true; break; }

					if (inRange)
					{
						s.DefenceKilledBeforeDirectEntry = s.EnemyKilledDefenceValue;
						break;
					}
				}
			}
		}

		bool ArmyCentroid(out int x, out int y, out int units, out int value)
		{
			long sx = 0, sy = 0;
			units = 0;
			value = 0;
			foreach (var u in ownUnits)
			{
				if (!u.F.Mobile || !u.F.Combat)
					continue;

				sx += u.X;
				sy += u.Y;
				units++;
				value += u.F.Value;
			}

			x = units > 0 ? (int)(sx / units) : 0;
			y = units > 0 ? (int)(sy / units) : 0;
			return units > 0;
		}

		// ── classification ─────────────────────────────────────────────────────────────────────────────────────────

		UnitFlags FlagsOf(ActorInfo info)
		{
			if (flagsCache.TryGetValue(info, out var f))
				return f;

			var profile = BotUnitProfiles.Get(world.Map.Rules, info);
			var building = info.HasTraitInfo<BuildingInfo>();
			var harvester = info.HasTraitInfo<HarvesterInfo>();
			var hasAttack = info.HasTraitInfo<AttackBaseInfo>();
			flagsCache[info] = f = new UnitFlags
			{
				Name = info.Name,
				Profile = profile,
				Value = info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 0,
				Building = building,
				Harvester = harvester,
				Armed = hasAttack && profile.Weapons.Length > 0,
				Defence = building && hasAttack && profile.Weapons.Length > 0,
				Combat = hasAttack && !building && !harvester,
				Mobile = !building && (info.HasTraitInfo<MobileInfo>() || info.HasTraitInfo<AircraftInfo>()),
				BaseBuilding = building && info.HasTraitInfo<BaseBuildingInfo>(),
				RangeCells = (profile.MaxRange.Length + 1023) / 1024,
			};
			return f;
		}

		IBotUnitRoles Roles() => roles ??= player.PlayerActor.TraitsImplementing<IBotUnitRoles>().FirstEnabledTraitOrDefault();

		void NoteEnemyDefence(EngagementState s, Actor defence)
		{
			if (defence == null || defence.Disposed || !defence.IsInWorld)
				return;

			var f = FlagsOf(defence.Info);
			if (!f.Defence || s.Defences.Any(d => d.Id == defence.ActorID))
				return;

			s.Defences.Add(new EngagementDefence(defence.ActorID, defence.Location.X, defence.Location.Y, f.RangeCells, f.Value));
		}

		static void TrackBuilding(EngagementState s, Actor building, bool own, UnitFlags f, AttackInfo e)
		{
			var health = building.TraitOrDefault<IHealth>();
			var max = Math.Max(1, health?.MaxHP ?? 1);
			var hp = e.DamageState == DamageState.Dead ? 0 : Math.Min(max, health?.HP ?? 0);
			if (!s.Buildings.TryGetValue(building.ActorID, out var b))
				s.Buildings[building.ActorID] = b = new EngagementBuilding
				{
					Own = own,
					Value = f.Value,
					MaxHp = max,
					HpStart = Math.Min(max, hp + e.Damage.Value),
				};

			b.HpEnd = hp;
			b.Dead |= e.DamageState == DamageState.Dead;
		}

		// ── what the bot SAW (fog-honest) ──────────────────────────────────────────────────────────────────────────

		// Enemy actors the bot can see (or remembers as frozen buildings) within `radiusCells`: its own sight, never the live world.
		List<ScanHit> SeenScan(int cx, int cy, int radiusCells)
		{
			var hits = new List<ScanHit>();
			var centre = world.Map.CenterOfCell(new CPos(cx, cy));
			var radius = WDist.FromCells(radiusCells);
			foreach (var a in world.FindActorsInCircle(centre, radius))
			{
				if (!a.IsInWorld || a.IsDead || a.Owner.NonCombatant || player.RelationshipWith(a.Owner) != PlayerRelationship.Enemy || !a.CanBeViewedByPlayer(player))
					continue;

				var f = FlagsOf(a.Info);
				if (!f.Armed)
					continue;

				hits.Add(new ScanHit(a.ActorID, a.Location.X, a.Location.Y, f));
				if (f.BaseBuilding)
					enemyBases[a.ActorID] = (a.Location.X, a.Location.Y);
			}

			var layer = player.FrozenActorLayer;
			if (layer != null)
			{
				foreach (var fa in layer.FrozenActorsInCircle(world, centre, radius, false))
				{
					if (fa.Visible || fa.Owner == null || player.RelationshipWith(fa.Owner) != PlayerRelationship.Enemy)
						continue;

					var f = FlagsOf(fa.Info);
					if (!f.Defence)
						continue;

					var cell = world.Map.CellContaining(fa.CenterPosition);
					hits.Add(new ScanHit(fa.ID, cell.X, cell.Y, f));
				}
			}

			return hits;
		}

		EngagementSeen BuildSeen(int tick, int cx, int cy, EngagementState s)
		{
			var seen = new EngagementSeen { Tick = tick };
			var r2 = EngagementConstants.RadiusCells * EngagementConstants.RadiusCells;
			var own = new Dictionary<UnitFlags, int>();
			foreach (var u in ownUnits)
			{
				if (EngagementGeometry.Dist2(u.X, u.Y, cx, cy) > r2)
					continue;

				if (u.F.Defence)
				{
					seen.OwnDefenceValue += u.F.Value;
					own[u.F] = own.GetValueOrDefault(u.F) + 1;
				}
				else if (u.F.Combat)
				{
					seen.OwnCommittedValue += u.F.Value;
					seen.OwnCommittedUnits++;
					if (u.Artillery)
						seen.OwnArtilleryValue += u.F.Value;
					own[u.F] = own.GetValueOrDefault(u.F) + 1;
				}
			}

			var enemy = new Dictionary<UnitFlags, int>();
			foreach (var h in SeenScan(cx, cy, EngagementConstants.RadiusCells))
			{
				if (h.F.Defence)
				{
					seen.EnemyDefenceValue += h.F.Value;
					seen.EnemyDefenceCount++;
					if (s != null && !s.Defences.Any(d => d.Id == h.Id))
						s.Defences.Add(new EngagementDefence(h.Id, h.X, h.Y, h.F.RangeCells, h.F.Value));
				}
				else if (h.F.Combat)
				{
					seen.EnemyUnitValue += h.F.Value;
					seen.EnemyUnits++;
					if (Roles()?.PrimaryRoleOf(h.F.Name) == BotUnitRole.Artillery)
						seen.EnemyArtilleryValue += h.F.Value;
				}
				else
					continue;

				enemy[h.F] = enemy.GetValueOrDefault(h.F) + 1;
			}

			var prediction = BotCombatPredictor.Predict(
				own.Select(kv => (kv.Key.Profile, kv.Value)).ToList(),
				enemy.Select(kv => (kv.Key.Profile, kv.Value)).ToList());
			seen.PredictedRatioMilli = (int)Math.Round(prediction.Ratio * 1000);
			seen.PredictedOwnSurvivingPermille = (int)Math.Round(prediction.OwnSurvivingFraction * 1000);
			seen.PredictedEnemySurvivingPermille = (int)Math.Round(prediction.EnemySurvivingFraction * 1000);
			return seen;
		}

		// ── what was REAL (offline scoring only) ───────────────────────────────────────────────────────────────────

		void BeginTruth(EngagementState s, int tick, int cx, int cy)
		{
			var actors = new List<(Actor, int)>();
			s.TruthStart = OmniscientTruthScan(tick, cx, cy, actors);
			truthActors[s.Id] = actors;
		}

		void EndTruth(EngagementState s, int tick)
		{
			var actors = new List<(Actor, int)>();
			s.TruthEnd = OmniscientTruthScan(tick, s.CentroidX, s.CentroidY, actors);
			if (s.TruthStart != null && truthActors.TryGetValue(s.Id, out var start))
			{
				foreach (var (actor, value) in start)
					if (actor.Disposed || actor.IsDead || !actor.IsInWorld)
						s.TruthEnd.EnemyLossValue += value;

				truthActors.Remove(s.Id);
			}
		}

		// DESIGN §19.13 "truth block, logging only": the ONE omniscient enumeration of this module. It reads the real enemy state in
		// the radius (no visibility filter) and only the writer's offline `truth` block uses the result; no decision, field or
		// condition ever reads it back. Called at engagement start and close only, never per tick.
		EngagementTruth OmniscientTruthScan(int tick, int cx, int cy, List<(Actor, int)> actors)
		{
			var truth = new EngagementTruth { Tick = tick };
			var centre = world.Map.CenterOfCell(new CPos(cx, cy));
			foreach (var a in world.FindActorsInCircle(centre, WDist.FromCells(EngagementConstants.RadiusCells)))
			{
				if (!a.IsInWorld || a.IsDead || a.Owner.NonCombatant || player.RelationshipWith(a.Owner) != PlayerRelationship.Enemy)
					continue;

				var f = FlagsOf(a.Info);
				if (f.Defence)
				{
					truth.EnemyDefenceValue += f.Value;
					truth.EnemyDefenceCount++;
				}
				else if (f.Combat)
				{
					truth.EnemyUnitValue += f.Value;
					truth.EnemyUnits++;
				}
				else
					continue;

				actors.Add((a, f.Value));
			}

			return truth;
		}

		// ── the records ────────────────────────────────────────────────────────────────────────────────────────────

		void Close(EngagementState s, int tick, string reason)
		{
			s.SeenEnd = BuildSeen(tick, s.CentroidX, s.CentroidY, null);
			s.SeenEnd.ArmyDistCells = ArmyCentroid(out var ax, out var ay, out _, out _) ? EngagementGeometry.DistCells(ax, ay, s.CentroidX, s.CentroidY) : -1;
			EndTruth(s, tick);

			var gameUid = world.LobbyInfo.GlobalSettings.GameUid;
			if (string.IsNullOrEmpty(gameUid))
				gameUid = sink.FallbackGameUid ?? "";

			var distOwn = NearestCells(ownBases, s.CentroidX, s.CentroidY);
			var distEnemy = NearestCells(enemyBases.Values.Select(v => (v.X, v.Y)), s.CentroidX, s.CentroidY);
			var kind = EngagementRecord.KindOf(distOwn, distEnemy);

			var header = new EngagementHeader
			{
				GameUid = gameUid,
				MapUid = world.Map.Uid,
				Player = player.InternalName,
				BotType = player.BotType ?? "",
				Faction = player.Faction.InternalName,
				Personality = PersonalityNow(),
				CloseReason = reason,
				EndTick = tick,
				DistOwnBase = distOwn,
				DistEnemyBase = distEnemy,
				OwnBaseX = ownBases.Count > 0 ? NearestOf(ownBases, s.CentroidX, s.CentroidY).X : -1,
				OwnBaseY = ownBases.Count > 0 ? NearestOf(ownBases, s.CentroidX, s.CentroidY).Y : -1,
				Kind = kind,
				DirectorPhase = player.PlayerActor.TraitsImplementing<IBotDirector>().FirstEnabledTraitOrDefault()?.DirectorPhase.ToString().ToLowerInvariant() ?? "",
				DirectorTension = player.PlayerActor.TraitsImplementing<IBotDirector>().FirstEnabledTraitOrDefault()?.DirectorTension ?? -1,
				Urgency = player.PlayerActor.TraitOrDefault<MasterAiBotModule>()?.Situation?.Urgency.ToString().ToLowerInvariant() ?? "",
			};

			sink.Append(EngagementRecord.BuildEngagement(header, s));
		}

		void WritePosture(int tick)
		{
			if (!ArmyCentroid(out var ax, out var ay, out var units, out var value))
				return;

			long dispersion = 0;
			var idle = 0;
			foreach (var u in ownUnits)
			{
				if (!u.F.Mobile || !u.F.Combat)
					continue;

				dispersion += EngagementGeometry.DistCells(u.X, u.Y, ax, ay);
				if (u.Actor.IsIdle)
					idle++;
			}

			var underAttack = -1;
			foreach (var b in buildingsUnderAttack.Values)
			{
				var d = EngagementGeometry.DistCells(ax, ay, b.X, b.Y);
				if (underAttack < 0 || d < underAttack)
					underAttack = d;
			}

			var enemyArmy = -1;
			foreach (var h in SeenScan(ax, ay, EngagementConstants.PostureSeenRadiusCells))
			{
				if (!h.F.Combat)
					continue;

				var d = EngagementGeometry.DistCells(ax, ay, h.X, h.Y);
				if (enemyArmy < 0 || d < enemyArmy)
					enemyArmy = d;
			}

			// AI_ARCHITECTURE 12.29: the staging point, read-only via IBotArmyStaging (null when no provider / no plan yet).
			string stagingCell = null;
			var stagingDist = -1;
			var staging = player.PlayerActor.TraitsImplementing<IBotArmyStaging>().FirstOrDefault();
			var stagingPoint = staging?.PrimaryStagingCell;
			if (stagingPoint != null)
			{
				stagingCell = stagingPoint.Value.X + "," + stagingPoint.Value.Y;
				stagingDist = EngagementGeometry.DistCells(ax, ay, stagingPoint.Value.X, stagingPoint.Value.Y);
			}

			var gameUid = world.LobbyInfo.GlobalSettings.GameUid;
			if (string.IsNullOrEmpty(gameUid))
				gameUid = sink.FallbackGameUid ?? "";

			sink.Append(EngagementRecord.BuildPosture(new EngagementHeader
			{
				GameUid = gameUid,
				MapUid = world.Map.Uid,
				Player = player.InternalName,
				BotType = player.BotType ?? "",
				Faction = player.Faction.InternalName,
				Personality = PersonalityNow(),
				EndTick = tick,
			}, postureCount++, ax, ay, units, value, NearestCells(ownBases, ax, ay), underAttack,
				(int)(dispersion / Math.Max(1, units)), enemyArmy, 1000 * idle / Math.Max(1, units), stagingCell, stagingDist));
		}

		string PersonalityNow() =>
			player.PlayerActor.TraitOrDefault<BotPersonalityController>()?.CurrentPersonality
				?? player.PlayerActor.TraitOrDefault<AiMatchLogRecorder>()?.CurrentPersonality ?? "";

		static (int X, int Y) NearestOf(IEnumerable<(int X, int Y)> cells, int x, int y)
		{
			var best = (X: -1, Y: -1);
			var bestDist = long.MaxValue;
			foreach (var c in cells)
			{
				var d = EngagementGeometry.Dist2(x, y, c.X, c.Y);
				if (d < bestDist)
				{
					bestDist = d;
					best = c;
				}
			}

			return best;
		}

		static int NearestCells(IEnumerable<(int X, int Y)> cells, int x, int y)
		{
			var n = NearestOf(cells, x, y);
			return n.X < 0 ? -1 : EngagementGeometry.DistCells(x, y, n.X, n.Y);
		}
	}

	/// <summary>The identity and context half of an engagement or posture line (everything not derived from the fight itself).</summary>
	public sealed class EngagementHeader
	{
		public string GameUid, MapUid, Player, BotType, Faction, Personality, CloseReason = "", Kind = "field", DirectorPhase = "", Urgency = "";
		public int EndTick, DistOwnBase = -1, DistEnemyBase = -1, DirectorTension = -1, OwnBaseX = -1, OwnBaseY = -1;
	}

	/// <summary>Builds the JSON lines (schema engagement/1). Pure, so the emitter's separators are unit-tested.</summary>
	public static class EngagementRecord
	{
		public const string Schema = "engagement/1";

		public static string KindOf(int distOwnBase, int distEnemyBase)
		{
			if (distOwnBase >= 0 && distOwnBase <= EngagementConstants.OwnBaseRadiusCells)
				return "defend";
			if (distEnemyBase >= 0 && distEnemyBase <= EngagementConstants.EnemyBaseRadiusCells)
				return "attack";
			return "field";
		}

		public static string BuildEngagement(EngagementHeader h, EngagementState s)
		{
			var ownBuildings = s.Buildings.Values.Where(b => b.Own).ToList();
			var enemyBuildings = s.Buildings.Values.Where(b => !b.Own).ToList();
			var ownBuildingLossMilli = EngagementScore.BuildingsLoss(ownBuildings.Select(b => (b.Value, EngagementScore.HpLost(b.HpStart, b.HpEnd, b.MaxHp), b.Dead)).ToList());
			var enemyBuildingLossMilli = EngagementScore.BuildingsLoss(enemyBuildings.Select(b => (b.Value, EngagementScore.HpLost(b.HpStart, b.HpEnd, b.MaxHp), b.Dead)).ToList());
			var ownBuildingValueLost = ownBuildings.Where(b => b.Dead).Sum(b => b.Value);

			var lost = s.OwnLostUnitValue + ownBuildingValueLost;
			var killed = s.EnemyKilledValue;
			var skirmish = lost + killed < EngagementConstants.MinValueTraded || s.Deaths < EngagementConstants.MinDeaths;

			var seen = s.SeenStart ?? new EngagementSeen();
			var ownStart = seen.OwnCommittedValue + seen.OwnDefenceValue;
			var enemyStart = seen.EnemyUnitValue + seen.EnemyDefenceValue;
			var trade = EngagementScore.Trade(killed, lost);
			var predicted = EngagementScore.PredictedTrade(ownStart, enemyStart, seen.PredictedOwnSurvivingPermille, seen.PredictedEnemySurvivingPermille);
			var vsPrediction = EngagementScore.VsPrediction(trade, predicted);
			var objective = EngagementScore.Objective(h.Kind, ownBuildingLossMilli, enemyBuildingLossMilli, ownBuildings.Count > 0, enemyBuildings.Count > 0);
			var total = EngagementScore.Total(trade, vsPrediction, objective);

			var defenceBefore = s.DefenceKilledBeforeDirectEntry >= 0 ? s.DefenceKilledBeforeDirectEntry : s.EnemyKilledDefenceValue;
			var suicide = (int)(1000L * s.IntoDefencesValue / Math.Max(1, s.EnemyKilledDefenceValue));
			var angle = -1;
			if (s.Defences.Count > 0 && h.OwnBaseX >= 0)
			{
				long dx = 0, dy = 0;
				foreach (var d in s.Defences) { dx += d.X; dy += d.Y; }
				dx /= s.Defences.Count;
				dy /= s.Defences.Count;
				angle = EngagementGeometry.AngleDegrees(s.ApproachDx, s.ApproachDy, dx - h.OwnBaseX, dy - h.OwnBaseY);
			}

			var b = new StringBuilder();
			AiMatchLogWriter.AppendObjectStart(b);
			AiMatchLogWriter.AppendString(b, "schema", Schema, true);
			AiMatchLogWriter.AppendString(b, "record", "engagement");
			AiMatchLogWriter.AppendString(b, "game_uid", h.GameUid);
			AiMatchLogWriter.AppendString(b, "record_id", h.GameUid + "|" + h.Player + "|" + s.Id);
			AiMatchLogWriter.AppendString(b, "map_uid", h.MapUid);
			AiMatchLogWriter.AppendString(b, "player", h.Player);
			AiMatchLogWriter.AppendString(b, "bot_type", h.BotType);
			AiMatchLogWriter.AppendString(b, "faction", h.Faction);
			AiMatchLogWriter.AppendString(b, "personality", h.Personality);
			AiMatchLogWriter.AppendNumber(b, "engagement_id", s.Id);
			AiMatchLogWriter.AppendNumber(b, "start_tick", s.StartTick);
			AiMatchLogWriter.AppendNumber(b, "end_tick", h.EndTick);
			AiMatchLogWriter.AppendNumber(b, "duration_ticks", Math.Max(0, h.EndTick - s.StartTick));
			AiMatchLogWriter.AppendString(b, "close_reason", h.CloseReason);
			AiMatchLogWriter.AppendString(b, "centroid", s.CentroidX + "," + s.CentroidY);
			AiMatchLogWriter.AppendString(b, "kind", h.Kind);
			AiMatchLogWriter.AppendBoolean(b, "skirmish", skirmish);

			AiMatchLogWriter.AppendObjectPropertyStart(b, "context");
			AiMatchLogWriter.AppendNumber(b, "dist_own_base", h.DistOwnBase, true);
			AiMatchLogWriter.AppendNumber(b, "dist_enemy_base", h.DistEnemyBase);
			AiMatchLogWriter.AppendString(b, "director_phase", h.DirectorPhase);
			AiMatchLogWriter.AppendNumber(b, "director_tension", h.DirectorTension);
			AiMatchLogWriter.AppendString(b, "urgency", h.Urgency);
			b.Append('}');

			AiMatchLogWriter.AppendObjectPropertyStart(b, "seen");
			AiMatchLogWriter.AppendString(b, "predicted_method", "lanchester_predictor", true);
			AppendSeen(b, "start", s.SeenStart);
			AppendSeen(b, "end", s.SeenEnd);
			b.Append('}');

			if (h.Kind == "defend")
			{
				AiMatchLogWriter.AppendObjectPropertyStart(b, "response");
				AiMatchLogWriter.AppendNumber(b, "first_own_hurt_tick", s.FirstOwnHurtTick, true);
				AiMatchLogWriter.AppendNumber(b, "first_own_mobile_dealt_tick", s.FirstOwnMobileDealtTick);
				AiMatchLogWriter.AppendNumber(b, "response_ticks", s.FirstOwnHurtTick >= 0 && s.FirstOwnMobileDealtTick >= 0
					? Math.Max(0, s.FirstOwnMobileDealtTick - s.FirstOwnHurtTick) : -1);
				AiMatchLogWriter.AppendNumber(b, "army_dist_at_start_cells", s.ArmyDistAtStartCells);
				b.Append('}');
			}

			AiMatchLogWriter.AppendObjectPropertyStart(b, "tactics");
			AiMatchLogWriter.AppendNumber(b, "approach_angle_deg", angle, true);
			AiMatchLogWriter.AppendNumber(b, "approach_units", s.ApproachUnits);
			AiMatchLogWriter.AppendBoolean(b, "artillery_first", defenceBefore > 0);
			AiMatchLogWriter.AppendNumber(b, "defence_killed_before_direct_entry", defenceBefore);
			AiMatchLogWriter.AppendNumber(b, "into_defences_value", s.IntoDefencesValue);
			AiMatchLogWriter.AppendNumber(b, "suicide_index_milli", suicide);
			AiMatchLogWriter.AppendNumber(b, "defence_points", s.Defences.Count);
			AiMatchLogWriter.AppendNumber(b, "own_hurt_events", s.OwnHurtEvents);
			AiMatchLogWriter.AppendNumber(b, "own_dealt_events", s.OwnDealtEvents);
			b.Append('}');

			AiMatchLogWriter.AppendObjectPropertyStart(b, "outcome");
			AiMatchLogWriter.AppendNumber(b, "own_lost_value", lost, true);
			AiMatchLogWriter.AppendNumber(b, "own_lost_unit_value", s.OwnLostUnitValue);
			AiMatchLogWriter.AppendNumber(b, "own_lost_units", s.OwnLostUnits);
			AiMatchLogWriter.AppendNumber(b, "own_lost_building_value", ownBuildingValueLost);
			AiMatchLogWriter.AppendNumber(b, "own_buildings_lost", s.OwnBuildingsLost);
			AiMatchLogWriter.AppendNumber(b, "enemy_killed_value", killed);
			AiMatchLogWriter.AppendNumber(b, "enemy_killed_unit_value", s.EnemyKilledUnitValue);
			AiMatchLogWriter.AppendNumber(b, "enemy_killed_units", s.EnemyKilledUnits);
			AiMatchLogWriter.AppendNumber(b, "enemy_killed_defence_value", s.EnemyKilledDefenceValue);
			AiMatchLogWriter.AppendNumber(b, "enemy_killed_defences", s.EnemyKilledDefences);
			AiMatchLogWriter.AppendNumber(b, "enemy_killed_building_value", s.EnemyKilledBuildingValue);
			AiMatchLogWriter.AppendNumber(b, "enemy_buildings_killed", s.EnemyBuildingsKilled);
			AiMatchLogWriter.AppendNumber(b, "enemy_killed_harvester_value", s.EnemyKilledHarvesterValue);
			AiMatchLogWriter.AppendNumber(b, "enemy_harvesters_killed", s.EnemyHarvestersKilled);
			AiMatchLogWriter.AppendObjectPropertyStart(b, "own_lost_by_role");
			var first = true;
			foreach (var kv in s.LostByRole)
			{
				AiMatchLogWriter.AppendNumber(b, kv.Key, kv.Value, first);
				first = false;
			}

			b.Append("}}");

			AiMatchLogWriter.AppendObjectPropertyStart(b, "truth");
			AppendTruth(b, "start", s.TruthStart, true);
			AppendTruth(b, "end", s.TruthEnd, false);
			AiMatchLogWriter.AppendNumber(b, "enemy_loss_value", s.TruthEnd?.EnemyLossValue ?? 0);
			b.Append('}');

			AiMatchLogWriter.AppendObjectPropertyStart(b, "score");
			AiMatchLogWriter.AppendNumber(b, "trade_milli", trade, true);
			AiMatchLogWriter.AppendNumber(b, "predicted_trade_milli", predicted);
			AiMatchLogWriter.AppendNumber(b, "vs_prediction_milli", vsPrediction);
			AiMatchLogWriter.AppendNumber(b, "own_building_loss_milli", ownBuildingLossMilli);
			AiMatchLogWriter.AppendNumber(b, "enemy_building_loss_milli", enemyBuildingLossMilli);
			AiMatchLogWriter.AppendNumber(b, "objective_milli", objective);
			AiMatchLogWriter.AppendNumber(b, "total_milli", total);
			b.Append("}}\n");
			return b.ToString();
		}

		static void AppendSeen(StringBuilder b, string name, EngagementSeen seen)
		{
			seen ??= new EngagementSeen();
			AiMatchLogWriter.AppendObjectPropertyStart(b, name);
			AiMatchLogWriter.AppendNumber(b, "tick", seen.Tick, true);
			AiMatchLogWriter.AppendNumber(b, "own_committed_value", seen.OwnCommittedValue);
			AiMatchLogWriter.AppendNumber(b, "own_committed_units", seen.OwnCommittedUnits);
			AiMatchLogWriter.AppendNumber(b, "own_defence_value", seen.OwnDefenceValue);
			AiMatchLogWriter.AppendNumber(b, "own_artillery_value", seen.OwnArtilleryValue);
			AiMatchLogWriter.AppendNumber(b, "enemy_unit_value", seen.EnemyUnitValue);
			AiMatchLogWriter.AppendNumber(b, "enemy_units", seen.EnemyUnits);
			AiMatchLogWriter.AppendNumber(b, "enemy_defence_value", seen.EnemyDefenceValue);
			AiMatchLogWriter.AppendNumber(b, "enemy_defence_count", seen.EnemyDefenceCount);
			AiMatchLogWriter.AppendNumber(b, "enemy_artillery_value", seen.EnemyArtilleryValue);
			AiMatchLogWriter.AppendNumber(b, "predicted_ratio_milli", seen.PredictedRatioMilli);
			AiMatchLogWriter.AppendNumber(b, "predicted_own_surviving_permille", seen.PredictedOwnSurvivingPermille);
			AiMatchLogWriter.AppendNumber(b, "predicted_enemy_surviving_permille", seen.PredictedEnemySurvivingPermille);
			AiMatchLogWriter.AppendNumber(b, "army_dist_cells", seen.ArmyDistCells);
			b.Append('}');
		}

		static void AppendTruth(StringBuilder b, string name, EngagementTruth truth, bool first)
		{
			truth ??= new EngagementTruth();
			AiMatchLogWriter.AppendObjectPropertyStart(b, name, first);
			AiMatchLogWriter.AppendNumber(b, "tick", truth.Tick, true);
			AiMatchLogWriter.AppendNumber(b, "enemy_unit_value", truth.EnemyUnitValue);
			AiMatchLogWriter.AppendNumber(b, "enemy_units", truth.EnemyUnits);
			AiMatchLogWriter.AppendNumber(b, "enemy_defence_value", truth.EnemyDefenceValue);
			AiMatchLogWriter.AppendNumber(b, "enemy_defence_count", truth.EnemyDefenceCount);
			b.Append('}');
		}

		public static string BuildPosture(EngagementHeader h, int index, int armyX, int armyY, int units, int value, int distOwnBase,
			int distUnderAttack, int dispersionCells, int distEnemyArmy, int idleShareMilli, string stagingCell, int stagingDist)
		{
			var b = new StringBuilder();
			AiMatchLogWriter.AppendObjectStart(b);
			AiMatchLogWriter.AppendString(b, "schema", Schema, true);
			AiMatchLogWriter.AppendString(b, "record", "posture");
			AiMatchLogWriter.AppendString(b, "game_uid", h.GameUid);
			AiMatchLogWriter.AppendString(b, "record_id", h.GameUid + "|" + h.Player + "|p" + index);
			AiMatchLogWriter.AppendString(b, "map_uid", h.MapUid);
			AiMatchLogWriter.AppendString(b, "player", h.Player);
			AiMatchLogWriter.AppendString(b, "bot_type", h.BotType);
			AiMatchLogWriter.AppendString(b, "faction", h.Faction);
			AiMatchLogWriter.AppendString(b, "personality", h.Personality);
			AiMatchLogWriter.AppendNumber(b, "tick", h.EndTick);
			AiMatchLogWriter.AppendString(b, "army_centroid", armyX + "," + armyY);
			AiMatchLogWriter.AppendNumber(b, "army_units", units);
			AiMatchLogWriter.AppendNumber(b, "army_value", value);
			AiMatchLogWriter.AppendNumber(b, "dist_own_base", distOwnBase);
			AiMatchLogWriter.AppendNumber(b, "dist_building_under_attack", distUnderAttack);
			AiMatchLogWriter.AppendNumber(b, "dispersion_cells", dispersionCells);
			AiMatchLogWriter.AppendNumber(b, "dist_seen_enemy_army", distEnemyArmy);
			AiMatchLogWriter.AppendNumber(b, "idle_share_milli", idleShareMilli);
			b.Append(",\"staging_cell\":").Append(stagingCell == null ? "null" : "\"" + stagingCell + "\"");
			b.Append(",\"army_to_staging_cells\":").Append(stagingCell == null ? "null" : stagingDist.ToString(System.Globalization.CultureInfo.InvariantCulture));
			b.Append("}\n");
			return b.ToString();
		}
	}
}
