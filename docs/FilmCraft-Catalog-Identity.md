# FilmCraft Command Catalog Identity Repair

[中文](FilmCraft-Catalog-Identity.zh_CN.md). This implements the plugin's FC-RL-001-CURRENT-FACTS and tasks 9.4—9.6; the plugin OpenSpec remains the behavioral authority.

The old reference declared craft.4 but retained an earlier binary digest, while the native snapshot and effective runtime lock already identified actual craft.4. Relabelling old observations would not prove a new capture. This repair first queries command_list in an actual empty session of the locked CLI, binding version, platform, binary digest, upstream provenance and native parameters to one source. All 666 command rows match the earlier rows individually; this establishes catalog consistency, not successful execution of every command.

The generator rejects identity mismatches, duplicate/malformed rows, and changed parameters or inventory under the same digest. The old runtimePatchSourceCommit lacks provenance in the current lock and is not inherited. Thirteen standalone skills synchronize parameters and metadata while retaining their existing command-ID subsets, without widening/narrowing published catalogs or adding runtime dependencies on sibling skills. Resource synchronization first performs a read-only catalog consistency check so an invalid master cannot be propagated as matching copies.

```bash
python3 -B scripts/build_command_coverage.py --capture-native
python3 -B scripts/sync_skill_suite.py
python3 -B scripts/build_command_coverage.py --check
python3 -B scripts/sync_skill_suite.py --check
python3 -B -m unittest discover -s tests -p test_catalog_identity.py -v
```

Capture requires an authorized, installed pinned runtime; the installer retains source, receipt and binary verification. `--check` does not capture, download or write files. See [bound candidate evidence](evidence/filmcraft-catalog-identity-candidate-20261008.json). Source regression and pinned installation are reported separately; older releases retain their bytes and original MISMATCH status.
