# FilmCraft Skills

Independent FilmCraft skills. Implementation is in progress; this repository is not a completed plugin release.

The `filmcraft-use` skill contains a self-contained Python 3.11+ bootstrap installer for the pinned official macOS arm64 CLI. It verifies the archive and executable, retains license files, atomically installs a new version, and reuses an intact installation without downloading again.

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
