# Portable Korean OpenMW installer payload

This directory contains the Windows installer-side files for the Korean OpenMW runtime package.

## User-facing installer

`Install-Korean.bat` is the primary entry point for release bundles.
It runs `install-korean.ps1`, which:

1. locates or asks for the OpenMW installation directory;
2. backs up the existing `openmw.exe`;
3. copies the Korean-patched `payload/openmw.exe`;
4. backs up and installs the Korean font assets under `resources/vfs/fonts`;
5. runs `install-korean-config.ps1` to back up and update the user's `openmw.cfg`.

The package therefore does not require the user to overwrite the engine or edit `openmw.cfg` manually.

## Config updater

`install-korean-config.ps1` targets `%Documents%\My Games\OpenMW\openmw.cfg` by default and accepts `-ConfigPath` for portable/custom setups.
It removes stale copies of only the managed Korean `fallback=` keys, preserves unrelated `data=`, `content=`, archives, mod order, and user settings, and does not change the global encoding value.

When a final `encoding=` line exists, the managed Korean fallback block is inserted immediately before it. If no `encoding=` line exists, the block is appended at the end.

`Install-Korean-Config.bat` remains available as a config-only helper.

## Release bundle layout

The packaging workflow creates:

- `Install-Korean.bat`
- `install-korean.ps1`
- `install-korean-config.ps1`
- `korean-fallbacks.cfg`
- `payload/openmw.exe`
- `payload/resources/vfs/fonts/...`

The Korean translation data package remains separate from the OpenMW engine runtime package.
