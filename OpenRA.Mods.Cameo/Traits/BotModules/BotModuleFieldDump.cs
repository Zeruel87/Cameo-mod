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
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits.BotModules
{
	/// <summary>
	/// AI_ARCHITECTURE.md §2.9 P0, the equivalence gate: every public field of every bot trait on the
	/// Player actor, as the engine holds it after rules load (after BotRoleSets has filled its targets).
	/// The Python resolver cannot see what the C# fills at load; this can. Opt-in with the environment
	/// variable CAMEO_DUMP_BOT_MODULES=1, so normal boots write nothing. `tools/ai/dump_bot_modules.py`
	/// boots a worktree with it set, and `tools/ai/diff_bot_modules.py` compares two dumps.
	/// </summary>
	public static class BotModuleFieldDump
	{
		public const string EnvironmentVariable = "CAMEO_DUMP_BOT_MODULES";
		public const string Header = "=== bot-modules dump ===";

		public static void WriteIfRequested(ActorInfo player)
		{
			if (Environment.GetEnvironmentVariable(EnvironmentVariable) != "1")
				return;

			Log.AddChannel("bot-modules", "bot-modules.log");
			Log.Write("bot-modules", Header);
			foreach (var line in Lines(player))
				Log.Write("bot-modules", line);
		}

		/// <summary>One line per trait instance and field, `Type@instance.Field = value`, sorted.</summary>
		public static IEnumerable<string> Lines(ActorInfo player)
		{
			var lines = new List<string>();
			foreach (var ti in player.TraitInfos<TraitInfo>())
			{
				var type = ti.GetType();
				var name = type.Name.EndsWith("Info", StringComparison.Ordinal) ? type.Name[..^4] : type.Name;
				if (!name.Contains("Bot", StringComparison.Ordinal))
					continue;

				var key = ti.InstanceName == null ? name : name + "@" + ti.InstanceName;
				foreach (var f in type.GetFields(BindingFlags.Public | BindingFlags.Instance))
					if (f.Name != nameof(TraitInfo.InstanceName))
						lines.Add($"{key}.{f.Name} = {Format(f.GetValue(ti))}");
			}

			lines.Sort(StringComparer.Ordinal);
			return lines;
		}

		/// <summary>
		/// Deterministic text for a field value. Sets and dictionaries are sorted: .NET randomises string
		/// hashing per process, so a HashSet's own order differs between two boots of identical rules.
		/// Arrays and lists keep their order, which can matter.
		/// </summary>
		public static string Format(object value)
		{
			switch (value)
			{
				case null:
					return "";
				case string s:
					return s;
				case IDictionary d:
					return "{" + string.Join("; ", d.Keys.Cast<object>()
						.Select(k => Format(k) + ": " + Format(d[k]))
						.OrderBy(e => e, StringComparer.Ordinal)) + "}";
				case IEnumerable items when IsKeyValueSequence(value.GetType()):
					// FrozenDictionary & co.: not always a non-generic IDictionary, and unordered
					return "{" + string.Join("; ", items.Cast<object>().Select(FormatPair).OrderBy(e => e, StringComparer.Ordinal)) + "}";
				case IEnumerable items when IsSet(value.GetType()):
					return "[" + string.Join(", ", items.Cast<object>().Select(Format).OrderBy(e => e, StringComparer.Ordinal)) + "]";
				case IEnumerable items:
					return "(" + string.Join(", ", items.Cast<object>().Select(Format)) + ")";
				default:
					return FieldSaver.FormatValue(value);
			}
		}

		static string FormatPair(object pair)
		{
			var t = pair.GetType();
			return Format(t.GetProperty("Key").GetValue(pair)) + ": " + Format(t.GetProperty("Value").GetValue(pair));
		}

		static bool IsKeyValueSequence(Type t) =>
			t.GetInterfaces().Any(i => i.IsGenericType && i.GetGenericTypeDefinition() == typeof(IEnumerable<>)
				&& i.GetGenericArguments()[0].IsGenericType
				&& i.GetGenericArguments()[0].GetGenericTypeDefinition() == typeof(KeyValuePair<,>));

		// HashSet, FrozenSet (the runtime may hand out an internal subclass), ImmutableHashSet…
		static bool IsSet(Type t)
		{
			for (; t != null && t != typeof(object); t = t.BaseType)
				if (t.GetInterfaces().Any(i => i.IsGenericType && i.GetGenericTypeDefinition() == typeof(IReadOnlySet<>)))
					return true;

			return false;
		}
	}
}
