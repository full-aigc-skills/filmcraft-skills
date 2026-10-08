"""能力阻断必须留下可检查证据，异常探测不得变成缺失或成功。"""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/filmcraft-use/scripts'


def load(name):
    spec = importlib.util.spec_from_file_location('capability_evidence_' + name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Session:
    def __init__(self, commands, drift_after_edit=False):
        self.commands = commands
        self.edits = []
        self.drift_after_edit = drift_after_edit
        self.registry_calls = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def request(self, method, params):
        if method == 'tools/list':
            return {'tools': [{'name': name} for name in self.commands.ROUTES['filmcraft'][:2]]}
        if params['name'] == self.commands.ROUTES['filmcraft'][0]:
            self.registry_calls += 1
            rows = [{**row, 'enabled': True} for row in self.commands.catalog()['commands']]
            if self.drift_after_edit and self.edits:
                for row in rows:
                    if row['id'] == 'file.newProject':
                        row['params'] = '{"changedRequiredField":str}'
            result = rows
        else:
            identifier = params['arguments']['id']
            if identifier == 'fonts.list':
                result = [{'family': 'Arial', 'styles': ['Regular']}]
            elif identifier == 'export.formats':
                result = [{'id': 'h264', 'available': True}]
            else:
                self.edits.append(params)
                result = {}
        return {'content': [{'type': 'text', 'text': json.dumps(result)}]}


class CapabilityEvidenceTests(unittest.TestCase):
    def test_partial_desktop_metadata_stays_unknown(self):
        module = load('capabilities')
        expected = {'pluginId': 'filmcraft', 'commands': []}
        for desktop in ({'version': '0.2.0', 'binarySha256': None},
                        {'version': '', 'binarySha256': 'a' * 64}):
            snapshot = module.snapshot({}, expected, [], 'bridge', desktop=desktop)
            self.assertEqual(snapshot['desktop']['status'], 'unknown')
            with self.assertRaisesRegex(ValueError, 'capability_unknown'):
                module.enforce(snapshot, {}, [])

    def test_conflicting_native_resource_rows_are_unknown(self):
        module = load('capabilities')
        cases = [
            ('codec', 'h264', [{'id': 'h264', 'available': True}, {'id': 'h264', 'available': False}]),
            ('model', 'tiny', {'available': True, 'models': [
                {'id': 'tiny', 'installed': True}, {'id': 'tiny', 'installed': False}]}),
            ('font', 'Arial', [{'family': 'Arial', 'styles': [None]}]),
        ]
        for kind, name, reply in cases:
            with self.subTest(kind=kind):
                result = module.probe_resources([{'kind': kind, 'name': name}], lambda _: reply)
                self.assertEqual(result[0]['status'], 'unknown')

    def test_failed_stage_preserves_snapshot_and_resource_check_hashes(self):
        module = load('preserved_stage')
        state = {'capabilitySnapshot': {'schema': 'filmcraft-capability-snapshot/v1', 'mode': 'headless'},
                 'resourceCapabilities': [{'kind': 'model', 'name': 'tiny', 'status': 'missing'}]}
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'delivery'
            with self.assertRaisesRegex(ValueError, 'capability_missing'):
                with module.preserved_stage(output, '.stage-', state) as directory:
                    stage = Path(directory)
                    raise ValueError('capability_missing: model:tiny')
            failure = json.loads((output / 'failure.json').read_text())
            self.assertIn('capabilities.json', failure['files'])
            evidence = json.loads((stage / 'capabilities.json').read_text())
            self.assertEqual(evidence['resourceChecks'], state['resourceCapabilities'])
            self.assertFalse(failure['replayAllowed'])

    def test_inferred_missing_font_is_recorded_as_blocked_without_edit(self):
        commands = load('commands')
        session = Session(commands)
        plan = {'schema': 'craft-command-plan/v1', 'operations': [
            {'command': 'captions.setStyle', 'params': {'track': 'C1', 'font': 'missing-test-font'}}]}
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'delivery'
            receipt = commands.execute(plan, output,
                installer=lambda *args: {'executable': 'native', 'binarySha256': 'a' * 64},
                session_factory=lambda *args: session)
            self.assertEqual(receipt['result'], 'FAIL')
            self.assertEqual(session.edits, [])
            self.assertEqual(len(receipt['steps']), 1)
            self.assertEqual(receipt['steps'][0]['state'], 'blocked')
            self.assertEqual(receipt['steps'][0]['resourceCapabilities'][0]['status'], 'missing')
            self.assertEqual(json.loads((output / 'failure.json').read_text()), receipt)

    def test_late_parameter_drift_retains_prior_success_and_blocked_attempt(self):
        commands = load('commands')
        session = Session(commands, drift_after_edit=True)
        plan = {'schema': 'craft-command-plan/v1', 'operations': [
            {'command': 'file.newProject', 'params': {}}, {'command': 'file.newProject', 'params': {}}]}
        with tempfile.TemporaryDirectory() as temporary:
            receipt = commands.execute(plan, Path(temporary) / 'delivery',
                installer=lambda *args: {'executable': 'native', 'binarySha256': 'a' * 64},
                session_factory=lambda *args: session)
            self.assertEqual(receipt['result'], 'FAIL')
            self.assertEqual(len(session.edits), 1)
            self.assertEqual([step['state'] for step in receipt['steps']], ['succeeded', 'blocked'])
            self.assertEqual(receipt['steps'][-1]['capabilityCheck']['parameterStatus'], 'drift')

    def test_resource_query_uses_current_contract_not_cached_catalog(self):
        commands = load('commands')
        session = Session(commands)
        original = session.request
        def changed(method, params):
            reply = original(method, params)
            if params.get('name') == commands.ROUTES['filmcraft'][0]:
                rows = json.loads(reply['content'][0]['text'])
                for row in rows:
                    if row['id'] == 'fonts.list':
                        row['params'] = '{"requiredNewParameter":str}'
                reply['content'][0]['text'] = json.dumps(rows)
            return reply
        session.request = changed
        rows = [{**row, 'enabled': True} for row in commands.catalog()['commands']]
        result = commands.probe_required_resources(session, [{'kind': 'font', 'name': 'Arial'}], rows)
        self.assertEqual(result[0]['status'], 'unknown')
        self.assertGreater(session.registry_calls, 0)

    def test_model_is_reprobed_after_explicit_install(self):
        module = load('capabilities')
        reply = {'available': True, 'models': [{'id': 'tiny', 'installed': False}]}
        query = Mock(side_effect=lambda _: copy.deepcopy(reply))
        required = [{'kind': 'model', 'name': 'tiny'}]
        self.assertEqual(module.probe_resources(required, query)[0]['status'], 'missing')
        reply['models'][0]['installed'] = True
        self.assertEqual(module.probe_resources(required, query)[0]['status'], 'available')
        self.assertEqual(query.call_count, 2)

    def test_workflow_checks_contract_again_before_first_edit(self):
        workflow = load('workflow')
        commands = workflow.native_module().commands
        session = Session(commands)
        original_request = session.request
        def changed(method, params):
            reply = original_request(method, params)
            if params.get('name') == commands.ROUTES['filmcraft'][0] and session.registry_calls > 1:
                rows = json.loads(reply['content'][0]['text'])
                for row in rows:
                    if row['id'] == 'file.newProject':
                        row['params'] = '{"newRequiredField":str}'
                reply['content'][0]['text'] = json.dumps(rows)
            return reply
        session.request = changed
        original_load = workflow.load_module
        def modules(name):
            if name == 'bootstrap':
                return Mock(install=lambda *args: {'executable': 'native', 'binarySha256': 'a' * 64})
            if name == 'mcp_session':
                return Mock(Session=lambda *args: session)
            return original_load(name)
        plan = {'document': {'name': 'test', 'width': 32, 'height': 32, 'frameRate': {'num': 12, 'den': 1}},
                'operations': [{'command': 'native.command', 'params': {'command': 'sequence.inspect', 'params': {}}}],
                'frames': ['0'], 'export': {'audioRequired': False}}
        with tempfile.TemporaryDirectory() as temporary, patch.object(workflow, 'load_module', side_effect=modules):
            output = Path(temporary) / 'delivery'
            with self.assertRaisesRegex(ValueError, 'capability_contract_drift'):
                workflow.execute(plan, output)
            self.assertEqual(session.edits, [])
            failure = json.loads((output / 'failure.json').read_text())
            self.assertIn('capabilities.json', failure['files'])
