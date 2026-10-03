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

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>The eight build-order knob names (AI_ARCHITECTURE 12.25). A knob is a multiplier in thousandths, 1000 = x1.0.</summary>
	public static class BuildOrderKnob
	{
		public const string Tempo = "tempo";
		public const string Greed = "greed";
		public const string Production = "production";
		public const string Tech = "tech";
		public const string Defence = "defence";
		public const string PowerMargin = "power_margin";
		public const string Expansion = "expansion";
		public const string Support = "support";

		public const int Neutral = 1000;

		public static readonly string[] All = { Tempo, Greed, Production, Tech, Defence, PowerMargin, Expansion, Support };
	}

	/// <summary>The building categories a provider derives from the rules (never from actor-id lists).</summary>
	public static class BuildOrderCategory
	{
		public const string Conyard = "conyard";
		public const string Power = "power";
		public const string Refinery = "refinery";
		public const string Barracks = "barracks";
		public const string Factory = "factory";
		public const string Production = "production";
		public const string Tech = "tech";
		public const string Defence = "defence";
		public const string Support = "support";
		public const string Superweapon = "superweapon";
		public const string Other = "other";

		/// <summary>
		/// Whether a building of category <paramref name="actual"/> satisfies an opening step <paramref name="wanted"/>:
		/// the generic `production` step takes a barracks, a factory or any other production building; every other step is exact.
		/// </summary>
		public static bool Satisfies(string wanted, string actual)
		{
			if (string.IsNullOrEmpty(wanted) || string.IsNullOrEmpty(actual))
				return false;

			if (string.Equals(wanted, actual, StringComparison.Ordinal))
				return true;

			return string.Equals(wanted, Production, StringComparison.Ordinal)
				&& (string.Equals(actual, Barracks, StringComparison.Ordinal) || string.Equals(actual, Factory, StringComparison.Ordinal));
		}

		/// <summary>The knob that scales a building category's fractions (null = none): see AI_ARCHITECTURE 12.25.</summary>
		public static string KnobFor(string category)
		{
			switch (category)
			{
				case Barracks:
				case Factory:
				case Production:
					return BuildOrderKnob.Production;
				case Tech:
				case Superweapon:
					return BuildOrderKnob.Tech;
				case Defence:
					return BuildOrderKnob.Defence;
				case Support:
					return BuildOrderKnob.Support;
				case Refinery:
					return BuildOrderKnob.Greed;
				default:
					return null;
			}
		}
	}

	/// <summary>
	/// Build-order knobs (DESIGN 19.2, AI_ARCHITECTURE 12.25): HOW and WHEN the base builder builds. Providers live in
	/// OpenRA.Mods.Cameo and must not be referenced by name from this assembly. The shared base builder reads this ONLY
	/// from an enabled provider; no provider (classic, or the switch off) means every number runs unchanged, bit-identical.
	/// </summary>
	public interface IBotBuildOrderKnobs
	{
		/// <summary>False while the provider is disabled: the consumer must behave as if it did not exist.</summary>
		bool Enabled { get; }

		/// <summary>The current value of a knob in thousandths (1000 = x1.0), after preset, learned, jitter and the react layer.</summary>
		int KnobMilli(string knob);

		/// <summary>The rules-derived category of a building (a BuildOrderCategory name), `other` when none applies.</summary>
		string CategoryOf(string actorName);

		/// <summary>The category the active opening wants built next, or null when no opening is active.</summary>
		string OpeningWanted { get; }

		/// <summary>The base builder queued this building: the opening advances when it satisfies the wanted step.</summary>
		void NotifyQueued(string actorName);
	}

	/// <summary>Consumer helpers: the first enabled provider answers.</summary>
	public static class BotBuildOrderKnobs
	{
		public static IBotBuildOrderKnobs FirstEnabled(this IBotBuildOrderKnobs[] providers)
		{
			if (providers != null)
				foreach (var provider in providers)
					if (provider.Enabled)
						return provider;

			return null;
		}

		/// <summary>value x milli / 1000, rounded down, in 64-bit so a large value cannot overflow.</summary>
		public static int Scale(int value, int milli)
		{
			return milli == BuildOrderKnob.Neutral ? value : (int)System.Math.Min(int.MaxValue, value * (long)milli / 1000);
		}
	}
}
