# Korean runtime support

This fork carries the OpenMW-side runtime changes required by the Korean Morrowind translation project.

## Repository roles

- `munument1/-KR-openmw`: active OpenMW engine development for Korean support.
- `munument1/OpenMW-korean-legacy`: legacy release history, translation payload tooling, validation reports, and the OpenMW 0.51 test lineage.

The fork keeps `master` as its single long-lived development branch. Korean runtime changes are maintained directly on `master` alongside upstream OpenMW updates.

## Current source integration

The Korean runtime source port was integrated onto fork `master` commit `01d86c54bdac8580d91066bc23ad035da9be8dbf`, after the fork had synced the then-current upstream OpenMW changes.

The validated Korean runtime changes are committed directly to the fork source and cover five upstream files:

- `apps/openmw/mwdialogue/keywordsearch.hpp`
- `apps/openmw/mwdialogue/keywordsearch.cpp`
- `apps/openmw/mwdialogue/dialoguemanagerimp.cpp`
- `components/translation/translation.cpp`
- `components/esm3/esmreader.cpp`

Reference patches are retained under `korean/patches/` and `.github/workflows/korean-runtime-guard.yml` verifies that the source still contains those changes on `master`.

## Runtime behavior

### Korean/CJK dialogue discovery

Implicit topic discovery may start on UTF-8 three- or four-byte character boundaries rather than requiring an ASCII word separator before the candidate. Topic-learning mode keeps overlapping matches so an implicit Korean topic does not suppress another valid topic or an explicit `@...#` link. Normal dialogue highlighting keeps the normal overlap-resolution behavior.

### UTF-8 translation sidecars

Translation sidecars (`.cel`, `.top`, `.mrk`) are opened in binary mode. A UTF-8 BOM on the first line explicitly opts that sidecar into direct UTF-8 handling; BOM-less sidecars continue through the configured legacy encoder.

### Mixed UTF-8 ESM strings

Validated UTF-8 strings containing Hangul are preserved before the legacy encoder runs. Strings that are not validated UTF-8 Hangul continue through the normal OpenMW encoder path. This allows a real-UTF-8 Korean translation plugin to coexist with the normal win1252 Morrowind/Tribunal/Bloodmoon masters without requiring a global `encoding=utf8` setting.

## Configuration policy

The Korean runtime must not require users to edit `openmw.cfg`, `user.cfg`, or `settings.cfg` to select UTF-8 or a font fallback.

The tested translation package uses OpenMW's normal `MysticCards` slot with a package-supplied `MysticCards.omwfont` descriptor pointing at Galmuri. The font binary/package asset is intentionally kept outside this engine source port for now; engine source changes and translation/package assets remain separately reviewable.

No GBK/CP936, pinyin, Chinese UI, or global UTF-8 encoding option is part of this port.

## Validation baseline

The behavior being ported was first real-game validated on an OpenMW 0.51.0 test build derived from commit `f4bec41444214a7903bebd178389ca22ca13f646` together with the migrated Korean UTF-8 ESP/sidecars.

The validated game paths included:

- Korean settings/UI text;
- Korean NPC, item, dialogue, book, and journal text;
- interior/exterior CELL and region display names;
- save/load;
- Tribunal and Bloodmoon smoke tests;
- Hasphat Antabolis topic progression;
- Ranis Athrys Mages Guild join/duties flow;
- Ajira/Galbedir bet topic progression.

That 0.51 result is the regression baseline. The source port in this fork must be rebuilt and re-tested before it is treated as a release-equivalent replacement for that test binary.
