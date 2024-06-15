using System;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Graphics;
using OpenRA.Mods.Cameo.Traits;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Traits;

namespace OpenRA.Mods.Cameo.Orders
{
	public enum ECustomFormationsUnitOrderGeneratorMode
	{
		None,
		Move,
		ForceFire,
		Max
	}

	//Use as the 'DefaultOrderGenerator' in your mod.yaml to enable custom formations
	public class CustomFormationsUnitOrderGenerator : CustomFormationsOrderGeneratorBase
	{
		protected PaletteReference MoveLineOrderTileMarkerPalette = null;
		protected ISpriteSequence MoveLineOrderTileMarkerSequence = null;
		protected Sprite MoveLineOrderTileMarkerSprite = null;
		protected Animation MoveLineOrderTileMarkerAnimation = null;
		protected bool bMoveLineOrderTileMarkerAnimates = false;

		protected PaletteReference MoveLineOrderMarkerPalette = null;
		protected ISpriteSequence MoveLineOrderMarkerSequence = null;
		protected Sprite MoveLineOrderMarkerSprite = null;
		protected Animation MoveLineOrderMarkerAnimation = null;
		protected bool bMoveLineOrderMarkerAnimates = false;

		protected PaletteReference ForceFireLineOrderTileMarkerPalette = null;
		protected ISpriteSequence ForceFireLineOrderTileMarkerSequence = null;
		protected Sprite ForceFireLineOrderTileMarkerSprite = null;
		protected Animation ForceFireLineOrderTileMarkerAnimation = null;
		protected bool bForceFireLineOrderTileMarkerAnimates = false;

		protected PaletteReference ForceFireLineOrderMarkerPalette = null;
		protected ISpriteSequence ForceFireLineOrderMarkerSequence = null;
		protected Sprite ForceFireLineOrderMarkerSprite = null;
		protected Animation ForceFireLineOrderMarkerAnimation = null;
		protected bool bForceFireLineOrderMarkerAnimates = false;

		protected ECustomFormationsUnitOrderGeneratorMode CurrentUnitOrderGeneratorMode = ECustomFormationsUnitOrderGeneratorMode.None;

		public override string GetCursor(World world, CPos cell, int2 worldPixel, MouseInput mi)
		{
			if (bInitialized && (CurrentMode == ECustomFormationsMode.CommandLine))
			{
				if (mi.Modifiers.HasModifier(Modifiers.Ctrl))
				{
					ChangeUnitOrderGeneratorMode(ECustomFormationsUnitOrderGeneratorMode.ForceFire);
				}
				else
				{
					ChangeUnitOrderGeneratorMode(ECustomFormationsUnitOrderGeneratorMode.Move);
				}
			}

			var target = OrderGeneratorHelpers.TargetForInput(world, cell, worldPixel, mi);

			bool useSelect;
			if (Game.Settings.Game.UseClassicMouseStyle && !OrderGeneratorHelpers.InputOverridesSelection(world, worldPixel, mi))
				useSelect = target.Type == TargetType.Actor && target.Actor.Info.HasTraitInfo<ISelectableInfo>();
			else
			{
				var ordersWithCursor = world.Selection.Actors
					.Select(a => OrderGeneratorHelpers.OrderForUnit(a, target, cell, mi))
					.Where(o => o != null && o.Cursor != null);

				var cursorOrder = ordersWithCursor.MaxByOrDefault(o => o.Order.OrderPriority);
				if (cursorOrder != null)
					return cursorOrder.Cursor;

				useSelect = target.Type == TargetType.Actor && target.Actor.Info.HasTraitInfo<ISelectableInfo>() &&
					(mi.Modifiers.HasModifier(Modifiers.Shift) || !world.Selection.Actors.Any());
			}

			return useSelect ? worldSelectCursor : worldDefaultCursor;
		}

		protected override bool OnInitialize(WorldRenderer inWorldRenderer, World inWorld)
		{
			if (base.OnInitialize(inWorldRenderer, inWorld))
			{
				CustomFormationsModOptions modoptions = OwningWorld.LocalPlayer.PlayerActor.Trait<CustomFormationsModOptions>();

				bMoveLineOrderTileMarkerAnimates = modoptions.PlaysMoveOrderTileMarkerAnimation;
				MoveLineOrderTileMarkerPalette = OwningWorldRenderer.Palette(modoptions.MoveOrderTileMarkerPaletteName);
				MoveLineOrderTileMarkerSequence = OwningWorld.Map.Sequences.GetSequence(modoptions.MoveOrderTileMarkerImageName, modoptions.MoveOrderTileMarkerSequenceName);
				if (bMoveLineOrderTileMarkerAnimates)
				{
					MoveLineOrderTileMarkerAnimation = new Animation(OwningWorld, modoptions.MoveOrderTileMarkerImageName);
					//MoveLineOrderTileMarkerAnimation.CurrentSequence = MoveLineOrderTileMarkerSequence;
					//MoveLineOrderTileMarkerAnimation.ChangeImage(modoptions.MoveOrderTileMarkerImageName, modoptions.MoveOrderTileMarkerSequenceName);
				}
				else
				{
					MoveLineOrderTileMarkerSprite = MoveLineOrderTileMarkerSequence.GetSprite(0);
				}

				bMoveLineOrderMarkerAnimates = modoptions.PlaysMoveOrderMarkerAnimation;
				MoveLineOrderMarkerPalette = OwningWorldRenderer.Palette(modoptions.MoveOrderMarkerPaletteName);
				MoveLineOrderMarkerSequence = OwningWorld.Map.Sequences.GetSequence(modoptions.MoveOrderMarkerImageName, modoptions.MoveOrderMarkerSequenceName);
				if (bMoveLineOrderMarkerAnimates)
				{
					MoveLineOrderMarkerAnimation = new Animation(OwningWorld, modoptions.MoveOrderMarkerImageName);
					//MoveLineOrderMarkerAnimation.ChangeImage(modoptions.MoveOrderMarkerImageName, modoptions.MoveOrderMarkerSequenceName);
				}
				else
				{
					MoveLineOrderMarkerSprite = MoveLineOrderMarkerSequence.GetSprite(0);
				}

				bForceFireLineOrderTileMarkerAnimates = modoptions.PlaysForceFireOrderTileMarkerAnimation;
				ForceFireLineOrderTileMarkerPalette = OwningWorldRenderer.Palette(modoptions.ForceFireOrderTileMarkerPaletteName);
				ForceFireLineOrderTileMarkerSequence = OwningWorld.Map.Sequences.GetSequence(modoptions.ForceFireOrderTileMarkerImageName, modoptions.ForceFireOrderTileMarkerSequenceName);
				if (bForceFireLineOrderTileMarkerAnimates)
				{
					ForceFireLineOrderTileMarkerAnimation = new Animation(OwningWorld, modoptions.ForceFireOrderTileMarkerImageName);
					//ForceFireLineOrderTileMarkerAnimation.ChangeImage(modoptions.ForceFireOrderTileMarkerImageName, modoptions.ForceFireOrderTileMarkerSequenceName);
				}
				else
				{
					ForceFireLineOrderTileMarkerSprite = ForceFireLineOrderTileMarkerSequence.GetSprite(0);
				}

				bForceFireLineOrderMarkerAnimates = modoptions.PlaysForceFireOrderMarkerAnimation;
				ForceFireLineOrderMarkerPalette = OwningWorldRenderer.Palette(modoptions.ForceFireOrderMarkerPaletteName);
				ForceFireLineOrderMarkerSequence = OwningWorld.Map.Sequences.GetSequence(modoptions.ForceFireOrderMarkerImageName, modoptions.ForceFireOrderMarkerSequenceName);
				if (bForceFireLineOrderMarkerAnimates)
				{
					ForceFireLineOrderMarkerAnimation = new Animation(OwningWorld, modoptions.ForceFireOrderMarkerImageName);
					//ForceFireLineOrderMarkerAnimation.ChangeImage(modoptions.ForceFireOrderMarkerImageName, modoptions.ForceFireOrderMarkerSequenceName);
				}
				else
				{
					ForceFireLineOrderMarkerSprite = ForceFireLineOrderMarkerSequence.GetSprite(0);
				}

				ChangeUnitOrderGeneratorMode(ECustomFormationsUnitOrderGeneratorMode.Move);

				return true;
			}

			return false;
		}

		protected override IEnumerable<Order> OnLMBDown(CPos inCell, int2 inWorldPixel, MouseInput inMouseInput)
		{
			CurrentMode = ECustomFormationsMode.Dragbox;
			DragStartMousePosition = CurrentMousePosition;
			yield break;
		}

		protected override IEnumerable<Order> OnLMBUp(CPos inCell, int2 inWorldPixel, MouseInput inMouseInput)
		{
			bool multiclick = inMouseInput.MultiTapCount >= 2;

			if (multiclick)
			{
				var unit = OwningWorld.ScreenMap.ActorsAtMouse(CurrentMousePosition)
					.WithHighestSelectionPriority(CurrentMousePosition, inMouseInput.Modifiers);

				var eligiblePlayers = SelectionUtils.GetPlayersToIncludeInSelection(OwningWorld);

				if (unit != null && eligiblePlayers.Contains(unit.Owner))
				{
					var s = unit.TraitOrDefault<ISelectable>();
					if (s != null)
					{
						// Select actors on the screen that have the same selection class as the actor under the mouse cursor
						var newSelection = SelectionUtils.SelectActorsOnScreen(OwningWorld, OwningWorldRenderer, new HashSet<string> { s.Class }, eligiblePlayers);

						OwningWorld.Selection.Combine(OwningWorld, newSelection, true, false);
					}
				}
			}
			else
			{
				var newSelection = SelectionUtils.SelectActorsInBoxWithDeadzone(OwningWorld, DragStartMousePosition, CurrentMousePosition, inMouseInput.Modifiers);
				OwningWorld.Selection.Combine(OwningWorld, newSelection, inMouseInput.Modifiers.HasModifier(Modifiers.Shift), DragStartMousePosition == CurrentMousePosition);
			}

			CurrentMode = ECustomFormationsMode.None;

			yield break;
		}

		protected override IEnumerable<Order> OnRMBDown(CPos inCell, int2 inWorldPixel, MouseInput inMouseInput)
		{
			if (!OwningWorld.Selection.Actors.Any())
			{
				yield break;
			}

			Target target = OrderGeneratorHelpers.TargetForInput(OwningWorld, inCell, inWorldPixel, inMouseInput);
			if (target.Type == TargetType.Actor)
			{
				if (target.Actor.Owner != OwningWorld.LocalPlayer)
				{
					if (target.Actor.Owner.IsAlliedWith(OwningWorld.LocalPlayer))
					{
						CurrentCircleTargetFilter = target.Actor.GetEnabledTargetTypes();
						StartCommandCircle(FriendlyCircleColor, ECircleCommandTargetMode.Allies);
					}
					else
					{
						CurrentCircleTargetFilter = target.Actor.GetEnabledTargetTypes();
						StartCommandCircle(HostileCircleColor, ECircleCommandTargetMode.Enemies);
					}
				}
				else
				{
					CurrentCircleTargetFilter = target.Actor.GetEnabledTargetTypes();
					StartCommandCircle(FriendlyCircleColor, ECircleCommandTargetMode.Allies);
				}
			}
			else if (target.Type == TargetType.Terrain)
			{
				if (inMouseInput.Modifiers.HasModifier(Modifiers.Ctrl))
				{
					ChangeUnitOrderGeneratorMode(ECustomFormationsUnitOrderGeneratorMode.ForceFire);
				}
				else {
					ChangeUnitOrderGeneratorMode(ECustomFormationsUnitOrderGeneratorMode.Move);
				}

				StartCommandLine(inCell);
			}
		}

		protected override IEnumerable<Order> OnRMBUp(CPos inCell, int2 inWorldPixel, MouseInput inMouseInput)
		{
			if (!OwningWorld.Selection.Actors.Any())
			{
				yield break;
			}

			if (IsTap)
			{
				// tapped
				IEnumerable<Order> results = TapOrder(inCell, inWorldPixel, inMouseInput);
				foreach (Order o in results)
				{
					yield return o;
				}
			}
			else if (IsValidCommandLine)
			{
				IEnumerable<Order> orders = EndCommandLine(inCell, inWorldPixel, inMouseInput);
				foreach (Order o in orders)
				{
					yield return o;
				}
			}
			else if (IsValidCommandCircle)
			{
				IEnumerable<Order> orders = EndCommandCircle(inWorldPixel, inMouseInput);
				foreach (Order o in orders)
				{
					yield return o;
				}
			}
		}

		protected void ChangeUnitOrderGeneratorMode(ECustomFormationsUnitOrderGeneratorMode inNewMode)
		{
			if (inNewMode == ECustomFormationsUnitOrderGeneratorMode.Move)
			{
				if (CurrentUnitOrderGeneratorMode == ECustomFormationsUnitOrderGeneratorMode.Move)
				{
					return;
				}

				CurrentUnitOrderGeneratorMode = ECustomFormationsUnitOrderGeneratorMode.Move;
				LineOrderTileMarkerSequence = MoveLineOrderTileMarkerSequence;
				LineOrderTileMarkerSprite = MoveLineOrderTileMarkerSprite;
				LineOrderTileMarkerPalette = MoveLineOrderTileMarkerPalette;
				LineOrderTileMarkerAnimation = MoveLineOrderTileMarkerAnimation;
				bLineOrderTileMarkerAnimates = bMoveLineOrderTileMarkerAnimates;

				LineOrderMarkerSequence = MoveLineOrderMarkerSequence;
				LineOrderMarkerSprite = MoveLineOrderMarkerSprite;
				LineOrderMarkerPalette = MoveLineOrderMarkerPalette;
				LineOrderMarkerAnimation = MoveLineOrderMarkerAnimation;
				bLineOrderMarkerAnimates = bMoveLineOrderMarkerAnimates;

				if (bLineOrderTileMarkerAnimates && (CurrentMode == ECustomFormationsMode.CommandLine))
				{
					LineOrderTileMarkerAnimation.PlayRepeating(LineOrderTileMarkerSequence.Name);
				}

				if (bLineOrderMarkerAnimates && (CurrentMode == ECustomFormationsMode.CommandLine))
				{
					LineOrderMarkerAnimation.PlayRepeating(LineOrderMarkerSequence.Name);
				}

				LineOrderTileMarkerRenderableArray.Clear();
				LineOrderMarkerRenderableArray.Clear();
			}
			else if (inNewMode == ECustomFormationsUnitOrderGeneratorMode.ForceFire)
			{
				if (CurrentUnitOrderGeneratorMode == ECustomFormationsUnitOrderGeneratorMode.ForceFire)
				{
					return;
				}

				CurrentUnitOrderGeneratorMode = ECustomFormationsUnitOrderGeneratorMode.ForceFire;
				LineOrderTileMarkerSequence = ForceFireLineOrderTileMarkerSequence;
				LineOrderTileMarkerSprite = ForceFireLineOrderTileMarkerSprite;
				LineOrderTileMarkerPalette = ForceFireLineOrderTileMarkerPalette;
				LineOrderTileMarkerAnimation = ForceFireLineOrderTileMarkerAnimation;
				bLineOrderTileMarkerAnimates = bForceFireLineOrderTileMarkerAnimates;

				LineOrderMarkerSequence = ForceFireLineOrderMarkerSequence;
				LineOrderMarkerSprite = ForceFireLineOrderMarkerSprite;
				LineOrderMarkerPalette = ForceFireLineOrderMarkerPalette;
				LineOrderMarkerAnimation = ForceFireLineOrderMarkerAnimation;
				bLineOrderMarkerAnimates = bForceFireLineOrderMarkerAnimates;

				if (bLineOrderTileMarkerAnimates && (CurrentMode == ECustomFormationsMode.CommandLine))
				{
					LineOrderTileMarkerAnimation.PlayRepeating(LineOrderTileMarkerSequence.Name);
				}

				if (bLineOrderMarkerAnimates && (CurrentMode == ECustomFormationsMode.CommandLine))
				{
					LineOrderMarkerAnimation.PlayRepeating(LineOrderMarkerSequence.Name);
				}

				LineOrderTileMarkerRenderableArray.Clear();
				LineOrderMarkerRenderableArray.Clear();
			}
		}
	}
}
