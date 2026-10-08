# FilmCraft Resolved Parameter Object Validation

[中文](FilmCraft-Parameter-Container.zh_CN.md). This implements FC-CM-001-RESOLVED-TICK and task 9.3 from the plugin's authoritative OpenSpec.

The old entry permitted a whole `params` reference during structural validation but did not check the resolved container type. A string could bypass tick field validation; booleans, numbers or arrays could raise an unhandled TypeError. The shared validator now requires the resolved value to remain a JSON object and returns `invalid_command_parameters` before dependent native requests. Existing literal parameters, object references, exact integers and receipt behavior stay compatible. Workflow-native retains its own `invalid_native_operation` structural error.

All eight entry tests pass. The added test covers seven whole-parameter reference results: before the fix, two incorrectly succeeded and five raised unstructured exceptions. After the fix, every case preserves a FAIL receipt and submits only the preceding read-only operation. The generator synchronizes all 13 standalone skills; plugin snapshots are not edited directly.

This records source behavior. Fixed installs, actual native references, command dimension matrices and full V1 retain separate evidence gates. See the [source regression report](evidence/filmcraft-params-container-source-20261008.json).
