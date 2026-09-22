#region Copyright & License Information
/*
 * Copyright (c) The OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License as
 * published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Linq;
using System.Reflection;
using NUnit.Framework;
using OpenRA.GameRules;
using OpenRA.Mods.Cameo.Warheads;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	/// <summary>
	/// Differential tests that EXECUTE the real <c>IRulesetLoaded&lt;WeaponInfo&gt;.RulesetLoaded</c>
	/// implementation on warheads loaded from MiniYaml through the engine's own
	/// <see cref="FieldLoader"/> — no copied equations. The method reads no rules/info
	/// state, so null arguments are safe. Effective fields are read via reflection.
	/// All expected vectors were produced by tools/balance/effective_heaviness.py
	/// (the TS90mm CannonAP_Medium percentage table is knife-edge free — verified).
	/// Requires the mod to be built (parent-controlled).
	/// </summary>
	[TestFixture]
	public sealed class AreaDamageWarheadHeavinessRulesLoadedTest
	{
		// TS90-authored 17-key percentage table, fixture insertion order.
		static readonly (string, int)[] Ts90Authored =
		{
			("Bomber", 6), ("Concrete", 15), ("Fighter", 5), ("Flak", 10), ("Heavy", 19),
			("Helicopter", 7), ("Heroic", 12), ("Light", 17), ("Medium", 18), ("None", 9),
			("Plate", 11), ("Scout", 16), ("Shield", 25), ("Spaceship", 8), ("Steel", 14),
			("Superheavy", 20), ("Wood", 13),
		};

		// Python mirror: bell(ReadOnlyDictionary(Ts90Authored), h) — one row per h.
		static readonly IReadOnlyDictionary<string, int>[] Ts90Belled =
		{
			// h = 0.0
			ToDict(("Bomber", 7), ("Concrete", 15), ("Fighter", 6), ("Flak", 10), ("Heavy", 19),
				("Helicopter", 7), ("Heroic", 9), ("Light", 17), ("Medium", 17), ("None", 9),
				("Plate", 11), ("Scout", 16), ("Shield", 25), ("Spaceship", 7), ("Steel", 15),
				("Superheavy", 19), ("Wood", 14)),
			// h = 0.5
			ToDict(("Bomber", 7), ("Concrete", 15), ("Fighter", 5), ("Flak", 10), ("Heavy", 18),
				("Helicopter", 7), ("Heroic", 8), ("Light", 17), ("Medium", 18), ("None", 9),
				("Plate", 11), ("Scout", 15), ("Shield", 25), ("Spaceship", 7), ("Steel", 15),
				("Superheavy", 19), ("Wood", 14)),
			// h = 1.0
			ToDict(("Bomber", 6), ("Concrete", 16), ("Fighter", 5), ("Flak", 10), ("Heavy", 19),
				("Helicopter", 8), ("Heroic", 8), ("Light", 17), ("Medium", 18), ("None", 8),
				("Plate", 11), ("Scout", 14), ("Shield", 25), ("Spaceship", 8), ("Steel", 15),
				("Superheavy", 20), ("Wood", 14)),
			// h = 1.5
			ToDict(("Bomber", 6), ("Concrete", 16), ("Fighter", 4), ("Flak", 11), ("Heavy", 19),
				("Helicopter", 8), ("Heroic", 7), ("Light", 16), ("Medium", 19), ("None", 8),
				("Plate", 11), ("Scout", 13), ("Shield", 25), ("Spaceship", 8), ("Steel", 15),
				("Superheavy", 20), ("Wood", 13)),
			// h = 2.0
			ToDict(("Bomber", 6), ("Concrete", 17), ("Fighter", 4), ("Flak", 10), ("Heavy", 21),
				("Helicopter", 8), ("Heroic", 7), ("Light", 15), ("Medium", 19), ("None", 7),
				("Plate", 12), ("Scout", 13), ("Shield", 25), ("Spaceship", 9), ("Steel", 14),
				("Superheavy", 21), ("Wood", 12)),
		};

		static MiniYamlNode Field(string key, string value)
		{
			return new MiniYamlNode(key, new MiniYaml(value));
		}

		static MiniYamlNode Table(string key, params (string, int)[] rows)
		{
			return new MiniYamlNode(key, new MiniYaml("", rows
				.Select(row => Field(row.Item1, row.Item2.ToString()))));
		}

		static T Load<T>(params MiniYamlNode[] fields) where T : new()
		{
			return FieldLoader.Load<T>(new MiniYaml("", fields));
		}

		static object Effective(object warhead, string name)
		{
			return typeof(AreaDamageWarhead).GetField(name,
				BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(warhead);
		}

		static IReadOnlyDictionary<string, int> EffectiveTable(object warhead, string name)
		{
			return (IReadOnlyDictionary<string, int>)Effective(warhead, name)!;
		}

		static void RulesetLoaded(object warhead)
		{
			((IRulesetLoaded<WeaponInfo>)warhead).RulesetLoaded(null, null);
		}

		static IReadOnlyDictionary<string, int> ToDict(params (string, int)[] rows)
		{
			var dict = new Dictionary<string, int>();
			foreach (var (armor, value) in rows)
				dict[armor] = value;
			return dict;
		}

		static AreaDamageWarhead LoadTs90(int? heaviness = null, params MiniYamlNode[] extra)
		{
			var fields = new List<MiniYamlNode>
			{
				Field("Damage", "6000"),
				Field("Spread", "600"),
				Field("PercentageScale", "10000"),
				Table("Versus", Ts90Authored),
				Table("PercentageVersus", Ts90Authored),
			};
			if (heaviness is int hv)
				fields.Add(Field("Heaviness", hv.ToString()));
			// Overrides must REPLACE the base fixture's same-key field — a duplicate
			// key is an engine-level InvalidDataException, not an override.
			fields.RemoveAll(f => extra.Any(x => string.Equals(
				x.Key, f.Key, StringComparison.Ordinal)));
			fields.AddRange(extra);
			return Load<AreaDamageWarhead>(fields.ToArray());
		}

		// Shared-mode base: NO percentage tables — the shared profile lives on the
		// belled flat Versus. `PercentageScale` stays the scalar dial.
		static AreaDamageWarhead LoadTs90Shared(int? heaviness, params MiniYamlNode[] extra)
		{
			var fields = new List<MiniYamlNode>
			{
				Field("Damage", "6000"),
				Field("Spread", "600"),
				Field("PercentageScale", "2000"),
				Field("HeavinessMode", "SharedVersus"),
				Table("Versus", Ts90Authored),
			};
			if (heaviness is int hv)
				fields.Add(Field("Heaviness", hv.ToString()));
			fields.AddRange(extra);
			return Load<AreaDamageWarhead>(fields.ToArray());
		}

		static AreaDamageWarhead LoadDirectGeometry(int? heaviness)
		{
			var fields = new List<MiniYamlNode>
			{
				Field("Damage", "6000"),
				Field("Spread", "600"),
				Field("Falloff", "100, 50, 0"),
				Field("Range", "0, 120, 300"),
				Field("MinRadius", "50"),
				Field("MaxRadius", "300"),
			};
			if (heaviness is int hv)
				fields.Add(Field("Heaviness", hv.ToString()));
			return Load<AreaDamageWarhead>(fields.ToArray());
		}

		[Test]
		public void DisabledHeaviness_Omitted_KeepsAuthoredGeometryCoordinatesVerbatim()
		{
			// AUTHORED coordinates directly (review P1: omitted vs explicit -1 were
			// previously only compared to each other, both through the same broken
			// path — a helper without a disabled early return scaled every
			// Explicit-Range coordinate to about 2/3 of authored (h = -0.001 gives
			// (h + 2) / 3 = 0.666333) on a disabled warhead).
			var warhead = LoadDirectGeometry(null);
			RulesetLoaded(warhead);

			Assert.That(Effective(warhead, "effectiveSpread"), Is.EqualTo(new WDist(600)));
			var range = (ImmutableArray<WDist>)Effective(warhead, "effectiveRange")!;
			Assert.That(range.Select(r => r.Length).ToArray(),
				Is.EqualTo(new[] { 0, 120, 300 }), "authored Range coordinates");
			Assert.That(Effective(warhead, "effectiveMinRadius"), Is.EqualTo(new WDist(50)));
			Assert.That(Effective(warhead, "effectiveMaxRadius"), Is.EqualTo(new WDist(300)));
		}

		[Test]
		public void DisabledHeaviness_ExplicitSentinel_KeepsAuthoredGeometryCoordinatesVerbatim()
		{
			var warhead = LoadDirectGeometry(-1);
			RulesetLoaded(warhead);

			Assert.That(Effective(warhead, "effectiveSpread"), Is.EqualTo(new WDist(600)));
			var range = (ImmutableArray<WDist>)Effective(warhead, "effectiveRange")!;
			Assert.That(range.Select(r => r.Length).ToArray(),
				Is.EqualTo(new[] { 0, 120, 300 }), "authored Range coordinates");
			Assert.That(Effective(warhead, "effectiveMinRadius"), Is.EqualTo(new WDist(50)));
			Assert.That(Effective(warhead, "effectiveMaxRadius"), Is.EqualTo(new WDist(300)));
		}

		[Test]
		public void InvalidHeaviness_FailsClearAtRulesLoad()
		{
			Assert.Throws<YamlException>(() => RulesetLoaded(LoadTs90(2500)));
			Assert.Throws<YamlException>(() => RulesetLoaded(LoadTs90(-500)));
		}

		[Test]
		public void OmittedHeaviness_IsByteEquivalentToExplicitlyDisabled()
		{
			var omitted = LoadTs90();
			RulesetLoaded(omitted);
			var disabled = LoadTs90(-1);
			RulesetLoaded(disabled);

			foreach (var name in new[] { "effectiveSpread", "effectiveRange",
				"effectiveMinRadius", "effectiveMaxRadius", "effectiveVersus",
				"effectivePercentageVersus" })
			{
				var a = Effective(omitted, name);
				var b = Effective(disabled, name);
				if (a is ImmutableArray<WDist> ra && b is ImmutableArray<WDist> rb)
					Assert.That(ra.ToArray(), Is.EqualTo(rb.ToArray()), name);
				else
					Assert.That(a, Is.EqualTo(b), name);
			}
		}

		[Test]
		public void DisabledHeaviness_KeepsAuthoredTablesVerbatim()
		{
			var warhead = LoadTs90(-1);
			RulesetLoaded(warhead);
			Assert.That(Effective(warhead, "effectiveSpread"), Is.EqualTo(new WDist(600)));
			Assert.That(EffectiveTable(warhead, "effectivePercentageVersus"),
				Is.EqualTo(ToDict(Ts90Authored)));
			var range = (ImmutableArray<WDist>)Effective(warhead, "effectiveRange")!;
			// Default Falloff (5 entries) x authored Spread 600.
			Assert.That(range.Select(r => r.Length).ToArray(),
				Is.EqualTo(new[] { 0, 600, 1200, 1800, 2400 }));
		}

		[TestCase(0, 400)]        // 600 * 2/3
		[TestCase(500, 500)]      // 600 * 5/6
		[TestCase(1000, 600)]
		[TestCase(1500, 700)]
		[TestCase(2000, 800)]
		public void ActiveHeaviness_ScalesSpreadTruncatingTowardZero(int heaviness, int expectedSpread)
		{
			var warhead = LoadTs90(heaviness);
			RulesetLoaded(warhead);
			Assert.That(Effective(warhead, "effectiveSpread"),
				Is.EqualTo(new WDist(expectedSpread)));
		}

		[TestCase(0, 0)]
		[TestCase(500, 1)]
		[TestCase(1000, 2)]
		[TestCase(1500, 3)]
		[TestCase(2000, 4)]
		public void ActiveHeaviness_BelledVersusMatchesThePythonMirror(int heaviness, int vectorIndex)
		{
			var warhead = LoadTs90(heaviness);
			RulesetLoaded(warhead);
			var versus = EffectiveTable(warhead, "effectiveVersus");
			foreach (var (armor, value) in Ts90Belled[vectorIndex])
				Assert.That(versus[armor], Is.EqualTo(value), $"armor {armor} at h={heaviness / 1000.0}");
		}

		[Test]
		public void ActiveHeaviness_FoldedPercentageHalfIsBelledOnceNotTwice()
		{
			// No authored anchors: the folded half reuses the ALREADY-belled main
			// table by reference (never a second transform).
			var warhead = LoadTs90(1000);
			RulesetLoaded(warhead);
			var pct = EffectiveTable(warhead, "effectivePercentageVersus");
			var versus = EffectiveTable(warhead, "effectiveVersus");
			Assert.That(pct["Heavy"], Is.EqualTo(versus["Heavy"]));
			Assert.That(pct["Heavy"], Is.EqualTo(19)); // Python mirror at h=1
		}

		[Test]
		public void ActiveHeaviness_TinyShockwaveRadiiTruncatingToZero_StaysShockwave()
		{
			// MinRadius 1 / MaxRadius 1 both truncate to 0 at h=0's 2/3 scale; the
			// AUTHORED MaxRadius branch decision must survive (rings at zero, not a
			// silent switch to static-cloud mode).
			var warhead = LoadTs90(0,
				Field("MinRadius", "1"),
				Field("MaxRadius", "1"),
				Field("Ticks", "4"));
			Assert.DoesNotThrow(() => RulesetLoaded(warhead));
			Assert.That(Effective(warhead, "effectiveMinRadius"), Is.EqualTo(new WDist(0)));
			Assert.That(Effective(warhead, "effectiveMaxRadius"), Is.EqualTo(new WDist(0)));
		}

		[Test]
		public void ActiveHeaviness_CollapsedExplicitRangeFailsClear()
		{
			// 1023 / 1024 are strictly increasing authored; scaled 2/3 both truncate
			// to the POSITIVE duplicate 682 — GetDamageFalloff enters segment 1 for
			// every in-range victim and calls int2.Lerp with span 0, so the
			// rules-load must fail clear instead.
			var warhead = LoadTs90(0,
				Field("Falloff", "100, 37"),
				Field("Range", "1023, 1024"));
			Assert.Throws<YamlException>(() => RulesetLoaded(warhead));
		}

		[Test]
		public void ActiveHeaviness_ZeroFrontAfterTruncationIsHarmlessNotRejected()
		{
			// A zero front (0 == 0) never satisfies the loop's `outer > distance`
			// entry condition for any distance >= 0, so the authored 0/1 -> scaled
			// 0/0 collapse is harmless and MUST be preserved, not rejected.
			var warhead = LoadTs90(0,
				Field("Falloff", "100, 37"),
				Field("Range", "0, 1"));
			Assert.DoesNotThrow(() => RulesetLoaded(warhead));
			var range = (ImmutableArray<WDist>)Effective(warhead, "effectiveRange")!;
			Assert.That(range.Select(r => r.Length).ToArray(), Is.EqualTo(new[] { 0, 0 }));
		}

		[TestCase(1_700_000_000, 2000)]   // 1_700_000_000 * 4/3 = 2_266_666_666 > Int32 max
		[TestCase(-2_000_000_000, 2000)]  // -2_000_000_000 * 4/3 < Int32 min (negative WDist underflow)
		public void ScaledRadiusLength_OverflowsFailClear(int length, int heaviness)
		{
			Assert.Throws<YamlException>(() => AreaDamageWarhead.ScaledRadiusLength(length, heaviness));
		}

		[TestCase(1_500_000_000, 2000, 2_000_000_000)]   // 1_500_000_000 * 4/3 fits
		[TestCase(-1_500_000_000, 2000, -2_000_000_000)] // normal negative magnitude fits
		[TestCase(-2_000_000_000, -1, -2_000_000_000)]   // disabled: negative legacy verbatim
		[TestCase(43, 0, 28)]                            // normal truncation toward zero
		public void ScaledRadiusLength_NormalValuesTruncate(int length, int heaviness, int expected)
		{
			Assert.That(AreaDamageWarhead.ScaledRadiusLength(length, heaviness), Is.EqualTo(expected));
		}

		[Test]
		public void ActiveHeaviness_AuthoredRadiusNearInt32Max_FailsClearAtRulesLoad()
		{
			var warhead = LoadTs90(2000, Field("Spread", "2100000000"));
			Assert.Throws<YamlException>(() => RulesetLoaded(warhead));
		}

		[Test]
		public void Anchors_FullBandProfileMatchesThePythonMirror()
		{
			// Light anchor == Medium anchor == the authored 17-key table (so the
			// interpolated table IS the authored table), Heavy = authored + 10.
			// The bell then runs once -> exactly the h=0.5 Python mirror vector.
			var warhead = LoadTs90(500,
				Table("PercentageVersusLight", Ts90Authored),
				Table("PercentageVersusHeavy", Ts90Authored
					.Select(kv => (kv.Item1, kv.Item2 + 10)).ToArray()));
			RulesetLoaded(warhead);
			var effective = EffectiveTable(warhead, "effectivePercentageVersus");
			foreach (var (armor, value) in Ts90Belled[1])
				Assert.That(effective[armor], Is.EqualTo(value),
					$"armor {armor} at h=0.5");
		}

		[Test]
		public void ActiveHeaviness_SingleEntryRangeIsAcceptedScaled()
		{
			var warhead = LoadTs90(0,
				Field("Falloff", "100, 37, 14, 5, 0"),
				Field("Range", "1024"));
			Assert.DoesNotThrow(() => RulesetLoaded(warhead));
			var range = (ImmutableArray<WDist>)Effective(warhead, "effectiveRange")!;
			Assert.That(range.Length, Is.EqualTo(1));
			Assert.That(range[0], Is.EqualTo(new WDist(682)));
		}

		[Test]
		public void ActiveHeaviness_ExplicitRangeScalesEveryCoordinateOnce()
		{
			var warhead = LoadTs90(500,
				Field("Falloff", "100, 37, 14, 5, 0"),
				Field("Range", "600, 1200, 1800, 2400, 3000"),
				Field("MinRadius", "300"),
				Field("MaxRadius", "3000"));
			RulesetLoaded(warhead);
			var range = (ImmutableArray<WDist>)Effective(warhead, "effectiveRange")!;
			Assert.That(range.Select(r => r.Length).ToArray(),
				Is.EqualTo(new[] { 500, 1000, 1500, 2000, 2500 }));
			Assert.That(Effective(warhead, "effectiveMinRadius"), Is.EqualTo(new WDist(250)));
			Assert.That(Effective(warhead, "effectiveMaxRadius"), Is.EqualTo(new WDist(2500)));
		}

		[Test]
		public void Anchors_SingleEndpointFailsClear()
		{
			var warhead = LoadTs90(1000,
				Table("PercentageVersusLight", ("None", 10), ("Flak", 30)));
			Assert.Throws<YamlException>(() => RulesetLoaded(warhead));
		}

		[Test]
		public void Anchors_MissingMediumAnchorFailsClear()
		{
			var warhead = LoadTs90(1000,
				Table("PercentageVersusLight", ("None", 10), ("Flak", 30)),
				Table("PercentageVersusHeavy", ("None", 30), ("Flak", 28)));
			Assert.Throws<YamlException>(() => RulesetLoaded(warhead));
		}

		[Test]
		public void Anchors_MismatchedKeysFailClear()
		{
			var warhead = LoadTs90(1000,
				Table("PercentageVersusLight", ("None", 10), ("Flak", 30)),
				Table("PercentageVersusHeavy", ("None", 30)));
			Assert.Throws<YamlException>(() => RulesetLoaded(warhead));
		}

		[Test]
		public void Anchors_NegativeEndpointValueFailsClear()
		{
			var warhead = LoadTs90(1000,
				Table("PercentageVersusLight", Ts90Authored.Select(kv =>
					(kv.Item1, kv.Item1 == "Heavy" ? -1 : kv.Item2)).ToArray()),
				Table("PercentageVersusHeavy", Ts90Authored.Select(kv =>
					(kv.Item1, kv.Item2 + 10)).ToArray()));
			Assert.Throws<YamlException>(() => RulesetLoaded(warhead));
		}

		[Test]
		public void Anchors_OnDisabledHeavinessFailClear()
		{
			var warhead = LoadTs90(-1,
				Table("PercentageVersusLight", Ts90Authored),
				Table("PercentageVersusHeavy", Ts90Authored
					.Select(kv => (kv.Item1, kv.Item2 + 10)).ToArray()));
			Assert.Throws<YamlException>(() => RulesetLoaded(warhead));
		}

		[Test]
		public void Anchors_FullBandPath_InterpolatesPiecewiseTiesEven()
		{
			// Light anchor == Medium anchor == the authored 17-key table; Heavy =
			// authored + 10. On h in [0,1] the interpolated value is the medium
			// anchor itself (L == M), so every armor must be exact at BOTH ends.
			var light = ToDict(Ts90Authored);
			var heavy = ToDict(Ts90Authored.Select(kv => (kv.Item1, kv.Item2 + 10)).ToArray());
			foreach (var hv in new[] { 500, 1000 })
			{
				var warhead = LoadTs90(hv,
					Table("PercentageVersusLight", Ts90Authored),
					Table("PercentageVersusHeavy", Ts90Authored
						.Select(kv => (kv.Item1, kv.Item2 + 10)).ToArray()));
				RulesetLoaded(warhead);
				var raw = AreaDamageWarhead.InterpolatePercentageBands(light, light, heavy, hv);
				foreach (var (armor, value) in light)
					Assert.That(raw[armor], Is.EqualTo(value), $"armor {armor} at h={hv / 1000.0}");
				// The bell then ran ONCE over the interpolated table (same key set).
				var effective = EffectiveTable(warhead, "effectivePercentageVersus");
				Assert.That(effective.Keys, Is.EquivalentTo(raw.Keys));
			}
		}

		[Test]
		public void Subclass_ActiveHeaviness_BellsItsOwnVersus()
		{
			// Subclass parity: the bell runs on the subclass's OWN Versus table.
			// Python mirror for {"Heavy":19,"Light":17,"Scout":16} at h=1.0:
			// {"Heavy":19,"Light":18,"Scout":15}.
			var warhead = Load<AreaDamagePercentageWarhead>(
				Field("Damage", "20"),
				Field("Spread", "600"),
				Field("Heaviness", "1000"),
				Table("Versus", ("Heavy", 19), ("Light", 17), ("Scout", 16)));
			Assert.DoesNotThrow(() => RulesetLoaded(warhead));
			var versus = EffectiveTable(warhead, "effectiveVersus");
			Assert.That(versus["Heavy"], Is.EqualTo(19));
			Assert.That(versus["Light"], Is.EqualTo(18));
			Assert.That(versus["Scout"], Is.EqualTo(15));
			Assert.That(Effective(warhead, "effectiveSpread"), Is.EqualTo(new WDist(600)));
		}

		[Test]
		public void Subclass_RejectsPercentageVersusAnchors_Active()
		{
			var warhead = Load<AreaDamagePercentageWarhead>(
				Field("Damage", "20"),
				Field("Spread", "600"),
				Field("Heaviness", "1000"),
				Table("PercentageVersus", ("None", 20), ("Flak", 35)),
				Table("PercentageVersusLight", ("None", 10), ("Flak", 30)),
				Table("PercentageVersusHeavy", ("None", 30), ("Flak", 28)));
			Assert.Throws<YamlException>(() => RulesetLoaded(warhead));
		}

		[Test]
		public void Subclass_RejectsPercentageVersusAnchors_Disabled()
		{
			var warhead = Load<AreaDamagePercentageWarhead>(
				Field("Damage", "20"),
				Field("Heaviness", "-1"),
				Table("PercentageVersusLight", ("None", 10), ("Flak", 30)),
				Table("PercentageVersusHeavy", ("None", 30), ("Flak", 28)));
			Assert.Throws<YamlException>(() => RulesetLoaded(warhead));
		}

		[Test]
		public void Subclass_DisabledKeepsAuthoredValuesVerbatim()
		{
			var warhead = Load<AreaDamagePercentageWarhead>(
				Field("Damage", "20"),
				Field("Spread", "600"),
				Field("PercentageDenominator", "10000"));
			RulesetLoaded(warhead);
			Assert.That(Effective(warhead, "effectiveSpread"), Is.EqualTo(new WDist(600)));
			Assert.That(EffectiveTable(warhead, "effectiveVersus"), Is.Empty);
		}

		[Test]
		public void FoldedPercentageBandsRegression_EndpointsExact()
		{
			Assert.That(AreaDamageWarhead.InterpolatePercentageBands(
				ToDict(("None", 10), ("Flak", 30), ("Plate", 50), ("Medium", 40)),
				ToDict(("None", 20), ("Flak", 35), ("Plate", 40), ("Medium", 38)),
				ToDict(("None", 30), ("Flak", 28), ("Plate", 60), ("Medium", 36)),
				1000),
				Is.EqualTo(ToDict(("None", 20), ("Flak", 35), ("Plate", 40), ("Medium", 38))));
			Assert.That(AreaDamageWarhead.InterpolatePercentageBands(
				ToDict(("None", 10), ("Flak", 30), ("Plate", 50), ("Medium", 40)),
				ToDict(("None", 20), ("Flak", 35), ("Plate", 40), ("Medium", 38)),
				ToDict(("None", 30), ("Flak", 28), ("Plate", 60), ("Medium", 36)),
				0)["Plate"], Is.EqualTo(50));
			Assert.That(AreaDamageWarhead.InterpolatePercentageBands(
				ToDict(("None", 10), ("Flak", 30), ("Plate", 50), ("Medium", 40)),
				ToDict(("None", 20), ("Flak", 35), ("Plate", 40), ("Medium", 38)),
				ToDict(("None", 30), ("Flak", 28), ("Plate", 60), ("Medium", 36)),
				2000)["Medium"], Is.EqualTo(36));
		}

		// ------------------------------------------------------------------
		// HEAVINESSMODE SHAREDVERSUS (the approved §12.0i shared profile).
		// ------------------------------------------------------------------

		[TestCase(0, 0)]
		[TestCase(500, 1)]
		[TestCase(1000, 2)]
		[TestCase(1500, 3)]
		[TestCase(2000, 4)]
		public void SharedMode_BothHalvesReadOneBelledTable_ShieldScaledOnce(
			int heaviness, int vectorIndex)
		{
			var warhead = LoadTs90Shared(heaviness);
			RulesetLoaded(warhead);

			var versus = EffectiveTable(warhead, "effectiveVersus");
			var pct = EffectiveTable(warhead, "effectivePercentageVersus");

			// The bell ran ONCE over the flat Versus (every non-Shield row matches the
			// Python-mirror vectors); the Shield row is then scaled ONCE half-up by
			// (2000 + h) / 2000 — authored 25 -> 25/31/38/44/50.
			foreach (var (armor, value) in Ts90Belled[vectorIndex])
			{
				var expected = armor == "Shield"
					? (int)((25L * (2000L + heaviness) + 1000L) / 2000L)
					: value;
				Assert.That(versus[armor], Is.EqualTo(expected),
					$"armor {armor} at h={heaviness / 1000.0}");
			}

			// The percentage half reads that SAME resulting table by reference —
			// never a second bell, never a second Shield scaling.
			Assert.That(pct, Is.SameAs(versus));
		}

		[Test]
		public void SharedMode_DisabledHeavinessFailsClearAtRulesLoad()
		{
			Assert.Throws<YamlException>(() => RulesetLoaded(LoadTs90Shared(-1)));
		}

		[Test]
		public void SharedMode_RejectsPercentageVersusTableAtRulesLoad()
		{
			var warhead = LoadTs90Shared(1000,
				Table("PercentageVersus", Ts90Authored));
			Assert.Throws<YamlException>(() => RulesetLoaded(warhead));
		}

		[Test]
		public void SharedMode_RejectsEndpointTablesAtRulesLoad()
		{
			var warhead = LoadTs90Shared(1000,
				Table("PercentageVersusLight", Ts90Authored),
				Table("PercentageVersusHeavy", Ts90Authored
					.Select(kv => (kv.Item1, kv.Item2 + 10)).ToArray()));
			Assert.Throws<YamlException>(() => RulesetLoaded(warhead));
		}

		[Test]
		public void SharedMode_RejectsMixedLegacyAndSharedConfiguration()
		{
			// Mixed config: shared mode + a folded percentage table (no endpoints)
			// is still a percentage-table reject — the mode cannot coexist with any
			// PercentageVersus* table.
			var warhead = LoadTs90Shared(1000,
				Table("PercentageVersus", ("None", 20), ("Flak", 35)));
			Assert.Throws<YamlException>(() => RulesetLoaded(warhead));
		}

		[Test]
		public void SharedMode_GeometryStillScalesConsistently()
		{
			var warhead = LoadTs90Shared(500);
			RulesetLoaded(warhead);
			Assert.That(Effective(warhead, "effectiveSpread"),
				Is.EqualTo(new WDist(500)));   // 600 x 5/6, unchanged by the mode
		}

		[Test]
		public void LegacyMode_IsTheDefaultAndKeepsPercentagesAnchored()
		{
			// The legacy identity: a DEFAULT-mode warhead authored like today's keeps
			// the anchored percentage table (h=1, authored Medium anchor -> the h=1 bell).
			var warhead = LoadTs90(1000);
			RulesetLoaded(warhead);
			Assert.That(EffectiveTable(warhead, "effectivePercentageVersus"),
				Is.Not.SameAs(EffectiveTable(warhead, "effectiveVersus")));
			Assert.That(EffectiveTable(warhead, "effectivePercentageVersus")["Heavy"],
				Is.EqualTo(19));
		}

		[Test]
		public void SharedMode_UnknownModeValueFailsAtFieldLoader()
		{
			// FieldLoader parses HeavinessMode as an enum: an unknown NAME can never
			// reach RulesetLoaded — it fails at load clear.
			Assert.Catch(() => Load<AreaDamageWarhead>(new[]
			{
				Field("Damage", "6000"),
				Field("HeavinessMode", "NotAMode"),
			}));
		}

		[Test]
		public void SharedMode_NumericUndefinedModeValueFailsClearAtRulesLoad()
		{
			// Review item 1: FieldLoader/Enum parsing ACCEPTS a numeric member
			// outside the enum, so the load-time Enum.IsDefined gate must reject it.
			Assert.Throws<YamlException>(() => RulesetLoaded(Load<AreaDamageWarhead>(new[]
			{
				Field("Damage", "6000"),
				Field("Heaviness", "1000"),
				Field("HeavinessMode", "7"),
				Field("PercentageScale", "2000"),
				Table("Versus", Ts90Authored),
			})));
		}

		[Test]
		public void SharedMode_PercentageOverflowFailsClearAtRulesLoad()
		{
			// Review item 2: Damage x Scale x h over Int32 is computed AT RULES LOAD.
			var warhead = Load<AreaDamageWarhead>(new[]
			{
				Field("Damage", "2000000000"),
				Field("Spread", "600"),
				Field("PercentageScale", "2000000000"),
				Field("Heaviness", "2000"),
				Field("HeavinessMode", "SharedVersus"),
				Table("Versus", Ts90Authored),
			});
			Assert.Throws<YamlException>(() => RulesetLoaded(warhead));
		}

		[Test]
		public void SharedMode_ShieldCoefficientOverflowFailsClearAtRulesLoad()
		{
			// Review item 2: the Shield scaling's final Int32 cast is checked —
			// Shield 2000000000 x 2 cannot round into Int32.
			var warhead = Load<AreaDamageWarhead>(new[]
			{
				Field("Damage", "6000"),
				Field("Spread", "600"),
				Field("PercentageScale", "2000"),
				Field("Heaviness", "2000"),
				Field("HeavinessMode", "SharedVersus"),
				Table("Versus", Ts90Authored.Select(kv =>
					(kv.Item1, kv.Item1 == "Shield" ? 2_000_000_000 : kv.Item2)).ToArray()),
			});
			Assert.Throws<OverflowException>(() => RulesetLoaded(warhead));
		}

		[TestCase("Damage", "")]
		[TestCase("PercentageScale", "-7000")]
		[TestCase("VersusNegativeShield", "")]
		public void SharedMode_NegativeInputsFailClearAtRulesLoadEvenAtH0(string kind, string value)
		{
			var fields = new List<MiniYamlNode>
			{
				Field("Heaviness", "0"),
				Field("HeavinessMode", "SharedVersus"),
				Field("PercentageScale", "2000"),
				Table("Versus", Ts90Authored),
				Field("Damage", "6000"),
			};
			if (kind == "Damage")
			{
				fields.RemoveAll(f => f.Key == "Damage");
				fields.Add(Field("Damage", "-6000"));
			}
			else if (kind == "PercentageScale")
			{
				fields.RemoveAll(f => f.Key == "PercentageScale");
				fields.Add(Field("PercentageScale", value));
			}
			else // negative Shield coefficient — still rejected at h = 0
			{
				fields.RemoveAt(fields.FindIndex(f => f.Key == "Versus"));
				fields.Add(Table("Versus", Ts90Authored
					.Select(kv => (kv.Item1, kv.Item1 == "Shield" ? -25 : kv.Item2)).ToArray()));
			}
			Assert.Throws<YamlException>(() => RulesetLoaded(
				Load<AreaDamageWarhead>(fields.ToArray())));
		}

		[Test]
		public void SharedMode_NumberOfPercentageUnitsFollowsScaleTimesHeaviness()
		{
			// The runtime RATIO: Scale 2000 + h=2 -> 2x the h=0 units (which are 0),
			// and Scale 10000 at h=2 -> Damage/2000 x 2 (0.20% per 100 damage). The
			// conversion itself is unit-tested in AreaDamageWarheadHeavinessTest.
			var h2000Scale2000 = AreaDamageWarhead.SharedFoldedPercentageUnits(2000, 2000, 2000);
			var h2000Scale10000 = AreaDamageWarhead.SharedFoldedPercentageUnits(2000, 10000, 2000);
			Assert.That(h2000Scale2000, Is.EqualTo(20));
			Assert.That(h2000Scale10000, Is.EqualTo(100));
		}

		[Test]
		public void Subclass_RejectsSharedVersusMode_UntilSupported()
		{
			var warhead = Load<AreaDamagePercentageWarhead>(
				Field("Damage", "20"),
				Field("Spread", "600"),
				Field("Heaviness", "1000"),
				Field("HeavinessMode", "SharedVersus"),
				Table("Versus", ("Heavy", 19), ("Light", 17), ("Scout", 16)));
			Assert.Throws<YamlException>(() => RulesetLoaded(warhead));
		}

	}
}
