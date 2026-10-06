"""显式启用的真实首次使用测试；未启用时不得算作运行时验收通过。"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


@unittest.skipUnless(os.environ.get('CRAFT_LIVE_TEST') == '1', 'set CRAFT_LIVE_TEST=1 for real official download and native roundtrip')
class FirstUseTests(unittest.TestCase):
    def test_isolated_skill_install_save_reopen_and_reuse(self):
        source = Path(__file__).resolve().parents[1] / 'skills/filmcraft-use'
        with tempfile.TemporaryDirectory(prefix='craft-first-use-') as tmp:
            root = Path(tmp)
            skill = root / 'single-skill'
            shutil.copytree(source, skill, ignore=shutil.ignore_patterns('__pycache__'))
            runtime = root / 'runtime'
            def run(argv, input=None):
                result = subprocess.run(argv, cwd=root, input=input, capture_output=True, text=True, timeout=180)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return result.stdout
            setup = [sys.executable, str(skill / 'scripts/bootstrap.py'), '--runtime-home', str(runtime)]
            installed = json.loads(run(setup))
            self.assertFalse(installed['reused'])
            cli = installed['executable']
            project = root / 'probe.fcproj'
            operations = [
                {'id': 'file.newProject', 'params': {'name': 'First use'}},
                {'id': 'file.newSequence', 'params': {'name': 'Probe', 'width': 640, 'height': 360, 'fps': 30}},
                {'id': 'captions.newTrack', 'params': {'format': 'Subtitle', 'name': 'Captions'}},
                {'id': 'captions.add', 'params': {'track': 'C1', 'text': 'First use verified', 'seconds': 0, 'durationSeconds': 2}},
            ]
            output = run([cli, '--save-as', str(project), 'run', '-'], '\n'.join(json.dumps(x) for x in operations) + '\n')
            receipts = [json.loads(line) for line in output.splitlines()]
            self.assertEqual(len(receipts), 4)
            self.assertTrue(all(x['ok'] for x in receipts))
            self.assertGreater(project.stat().st_size, 0)
            reopened = json.loads(run([cli, '--project', str(project), 'inspect']))
            self.assertEqual(reopened['sequence']['settings']['width'], 640)
            self.assertEqual(reopened['sequence']['durationFrames'], 60)
            captions = run([cli, '--project', str(project), 'exec', 'captions.list'])
            self.assertIn('First use verified', captions)
            reused = json.loads(run(setup))
            self.assertTrue(reused['reused'])
            self.assertEqual(installed['executable'], reused['executable'])
            # 真实下载后污染回执，拒绝复用且保留原生工程及整套安装。
            receipt_path = Path(cli).parent / 'installation.json'
            original_receipt = receipt_path.read_bytes()
            changed = json.loads(original_receipt)
            changed['platform'] = 'wrong-platform'
            receipt_path.write_text(json.dumps(changed))
            snapshot = {p.name: p.read_bytes() for p in receipt_path.parent.iterdir() if p.is_file()}
            project_bytes = project.read_bytes()
            refused = subprocess.run(setup, cwd=root, capture_output=True, text=True, timeout=20)
            self.assertEqual(refused.returncode, 1, refused.stdout + refused.stderr)
            self.assertIn('installation_receipt_mismatch', json.loads(refused.stdout)['error'])
            self.assertEqual(snapshot, {p.name: p.read_bytes() for p in receipt_path.parent.iterdir() if p.is_file()})
            self.assertEqual(project.read_bytes(), project_bytes)
            receipt_path.write_bytes(original_receipt)
            self.assertTrue(json.loads(run(setup))['reused'])
            self.assertIn('First use verified', run([cli, '--project', str(project), 'exec', 'captions.list']))


if __name__ == '__main__':
    unittest.main()
