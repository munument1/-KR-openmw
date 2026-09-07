# Portable Korean OpenMW installer payload

This directory contains the Windows installer-side files for the Korean OpenMW runtime package.

## User-facing installer

`Install-Korean.bat` is the primary entry point for release bundles.
It runs `install-korean.ps1`, which:

1. locates or asks for the OpenMW installation directory;
2. backs up the existing `openmw.exe`;
3. copies the Korean-patched `payload/openmw.exe`;
4. backs up and installs the Korean font assets under `resources/vfs/fonts`;
5. backs up an existing managed Korean translation folder and installs the full translation payload to `<OpenMW>/mods/Morrowind_Korean_ReTranslation`;
6. validates the bundled ESP/CEL/MRK/TOP files, `l10n` directory, and Korean video SRT files;
7. runs `install-korean-config.ps1` to back up and update the user's `openmw.cfg`.

The full installer therefore does not require the user to overwrite the engine, copy the translation files manually, install the video subtitles separately, or edit `openmw.cfg` manually.

## Translation data registration

For the full installer, `install-korean-config.ps1` receives the resolved OpenMW installation path and manages exactly one Korean data directory and plugin entry:

- `data="<OpenMW>/mods/Morrowind_Korean_ReTranslation"`
- `content=Morrowind_Korean_ReTranslation.esp`

Stale copies of the current Korean data path, the previous `Morrowind_Korean_ReTranslation_v01` data path, duplicate Korean ESP entries, and the retired `Morrowind_Korean_Interior_CellNames_v01.esp` entry are removed. Other user `data=` and `content=` lines are preserved.

The Korean ESP is inserted after the last official `Morrowind.esm`, `Tribunal.esm`, or `Bloodmoon.esm` content entry when those masters are present. Existing third-party mod entries retain their relative order.

## Video subtitles

The Korean OpenMW runtime patch automatically looks for an SRT with the same VFS path and basename as a playing BIK video. For example, `video/mw_intro.bik` uses `video/mw_intro.srt` when that subtitle file is present.

The release bundle installs the subtitle files under `<OpenMW>/mods/Morrowind_Korean_ReTranslation/video`. Original BIK files are not modified or redistributed. If an SRT is absent, video playback behaves as upstream OpenMW.

The KR bundle currently includes subtitles for three Morrowind videos and seven Bloodmoon videos:

- `mw_intro.srt`
- `mw_cavern.srt`
- `mw_end.srt`
- `bm_bearhunt1.srt`
- `bm_bearhunt2.srt`
- `bm_ceremony1.srt`
- `bm_ceremony2.srt`
- `bm_endgame.srt`
- `bm_frostgiant1.srt`
- `bm_frostgiant2.srt`

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
- `payload/mods/Morrowind_Korean_ReTranslation/Morrowind_Korean_ReTranslation.esp`
- `payload/mods/Morrowind_Korean_ReTranslation/Morrowind_Korean_ReTranslation.cel`
- `payload/mods/Morrowind_Korean_ReTranslation/Morrowind_Korean_ReTranslation.mrk`
- `payload/mods/Morrowind_Korean_ReTranslation/Morrowind_Korean_ReTranslation.top`
- `payload/mods/Morrowind_Korean_ReTranslation/l10n/...`
- `payload/mods/Morrowind_Korean_ReTranslation/video/*.srt`

Packaging must fail rather than publish if the complete translation and subtitle payload is missing.
