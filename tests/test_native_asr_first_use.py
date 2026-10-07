"""独立转录技能的真实模型首次安装与识别；需显式启用，保留原生交付证据。"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = Path(os.environ.get('CRAFT_INSTALLED_TASK_SKILLS_ROOT', ROOT / 'skills')).resolve()
TICKS = 254016000000
REFERENCE = ('Welcome to our creative studio. Today we are making a short film with clear sound '
             'and simple captions. Save the project and keep every scene ready for editing.')
MODEL_FILES = {
    'config.json': (1983, 'ffdccec4f3211f4c63310f2b7098f309fe70f3952cedc5e4d11e43f5b2379b98'),
    'generation_config.json': (3747, 'a5d5325911f16e74001a72fa13d6e208eee51548f994646de1f4b4cc8b35b512'),
    'tokenizer.json': (2480466, '27fc476bfe7f17299480be2273fc0608e4d5a99aba2ab5dec5374b4482d1a566'),
    'model.safetensors': (151061672, '7ebd0e69e78190ffe1438491fa05cc1f5c1aa3a4c4db3bc1723adbb551ea2395'),
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@unittest.skipUnless(os.environ.get('CRAFT_ASR_FIRST_USE') == '1',
                     'requires macOS arm64, spoken fixture, pinned model download and retained output')
class NativeAsrFirstUseTests(unittest.TestCase):
    def test_single_skill_downloads_recognizes_reopens_and_exports_captions(self):
        output = Path(os.environ['CRAFT_ASR_OUTPUT']).resolve()
        output.mkdir(parents=True, exist_ok=False)
        skill = output / '.agents/skills/filmcraft-cli-transcript'
        shutil.copytree(SKILLS / skill.name, skill, ignore=shutil.ignore_patterns('__pycache__'))
        runtime, data = output / 'fresh-runtime', output / 'declared-data'
        candidate = os.environ.get('CRAFT_ASR_CANDIDATE_DIRECTORY')
        archive = None
        if candidate:
            # 只修改测试副本；本地候选验收不能冒充公开下载或固定安装快照验收。
            receipt = json.loads((Path(candidate) / 'build-receipt.json').read_text())
            archive = Path(candidate).resolve() / receipt['archive']
            lock_path = skill / 'scripts/runtime.lock.json'
            lock = json.loads(lock_path.read_text())
            lock['resolvedVersion'] = receipt['runtimeVersion']
            lock['releaseRef'] = 'runtime-v' + receipt['runtimeVersion']
            entry = lock['artifacts']['darwin-arm64']
            entry.update({key: receipt[key] for key in
                          ['archiveSha256', 'binarySha256', 'provenanceSha256', 'versionOutput']})
            entry['url'] = lock['repository'] + '/releases/download/' + lock['releaseRef'] + '/' + receipt['archive']
            lock_path.write_text(json.dumps(lock, indent=2) + '\n')
        lock = json.loads((skill / 'scripts/runtime.lock.json').read_text())
        environment = dict(os.environ, PATH='/usr/bin:/bin')
        for key in ['FILMCRAFT_DATA_DIR', 'CRAFT_RUNTIME_HOME', 'CRAFT_NATIVE_ARCHIVE_DIRECTORY']:
            environment.pop(key, None)
        calls = []

        def cli(*arguments):
            prefix = [sys.executable, '-I', '-B', str(skill / 'scripts/cli.py'), '--runtime-home', str(runtime)]
            if archive:
                prefix += ['--archive', str(archive)]
            result = subprocess.run(prefix + ['--', *map(str, arguments), '--data-dir', str(data)],
                                    env=environment, capture_output=True, text=True, timeout=1500)
            log = output / ('call-%02d.log' % len(calls))
            log.write_text(result.stdout + result.stderr)
            calls.append({'operation': str(arguments[0]), 'exitCode': result.returncode,
                          'logSha256': digest(log)})
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return json.loads(result.stdout)

        models = cli('exec', 'transcript.models')
        self.assertTrue(models['available'], 'fixed native runtime must include real Whisper')
        self.assertEqual(Path(models['dir']), data / 'models')
        tiny = next(model for model in models['models'] if model['id'] == 'whisper-tiny')
        self.assertFalse(tiny['installed'])
        self.assertEqual(tiny['size'], sum(size for size, _ in MODEL_FILES.values()))
        cli('exec', 'transcript.downloadModel', json.dumps({'model': 'whisper-tiny'}))
        weights = data / 'models/whisper-tiny'
        for name, (size, checksum) in MODEL_FILES.items():
            self.assertEqual((weights / name).stat().st_size, size)
            self.assertEqual(digest(weights / name), checksum)
        mtimes = {name: (weights / name).stat().st_mtime_ns for name in MODEL_FILES}
        cli('exec', 'transcript.downloadModel', json.dumps({'model': 'whisper-tiny'}))
        self.assertEqual(mtimes, {name: (weights / name).stat().st_mtime_ns for name in MODEL_FILES})

        voice, shot = output / 'voice.wav', output / 'shot.mp4'
        speech = output / 'speech.aiff'
        subprocess.run(['/usr/bin/say', '-v', 'Samantha', '-r', '155', '-o', str(speech), REFERENCE], check=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-i', str(speech), '-ar', '48000', '-ac', '1',
                        '-c:a', 'pcm_s16le', str(voice)], check=True)
        duration = float(json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
                         'format=duration', '-of', 'json', str(voice)]))['format']['duration'])
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                        'color=c=red:s=320x180:r=12:d=' + str(duration), '-c:v', 'libx264',
                        '-pix_fmt', 'yuv420p', str(shot)], check=True)
        spec = importlib.util.spec_from_file_location('asr_fixture_workflow', skill / 'scripts/workflow.py')
        workflow = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(workflow)
        plan = json.loads((skill / 'examples/short-film.json').read_text())
        plan['assets'] = {key: {'path': str(path), 'sha256': digest(path)}
                          for key, path in [('voice', voice), ('shot', shot)]}
        for operation in plan['operations']:
            if operation['command'] == 'timeline.place':
                operation['params']['duration'] = str(int(duration * 12) * TICKS // 12)
        plan['frames'] = [str(TICKS // 2)]
        delivered = workflow.execute(plan, output / 'base', runtime_home=runtime)
        project = output / 'base/project.fcproj'
        before = digest(project)
        baseline = cli('inspect', '--project', project)
        target, captioned = output / 'recognized.fcproj', output / 'captioned.fcproj'
        result = cli('exec', 'transcript.generate', json.dumps({'model': 'whisper-tiny', 'language': 'en',
                     'items': [delivered['bindings']['voice']['item']]}), '--project', project, '--save-as', target)
        self.assertNotEqual(result['items'][0]['source'], 'fixed')
        transcript = cli('exec', 'transcript.inspect', '--project', target)
        words = transcript['words']
        self.assertGreaterEqual(len(words), 15)
        text = ' '.join(word['text'] for word in words)
        reference_words = set(re.findall('[a-z]+', REFERENCE.lower()))
        coverage = len(reference_words & set(re.findall('[a-z]+', text.lower()))) / len(reference_words)
        self.assertGreaterEqual(coverage, .8, text)
        for word in words:
            self.assertTrue(0 <= int(word['start']) < int(word['end']) <= int(duration * TICKS))
        cli('exec', 'transcript.createCaptions', json.dumps({'name': 'Recognized speech', 'maxChars': 42}),
            '--project', target, '--save-as', captioned)
        reopened = cli('inspect', '--project', captioned)
        for track in ['audio', 'video']:
            self.assertEqual(reopened['sequence'][track], baseline['sequence'][track])
        self.assertEqual(digest(project), before)
        srt = output / 'recognized.srt'
        cli('exec', 'captions.export', json.dumps({'path': str(srt), 'format': 'srt'}), '--project', captioned)
        for word in ['studio', 'captions']:
            self.assertIn(word, srt.read_text().lower())
        # 公共工作流从同一首次下载目录识别；验证显式目录优先于环境变量。
        revision = {'expectedProjectSha256': before, 'operations': [
            {'command': 'native.command', 'params': {'command': 'transcript.models', 'params': {}}, 'as': 'models'},
            {'command': 'native.command', 'params': {'command': 'transcript.generate', 'params': {
                'model': 'whisper-tiny', 'language': 'en', 'items': [delivered['bindings']['voice']['item']]}}, 'as': 'recognized'},
            {'command': 'native.command', 'params': {'command': 'transcript.inspect', 'params': {}}, 'as': 'transcript'},
            {'command': 'native.command', 'params': {'command': 'transcript.createCaptions', 'params': {
                'name': 'Workflow speech', 'maxChars': 42}}}], 'frames': [str(TICKS // 2)], 'export': {'audioRequired': True}}
        from unittest.mock import patch
        wrong = output / 'unused-environment-data'
        with patch.dict(os.environ, {'FILMCRAFT_DATA_DIR': str(wrong)}):
            workflow_delivery = workflow.execute(revision, output / 'workflow-asr', runtime_home=runtime,
                                                  source=output / 'base', data_dir=data)
        self.assertEqual(Path(workflow_delivery['bindings']['models']['dir']), data / 'models')
        self.assertFalse(wrong.exists())
        self.assertGreaterEqual(len(workflow_delivery['bindings']['transcript']['words']), 15)
        self.assertNotEqual(workflow_delivery['bindings']['recognized']['items'][0]['source'], 'fixed')
        workflow_native = json.loads((output / 'workflow-asr/native.json').read_text())
        for track in ['audio', 'video']:
            self.assertEqual(workflow_native['sequence'][track], workflow.precise(baseline['sequence'][track]))
        self.assertEqual(digest(project), before)
        for word in ['studio', 'captions']:
            self.assertIn(word, (output / 'workflow-asr/captions.srt').read_text().lower())
        workflow_proof = {'modelsDirCorrect': True, 'environmentOverrideUnused': True,
                          'wordCount': len(workflow_delivery['bindings']['transcript']['words']),
                          'sourcePreserved': True, 'audioVideoPreserved': True,
                          'files': {name: digest(output / 'workflow-asr' / name)
                                    for name in ['project.fcproj', 'captions.srt', 'film.mp4']}}
        binary = runtime / 'filmcraft' / lock['resolvedVersion'] / 'filmcraft-cli'
        proof = {'schema': 'filmcraft-single-skill-real-asr-first-use/v1', 'result': 'PASS',
                 'installation': 'local candidate archive' if candidate else 'public fixed runtime',
                 'nativeBinarySha256': digest(binary), 'runtimeVersion': lock['resolvedVersion'],
                 'skillFiles': {str(p.relative_to(skill)): digest(p) for p in sorted(skill.rglob('*'))
                                if p.is_file()}, 'inputSpeechSha256': digest(voice),
                 'sourceProjectSha256': before, 'sourcePreserved': True, 'audioVideoPreserved': True,
                 'workflowAsr': workflow_proof, 'wordCount': len(words), 'recognizedText': text, 'referenceWordCoverage': coverage,
                 'modelFiles': {name: checksum for name, (_, checksum) in MODEL_FILES.items()},
                 'outputSha256': {p.name: digest(p) for p in [target, captioned, srt]}, 'calls': calls,
                 'scope': 'Actual speech recognition, native reopening and SRT in one isolated skill; '
                          'fixed plugin/Art and general creative quality remain separate.'}
        (output / 'proof.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n')
