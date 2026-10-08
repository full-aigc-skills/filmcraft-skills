"""命令说明必须来自已核验的同一原生快照，不能只改版本或摘要。"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CatalogIdentityTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('catalog_identity_builder', ROOT / 'scripts/build_command_coverage.py')
        self.builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.builder)
        base = ROOT / 'skills/filmcraft-use'
        self.lock = json.loads((base / 'scripts/runtime.lock.json').read_text())
        self.snapshot = {
            'schema': 'craft-native-command-snapshot/v1', 'pluginId': 'filmcraft',
            'runtimeVersion': self.lock['resolvedVersion'], 'platform': 'darwin-arm64',
            'runtimeSha256': self.lock['artifacts']['darwin-arm64']['binarySha256'],
            'mode': 'headless-empty',
            'commands': [{'id': 'file.saveAs', 'label': 'Save As', 'params': '{"path":str}', 'enabled': True}],
        }

    def test_current_reference_binds_the_captured_binary_not_an_older_runtime(self):
        base = ROOT / 'skills/filmcraft-use/references'
        reference = json.loads((base / 'commands.json').read_text())
        snapshot = json.loads((base / 'native-command-snapshot.json').read_text())
        self.assertEqual(reference['runtimeSha256'], snapshot['runtimeSha256'])
        self.assertEqual(reference['runtimeSha256'], self.lock['artifacts']['darwin-arm64']['binarySha256'])

    def test_each_standalone_reference_retains_its_inventory_with_current_parameters(self):
        base = ROOT / 'skills/filmcraft-use/references'
        master = json.loads((base / 'commands.json').read_text())
        known = {row['id']: row for row in master['commands']}
        expected_counts = {'filmcraft-cli-audio': 38, 'filmcraft-cli-color': 13,
            'filmcraft-cli-export': 33, 'filmcraft-cli-media': 31, 'filmcraft-cli-motion': 105,
            'filmcraft-cli-project': 131, 'filmcraft-cli-subtitles': 22, 'filmcraft-cli-timeline': 135}
        for path in sorted((ROOT / 'skills').glob('*/references/commands.json')):
            with self.subTest(skill=path.parts[-3]):
                value = json.loads(path.read_text())
                self.assertEqual(value['runtimeSha256'], master['runtimeSha256'])
                self.assertEqual(value['runtimeVersion'], master['runtimeVersion'])
                self.assertNotIn('runtimePatchSourceCommit', value)
                self.assertEqual(len(value['commands']), expected_counts.get(path.parts[-3], 666))
                self.assertEqual(value['commands'], [known[row['id']] for row in value['commands']])

    def test_capture_uses_actual_rows_and_lock_provenance_without_execution_claims(self):
        result = self.builder.reflection_from_snapshot(self.snapshot, self.lock)
        self.assertEqual(result['runtimeSha256'], self.snapshot['runtimeSha256'])
        self.assertEqual(result['runtimeVersion'], self.lock['resolvedVersion'])
        self.assertEqual(result['upstreamCommit'], self.lock['upstreamCommit'])
        self.assertEqual(result['commands'], [{'id': 'file.saveAs', 'label': 'Save As',
                                             'params': '{"path":str}', 'enabledAtEmptySession': True}])
        self.assertNotIn('runtimePatchSourceCommit', result)
        self.assertIn('not capability or creative acceptance', result['scope'])

    def test_unverified_identity_or_execution_mode_cannot_be_relabelled(self):
        for field, value in [('runtimeSha256', '0' * 64), ('runtimeVersion', '0.0.0'),
                             ('platform', 'unsupported'), ('pluginId', 'foreign'),
                             ('mode', 'bridge')]:
            changed = copy.deepcopy(self.snapshot); changed[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'native_snapshot_identity_mismatch'):
                self.builder.reflection_from_snapshot(changed, self.lock)

    def test_ambiguous_or_malformed_rows_are_rejected_before_generation(self):
        row = self.snapshot['commands'][0]
        for rows in ([], [row, row], [None], [{**row, 'enabled': 'true'}],
                     [{**row, 'params': None}], [{**row, 'id': ''}]):
            changed = copy.deepcopy(self.snapshot); changed['commands'] = rows
            with self.subTest(rows=rows), self.assertRaisesRegex(ValueError, 'native_command_rows_invalid'):
                self.builder.reflection_from_snapshot(changed, self.lock)

    def test_generation_rejects_same_identity_with_changed_parameters_or_inventory(self):
        reflection = self.builder.reflection_from_snapshot(self.snapshot, self.lock)
        self.builder.verify_reflection(reflection, self.snapshot, self.lock)
        edits = [lambda x: x.update(runtimeSha256='0' * 64),
                 lambda x: x['commands'][0].update(params='{"changed":str}'),
                 lambda x: x['commands'].append(copy.deepcopy(x['commands'][0])),
                 lambda x: x['commands'].clear()]
        for edit in edits:
            changed = copy.deepcopy(reflection); edit(changed)
            with self.subTest(edit=edit), self.assertRaisesRegex(ValueError, 'reference_snapshot_mismatch'):
                self.builder.verify_reflection(changed, self.snapshot, self.lock)


if __name__ == '__main__':
    unittest.main()
