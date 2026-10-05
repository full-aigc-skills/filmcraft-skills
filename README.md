# FilmCraft Skills

Independent FilmCraft skills. Implementation is in progress; this repository is not a completed plugin release.

The `filmcraft-use` skill contains a self-contained Python 3.11+ bootstrap installer for the pinned official macOS arm64 CLI. It verifies the archive and executable, retains license files, atomically installs a new version, and reuses an intact installation without downloading again.

Run tests with `python3 -m unittest discover -s tests -v`. Full creative workflow and host acceptance remain pending.

Normative requirements and implementation tracking: [FilmCraft plugin OpenSpec](https://github.com/full-aigc-plugins/filmcraft-plugin/tree/main/openspec/changes/establish-v1-plugin).

[简体中文](README.zh-CN.md)

The native editing helper supports media import and collection, exact tick-based clip timing, independent audio, styled captions, project reopening, H.264 export and hash-checked revisions after moving a delivery folder. See [workflow guidance](skills/filmcraft-use/references/workflow.md). The helper uses Python stdlib and the bootstrapped CLI; live acceptance tests additionally require ffmpeg, ffprobe and Pillow.
