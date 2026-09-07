# Korean video subtitles

OpenMW Korean builds can display external UTF-8 SRT subtitles for BIK videos through `0005-video-subtitles.patch`.

The engine looks for an SRT with the same VFS path and basename as the video, for example `video\\mw_intro.bik` -> `video\\mw_intro.srt`. Missing subtitles are ignored and video playback remains unchanged.

The Korean subtitle text in `video/` is paired with timing data from the community `Morrowind Video Subtitles 1.1.0` pack. Its published description states that timings were adjusted for the original English GOG GOTY videos. The Korean wording was prepared separately for this project; original BIK files are not redistributed.

Included subtitles:
- Morrowind: `mw_intro`, `mw_cavern`, `mw_end`
- Bloodmoon: `bm_bearhunt1`, `bm_bearhunt2`, `bm_ceremony1`, `bm_ceremony2`, `bm_endgame`, `bm_frostgiant1`, `bm_frostgiant2`
