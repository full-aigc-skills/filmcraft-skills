"""公共工作流把明确模型目录传给原生进程，且不改变调用者环境。"""
import importlib.util
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/filmcraft-use/scripts/workflow.py'
class WorkflowDataDirectoryTests(unittest.TestCase):
    def module(self):
        spec = importlib.util.spec_from_file_location('workflow_data_test', SCRIPT)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        return module
    def test_explicit_directory_overrides_environment_for_mcp(self):
        self.check_mcp(True)
    def test_environment_directory_reaches_mcp_without_explicit_option(self):
        self.check_mcp(False)
    def check_mcp(self, explicit):
        module = self.module(); original = module.load_module; calls = []
        def session(argv):
            calls.append(argv)
            raise RuntimeError('captured_native_start')
        def load(name):
            if name == 'bootstrap':
                return SimpleNamespace(install=lambda *a: {'executable':'fixture-cli', 'binarySha256':'c'*64})
            if name == 'mcp_session':
                return SimpleNamespace(Session=session)
            return original(name)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); configured = root / 'environment models'
            selected = root / 'explicit models' if explicit else configured
            with patch.dict(os.environ, {'FILMCRAFT_DATA_DIR':str(configured)}), patch.object(module, 'load_module', side_effect=load):
                plan = {'document':{'name':'test','width':16,'height':16,'frameRate':{'num':12,'den':1}},'operations':[]}
                with self.assertRaisesRegex(RuntimeError, 'captured_native_start'):
                    module.execute(plan, root/'output', **({'data_dir':selected} if explicit else {}))
                self.assertEqual(calls, [['fixture-cli','--data-dir',str(selected.resolve()),'mcp']])
                self.assertEqual(os.environ['FILMCRAFT_DATA_DIR'], str(configured))
                self.assertFalse(selected.exists())
    def test_auxiliary_native_process_receives_same_directory(self):
        module = self.module()
        with patch.object(module.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout='ok')) as invoke:
            self.assertEqual(module.run('native', ['inspect'], data_dir=Path('/tmp/film models')), 'ok')
            self.assertEqual(invoke.call_args.args[0], ['native','--data-dir','/tmp/film models','inspect'])
    def test_unconfigured_auxiliary_process_preserves_original_arguments(self):
        module = self.module()
        with patch.object(module.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout='ok')) as invoke:
            module.run('native', ['inspect'])
            self.assertEqual(invoke.call_args.args[0], ['native','inspect'])
if __name__ == '__main__':
    unittest.main()
