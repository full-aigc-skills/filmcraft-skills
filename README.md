# FilmCraft Skills

Edit existing media into a reopenable `.fcproj`, asset inventory, previews and a finished video.

Current source snapshot: `0.1.0-dev.34`; current fixed plugin `0.1.0-dev.34` retains older source32. New plugin/Art snapshots remain pending;13 independent skills.

Verified first-use platform: macOS arm64 and Python 3.11+. Pinned runtimes install into the user data directory; skill files stay in their host-loaded directory. These are development releases; complete V1 acceptance and generic Skills CLI installation remain open.

Historical craft.3 evidence: maintained runtime `0.2.0-craft.3` is publicly available. Audio tracks retain exact source sample ticks while video frame alignment is preserved. Source cold-use tests pass both off-grid audio tails, gain revisions, sequence relocation and the original short-film task. Asset preflight rejects corrupt input before installation/recovery writes; failures after editing starts retain diagnostics. Fixed Film/Art distribution verification remains pending. [Bound evidence](docs/evidence/audio-sample-public-first-use-20261007.json).

Maintained `0.2.0-craft.4` is published and passes independent public CLI/model cold installation and real recognition (45.826s). Native `--data-dir`,28 words, reopening/SRT and audio/video/source preservation pass. All666 commands were recaptured from the public binary with unchanged parameter contracts; source regression passes130 executed tests,34 skips. Fixed plugin/Art acceptance remains pending. [ASR evidence](docs/evidence/whisper-candidate-inference-20261008.json).

## First use

Invoke **`filmcraft-use`** in your host. For direct CLI use, set `SKILL_DIR` to the absolute directory of the `SKILL.md` actually loaded by that host. It may be under user/project `.agents/skills`, the plugin, or a host cache; use the actual path. Each entry below installs/verifies its locked runtime before invoking it.

<!-- CRAFT_FIRST_USE_START -->
```bash
: "${SKILL_DIR:?Set to the actual loaded skill directory}"
python3 -I -B "$SKILL_DIR/scripts/cli.py" -- --version
python3 -I -B "$SKILL_DIR/scripts/cli.py" -- commands --json
```
<!-- CRAFT_FIRST_USE_END -->

Read the [editable workflow](skills/filmcraft-use/references/workflow.md) for inputs, native projects and targeted revisions. [Setup and skill entry](skills/filmcraft-use/SKILL.md) · [version-bound history](RELEASE-HISTORY.md). Command/version queries verify installation and discovery; they do not constitute creative completion.

[First-use navigation evidence](docs/evidence/craft-readme-first-use-navigation-20261007.json).

Fixed installed path acceptance: standalone skills and Art mixed work pass native creation/reopen, targeted revision and export under Chinese-and-space paths; Art also verifies moved delivery. Skills/runtime identities stay unchanged. This is bounded macOS arm64 first-use evidence. [Path acceptance evidence](docs/evidence/craft-fixed-unicode-path-first-use-20261007.json).

Historical source candidate before the fixed release: structurally invalid runtime/Node locks now return local setup diagnostics before runtime writes/downloads. Five candidate native first-use checks pass; published plugin snapshots remain unchanged until separate immutable release acceptance. [Lock diagnostics candidate](docs/FilmCraft-Lock-Shape-Architecture.md).

---

Fixed native first-use and complete-command recovery acceptance passed:58 standalone cold installations, ten Art all-domain cold installations, four partial-download SSL EOF recoveries,72 post-save faults, four healthy command revisions and mixed HD revision/recovery/moved delivery. Installed identities remain unchanged. Only domain2.10/8.11 and Art4.10 close; exhaustive2639-command, GUI, model, generic Skills CLI and fullV1 gates remain open. [Version-bound evidence](docs/evidence/codex-native-download-first-use-20261007.json).

Historical candidate observation before fixed acceptance: Native download recovery candidate: up to three read-only attempts discard partial archives. Earlier fixed cold installs failed on SSL EOF; new fixed installed acceptance remains open.

Historical release record: Current standalone source: `0.1.0-dev.19`; bounded fixed native gateway first use passes; full V1 remains open.

Previous version-bound failed-stage acceptance: plugin dev.18, standalone source dev.16. All58 independent CLI cold starts,24 original-stage native fault cases and37 native scene tests plus6 contracts pass. Art77 bundle upgrade remains open. [Evidence](docs/evidence/codex-failed-stage-first-use-20261007.json).

Fixed domain-client first use: Film plugin dev.16 / source dev.15; Effect/Photo/Vector plugin dev.15 / source dev.14. Codex discovers 58 skills without errors. Actual installed copies pass 24 post-save faults and four healthy public workflows; the published Art engine with the installed Vector client passes six faults. All58 installed identities remain unchanged. Art dev.75 still bundles earlier domain sources; exhaustive command/GUI/model acceptance remains open. [Version-bound evidence](docs/evidence/codex-public-workflow-session-first-use-20261007.json).
Historical release record: Current standalone source: `0.1.0-dev.19`; bounded fixed native gateway first use passes; full V1 remains open.
Previous version-bound protocol recovery acceptance passed: 288 cases across 48 standalone source skills, 24 cases in actual installed copies, four healthy revision cases, and 58 unchanged installed skill identities. See [fixed evidence](docs/evidence/codex-protocol-fault-first-use-20261007.json). Exhaustive command/GUI acceptance and the Art domain-bundle upgrade remain open.

Protocol fault repair candidate: all 11 independently copied skills pass separate empty public-runtime installation and six faulty replies after real native save (66 cases; zero skips). Requests are not replayed; unknown receipts, saved-project reopening and delivery/skill preservation are checked. [Evidence](docs/evidence/protocol-fault-first-use-20261007.json). Fixed installed release and Art bundle upgrade remain separate gates.

Fixed plugin 0.1.0-dev.14 / skills 0.1.0-dev.13 installed revision acceptance passes: isolated Codex discovers all 58 skills without loading errors; this installed domain skill completes the documented cold creation/revision plans, saved-project reopening and non-target preservation. All58 installed digests remain unchanged; current fixed release CI passes. [Fixed revision evidence](docs/evidence/codex-complete-command-revision-first-use-20261007.json). Full command/GUI/model acceptance remains open.

All 11 domain skills pass the paired revision plans when copied alone and installed from separate empty public runtimes (67.161 seconds; zero skips). [Revision evidence](docs/evidence/complete-command-revision-first-use-20261007.json). Fixed installation of the updated snapshot remains a separate gate.

The complete-command entry now includes paired executable creation/revision recipes, explicit selection prerequisites after reopening, and native persisted-state/non-target checks. Each standalone skill includes both JSON plans. [Usage](skills/filmcraft-use/references/command-usage.md#7-可执行局部返工--executable-targeted-revision). Full per-command and GUI acceptance remains open.

Previous fixed Codex snapshot first use passes: five plugins / 58 skills discovered, independent public cold runtime installs for all 58 installed skills, four complete-command native samples, Art HD revision/recovery/package checks, unchanged installed digests and fixed release CI. [Evidence](docs/evidence/codex-complete-command-first-use-20261007.json). This remains bounded native acceptance; generic Skills CLI installation and exhaustive command/GUI acceptance are open.

## Complete native command entry

All 11 standalone skills now pass separate empty-runtime installation from locked public CLI archives, followed by native creation, save/reopen, domain assertions and rendered image checks (72.162 seconds; zero skips). [Cold-first-use evidence](docs/evidence/complete-commands-cold-first-use-20261007.json). This verifies this complete-command sample in every skill; exhaustive command/GUI and actual host installation remain separate.

Published development snapshot: skills dev.12 / plugin dev.13; bounded fixed-host first use passed.

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

Public-workflow reply validation is synchronized in the domain source candidates and has bounded native/Art protocol evidence. Fixed updated domain and Art distributions are still pending. [Candidate architecture](docs/FilmCraft-Complete-Commands-Architecture.md) · [Evidence](docs/evidence/public-workflow-session-candidate-20261007.json).

Failed-stage candidate: public workflows retain original native staging paths, dependency hashes, last submitted requests and completed receipts; replay is prohibited. Fixed releases and installed-host acceptance remain open. [Architecture](docs/FilmCraft-Failed-Stage-Architecture.md).

Fixed domain failed-stage first use passes: Film plugin18/source16 and other domain plugins17/source15; five plugins/58 skills without loading errors; all58 independent empty-runtime CLI starts (417.646s); actual installed24 post-save faults reopen product-retained original projects and dependencies; four healthy native creation/revision cases pass. All installed identities and16 fixed plugin CI runs pass. Source repositories have no CI runs, only local regression. Only domain OpenSpec3.12 closes; Art77 bundles older domain sources, task4.9 and fullV1 remain open. [Evidence](docs/evidence/codex-failed-stage-first-use-20261007.json).

Fixed installed scene matrix passes37 native scenarios and6 contract checks with zero skips. The Photo fixture now resolves the maintained native version from the installed skill lock; the CLI and installed skills are unchanged. [Evidence](docs/evidence/codex-failed-stage-first-use-20261007.json).


Candidate complete-command inner JSON fix: nonfinite values, overflow and duplicate keys now retain unknown receipts before binding results. All nine real post-save fault classes pass with original reopen; this is candidate-source evidence, fixed releases and installed-copy acceptance are pending. Complete per-command/GUI acceptance stays open.

## Desktop installation component (source candidate)

The 48 standalone domain skills now have their own pinned official desktop installers. See the [installation architecture](docs/Craft-Desktop-First-Use-Architecture.md) and [48-skill installation evidence](docs/evidence/craft-desktop-source48-first-use-20261007.json). Existing release-tag skill copies do not yet contain this candidate component. Desktop startup, GUI edits/save/reopen and complete command execution remain open acceptance gates.

Source candidate now includes owned standalone desktop startup: 48/48 single-skill cold GUI save/reopen and cleanup cases passed. See [runtime evidence](docs/evidence/craft-owned-desktop-first-use-20261007.json). Fixed-release installation and complete command execution remain open.

Command-plan JSON source candidate: duplicate keys are rejected before installation and output creation. All 13 domain skills pass standalone-copy rejection and valid-plan checks. Three focused tests pass; fixed-plugin publication and installed acceptance remain NOT_RUN. [Evidence](docs/evidence/command-plan-json-candidate-20261007.json).

Fixed strict-plan installed verification passes: 64 CLI probes, 324 duplicate-key rejections across54 independently copied installed domain skills, 54 unique-plan structure checks and four cold native save/reopen/render samples. All64 installed skill hashes remain unchanged. Only the bounded strict-plan publication gate closes; generic Skills CLI, Art domain-bundle upgrade, exhaustive contexts and fullV1 remain open. [Evidence](docs/evidence/command-plan-json-fixed-first-use-20261007.json).

Native Whisper recognition remains in candidate build and real-model acceptance; fixed installation locks retain the previous release. See [native ASR architecture](docs/FilmCraft-Native-ASR-Architecture.md) for directory isolation and release gates.

[Whisper candidate inference evidence](docs/evidence/whisper-candidate-inference-20261008.json): actual28-word recognition, reference-word coverage1.0 for this sample, native/SRT and source preservation passed using an explicit environment directory. Native `--data-dir`, public installation and fixed plugin/Art remain separate gates.

Directory-corrected native candidate single-skill acceptance passed in39.339s: empty CLI/model caches, pinned model download via `--data-dir`, actual recognition, native reopening/SRT and audio/video preservation. Public and fixed plugin/Art installation remain pending; evidence above binds candidate hashes.

Source33 final verification:13 separate empty runtime installations (67.272s), actual public ASR on the current skill bytes (50.350s),10 native scenes (89.158s) and actual advanced gateway creation/reopen/render pass. All666 parameter contracts remain unchanged. Fixed Film/Art publication/host acceptance remains open.
