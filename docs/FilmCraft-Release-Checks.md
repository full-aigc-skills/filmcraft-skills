# Layered release checks

The source offline CI unconditionally executes `python3 -I -B scripts/check_release.py --output REPORT_DIRECTORY`. It records individual tests, original logs and file hashes. Metadata, single-skill links, shared resources, command/scenario catalogs, parameter contracts and entry tests are required; package conditions cannot skip missing or failing checks.

A fixed test-ID policy separates mandatory units from environment-dependent native tests. Units must pass. Missing native environments produce individual NOT_RUN records with reasons. Undeclared skips and missing environment test IDs fail the gate. Green ordinary CI proves offline checks only, not native execution, hosts, platforms, real media or full V1.

The plugin independently consumes immutable source tags and whole-tree hashes. Its CI verifies fixed source, metadata and fixed public protocol mappings. Cold start, native delivery, headless/bridge and host discovery must run separately in installed copies. Source, CI, fixed installation, real media, host and platform evidence retain their own version and input bindings; historical success never qualifies a new combination.
