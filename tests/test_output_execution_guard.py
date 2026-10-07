"""同一目标只允许一个原生执行；中断身份不可自动重放。"""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/filmcraft-use/scripts/output_guard.py'


class OutputGuardTests(unittest.TestCase):
    def module(self):
        spec = importlib.util.spec_from_file_location('output_guard', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_public_workflow_claims_target_before_starting_native_session(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from contextlib import contextmanager
        spec = importlib.util.spec_from_file_location('workflow', SCRIPT.with_name('workflow.py'))
        workflow = importlib.util.module_from_spec(spec); spec.loader.exec_module(workflow)
        original = workflow.load_module
        @contextmanager
        def conflict(*args):
            raise ValueError('output_execution_conflict')
            yield
        def module(name):
            if name == 'bootstrap':
                return SimpleNamespace(install=lambda *args: {'executable': 'fixture-cli', 'binarySha256': 'c'*64})
            if name == 'output_guard':
                return SimpleNamespace(claim=conflict)
            if name == 'mcp_session':
                raise RuntimeError('native_started_without_claim')
            return original(name)
        with tempfile.TemporaryDirectory() as directory, patch.object(workflow, 'load_module', side_effect=module):
            with self.assertRaisesRegex(ValueError, 'output_execution_conflict'):
                workflow.execute({'document': {'name':'test', 'width':16, 'height':16, 'frameRate':{'num':12, 'den':1}}, 'operations': []}, Path(directory)/'delivery')

    def test_completed_owner_is_recorded_and_different_targets_are_independent(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with module.claim(root/'one', {'planHash': 'a'*64}):
                with module.claim(root/'two', {'planHash': 'b'*64}):
                    pass
            records = [json.loads(p.read_text()) for p in root.glob('.filmcraft-execution-*.json')]
            self.assertEqual(len(records), 2)
            self.assertTrue(all(r['state'] == 'finished' for r in records))
            self.assertEqual({r['identity']['planHash'] for r in records}, {'a'*64, 'b'*64})

    def test_live_owner_conflicts_and_killed_owner_requires_reconciliation(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'delivery'
            code = "import importlib.util,sys,time; s=importlib.util.spec_from_file_location('g',sys.argv[1]); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)\nwith m.claim(sys.argv[2],{'planHash':'a'*64}):\n print('owned',flush=True)\n time.sleep(60)"
            child = subprocess.Popen([sys.executable, '-I', '-B', '-c', code, str(SCRIPT), str(output)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                self.assertEqual(child.stdout.readline().strip(), 'owned')
                with self.assertRaisesRegex(ValueError, 'output_execution_conflict'):
                    with module.claim(output, {'planHash': 'a'*64}):
                        self.fail('second writer entered')
                child.kill(); child.communicate(timeout=10)
                with self.assertRaisesRegex(ValueError, 'output_execution_reconciling'):
                    with module.claim(output, {'planHash': 'a'*64}):
                        self.fail('unknown execution replayed')
                self.assertFalse(output.exists())
            finally:
                if child.poll() is None:
                    child.kill(); child.communicate(timeout=10)
                child.stdout.close(); child.stderr.close()

    def test_exception_preserves_unknown_identity(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'delivery'
            with self.assertRaisesRegex(RuntimeError, 'lost reply'):
                with module.claim(output, {'runtimeSha256': 'c'*64}):
                    raise RuntimeError('lost reply')
            record = json.loads(next(Path(directory).glob('.filmcraft-execution-*.json')).read_text())
            self.assertEqual(record['state'], 'reconciling')
            self.assertEqual(record['identity']['runtimeSha256'], 'c'*64)
            with self.assertRaisesRegex(ValueError, 'output_execution_reconciling'):
                with module.claim(output, {}):
                    self.fail('unknown replayed')

    def test_invalid_existing_registration_is_preserved(self):
        import hashlib
        module = self.module()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'delivery'
            digest = hashlib.sha256(str(output.resolve()).encode()).hexdigest()
            record = Path(directory)/('.filmcraft-execution-'+digest+'.json')
            record.write_bytes(b'user-owned data')
            with self.assertRaisesRegex(ValueError, 'output_execution_record_invalid'):
                with module.claim(output, {}):
                    self.fail('unrecognized file replaced')
            self.assertEqual(record.read_bytes(), b'user-owned data')

    def test_registration_symlink_cannot_overwrite_user_file(self):
        import hashlib
        module = self.module()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'delivery'
            digest = hashlib.sha256(str(output.resolve()).encode()).hexdigest()
            user = Path(directory)/'keep'; user.write_bytes(b'original')
            record = Path(directory)/('.filmcraft-execution-'+digest+'.json')
            record.symlink_to(user)
            with self.assertRaises(OSError):
                with module.claim(output, {}):
                    self.fail('symlink followed')
            self.assertEqual(user.read_bytes(), b'original')
            self.assertTrue(record.is_symlink())

    def test_existing_output_is_not_claimed_or_modified(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'user';output.mkdir();(output/'keep').write_text('original')
            with self.assertRaisesRegex(ValueError, 'output_exists'):
                with module.claim(output, {}):
                    self.fail('user directory entered')
            self.assertEqual((output/'keep').read_text(), 'original')
            self.assertFalse(list(Path(directory).glob('.filmcraft-execution-*.json')))


if __name__ == '__main__':
    unittest.main()
