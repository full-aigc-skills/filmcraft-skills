"""八类场景技能的独立首次安装与真实 CLI 操作；不把命令目录当业务验收。"""
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
TICKS = 254016000000


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@unittest.skipUnless(os.environ.get('CRAFT_TASK_FIRST_USE') == '1',
                     'requires macOS arm64, public archives, ffmpeg, ffprobe and Pillow')
class TaskSkillFirstUseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 基础工程是用户已有工程的测试替身。场景执行时只安装当前一个技能。
        cls.fixture_directory = tempfile.TemporaryDirectory(prefix='filmcraft-task-fixture-')
        cls.fixture = Path(cls.fixture_directory.name)
        source = ROOT / 'skills/filmcraft-use'
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
        executable = cls.fixture / 'fixture-runtime/filmcraft/0.2.0/filmcraft-cli'
        cls.native = json.loads(subprocess.check_output([
            str(executable), 'inspect', '--project', str(cls.project),
            '--data-dir', str(cls.fixture / 'fixture-data')]))

    @classmethod
    def tearDownClass(cls):
        cls.fixture_directory.cleanup()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='filmcraft-task-single-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.runtime = self.root / 'fresh-runtime'
        self.data = self.root / 'isolated-data'
        self.environment = dict(os.environ, PATH='/usr/bin:/bin')
        self.addCleanup(lambda: self.assertEqual(digest(self.project), self.project_sha))

    def install_only(self, task):
        self.skill_name = 'filmcraft-cli-' + task
        self.skill = self.root / 'single-skill'
        shutil.copytree(ROOT / 'skills' / self.skill_name, self.skill,
                        ignore=shutil.ignore_patterns('__pycache__'))
        self.assertFalse(self.runtime.exists())

    def cli(self, *arguments, success=True):
        result = subprocess.run([sys.executable, '-I', '-B', str(self.skill / 'scripts/cli.py'),
                                 '--runtime-home', str(self.runtime), '--', *map(str, arguments),
                                 '--data-dir', str(self.data)], env=self.environment,
                                capture_output=True, text=True, timeout=240)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((self.runtime / 'filmcraft/0.2.0/filmcraft-cli').is_file())
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
