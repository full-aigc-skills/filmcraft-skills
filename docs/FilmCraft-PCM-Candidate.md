# PCM packet timing candidate

Source dev.45 includes a cumulative `0.2.0-craft.5` candidate patch against upstream `adfd9a66de2bebc764c7f57435ccdf0f1d2e1df6`. The existing immutable craft.4 installer lock is unchanged.

The fixed dev.52 real-media VFR probe exported and decoded successfully, but audio correlation was 0.49865 against a 0.98 minimum. Native PCM WAV export also failed correlation (0.47976); an independent AAC comparator achieved 0.99987. Millisecond Matroska timestamps at 44.1 kHz introduced packet-boundary gaps or overlap.

The candidate accumulates exact PCM packet sample counts within one container timestamp unit and retains larger actual gaps. Checked arithmetic and frame-alignment validation reject malformed input. Other codecs are unchanged. Prior caption, sequence, exact audio duration and Whisper patches remain included.

Regression evidence: the continuous-sample test failed before the fix while the genuine 100 ms gap case passed; all three final PCM tests and 43 codec library regressions passed locally on macOS arm64. These tests do not close OpenSpec 9.32/9.33 or full V1. Build and real-media candidate results are recorded separately; no binary is installed by this source release.

Build with `python3 -I -B scripts/build_pcm_runtime.py --repository <upstream-checkout> --output <new-private-directory> --target-directory <private-cargo-target>`. The builder verifies the pinned commit and patch digest, runs related regressions, enables Whisper and emits a version-bound build receipt. Required Cargo dependencies must already be cached. Research stays read-only.
