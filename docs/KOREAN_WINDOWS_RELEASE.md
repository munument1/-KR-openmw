# Korean Windows upstream port and release

This repository can build the maintained Korean OpenMW runtime directly from an upstream `OpenMW/openmw` branch, tag, or commit without first merging that upstream source into the fork.

## What is automated

The `Korean Windows upstream port` workflow:

1. checks out the requested upstream OpenMW ref;
2. checks out the Korean port assets from this repository at the workflow commit;
3. applies, in order:
   - `korean/patches/0001-cjk-topic-discovery.patch`
   - `korean/patches/0002-utf8-bom-sidecars.patch`
   - `korean/patches/0003-mixed-utf8-esm-reader.patch`;
4. overlays the maintained Korean font definitions and Galmuri11 font asset;
5. verifies the Korean runtime invariants;
6. runs the normal reusable Windows OpenMW Release/CPack build;
7. adds `KoreanConfig/` containing the safe user `openmw.cfg` updater;
8. creates a final ZIP and SHA-256 checksum;
9. optionally creates a draft prerelease for the requested Korean release tag.

The Korean translation data (`ESP`, translation sidecars, and other translated game data) remains a separate package.

## Running the build

Open **Actions -> Korean Windows upstream port -> Run workflow**.

Inputs:

- `upstream_ref`: upstream OpenMW branch, tag, or commit, for example `openmw-0.51.0`.
- `release_tag`: Korean bundle/release label, for example `openmw-0.51.0-kr2`.
- `publish_release`: leave disabled for a CI-only build; enable it to create/update a draft prerelease.

The safe first regression target is `openmw-0.51.0`, which is the source baseline used for the original validated Korean 0.51 runtime.

## Config installation

The final ZIP contains `KoreanConfig/Install-Korean-Config.bat`.

The updater:

- locates the user's OpenMW `openmw.cfg`;
- creates a timestamped backup;
- preserves unrelated `data=`, `content=`, archive, mod-order, and user settings;
- removes stale copies of only the Korean-managed fallback keys;
- appends the current managed Korean fallback block at the end;
- does not force a global `encoding=utf8` setting.

## Future OpenMW updates

For a new OpenMW release:

1. run `Korean upstream patch check` against the new upstream ref;
2. if all three patches apply, run `Korean Windows upstream port` with the same upstream ref;
3. download and test the generated ZIP;
4. run the Korean gameplay regression baseline;
5. publish the draft release after validation.

If the patch check fails, update only the affected patch and corresponding fork source implementation. Translation/config payloads should not need to be rebuilt merely because the OpenMW version changed.
