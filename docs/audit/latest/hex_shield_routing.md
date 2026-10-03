# Hex-shield routing audit

Resolved shield receivers: **1772**
Dormant non-shield footprint actors: **378**
Other dormant overlay actors: **0**
Total actors carrying shield overlays: **2150**
Errors: **18**

- scrin_drone_ship: concrete actor defines shield sizing in WithIdleOverlay@shield1
- scrin_drone_ship: concrete actor defines shield sizing in WithIdleOverlay@shield_damage
- scrin_drone_ship: unsupported resolved shield route ('hexshield_sphere', 'colossal-mobile-west')
- scrin_devastator_warship: concrete actor defines shield sizing in WithIdleOverlay@shield1
- scrin_devastator_warship: concrete actor defines shield sizing in WithIdleOverlay@shield_damage
- scrin_devastator_warship: unsupported resolved shield route ('hexshield_directional_oval', 'aircraft-large-west')
- scrin_planetary_assault_carrier: concrete actor defines shield sizing in WithIdleOverlay@shield1
- scrin_planetary_assault_carrier: concrete actor defines shield sizing in WithIdleOverlay@shield_damage
- scrin_planetary_assault_carrier: unsupported resolved shield route ('hexshield_directional_oval', 'aircraft-colossal')
- scrin_mothership: concrete actor defines shield sizing in WithIdleOverlay@shield1
- scrin_mothership: concrete actor defines shield sizing in WithIdleOverlay@shield_damage
- scrin_mothership: unsupported resolved shield route ('hexshield_sphere', 'capital-mobile-standard')
- protoss_carrier: concrete actor defines shield sizing in WithIdleOverlay@shield1
- protoss_carrier: concrete actor defines shield sizing in WithIdleOverlay@shield_damage
- protoss_carrier: unsupported resolved shield route ('hexshield_directional_oval', 'aircraft-colossal')
- protoss_starshipsovereign: concrete actor defines shield sizing in WithIdleOverlay@shield1
- protoss_starshipsovereign: concrete actor defines shield sizing in WithIdleOverlay@shield_damage
- protoss_starshipsovereign: unsupported resolved shield route ('hexshield_directional_oval', 'aircraft-colossal')

Selection-box consistency warnings: **23**

- td_gdi_advancedguardtower: selection-box route mismatch ('hexshield_dome', 'dome-1x1') != ('hexshield_dome', 'dome-1x2')
- ra1_advancedpowerplant: selection-box route mismatch ('hexshield_dome', 'dome-3x2') != ('hexshield_dome', 'dome-3x3')
- ra1_allies_gapgenerator: selection-box route mismatch ('hexshield_dome', 'dome-1x1') != ('hexshield_dome', 'dome-1x2')
- cabal_techcenter: selection-box route mismatch ('hexshield_dome', 'dome-3x2') != ('hexshield_dome', 'dome-2x2')
- cabal_obeliskofdarkness: selection-box route mismatch ('hexshield_dome', 'dome-1x1') != ('hexshield_dome', 'dome-2x2')
- ts_nod_techcenter: selection-box route mismatch ('hexshield_dome', 'dome-3x2') != ('hexshield_dome', 'dome-2x2')
- ts_gdi_techcenter: selection-box route mismatch ('hexshield_dome', 'dome-3x2') != ('hexshield_dome', 'dome-2x2')
- ts_gdi_upgradecenter: selection-box route mismatch ('hexshield_dome', 'dome-3x2') != ('hexshield_dome', 'dome-2x2')
- scrin_extractor: selection-box route mismatch ('hexshield_dome', 'dome-4x3') != ('hexshield_dome', 'dome-3x2')
- ra2_allies_gapgenerator: selection-box route mismatch ('hexshield_dome', 'dome-1x1') != ('hexshield_dome', 'dome-1x2')
- ra2_soviets_teslacoil: selection-box route mismatch ('hexshield_dome', 'dome-1x1') != ('hexshield_dome', 'dome-1x2')
- yuri_lunarcommandcenter: selection-box route mismatch ('hexshield_dome', 'dome-4x3') != ('hexshield_dome', 'dome-4x4')
- latinsyndicate_latinempradar: selection-box route mismatch ('hexshield_dome', 'dome-3x3') != ('hexshield_dome', 'dome-3x2')
- futuretech_battlelab: selection-box route mismatch ('hexshield_dome', 'dome-3x3') != ('hexshield_dome', 'dome-3x2')
- tkm_observationvan: selection-box route mismatch ('hexshield_dome', 'dome-1x1') != ('hexshield_dome', 'dome-2x2')
- tkm_techcenter: selection-box route mismatch ('hexshield_dome', 'dome-4x4') != ('hexshield_dome', 'dome-2x2')
- protoss_shieldbattery: selection-box route mismatch ('hexshield_dome', 'dome-3x2') != ('hexshield_dome', 'dome-2x2')
- EDEN_GARAGE: selection-box route mismatch ('hexshield_dome', 'dome-3x3') != ('hexshield_dome', 'dome-2x1')
- EDEN_LAB_ADVANCED: selection-box route mismatch ('hexshield_dome', 'dome-2x2') != ('hexshield_dome', 'dome-3x3')
- EDEN_SPACEPORT: selection-box route mismatch ('hexshield_dome', 'dome-4x4') != ('hexshield_dome', 'dome-3x3')
- PLYMOUTH_GARAGE: selection-box route mismatch ('hexshield_dome', 'dome-3x3') != ('hexshield_dome', 'dome-2x1')
- PLYMOUTH_LAB_ADVANCED: selection-box route mismatch ('hexshield_dome', 'dome-2x2') != ('hexshield_dome', 'dome-3x3')
- PLYMOUTH_SPACEPORT: selection-box route mismatch ('hexshield_dome', 'dome-4x4') != ('hexshield_dome', 'dome-3x3')
