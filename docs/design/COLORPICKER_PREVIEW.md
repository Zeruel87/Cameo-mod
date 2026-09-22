# Colour-picker preview — every faction, no clone actors

**Maintainer order, 2026-09-07.** Status: **SPECIFIED, NOT BUILT.**

> *"I want all factions to automatically have something like that, but with a C# trait
> that always uses the main building and recolors it instead of a separate
> `conyard.colorpicker` actor. We have only done that so far for TD and RA factions like
> Japan — but it should be done with everything."*

## The actual state, verified 2026-09-07 — it is worse than "done for TD and RA"

Four clone actors exist in `mods/cameo/rules/misc.yaml:370-397`:

| actor | image | wired up? |
|---|---|---|
| `fact.colorpicker` | `fact` (TD conyard) | **NO — dead, nothing references it** |
| `rafact.colorpicker` | `rafactcolor` (RA conyard) | **NO — dead** |
| `rafactj.colorpicker` | `rafactj` (RA Japan conyard) | **NO — dead** |
| `ra1_soviets_sovietmammothtank.colorpicker` | mammoth tank | yes, the single global preview |

`rules/world.yaml:1339` sets `ColorPickerManager.PreviewActor:` to the **mammoth tank**,
and there is **no `FactionPreviewActors` block anywhere in the tree.**

So the TD/RA/Japan conyard previews were *started and never connected* — three dead
actors, and every faction currently previews a Soviet mammoth tank. Confirmed by grep:
nothing outside `misc.yaml` mentions those three ids.

## Half of it already ships in the engine

`ColorPickerManager` (`engine/OpenRA.Mods.Common/Traits/World/ColorPickerManager.cs:55`):

```csharp
[Desc("Actor type to show in the color picker for specific factions. Overrides PreviewActor.")]
public readonly FrozenDictionary<string, string> FactionPreviewActors
```

Per-faction previews need **zero C#** — one yaml table. But used as-is it needs one
`.colorpicker` clone per faction (~31 dead-weight actors, each another id to keep
renamed), which is exactly what the maintainer objects to.

## Why the clones exist at all

Only to override `RenderSprites.Palette` to a live `ColorPickerPalette`. A real actor
renders through `PlayerPalette + ownerName` (`RenderSprites.cs:53`), fixed at world load,
so it cannot follow the slider.

## The build — a Cameo shadow, no engine fork

The engine already tags the preview: `ColorPickerManager.cs:214` passes
`ActorPreviewType.ColorPicker` into `IActorPreviewInitInfo.ActorPreviewInits`
(enum at `TraitsInterfaces.cs:531`). **Nothing in `RenderSprites` consumes it.** That is
the whole gap.

1. **Shadow `RenderSprites` in `OpenRA.Mods.Cameo`** so that when the preview is built
   for `ActorPreviewType.ColorPicker`, the palette resolves to the live colour-picker
   palette instead of `PlayerPalette + ownerName`. Then **any actor is its own preview**,
   in the picked colour, with no clone and no `Palette:` override.

   ⭐ **The shadow route is confirmed open**: `ObjectCreator.FindType` takes the first
   assembly in `mod.yaml`'s `Assemblies` list — AS, CA, **Cameo**, Cnc, D2k, Common —
   and **neither AS nor CA defines `RenderSprites`**, so a Cameo type of that name wins
   with zero yaml changes. Precedents: `ColorPickerColorShift`, `PlayerColorShift`,
   `SelectionDecorations`. **No `mod.config` bump, no `make all`.**

   ⚠ Prove the shadow the sanctioned way: give the Cameo Info a field the Common one
   lacks and boot with that field set. `--docs` lists both types and proves nothing.

2. **Resolve each faction's construction yard from data**, not from a hand-written table.
   Every faction has one and it is identifiable from the roster without a new list. A
   hand-maintained `FactionPreviewActors` of ~31 rows rots the moment a conyard is
   renamed — and there are ~450 renames still queued across the faction lanes.

3. **Delete the four clone actors** and the `PreviewActor` line.

4. Rebuild (`dotnet build -c Release --nologo -p:TargetPlatform=win-x64` → `engine/bin`),
   boot-gate, and verify the picker live. ⭐ Observer/menu UI can be verified without
   playing a match by launching with `Launch.Replay=<file>` — that is how the spectator
   set was verified.

**Net: −4 actors, −31 never created, +1 trait, and the picker works for every faction
including ones that do not exist yet.**

## Related, and probably already fine

The maintainer also asked about **a fallback actor for Random**. `ColorPickerManager`
falls back to `PreviewActor` whenever the faction is `null` or missing from
`FactionPreviewActors`, and throws a `YamlException` only if `PreviewActor` is also
unset — so keeping one global `PreviewActor` as the Random/unknown case is already the
engine's behaviour. **Verify this once the per-faction path exists**; do not remove
`PreviewActor` when deleting the clones — repoint it at a real actor instead.

⚠ This is a **C# change**: not a naming-lane task, and it does not outrank the balance
pipeline. Pick it up as one self-contained item.
