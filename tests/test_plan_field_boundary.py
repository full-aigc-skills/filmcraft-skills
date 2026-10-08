"""不可信计划扩展字段不得进入原生执行或交付包。"""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/filmcraft-use/scripts/workflow.py'
CANARY = 'OWNED_TEST_CANARY_NO_REAL_SECRET'

class PlanFieldBoundaryTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('field_boundary_workflow', SCRIPT)
        self.workflow = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.workflow)

    def test_unknown_root_fields_refuse_before_any_asset_or_runtime_read(self):
        for field in ('metadata', 'apiKey', CANARY):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                with patch.object(self.workflow, 'preflight_assets', side_effect=AssertionError('asset read reached')):
                    with self.assertRaisesRegex(ValueError, '^invalid_workflow_fields$'):
                        self.workflow.execute({'document': {'name': 'Owned', 'width': 32, 'height': 32, 'frameRate': {'num': 12, 'den': 1}}, 'operations': [], field: CANARY}, root/'output', root/'runtime')
                self.assertFalse((root/'output').exists())
                self.assertFalse((root/'runtime').exists())

    def test_unknown_operation_fields_refuse_without_echoing_field_or_value(self):
        for field in ('metadata', 'instructions', CANARY):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, '^invalid_operation_fields$') as caught:
                    self.workflow.validate({'operations': [{'command': 'captions.newTrack', 'params': {}, field: CANARY}]})
                self.assertNotIn(CANARY, str(caught.exception))

    def test_public_entry_returns_safe_refusal_and_preserves_existing_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = root/'plan.json';plan.write_text(json.dumps({'operations': [], 'metadata': {'apiKey': CANARY}}))
            marker = root/'untouched.fcproj';marker.write_bytes(b'owned existing project')
            result = subprocess.run([sys.executable, '-I', '-B', str(SCRIPT), str(plan), '--read-root', str(root.resolve()), '--write-root', str(root.resolve()), '--output', str(root/'output'),
                                     '--runtime-home', str(root/'runtime')], capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)['error'], 'invalid_workflow_fields')
            self.assertNotIn(CANARY, result.stdout+result.stderr)
            self.assertFalse((root/'output').exists());self.assertFalse((root/'runtime').exists())
            self.assertEqual(marker.read_bytes(), b'owned existing project')

    def test_documented_workflow_fields_keep_existing_contract(self):
        self.workflow.validate({'document': {'name': 'Owned', 'width': 32, 'height': 32, 'frameRate': {'num': 12, 'den': 1}},
            'assets': {}, 'operations': [], 'frames': ['0'], 'export': {'audioRequired': False, 'burnCaptions': True},
            'expectedProjectSha256': 'a'*64})

    def test_command_plan_keeps_its_existing_entry_hint(self):
        with self.assertRaisesRegex(ValueError, 'use commands.py check/run'):
            self.workflow.validate({'schema': 'craft-command-plan/v1', 'operations': []})
