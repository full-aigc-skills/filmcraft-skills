"""独立音频技能首次安装、静态增益另存及实际成片音频验收。"""
import array
import copy
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get('CRAFT_AUDIO_SUBFRAME_FIRST_USE') == '1', 'requires public runtime and existing ffmpeg')
class AudioSubframeFirstUseTests(unittest.TestCase):
    def test_gain_revision_attenuates_decoded_audio_and_preserves_source(self):
        source = Path(os.environ.get('CRAFT_INSTALLED_AUDIO_SKILL_ROOT', ROOT / 'skills/filmcraft-cli-audio'))
        with tempfile.TemporaryDirectory(prefix='filmcraft-subframe-') as temporary:
            root = Path(temporary)
            skill = root / '.agents/skills/filmcraft-cli-audio'
            shutil.copytree(source, skill, ignore=shutil.ignore_patterns('__pycache__'))
            spec = importlib.util.spec_from_file_location('gain_workflow', skill / 'scripts/workflow.py')
            workflow = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(workflow)
            skill_hashes = {str(p.relative_to(skill)): workflow.sha(p) for p in skill.rglob('*') if p.is_file()}
            shot, voice = root / 'shot.mp4', root / 'voice.wav'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=red:s=320x180:r=12:d=3', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(shot)], check=True)
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=2.211333333333333:sample_rate=48000', '-c:a', 'pcm_s16le', str(voice)], check=True)
            plan = json.loads((skill / 'examples/short-film.json').read_text())
            plan['assets'] = {name: {'path': str(path), 'sha256': workflow.sha(path)} for name, path in [('shot', shot), ('voice', voice)]}
            for operation in plan['operations']:
                if operation['command'] == 'timeline.place':
                    if operation['params']['track'] == 'A1':
                        operation['params'].pop('duration')
                    else:
                        operation['params']['duration'] = '762048000000'
            runtime, first, second = root / 'empty-runtime', root / 'first', root / 'second'
            self.assertFalse(runtime.exists())
            initial = workflow.execute(plan, first, runtime_home=runtime)
            source_hashes = {str(p.relative_to(first)): workflow.sha(p) for p in first.rglob('*') if p.is_file()}
            revision = {'expectedProjectSha256': initial['files']['project.fcproj'], 'assets': {}, 'operations': [{'command': 'mixer.setStrip', 'params': {'strip': 'A1', 'volumeDb': -6.0}}], 'export': {'audioRequired': True}}
            result = workflow.execute(revision, second, runtime_home=runtime, source=first)
            before = json.loads((first / 'native.json').read_text())['sequence']
            after = json.loads((second / 'native.json').read_text())['sequence']
            self.assertEqual(before['video'], after['video'])
            self.assertEqual(before['audio'], after['audio'])
            self.assertEqual((first / 'captions.json').read_bytes(), (second / 'captions.json').read_bytes())
            def rms(path):
                raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0', '-ar', '48000', '-ac', '1', '-f', 'f32le', '-'])
                samples = array.array('f', raw)
                if sys.byteorder != 'little':
                    samples.byteswap()
                selected = samples[104160:105600]
                self.assertEqual(len(selected), 1440)
                return math.sqrt(sum(x*x for x in selected) / len(selected))
            tail_rms = rms(first / 'film.mp4')
            self.assertGreater(tail_rms, .02, 'full source audio tail must survive frame alignment')
            ratio = rms(second / 'film.mp4') / rms(first / 'film.mp4')
            self.assertAlmostEqual(ratio, 10 ** (-6 / 20), delta=.025)
            oversized = copy.deepcopy(plan)
            for operation in oversized['operations']:
                if operation['command'] == 'timeline.place' and operation['params']['track'] == 'A1':
                    operation['params']['duration'] = '762048000000'
            with self.assertRaisesRegex(ValueError, 'clip_out_of_range'):
                workflow.execute(oversized, root / 'invalid', runtime_home=runtime)
            self.assertFalse((root / 'invalid' / 'manifest.json').exists())
            for name, digest in source_hashes.items():
                self.assertEqual(workflow.sha(first / name), digest)
            for name, digest in skill_hashes.items():
                self.assertEqual(workflow.sha(skill / name), digest)
            self.assertFalse(list(skill.rglob('*.pyc')))
            if os.environ.get('CRAFT_AUDIO_SUBFRAME_EVIDENCE'):
                with Path(os.environ['CRAFT_AUDIO_SUBFRAME_EVIDENCE']).open('x') as stream:
                    json.dump({'schema': 'filmcraft-audio-subframe-first-use/v1', 'scope': 'single copied audio skill; empty public runtime installation; synthetic existing audio; static A1 gain only; no creative or GUI acceptance', 'sourceDurationSeconds': 2.211333333333333, 'decodedTailWindowSeconds': [2.17, 2.20], 'decodedTailRms': tail_rms, 'oversizedExplicitRangeRejected': True, 'gainDb': -6, 'decodedRmsRatio': ratio, 'expectedRatio': 10 ** (-6 / 20), 'runtimeSha256': result['runtimeSha256'], 'sourcePreserved': True, 'videoAudioClipIdentityPreserved': True, 'captionsPreserved': True, 'skillFilesPreserved': True, 'initialProjectSha256': initial['files']['project.fcproj'], 'revisedFiles': result['files']}, stream, indent=2)
