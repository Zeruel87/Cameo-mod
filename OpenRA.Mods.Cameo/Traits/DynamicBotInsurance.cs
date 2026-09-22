#region Copyright & License Information

/*
 * Copyright 2007-2020 The OpenRA Developers (see AUTHORS)
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */

#endregion

using System;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Traits
{
	[Desc("Bot anti-bankruptcy income, as ONE trait on the Player actor with ONE dynamic threshold",
		"and ONE dynamic delay, scaled automatically by the owner's bot difficulty name.",
		"",
		"Replaces the ten-rung ladder of BotInsurance + CashTrickler + ResourcePurifier that used to",
		"sit on ^AIConyardCash. That ladder had three problems this trait exists to fix:",
		"  1. it needed ten near-identical trait triples and ten hand-maintained condition lists,",
		"     one of which was wrong for months (`normalbot`) so `medium` bots got nothing at all;",
		"  2. it lived on the CONSTRUCTION YARD, so it multiplied by conyard count -- a late-game",
		"     snowball -- and switched off entirely when a bot lost its last conyard, which is the",
		"     exact 'stuck with no income' case the feature exists to prevent;",
		"  3. its thresholds and delays were fixed numbers that ignored how the economy was actually",
		"     going.",
		"",
		"The ore-purifier bonus is folded in here too, so the whole mechanic is one Cameo-owned",
		"trait rather than three traits from three assemblies.")]
	public class DynamicBotInsuranceInfo : TraitInfo
	{
		[Desc("Bot type names, EASIEST FIRST. The owner's bot type is looked up here and its INDEX",
			"drives every scaled value below, so adding a difficulty needs no new traits and no new",
			"conditions -- just another name in this list. A non-bot owner, or a bot type absent",
			"from this list (`campaign`, deliberately), gets nothing at all.")]
		public readonly string[] Difficulties =
		{
			"easiest", "veryeasy", "easy", "medium", "hard",
			"veryhard", "brutal", "challenger", "unbeatable", "cameogod"
		};

		[Desc("Ticks of liquid-funds history used for the rolling average that sets the delay and the",
			"threshold floor. ⚠ 1500 ticks is ONE MINUTE at the mod's default 40ms timestep",
			"(mod.yaml GameSpeeds/default); it is not 3000.")]
		public readonly int AverageWindow = 1500;

		[Desc("Ceiling on the dynamic threshold, AND the total liquid funds level at which a payout stops.",
			"The bar never rises above this, so an owner richer than this is never insured, and a",
			"payout runs until the owner reaches it.",
			"",
			"⚠ ONE NUMBER DOES BOTH JOBS ON PURPOSE. A ceiling above the payout exit would let an",
			"owner qualify and then immediately stop paying -- churn with no benefit. Raising this",
			"is a real balance decision: at 20000 a bot sitting on 18000 credits is insured, which",
			"is a subsidy, not insurance. Measured with tools/balance/bot_insurance_model.py.")]
		public readonly int MaxThreshold = 10000;

		[Desc("Absolute poverty line: below this total liquid funds level the owner is insured whatever its history says.",
			"",
			"⛔ MUST BE GREATER THAN ZERO. The trigger is STRICTLY `liquidity < threshold`, and the bar",
			"tracks the rolling average -- so a persistently broke owner drives its own average to",
			"zero, the bar follows it to zero, and `liquidity < 0` is unsatisfiable. With a floor of 0 a",
			"bankrupt bot is stranded forever, which is the exact failure this trait exists to",
			"prevent. Verified in test_a_zero_floor_strands_a_bankrupt_bot.")]
		public readonly int MinThreshold = 1000;

		[Desc("Threshold tracking rate per tick for the EASIEST difficulty.",
			"",
			"The bar is a SLEW-LIMITED TRACKER of the rolling average: it moves up when the average",
			"is above it and down when below, by at most this much per tick, in either direction.",
			"",
			"⛔ IT IS NOT A ONE-WAY RAMP AND NOT A FALLING BAR. A bar falling from MaxThreshold (the",
			"first design tried) is dead mechanics: `liquidity < threshold` is EASIEST to satisfy at the",
			"highest bar, so a falling bar fires on tick one for anyone under MaxThreshold and only",
			"ever makes triggering harder afterwards -- simulated, every difficulty behaved",
			"identically and all the ordering came from the delay divisor instead.",
			"",
			"⚠ HONEST LIMIT: even tracking both ways, this is the WEAKEST of the three difficulty",
			"knobs. The trigger fires as soon as liquid funds dip below the tracked average, so convergence",
			"speed rarely gates anything; MinDelayDivisor/MaxDelayDivisor and MinCashPerTick/",
			"MaxCashPerTick are what actually separate the difficulties. If this needs more bite,",
			"the lever is AverageWindow, not this rate.")]
		public readonly int MinThresholdRatePerTick = 1;

		[Desc("Threshold tracking rate per tick for the HARDEST difficulty. Interpolated by index.")]
		public readonly int MaxThresholdRatePerTick = 10;

		[Desc("Delay divisor for the EASIEST difficulty: delay ticks = rolling average / divisor.",
			"An average of 1500 therefore waits 150 ticks (6 seconds) at the easiest setting.")]
		public readonly int MinDelayDivisor = 10;

		[Desc("Delay divisor for the HARDEST difficulty. Larger divisor = shorter wait, so the",
			"hardest bots react roughly ten times faster than the easiest ones.")]
		public readonly int MaxDelayDivisor = 100;

		[Desc("Hard floor on the computed delay, so a bot with zero liquid funds still waits a moment.")]
		public readonly int MinDelayTicks = 25;

		[Desc("Hard ceiling on the computed delay, so a very rich average cannot park the delay",
			"beyond any useful horizon.")]
		public readonly int MaxDelayTicks = 1500;

		[Desc("PEAK credits per tick for the EASIEST difficulty — the rate paid at zero liquid funds.",
			"⚠ 1 credit/tick is exactly one buildable oil derrick (Interval 250 / Amount 250).",
			"",
			"⭐ THE PAYOUT IS PROPORTIONAL TO DEPTH, NOT FLAT. This is where the old ten-rung",
			"ladder's granularity lived: the rungs STACKED, so a `cameogod` bot drew 1 credit/tick",
			"just under 10000 and 10 credits/tick near zero. A flat on/off payout throws that away",
			"and hands the hardest bot its maximum for the whole time it is insured. Scaling by",
			"depth reproduces the old ladder rung for rung (cameogod: 9000 -> 1/tick, 5000 -> 5,",
			"0 -> 10) and then keeps going smoothly BETWEEN the old rungs.")]
		public readonly int MinCashPerTick = 1;

		[Desc("PEAK credits per tick for the HARDEST difficulty, at zero liquid funds.")]
		public readonly int MaxCashPerTick = 10;

		[Desc("Percentage of resource value delivered WHILE paying, granted as bonus cash for the",
			"EASIEST difficulty. This is the ore-purifier half, folded in.")]
		public readonly int MinPurifierModifier = 5;

		[Desc("Purifier percentage for the HARDEST difficulty.")]
		public readonly int MaxPurifierModifier = 50;

		[Desc("Minimum resources banked before the purifier bonus is released, as in ResourcePurifierCA.")]
		public readonly int PurifierMinAmount = 250;

		[Desc("Percent of PlayerStatistics.ArmyValue added ON TOP of AssetsValue when valuing the",
			"owner.",
			"",
			"⛔ ZERO ON PURPOSE. `PlayerStatistics` exposes both, and whether `AssetsValue` already",
			"counts combat units could not be settled from a container without the Common assembly",
			"vendored. At 0 the army is counted exactly once, through AssetsValue. If a real game",
			"shows AssetsValue EXCLUDES the army, raise this to 100 — but do not guess, because a",
			"wrong value double-counts the largest term in the whole calculation.")]
		public readonly int ArmyValueWeight = 0;

		[Desc("Floor, in permille, under `worth / my own peak worth`. Stops a total collapse",
			"dividing by roughly nothing.")]
		public readonly int MinSelfRatio = 100;

		[Desc("Clamp, in permille, on `worth / par curve` BEFORE it is combined.",
			"",
			"⚠ The par curve's magnitudes are invented, not measured. Clamping its ratio means even",
			"a badly calibrated curve can only move the combined figure by about sqrt(0.5) = 0.71x,",
			"instead of dominating it. Widen these only once real match data says the curve is right.")]
		public readonly int ParRatioMin = 500;

		[Desc("Upper clamp on the par ratio, in permille.")]
		public readonly int ParRatioMax = 2000;

		[Desc("Floor, in permille, under the worth factor. A bot that is wealthy on paper but has no",
			"liquid funds still gets SOME help: assets it cannot sell do not rebuild a base.")]
		public readonly int MinWorthFactor = 250;

		[Desc("Whether the par curve contributes at all. Disabled by default until measured match data",
			"can replace its provisional magnitudes. With it off, distress is measured purely against",
			"the owner's own peak, which is fully fog-safe and needs no external calibration.")]
		public readonly bool UseParCurve = false;

		[Desc("The par curve's SHAPE: permille of the way from ParBaseWorth to the asymptote,",
			"sampled every ParShapeStep permille of the midpoint, interpolated linearly between.",
			"",
			"⛔ A TABLE, NOT A FORMULA, AND THAT IS THE POINT. This feeds a synced value in a",
			"simulation OpenRA replays in lockstep across machines. `Math.Exp` is not guaranteed",
			"bit-identical across platforms or runtimes, so evaluating a logistic live is a desync",
			"waiting for a multiplayer game. Sampling it at authoring time makes the curve integer",
			"arithmetic end to end.",
			"⭐ And it makes the economy model a yaml array, so retuning it needs no rebuild.",
			"Default: the logistic k*t0 = 5.4 from tools/balance/bot_difficulty_curve.py. Index 4 is",
			"the midpoint (index 8) and reads 498 — half way, as a sigmoid must. The 0.125x step is",
			"not cosmetic: at 0.25x, interpolating across the steepest stretch diverged 22.5% from the",
			"logistic it was sampled from.")]
		public readonly int[] ParShape = { 0, 4, 13, 29, 59, 113, 202, 334, 498, 661, 793, 883, 937, 967, 983, 991, 995, 998, 999, 999, 1000, 1000, 1000, 1000, 1000 };

		[Desc("Permille of the midpoint between ParShape samples.")]
		public readonly int ParShapeStep = 125;

		[Desc("Expected net worth at t=0 — the opening bank. The curve starts here by construction.")]
		public readonly int ParBaseWorth = 10000;

		[Desc("Added to ParBaseWorth per difficulty rank to give that rank's asymptote.",
			"⭐ 15000 per rank IS 5000 per harvester slot: BotLimits.HarvesterLimit is exactly",
			"3*(rank+1), an unbroken 1x..10x ladder, so the asymptote scale needs no new number.")]
		public readonly int ParAsymptotePerRank = 15000;

		[Desc("Ticks to the curve's midpoint for the EASIEST difficulty.",
			"⭐ 23400 = 12 minutes x ProductionTimeMultiplier 130%, reusing a ladder that is already",
			"tuned instead of adding a second one to keep in sync.")]
		public readonly int ParMidpointEasiest = 23400;

		[Desc("Ticks to the curve's midpoint for the HARDEST difficulty (12 min x 40%).")]
		public readonly int ParMidpointHardest = 7200;

		[Desc("Ticks between debug log lines recording measured-vs-expected worth. 0 disables.",
			"⚠ Left ON by default: the par curve's magnitudes are invented, and this is how they",
			"get replaced with measured ones. Turn it off once they have been.")]
		public readonly int LogInterval = 1500;

		[GrantedConditionReference]
		[Desc("Optional condition granted while this trait is paying out, so yaml can hang other",
			"emergency behaviour off the same signal.")]
		public readonly string Condition = null;

		public override object Create(ActorInitializer init) { return new DynamicBotInsurance(this); }
	}

	public class DynamicBotInsurance : INotifyCreated, INotifyOwnerChanged, INotifyResourceAccepted, ITick, ISync
	{
		enum Phase { Arming, Delaying, Paying }

		readonly DynamicBotInsuranceInfo info;

		PlayerResources playerResources;
		int conditionToken = Actor.InvalidConditionToken;

		// -1 means "this owner gets no insurance" (not a bot, or a bot type not in Difficulties).
		int rank = -1;
		int ratePerTick;
		int delayDivisor;
		int cashPerTick;
		int purifierModifier;

		// Rolling mean of total spendable funds over AverageWindow ticks, kept as a running sum so Tick stays O(1).
		int[] history;
		int historyIndex;
		int historyCount;
		long historySum;
		// Index-aware digest of the history array, updated with each replacement to retain O(1) Tick.
		int historyHash;

		[VerifySync]
		int threshold;

		[VerifySync]
		int delayRemaining;

		[VerifySync]
		int amtAwaitingPurification;

		PlayerStatistics stats;

		[VerifySync]
		int gameTicks;

		[VerifySync]
		int peakWorth;

		int worthFactor = 1000;

		// Milli-credits carried between ticks so a fractional rate really pays.
		// ⚠ Integer, never floating point: the payout must be deterministic across machines.
		[VerifySync]
		int accumulator;

		Phase phase = Phase.Arming;

		// VerifySync can hash only primitive values.  This compact hash covers the rest of the
		// simulation-driving state (including the rolling-history array and enum) without putting
		// an unsupported array, long, or enum directly behind the attribute.
		[VerifySync]
		int stateHash;

		public DynamicBotInsurance(DynamicBotInsuranceInfo info)
		{
			this.info = info;
			threshold = 0;
		}

		/// <summary>Linear interpolation across the difficulty list by index.</summary>
		int ByRank(int min, int max)
		{
			return InterpolateByRank(min, max, rank, info.Difficulties.Length);
		}

		internal static int InterpolateByRank(int min, int max, int rank, int difficultyCount)
		{
			var steps = difficultyCount - 1;
			if (steps <= 0)
				return min;

			return min + ((max - min) * rank) / steps;
		}

		void Configure(OpenRA.Player owner)
		{
			rank = owner != null && owner.IsBot && !string.IsNullOrEmpty(owner.BotType)
				? Array.FindIndex(info.Difficulties,
					d => string.Equals(d, owner.BotType, StringComparison.OrdinalIgnoreCase))
				: -1;

			history = new int[Math.Max(1, info.AverageWindow)];
			historyIndex = historyCount = 0;
			historySum = 0;
			historyHash = 0;
			threshold = 0;
			delayRemaining = 0;
			amtAwaitingPurification = 0;
			accumulator = 0;
			gameTicks = 0;
			peakWorth = 0;
			worthFactor = 1000;
			phase = Phase.Arming;

			if (rank >= 0)
			{
				ratePerTick = Math.Max(1, ByRank(info.MinThresholdRatePerTick, info.MaxThresholdRatePerTick));
				delayDivisor = Math.Max(1, ByRank(info.MinDelayDivisor, info.MaxDelayDivisor));
				cashPerTick = ByRank(info.MinCashPerTick, info.MaxCashPerTick);
				purifierModifier = ByRank(info.MinPurifierModifier, info.MaxPurifierModifier);
			}

			UpdateStateHash();
		}

		void INotifyCreated.Created(Actor self)
		{
			// Special case handling is required for the Player actor.
			// Created is called before Player.PlayerActor is assigned, so we must query other
			// player traits from self, knowing that it refers to the same actor as
			// self.Owner.PlayerActor.  (Same idiom as BotInsurance and ResourcePurifierCA.)
			var playerActor = self.Info.Name == "player" ? self : self.Owner.PlayerActor;
			playerResources = playerActor.Trait<PlayerResources>();

			// Optional on purpose. Without it the worth factor stays neutral and the trait behaves
			// exactly as it did before net worth existed -- absence degrades, never breaks.
			stats = playerActor.TraitOrDefault<PlayerStatistics>();

			Configure(self.Owner);
		}

		void INotifyOwnerChanged.OnOwnerChanged(Actor self, OpenRA.Player oldOwner, OpenRA.Player newOwner)
		{
			playerResources = newOwner.PlayerActor.Trait<PlayerResources>();
			stats = newOwner.PlayerActor.TraitOrDefault<PlayerStatistics>();

			// A captured or transferred player is a different economy: start the machine over
			// rather than carrying the old owner's history and frozen threshold across.
			Configure(newOwner);
			Revoke(self);
			UpdateStateHash();
		}

		void INotifyResourceAccepted.OnResourceAccepted(Actor self, Actor refinery, string resourceType, int count, int value)
		{
			// The old purifier was condition-gated: harvests before an insurance incident were never
			// eligible.  Preserve that rule so a rich bot cannot release a lifetime stockpile when
			// it first becomes distressed.
			if (rank >= 0 && phase == Phase.Paying)
			{
				amtAwaitingPurification += value;
				UpdateStateHash();
			}
		}

		/// <summary>Cash, resources, and everything the owner holds.</summary>
		int NetWorth()
		{
			var worth = playerResources.GetCashAndResources();
			if (stats != null)
				worth += stats.AssetsValue + (stats.ArmyValue * info.ArmyValueWeight) / 100;

			return worth;
		}

		/// <summary>Expected net worth for this difficulty at this game time. Integer throughout.</summary>
		int ParWorth()
		{
			return ParWorthAt(info, rank, gameTicks);
		}

		internal static int ParWorthAt(DynamicBotInsuranceInfo info, int rank, int gameTicks)
		{
			var midpoint = InterpolateByRank(
				info.ParMidpointEasiest, info.ParMidpointHardest, rank, info.Difficulties.Length);
			if (midpoint <= 0 || info.ParShape.Length < 2 || info.ParShapeStep <= 0)
				return info.ParBaseWorth;

			// Widen before multiplying: a long match can exceed Int32.MaxValue here even though
			// gameTicks itself is still a valid int.
			var progress = ((long)gameTicks * 1000L) / midpoint;    // permille of the midpoint
			var index = progress / info.ParShapeStep;

			int shape;
			if (index >= info.ParShape.Length - 1)
				shape = info.ParShape[info.ParShape.Length - 1];
			else
			{
				var shapeIndex = (int)index;
				var frac = (int)(progress - index * info.ParShapeStep);
				var lo = info.ParShape[shapeIndex];
				var hi = info.ParShape[shapeIndex + 1];
				shape = lo + ((hi - lo) * frac) / info.ParShapeStep;
			}

			var asymptote = (long)info.ParBaseWorth + (long)info.ParAsymptotePerRank * (rank + 1);
			return (int)((long)info.ParBaseWorth + ((asymptote - info.ParBaseWorth) * shape) / 1000L);
		}

		/// <summary>How much of the peak payout this owner's NET WORTH justifies, 0..1000.</summary>
		/// <remarks>
		/// Two ratios, both clamped, combined by GEOMETRIC MEAN rather than by product:
		///   rSelf   = worth / my own peak worth      -- fog-safe: never reads another player
		///   rTarget = worth / the par curve
		/// ⛔ NOT a product. The two are correlated -- a bot behind its own peak is usually also
		/// behind the curve -- so multiplying squares one piece of evidence: 0.5 x 0.5 = 0.25
		/// claims "four times worse than par" from two observations that each said "twice", and
		/// 0.25 x 0.25 = 0.0625 would pin the payout at maximum permanently. The geometric mean
		/// keeps the answer on the scale of its inputs.
		/// </remarks>
		int WorthFactorPermille(int worth)
		{
			if (peakWorth <= 0)
				return 1000;

			var rSelf = (int)Math.Clamp((1000L * worth) / peakWorth, info.MinSelfRatio, 1000L);

			var rTarget = 1000;
			if (info.UseParCurve)
			{
				var target = ParWorth();
				if (target > 0)
					rTarget = (int)Math.Clamp((1000L * worth) / target, info.ParRatioMin, info.ParRatioMax);
			}

			// Integer square root -- deterministic, unlike Math.Sqrt on a double.
			var combined = IntSqrt(rSelf * rTarget);
			var shortfall = Math.Clamp(1000 - combined, 0, 1000);
			return info.MinWorthFactor + ((1000 - info.MinWorthFactor) * shortfall) / 1000;
		}

		static int IntSqrt(int value)
		{
			if (value <= 0)
				return 0;

			var x = value;
			var y = (x + 1) / 2;
			while (y < x)
			{
				x = y;
				y = (x + value / x) / 2;
			}

			return x;
		}

		/// <summary>How deep below the cap the owner is: 0 at the cap, 1000 at zero liquid funds.</summary>
		/// <remarks>
		/// Measured against MaxThreshold rather than against the dynamic bar on purpose — this is
		/// the ABSOLUTE poverty scale the old ladder used, so the two agree rung for rung.
		/// </remarks>
		int DepthPermille(int liquidity)
		{
			return DepthPermille(liquidity, info.MaxThreshold);
		}

		internal static int DepthPermille(int liquidity, int maxThreshold)
		{
			if (liquidity >= maxThreshold)
				return 0;

			// Keep a sub-cap owner recoverable even when integer permille rounding would turn a
			// one-credit gap into zero depth. The accumulator still makes this a fractional payout,
			// but it cannot strand the Paying phase at MaxThreshold - 1.
			return Math.Max(1, (int)Math.Clamp(
				(1000L * (maxThreshold - (long)liquidity)) / maxThreshold, 0L, 1000L));
		}

		internal static bool ShouldStartDelay(int liquidity, int threshold) { return liquidity < threshold; }

		internal static bool ShouldCancelDelay(int liquidity, int threshold) { return liquidity > threshold; }

		internal static bool ShouldStopPaying(int liquidity, int maxThreshold) { return liquidity >= maxThreshold; }

		internal static int DelayTicks(int average, int divisor, int minimum, int maximum)
		{
			return Math.Clamp(average / Math.Max(1, divisor), minimum, maximum);
		}

		internal static (int Grant, int Accumulator) CashPayout(
			int accumulator, int cashPerTick, int depth, int liquidity, int maxThreshold)
		{
			var accumulated = (long)accumulator + (long)cashPerTick * depth;
			var grant = accumulated / 1000L;
			var remainder = (int)(accumulated - grant * 1000L);
			var cappedGrant = (int)Math.Min(grant, Math.Max(0L, maxThreshold - (long)liquidity));
			return (cappedGrant, remainder);
		}

		internal static int PurifierPayout(
			int amount, int modifier, int depth, int liquidity, int cashGrant, int maxThreshold)
		{
			var modified = Util.ApplyPercentageModifiers(amount, new[] { modifier });
			var bonus = ((long)modified * depth) / 1000L;
			return (int)Math.Min(bonus,
				Math.Max(0L, maxThreshold - (long)liquidity - cashGrant));
		}

		int RollingAverage()
		{
			return historyCount == 0 ? 0 : (int)(historySum / historyCount);
		}

		void Record(int liquidity)
		{
			if (historyCount == history.Length)
				historySum -= history[historyIndex];
			else
				historyCount++;

			historyHash ^= MixedHistorySlotHash(historyIndex, history[historyIndex]);
			history[historyIndex] = liquidity;
			historyHash ^= MixedHistorySlotHash(historyIndex, liquidity);
			historySum += liquidity;
			historyIndex = (historyIndex + 1) % history.Length;
		}

		internal static int MixedHistorySlotHash(int index, int value)
		{
			if (value == 0)
				return 0;

			// Mix the slot and value before XORing it into the aggregate. Keeping them as two
			// independent XOR terms makes permutations collide because every occupied slot and
			// every value then contributes the same terms regardless of their pairing.
			unchecked
			{
				var hash = (uint)value ^ ((uint)(index + 1) * 0x9E3779B9u);
				hash ^= hash >> 16;
				hash *= 0x85EBCA6Bu;
				hash ^= hash >> 13;
				hash *= 0xC2B2AE35u;
				hash ^= hash >> 16;
				return (int)hash;
			}
		}

		void Grant(Actor self)
		{
			if (!string.IsNullOrEmpty(info.Condition) && conditionToken == Actor.InvalidConditionToken)
				conditionToken = self.GrantCondition(info.Condition);
		}

		void Revoke(Actor self)
		{
			if (conditionToken != Actor.InvalidConditionToken)
				conditionToken = self.RevokeCondition(conditionToken);
		}

		void UpdateStateHash()
		{
			unchecked
			{
				var hash = 17;
				hash = (hash * 397) ^ rank;
				hash = (hash * 397) ^ ratePerTick;
				hash = (hash * 397) ^ delayDivisor;
				hash = (hash * 397) ^ cashPerTick;
				hash = (hash * 397) ^ purifierModifier;
				hash = (hash * 397) ^ historyIndex;
				hash = (hash * 397) ^ historyCount;
				hash = (hash * 397) ^ (int)historySum;
				hash = (hash * 397) ^ (int)(historySum >> 32);
				hash = (hash * 397) ^ historyHash;

				hash = (hash * 397) ^ threshold;
				hash = (hash * 397) ^ delayRemaining;
				hash = (hash * 397) ^ amtAwaitingPurification;
				hash = (hash * 397) ^ gameTicks;
				hash = (hash * 397) ^ peakWorth;
				hash = (hash * 397) ^ worthFactor;
				hash = (hash * 397) ^ accumulator;
				stateHash = (hash * 397) ^ (int)phase;
			}
		}

		void ITick.Tick(Actor self)
		{
			if (rank < 0)
				return;

			if (gameTicks < int.MaxValue)
				gameTicks++;

			// Stored resources are immediately spendable (PlayerResources.TakeCash spends them
			// before cash), so the rescue must use the same total liquid funds for history,
			// triggering, recovery, exit, and payout depth.
			var liquidity = playerResources.GetCashAndResources();
			Record(liquidity);

			// ⭐ TWO-FACTOR. Liquid funds decide WHETHER the insurance arms and fires, while NET
			// WORTH decides HOW MUCH. That removes the false positive where a bot with no liquid
			// funds mid-push, holding a 30,000-credit army, reads as
			// bankrupt when it is simply spending correctly and its harvesters will refill it.
			var worth = NetWorth();
			if (worth > peakWorth)
				peakWorth = worth;

			worthFactor = stats != null ? WorthFactorPermille(worth) : 1000;

			if (info.LogInterval > 0 && gameTicks % info.LogInterval == 0)
				Log.Write("debug", $"BotInsurance {self.Owner.InternalName} [{self.Owner.BotType}] "
					+ $"t={gameTicks} phase={phase} liquidity={liquidity} worth={worth} peak={peakWorth} "
					+ $"par={(info.UseParCurve ? ParWorth() : 0)} worthFactor={worthFactor} "
					+ $"threshold={threshold}");

			switch (phase)
			{
				case Phase.Arming:
				{
					// The bar TRACKS the rolling average, moving toward it by at most ratePerTick a
					// tick -- up when the average is above, down when below, same rate either way.
					// MinThreshold floors the target so a broke owner stays reachable; MaxThreshold
					// caps it so a rich one is not insured.
					var target = Math.Clamp(RollingAverage(), info.MinThreshold, info.MaxThreshold);
					var step = Math.Clamp(target - threshold, -ratePerTick, ratePerTick);
					threshold += step;

					// ⛔ STRICTLY below. With `<=` the bar converges to the average, the average
					// converges to a stable liquid-funds pile, and every owner under the cap eventually
					// insures itself -- baseline income rather than an emergency measure.
					if (ShouldStartDelay(liquidity, threshold))
					{
						delayRemaining = DelayTicks(RollingAverage(), delayDivisor,
							info.MinDelayTicks, info.MaxDelayTicks);
						phase = Phase.Delaying;
					}

					break;
				}

				case Phase.Delaying:
				{
					// Recovering above the frozen bar during the wait cancels it outright.
					if (ShouldCancelDelay(liquidity, threshold))
					{
						// Unfreeze only. Slamming the bar back to zero would discard the tracker and
						// start the next arming cycle from a lie about the economy.
						phase = Phase.Arming;
						break;
					}

					if (--delayRemaining <= 0)
						phase = Phase.Paying;

					break;
				}

				case Phase.Paying:
				{
					// Pay until the owner is solvent again, then re-arm. Exiting at MaxThreshold
					// rather than at the frozen bar is what makes the rescue actually useful: a bot
					// released at its own poverty line has too little to rebuild with, which is the
					// whole point of the trait.
					if (ShouldStopPaying(liquidity, info.MaxThreshold))
					{
						amtAwaitingPurification = 0;
						accumulator = 0;
						phase = Phase.Arming;
						Revoke(self);
						break;
					}

					// Proportional to depth, accumulated in milli-credits so a fractional rate is
					// actually paid instead of being truncated to nothing every tick.
					var depth = Math.Max(1, (DepthPermille(liquidity) * worthFactor + 999) / 1000);
					var payout = CashPayout(accumulator, cashPerTick, depth, liquidity, info.MaxThreshold);
					accumulator = payout.Accumulator;
					var cappedGrant = payout.Grant;
					if (cappedGrant > 0)
						playerResources.GiveCash(cappedGrant);

					// The purifier bonus rides the same depth signal, as the stacked purifiers did.
					if (amtAwaitingPurification >= info.PurifierMinAmount)
					{
						// Deliveries can arrive in a burst. Do not let the purifier bonus overshoot the
						// same liquid-funds cap that ends the normal payout.
						var cappedBonus = PurifierPayout(amtAwaitingPurification, purifierModifier,
							depth, liquidity, cappedGrant, info.MaxThreshold);
						if (cappedBonus > 0)
							playerResources.GiveCash(cappedBonus);
						amtAwaitingPurification = 0;
					}

					Grant(self);
					break;
				}
			}

			UpdateStateHash();
		}
	}
}
