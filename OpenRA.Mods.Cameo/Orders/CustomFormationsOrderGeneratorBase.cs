using System;
using System.Collections.Generic;
using System.Linq;
using Accord.Math.Optimization;
using OpenRA.Graphics;
using OpenRA.Mods.Common;
using OpenRA.Mods.Common.Graphics;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Mods.Cameo.Graphics;
using OpenRA.Orders;
using OpenRA.Primitives;
using OpenRA.Traits;
using OpenRA.Widgets;
using System.Collections;

namespace OpenRA.Mods.Cameo.Orders
{
	public enum ECustomFormationsMode
	{
		None,
		Dragbox,
		CommandLine,
		CommandCircle,
		Max
	}

	public enum ECircleCommandTargetMode
	{
		None,
		Allies,
		Enemies,
		All,
		Max
	}

	public sealed class UnitOrderResult
	{
		public readonly Actor Actor;
		public readonly IOrderTargeter Order;
		public readonly IIssueOrder Trait;
		public readonly string Cursor;
		public ref readonly Target Target => ref target;

		readonly Target target;

		public UnitOrderResult(Actor actor, IOrderTargeter order, IIssueOrder trait, string cursor, in Target target)
		{
			Actor = actor;
			Order = order;
			Trait = trait;
			Cursor = cursor;
			this.target = target;
		}
	}

	/**
	 * Base class for Custom Formations order generators. See CustomFormationsUnitOrderGenerator for default contextual command
	 */
	public class CustomFormationsOrderGeneratorBase : IOrderGenerator
	{
		protected World OwningWorld = null;
		protected WorldRenderer OwningWorldRenderer = null;

		protected int2 DragStartMousePosition = new();
		protected int2 CurrentMousePosition = new();
		protected WPos CurrentMouseTilePos = new();

		protected ECustomFormationsMode CurrentMode = ECustomFormationsMode.None;
		protected ECircleCommandTargetMode CurrentCircleTargetMode = ECircleCommandTargetMode.None;

		public virtual bool IsTap => ((DragStartMousePosition - CurrentMousePosition).Length <= Game.Settings.Game.SelectionDeadzone);
		public virtual bool IsValidDragbox => ((CurrentMode == ECustomFormationsMode.Dragbox) && ((DragStartMousePosition - CurrentMousePosition).Length > Game.Settings.Game.SelectionDeadzone));
		public virtual bool IsValidCommandLine => ((CurrentMode == ECustomFormationsMode.CommandLine) && (CurrentMarkedCells.Count > 1));
		public virtual bool IsValidCommandCircle => ((CurrentMode == ECustomFormationsMode.CommandCircle) && ((DragStartMousePosition - CurrentMousePosition).Length > Game.Settings.Game.SelectionDeadzone));
		public virtual bool ClearSelectionOnLeftClick => true;

		protected Color CurrentCircleColor = Color.White;
		protected Color HostileCircleColor = Color.OrangeRed;
		protected Color FriendlyCircleColor = Color.SkyBlue;

		protected BitSet<TargetableType> CurrentCircleTargetFilter = new BitSet<TargetableType>();

		protected Color normalSelectionColor;
		protected Color altSelectionColor;
		protected Color ctrlSelectionColor;

		protected readonly string worldSelectCursor = ChromeMetrics.Get<string>("WorldSelectCursor");
		protected readonly string worldDefaultCursor = ChromeMetrics.Get<string>("WorldDefaultCursor");

		protected bool bInitialized = false;
		protected bool bLMBDown;
		protected bool bRMBDown;

		protected PaletteReference LineOrderTileMarkerPalette = null;
		protected ISpriteSequence LineOrderTileMarkerSequence = null;
		protected Sprite LineOrderTileMarkerSprite = null;
		protected Animation LineOrderTileMarkerAnimation = null;
		protected bool bLineOrderTileMarkerAnimates = false;

		protected PaletteReference LineOrderMarkerPalette = null;
		protected ISpriteSequence LineOrderMarkerSequence = null;
		protected Sprite LineOrderMarkerSprite = null;
		protected Animation LineOrderMarkerAnimation = null;
		protected bool bLineOrderMarkerAnimates = false;

		protected List<SpriteRenderable> LineOrderTileMarkerRenderableArray = new();
		protected List<SpriteRenderable> LineOrderMarkerRenderableArray = new();

		protected List<CPos> CurrentMarkedCells = new();
		protected List<WPos> CurrentOrderMarkers = new();
		protected CPos LastMarkedCell = new();

		// IOrderGenerator
		public virtual void Tick(World world)
		{
			if (bInitialized && (CurrentMode == ECustomFormationsMode.CommandLine))
			{
				if (bLineOrderTileMarkerAnimates && (LineOrderTileMarkerAnimation != null))
				{
					LineOrderTileMarkerAnimation.Tick();
				}
				if (bLineOrderMarkerAnimates && (LineOrderMarkerAnimation != null))
				{
					LineOrderMarkerAnimation.Tick();
				}
			}
		}

		public virtual IEnumerable<IRenderable> Render(WorldRenderer wr, World world) { yield break; }

		public virtual IEnumerable<IRenderable> RenderAboveShroud(WorldRenderer wr, World world)
		{
			List<IRenderable> totalrenderables = new();

			if (!bInitialized)
			{
				bInitialized = OnInitialize(wr, world);
				if (!bInitialized)
				{
					return totalrenderables.ToArray<IRenderable>();
				}
			}

			var modifiers = Game.GetModifierKeys();
			IEnumerable<Actor> rollover;
			if (IsValidDragbox)
			{
				var a = wr.Viewport.WorldToViewPx(DragStartMousePosition);
				var b = wr.Viewport.WorldToViewPx(CurrentMousePosition);

				var color = normalSelectionColor;
				if (modifiers.HasFlag(Modifiers.Alt) && !modifiers.HasFlag(Modifiers.Ctrl))
				{
					color = altSelectionColor;
				}
				else if (modifiers.HasFlag(Modifiers.Ctrl) && !modifiers.HasFlag(Modifiers.Alt))
				{
					color = ctrlSelectionColor;
				}

				totalrenderables.Add(new UIRectangleAnnotationRenderable(a, b, 2.0f, color, CurrentMouseTilePos));

				// Render actors in the dragbox
				rollover = SelectionUtils.SelectActorsInBoxWithDeadzone(OwningWorld, DragStartMousePosition, CurrentMousePosition, modifiers);
			}
			else
			{
				// Render actors under the mouse pointer
				rollover = SelectionUtils.SelectActorsInBoxWithDeadzone(OwningWorld, CurrentMousePosition, CurrentMousePosition, modifiers);
			}

			wr.World.Selection.SetRollover(rollover);

			if (IsValidCommandLine)
			{
				if ((CurrentMarkedCells.Count < LineOrderTileMarkerRenderableArray.Count) || bLineOrderTileMarkerAnimates)
				{
					LineOrderTileMarkerRenderableArray.Clear();
				}
				//todo: branch animation or not animated before loops
				while (CurrentMarkedCells.Count > LineOrderTileMarkerRenderableArray.Count)
				{
					WPos pos = world.Map.CenterOfCell(CurrentMarkedCells[LineOrderTileMarkerRenderableArray.Count]);
					if (bLineOrderTileMarkerAnimates)
					{
						IRenderable[] animrenderables = LineOrderTileMarkerAnimation.Render(pos, LineOrderTileMarkerPalette);
						foreach (IRenderable renderable in animrenderables)
						{
							if (renderable is SpriteRenderable)
							{
								LineOrderTileMarkerRenderableArray.Add((SpriteRenderable)renderable);
							}
						}
					}
					else
					{
						LineOrderTileMarkerRenderableArray.Add(new SpriteRenderable(LineOrderTileMarkerSprite, pos, WVec.Zero, 0, LineOrderTileMarkerPalette, 1.0f, 0.75f, new float3(1.0f, 1.0f, 1.0f), TintModifiers.None, true, WAngle.Zero));
					}
				}

				//if (CurrentOrderMarkers.Count < LineOrderMarkerRenderableArray.Count)
				//{
					LineOrderMarkerRenderableArray.Clear();
				//}

				while (CurrentOrderMarkers.Count > LineOrderMarkerRenderableArray.Count)
				{
					WPos pos = CurrentOrderMarkers[LineOrderMarkerRenderableArray.Count];
					if (bLineOrderMarkerAnimates)
					{
						IRenderable[] animrenderables = LineOrderMarkerAnimation.Render(pos, LineOrderMarkerPalette);
						foreach (IRenderable renderable in animrenderables)
						{
							if (renderable is SpriteRenderable)
							{
								LineOrderMarkerRenderableArray.Add((SpriteRenderable)renderable);
							}
						}
					}
					else
					{
						LineOrderMarkerRenderableArray.Add(new SpriteRenderable(LineOrderMarkerSprite, pos, WVec.Zero, 0, LineOrderMarkerPalette, 1.0f, 0.75f, new float3(1.0f, 1.0f, 1.0f), TintModifiers.None, true, WAngle.Zero));
					}
				}

				totalrenderables.AddRange(LineOrderTileMarkerRenderableArray.AsEnumerable<IRenderable>());
				totalrenderables.AddRange(LineOrderMarkerRenderableArray.AsEnumerable<IRenderable>());
			}

			if (IsValidCommandCircle)
			{
				WPos startwpos = OwningWorldRenderer.ProjectedPosition(DragStartMousePosition);
				WPos endwpos = OwningWorldRenderer.ProjectedPosition(CurrentMousePosition);
				WDist radius = new WDist((startwpos - endwpos).Length);
				totalrenderables.Add(new CircleAnnotationRenderable(startwpos, radius, 2, CurrentCircleColor, false));
			}

			return totalrenderables.ToArray<IRenderable>();
		}

		public virtual IEnumerable<IRenderable> RenderAnnotations(WorldRenderer wr, World world) { yield break; }

		public void Deactivate() { }

		bool IOrderGenerator.HandleKeyPress(KeyInput e) { return false; }

		public virtual void SelectionChanged(World world, IEnumerable<Actor> selected) { }

		public virtual IEnumerable<Order> Order(World world, CPos cell, int2 worldPixel, MouseInput mi)
		{
			List<Order> retval = new();

			if (!bInitialized)
			{
				return retval;
			}

			CurrentMousePosition = OwningWorldRenderer.Viewport.ViewToWorldPx(mi.Location);
			CurrentMouseTilePos = world.Map.CenterOfCell(cell);

			if ((!bLMBDown) && (mi.Button == MouseButton.Left) && (mi.Event == MouseInputEvent.Down))
			{
				bLMBDown = true;
				retval.AddRange(OnLMBDown(cell, worldPixel, mi));
			}
			else if (bLMBDown && (mi.Button == MouseButton.Left) && (mi.Event == MouseInputEvent.Up))
			{
				bLMBDown = false;
				retval.AddRange(OnLMBUp(cell, worldPixel, mi));
			}

			if ((!bRMBDown) && (mi.Button == MouseButton.Right) && (mi.Event == MouseInputEvent.Down))
			{
				bRMBDown = true;
				retval.AddRange(OnRMBDown(cell, worldPixel, mi));
			}
			else if (bRMBDown && (mi.Button == MouseButton.Right) && (mi.Event == MouseInputEvent.Up))
			{
				bRMBDown = false;
				retval.AddRange(OnRMBUp(cell, worldPixel, mi));
			}

			if ((mi.Event == MouseInputEvent.Move) && (CurrentMode == ECustomFormationsMode.CommandLine))
			{
				if (!CurrentMarkedCells.Contains(cell))
				{
					if ((Math.Abs(LastMarkedCell.X - cell.X) > 1) || (Math.Abs(LastMarkedCell.Y - cell.Y) > 1))
					{
						List<CPos> linetiles = BresenhamTileMarkingHelpers.PlotLine(LastMarkedCell, cell);

						for (int i = 0; i < linetiles.Count; i++)
						{
							if (!CurrentMarkedCells.Contains(linetiles[i]))
							{
								MarkTileForCommandLine(linetiles[i]);
							}
						}
					}
					else
					{
						// adjacent to last
						MarkTileForCommandLine(cell, false, false);
					}

					LastMarkedCell = cell;
				}
			}

			return retval;
		}

		public virtual string GetCursor(World world, CPos cell, int2 worldPixel, MouseInput mi)
		{
			return worldDefaultCursor;
		}

		// ~IOrderGenerator

		protected virtual bool OnInitialize(WorldRenderer inWorldRenderer, World inWorld)
		{
			if ((inWorldRenderer == null) || (inWorld == null) || (inWorld.Map == null) || (inWorld.LocalPlayer == null) || (inWorld.LocalPlayer.PlayerActor == null))
			{
				return false;
			}

			OwningWorld = inWorld;
			OwningWorldRenderer = inWorldRenderer;

			if (!ChromeMetrics.TryGet("AltSelectionColor", out altSelectionColor))
			{
				altSelectionColor = Color.White;
			}

			if (!ChromeMetrics.TryGet("CtrlSelectionColor", out ctrlSelectionColor))
			{
				ctrlSelectionColor = Color.White;
			}

			if (!ChromeMetrics.TryGet("NormalSelectionColor", out normalSelectionColor))
			{
				normalSelectionColor = Color.White;
			}

			return true;
		}

		protected virtual IEnumerable<Order> OnLMBDown(CPos inCell, int2 inWorldPixel, MouseInput inMouseInput)
		{
			yield break;
		}

		protected virtual IEnumerable<Order> OnLMBUp(CPos inCell, int2 inWorldPixel, MouseInput inMouseInput)
		{
			yield break;
		}

		protected virtual IEnumerable<Order> OnRMBDown(CPos inCell, int2 inWorldPixel, MouseInput inMouseInput)
		{
			yield break;
		}

		protected virtual IEnumerable<Order> OnRMBUp(CPos inCell, int2 inWorldPixel, MouseInput inMouseInput)
		{
			yield break;
		}

		protected void MarkTileForCommandLine(CPos inTile, bool bClearTiles = false, bool bFromLinePlot = true)
		{
			if (bClearTiles)
			{
				CurrentMarkedCells.Clear();
			}
			CurrentMarkedCells.Add(inTile);
			UpdateMarkerLocationsForCommandLine();
			if (!bFromLinePlot)
			{
				LastMarkedCell = inTile;
			}
		}

		protected void StartCommandCircle(Color inColor, ECircleCommandTargetMode inTargetMode)
		{
			CurrentMode = ECustomFormationsMode.CommandCircle;
			DragStartMousePosition = CurrentMousePosition;
			CurrentCircleTargetMode = inTargetMode;
			CurrentCircleColor = inColor;
		}

		protected IEnumerable<Order> EndCommandCircle(int2 inWorldPixel, MouseInput inMouseInput, string inOverrideCommand = null)
		{
			WPos circlecenter = OwningWorldRenderer.ProjectedPosition(DragStartMousePosition);
			WPos mouseworldpos = OwningWorldRenderer.ProjectedPosition(CurrentMousePosition);
			WDist radius = new WDist((mouseworldpos - circlecenter).Length);
			List<Actor> circleactors = OwningWorld.FindActorsOnCircle(circlecenter, radius).ToList();
			List<Target> targets = new();

			foreach (Actor actor in circleactors)
			{
				if (CurrentCircleTargetMode == ECircleCommandTargetMode.Allies)
				{
					if ((actor.Owner.IsAlliedWith(OwningWorld.LocalPlayer)) && actor.TraitsImplementing<ITargetable>().Any())
					{
						BitSet<TargetableType> enabledtargetabletypes = actor.GetEnabledTargetTypes();
						if (enabledtargetabletypes.Overlaps(CurrentCircleTargetFilter))
						{
							targets.Add(Target.FromActor(actor));
						}
					}
				}
				else if (CurrentCircleTargetMode == ECircleCommandTargetMode.Enemies)
				{
					if ((!actor.Owner.IsAlliedWith(OwningWorld.LocalPlayer)) && actor.TraitsImplementing<ITargetable>().Any())
					{
						BitSet<TargetableType> enabledtargetabletypes = actor.GetEnabledTargetTypes();
						if (enabledtargetabletypes.Overlaps(CurrentCircleTargetFilter))
						{
							targets.Add(Target.FromActor(actor));
						}
					}
				}
				else if (CurrentCircleTargetMode == ECircleCommandTargetMode.All)
				{
					if (actor.TraitsImplementing<ITargetable>().Any())
					{
						BitSet<TargetableType> enabledtargetabletypes = actor.GetEnabledTargetTypes();
						if (enabledtargetabletypes.Overlaps(CurrentCircleTargetFilter))
						{
							targets.Add(Target.FromActor(actor));
						}
					}
				}
			}

			if (targets.Any())
			{
				WPos centerpos = OrderGeneratorHelpers.GetCenterOfActorGroup(OwningWorld.Selection.Actors.ToList());
				List<Target> sortedtargets = OrderGeneratorHelpers.GetTargetsByDistance(centerpos, targets);
				yield return StartGiveOrders();

				for (int i = 0; i < sortedtargets.Count; i++)
				{
					CPos cell = OwningWorld.Map.CellContaining(sortedtargets[i].CenterPosition);
					var orders = OwningWorld.Selection.Actors
						.Select(a => OrderGeneratorHelpers.OrderForUnit(a, sortedtargets[i], cell, inMouseInput))
						.Where(o => o != null)
						.ToList();

					var actorsInvolved = orders.Select(o => o.Actor).Distinct();
					bool isqueued = (inMouseInput.Modifiers.HasModifier(Modifiers.Shift) || (i > 0));
					if (actorsInvolved.Any())
					{
						foreach (var o in orders)
						{
							yield return OrderGeneratorHelpers.CheckSameOrder(o.Order, o.Trait.IssueOrder(o.Actor, o.Order, o.Target, isqueued));
						}
					}
				}
			}

			CurrentMode = ECustomFormationsMode.None;
			CurrentCircleTargetMode = ECircleCommandTargetMode.None;
			yield break;
		}

		protected void StartCommandLine(CPos inStartTile)
		{
			if (CurrentMode == ECustomFormationsMode.CommandLine)
			{
				return;
			}

			CurrentMode = ECustomFormationsMode.CommandLine;
			DragStartMousePosition = CurrentMousePosition;

			if (bLineOrderTileMarkerAnimates)
			{
				LineOrderTileMarkerAnimation.PlayRepeating(LineOrderTileMarkerSequence.Name);
			}

			if (bLineOrderMarkerAnimates)
			{
				LineOrderMarkerAnimation.PlayRepeating(LineOrderMarkerSequence.Name);
			}

			MarkTileForCommandLine(inStartTile, true, false);
		}

		protected void UpdateMarkerLocationsForCommandLine()
		{
			CurrentOrderMarkers.Clear();
			int selectioncount = OwningWorld.Selection.Actors.Count();
			int cellcount = CurrentMarkedCells.Count;

			bool issingleunitline = (cellcount > 1) && (selectioncount == 1);

			if (issingleunitline)
			{
				// special case, a single unit is given a queued move order per tile
				foreach (CPos cell in CurrentMarkedCells)
				{
					CurrentOrderMarkers.Add(OwningWorld.Map.CenterOfCell(cell));
				}
			}
			else
			{
				List<Target> targets = new();
				List<CPos> cells = new();
				Dictionary<CPos, int> targetmap = GetCommandLineCells();
				foreach (var kv in targetmap)
				{
					CurrentOrderMarkers.Add(OwningWorld.Map.CenterOfCell(kv.Key));
				}
			}
		}

		protected Dictionary<CPos, int> GetCommandLineCells()
		{
			Dictionary<CPos, int> retval = new();
			int selectioncount = OwningWorld.Selection.Actors.Count();
			int cellcount = CurrentMarkedCells.Count;
			int remainingselectionactors = selectioncount;

			//early out if we have 0 cells marked
			if ((cellcount < 1) || (selectioncount < 1))
			{
				return retval;
			}

			while (remainingselectionactors >= cellcount)
			{
				for (int i = 0; i < cellcount; i++)
				{
					if (retval.ContainsKey(CurrentMarkedCells[i]))
					{
						retval[CurrentMarkedCells[i]]++;
					}
					else
					{
						retval.Add(CurrentMarkedCells[i], 1);
					}
				}

				remainingselectionactors -= cellcount;
			}

			if (remainingselectionactors > 0)
			{
				if (retval.ContainsKey(CurrentMarkedCells.First()))
				{
					retval[CurrentMarkedCells.First()]++;
				}
				else
				{
					retval.Add(CurrentMarkedCells.First(), 1);
				}

				remainingselectionactors--;

				double tilespacing = (double)cellcount / (double)remainingselectionactors;
				double accumulator = tilespacing;

				double floored = Math.Floor(accumulator);
				int currenttile = (int)floored;
				accumulator -= floored;

				while (remainingselectionactors > 1)
				{
					int idx = Math.Min(currenttile, CurrentMarkedCells.Count - 1);
					if (retval.ContainsKey(CurrentMarkedCells[idx]))
					{
						retval[CurrentMarkedCells[idx]]++;
					}
					else
					{
						retval.Add(CurrentMarkedCells[idx], 1);
					}

					accumulator += tilespacing;
					floored = Math.Floor(accumulator);
					currenttile += (int)floored;
					accumulator -= floored;

					remainingselectionactors--;
				}

				if (remainingselectionactors > 0)
				{
					if (retval.ContainsKey(CurrentMarkedCells.Last()))
					{
						retval[CurrentMarkedCells.Last()]++;
					}
					else
					{
						retval.Add(CurrentMarkedCells.Last(), 1);
					}
				}
			}

			return retval;
		}

		protected IEnumerable<Order> EndCommandLine(CPos inEndTile, int2 inWorldPixel, MouseInput inMouseInput, string inOverrideCommand = null)
		{
			if (CurrentMode != ECustomFormationsMode.CommandLine)
			{
				yield break;
			}

			int selectioncount = OwningWorld.Selection.Actors.Count();
			int cellcount = CurrentMarkedCells.Count;

			if (cellcount < 1)
			{
				yield break;
			}

			bool issingleunitline = (cellcount > 1) && (selectioncount == 1);

			if (cellcount == 1)
			{
				// tap
				IEnumerable<Order> orders = TapOrder(inEndTile, inWorldPixel, inMouseInput, inOverrideCommand);
				foreach (Order o in orders)
				{
					yield return o;
				}
			}

			if (issingleunitline)
			{
				// special case, a single unit is given a queued ground order per tile
				IEnumerable<Order> orders = GetCommandLineOrdersSingleUnit(inEndTile, inWorldPixel, inMouseInput, inOverrideCommand);
				foreach (Order o in orders)
				{
					yield return o;
				}
			}
			else
			{
				List<Target> targets = new();
				List<CPos> cells = new();
				Dictionary<CPos, int> targetmap = GetCommandLineCells();
				foreach (var kv in targetmap)
				{
					for (int i = 0; i < kv.Value; i++)
					{
						targets.Add(Target.FromCell(OwningWorld, kv.Key));
						cells.Add(kv.Key);
					}
				}

				IEnumerable<Order> orders = GetCommandLineOrders(OwningWorld.Selection.Actors.ToList(), targets, cells, inMouseInput, inOverrideCommand);
				foreach (Order o in orders)
				{
					yield return o;
				}
			}

			CurrentMode = ECustomFormationsMode.None;
			CurrentMarkedCells.Clear();
			CurrentOrderMarkers.Clear();
		}

		protected IEnumerable<Order> TapOrder(CPos inCell, int2 inWorldPixel, MouseInput inMouseInput, string inOverrideCommand = null)
		{
			var target = OrderGeneratorHelpers.TargetForInput(OwningWorld, inCell, inWorldPixel, inMouseInput);
			if (inOverrideCommand == null)
			{
				var orders = OwningWorld.Selection.Actors
					.Select(a => OrderGeneratorHelpers.OrderForUnit(a, target, inCell, inMouseInput))
					.Where(o => o != null)
					.ToList();

				var actorsInvolved = orders.Select(o => o.Actor).Distinct();
				if (actorsInvolved.Any())
				{
					yield return StartGiveOrders();

					foreach (var o in orders)
					{
						yield return OrderGeneratorHelpers.CheckSameOrder(o.Order, o.Trait.IssueOrder(o.Actor, o.Order, o.Target, inMouseInput.Modifiers.HasModifier(Modifiers.Shift)));
					}
				}
			}
			else
			{
				foreach (var actor in OwningWorld.Selection.Actors)
				{
					yield return new Order(inOverrideCommand, actor, target, inMouseInput.Modifiers.HasModifier(Modifiers.Shift));
				}
			}

			CurrentMode = ECustomFormationsMode.None;
			CurrentMarkedCells.Clear();
			CurrentOrderMarkers.Clear();
		}

		protected IEnumerable<Order> GetCommandLineOrdersSingleUnit(CPos inCell, int2 inWorldPixel, MouseInput inMouseInput, string inOverrideCommand = null)
		{
			Actor unitactor = OwningWorld.Selection.Actors.First();
			List<Target> targets = new();

			for (int i = 0; i < CurrentMarkedCells.Count; i++)
			{
				targets.Add(Target.FromCell(OwningWorld, CurrentMarkedCells[i]));
			}

			if (inOverrideCommand == null)
			{
				List<UnitOrderResult> orders = new();
				for (int i = 0; i < targets.Count; i++)
				{
					Target target = Target.FromCell(OwningWorld, CurrentMarkedCells[i]);
					orders.Add(OrderGeneratorHelpers.OrderForUnit(unitactor, target, CurrentMarkedCells[i], inMouseInput));
				}

				if (orders.Count > 0)
				{
					yield return StartGiveOrders();

					yield return OrderGeneratorHelpers.CheckSameOrder(orders[0].Order, orders[0].Trait.IssueOrder(orders[0].Actor, orders[0].Order, orders[0].Target, inMouseInput.Modifiers.HasModifier(Modifiers.Shift)));

					foreach (UnitOrderResult o in orders)
					{
						yield return OrderGeneratorHelpers.CheckSameOrder(o.Order, o.Trait.IssueOrder(o.Actor, o.Order, o.Target, true));
					}
				}
			}
			else
			{
				if (targets.Count > 0)
				{
					yield return new Order(inOverrideCommand, unitactor, targets[0], inMouseInput.Modifiers.HasModifier(Modifiers.Shift));
					for (int i = 1; i < targets.Count; i++)
					{
						yield return new Order(inOverrideCommand, unitactor, targets[i], true);
					}
				}
			}
		}

		protected IEnumerable<Order> GetCommandLineOrdersLessTilesThanUnits(CPos inCell, int2 inWorldPixel, MouseInput inMouseInput, string inOverrideCommand = null)
		{
			List<Actor> selectionactors = OwningWorld.Selection.Actors.ToList();
			int unitspertile = (int)Math.Ceiling((float)selectionactors.Count / (float)CurrentMarkedCells.Count);
			List<Target> targets = new();
			List<CPos> cells = new();
			for (int i = 0; i < CurrentMarkedCells.Count; i++)
			{
				for (int j = 0; j < unitspertile; j++)
				{
					targets.Add(Target.FromCell(OwningWorld, CurrentMarkedCells[i]));
					cells.Add(CurrentMarkedCells[i]);
				}
			}

			return GetCommandLineOrders(selectionactors, targets, cells, inMouseInput, inOverrideCommand);
		}

		protected IEnumerable<Order> GetCommandLineOrdersMoreTilesThanUnits(CPos inCell, int2 inWorldPixel, MouseInput inMouseInput, string inOverrideCommand = null)
		{
			List<Actor> selectionactors = OwningWorld.Selection.Actors.ToList();
			List<UnitOrderResult> orders = new();
			List<Target> targets = new();
			// why cant i get cell out of target lol
			List<CPos> cells = new();

			targets.Add(Target.FromCell(OwningWorld, CurrentMarkedCells.First()));
			cells.Add(CurrentMarkedCells.First());

			int remainder = selectionactors.Count - 1;
			int tilespacing = (int)Math.Ceiling((float)CurrentMarkedCells.Count / (float)remainder);

			int currenttile = tilespacing;

			for (int i = 1; i < selectionactors.Count - 1; i++)
			{
				int idx = Math.Min(currenttile, CurrentMarkedCells.Count - 1);
				targets.Add(Target.FromCell(OwningWorld, CurrentMarkedCells[idx]));
				cells.Add(CurrentMarkedCells[idx]);
				currenttile += tilespacing;
			}

			targets.Add(Target.FromCell(OwningWorld, CurrentMarkedCells.Last()));
			cells.Add(CurrentMarkedCells.Last());

			return GetCommandLineOrders(selectionactors, targets, cells, inMouseInput, inOverrideCommand);
		}

		protected IEnumerable<Order> GetCommandLineOrdersEqualTilesAndUnits(CPos inCell, int2 inWorldPixel, MouseInput inMouseInput, string inOverrideCommand = null)
		{
			List<Actor> selectionactors = OwningWorld.Selection.Actors.ToList();
			List<UnitOrderResult> orders = new();
			List<Target> targets = new();
			List<CPos> cells = new();

			for (int i = 0; i < CurrentMarkedCells.Count; i++)
			{
				targets.Add(Target.FromCell(OwningWorld, CurrentMarkedCells[i]));
				cells.Add(CurrentMarkedCells[i]);
			}

			return GetCommandLineOrders(selectionactors, targets, cells, inMouseInput, inOverrideCommand);
		}

		protected IEnumerable<Order> GetCommandLineOrders(List<Actor> inActors, List<Target> inTargets, List<CPos> inCells, MouseInput inMouseInput, string inOverrideCommand = null)
		{
			List<UnitOrderResult> orders = new();
			List<Actor> sortedactors = AssignmentProblemHelpers.AssignUnitsToTargets(inActors, inTargets);

			int ordercount = Math.Min(Math.Min(sortedactors.Count, inTargets.Count), inCells.Count);

			bool queued = inMouseInput.Modifiers.HasModifier(Modifiers.Shift);

			if (inOverrideCommand == null)
			{
				for (int i = 0; i < ordercount; i++)
				{
					orders.Add(OrderGeneratorHelpers.OrderForUnit(sortedactors[i], inTargets[i], inCells[i], inMouseInput));
				}

				yield return StartGiveOrders();

				foreach (UnitOrderResult o in orders)
				{
					yield return OrderGeneratorHelpers.CheckSameOrder(o.Order, o.Trait.IssueOrder(o.Actor, o.Order, o.Target, queued));
				}
			}
			else
			{
				for (int i = 0; i < ordercount; i++)
				{
					yield return new Order(inOverrideCommand, sortedactors[i], inTargets[i], queued);
				}
			}
		}

		protected Order StartGiveOrders()
		{
			if (OwningWorld.Selection.Actors.Count() < 0)
			{
				return new Order();
			}
			// HACK: This is required by the hacky player actions-per-minute calculation
			// TODO: Reimplement APM properly and then remove this
			return new Order("CreateGroup", OwningWorld.Selection.Actors.First().Owner.PlayerActor, false, OwningWorld.Selection.Actors.ToArray());
		}
	}

	public class OrderGeneratorHelpers
	{
		public static Target TargetForInput(World world, CPos cell, int2 worldPixel, MouseInput mi)
		{
			var actor = world.ScreenMap.ActorsAtMouse(mi)
				.Where(a => !a.Actor.IsDead && a.Actor.Info.HasTraitInfo<ITargetableInfo>() && !world.FogObscures(a.Actor))
				.WithHighestSelectionPriority(worldPixel, mi.Modifiers);

			if (actor != null)
				return Target.FromActor(actor);

			var frozen = world.ScreenMap.FrozenActorsAtMouse(world.RenderPlayer, mi)
				.Where(a => a.Info.HasTraitInfo<ITargetableInfo>() && a.Visible && a.HasRenderables)
				.WithHighestSelectionPriority(worldPixel, mi.Modifiers);

			if (frozen != null)
				return Target.FromFrozenActor(frozen);

			return Target.FromCell(world, cell);
		}

		// Used for classic mouse orders, determines whether or not action at xy is move or select
		public static bool InputOverridesSelection(World world, int2 xy, MouseInput mi)
		{
			var actor = world.ScreenMap.ActorsAtMouse(xy)
				.Where(a => !a.Actor.IsDead && a.Actor.Info.HasTraitInfo<ISelectableInfo>() && (a.Actor.Owner.IsAlliedWith(world.RenderPlayer) || !world.FogObscures(a.Actor)))
				.WithHighestSelectionPriority(xy, mi.Modifiers);

			if (actor == null)
				return true;

			var target = Target.FromActor(actor);
			var cell = world.Map.CellContaining(target.CenterPosition);
			var actorsAt = world.ActorMap.GetActorsAt(cell).ToList();

			var modifiers = TargetModifiers.None;
			if (mi.Modifiers.HasModifier(Modifiers.Ctrl))
				modifiers |= TargetModifiers.ForceAttack;
			if (mi.Modifiers.HasModifier(Modifiers.Shift))
				modifiers |= TargetModifiers.ForceQueue;
			if (mi.Modifiers.HasModifier(Modifiers.Alt))
				modifiers |= TargetModifiers.ForceMove;

			foreach (var a in world.Selection.Actors)
			{
				var o = OrderForUnit(a, target, cell, mi);
				if (o != null && o.Order.TargetOverridesSelection(a, target, actorsAt, cell, modifiers))
					return true;
			}

			return false;
		}

		/// <summary>
		/// Returns the most appropriate order for a given actor and target.
		/// First priority is given to orders that interact with the given actors.
		/// Second priority is given to actors in the given cell.
		/// </summary>
		public static UnitOrderResult OrderForUnit(Actor self, Target target, CPos xy, MouseInput mi)
		{
			if (mi.Button != Game.Settings.Game.MouseButtonPreference.Action)
				return null;

			if (self.Owner != self.World.LocalPlayer)
				return null;

			if (self.World.IsGameOver)
				return null;

			if (self.Disposed || !target.IsValidFor(self))
				return null;

			var modifiers = TargetModifiers.None;
			if (mi.Modifiers.HasModifier(Modifiers.Ctrl))
				modifiers |= TargetModifiers.ForceAttack;
			if (mi.Modifiers.HasModifier(Modifiers.Shift))
				modifiers |= TargetModifiers.ForceQueue;
			if (mi.Modifiers.HasModifier(Modifiers.Alt))
				modifiers |= TargetModifiers.ForceMove;

			// The Select(x => x) is required to work around an issue on mono 5.0
			// where calling OrderBy* on SelectManySingleSelectorIterator can in some
			// circumstances (which we were unable to identify) replace entries in the
			// enumeration with duplicates of other entries.
			// Other action that replace the SelectManySingleSelectorIterator with a
			// different enumerator type (e.g. .Where(true) or .ToList()) also work.
			var orders = self.TraitsImplementing<IIssueOrder>()
				.SelectMany(trait => trait.Orders.Select(x => new { Trait = trait, Order = x }))
				.Select(x => x)
				.OrderByDescending(x => x.Order.OrderPriority);

			for (var i = 0; i < 2; i++)
			{
				foreach (var o in orders)
				{
					var localModifiers = modifiers;
					string cursor = null;
					if (o.Order.CanTarget(self, target, ref localModifiers, ref cursor))
						return new UnitOrderResult(self, o.Order, o.Trait, cursor, target);
				}

				// No valid orders, so check for orders against the cell
				target = Target.FromCell(self.World, xy);
			}

			return null;
		}

		public static Order CheckSameOrder(IOrderTargeter iot, Order order)
		{
			if (order == null && iot.OrderID != null)
				TextNotificationsManager.Debug("BUG: in order targeter - decided on {0} but then didn't order", iot.OrderID);
			else if (order != null && iot.OrderID != order.OrderString)
				TextNotificationsManager.Debug("BUG: in order targeter - decided on {0} but ordered {1}", iot.OrderID, order.OrderString);
			return order;
		}

		struct TargetAndDistance : IComparable<TargetAndDistance>
		{
			public Target Target;
			public int Distance;

			public TargetAndDistance(Target t, int d)
			{
				Target = t;
				Distance = d;
			}

			public static bool operator >(TargetAndDistance A, TargetAndDistance B)
			{
				return A.Distance > B.Distance;
			}

			public static bool operator <(TargetAndDistance A, TargetAndDistance B)
			{
				return A.Distance < B.Distance;
			}

			public static bool operator >=(TargetAndDistance A, TargetAndDistance B)
			{
				return A.Distance >= B.Distance;
			}

			public static bool operator <=(TargetAndDistance A, TargetAndDistance B)
			{
				return A.Distance <= B.Distance;
			}

			public int CompareTo(TargetAndDistance other)
			{
				return Distance.CompareTo(other.Distance);
			}
		}
		public static List<Target> GetTargetsByDistance(WPos inReferencePosition, List<Target> inTargets)
		{
			List<Target> retval = new List<Target>();
			List<TargetAndDistance> presort = new List<TargetAndDistance>();
			foreach (Target t in inTargets)
			{
				presort.Add(new TargetAndDistance(t, (inReferencePosition - t.CenterPosition).Length));
			}

			presort.Sort();

			foreach (TargetAndDistance ps in presort)
			{
				retval.Add(ps.Target);
			}

			return retval;

		}

		public static WPos GetCenterOfActorGroup(List<Actor> inActors)
		{
			List<WPos> positions = new();
			foreach (Actor a in inActors)
			{
				positions.Add(a.CenterPosition);
			}

			int minx = 0;
			int maxx = 0;
			int miny = 0;
			int maxy = 0;
			bool first = true;

			foreach (WPos pos in positions)
			{
				if (first)
				{
					minx = pos.X;
					maxx = pos.X;
					miny = pos.Y;
					maxy = pos.Y;
					first = false;
					continue;
				}

				if (maxx < pos.X)
				{
					maxx = pos.X;
				}

				if (minx > pos.X)
				{
					minx = pos.X;
				}

				if (maxy < pos.Y)
				{
					maxy = pos.Y;
				}

				if (miny > pos.Y)
				{
					miny = pos.Y;
				}
			}

			int diffx = maxx - minx;
			int diffy = maxx - minx;
			int midx = minx + (int)Math.Floor((float)diffx / 2.0f);
			int midy = miny + (int)Math.Floor((float)diffy / 2.0f);
			return new WPos(midx, midy, 0);
		}

		public static WPos GetCenterOfTargetGroup(List<Target> inTargets)
		{
			List<WPos> positions = new();
			foreach (Target t in inTargets)
			{
				positions.Add(t.CenterPosition);
			}

			int minx = 0;
			int maxx = 0;
			int miny = 0;
			int maxy = 0;
			bool first = true;

			foreach (WPos pos in positions)
			{
				if (first)
				{
					minx = pos.X;
					maxx = pos.X;
					miny = pos.Y;
					maxy = pos.Y;
					first = false;
					continue;
				}

				if (maxx < pos.X)
				{
					maxx = pos.X;
				}

				if (minx > pos.X)
				{
					minx = pos.X;
				}

				if (maxy < pos.Y)
				{
					maxy = pos.Y;
				}

				if (miny > pos.Y)
				{
					miny = pos.Y;
				}
			}

			int diffx = maxx - minx;
			int diffy = maxx - minx;
			int midx = minx + (int)Math.Floor((float)diffx / 2.0f);
			int midy = miny + (int)Math.Floor((float)diffy / 2.0f);
			return new WPos(midx, midy, 0);
		}
	}

	public class BresenhamTileMarkingHelpers
	{
		public static List<CPos> PlotLine(CPos StartPos, CPos EndPos)
		{
			if (Math.Abs(EndPos.Y - StartPos.Y) < Math.Abs(EndPos.X - StartPos.X))
			{
				if (StartPos.X > EndPos.X)
				{
					return PlotLineLow(EndPos, StartPos);
				}
				else
				{
					return PlotLineLow(StartPos, EndPos);
				}
			}
			else
			{
				if (StartPos.Y > EndPos.Y)
				{
					return PlotLineHigh(EndPos, StartPos);
				}
				else
				{
					return PlotLineHigh(StartPos, EndPos);
				}
			}
		}

		public static List<CPos> PlotLineLow(CPos StartPos, CPos EndPos)
		{
			List<CPos> retval = new();
			int dx = EndPos.X - StartPos.X;
			int dy = EndPos.Y - StartPos.Y;
			int yi = 1;

			if (dy < 0)
			{
				yi = -1;
				dy = -dy;
			}

			int D = (2 * dy) - dx;
			int y = StartPos.Y;

			for (int x = StartPos.X; x <= EndPos.X; x++)
			{
				retval.Add(new CPos(x, y, StartPos.Layer));
				if (D > 0)
				{
					y = y + yi;
					D = D + (2 * (dy - dx));
				}
				else
				{
					D = D + 2 * dy;
				}
			}

			return retval;
		}

		public static List<CPos> PlotLineHigh(CPos StartPos, CPos EndPos)
		{
			List<CPos> retval = new();
			int dx = EndPos.X - StartPos.X;
			int dy = EndPos.Y - StartPos.Y;
			int xi = 1;

			if (dx < 0)
			{
				xi = -1;
				dx = -dx;
			}

			int D = (2 * dx) - dy;
			int x = StartPos.X;

			for (int y = StartPos.Y; y <= EndPos.Y; y++)
			{
				retval.Add(new CPos(x, y, StartPos.Layer));
				if (D > 0)
				{
					x = x + xi;
					D = D + (2 * (dx - dy));
				}
				else
				{
					D = D + 2 * dx;
				}
			}

			return retval;
		}
	}

	public class AssignmentProblemHelpers
	{
		public static List<Actor> AssignUnitsToTargets(List<Actor> inActors, List<Target> inTargets)
		{
			int goalcount = Math.Min(inActors.Count, inTargets.Count);
			if (inActors == null || goalcount == 0)
			{
				return new List<Actor>();
			}
			List<Actor> retval = new();
			double[][] costMatrix = new double[goalcount][];

			for (int i = 0; i < goalcount; i++)
			{
				costMatrix[i] = new double[goalcount];

				for (int j = 0; j < goalcount; j++)
				{
					costMatrix[i][j] = (inTargets[i].CenterPosition - inActors[j].CenterPosition).Length;
				}
			}

			Munkres munkres = new Munkres(costMatrix);
			munkres.Minimize();
			double[] solution = munkres.Solution;
			int[] assignments = Enumerable.Range(0, inActors.Count).OrderBy(a => solution[a]).ToArray();
			retval = assignments.Select(i => inActors[i]).ToList();
			return retval;
		}
	}
}
