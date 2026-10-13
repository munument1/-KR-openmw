# KR5 journal and potion correction

The English-only EET database is source material, not a Korean completion tracker.
Compare its ALCH/FNAM IDs against the loaded translation and all three original masters.
The missing records are `p_restore_health_b`, `p_restore_health_c`, and `p_restore_health_s`.
Only FNAM is changed; all other potion fields come verbatim from Morrowind.esm.

The journal's `.mrk` search phrase can differ from the canonical topic name. Patch
0006 seeds both names, then adds explicitly reviewed journal aliases from the new
optional UTF-8 BOM `.jrn` sidecar. Each line is `display phrase<TAB>canonical topic`.
Aliases are seeded only for topics with recorded dialogue in the current journal.
Saved text, actor substitutions, quest indices, timestamps and player knowledge
are preserved; no unknown topics are added to the journal.

For the reported Caldera case, the aliases are `칼데라의 에보니 광산` and
`에보니 광산`, both targeting `칼데라 에보니 광산`. The latter occurs in the
Caldera donation quest; it is not an alias for unrelated ebony mines.
An English A-Z index remains a separate issue.

Build `yampt-journal-tagger.cpp` with the unmodified `topic_tagger.cpp` and
`keyword_trie.cpp` from [YAMPT](https://github.com/raffll/yampt), commit
`6070d0a88acd6ea7b29982b6a3d61e06a0520f2f` (MIT). The adapter reads canonical
topics, reviewed inflection pairs, then text spans as little-endian uint32 counts
and UTF-8 length-prefixed strings. Existing tags are preserved outside the adapter.

Run `build_kr5_data.py --help` for required input paths. Output must be a new folder.
The JSON allowlist limits changes to entries reviewed with the actual OpenMW parser;
the three reported Caldera entries are added explicitly. Every journal change is
checked for identical displayed text and preserved existing tags.

Compile `verify-journal-links.cpp` with OpenMW's keywordsearch, translation, files,
toutf8 and debuglog implementations. It loads actual CEL/MRK/TOP/JRN files and
can compare legacy and patched seeding against the same text. A saved-text test
must use the original KR4 text with the new `.jrn` file, without rewriting the save.
