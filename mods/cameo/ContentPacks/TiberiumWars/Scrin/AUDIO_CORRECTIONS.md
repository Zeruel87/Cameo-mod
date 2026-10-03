# PAC and Drone Platform audio correction — 2026-09-07

- PAC select: all 11 `ALI_PAC_SoundSelect` variants.
- PAC move/action: six `ALI_PAC_SoundMoveStart` clips, replacing copied selection sounds. Using these as order acknowledgements is an OpenRA adaptation of CNC3's movement-start event.
- PAC attack: all six `ALI_PAC_SoundAttack` variants.
- PAC death: all five `ALI_PAC_SoundDie` variants.
- Drone Platform select: `ALI_DronePlatform_Select` / `ABDrone_selecta`.

Re-extracted from the installed Kane's Wrath `Core/1.0/GlobalStream.big`, using the decoded `global_common.manifest` event-to-AudioFile references. Encoded directly from EA XAS CData to mono 22050 Hz Westwood IMA ADPCM AUD (512-byte blocks). No speech normalization, pitch shift, time stretch, or synthesized replacement. Original event-level volume/random-pitch logic is not recreated.

The raw source dynamics are retained: PAC select 1 measures mean -15.7 dB / peak approximately 0 dBFS, versus the previous -11.9 / -1.4. Drone Platform select measures -15.0 / -0.7, versus -14.5 / -2.2. These are effects, not spoken barks; compression was deliberately removed instead of matching the loudness of human speech.

Validation: 29 clips; codec, sample rate and mono checks passed. All AUD chunk sentinels, input extents and decoded-size totals match their headers. FFmpeg emits an EOF demux warning on both previous and replacement AUDs; this is not used as a clean decoder-test claim. All voice references exist. No gameplay, sprite, engine or debug-map changes belong to this audio correction. In-game listening remains user validation.
