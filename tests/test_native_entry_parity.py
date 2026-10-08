"""FC-CM-001：公开原生入口共享精确 tick 合同且在副作用前拒绝非法输入。"""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/filmcraft-use/scripts'


def load(name):
    spec = importlib.util.spec_from_file_location('entry_parity_' + name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NativeEntryParityTests(unittest.TestCase):
    def setUp(self):
        self.commands = load('commands')
        self.native = load('native_workflow')
        self.workflow = load('workflow')

    def operation(self, value):
        return {'command': 'multicam.cutToCamera', 'params': {'camera': 2, 'time': value}}

    def test_both_entries_reject_invalid_literal_ticks(self):
        for value in ('254016000000', True, False, 1.5, 2 ** 63, -(2 ** 63) - 1):
            for entry in ('commands', 'workflow'):
                with self.subTest(value=value, entry=entry), self.assertRaisesRegex(ValueError, 'invalid_tick_parameter'):
                    operation = self.operation(value)
                    if entry == 'commands':
                        self.commands.validate({'schema': 'craft-command-plan/v1', 'operations': [operation]})
                    else:
                        self.workflow.validate({'operations': [{'command': 'native.command', 'params': operation}]})

    def test_nested_word_ticks_share_the_same_contract(self):
        for field in ('start', 'end'):
            for value in ('0', True, 0.0, 2 ** 63):
                operation = {'command': 'transcript.set', 'params': {'item': 1, 'transcript': {
                    'words': [{'text': 'word', 'start': 0, 'end': 1}]}}}
                operation['params']['transcript']['words'][0][field] = value
                with self.subTest(field=field, value=value), self.assertRaisesRegex(ValueError, 'invalid_tick_parameter'):
                    self.native.validate(operation)

    def test_exact_large_and_boundary_integers_remain_exact(self):
        for value in (2 ** 53 + 1, 2 ** 63 - 1, -(2 ** 63)):
            operation = self.operation(value)
            self.native.validate(operation)
            self.assertEqual(json.loads(json.dumps(operation))['params']['time'], value)
        self.assertEqual(self.workflow.ticks(str(2 ** 53 + 1)), 2 ** 53 + 1)

    def test_literal_failure_precedes_install_and_output_writes_in_each_skill(self):
        suite = json.loads((ROOT / 'skill-suite.json').read_text())
        for entry in suite['skills']:
            with self.subTest(skill=entry['name']), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                skill = root / entry['name']
                shutil.copytree(ROOT / 'skills' / entry['name'], skill,
                                ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                # 非法输入测试禁止网络及实际安装；到达安装器即暴露预检缺失。
                (skill / 'scripts/bootstrap.py').write_text(
                    "def install(*args, **kwargs):\n    raise RuntimeError('unexpected_runtime_install')\n")
                for script in ('commands', 'workflow'):
                    operation = self.operation('254016000000')
                    plan = {'schema': 'craft-command-plan/v1', 'operations': [operation]} if script == 'commands' else {
                        'document': {'name': 'Parity', 'width': 320, 'height': 180,
                                     'frameRate': {'num': 12, 'den': 1}},
                        'operations': [{'command': 'native.command', 'params': operation}]}
                    plan_path = root / 'plan.json'
                    plan_path.write_text(json.dumps(plan))
                    output, runtime = root / 'output', root / 'runtime'
                    argv = [sys.executable, '-I', '-B', str(skill / 'scripts' / (script + '.py'))]
                    if script == 'commands':
                        argv.append('run')
                    argv += [str(plan_path), '--output', str(output), '--runtime-home', str(runtime)]
                    result = subprocess.run(argv, capture_output=True, text=True, timeout=10)
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertIn('invalid_tick_parameter', json.loads(result.stdout)['error'])
                    self.assertFalse(output.exists())
                    self.assertFalse(runtime.exists())
                self.assertFalse(any(skill.rglob('*.pyc')))

    def test_reference_is_allowed_in_plan_and_rechecked_before_native_request(self):
        operation = self.operation({'$ref': 'timing.value'})
        self.workflow.validate({'operations': [{'command': 'native.command', 'params': operation}]})
        for value in ('0', True, 0.0, 2 ** 63):
            resolved = self.workflow.resolve(operation, {'timing': {'value': value}})
            session = Mock()
            state, receipts = {}, []
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'invalid_tick_parameter'):
                self.native.execute(session, resolved, state, receipts, ROOT)
            session.request.assert_not_called()
            self.assertEqual(state, {})
            self.assertEqual(receipts, [])

    def test_entire_referenced_transcript_is_checked_after_resolution(self):
        operation = {'command': 'transcript.set', 'params': {'item': 1, 'transcript': {'$ref': 'prior.transcript'}}}
        self.workflow.validate({'operations': [{'command': 'native.command', 'params': operation}]})
        resolved = self.workflow.resolve(operation, {'prior': {'transcript': {
            'words': [{'text': 'word', 'start': '0', 'end': 1}]}}})
        session = Mock()
        with self.assertRaisesRegex(ValueError, 'invalid_tick_parameter'):
            self.native.execute(session, resolved, {}, [], ROOT)
        session.request.assert_not_called()

    def test_wrong_plan_entry_reports_the_correct_runner(self):
        with self.assertRaisesRegex(ValueError, r'invalid_command_plan.*workflow.py'):
            self.commands.validate({'operations': [{'command': 'native.command', 'params': self.operation(0)}]})
        with self.assertRaisesRegex(ValueError, r'invalid_workflow_plan.*commands.py'):
            self.workflow.validate({'schema': 'craft-command-plan/v1', 'operations': [self.operation(0)]})


if __name__ == '__main__':
    unittest.main()
