"""旧公开原生转发入口也必须遵守独立根授权与子进程环境边界。"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RawCliPermissionsTests(unittest.TestCase):
    def fixture(self, root):
        scripts = root / 'one-skill/scripts'; scripts.mkdir(parents=True)
        for name in ('cli.py', 'execution_permissions.py', 'runtime.lock.json'):
            shutil.copyfile(ROOT / 'skills/filmcraft-use/scripts' / name, scripts / name)
        (scripts / 'bootstrap.py').write_text("def install(*args): raise ValueError('owned_installer_would_run')\n")
        return scripts / 'cli.py'

    def call(self, path, root, args, environment=None, policy=False, maintenance=False):
        prefix = [sys.executable, '-I', '-B', str(path), '--runtime-home', str(root / 'runtime')]
        if policy: prefix += ['--read-root', str(root), '--write-root', str(root)]
        if maintenance: prefix += ['--model-maintenance']
        return subprocess.run([*prefix, '--', *args], env=environment, capture_output=True, text=True)

    def test_native_edit_refuses_missing_policy_before_installer(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); path = self.fixture(root)
            result = self.call(path, root, ['exec', 'file.newProject', '{"name":"Owned"}', '--save-as', str(root / 'forbidden.fcproj')])
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)['error'], 'execution_permissions_required')
            self.assertFalse((root / 'runtime').exists())
            self.assertFalse((root / 'forbidden.fcproj').exists())

    def test_discovery_with_project_cannot_bypass_required_policy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); path = self.fixture(root)
            result = self.call(path, root, ['commands', '--json', '--project', str(root / 'project.fcproj')])
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)['error'], 'execution_permissions_required')
            self.assertFalse((root / 'runtime').exists())

    def test_exact_version_discovery_filters_environment_without_requiring_edit_roots(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); path = self.fixture(root)
            observer = root / 'owned-observer'
            observer.write_text('#!' + sys.executable + '\nimport json,os\nprint(json.dumps({"canaryPresent":"FILMCRAFT_OWNED_SECRET_CANARY" in os.environ,"proxyPresent":"HTTP_PROXY" in os.environ}))\n')
            observer.chmod(0o700)
            path.with_name('bootstrap.py').write_text('def install(*args): return {"executable":' + repr(str(observer)) + '}\n')
            result = self.call(path, root, ['--version'], dict(os.environ, FILMCRAFT_OWNED_SECRET_CANARY='OWNED_TEST_ONLY', HTTP_PROXY='https://owned-test.invalid'))
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual(json.loads(result.stdout), {'canaryPresent':False, 'proxyPresent':False})

    def test_model_download_requires_separate_maintenance_before_installer(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); path = self.fixture(root)
            result = self.call(path, root, ['exec', 'transcript.downloadModel', '{"model":"whisper-tiny"}'], policy=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)['error'], 'model_maintenance_required')
            self.assertFalse((root / 'runtime').exists())

    def test_model_maintenance_refuses_combined_editing_and_duplicate_model_fields(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); path = self.fixture(root); data = root / 'data'; data.mkdir()
            for arguments in [
                ['exec', 'file.newProject', '{}', '--data-dir', str(data)],
                ['exec', 'transcript.downloadModel', '{"model":"whisper-tiny"}', '--data-dir', str(data), '--project', str(root / 'user.fcproj')],
                ['exec', 'transcript.downloadModel', '{"model":"whisper-tiny","model":"whisper-base"}', '--data-dir', str(data)],
                ['exec', 'transcript.downloadModel', '{"model":"whisper-tiny","extra":"owned"}', '--data-dir', str(data)]]:
                with self.subTest(arguments=arguments):
                    result = self.call(path, root, arguments, policy=True, maintenance=True)
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(json.loads(result.stdout)['error'], 'invalid_model_maintenance_request')
                    self.assertFalse((root / 'runtime').exists())

    def test_model_maintenance_refuses_runtime_cache_as_data_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); path = self.fixture(root); data = root / 'runtime'; data.mkdir()
            result = self.call(path, root, ['exec', 'transcript.downloadModel', '{"model":"whisper-tiny"}', '--data-dir', str(data)], policy=True, maintenance=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)['error'], 'model_maintenance_protected_directory')


if __name__ == '__main__':
    unittest.main()
