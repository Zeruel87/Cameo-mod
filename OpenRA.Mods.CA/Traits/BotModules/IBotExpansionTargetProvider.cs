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
	/// Cameo (docs/design/AI_ARCHITECTURE.md §12.13, EX-1): the resource field an expansion planner wants the base
	/// to walk toward. <c>BaseBuilderBotModuleCA</c>'s BaseCrawl placements aim at it when one is published; null
	/// keeps today's behaviour. Providers live in OpenRA.Mods.Cameo and must not be referenced by name here.
	/// </summary>
	public interface IBotExpansionTargetProvider
	{
		CPos? ExpansionTarget { get; }

		/// <summary>EX-2: the target field is in reach and unclaimed, so a refinery should go there next.</summary>
		bool WantsRefineryAtExpansionTarget { get; }

		/// <summary>EX-2: how close (cells) to the target a refinery must stand to claim the field.</summary>
		int ExpansionTargetClaimRadius { get; }

		/// <summary>
		/// EX-2c: the field whose resource centre the next refinery should claim. May differ from
		/// <see cref="ExpansionTarget"/> (the crawl aim): any free field already in reach qualifies, so an
		/// outpost yard draws its refinery the moment it can place one instead of waiting to become the
		/// crawl target. Null = claim <see cref="ExpansionTarget"/> (the EX-2 behaviour).
		/// </summary>
		CPos? RefineryClaimTarget { get; }

		/// <summary>
		/// FE-1 (§12.24, DESIGN §19.1b): the provider enforces one refinery per anchor (resource spreader or spreaderless
		/// field centre). While true the base builder replaces its yard-based refinery cap, OptimalRefineryCount and the
		/// scale-target refinery cap by <see cref="RefineryAnchorCount"/> / <see cref="UnservedAnchorsInReach"/>, and
		/// <see cref="RefineryClaimTarget"/> is the anchor. Default false: no provider (classic) or switch off = unchanged.
		/// </summary>
		bool RefineryLawActive => false;

		/// <summary>FE-1: the number of anchors; the physical ceiling of the refinery count.</summary>
		int RefineryAnchorCount => 0;

		/// <summary>FE-1: anchors within building reach that no own refinery serves yet.</summary>
		int UnservedAnchorsInReach => 0;

		/// <summary>FE-1: the resource centre of the anchor's field, the tie-break of the claim placement. Null = none.</summary>
		CPos? RefineryClaimFieldCenter => null;
	}
}
