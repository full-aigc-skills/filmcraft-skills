"""受控 Harness 的尝试身份附加到原始 guard；独立旧调用保持兼容。"""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location('context_' + name, ROOT / 'skills/filmcraft-use/scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


class ExecutionContextTests(unittest.TestCase):
    def context(self):
        return {'taskId': '任务一', 'attemptId': 'attempt-1', 'sourceRevision': 'a' * 40, 'sourceTreeSha256': 'b' * 64}

    def test_context_is_preserved_without_rewriting_plan_identity(self):
        guard = load('output_guard'); context = self.context()
        with patch.dict(os.environ, {'FILMCRAFT_EXECUTION_CONTEXT': json.dumps(context)}):
            self.assertEqual(guard.execution_context(), context)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); output = root / 'delivery'; identity = {'planHash': 'c' * 64}
            with guard.claim(output, identity, context): pass
            record = json.loads(next(root.glob('.filmcraft-execution-*.json')).read_text())
            self.assertEqual(record['context'], context); self.assertEqual(record['identity'], identity)
            self.assertEqual(record['state'], 'finished')

    def test_legacy_call_does_not_invent_context(self):
        guard = load('output_guard')
        with patch.dict(os.environ, {}, clear=True): self.assertIsNone(guard.execution_context())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with guard.claim(root / 'delivery', {}): pass
            record = json.loads(next(root.glob('.filmcraft-execution-*.json')).read_text())
            self.assertNotIn('context', record)

    def test_invalid_or_ambiguous_context_is_rejected(self):
        guard = load('output_guard'); context = self.context()
        invalid = ['null', '[]', '{}', '{"taskId":"a","taskId":"b"}']
        for key, value in [('taskId', ''), ('attemptId', True), ('sourceRevision', 'x'), ('sourceTreeSha256', 'x')]:
            invalid.append(json.dumps(dict(context, **{key: value})))
        invalid.append(json.dumps(dict(context, forged=True)))
        for raw in invalid:
            with self.subTest(raw=raw), patch.dict(os.environ, {'FILMCRAFT_EXECUTION_CONTEXT': raw}):
                with self.assertRaisesRegex(ValueError, 'invalid_execution_context'): guard.execution_context()

    def test_invalid_context_fails_before_install_or_output(self):
        workflow = load('workflow'); original = workflow.load_module
        def modules(name):
            if name == 'bootstrap': return Mock(install=Mock(side_effect=AssertionError('installed')))
            return original(name)
        plan = {'document': {'name': 'test', 'width': 32, 'height': 32, 'frameRate': {'num': 12, 'den': 1}}, 'operations': []}
        with tempfile.TemporaryDirectory() as temporary, patch.object(workflow, 'load_module', side_effect=modules), patch.dict(os.environ, {'FILMCRAFT_EXECUTION_CONTEXT': '{}'}):
            output = Path(temporary) / 'output'
            with self.assertRaisesRegex(ValueError, 'invalid_execution_context'): workflow.execute(plan, output)
            self.assertFalse(output.exists())
