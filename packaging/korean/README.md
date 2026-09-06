# Portable Korean OpenMW installer payload

This directory contains the Windows installer-side files for the Korean OpenMW runtime package.

## User-facing installer

`Install-Korean.bat` is the primary entry point for release bundles.
It runs `install-korean.ps1`, which:

1. locates or asks for the OpenMW installation directory;
2. backs up the existing `openmw.exe`;
3. copies the Korean-patched `payload/openmw.exe`;
4. backs up and installs the Korean font assets under `resources/vfs/fonts`;
5. backs up an existing managed Korean translation folder and installs the translation payload to `<OpenMW>/mods/Morrowind_Korean_ReTranslation_v01`;
6. runs `install-korean-config.ps1` to back up and update the user's `openmw.cfg`.

The full installer therefore does not require the user to overwrite the engine, copy the translation ESP manually, or edit `openmw.cfg` manually.

## Translation data registration

For the full installer, `install-korean-config.ps1` receives the resolved OpenMW installation path and manages exactly one Korean data directory and plugin entry:

- `data="<OpenMW>/mods/Morrowind_Korean_ReTranslation_v01"`
- `content=Morrowind_Korean_ReTranslation_v01.esp`

Stale copies of the same Korean data path, duplicate Korean ESP entries, and the retired `Morrowind_Korean_Interior_CellNames_v01.esp` entry are removed. Other user `data=` and `content=` lines are preserved.

The Korean ESP is inserted after the last official `Morrowind.esm`, `Tribunal.esm`, or `Bloodmoon.esm` content entry when those masters are present. Existing third-party mod entries retain their relative order.

## Config updater

`install-korean-config.ps1` targets `%Documents%\My Games\OpenMW\openmw.cfg` by default and accepts `-ConfigPath` for portable/custom setups.

When called without `-OpenMWPath` (for example through `Install-Korean-Config.bat`), it remains a config-only helper and manages only the Korean `fallback=` values. It preserves unrelated `data=`, `content=`, archives, mod order, user settings, and the existing global encoding value.

When a final `encoding=` line exists, the managed Korean fallback block is inserted immediately before it. If no `encoding=` line exists, the block is appended at the end.

## Required release bundle layout

A complete release bundle must contain:

- `Install-Korean.bat`
- `install-korean.ps1`
- `install-korean-config.ps1`
- `korean-fallbacks.cfg`
- `payload/openmw.exe`
- `payload/resources/vfs/fonts/...`
- `payload/mods/Morrowind_Korean_ReTranslation_v01/Morrowind_Korean_ReTranslation_v01.esp`
- any additional files that belong to the same validated translation data package under that mod directory

Packaging must fail rather than publish if the translation ESP payload is missing.
