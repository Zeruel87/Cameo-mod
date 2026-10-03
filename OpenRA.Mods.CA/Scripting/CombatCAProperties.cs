#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

using OpenRA.Mods.CA.Activities;
using OpenRA.Mods.Common.Activities;
using OpenRA.Mods.Common.Traits;
using OpenRA.Scripting;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Scripting
{
	[ScriptPropertyGroup("Combat")]
	public class CombatCAProperties : ScriptActorProperties, Requires<AttackBaseInfo>, Requires<IMoveInfo>
	{
		private readonly IMove move;

		public CombatCAProperties(ScriptContext context, Actor self)
			: base(context, self)
		{
			move = self.Trait<IMove>();
		}

		[ScriptActorPropertyActivity]
		[Desc("Ignoring visibility, find the closest hostile target and attack move to within 2 cells of it.")]
		public void HuntCA()
		{
			Self.QueueActivity(new HuntCA(Self));
		}

		[ScriptActorPropertyActivity]
		[Desc("Move to a cell, but stop and attack anything within range on the way. " +
			"closeEnough defines an optional range (in cells) that will be considered " +
			"close enough to complete the activity.")]
		public void AttackMoveCA(CPos cell, int closeEnough = 0)
		{
			Self.QueueActivity(new AttackMoveActivity(Self, () => move.MoveTo(cell, closeEnough, evaluateNearestMovableCell: true)));
		}
	}
}
