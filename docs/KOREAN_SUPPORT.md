# Korean runtime support

This fork carries the OpenMW-side runtime changes required by the Korean Morrowind translation project.

## Repository roles

- `munument1/-KR-openmw`: active OpenMW engine development for Korean support.
- `munument1/OpenMW-korean-legacy`: legacy release history, translation payload tooling, validation reports, and the OpenMW 0.51 test lineage.

The fork keeps `master` as its single long-lived development branch. Korean runtime changes are maintained directly on `master` alongside upstream OpenMW updates.

## Current source integration

The Korean runtime source port was integrated onto fork `master` commit `01d86c54bdac8580d91066bc23ad035da9be8dbf`, after the fork had synced the then-current upstream OpenMW changes.

The validated Korean runtime changes are committed directly to the fork source and currently cover six upstream files:

- `apps/openmw/mwdialogue/keywordsearch.hpp`
- `apps/openmw/mwdialogue/keywordsearch.cpp`
- `apps/openmw/mwdialogue/dialoguemanagerimp.cpp`
- `apps/openmw/mwdialogue/journalentry.cpp`
- `components/translation/translation.cpp`
- `components/esm3/esmreader.cpp`

Reference patches are retained under `korean/patches/` and `.github/workflows/korean-runtime-guard.yml` verifies that the source still contains those changes on `master`.

`.github/workflows/korean-upstream-patch-check.yml` is the portability check for future OpenMW updates. Run it manually with an upstream branch, tag, or commit; it fetches that clean upstream revision, applies the four Korean runtime patches in order, and verifies the expected runtime invariants. A failure means the Korean patchset needs rebasing before building a new release.

## Runtime behavior

### Korean/CJK dialogue discovery

Implicit topic discovery may start on UTF-8 three- or four-byte character boundaries rather than requiring an ASCII word separator before the candidate. Topic-learning mode keeps overlapping matches so an implicit Korean topic does not suppress another valid topic or an explicit `@...#` link. Normal dialogue highlighting keeps the normal overlap-resolution behavior.

### UTF-8 translation sidecars

Translation sidecars (`.cel`, `.top`, `.mrk`) are opened in binary mode. A UTF-8 BOM on the first line explicitly opts that sidecar into direct UTF-8 handling; BOM-less sidecars continue through the configured legacy encoder.

### Mixed UTF-8 ESM strings

Validated UTF-8 strings containing Hangul are preserved before the legacy encoder runs. Strings that are not validated UTF-8 Hangul continue through the normal OpenMW encoder path. This allows a real-UTF-8 Korean translation plugin to coexist with the normal win1252 Morrowind/Tribunal/Bloodmoon masters without requiring a global `encoding=utf8` setting.

### Legacy Korean journal recovery

Older Korean test builds could write already-mojibaked journal text into save files. When loading a saved journal entry, the Korean runtime now checks only entries that contain non-ASCII bytes but no Hangul. If the currently loaded plugin has the same journal topic/INFO and its response contains Hangul, the displayed/saved journal text is rebuilt from that current INFO response. Existing valid Korean entries, plain ASCII entries, missing INFO records, and unrelated content are left unchanged.

This is a compatibility path for old affected saves. New saves created with the current Korean UTF-8 runtime store and display journal text normally.

## Configuration and font policy

The Korean runtime must not require users to manually edit `openmw.cfg`, `user.cfg`, or `settings.cfg` to select UTF-8 or a font fallback.

The Korean package uses OpenMW's normal font fallback names while supplying Korean-capable descriptors:

- `Fonts_Font_0` / `MysticCards` -> Gowun Batang Bold, antialiased;
- `Fonts_Font_1` / `DejaVuLGCSansMono` -> Gowun Batang Bold, antialiased;
- `Fonts_Font_2` / `DemonicLetters` -> original DemonicLetters Daedric font, unchanged.

The Daedric slot is intentionally preserved so Daedric writing keeps its original glyphs. Gowun Batang is distributed under the SIL Open Font License 1.1 and its OFL text is included with packaged builds. The build workflow retrieves the upstream `GowunBatang-Bold.ttf` and verifies its Git blob SHA before packaging it.

Translated OpenMW fallback strings are maintained separately under `packaging/korean/korean-fallbacks.cfg`. The Windows config updater backs up the user's existing `openmw.cfg`, removes only stale copies of the managed fallback keys, and installs the Korean managed block without replacing unrelated configuration or mod ordering.

The config updater does not set `encoding=utf8` or otherwise change the global encoding. The mixed UTF-8 runtime patch is specifically designed so Korean UTF-8 translation data can coexist with the normal win1252 masters.

No GBK/CP936, pinyin, Chinese UI, or global UTF-8 encoding option is part of this port.

## Update flow

For a new OpenMW release:

1. run `Korean upstream patch check` against the new upstream tag or commit;
2. if all four patches apply, sync/rebase the fork to that upstream revision and apply the same patchset;
3. run the targeted `openmw` build to verify the Korean runtime compiles without building unrelated tools;
4. verify the Gowun Batang source hash and the three font-slot mappings;
5. package the runtime binary, translation assets, fonts, and config updater together;
6. repeat the Korean regression tests before publishing.

The translation/config payload and the engine source patchset are intentionally versioned separately so routine OpenMW engine updates do not require rewriting the translated fallback data.

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
