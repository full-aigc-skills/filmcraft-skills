# Layered release checks

The source offline CI unconditionally executes `python3 -I -B scripts/check_release.py --output REPORT_DIRECTORY`. It records individual tests, original logs and file hashes. Metadata, single-skill links, shared resources, command/scenario catalogs, parameter contracts and entry tests are required; package conditions cannot skip missing or failing checks.

A fixed test-ID policy separates mandatory units from environment-dependent native tests. Units must pass. Missing native environments produce individual NOT_RUN records with reasons. Undeclared skips and missing environment test IDs fail the gate. Green ordinary CI proves offline checks only, not native execution, hosts, platforms, real media or full V1.

The plugin independently consumes immutable source tags and whole-tree hashes. Its CI verifies fixed source, metadata and fixed public protocol mappings. Cold start, native delivery, headless/bridge and host discovery must run separately in installed copies. Source, CI, fixed installation, real media, host and platform evidence retain their own version and input bindings; historical success never qualifies a new combination.

## MP4 resampling candidate

`runtime/audio-resample-edit-list-patch.json` defines the independent `0.2.0-craft.6` candidate. It retains the complete craft.5 patch and backports [upstream 5bf2203](https://github.com/storytold/filmcraft/commit/5bf2203bb89d1415450b0d69f0f40c7927c73860): apply the MP4 edit-list offset to the source window while computing the local resampling phase from the unshifted request. This prevents extrapolated peaks when primed AAC is read at another sample rate and retains the priming crop.

From a local checkout containing the fixed upstream baseline, run:

```bash
python3 -I -B scripts/build_resample_runtime.py --repository FILMCRAFT_REPOSITORY --output NEW_CANDIDATE_DIRECTORY --target-directory CARGO_TARGET_DIRECTORY
```

The shared builder checks the cumulative patch hash, exports the fixed commit, applies the patch and runs caption, sequence, project, Whisper/transcript, PCM packet timing and MP4 edit/resample regressions before building the candidate with `whisper`. The synthetic MP4 tests cover PCM phase/sample alignment and AAC priming across request boundaries. This candidate sets the existing testkit `FILMCRAFT_REQUIRE_ORACLES=1` policy, so missing FFmpeg fails the required AAC regression rather than returning without exercising it. No model weights are downloaded by this recipe. Candidate archive/provenance receipts are separate from source offline checks. Published runtimes, installer locks and installed binaries remain unchanged; release publication, installed-host acceptance, real recognition and listening require their own evidence.
