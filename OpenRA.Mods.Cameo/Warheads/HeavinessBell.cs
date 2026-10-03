#region Copyright & License Information
/*
 * Copyright 2015- OpenRA.Mods.AS Developers (see AUTHORS)
 * This file is a part of a third-party plugin for OpenRA, which is
 * free software. It is made available to you under the terms of the
 * GNU General Public License as published by the Free Software
 * Foundation. For more information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;
using System.Linq;

namespace OpenRA.Mods.Cameo.Warheads
{
	/// <summary>
	/// §12.0i continuous-heaviness bell. Ported from
	/// `tools/balance/gen_weapon_template.py:heaviness_bell` with the same constants
	/// and guarantees: derived armors are excluded, rank is restored per ladder,
	/// and Heroic / Airborne are re-derived LAST. `h` is a continuous scalar 0..2;
	/// `Heaviness` in yaml is `h * 1000`.
	/// </summary>
	public static class HeavinessBell
	{
		// ONE GLOBAL 13-slot scale, 0..2, step 1/6.
		// This is the ruling in DESIGN §12.0i / WEAPON_HEAVINESS.md §9.5b.
		static readonly string[][] BellAxisOrder =
		{
			new[] { "Scout" },
			new[] { "None" },
			new[] { "Fighter" },
			new[] { "Light" },
			new[] { "Wood" },
			new[] { "Bomber" },
			new[] { "Medium", "Flak", "Steel" },
			new[] { "Helicopter" },
			new[] { "Concrete" },
			new[] { "Heavy" },
			new[] { "Spaceship" },
			new[] { "Plate" },
			new[] { "Superheavy" }
		};

		static readonly Dictionary<string, double> BellAxis = new();

		// LO = 1 / TILT_RATIO; the bell must span the same 1.5x the discrete tilt already spans.
		const double BellLo = 1.0 / 1.5;
		const double BellSigma = 0.75;

		// DESIGN §12.0l (2026-09-26): every derived armour is the GEOMETRIC MEAN of its parents,
		// re-derived LAST in this order (a parent is final before its child reads it); Heroic alone
		// is a PRODUCT, Plate x Scout / 200, in the MAIN table only. Mirror of
		// gen_weapon_template.GEO_DERIVED — keep the two lists identical.
		static readonly (string Name, string[] Parents)[] GeoDerived =
		{
			("FlyingInfantry", new[] { "Scout", "Flak", "Helicopter" }),
			("CyborgLight", new[] { "None", "Light" }),
			("CyborgMedium", new[] { "Flak", "Medium" }),
			("CyborgHeavy", new[] { "Plate", "Heavy" }),
			("CyborgHeroic", new[] { "Heroic", "Superheavy" }),
			("AntiAirInfantry", new[] { "None", "Flak" }),
			("AntiAirVehicle", new[] { "Light", "Medium" }),
			("AntiAirBuilding", new[] { "Concrete", "Steel" }),
			("ShipLight", new[] { "Light", "Wood" }),
			("ShipMedium", new[] { "Medium", "Concrete" }),
			("ShipHeavy", new[] { "Heavy", "Steel" }),
			("ShipSuperheavy", new[] { "Superheavy", "Steel" }),
			("AntiAirShip", new[] { "ShipLight", "ShipMedium" }),
			("SubmarineLight", new[] { "ShipMedium", "Heavy" }),
			("SubmarineHeavy", new[] { "ShipHeavy", "Superheavy" })
		};

		const double HeroicDivisor = 200.0;

		static readonly HashSet<string> DerivedArmors = new(new[] { "Heroic" }.Concat(GeoDerived.Select(d => d.Name)));
		static readonly string[] NonArmorRows = { "Shield", "HAZMAT", "COMPOSITE", "BLAST", "REFLECTOR", "ARMOR" };

		// Ladders, lightest -> heaviest, for the rank-restore step.
		static readonly string[][] Ladders =
		{
			new[] { "None", "Flak", "Plate", "Heroic" },
			new[] { "Scout", "Light", "Medium", "Heavy", "Superheavy" },
			new[] { "Wood", "Steel", "Concrete" },
			new[] { "Fighter", "Bomber", "Helicopter", "Spaceship" }
		};

		static HeavinessBell()
		{
			var n = BellAxisOrder.Length;
			for (var i = 0; i < n; i++)
			{
				var x = i * 2.0 / (n - 1);
				foreach (var a in BellAxisOrder[i])
					BellAxis[a] = x;
			}
		}

		/// <param name="mainTable">True for the MAIN `Versus` only: Heroic is re-derived as
		/// Plate x Scout / 200 there. The percentage tables keep their own Heroic (200 is the MAIN
		/// table's ceiling; the percentage tops are 16-30).</param>
		public static Dictionary<string, int> Transform(IReadOnlyDictionary<string, int> table, double h, bool mainTable = false)
		{
			var values = new Dictionary<string, double>();
			foreach (var kv in table)
				values[kv.Key] = kv.Value;

			var live = values.Where(kv => !NonArmorRows.Contains(kv.Key)).Select(kv => kv.Value).ToList();
			if (live.Count == 0 || live.Max() <= live.Min())
				return table.ToDictionary(kv => kv.Key, kv => kv.Value);

			var tiltable = values
				.Where(kv => BellAxis.ContainsKey(kv.Key) && !DerivedArmors.Contains(kv.Key))
				.ToDictionary(kv => kv.Key, kv => kv.Value);

			var com = CentreOfMass(tiltable);
			if (com.HasValue)
			{
				var mu = (h + com.Value) / 2.0;

				var belled = new Dictionary<string, double>();
				foreach (var kv in tiltable)
				{
					var x = BellAxis[kv.Key];
					var curve = BellLo + (1.0 - BellLo) * Math.Exp(-Math.Pow(x - mu, 2) / (2.0 * BellSigma * BellSigma));
					belled[kv.Key] = kv.Value * curve;
				}

				// Renormalise so heaviness redistributes and never inflates (§12.0i law 2), on the
				// GEOMETRIC mean — R16 (2026-09-25) made geomean 100 the binding law, so the tilt
				// must leave the table's geometric mean where it found it. Zero rows are skipped
				// (a single zero collapses a geometric mean); they stay zero under the bell anyway.
				var before = GeometricMean(tiltable.Values);
				var after = GeometricMean(belled.Values);
				if (before > 0 && after > 0)
				{
					foreach (var a in belled.Keys.ToList())
						belled[a] *= before / after;
				}

				// Rank restore: give each armor the same rank it held in the input.
				foreach (var ladder in Ladders)
				{
					var rungs = ladder.Where(a => belled.ContainsKey(a)).ToList();
					if (rungs.Count < 2)
						continue;

					var order = Enumerable.Range(0, rungs.Count)
						.OrderByDescending(i => values[rungs[i]])
						.ThenBy(i => i)
						.ToList();

					var ranked = rungs.Select(a => belled[a]).OrderByDescending(v => v).ToList();
					for (var slot = 0; slot < order.Count; slot++)
						values[rungs[order[slot]]] = ranked[slot];
				}
			}

			// Re-derive the derived armors LAST from the finished profile (§12.0b / §12.0l), on
			// the ROUNDED rows, exactly as the generator's `derive_rows` does on emitted integers.
			var result = values.ToDictionary(kv => kv.Key, kv => (int)Math.Round(kv.Value));
			if (mainTable && result.ContainsKey("Heroic") && result.ContainsKey("Plate") && result.ContainsKey("Scout"))
			{
				var body = result
					.Where(kv => !NonArmorRows.Contains(kv.Key) && !DerivedArmors.Contains(kv.Key))
					.Select(kv => kv.Value)
					.ToList();
				result["Heroic"] = body.Count > 0 && body.Min() == body.Max()
					? body[0]
					: (int)Math.Round(result["Plate"] * (double)result["Scout"] / HeroicDivisor);
			}

			foreach (var (name, parents) in GeoDerived)
			{
				if (!result.ContainsKey(name) || !parents.All(result.ContainsKey))
					continue;

				var product = 1.0;
				foreach (var p in parents)
					product *= Math.Max(result[p], 0);
				result[name] = (int)Math.Round(Math.Pow(product, 1.0 / parents.Length));
			}

			return result;
		}

		static double GeometricMean(IEnumerable<double> values)
		{
			var positive = values.Where(v => v > 0).ToList();
			if (positive.Count == 0)
				return 0;

			return Math.Exp(positive.Sum(Math.Log) / positive.Count);
		}

		static double? CentreOfMass(Dictionary<string, double> vals)
		{
			double total = 0;
			double weighted = 0;
			foreach (var kv in vals)
			{
				if (kv.Value > 0 && BellAxis.TryGetValue(kv.Key, out var x))
				{
					total += kv.Value;
					weighted += x * kv.Value;
				}
			}

			return total > 0 ? weighted / total : null;
		}
	}
}
