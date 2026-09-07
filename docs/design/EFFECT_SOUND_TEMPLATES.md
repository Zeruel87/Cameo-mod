# Paired effect+sound templates — one inherit carries both

**Maintainer order, 2026-09-07.** Status: **SPECIFIED, NOT BUILT.** This document is the
spec; nothing has been implemented yet.

---

## The order, in the maintainer's words

> *"What I wanted for the effects was to make a new inherit list for all the different
> effects we have from each game and then name them like the file name and map a fitting
> sound together with the visual effect so the two things are always linked as a single
> inherit. For example let's say the effect is called big explosion and is from D2K then
> name the effect `^d2k_big_explosion` and map the sound effect that usually goes with
> that effect."*

Prompted by a concrete symptom: **the Dune rocket trooper's inherited effect sounds
wrong** — the visual and the audio do not belong together, because they are chosen
independently today.

## The problem

A `CreateEffect` warhead carries the visual (`Explosions:` / `Image:` / `Sequence:`) and
the audio (`ImpactSounds:`) as **separate fields that nothing keeps in step**. Two
weapons using the same explosion sprite can carry different sounds, and a weapon can
inherit a visual from one template and a sound from another — or declare one locally and
inherit the other. `audit_weapon_shape` W6 counts **694 weapons declaring an effect
warhead locally**, so this is the common case, not the exception.

There is no place where "this sprite goes with this sound" is written down once.

## Measured, 2026-09-07 — the problem is real and sized

```
CreateEffect warheads on concrete weapons     6987
   with a visual  5010     with a sound  5985     with BOTH  4008
distinct (visual, sound) pairings              331
visuals used with MORE THAN ONE sound           68   <- the mismatches
```

Only **4008 of 6987** effect warheads carry both halves; the rest are half-specified.
And 68 sprites are each paired with several different sounds, e.g.

```
small_poof           -> expnew13.aud / kaboom12.aud / kaboom15.aud
small_frag           -> expnew09.aud / expnew12.aud / expnew14.aud
piffs                -> EXPLSML1.WAV / kaboom12.aud / kaboom15.aud
small_explosion_air  -> kaboom25.aud / xplos.aud
```

### The reported symptom, located — and it is CROSS-GAME

The maintainer's correction, 2026-09-07: *"`xplobig4.aud` is not a D2K sound at all!
That's a sound from Tiberian Dawn!"* — correct, and confirmed against the reference.

`tools/audit/extract_reference_effects.py` reads the upstream mods that ship in
`engine/mods/` and prints what each game actually pairs. The tell is unmistakable:

```
d2k    EXPLSML1.WAV  EXPLMD2.WAV  EXPLLG3.WAV   uppercase .WAV, EXPL* family
cnc    xplos.aud  xplobig4.aud  flamer2.aud     .aud
ra     kaboom12.aud  firebl3.aud  splash9.aud   .aud
```

`xplobig4.aud` is **Tiberian Dawn's** sound for `big_frag`, `med_frag` and `small_poof`.
So the Dune rocket trooper plays a big TD explosion over a tiny Dune sprite:

```
D2K_Rocket_Trooper      d2k_tiny_explosion  + xplobig4.aud   ⛔ TD sound on a D2k visual
D2K_Rocket_Trooper2     d2k_small_napalm    + kaboom12.aud   ⛔ RA sound on a D2k visual
D2K_Rocket_Trooper_AA   d2k_small_explosion + EXPLSML1.WAV   ✅ correct — this IS the
                                                                canonical d2k pairing
```

⚠ **I got the third one wrong first time** and called `EXPLSML1.WAV` "a RA/TD sound".
It is not: the reference shows `small_explosion -> EXPLSML1.WAV` is exactly what Dune
2000 ships. **Read the reference before judging a pairing** — the extension alone
(`.WAV` vs `.aud`) already separates d2k from cnc/ra.

## The canonical pairings, extracted not invented

`python tools/audit/extract_reference_effects.py` prints the live table from
`engine/mods/`. **Run it rather than trusting a copy** — the numbers below are a snapshot
of 2026-09-07 and the tool is the authority.

```
=== d2k  -  10 visuals, 3 used with more than one sound
    building                   EXPLHG1.WAV, EXPLLG2.WAV, EXPLLG3.WAV, EXPLSML2.WAV, EXPLSML4.WAV  <-- AMBIGUOUS
    devastator                 EXPLLG5.WAV
    large_explosion            EXPLLG2.WAV, EXPLSML4.WAV  <-- AMBIGUOUS
    med_explosion              EXPLMD2.WAV, EXPLSML2.WAV  <-- AMBIGUOUS
    nuke                       EXPLLG2.WAV
    self_destruct              EXPLSML1.WAV
    shockwave                  EXPLMD4.WAV
    small_explosion            EXPLSML1.WAV
    small_napalm               EXPLSML2.WAV
    wall_explosion             EXPLHG1.WAV

Pair a visual only with a sound from ITS OWN mod. Cross-game pairing is the defect this table exists to prevent.
```

⚠ **The reference is not unanimous, and that is the real finding.** Three of the ten d2k
visuals are used with more than one sound *in Dune 2000 itself* — `building` alone spans
five. So the job is **not** a mechanical merge:

* where a visual has exactly one sound in the reference, that pairing is settled — take it;
* where it has several, **that is a design decision for the maintainer**, and it must be
  presented with usage counts, not resolved by picking the first one.

**Start with Dune 2000**, per the maintainer: smallest set, it is the reported symptom,
and its sounds are unmistakable so a mistake is obvious by ear.

## The design

**One template per real effect, named after the source game and the effect's own file
name, carrying BOTH halves.** The name is the contract:

```
^d2k_big_explosion          the D2k large-explosion sprite + the sound that ships with it
^ra1_napalm_burst
^ts_ion_impact
```

* `^<game>_<effect_file_stem>` — no invented names. **Read the actual sprite/sequence
  names and use them**; interpret only where a filename is unreadable, and record the
  interpretation in this file.
* ⛔ **Name the effect for WHAT IT IS, never for the weapon that fires it.**
  `^d2k_napalm_small`, not `^Effect_HeavyFlame`. A role name is what let a "medium
  explosion" template pick up whatever sound was nearest; a name taken from the sprite
  cannot drift, because the sprite is the thing being named.
* ⛔ **NEVER pair a visual from one game with a sound from another.** Every template's
  two halves come from the same mod. This is the defect the maintainer heard, and
  `extract_reference_effects.py` exists to make the correct pairing checkable rather
  than a matter of taste.
* Every template sets the visual **and** `ImpactSounds` together. Neither half is ever
  set on a weapon.
* This slots straight into the ONE-WARHEAD / THREE-INHERIT law (DESIGN §11b.1): the
  effect inherit is the third of the three, so **a weapon gets its effect exactly once,
  as `Inherits@fx: ^<game>_<effect>`**, and W6 falls as the templates land.

## Why the naming rule matters more than it looks

Naming a template after the **file** rather than after a role (`^Effect_Big`,
`^Effect_Medium`) means two people cannot disagree about which sprite it is, and a
missing pairing is visible as a missing file. Role-named effect templates are what
allowed a Dune rocket trooper to end up with a mismatched sound in the first place: the
role said "medium explosion", and the sound that got attached was whatever the nearest
template happened to carry.

## Build order

1. **Inventory.** Enumerate every effect sprite actually referenced by a `CreateEffect`
   warhead, grouped by source game, with the sounds each is currently paired with. Where
   one sprite already has a dominant sound, that is the pairing — **measure it, do not
   invent it.**
2. **Report the conflicts.** Any sprite used with more than one sound is a design
   decision, not a merge: list them for the maintainer with the usage counts.
3. **Generate the templates** into the shared effect file, `^<game>_<stem>`, each with
   the visual and `ImpactSounds` together.
4. **Convert weapons in batches**, `Inherits@fx:` only, deleting the local effect
   warhead. Boot-gate each batch. W6 must fall and never rise.
5. **Guard it**: an audit that fails when a weapon declares an effect visual or an
   `ImpactSounds` locally instead of inheriting a paired template.

⚠ **Start with the Dune rocket trooper**, since that is the reported symptom and it will
show immediately whether the pairing is right.

⛔ **This touches warheads.** `CreateEffect` warheads are warheads, and DESIGN forbids
changing a warhead without explicit permission — this document IS that permission for
the effect half, and for nothing else. Damage warheads, `Burst` and `BurstDelays` are
untouched.

## Open questions for the maintainer

1. Where do the templates live — one shared file per game, or one global effect file?
2. What happens to an effect with **no** sound today: pick a neighbour's, or leave
   `ImpactSounds` unset and record it as a gap?
3. Cross-game reuse — may an RA2 weapon inherit `^d2k_big_explosion` if that is genuinely
   the right sprite, or does each game get its own copy?
