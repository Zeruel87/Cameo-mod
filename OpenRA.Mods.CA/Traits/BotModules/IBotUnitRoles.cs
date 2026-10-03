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

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// The runtime query of the merged §12.4 roles system: which roles an actor type holds
	/// (frontline, anti_air, artillery, scout, ...) - derived once per ruleset from the
	/// ContentPack's declared BotRoles entries, the Player's BotRoleSets derivations and a
	/// statistical classifier for the units those leave unroled. Implemented in the Cameo
	/// assembly (OpenRA.Mods.Cameo BotUnitRoles) where the declared/derived role machinery
	/// lives; the CA consumers read through this interface and treat an absent provider as
	/// "feature off" - which is exactly what keeps `classic` untouched (§19.3: ONE merged
	/// system, not a second parallel roles map next to BotRoleSets).
	/// </summary>
	public interface IBotUnitRoles
	{
		/// <summary>role -> member actor names, resolved once per ruleset.</summary>
		IReadOnlyDictionary<string, HashSet<string>> RoleMembers { get; }

		/// <summary>actor name -> the roles it holds; absent key means unclassified.</summary>
		IReadOnlyDictionary<string, HashSet<string>> ActorRoles { get; }

		/// <summary>
		/// The one role an actor counts toward for composition accounting - first match in
		/// BotUnitRole.PrimaryRoleOrder, so specialists claim before frontline. Null when the
		/// actor is unclassified or holds no combat role.
		/// </summary>
		string PrimaryRoleOf(string actorName);
	}

	/// <summary>The shared §12.4 role taxonomy: the names the provider computes, the CA
	/// consumers compare against, and RoleMix/StageRequiredRoles yaml entries must use.</summary>
	public static class BotUnitRole
	{
		public const string Frontline = "frontline";
		public const string Skirmisher = "skirmisher";
		public const string AntiInfantry = "anti_infantry";
		public const string AntiArmour = "anti_armour";
		public const string Artillery = "artillery";
		public const string AntiAir = "anti_air";
		public const string Scout = "scout";
		public const string Support = "support";
		public const string Transport = "transport";
		public const string Gunship = "gunship";
		public const string Fighter = "fighter";
		public const string Bomber = "bomber";
		public const string AirTransport = "air_transport";

		// Target tags (§12.4): buildings worth striking, not units to produce.
		public const string Power = "power";
		public const string Defence = "defence";
		public const string Tech = "tech";

		// Primary-role precedence for counting a unit toward exactly one role:
		// specialists claim first so `frontline` remains the residual tank mass.
		public static readonly string[] PrimaryRoleOrder =
		{
			Support, Transport, AirTransport, Scout, Artillery, AntiAir, Bomber, Fighter, Gunship,
			AntiInfantry, AntiArmour, Skirmisher, Frontline
		};

		// The roles a unit can be counted toward (and the only valid RoleMix keys): the
		// mobile-combat taxonomy. Target tags and yaml-side list roles (guerrilla,
		// firesupport, navalunit, ...) are deliberately outside it.
		public static readonly HashSet<string> CombatRoles = new(PrimaryRoleOrder, System.StringComparer.Ordinal);
	}
}
