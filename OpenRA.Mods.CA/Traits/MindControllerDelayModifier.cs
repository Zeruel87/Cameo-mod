#region Copyright & License Information
/**
 * Copyright (c) The OpenRA Combined Arms Developers (see CREDITS).
 * This file is part of OpenRA Combined Arms, which is free software.
 * It is made available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version. For more information, see COPYING.
 */
#endregion

using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.CA.Traits
{
	[Desc("This actor can mind control other actors.")]
	public class MindControllerDelayModifierInfo : ConditionalTraitInfo, Requires<MindControllerCAInfo>
	{
		[Desc("Percentage modifier to apply.")]
		public readonly int Modifier = 100;

		public override object Create(ActorInitializer init) { return new MindControllerDelayModifier(init.Self, this); }
	}

	public class MindControllerDelayModifier : ConditionalTrait<MindControllerDelayModifierInfo>
	{
		readonly MindControllerDelayModifierInfo info;
		readonly MindControllerCA mindController;

		public MindControllerDelayModifier(Actor self, MindControllerDelayModifierInfo info)
			: base(info)
		{
			this.info = info;
			mindController = self.Trait<MindControllerCA>();
		}

		public int Modifier { get { return IsTraitDisabled ? 100 : info.Modifier; } }

		protected override void TraitEnabled(Actor self)
		{
			mindController.ModifierUpdated();
		}

		protected override void TraitDisabled(Actor self)
		{
			mindController.ModifierUpdated();
		}
	}
}
