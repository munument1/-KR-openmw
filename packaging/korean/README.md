# Portable Korean OpenMW config payload

This directory contains the user-config side of the Korean OpenMW runtime package.

## Files

- `korean-fallbacks.cfg`: Korean `fallback=` values only. It must not contain `data=`, `content=`, `fallback-archive=`, or `encoding=` entries.
- `install-korean-config.ps1`: backs up the user's existing `openmw.cfg`, removes stale copies of managed fallback keys, and appends one managed Korean block at the end.
- `Install-Korean-Config.bat`: Windows wrapper for the PowerShell updater.

## Default config path

The updater targets:

`%USERPROFILE%\Documents\My Games\OpenMW\openmw.cfg`

More precisely, it uses the Windows Documents known folder and appends `My Games\OpenMW\openmw.cfg`.

A custom path can be supplied:

```bat
Install-Korean-Config.bat -ConfigPath "D:\PortableOpenMW\openmw.cfg"
```

## Safety rules

The updater:

1. requires an existing `openmw.cfg`;
2. creates `openmw.cfg.korean-backup-YYYYMMDD-HHMMSS` before writing;
3. preserves unrelated user lines, including `data=`, `content=`, archives, mod ordering, and other personal configuration;
4. replaces only fallback keys present in `korean-fallbacks.cfg`;
5. keeps the managed Korean block at the end so its fallback values win over stale earlier copies;
6. writes UTF-8 without BOM;
7. does not change the global OpenMW encoding setting.

## Engine/update separation

The config payload is independent from the engine runtime patches under `korean/patches/`.
When a new OpenMW version is released, first run the `Korean upstream patch check` workflow against the new upstream tag or commit. If all three engine patches apply, the same config payload can be reused unchanged unless Korean fallback translations themselves changed.
