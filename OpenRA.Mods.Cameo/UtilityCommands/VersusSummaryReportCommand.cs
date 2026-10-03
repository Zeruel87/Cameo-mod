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
using System.Linq;
using OpenRA.Mods.Cameo.Widgets.Logic;
using OpenRA.Mods.Common.Traits;

namespace OpenRA.Mods.Cameo.UtilityCommands
{
	sealed class VersusSummaryReportCommand : IUtilityCommand
	{
		string IUtilityCommand.Name => "--versus-summary";

		bool IUtilityCommand.ValidateArguments(string[] args) => true;

		[Desc("[--no-naval] [actor ...]",
			"Print what the production tooltip shows for each buildable actor: damage % per armour ladder, the " +
			"Armor Piercing tag, the target domains, the derived Strong/Weak armours, and the grouped " +
			"Strong/Medium/Weak lines (--no-naval: as with the lobby's Naval Units option off). Tab-separated. " +
			"Uses the SAME VersusSummary the tooltip does, so it is the tooltip's data proven without a hover.")]
		void IUtilityCommand.Run(Utility utility, string[] args)
		{
			var modData = Game.ModData = utility.ModData;
			var rules = modData.DefaultRules;
			var naval = !args.Contains("--no-naval");
			var only = args.Skip(1).Where(a => a != "--no-naval").Select(a => a.ToLowerInvariant()).ToHashSet();

			static string Groups(System.Collections.Generic.List<VersusSummary.GroupValue> values) =>
				string.Join(", ", values.Select(v => v.Percent is int p ? $"{v.Group} ({p}%)" : $"{v.Group} (cannot attack)"));

			Console.WriteLine("actor\tinfantry\tvehicles\tbuildings\taircraft\tarmor_piercing\ttargets\tstrong\tweak\tgroup_strong\tgroup_medium\tgroup_weak");
			foreach (var actor in rules.Actors.Values.OrderBy(a => a.Name, StringComparer.Ordinal))
			{
				if (actor.Name.StartsWith('^') || !actor.HasTraitInfo<BuildableInfo>())
					continue;
				if (only.Count > 0 && !only.Contains(actor.Name))
					continue;

				var summary = VersusSummary.For(actor, rules, naval);
				if (!summary.HasWeapons)
					continue;

				var (strong, medium, weak) = VersusSummary.Bands(summary.GroupValues);

				var ladders = summary.Rows.Select(r => r.CanAttack
					? string.Join(" ", r.Rungs.Select(v => $"{v.Armor}={v.Percent}"))
					: "-");
				Console.WriteLine(string.Join("\t", new[] { actor.Name }
					.Concat(ladders)
					.Append(summary.ArmorPiercing ? "AP" : "")
					.Append(string.Join(",", summary.Targets))
					.Append(string.Join(",", summary.Strong()))
					.Append(string.Join(",", summary.Weak()))
					.Append(Groups(strong))
					.Append(Groups(medium))
					.Append(Groups(weak))));
			}
		}
	}
}
