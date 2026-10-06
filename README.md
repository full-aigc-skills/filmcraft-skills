# FilmCraft Skills

## Complete native command entry

Local candidate: skills dev.12 / plugin dev.13; publication and installed-host checks pending.

All 666 commands now have verbatim parameters, skill routing, and same-session invocation through `commands.py list / describe / check / run`. Live enabled state is checked; the existing 17-operation delivery workflow remains bounded. GUI commands require explicit bridge mode. Complete registry coverage does not establish full command acceptance.

[Architecture and usage](docs/FilmCraft-Complete-Commands-Architecture.md) · [Complete reference](skills/filmcraft-use/references/command-reference.md) · [Runnable example](skills/filmcraft-use/examples/commands-advanced.json)

Independent FilmCraft skills. Implementation is in progress; this repository is not a completed plugin release.

The `filmcraft-use` skill contains a self-contained Python 3.11+ bootstrap installer for the pinned macOS arm64 CLI (upstream or explicitly identified maintained variant). It verifies the archive and executable, retains license files, atomically installs a new version, and reuses an intact installation without downloading again.

Run tests with `python3 -m unittest discover -s tests -v`. Full creative workflow and host acceptance remain pending.

Normative requirements and implementation tracking: [FilmCraft plugin OpenSpec](https://github.com/full-aigc-plugins/filmcraft-plugin/tree/main/openspec/changes/establish-v1-plugin).

[简体中文](README.zh-CN.md)

The native editing helper supports media import and collection, exact tick-based clip timing, independent audio, styled captions, project reopening, H.264 export and hash-checked revisions after moving a delivery folder. See [workflow guidance](skills/filmcraft-use/references/workflow.md). The helper uses Python stdlib and the bootstrapped CLI; live acceptance tests additionally require ffmpeg, ffprobe and Pillow.

Development version `0.1.0-dev.1` fixes concurrent first-use/reuse install-lock contention: wait up to 120 seconds, then verify and reuse; timeout preserves installations and never replays editing tasks.

Development version dev.2 includes hash-bound exchange-loss.json with every native delivery. Reports distinguish format losses, observed structure and unknown font/effect fidelity; exported derivatives never replace the retained native project.

## CLI and task skill suite

[FilmCraft Skill Suite Architecture](docs/FilmCraft-Skill-Suite-Architecture.md)

| Skill | Purpose |
| :--- | :--- |
| `filmcraft-use` | use |
| `filmcraft-cli` | cli |
| `filmcraft-cli-setup` | cli setup |
| `filmcraft-cli-project` | cli project |
| `filmcraft-cli-media` | cli media |
| `filmcraft-cli-timeline` | cli timeline |
| `filmcraft-cli-audio` | cli audio |
| `filmcraft-cli-subtitles` | cli subtitles |
| `filmcraft-cli-color` | cli color |
| `filmcraft-cli-motion` | cli motion |
| `filmcraft-cli-export` | cli export |

`npx skills add full-aigc-skills/filmcraft-skills --skill <skill-name>`

## Focused task skills: clean first use

All eight FilmCraft task skills passed independent first-install operations on macOS arm64, with only that skill copied and a fresh runtime downloaded from its locked public URL. Assertions cover persisted native edits, actual audio samples and rendered pixels, original-project preservation, and rejected unknown commands. The full suite passed 31 tests with no skips. [Evidence](docs/evidence/task-skill-first-use.json). This verifies the listed operations, not every command, GUI or final creative acceptance.

```bash
CRAFT_TASK_FIRST_USE=1 CRAFT_LIVE_TEST=1 CRAFT_LIVE_SUITE=1 python3 -B -m unittest discover -s tests -v
```

Run this command in the independent `filmcraft-skills` repository; live tests require ffmpeg, ffprobe and Pillow.

Commands use `SKILL_DIR`, the absolute directory of the `SKILL.md` actually loaded by the host. User/project `.agents/skills` and plugin-internal/cache layouts are supported; the CLI runtime is installed separately in the user data directory. Each skill was copied alone into all three layouts, including paths with spaces, and its documented script entry points ran `--help`. [Path verification](docs/evidence/installed-skill-paths.json). Existing host caches need an explicit update to receive the corrected documentation.

The Chinese subtitle acceptance fixture exposed an official CLI 0.2.0 bug: caption burn-in ignores the stored font family and renders identical missing-glyph boxes. A source-bound candidate patch and native regression tests are under `runtime/`; the prior public skill release remains unchanged. Unicode native/SRT storage and audio correlation passed, but the Chinese visual acceptance gate remains failed until a fixed public runtime passes isolated installation and output review.

Caption exports now explicitly enable native `burnCaptions` when caption tracks are enabled; `export.burnCaptions=false` retains sidecar/native captions without burning. This fixes missing subtitles in movie outputs, but official 0.2.0 Chinese glyph rendering remains a separate blocker.

Development dev.5 pins maintained `0.2.0-craft.1`, built from a fixed upstream commit and the caption-font patch. A clean single subtitle skill installation from the local checksummed release archive passed Unicode/SRT, native reopening, actual burned export frames, distinct Chinese glyphs, speech correlation and local revision tests. Public-URL first-use verification passed on 2026-10-06. The official 0.2.0 lock is retained under runtime/ for provenance; old versions are not overwritten.

The maintained runtime is published and cold online subtitle acceptance passed; the full current source regression passed 44 tests with no skips. [Bounded evidence](docs/evidence/chinese-first-use.json). This completes the listed native first-use operations, not GUI/model dispatch or all five-plugin acceptance.

Current installed plugin dev.6 / skills dev.5 pass all eight independent task cold starts with maintained CLI 0.2.0-craft.1 (43.688 seconds). Input, output, test-driver and native fingerprints are recorded; all 58 installed hashes remain unchanged. This supplements the older 0.2.0 scene proof without changing release bytes. [Evidence](docs/evidence/maintained-runtime-task-first-use.json).

Candidate installation-receipt reuse validation is implemented and tested; fixed plugin and ArtCraft publication remain pending. [Architecture and evidence](docs/FilmCraft-Runtime-Receipt-Architecture.md).

Fixed FilmCraft plugin dev.7 / source dev.6 passed actual Codex 0.153.4 installation and four installed-snapshot tests: public cold native install, save/reopen, receipt refusal/restoration, and 11 isolated CLI entries. All 58 installed digests remain unchanged. [Fixed-release evidence](docs/evidence/codex-filmcraft7-receipt-first-use-20261006.json). ArtCraft dev.42 still locks source dev.5; its update remains pending.

[Temporal-source trim and move acceptance](docs/FilmCraft-Temporal-Timeline-Acceptance.md): one installed single-skill empty-runtime case passes, checking source in-points in reopened projects and native exports while preserving other clips, audio, captions and original deliveries. Complete timeline/creative acceptance remains open.

Published source dev.7 adds static audio-track gain through mixer.setStrip in the native workflow, with finite-value checks and decoded -6 dB acceptance. See [architecture and scope](docs/FilmCraft-Audio-Gain-Architecture.md). Fixed installed-plugin verification passed with all 58 hashes preserved; [evidence](docs/evidence/codex-filmcraft8-audio-gain-first-use-20261006.json).

Installed plugin dev.8 verifies three independent voice/music/original-audio tracks, staggered starts and a music-only gain revision through real decoded frequency amplitudes. All 58 installed hashes remain unchanged. [Scope and evidence](docs/FilmCraft-Multitrack-Audio-Architecture.md).

Published source dev.8 rejects generated silent AAC when required native source audio is absent, retains diagnostic outputs and still accepts explicit video-only or intentional silent WAV delivery. [Architecture and scope](docs/FilmCraft-Required-Audio-Architecture.md). Fixed plugin dev.9 installed verification passed: three real tests and all 58 hashes preserved. [Evidence](docs/evidence/codex-filmcraft9-required-audio-first-use-20261006.json).

Public runtime craft.2 adds explicit-rate sequence import, complete collection and moved-project relinking. Source-skill cold installation and actual Effect→Film handoff passed; immutable plugin and Art acceptance remain pending. [Evidence and architecture](docs/FilmCraft-Public-Sequence-First-Use-Architecture.md).

Fixed Film plugin dev.10 installed-first-use sequence acceptance now passes in isolated Codex 0.153.4. All 58 skills are discovered without loading errors and retain their hashes after Film execution. [Bounded evidence](docs/evidence/codex-filmcraft10-sequence-first-use-20261006.json); Effect/Art dynamic release integration remains pending.

Candidate motion/LUT workflow: explicit keyframes, registered LUTs, native reopening and moved revisions passed a public-runtime first-use test. Immutable plugin dev.10 and Art integration do not yet include this mapping. See [architecture](docs/FilmCraft-Motion-LUT-Workflow-Architecture.md) and [evidence](docs/evidence/motion-lut-workflow-candidate-20261006.json).

Source dev.10 includes the motion/LUT workflow in all eleven independent skills. Native CLI remains 0.2.0-craft.2. Installed plugin acceptance is tracked separately.

Fixed Film dev.11 / source dev.10 installed-first-use verification passed: isolated Codex discovers 58 skills without errors; all 11 Film skills pass separate cold CLI startup; installed motion/LUT, audio-gain and sequence scenarios pass with zero skips. All 58 installed hashes remain intact. New Art LUT runtime publication and full V1 remain pending. [Evidence](docs/evidence/codex-filmcraft11-motion-lut-first-use-20261006.json).

Working-tree segmented asset consumer candidate validates Effect checkpoints, collects continuous frames and preserves source hashes. Fixed release, full HD long render and Art integration remain pending. [Architecture](docs/FilmCraft-Segmented-Assets-Architecture.md).

Current-source HD segmented candidate passes 1080p / 24 fps / five seconds and animated-title checks; immutable installed releases and Art HD remain pending. [Architecture and evidence](docs/FilmCraft-HD-Sequence-Architecture.md).

Skill source 0.1.0-dev.11 includes bounded segmented workflows and HD RGBA verification optimization. Native CLI identity is unchanged; corresponding immutable plugin and installed Art acceptance are recorded separately.
