"""用三种可分离频率核验独立音轨、局部增益及实际原生混音。"""
import array
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


@unittest.skipUnless(os.environ.get('CRAFT_MULTITRACK_AUDIO_FIRST_USE') == '1', 'requires public native runtime and ffmpeg')
class MultitrackAudioFirstUseTests(unittest.TestCase):
    def test_music_gain_preserves_voice_original_audio_and_native_project(self):
        source = Path(os.environ.get('CRAFT_INSTALLED_MULTITRACK_SKILL_ROOT', ROOT / 'skills/filmcraft-cli-audio'))
        with tempfile.TemporaryDirectory(prefix='filmcraft-multitrack-') as temporary:
            root = Path(temporary)
            skill = root / '.agents/skills/filmcraft-cli-audio'
            shutil.copytree(source, skill, ignore=shutil.ignore_patterns('__pycache__'))
            spec = importlib.util.spec_from_file_location('multitrack_workflow', skill / 'scripts/workflow.py')
            workflow = importlib.util.module_from_spec(spec); spec.loader.exec_module(workflow)
            hashes = {str(p.relative_to(skill)): workflow.sha(p) for p in skill.rglob('*') if p.is_file()}
            shot, voice, music = root / 'shot.mp4', root / 'voice.wav', root / 'music.wav'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=red:s=320x180:r=12:d=2', '-f', 'lavfi', '-i', 'sine=frequency=1200:duration=2:sample_rate=48000', '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', str(shot)], check=True)
            for path, frequency in [(voice, 400), (music, 800)]:
                subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', f'sine=frequency={frequency}:duration=2:sample_rate=48000', '-c:a', 'pcm_s16le', str(path)], check=True)
            plan = json.loads((skill / 'examples/short-film.json').read_text())
            plan['assets'] = {name: {'path': str(path), 'sha256': workflow.sha(path)} for name, path in [('shot', shot), ('voice', voice), ('music', music)]}
            plan['operations'][2]['params']['audioTrack'] = 'A3'
            # 不同起点同时检验同步，选取三音轨同时存在的稳定窗口分析。
            plan['operations'][3]['params'].update(time=str(workflow.TICKS // 4), duration=str(7 * workflow.TICKS // 4))
            plan['operations'].insert(4, {'command': 'asset.import', 'params': {'asset': 'music'}, 'as': 'music'})
            plan['operations'].insert(5, {'command': 'timeline.place', 'params': {'item': {'$ref': 'music.item'}, 'track': 'A2', 'audioTrack': 'A2', 'time': str(workflow.TICKS // 2), 'duration': str(3 * workflow.TICKS // 2), 'sourceIn': '0', 'insert': False}, 'as': 'musicClip'})
            plan['operations'] += [{'command': 'mixer.setStrip', 'params': {'strip': track, 'volumeDb': gain}} for track, gain in [('A1', -3), ('A2', -9), ('A3', -15)]]
            runtime, first, second = root / 'empty-runtime', root / 'first', root / 'second'
            self.assertFalse(runtime.exists())
            initial = workflow.execute(plan, first, runtime_home=runtime)
            originals = {str(p.relative_to(first)): workflow.sha(p) for p in first.rglob('*') if p.is_file()}
            revision = {'expectedProjectSha256': initial['files']['project.fcproj'], 'assets': {}, 'operations': [{'command': 'mixer.setStrip', 'params': {'strip': 'A2', 'volumeDb': -15}}], 'frames': ['127008000000'], 'export': {'audioRequired': True}}
            result = workflow.execute(revision, second, runtime_home=runtime, source=first)
            before = json.loads((first / 'native.json').read_text())['sequence']
            after = json.loads((second / 'native.json').read_text())['sequence']
            self.assertEqual(before, after)
            active_tracks = [track for track in before['audio'] if track['items']]
            self.assertEqual(len(active_tracks), 3)
            self.assertEqual({item['item'] for track in active_tracks for item in track['items']}, {initial['assets'][alias]['item'] for alias in ('shot', 'voice', 'music')})
            by_item = {item['item']: item for track in active_tracks for item in track['items']}
            for alias, start, duration in [('shot', 0, 2*workflow.TICKS), ('voice', workflow.TICKS//4, 7*workflow.TICKS//4), ('music', workflow.TICKS//2, 3*workflow.TICKS//2)]:
                item = by_item[initial['assets'][alias]['item']]
                self.assertEqual((str(item['start']), str(item['sourceIn']), str(item['duration'])), (str(start), '0', str(duration)))
            self.assertEqual((first / 'captions.json').read_bytes(), (second / 'captions.json').read_bytes())
            self.assertEqual((first / 'frame-0000.png').read_bytes(), (second / 'frame-0000.png').read_bytes())
            def amplitudes(path, start=.75, end=1.5):
                raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0', '-ar', '48000', '-ac', '1', '-f', 'f32le', '-'])
                samples = array.array('f', raw)
                if sys.byteorder != 'little': samples.byteswap()
                selected = samples[round(start*48000):round(end*48000)]
                self.assertEqual(len(selected), round((end-start)*48000))
                return {str(f): 2*math.hypot(sum(x*math.sin(2*math.pi*f*i/48000) for i,x in enumerate(selected)), sum(x*math.cos(2*math.pi*f*i/48000) for i,x in enumerate(selected)))/len(selected) for f in (400, 800, 1200)}
            old_amplitude, new_amplitude = amplitudes(first / 'film.mp4'), amplitudes(second / 'film.mp4')
            for amplitude in old_amplitude.values(): self.assertGreater(amplitude, .005)
            # 同幅输入的频率分量比例同时验证首次设置的三种独立增益。
            self.assertAlmostEqual(old_amplitude['800']/old_amplitude['400'], 10 ** (-6/20), delta=.025)
            self.assertAlmostEqual(old_amplitude['1200']/old_amplitude['400'], 10 ** (-12/20), delta=.025)
            ratios = {f: new_amplitude[f]/old_amplitude[f] for f in old_amplitude}
            self.assertAlmostEqual(ratios['800'], 10 ** (-6/20), delta=.025)
            for f in ('400', '1200'): self.assertAlmostEqual(ratios[f], 1, delta=.03)
            early = amplitudes(first / 'film.mp4', .05, .20)
            self.assertLess(early['400'], old_amplitude['400']*.03)
            self.assertLess(early['800'], old_amplitude['800']*.03)
            self.assertGreater(early['1200'], old_amplitude['1200']*.90)
            for name, sha in originals.items(): self.assertEqual(workflow.sha(first / name), sha)
            for name, sha in hashes.items(): self.assertEqual(workflow.sha(skill / name), sha)
            self.assertFalse(list(skill.rglob('*.pyc')))
            if os.environ.get('CRAFT_MULTITRACK_AUDIO_EVIDENCE'):
                proof = {'schema': 'filmcraft-multitrack-audio-first-use/v1', 'scope': 'single copied installed audio skill; public empty runtime install; three synthetic source tones including embedded source-video audio; static A2 gain revision only', 'initialGainDb': {'A1': -3, 'A2': -9, 'A3': -15}, 'revisedGainDb': {'A2': -15}, 'frequenciesHz': {'voice': 400, 'music': 800, 'original': 1200}, 'decodedInitialAmplitudes': old_amplitude, 'decodedRevisedAmplitudes': new_amplitude, 'decodedAmplitudeRatios': ratios, 'earlyAmplitudes': early, 'runtimeSha256': result['runtimeSha256'], 'nativeSequence': before, 'initialProjectSha256': initial['files']['project.fcproj'], 'revisedFiles': result['files'], 'originalDeliveryPreserved': True, 'nativeClipIdentitiesAndTimingPreserved': True, 'captionsAndPreviewPreserved': True, 'skillFilesPreserved': True}
                with Path(os.environ['CRAFT_MULTITRACK_AUDIO_EVIDENCE']).open('x') as stream: json.dump(proof, stream, indent=2)
