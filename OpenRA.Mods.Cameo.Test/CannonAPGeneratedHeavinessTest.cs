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
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using NUnit.Framework;
using OpenRA.GameRules;
using OpenRA.Mods.Cameo.Warheads;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Test
{
	/// <summary>
	/// END-TO-END generator / runtime-adapter proof for the ACTUAL generated
	/// CannonAP continuous base — NOT a hand-picked table and NOT a balance claim.
	/// The expected values ("effectiveVersus" / "effectivePercentageVersus" / radii)
	/// come entirely from the committed fixture JSON (tools/tests/fixtures/
	/// cannonap_continuous_fixture.json), built by the Python model from the
	/// generator's stdout parsed through the SHARED miniyaml. The expected tables
	/// are never recomputed inside C#; this class only parses the real generated
	/// YAML with the engine's MiniYaml reader, loads the real AreaDamageWarhead
	/// through FieldLoader, invokes the real IRulesetLoaded&lt;WeaponInfo&gt;.RulesetLoaded,
	/// and compares the private effective fields against the fixture.
	/// </summary>
	[TestFixture]
	public sealed class CannonAPGeneratedHeavinessTest
	{
		static string FixtureBase()
		{
			return Path.Combine(AppContext.BaseDirectory, "tools", "tests", "fixtures");
		}

		static JsonElement FixtureRoot()
		{
			var json = File.ReadAllText(Path.Combine(FixtureBase(),
				"cannonap_continuous_fixture.json"));
			using var document = JsonDocument.Parse(json);
			return document.RootElement.Clone();
		}

		static MiniYamlNode WarheadNodeFromGeneratedYaml()
		{
			var text = File.ReadAllText(Path.Combine(FixtureBase(),
				"cannonap_continuous_generated.yaml"));
			var nodes = MiniYaml.FromString(text, "cannonap_generated_fixture");
			var weapon = nodes.First(n => n.Key == "^Warhead_CannonAP");
			foreach (var child in weapon.Value.Nodes)
				if (child.Key.StartsWith("Warhead@"))
					return child;
			Assert.Fail("generated block carries no Warhead@ child");
			return null;
		}

		static AreaDamageWarhead LoadHeaviness(MiniYamlNode warheadNode, int heaviness)
		{
			var fields = new List<MiniYamlNode>();
			foreach (var field in warheadNode.Value.Nodes)
			{
				if (field.Key == "Heaviness")
					continue;
				if (heaviness < 0 && field.Key == "HeavinessMode")
					continue;
				fields.Add(field);
			}

			if (heaviness >= 0)
			{
				// Active: keep HeavinessMode (the SHARED PROFILE opt-in) and set
				// the scalar.
				fields.Add(new MiniYamlNode("Heaviness", new MiniYaml(heaviness.ToString())));
			}
			else
			{
				// Disabled = the LEGACY mode (SharedVersus requires an active
				// Heaviness and is rejected with the sentinel): keep authored
				// tables verbatim + the negative sentinel.
				fields.Add(new MiniYamlNode("HeavinessMode", new MiniYaml("Legacy")));
				fields.Add(new MiniYamlNode("Heaviness", new MiniYaml("-1")));
			}

			var warhead = new AreaDamageWarhead();
			FieldLoader.Load(warhead, new MiniYaml(warheadNode.Value.Value, fields));
			((IRulesetLoaded<WeaponInfo>)warhead).RulesetLoaded(null, null);
			return warhead;
		}

		static IReadOnlyDictionary<string, int> EffectiveTable(object warhead, string name)
		{
			return (IReadOnlyDictionary<string, int>)typeof(AreaDamageWarhead)
				.GetField(name, BindingFlags.Instance | BindingFlags.NonPublic)!
				.GetValue(warhead)!;
		}

		static void AssertTable(JsonElement expected, IReadOnlyDictionary<string, int> effective,
			string label)
		{
			Assert.That(effective.Count, Is.EqualTo(expected.EnumerateObject().Count()), label);
			foreach (var armor in expected.EnumerateObject())
				Assert.That(effective[armor.Name], Is.EqualTo(armor.Value.GetInt32()),
					$"{label}: armor {armor.Name}");
		}

		static void AssertGeometry(JsonElement expected, object warhead)
		{
			Assert.That(Effective(warhead, "effectiveSpread"), Is.EqualTo(
				new WDist(expected.GetProperty("effective_spread").GetInt32())));

			var range = (ImmutableArray<WDist>)Effective(warhead, "effectiveRange")!;
			var expectedRange = expected.GetProperty("effective_range")
				.EnumerateArray().Select(v => v.GetInt32()).ToArray();
			Assert.That(range.Select(r => r.Length).ToArray(), Is.EqualTo(expectedRange),
				"effectiveRange (derived from Falloff x Spread)");

			Assert.That(Effective(warhead, "effectiveMinRadius"), Is.EqualTo(
				new WDist(expected.GetProperty("effective_min_radius").GetInt32())));
			Assert.That(Effective(warhead, "effectiveMaxRadius"), Is.EqualTo(
				new WDist(expected.GetProperty("effective_max_radius").GetInt32())));
		}

		static object Effective(object warhead, string name)
		{
			return typeof(AreaDamageWarhead).GetField(name,
				BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(warhead);
		}

		[TestCase(0)]
		[TestCase(500)]
		[TestCase(1000)]
		[TestCase(1500)]
		[TestCase(2000)]
		public void Generated_ActiveHeaviness_EffectiveFieldsMatchFixture(int heaviness)
		{
			var fixture = FixtureRoot();
			var expected = fixture.GetProperty("per_heaviness").GetProperty(heaviness.ToString());
			var warhead = LoadHeaviness(WarheadNodeFromGeneratedYaml(), heaviness);

			AssertTable(expected.GetProperty("effective_versus"),
				EffectiveTable(warhead, "effectiveVersus"),
				$"effectiveVersus at h={heaviness / 1000.0}");
			AssertTable(expected.GetProperty("effective_percentage_versus"),
				EffectiveTable(warhead, "effectivePercentageVersus"),
				$"effectivePercentageVersus at h={heaviness / 1000.0}");
			AssertGeometry(expected, warhead);
		}

		[Test]
		public void Generated_DisabledWithoutAnchors_KeepsAuthoredTablesAndGeometryVerbatim()
		{
			var fixture = FixtureRoot();
			var expected = fixture.GetProperty("disabled");
			var warhead = LoadHeaviness(WarheadNodeFromGeneratedYaml(), -1);

			AssertTable(expected.GetProperty("effective_versus"),
				EffectiveTable(warhead, "effectiveVersus"), "disabled effectiveVersus");
			AssertTable(expected.GetProperty("effective_percentage_versus"),
				EffectiveTable(warhead, "effectivePercentageVersus"),
				"disabled effectivePercentageVersus");
			AssertGeometry(expected, warhead);
		}

		[Test]
		public void Generated_FixtureCarriesShieldPlatingAndDerivedArmors()
		{
			// The fixture's expected tables cover each ACTUAL armor key, including
			// Shield, the five platings and the derived Heroic (Airborne is NOT in
			// the generated table — documented in the fixture assertions).
			var fixture = FixtureRoot();
			var authored = fixture.GetProperty("authored");
			foreach (var armor in new[]
			{
				"Shield", "HAZMAT", "COMPOSITE", "BLAST", "REFLECTOR", "ARMOR",
				"Heroic", "Superheavy", "Fighter", "Scout",
			})
				Assert.That(authored.GetProperty("Versus").TryGetProperty(armor, out _),
					Is.True, $"authored Versus key {armor}");
			Assert.That(authored.GetProperty("Versus").EnumerateObject().Count(),
				Is.EqualTo(22));
		}
	}
}
