#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

using System.Collections.Generic;
using System.Linq;
using OpenRA.Mods.Common.Traits;
using OpenRA.Support;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Traits.BotModules.Squads
{
	public enum SquadCAType { Guerrilla, Air, Rush, Protection, Naval, Artillery, Support, Harass, FireSupport, Fighter, Gunship, Bomber, Stealth }

	public class SquadCA
	{
		public List<UnitWposWrapper> Units = new();

		// lists used for air squads to determine what members should be doing
		public HashSet<Actor> NewUnits = new HashSet<Actor>();
		public HashSet<Actor> WaitingUnits = new HashSet<Actor>();
		public HashSet<Actor> RearmingUnits = new HashSet<Actor>();

		public SquadCAType Type;

		internal IBot Bot;
		internal World World;
		internal SquadManagerBotModuleCA SquadManager;
		internal MersenneTwister Random;

		internal Target Target;
		internal StateMachineCA FuzzyStateMachine;

		// 6f: artillery squads attach to an assault squad and bombard what it can
		// see. Runtime-only — not serialized; the state reattaches after load.
		internal SquadCA Parent;

		// 6g (CN A3): rules-derived BotTargetTags this squad prefers when picking
		// targets (e.g. air raiders prefer artillery). Empty = no preference.
		internal HashSet<string> PriorityTags = [];

		// Objective-shape deploy cooldown (12.7a, merged assault fan): the target cell and tick of this
		// squad's last objective deployment arm/commit/abort, so the squad is not looped back onto the
		// prongs forever. Per squad (no provider needed - the objective shape is gated by
		// FormationMovement); it dies with the squad.
		internal CPos DeployCooldownCell;
		internal int DeployCooldownTick = int.MinValue / 2;

		// internal CPos BaseLocation;

		public SquadCA(IBot bot, SquadManagerBotModuleCA squadManager, SquadCAType type)
			: this(bot, squadManager, type, null) { }

		public SquadCA(IBot bot, SquadManagerBotModuleCA squadManager, SquadCAType type, Actor target)
		{
			Bot = bot;
			SquadManager = squadManager;
			World = bot.Player.PlayerActor.World;
			Random = World.LocalRandom;
			Type = type;
			Target = Target.FromActor(target);
			FuzzyStateMachine = new StateMachineCA();

			switch (type)
			{
				case SquadCAType.Guerrilla:
					FuzzyStateMachine.ChangeState(this, new GroundUnitsIdleStateCA(), true);
					break;
				case SquadCAType.Harass:
					FuzzyStateMachine.ChangeState(this, new HarasserUnitsIdleStateCA(), true);
					break;
				case SquadCAType.Rush:
					FuzzyStateMachine.ChangeState(this, new GroundUnitsIdleStateCA(), true);
					break;
				case SquadCAType.Air:
					FuzzyStateMachine.ChangeState(this, new AirIdleStateCA(), true);
					break;
				case SquadCAType.Fighter:
					FuzzyStateMachine.ChangeState(this, new FighterIdleStateCA(), true);
					break;
				case SquadCAType.Gunship:
					FuzzyStateMachine.ChangeState(this, new GunshipCASStateCA(), true);
					break;
				case SquadCAType.Bomber:
					FuzzyStateMachine.ChangeState(this, new BomberIdleStateCA(), true);
					break;
				case SquadCAType.Protection:
					FuzzyStateMachine.ChangeState(this, new UnitsForProtectionIdleState(), true);
					break;
				case SquadCAType.Naval:
					FuzzyStateMachine.ChangeState(this, new NavyUnitsIdleState(), true);
					break;
				case SquadCAType.Artillery:
					FuzzyStateMachine.ChangeState(this, new ArtilleryUnitsIdleStateCA(), true);
					break;
				case SquadCAType.Support:
					FuzzyStateMachine.ChangeState(this, new SupportUnitsIdleStateCA(), true);
					break;
				case SquadCAType.FireSupport:
					FuzzyStateMachine.ChangeState(this, new FireSupportUnitsIdleStateCA(), true);
					break;
				case SquadCAType.Stealth:
					FuzzyStateMachine.ChangeState(this, new StealthUnitsIdleStateCA(), true);
					break;
			}
		}

		public void Update()
		{
			if (IsValid)
			{
				// LC6: the target the state is about to act on must still be
				// observable — an Actor that went hidden while committed is
				// stale consumption and the canary logs it. FrozenActor memory
				// targets are legal by design and skip the check.
				if (Target.Type == TargetType.Actor)
					SquadManager.CanaryObserved(Target.Actor, "squad-update-target");

				FuzzyStateMachine.Update(this);
			}
		}

		public bool IsValid => Units.Count > 0;

		public Actor TargetActor
		{
			get => Target.Actor;
			set => Target = Target.FromActor(value);
		}

		public bool IsTargetValid => IsValid && Target.IsValidFor(Units[0].Actor);

		public bool IsTargetVisible => Target.Actor == null || Target.Actor.CanBeViewedByPlayer(Bot.Player);

		public WPos CenterPosition { get { return Units[0].Actor.CenterPosition; } }

		public MiniYaml Serialize()
		{
			var nodes = new List<MiniYamlNode>()
			{
				new("Type", FieldSaver.FormatValue(Type)),
				new("Units", FieldSaver.FormatValue(Units.Where(a => !SquadManager.unitCannotBeOrdered(a.Actor)).Select(a => a.Actor.ActorID).ToArray())),
			};
			if (Target.Type == TargetType.Actor)
				nodes.Add(new MiniYamlNode("Target", FieldSaver.FormatValue(Target.Actor.ActorID)));

			return new MiniYaml("", nodes);
		}

		public static SquadCA Deserialize(IBot bot, SquadManagerBotModuleCA squadManager, MiniYaml yaml)
		{
			var type = SquadCAType.Rush;
			Actor targetActor = null;

			var typeNode = yaml.NodeWithKeyOrDefault("Type");
			if (typeNode != null)
				type = FieldLoader.GetValue<SquadCAType>("Type", typeNode.Value.Value);

			var targetNode = yaml.NodeWithKeyOrDefault("Target");
			if (targetNode != null)
				targetActor = squadManager.World.GetActorById(FieldLoader.GetValue<uint>("Target", targetNode.Value.Value));

			var squad = new SquadCA(bot, squadManager, type, targetActor);

			// RegisterNewSquad assigns this — Deserialize bypassed it, losing the
			// per-type target preferences (PreferTagged) for every loaded squad.
			squad.PriorityTags = squadManager.PriorityTagsFor(type);

			var unitsNode = yaml.NodeWithKeyOrDefault("Units");
			if (unitsNode != null)
			{
				// GetActorById can return null for actors removed between save
				// versions; a null wrapper survives Count>0 IsValid checks and
				// then NREs on the first .Actor dereference.
				foreach (var a in FieldLoader.GetValue<uint[]>("Units", unitsNode.Value.Value)
					.Select(a => squadManager.World.GetActorById(a))
					.Where(a => a != null))
				{
					squad.Units.Add(new UnitWposWrapper(a));
				}
			}

			return squad;
		}
	}
}
