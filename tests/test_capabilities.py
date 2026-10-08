"""FC-RT-002：参数漂移与运行上下文必须在依赖编辑前拒绝。"""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/filmcraft-use/scripts'


def load(name):
    path = SCRIPTS / (name + '.py')
    spec = importlib.util.spec_from_file_location('capability_test_' + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CapabilityTests(unittest.TestCase):
    def setUp(self):
        path = SCRIPTS / 'capabilities.py'
        self.assertTrue(path.is_file(), 'runtime capability adapter is missing')
        self.module = load('capabilities')
        self.expected = {'pluginId': 'filmcraft', 'runtimeSha256': 'a' * 64,
                         'commands': [{'id': 'example.edit', 'params': '{"time":tick}'}]}
        self.rows = [{'id': 'example.edit', 'params': '{"time":tick}', 'enabled': True}]
        self.installed = {'binarySha256': 'a' * 64, 'version': '0.2.0-test',
                          'versionOutput': 'filmcraft-cli 0.2.0-test', 'platform': 'darwin-arm64'}

    def snapshot(self, rows=None, mode='headless', desktop=None, resources=None):
        return self.module.snapshot(self.installed, self.expected, rows if rows is not None else self.rows,
                                    mode, desktop=desktop, resources=resources)

    def test_same_ids_with_different_parameter_types_are_rejected(self):
        changed = copy.deepcopy(self.rows)
        changed[0]['params'] = '{"time":str}'
        snapshot = self.snapshot(changed)
        self.assertEqual(snapshot['commands'][0]['parameterStatus'], 'drift')
        with self.assertRaisesRegex(ValueError, 'capability_contract_drift'):
            self.module.enforce(snapshot, {}, ['example.edit'])

    def test_absent_parameter_documentation_is_unknown_and_blocked(self):
        snapshot = self.snapshot([{'id': 'example.edit', 'enabled': True}])
        self.assertEqual(snapshot['commands'][0]['parameterStatus'], 'unknown')
        with self.assertRaisesRegex(ValueError, 'capability_unknown'):
            self.module.enforce(snapshot, {}, ['example.edit'])

    def test_known_parameters_are_verbatim_docs_not_invented_json_schema(self):
        snapshot = self.snapshot()
        self.module.enforce(snapshot, {}, ['example.edit'])
        self.assertEqual(snapshot['commands'][0]['execution'], 'NOT_RUN')
        self.assertEqual(snapshot['commands'][0]['reopen'], 'NOT_RUN')
        self.assertEqual(snapshot['commands'][0]['nonTargetPreservation'], 'NOT_RUN')
        self.assertNotIn('jsonSchema', snapshot['commands'][0])
        changed = copy.deepcopy(self.rows)
        changed[0]['enabled'] = False
        self.assertEqual(snapshot['parametersSha256'], self.snapshot(changed)['parametersSha256'])

    def test_missing_command_is_not_enabled_or_available(self):
        snapshot = self.snapshot([])
        with self.assertRaisesRegex(ValueError, 'capability_missing'):
            self.module.enforce(snapshot, {}, ['example.edit'])

    def test_runtime_mode_platform_version_and_digest_are_bound(self):
        snapshot = self.snapshot()
        for requires in ({'mode': 'bridge'}, {'platform': 'linux-x86_64'}, {'runtimeVersion': 'other'},
                         {'runtimeSha256': 'b' * 64}, {'parametersSha256': 'c' * 64}):
            with self.subTest(requires=requires), self.assertRaisesRegex(ValueError, 'capability_identity_mismatch'):
                self.module.enforce(snapshot, requires, ['example.edit'])
        self.module.enforce(snapshot, {'mode': 'headless', 'platform': 'darwin-arm64',
                                      'runtimeVersion': '0.2.0-test', 'runtimeSha256': 'a' * 64}, ['example.edit'])

    def test_bridge_requires_actual_desktop_identity_and_compatible_parameters(self):
        snapshot = self.snapshot(mode='bridge')
        with self.assertRaisesRegex(ValueError, 'capability_unknown.*desktop'):
            self.module.enforce(snapshot, {}, ['example.edit'])
        desktop = {'version': '0.2.0', 'binarySha256': 'd' * 64}
        snapshot = self.snapshot(mode='bridge', desktop=desktop)
        self.module.enforce(snapshot, {'desktopSha256': 'd' * 64}, ['example.edit'])
        with self.assertRaisesRegex(ValueError, 'capability_identity_mismatch'):
            self.module.enforce(snapshot, {'desktopSha256': 'e' * 64}, ['example.edit'])

    def test_missing_or_unknown_required_resources_block(self):
        for status in ('missing', 'unknown'):
            for kind in ('codec', 'model', 'font'):
                requires = {'resources': [{'kind': kind, 'name': 'required'}]}
                snapshot = self.snapshot(resources=[{'kind': kind, 'name': 'required', 'status': status}])
                with self.subTest(status=status, kind=kind), self.assertRaisesRegex(ValueError, 'capability_(missing|unknown)'):
                    self.module.enforce(snapshot, requires, ['example.edit'])

    def test_resource_requirements_cannot_assert_their_own_success(self):
        invalid = [None, [], {'unknown': True}, {'mode': 'auto'}, {'runtimeSha256': 'x'},
                   {'resources': [{'kind': 'font', 'name': 'Arial', 'status': 'available'}]},
                   {'resources': [{'kind': 'invented', 'name': 'x'}]}]
        for value in invalid:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'invalid_capability_requirements'):
                self.module.validate_requirements(value)

    def test_native_resource_queries_are_readonly_and_bound_to_probe_digest(self):
        responses = {
            'export.formats': [{'id': 'h264', 'available': True}],
            'fonts.list': [{'family': 'Arial', 'styles': ['Regular']}],
            'transcript.models': {'available': True, 'models': [{'id': 'whisper-base', 'installed': False}]},
        }
        calls = []
        def query(identifier):
            calls.append(identifier)
            return responses[identifier]
        resources = self.module.probe_resources([
            {'kind': 'codec', 'name': 'h264'}, {'kind': 'font', 'name': 'Arial'},
            {'kind': 'model', 'name': 'whisper-base'}], query)
        self.assertEqual([r['status'] for r in resources], ['available', 'available', 'missing'])
        self.assertEqual(set(calls), set(responses))
        self.assertTrue(all(len(r['probeSha256']) == 64 for r in resources))

    def test_malformed_probe_is_unknown_not_available(self):
        for reply in (None, {}, [{'id': 'h264', 'available': 'true'}]):
            result = self.module.probe_resources([{'kind': 'codec', 'name': 'h264'}], lambda _: reply)
            self.assertEqual(result[0]['status'], 'unknown')


class PublicCapabilityGateTests(unittest.TestCase):
    def test_native_workflow_rejects_parameter_drift_before_edit(self):
        native = load('native_workflow')
        rows = native.commands.catalog()['commands']
        identifier = rows[0]['id']
        current = [{**row, 'enabled': True} for row in rows]
        current[0]['params'] = '{"changedRequiredField":str}'
        session = Mock()
        session.request.return_value = {'content': [{'type': 'text', 'text': json.dumps(current)}]}
        state, receipts = {}, []
        with self.assertRaisesRegex((ValueError, RuntimeError), 'capability_contract_drift'):
            native.execute(session, {'command': identifier, 'params': {}}, state, receipts, ROOT)
        self.assertEqual(session.request.call_count, 1)
        self.assertEqual(state.get('lastAttempt'), None)
        self.assertEqual(receipts, [])

    def test_invalid_capability_requirement_fails_before_install_or_output(self):
        module = load('commands')
        identifier = module.catalog()['commands'][0]['id']
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'result'
            plan = {'schema': 'craft-command-plan/v1', 'requires': {'mode': 'invented'},
                    'operations': [{'command': identifier, 'params': {}}]}
            with self.assertRaisesRegex(ValueError, 'invalid_capability_requirements'):
                module.execute(plan, output, installer=Mock(side_effect=AssertionError('installed')))
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
