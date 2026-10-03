#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

namespace OpenRA.Mods.CA.Traits
{
	/// <summary>
	/// Human-likeness gate H1 (AI_SYNTHESIS.md §5): a shared budget of actions and
	/// attention so the bot cannot spend a superhuman burst at a critical moment
	/// (the AlphaStar lesson — a cap alone is not enough, the quota must not be
	/// spendable in bursts) and so decision points take turns instead of all
	/// acting on the same tick (humans move groups one after another).
	///
	/// Implemented by <c>HumanPaceBotModule</c>, which lives in OpenRA.Mods.Cameo
	/// and must not be referenced by name from this assembly. Consumers: the
	/// Cameo <c>ModularBot</c> shadow consults <see cref="TryConsumeActions"/>
	/// while draining its order queue, and <c>SquadManagerBotModuleCA</c>
	/// consults <see cref="TryConsumeAttention"/> before each squad's update.
	/// </summary>
	public interface IBotActionBudget
	{
		/// <summary>
		/// True if <paramref name="count"/> orders may be issued right now without
		/// exceeding the sliding-window rate or the per-tick burst cap. Consumes
		/// budget only when true — callers that get false must defer (deferral is
		/// the stagger: denied work retries on a later tick).
		/// </summary>
		bool TryConsumeActions(int count = 1);

		/// <summary>
		/// True if <paramref name="decisionPoint"/> holds attention this tick. At
		/// most AttentionSlotsPerTick distinct callers pass per tick; a caller that
		/// already passed may act again freely. Defer on false.
		/// </summary>
		bool TryConsumeAttention(object decisionPoint);

		/// <summary>Orders admitted in the current window (telemetry/tests).</summary>
		int ActionsInWindow { get; }

		/// <summary>Orders admitted this tick (the burst counter, telemetry/tests).</summary>
		int ActionsThisTick { get; }

		/// <summary>Distinct decision points holding attention this tick (telemetry/tests).</summary>
		int AttentionInUse { get; }
	}
}
