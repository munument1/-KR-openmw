# Morrowind Official Addon Korean Translation

This package is intentionally distributed **separately** from the main OpenMW Korean translation package.

## Output

Release asset:

- `Morrowind_OfficialAddon_KR.zip`

Expected payload:

- `Morrowind_OfficialAddon_KR.esp`
- `Morrowind_OfficialAddon_KR.top`
- `Morrowind_OfficialAddon_KR.mrk`
- `README.txt`
- `SHA256SUMS.txt`

The existing `Morrowind-Korean-OpenMW-0.51.0-KR3-Full.zip` must not be modified just to carry this addon translation.

## Required official Bethesda plugins

All eight official addons are required by the integrated translation ESP:

- AreaEffectArrows.esp
- LeFemmArmor.esp
- master_index.esp
- bcsounds.esp
- entertainers.esp
- adamantiumarmor.esp
- EBQ_Artifact.esp
- Siege at Firemoth.esp

Exact source hashes are pinned in `manifest.json`.

## Load order

The eight official Bethesda plugins must load before the Korean translation plugins.

Recommended order:

1. Bethesda official addons
2. `Morrowind_Korean_ReTranslation.esp`
3. `Morrowind_OfficialAddon_KR.esp`

`Morrowind_OfficialAddon_KR.esp` is the last writer for addon records that overlap the base Korean ESP.

## Dialogue/topic safety rules

This project must not repeat the Master Index regression.

For DIAL/INFO records derived from an official addon:

- Preserve the complete official addon dialogue chain, not only the strings that need translation.
- Preserve INFO identifiers and ordering.
- Preserve `INAM`, `PNAM`, `NNAM`, conditions, filters, quest flags and result scripts byte-for-byte unless a change is explicitly required for localization.
- Translate user-visible response/journal/topic text only.
- Never reconstruct a plugin dialogue chain from the base game or from the main Korean ESP when the official addon changed that chain.
- Generate and validate `.top` mappings for Korean phrases that should discover/link to topics.
- Generate `.mrk` marker corrections when the translated wording does not contain a directly discoverable topic phrase.
- Validate every translated DIAL section against its official-addon source before packaging.

The build must fail if a source INFO record disappears, changes parent DIAL, changes structural condition/result fields, or loses its expected topic mapping.

## Distribution

The addon translation should be uploaded as an additional asset on the current Korean release page, not embedded inside the main KR3 Full ZIP.
