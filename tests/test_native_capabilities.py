"""单技能真实 MCP 能力探测与受控回复故障；不代表固定发行验收。"""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def hashes(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}


@unittest.skipUnless(os.environ.get('CRAFT_NATIVE_CAPABILITIES') == '1', 'explicit native opt-in')
class NativeCapabilitiesTests(unittest.TestCase):
    def test_isolated_native_snapshot_reopen_and_dependency_blocks(self):
        source = ROOT / 'skills/filmcraft-cli'
        before = hashes(source)
        with tempfile.TemporaryDirectory(prefix='filmcraft-capabilities-') as temporary:
            root = Path(temporary)
            skill = root / 'single-skill'
            shutil.copytree(source, skill)
            spec = importlib.util.spec_from_file_location('native_capabilities_commands', skill / 'scripts/commands.py')
            commands = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(commands)
            lock = json.loads((skill / 'scripts/runtime.lock.json').read_text())
            runtime = commands.load('bootstrap').install(lock, Path.home() / '.local/share/craft-runtimes')
            plan = json.loads((skill / 'examples/desktop-first-use.json').read_text())
            plan['requires'] = {'mode': 'headless', 'platform': runtime['platform'],
                'runtimeVersion': runtime['version'], 'runtimeSha256': runtime['binarySha256'],
                'resources': [{'kind': 'codec', 'name': 'h264'}, {'kind': 'font', 'name': 'Arial'}]}
            success = commands.execute(plan, root / 'success')
            self.assertEqual(success['result'], 'PASS', success.get('error'))
            snapshot = success['capabilitySnapshot']
            self.assertEqual(snapshot['runtime']['binarySha256'], runtime['binarySha256'])
            self.assertTrue(all(r['status'] == 'available' for r in snapshot['resources']))
            self.assertTrue(all(row['parameterStatus'] == 'match' for row in snapshot['commands']))
            self.assertTrue(all(row['execution'] == 'NOT_RUN' for row in snapshot['commands']))
            project = root / 'success/project.fcproj'
            original = hashlib.sha256(project.read_bytes()).hexdigest()
            reopen_plan = {'schema': 'craft-command-plan/v1', 'requires': plan['requires'], 'operations': [
                {'command': 'file.open', 'params': {'path': {'$ref': 'project.path'}}},
                {'command': 'sequence.inspect', 'params': {}}]}
            opened = commands.execute(reopen_plan, root / 'reopen', inputs={'project': project})
            self.assertEqual(opened['result'], 'PASS', opened.get('error'))
            sequence = opened['steps'][-1]['result']
            self.assertEqual((sequence['settings']['width'], sequence['settings']['height']), (96, 64))
            self.assertEqual(sequence['settings']['frame_rate'], {'num': 12, 'den': 1})
            outcomes = []
            for key, value in [('mode', 'bridge'), ('platform', 'unsupported-platform'),
                               ('runtimeSha256', '0' * 64), ('parametersSha256', '0' * 64)]:
                changed = copy.deepcopy(plan)
                changed['requires'][key] = value
                receipt = commands.execute(changed, root / ('mismatch-' + key))
                self.assertEqual(receipt['result'], 'FAIL')
                self.assertIn('capability_identity_mismatch', receipt['error'])
                self.assertEqual(receipt['steps'], [])
                outcomes.append({'case': key, 'result': 'PASS', 'error': receipt['error'], 'edits': 0})
            for kind in ('codec', 'model', 'font'):
                changed = copy.deepcopy(plan)
                changed['requires']['resources'] = [{'kind': kind, 'name': 'missing-filmcraft-evidence-resource'}]
                receipt = commands.execute(changed, root / ('missing-' + kind))
                self.assertEqual(receipt['result'], 'FAIL')
                self.assertIn('capability_missing', receipt['error'])
                self.assertEqual(receipt['steps'], [])
                self.assertEqual(receipt['capabilitySnapshot']['resources'][0]['status'], 'missing')
                outcomes.append({'case': 'missing-' + kind, 'result': 'PASS', 'edits': 0})
            native_session = commands.load('mcp_session').Session
            class FaultSession:
                def __init__(self, argv, fault):
                    self.session = native_session(argv)
                    self.fault = fault
                def __enter__(self):
                    self.session.__enter__()
                    return self
                def __exit__(self, *args):
                    return self.session.__exit__(*args)
                def request(self, method, params):
                    reply = self.session.request(method, params)
                    if (self.fault == 'late-contract' and params.get('name') == 'command_list'
                            and params.get('arguments', {}).get('filter') == 'file.saveAs'):
                        rows = commands.parse_reply(reply)
                        for row in rows:
                            if row['id'] == 'file.saveAs':
                                row['params'] = '{"newRequiredField":str}'
                        return {'content': [{'type': 'text', 'text': json.dumps(rows)}]}
                    if (self.fault == 'unknown-resource' and params.get('name') == 'command_run'
                            and params.get('arguments', {}).get('id') == 'fonts.list'):
                        return {'content': [{'type': 'text', 'text': '{"unexpected":"font list"}'}]}
                    return reply
            for fault in ('late-contract', 'unknown-resource'):
                receipt = commands.execute(plan, root / fault,
                    session_factory=lambda argv: FaultSession(argv, fault))
                self.assertEqual(receipt['result'], 'FAIL')
                if fault == 'late-contract':
                    self.assertEqual([s['state'] for s in receipt['steps']], ['succeeded', 'succeeded', 'blocked'])
                    self.assertEqual(receipt['steps'][-1]['capabilityCheck']['parameterStatus'], 'drift')
                    self.assertFalse((root / fault / 'project.fcproj').exists())
                else:
                    self.assertEqual(receipt['steps'], [])
                    self.assertEqual(receipt['capabilitySnapshot']['resources'][-1]['status'], 'unknown')
                self.assertTrue((root / fault / 'failure.json').is_file())
                outcomes.append({'case': fault, 'result': 'PASS', 'stepStates': [s['state'] for s in receipt['steps']]})
            self.assertEqual(hashlib.sha256(project.read_bytes()).hexdigest(), original)
            self.assertEqual(hashes(skill), before)
            self.assertEqual(hashes(source), before)
            report = {'schema': 'filmcraft-native-capability-evidence/v1', 'result': 'PASS',
                'scope': 'source candidate isolated single skill, actual headless MCP plus controlled reply faults; not pinned install or all modes',
                'skillFiles': before, 'runtime': snapshot['runtime'], 'snapshot': snapshot,
                'projectSha256': original, 'nativeReopen': 'PASS', 'sourcePreservation': 'PASS',
                'cases': outcomes, 'bridge': 'NOT_RUN', 'otherPlatforms': 'NOT_RUN',
                'modelInference': 'NOT_RUN', 'fontAppearance': 'NOT_RUN', 'codecExport': 'NOT_RUN'}
            if os.environ.get('CRAFT_NATIVE_CAPABILITIES_REPORT'):
                Path(os.environ['CRAFT_NATIVE_CAPABILITIES_REPORT']).write_text(json.dumps(report, indent=2) + '\n')
