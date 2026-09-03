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

using System.Linq;
using OpenRA.Mods.AS.Traits;
using OpenRA.Mods.Common.Traits;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[Desc("An ARMOR PLATING pool — the middle layer of Cameo's Shield -> Integrity -> Armor",
		"-> Health stack (BALANCE_PROGRAM_PLAN W21). Absorbs damage that would otherwise reach",
		"HEALTH, and protects nothing else: an intact shield stops everything, Integrity eats",
		"electrical damage, and this bar only stands between what is left and the health pool.",
		"",
		"Every 'this unit is tougher now' effect in Cameo is meant to be one of these, granted",
		"as a CONDITIONAL trait — cyborgs and droids carry one from the start, upgrades and",
		"veterancy add more, and they stack additively. That is the R1 law: 1 HP is 1 HP, so",
		"toughness is a visible bar rather than an invisible DamageMultiplier.",
		"",
		"Pair FullCondition/EmptyCondition with conditional Armor traits to make the ACTIVE",
		"layer decide the Versus lookup — that is what stops two armor types multiplying.")]
	public class ArmorPlatingInfo : PausableConditionalTraitInfo
	{
		[Desc("Pool as a FLAT amount of damage absorbed. Added to MaxPercentageStrength.")]
		public readonly int MaxStrength = 0;

		[Desc("Pool as a PERCENTAGE of the actor's max health. Added to MaxStrength.",
			"W21 R6: 50 for a unit that starts with plating or gains a full bar from an",
			"upgrade; smaller additive grants stack on top of it.")]
		public readonly int MaxPercentageStrength = 50;

		[Desc("Flat pool the actor starts with. -1 means start at the maximum.")]
		public readonly int InitialStrength = -1;

		[Desc("Flat amount repaired each interval, once the ramp is at full rate.",
			"Added to PercentageRegenAmount — set one of the two to 0 unless both are wanted.")]
		public readonly int RegenAmount = 0;

		[Desc("Percentage OF THE MAXIMUM pool repaired each interval, once the ramp is at full",
			"rate. Added to RegenAmount (see above).")]
		public readonly int PercentageRegenAmount = 0;

		[Desc("Ticks between repair steps.")]
		public readonly int RegenInterval = 25;

		[Desc("W21 R7 — the RAMP. Repair rate scales with how long the actor has gone undamaged:",
			"rate = base * min(1, ticks_since_damage / RampTicks), so a unit under fire repairs",
			"nothing and one left alone winds up to full rate. 125 for armor (health uses 25, or",
			"50 for infantry; shields use 250). Set 0 to disable the ramp and repair at full rate",
			"immediately.")]
		public readonly int RampTicks = 125;

		[Desc("Damage types this plating does NOT absorb — they pass straight through to health.",
			"Leave empty and the plating absorbs everything that reaches it.")]
		public readonly BitSet<DamageType> BypassDamageTypes = default;

		[GrantedConditionReference]
		[Desc("Condition granted while the plating still has strength left. Gate an Armor trait",
			"on this to give the plating its own armor TYPE.")]
		public readonly string FullCondition = null;

		[GrantedConditionReference]
		[Desc("Condition granted while the plating is depleted. Gate the actor's BODY Armor trait",
			"on this so exactly one armor type is ever enabled — otherwise the engine MULTIPLIES",
			"them and squares the weapon's profile (see W20).")]
		public readonly string EmptyCondition = null;

		public readonly bool ShowSelectionBar = true;

		[Desc("Hide the bar while the plating is at full strength, so an undamaged unit shows",
			"no plating bar. This is what makes the layer honour the player's",
			"'Show Status Bars: On Damage' setting — the renderer draws an extra bar whenever",
			"its value is non-zero, so a bar that reports full is a bar that is always on screen.")]
		public readonly bool HideBarWhenFull = true;

		[Desc("W21 R13: armor reads yellow-orange, distinct from the health bar and the shield's purple.")]
		public readonly Color SelectionBarColor = Color.FromArgb(255, 176, 64);

		public override object Create(ActorInitializer init) { return new ArmorPlating(init, this); }
	}

	public class ArmorPlating : PausableConditionalTrait<ArmorPlatingInfo>, ITick, ISync,
		ISelectionBar, IDamageModifier, INotifyDamage, ITransformActorInitModifier
	{
		// Resolved in Created(), NOT in the constructor. Traits are constructed in declaration
		// order, so TraitOrDefault<Health>() from a constructor returns null whenever Health
		// happens to be registered later — and a null health means MaxStrength collapses to
		// Info.MaxStrength (0 by default), the plating starts empty, EmptyCondition fires
		// immediately, and the whole layer silently does nothing. Created() runs after every
		// trait exists, so the lookup is always valid there.
		Health health;

		// The layer directly outside this one. W21's stack is SEQUENTIAL — Shield ->
		// Integrity -> Armor -> Health — and this reference is what enforces it.
		Shielded shield;

		// An actor can carry SEVERAL ArmorPlating traits — innate plating plus an upgrade that
		// grants more (Schwarzer Mond's noid walkers plus Lunar Alloys, say). W21 R6 says those
		// stack ADDITIVELY, and the maintainer does not want one bar per source, so the FIRST
		// trait on the actor OWNS the single pool, bar and conditions; every other one only
		// contributes its size while enabled and is otherwise inert. A contributor enabling
		// mid-game (the upgrade completing) grows the pool AND hands over that much strength
		// immediately, so researching an upgrade visibly plates the units you already own.
		ArmorPlating[] contributors;
		ArmorPlating owner;
		bool contributed;
		bool IsOwner => owner == this;

		[VerifySync]
		public int Strength { get; private set; }

		public int MaxStrength { get; private set; }

		int regenTicks;
		int ticksSinceDamage;
		int fullToken = Actor.InvalidConditionToken;
		int emptyToken = Actor.InvalidConditionToken;

		// The pre-modifier damage, stashed by GetDamageModifier so Damaged() can charge the
		// pool at FULL PRECISION. AS's Shielded instead recovers the value by dividing the
		// 1%-scaled result by 0.01, which is integer-lossy: a 5032 hit becomes 50 and comes
		// back as 5000, forgiving up to 99 damage per hit, and anything under 100 damage
		// scales to 0 and costs the shield nothing at all. That matters most for exactly the
		// small hits this stack now has to absorb — DoT ticks, physical-state chip damage and
		// %-twin damage (W21 R9). Stashing the real number avoids the round trip entirely.
		int pendingDamage;

		// ⭐ CARRIED ACROSS A TRANSFORM AS A PERCENTAGE, exactly the way health is.
		// `Transform.cs` does `newHP = health.HP * 100 / health.MaxHP` and passes a HealthInit,
		// so a half-dead MCV deploys into a half-dead construction yard even though the two
		// actors have completely different MaxHP. A percentage is the only thing that means
		// anything across two actors, and it is equally the right unit for a toggle: the pool
		// can be a different size on the way back in (another contributor enabled meanwhile).
		public ArmorPlating(ActorInitializer init, ArmorPlatingInfo info)
			: base(info)
		{
			retainedPercentage = init.GetOrDefault<ArmorPlatingInit>()?.Value;
		}

		void ITransformActorInitModifier.ModifyTransformActorInit(Actor self, TypeDictionary init)
		{
			// Only the owner holds the pool, so only the owner reports it — ArmorPlatingInit is
			// ISingleInstanceInit and a second Add would throw on a multi-source actor.
			if (!IsOwner || MaxStrength <= 0)
				return;

			init.Add(new ArmorPlatingInit((int)(Strength * 100L / MaxStrength)));
		}

		protected override void Created(Actor self)
		{
			health = self.TraitOrDefault<Health>();
			shield = self.TraitOrDefault<Shielded>();
			contributors = self.TraitsImplementing<ArmorPlating>().ToArray();
			owner = contributors[0];

			// Before base.Created, which is what fires TraitEnabled for an unconditional
			// trait (ConditionalTrait.cs:63) — TraitEnabled sets Strength from MaxStrength,
			// so MaxStrength has to be real by then.
			RecalculateMax();
			base.Created(self);
		}

		int PoolOf(ArmorPlating p)
		{
			var fromHealth = health != null ? p.Info.MaxPercentageStrength * health.MaxHP / 100 : 0;
			return p.Info.MaxStrength + fromHealth;
		}

		void RecalculateMax()
		{
			if (!IsOwner)
			{
				MaxStrength = 0;
				return;
			}

			// Count a source only once it has actually reported in (TraitEnabled), never from
			// IsTraitDisabled: the owner's Created() runs BEFORE a later contributor's, so
			// reading the flag there and adding the delta here would count the same pool twice.
			// The owner counts itself the same way as everyone else — ownership is POSITIONAL
			// (whoever the trait dictionary lists first) and says nothing about whether that
			// particular source is switched on.
			MaxStrength = 0;
			foreach (var c in contributors)
				if (c.contributed)
					MaxStrength += PoolOf(c);
		}

		// A source switching on or off. Grow/shrink the shared pool by exactly that source's
		// size and move Strength with it, so an upgrade grants its plating immediately
		// instead of waiting for the regen to fill the new headroom.
		void PoolChanged(Actor self, int delta)
		{
			RecalculateMax();
			Strength = (Strength + delta).Clamp(0, MaxStrength);
			UpdateConditions(self);
		}

		// Conditions are per-SOURCE, driven by the shared pool. The owner is whichever
		// ArmorPlating the trait dictionary happens to list first — on the noid walkers that
		// is the conditional Lunar Alloys grant, whose Info carries no FullCondition at all —
		// so reading conditions off the owner alone would leave `plating_up` ungranted and
		// silently kill the armor-type swap. Every source publishes its OWN conditions.
		void UpdateConditions(Actor self)
		{
			var hasPlating = owner.Strength > 0;
			foreach (var c in contributors)
				c.UpdateOwnConditions(self, hasPlating);
		}

		void UpdateOwnConditions(Actor self, bool hasPlating)
		{
			// A source that is switched off publishes nothing: an unresearched upgrade must
			// not claim the unit is plated just because some other source filled the pool.
			if (hasPlating && contributed)
			{
				if (emptyToken != Actor.InvalidConditionToken)
					emptyToken = self.RevokeCondition(emptyToken);

				if (fullToken == Actor.InvalidConditionToken && !string.IsNullOrEmpty(Info.FullCondition))
					fullToken = self.GrantCondition(Info.FullCondition);
			}
			else
			{
				if (fullToken != Actor.InvalidConditionToken)
					fullToken = self.RevokeCondition(fullToken);

				if (emptyToken == Actor.InvalidConditionToken && contributed
					&& !string.IsNullOrEmpty(Info.EmptyCondition))
					emptyToken = self.GrantCondition(Info.EmptyCondition);
			}
		}

		// Every guard below tests IsOwner and the POOL, never this instance's own enabled
		// state: the owner is positional, so a disabled owner with an enabled contributor
		// still has real plating to regenerate, absorb with and draw.
		void ITick.Tick(Actor self)
		{
			if (!IsOwner || IsTraitPaused || MaxStrength == 0)
				return;

			if (ticksSinceDamage < int.MaxValue)
				ticksSinceDamage++;

			if (Strength >= MaxStrength || --regenTicks > 0)
				return;

			regenTicks = Info.RegenInterval;

			var step = Info.RegenAmount + Info.PercentageRegenAmount * MaxStrength / 100;
			if (step <= 0)
				return;

			// W21 R7: the ramp. Integer maths deliberately — a unit still under fire gets 0.
			if (Info.RampTicks > 0 && ticksSinceDamage < Info.RampTicks)
				step = step * ticksSinceDamage / Info.RampTicks;

			if (step <= 0)
				return;

			Strength = (Strength + step).Clamp(0, MaxStrength);
			UpdateConditions(self);
		}

		int IDamageModifier.GetDamageModifier(Actor attacker, Damage damage)
		{
			if (!Absorbs(damage))
				return 100;

			// 1, never 0: a hit scaled to nothing fires no damage event, so Damaged() would
			// never run and the plating would absorb the shot for free. The 1% that leaks
			// through is healed back below.
			pendingDamage = damage.Value;
			return 1;
		}

		// ⚠ TWO INTERCEPTING LAYERS MUST NEVER SHARE A HIT. Both Shielded and this trait
		// absorb by returning damage modifier 1 — i.e. "let 1% through, then heal it back".
		// The engine MULTIPLIES damage modifiers, so if both fire the hit is scaled to
		// 1% x 1% = 0.01%, and each layer then recovers its "original" from that and
		// charges its pool roughly 1% of the real damage. The unit becomes effectively
		// immortal: observed in play 2026-08-15, a shielded and plated noid walker under a
		// whole army's focus fire dropped from 125 shield to 124 for a split second.
		//
		// So the stack is enforced here: while the SHIELD still holds, the plating is not
		// the outermost layer and stands completely down.
		//
		// ⚠ Known gap, matching how Shielded already behaves: when a shield BREAKS, its
		// excess damage cascades straight to health rather than into the plating, because
		// Shielded does that cascade itself and knows nothing about this layer.
		bool ShieldHolds => shield != null && !shield.IsTraitDisabled && shield.Strength > 0;

		bool Absorbs(Damage damage)
		{
			return IsOwner && !ShieldHolds && Strength > 0 && damage.Value > 0
				&& !(!Info.BypassDamageTypes.IsEmpty && damage.DamageTypes.Overlaps(Info.BypassDamageTypes));
		}

		void INotifyDamage.Damaged(Actor self, AttackInfo e)
		{
			// ShieldHolds mirrors Absorbs: if the shield took this hit, GetDamageModifier
			// never stashed anything and there is nothing here to charge.
			if (!IsOwner || ShieldHolds || Strength == 0 || e.Damage.Value <= 0 || e.Attacker == self)
				return;

			if (!Info.BypassDamageTypes.IsEmpty && e.Damage.DamageTypes.Overlaps(Info.BypassDamageTypes))
				return;

			ticksSinceDamage = 0;

			// Recover what the actor WOULD have taken without this layer.
			//
			// The stashed pre-modifier value is exact, but it ignores every OTHER damage
			// modifier on the actor (a promotion's DamageMultiplier, say) — using it blindly
			// would make plating absorb the unreduced hit and deplete too fast. So: if the
			// engine's result is exactly this trait's own 1% of the stash, nothing else
			// modified the damage and the exact value is safe. Otherwise something else had a
			// say, and undoing only our own 1% (x100) preserves it, at the cost of the integer
			// residue Shielded always pays.
			//
			// R1 abolishes DamageMultiplier, after which the exact branch is the only one that
			// ever runs — but this must be correct BEFORE that pass lands, not after.
			var mineOnly = pendingDamage / 100;
			var incoming = pendingDamage > 0 && e.Damage.Value == mineOnly
				? pendingDamage
				: e.Damage.Value * 100;
			pendingDamage = 0;

			var excess = incoming - Strength;
			Strength = (Strength - incoming).Clamp(0, MaxStrength);

			// Undo the 1% that reached health while the plating was standing.
			if (health != null && e.Damage.Value > 0)
				health.InflictDamage(self, self,
					new Damage(-e.Damage.Value, e.Damage.DamageTypes, e.Damage.ProjectileType), true);

			// W21 R3: damage always cascades into the next layer in the same shot.
			if (excess > 0 && health != null)
				health.InflictDamage(self, e.Attacker,
					new Damage(excess, e.Damage.DamageTypes, e.Damage.ProjectileType), true);

			UpdateConditions(self);
		}

		// ⛔ TOGGLING A SOURCE OFF AND ON MUST NOT REFILL THE BAR.
		//
		// Maintainer 2026-08-22: *"if undeploying and deploying gives instantly a full shield
		// this is an exploit ... quickly undeploying and redeploying can instantly refill your
		// armor bar for unlimited armor."* Exactly right, and it was true here: TraitEnabled
		// granted `pool` unconditionally, so disable -> enable ran
		//
		//     Strength = (10 - P).Clamp(0, 0) = 0        then  (0 + P).Clamp(0, P) = P
		//
		// i.e. a full bar for the price of two key presses. It also reset the owner's regen
		// ramp, so the RampTicks wait was skipped for free on top.
		//
		// ⚠ Not reachable in the CURRENT tree — all 39 ArmorPlating actors gate on
		// `schwarzermond_upgrade_lunaralloys`, a one-way research upgrade — but it goes live the
		// moment plating is granted on anything a player can toggle, which is precisely what a
		// deploy-granted plating would be.
		//
		// The fix is to remember what this source had, AS A PERCENTAGE — null until either a
		// transform hands one over or this source is disabled, so a genuine first grant still
		// yields a full bar and a fresh ramp.
		int? retainedPercentage;

		// Distinct from `retainedPercentage`: a transformed actor arrives with a percentage but
		// has never been enabled, and should still get a fresh regen ramp.
		bool hasBeenEnabled;

		// Uniform for every source, owner or not: report in, hand the pool this source's
		// worth of plating, let the owner do the arithmetic.
		protected override void TraitEnabled(Actor self)
		{
			contributed = true;

			var pool = PoolOf(this);
			var granted = retainedPercentage != null
				? (int)(pool * (long)retainedPercentage.Value / 100)
				: (Info.InitialStrength < 0 ? pool : Info.InitialStrength);
			granted = granted.Clamp(0, pool);

			// Only a FIRST enable resets the ramp. Resetting it on every re-enable would hand
			// back the skipped regen delay even once the strength itself is preserved, and the
			// ramp lives on the OWNER, so one contributor toggling would clear it for all.
			if (!hasBeenEnabled)
			{
				owner.regenTicks = owner.Info.RegenInterval;
				owner.ticksSinceDamage = owner.Info.RampTicks;
			}

			hasBeenEnabled = true;
			owner.PoolChanged(self, granted);
		}

		protected override void TraitDisabled(Actor self)
		{
			var was = contributed ? PoolOf(this) : 0;

			// ⚠ The pool is SHARED and damage is not attributed to a source, so "what was left
			// of mine" has to be apportioned: this source's share of the surviving strength, by
			// its share of the maximum. With a single source that is just the current strength;
			// with several it splits a partly-drained pool proportionally instead of letting
			// one source claim all the survivors or none of them.
			var share = owner.MaxStrength > 0
				? (int)((long)owner.Strength * was / owner.MaxStrength)
				: 0;
			retainedPercentage = was > 0 ? (int)(share * 100L / was) : 0;

			contributed = false;

			// ⚠ REMOVE THE SHARE, NOT THE WHOLE CONTRIBUTION — and this also fixes a bug that
			// predates the refill one. `-was` takes the source's FULL size out of a pool that
			// may be half drained, so it eats the OTHER sources' surviving strength: with a
			// 600 owner + 400 contributor drained to 500, disabling the contributor left 100
			// when the owner's own share was 300. Removing the same proportional share that
			// gets handed back makes a toggle round-trip exactly (500 -> 300 -> 500 instead of
			// 500 -> 100 -> 300), which is what "no free armour, no stolen armour" requires.
			owner.PoolChanged(self, -share);
		}

		float ISelectionBar.GetValue()
		{
			// Contributors report nothing: one pool, one bar, however many sources feed it.
			if (!IsOwner || !Info.ShowSelectionBar || MaxStrength == 0)
				return 0f;

			// Reporting 0 is how an extra bar hides: the renderer draws it when the value is
			// non-zero OR DisplayWhenEmpty is set (IsometricSelectionBarsAnnotationRenderable
			// .DrawExtraBars). An intact plating that reported its full value would sit on
			// screen permanently, ignoring 'Show Status Bars: On Damage'.
			if (Info.HideBarWhenFull && Strength >= MaxStrength)
				return 0f;

			return (float)Strength / MaxStrength;
		}

		// False, so a plating stripped to nothing stops drawing an empty bar too. R13's "all
		// three bars are always visible" means visible to EVERY player, not visible at every
		// moment — an undamaged unit should show no damage bars at all.
		bool ISelectionBar.DisplayWhenEmpty => false;

		Color ISelectionBar.GetColor() { return Info.SelectionBarColor; }
	}

	// Percentage (0-100) of the plating pool an actor starts with, mirroring HealthInit's
	// contract. Emitted by Transform via ITransformActorInitModifier so a damaged MCV deploys
	// into a construction yard with the same FRACTION of plating it had, not a full bar.
	public class ArmorPlatingInit : ValueActorInit<int>, ISingleInstanceInit
	{
		public ArmorPlatingInit(int value)
			: base(value) { }
	}
}
