"""全部十三技能的独立首次安装与真实业务操作；不把命令目录当业务验收。"""
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import wave

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SKILLS = Path(os.environ.get('CRAFT_INSTALLED_TASK_SKILLS_ROOT', ROOT / 'skills')).resolve()
TICKS = 254016000000


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@unittest.skipUnless(os.environ.get('CRAFT_TASK_FIRST_USE') == '1',
                     'requires macOS arm64, public archives, ffmpeg, ffprobe and Pillow')
class TaskSkillFirstUseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 基础工程是用户已有工程的测试替身。场景执行时只安装当前一个技能。
        cls.evidence = []
        cls.fixture_directory = tempfile.TemporaryDirectory(prefix='filmcraft-task-fixture-')
        cls.fixture = Path(cls.fixture_directory.name)
        source = SKILLS / 'filmcraft-use'
        cls.runtime_version=json.loads((source/'scripts/runtime.lock.json').read_text())['resolvedVersion']
        spec = importlib.util.spec_from_file_location('first_use_fixture', source / 'scripts/workflow.py')
        workflow = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(workflow)
        shot, voice = cls.fixture / 'red.mp4', cls.fixture / 'voice.wav'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                        'color=c=red:s=320x180:r=12:d=2', '-c:v', 'libx264',
                        '-pix_fmt', 'yuv420p', str(shot)], check=True)
        with wave.open(str(voice), 'wb') as stream:
            stream.setparams((1, 2, 48000, 96000, 'NONE', 'not compressed'))
            stream.writeframes(b''.join(struct.pack('<h', int(5000 * math.sin(n * 2 * math.pi * 440 / 48000)))
                                       for n in range(96000)))
        plan = json.loads((source / 'examples/short-film.json').read_text())
        plan['assets'] = {key: {'path': str(path), 'sha256': digest(path)}
                          for key, path in [('shot', shot), ('voice', voice)]}
        cls.base = cls.fixture / 'base'
        delivered = workflow.execute(plan, cls.base, runtime_home=cls.fixture / 'fixture-runtime')
        cls.bindings = delivered['bindings']
        cls.project = cls.base / 'project.fcproj'
        cls.project_sha = digest(cls.project)
        # 原生 CLI 返回整数时间；工作流交付 JSON 将其转成十进制字符串。
        # 保留原生基线比较原生结果，避免把表示差异误判为轨道被修改。
        executable = cls.fixture / 'fixture-runtime/filmcraft' / cls.runtime_version / 'filmcraft-cli'
        cls.native = json.loads(subprocess.check_output([
            str(executable), 'inspect', '--project', str(cls.project),
            '--data-dir', str(cls.fixture / 'fixture-data')]))

    @classmethod
    def tearDownClass(cls):
        try:
            if os.environ.get('CRAFT_TASK_EVIDENCE_FILE'):
                path = Path(os.environ['CRAFT_TASK_EVIDENCE_FILE'])
                with path.open('x', encoding='utf-8') as output:
                    json.dump({'schema': 'craft-native-task-observations/v1', 'runtimeVersion': cls.runtime_version, 'observations': cls.evidence}, output, ensure_ascii=False, indent=2)
                    output.write('\n')
        finally:
            cls.fixture_directory.cleanup()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='filmcraft-task-single-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.runtime = self.root / 'fresh-runtime'
        self.data = self.root / 'isolated-data'
        self.environment = dict(os.environ, PATH='/usr/bin:/bin')
        self.addCleanup(lambda: self.assertEqual(digest(self.project), self.project_sha))

    def tearDown(self):
        # 只记录合成 fixture 和派生产物摘要；成功状态由 unittest 的真实结果提供。
        if os.environ.get('CRAFT_TASK_EVIDENCE_FILE') and hasattr(self, 'skill'):
            executable = self.runtime / 'filmcraft' / self.runtime_version / 'filmcraft-cli'
            self.evidence.append({
                'test': self._testMethodName,
                'skill': self.skill_name,
                'sourceProjectSha256': self.project_sha,
                'inputSha256': {name: digest(self.fixture / name) for name in ['red.mp4', 'voice.wav']},
                'nativeBinarySha256': digest(executable) if executable.is_file() else None,
                'outputSha256': {str(p.relative_to(self.root)): digest(p) for p in sorted(self.root.rglob('*'))
                                 if p.is_file() and not any(p.is_relative_to(directory) for directory in
                                     [self.runtime, self.data, self.skill])},
            })

    def install_only(self, task):
        self.skill_name = task if task in ('filmcraft-use', 'filmcraft-cli', 'filmcraft-cli-setup') else 'filmcraft-cli-' + task
        self.skill = self.root / 'single-skill'
        shutil.copytree(SKILLS / self.skill_name, self.skill,
                        ignore=shutil.ignore_patterns('__pycache__'))
        self.assertFalse(self.runtime.exists())

    def cli(self, *arguments, success=True):
        result = subprocess.run([sys.executable, '-I', '-B', str(self.skill / 'scripts/cli.py'),
                                 '--runtime-home', str(self.runtime), '--', *map(str, arguments),
                                 '--data-dir', str(self.data)], env=self.environment,
                                capture_output=True, text=True, timeout=240)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((self.runtime / 'filmcraft' / self.runtime_version / 'filmcraft-cli').is_file())
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def execute(self, command, params, target):
        # 参数来源和实时 enabled 状态来自当前技能目录与已打开工程。
        catalog = json.loads((self.skill / 'references/commands.json').read_text())
        self.assertIn(command, {entry['id'] for entry in catalog['commands']})
        described = json.loads(self.cli('describe', command, '--project', self.project).stdout)
        self.assertTrue(described['enabled'], command)
        result = self.cli('exec', command, json.dumps(params), '--project', self.project,
                          '--save-as', target)
        self.assertTrue(target.is_file())
        return json.loads(result.stdout)

    def inspect(self, project):
        return json.loads(self.cli('inspect', '--project', project).stdout)

    def public_plan(self, entry, plan, output, source=None):
        path = self.root / (output.name + '-plan.json')
        path.write_text(json.dumps(plan))
        argv = [sys.executable, '-I', '-B', str(self.skill / 'scripts' / (entry + '.py'))]
        if entry != 'workflow':
            argv.append('run')
        argv += [str(path), '--output', str(output), '--runtime-home', str(self.runtime),
                 '--read-root', str(self.root.resolve()), '--read-root', str(self.fixture.resolve()),
                 '--write-root', str(self.root.resolve())]
        if source is not None:
            argv += ['--source', str(source)]
        result = subprocess.run(argv, env=self.environment, capture_output=True, text=True, timeout=240)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_use_routes_composed_film_and_revises_only_requested_caption(self):
        self.install_only('filmcraft-use')
        plan = json.loads((self.skill / 'examples/short-film.json').read_text())
        plan['assets'] = {name: {'path': str(self.fixture / filename),
                                'sha256': digest(self.fixture / filename)}
                          for name, filename in [('shot', 'red.mp4'), ('voice', 'voice.wav')]}
        original = self.root / 'composed'; made = self.public_plan('workflow', plan, original)
        original_hash = digest(original / 'project.fcproj')
        before = self.inspect(original / 'project.fcproj')['sequence']
        captions_before = json.loads(self.cli('exec', 'captions.list', '--project', original / 'project.fcproj').stdout)
        revised = self.root / 'revised'
        revision = {'expectedProjectSha256': original_hash,
                    'operations': [{'command': 'captions.setText',
                                    'params': {'caption': {'$ref': 'caption.caption'},
                                               'text': 'Only requested caption'}}],
                    'frames': ['127008000000'], 'export': {'audioRequired': True}}
        self.public_plan('workflow', revision, revised, source=original)
        after = self.inspect(revised / 'project.fcproj')['sequence']
        self.assertEqual(before['video'], after['video'])
        self.assertEqual(before['audio'], after['audio'])
        expected_captions = json.loads(json.dumps(captions_before))
        target_caption = made['bindings']['caption']['caption']
        changed = 0
        for track in expected_captions['tracks']:
            for caption in track['captions']:
                if caption['id'] == target_caption:
                    caption['text'] = 'Only requested caption'; changed += 1
        self.assertEqual(changed, 1)
        captions_after = json.loads(self.cli('exec', 'captions.list', '--project', revised / 'project.fcproj').stdout)
        self.assertEqual(captions_after, expected_captions)
        self.assertEqual(digest(original / 'project.fcproj'), original_hash)
        self.assertIn('Only requested caption', (revised / 'captions.srt').read_text())
        self.assertIn('First scene', (original / 'captions.srt').read_text())
        self.assertTrue(made['runtimeSha256'])

    def test_cli_executes_explicit_native_plan_and_reopens_unchanged_sequence(self):
        self.install_only('filmcraft-cli')
        plan = json.loads((self.skill / 'examples/commands-advanced.json').read_text())
        plan['operations'] += [
            {'command': 'file.open', 'params': {'path': {'$output': 'project.fcproj'}}},
            {'command': 'sequence.inspect', 'params': {}, 'as': 'reopened'}]
        made = self.public_plan('commands', plan, self.root / 'native-plan')
        inspections = [row['result'] for row in made['steps'] if row.get('command') == 'sequence.inspect']
        self.assertEqual(len(inspections), 2)
        # 现有合同明确重开不恢复界面选择；只比较原生持久工程内容。
        self.assertTrue(inspections[0]['selection'])
        self.assertEqual(inspections[1]['selection'], [])
        self.assertEqual({k: v for k, v in inspections[0].items() if k != 'selection'},
                         {k: v for k, v in inspections[1].items() if k != 'selection'})
        self.assertEqual(made['result'], 'PASS')
        self.assertGreater(len(made['steps']), 10)

    def test_setup_verifies_pinned_install_and_refuses_owned_corrupt_copy(self):
        self.install_only('filmcraft-cli-setup')
        self.assertIn(self.runtime_version, self.cli('--version').stdout)
        executable = self.runtime / 'filmcraft' / self.runtime_version / 'filmcraft-cli'
        lock = json.loads((self.skill / 'scripts/runtime.lock.json').read_text())
        self.assertEqual(digest(executable), lock['artifacts']['darwin-arm64']['binarySha256'])
        # 只破坏本用例拥有的独立缓存，不改共享运行时或用户安装。
        payload = bytearray(executable.read_bytes()); payload[-1] ^= 1; executable.write_bytes(payload)
        changed = digest(executable)
        refused = self.cli('--version', success=False)
        diagnostic = json.loads(refused.stdout)
        self.assertIn('filmcraft-cli-setup', json.dumps(diagnostic))
        self.assertEqual(digest(executable), changed)

    def test_project_creates_and_reopens_sequence_and_bin(self):
        self.install_only('project')
        # 官方 save-as 按文件名更新项目名，文件名与需求名保持一致。
        target, script = self.root / 'Independent project.fcproj', self.root / 'create.jsonl'
        script.write_text('\n'.join(json.dumps(row) for row in [
            {'id': 'file.newProject', 'params': {'name': 'Independent project'}},
            {'id': 'file.newSequence', 'params': {'name': 'Main', 'width': 320, 'height': 180, 'fps': 12}},
            {'id': 'file.newBin', 'params': {'name': 'Footage'}}]) + '\n')
        result = self.cli('run', script, '--save-as', target)
        self.assertTrue(all(json.loads(line)['ok'] for line in result.stdout.splitlines()))
        reopened = self.inspect(target)
        self.assertEqual(reopened['project']['name'], 'Independent project')
        self.assertEqual(reopened['sequence']['name'], 'Main')
        self.assertEqual(reopened['sequence']['settings']['width'], 320)
        self.assertIn('Footage', [item['name'] for item in reopened['project']['root']['children']])

    def test_media_probes_imports_and_preserves_existing_timeline(self):
        self.install_only('media')
        extra = self.root / 'additional.mp4'
        shutil.copyfile(self.fixture / 'red.mp4', extra)
        probe = json.loads(self.cli('probe', extra).stdout)
        self.assertEqual((probe['video']['width'], probe['video']['height']), (320, 180))
        target = self.root / 'imported.fcproj'
        self.cli('import', extra, '--project', self.project, '--save-as', target)
        reopened = self.inspect(target)
        self.assertIn('additional.mp4', [item['name'] for item in reopened['project']['root']['children']])
        self.assertEqual(reopened['sequence'], self.native['sequence'])

    def test_timeline_razor_preserves_audio_and_duration(self):
        self.install_only('timeline')
        target = self.root / 'cut.fcproj'
        self.execute('timeline.razor', {'clip': self.bindings['shotClip']['clips'][0], 'time': TICKS}, target)
        sequence = self.inspect(target)['sequence']
        clips = sequence['video'][0]['items']
        self.assertEqual(len(clips), 2)
        self.assertEqual([(str(clip['start']), str(clip['duration'])) for clip in clips],
                         [('0', str(TICKS)), (str(TICKS), str(TICKS))])
        self.assertEqual(sequence['durationFrames'], 24)
        self.assertEqual(sequence['audio'], self.native['sequence']['audio'])
        rejected = self.root / 'invalid-command.fcproj'
        self.cli('exec', 'craft.nonexistent.command', '{}', '--project', self.project,
                 '--save-as', rejected, success=False)
        self.assertFalse(rejected.exists())

    def test_audio_gain_survives_reopen_and_changes_exported_samples(self):
        self.install_only('audio')
        target, output = self.root / 'audio.fcproj', self.root / 'quieter.wav'
        self.execute('mixer.setStrip', {'strip': 'A1', 'name': 'Narration', 'volumeDb': -6}, target)
        mixer = json.loads(self.cli('exec', 'mixer.inspect', '--project', target).stdout)
        strip = next(value for value in mixer['strips'] if value['ref'] == 'A1')
        self.assertEqual((strip['name'], strip['volumeDb']), ('Narration', -6.0))
        self.cli('export', output, '--format', 'wav', '--project', target)
        pcm = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(output),
                                       '-f', 's16le', '-ac', '1', '-ar', '48000', '-'])
        samples = struct.unpack('<' + str(len(pcm) // 2) + 'h', pcm)
        rms = math.sqrt(sum(value * value for value in samples[12000:84000]) / 72000)
        self.assertGreater(rms, 1500)
        self.assertLess(rms, 2100)
        self.assertEqual(self.inspect(target)['sequence']['video'], self.native['sequence']['video'])

    def test_subtitles_updates_text_without_changing_timing_and_exports_srt(self):
        self.install_only('subtitles')
        target, srt = self.root / 'captions.fcproj', self.root / 'captions.srt'
        self.execute('captions.setText', {'caption': self.bindings['caption']['caption'], 'text': 'Updated caption'}, target)
        captions = json.loads(self.cli('exec', 'captions.list', '--project', target).stdout)
        caption = captions['tracks'][0]['captions'][0]
        self.assertEqual((str(caption['start']), str(caption['end']), caption['text']),
                         ('0', str(TICKS), 'Updated caption'))
        self.cli('exec', 'captions.export', json.dumps({'path': str(srt), 'format': 'srt'}), '--project', target)
        self.assertIn('00:00:01,000', srt.read_text())
        self.assertIn('Updated caption', srt.read_text())
        self.assertEqual(self.inspect(target)['sequence']['video'], self.native['sequence']['video'])

    def test_color_lut_survives_source_removal_and_empty_library(self):
        from PIL import Image
        self.install_only('color')
        cube, target = self.root / 'swap.cube', self.root / 'color.fcproj'
        cube.write_text('TITLE "Swap red and green"\nLUT_3D_SIZE 2\n' +
                        ''.join(f'{g} {r} {b}\n' for b in range(2) for g in range(2) for r in range(2)))
        self.execute('lumetri.setInputLut', {'clip': self.bindings['shotClip']['clips'][0], 'path': str(cube)}, target)
        cube.unlink()
        # 原生工程内的 LUT 必须足够重开，不能偷偷依靠旧用户库。
        self.data = self.root / 'new-empty-library'
        frame = self.root / 'colored.png'
        self.cli('render', '--seconds', '1.5', '--out', frame, '--project', target)
        with Image.open(frame) as image:
            red, green, blue, *_ = image.getpixel((20, 20))
            self.assertGreater(green, 200)
            self.assertLess(red, 20)
        self.assertEqual(self.inspect(target)['sequence']['audio'], self.native['sequence']['audio'])

    def test_motion_keyframes_survive_reopen_and_change_rendered_frames(self):
        from PIL import Image, ImageChops
        self.install_only('motion')
        clip = self.bindings['shotClip']['clips'][0]
        target, script = self.root / 'motion.fcproj', self.root / 'motion.jsonl'
        rows = [
            {'id': 'effects.toggleAnimation', 'params': {'clip': clip, 'effect': 'motion', 'param': 'position'}},
            {'id': 'effects.setParam', 'params': {'clip': clip, 'effect': 'motion', 'param': 'position', 'value': [100, 90], 'time': 0}},
            {'id': 'effects.setParam', 'params': {'clip': clip, 'effect': 'motion', 'param': 'position', 'value': [200, 90], 'time': TICKS}}]
        script.write_text(''.join(json.dumps(row) + '\n' for row in rows))
        self.cli('run', script, '--project', self.project, '--save-as', target)
        sequence = self.inspect(target)['sequence']
        params = sequence['video'][0]['items'][0]['effects'][0]['params']
        self.assertEqual(params['position']['keyframes'], 2)
        before, after = self.root / 'before.png', self.root / 'after.png'
        for seconds, path in [('0', before), ('1.5', after)]:
            self.cli('render', '--seconds', seconds, '--out', path, '--project', target)
        with Image.open(before) as first, Image.open(after) as second:
            self.assertIsNotNone(ImageChops.difference(first.convert('RGB'), second.convert('RGB')).getbbox())
        self.assertEqual(sequence['audio'], self.native['sequence']['audio'])

    def test_transcript_import_reopens_and_generates_timed_captions(self):
        self.install_only('transcript')
        target = self.root / 'transcript.fcproj'
        transcript = {'language': 'en', 'speakers': [{'name': 'Narrator'}],
                      'words': [{'text': 'Hello', 'start': 0, 'end': TICKS // 2, 'speaker': 0},
                                {'text': 'world.', 'start': TICKS // 2, 'end': TICKS, 'speaker': 0}]}
        result = self.execute('transcript.set', {'item': self.bindings['voice']['item'],
                             'transcript': transcript}, target)
        self.assertEqual(result['words'], 2)
        inspected = json.loads(self.cli('exec', 'transcript.inspect', '--project', target).stdout)
        self.assertEqual([word['text'] for word in inspected['words']], ['Hello', 'world.'])
        self.assertEqual(int(inspected['words'][0]['start']), 0)
        self.assertEqual(int(inspected['words'][-1]['end']), TICKS)
        captioned = self.root / 'transcript-captions.fcproj'
        self.cli('exec', 'transcript.createCaptions',
                 json.dumps({'name': 'Transcript captions', 'maxChars': 32}),
                 '--project', target, '--save-as', captioned)
        captions = json.loads(self.cli('exec', 'captions.list', '--project', captioned).stdout)
        self.assertIn('Hello world.', [caption['text'] for track in captions['tracks']
                                      for caption in track['captions']])
        after = self.inspect(captioned)['sequence']
        self.assertEqual(after['video'], self.native['sequence']['video'])
        self.assertEqual(after['audio'], self.native['sequence']['audio'])
        srt = self.root / 'transcript.srt'
        self.cli('exec', 'captions.export', json.dumps({'path': str(srt), 'format': 'srt'}),
                 '--project', captioned)
        self.assertIn('Hello world.', srt.read_text())

    def test_multicam_switch_reopens_renders_other_camera_and_preserves_existing_tracks(self):
        from PIL import Image
        self.install_only('multicam')
        blue = self.root / 'camera-blue.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                        'color=c=blue:s=320x180:r=12:d=2', '-c:v', 'libx264',
                        '-pix_fmt', 'yuv420p', str(blue)], check=True)
        imported = self.root / 'cameras.fcproj'
        self.cli('import', blue, '--project', self.project, '--save-as', imported)
        camera = next(item['item'] for item in self.inspect(imported)['project']['root']['children']
                      if item['name'] == 'camera-blue.mp4')
        source = self.root / 'multicam-source.fcproj'
        script = self.root / 'multicam-create.jsonl'
        script.write_text('\n'.join(json.dumps(row) for row in [
            {'id': 'project.select', 'params': {'items': [self.bindings['shot']['item'], camera]}},
            {'id': 'clip.createMulticam', 'params': {'method': 'in', 'cameraNames': 'clip',
                                                   'audio': 'camera1'}}]) + '\n')
        result = self.cli('run', script, '--project', imported, '--save-as', source)
        created = json.loads(result.stdout.splitlines()[-1])['result']
        placed = self.root / 'multicam-placed.fcproj'
        clip = json.loads(self.cli('exec', 'timeline.place',
                         json.dumps({'item': created['sequence'], 'track': 'V1',
                                     'time': 2 * TICKS, 'sourceIn': 0,
                                     'duration': 2 * TICKS, 'insert': False}),
                         '--project', source, '--save-as', placed).stdout)['clips'][0]
        switched = self.root / 'multicam-switched.fcproj'
        self.cli('exec', 'multicam.switchAngle',
                 json.dumps({'clips': [clip], 'angle': 1, 'time': 5 * TICKS // 2,
                             'videoOnly': True}), '--project', placed, '--save-as', switched)
        after = self.inspect(switched)['sequence']
        self.assertEqual(after['video'][0]['items'][0], self.native['sequence']['video'][0]['items'][0])
        # 放置多机位源会附加其音轨；仅切换画面必须保全放置后的全部音频和原配音。
        self.assertEqual(after['audio'], self.inspect(placed)['sequence']['audio'])
        for original, current in zip(self.native['sequence']['audio'], after['audio']):
            self.assertEqual(current['items'][:len(original['items'])], original['items'])
            self.assertEqual({k: v for k, v in current.items() if k != 'items'},
                             {k: v for k, v in original.items() if k != 'items'})
        for project, name, channel in [(placed, 'camera-one.png', 0),
                                       (switched, 'camera-two.png', 2)]:
            image = self.root / name
            self.cli('render', '--seconds', 2.5, '--out', image, '--project', project)
            with Image.open(image) as frame:
                pixel = frame.convert('RGB').getpixel((160, 90))
                self.assertGreater(pixel[channel], 180)
                self.assertLess(pixel[2 if channel == 0 else 0], 30)

    def test_export_video_preview_and_interchange_keep_native_project(self):
        from PIL import Image
        self.install_only('export')
        video, preview, otio = self.root / 'film.mp4', self.root / 'preview.png', self.root / 'film.otio'
        self.cli('export', video, '--format', 'h264', '--project', self.project)
        streams = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames',
                                                      '-show_streams', '-of', 'json', str(video)]))['streams']
        track = next(stream for stream in streams if stream['codec_type'] == 'video')
        self.assertEqual((track['width'], track['height'], track['nb_read_frames']), (320, 180, '24'))
        self.assertTrue(any(stream['codec_type'] == 'audio' for stream in streams))
        self.cli('render', '--seconds', '1.5', '--out', preview, '--project', self.project)
        with Image.open(preview) as image:
            self.assertEqual(image.size, (320, 180))
        self.cli('exec', 'file.exportOtio', json.dumps({'path': str(otio)}), '--project', self.project)
        self.assertIn('OTIO_SCHEMA', json.loads(otio.read_text()))


if __name__ == '__main__':
    unittest.main()
