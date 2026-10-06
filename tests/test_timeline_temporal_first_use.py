"""用随时间改变颜色的素材验收源入点、普通裁切、移动与保全。"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
TICKS = 254016000000


@unittest.skipUnless(os.environ.get('CRAFT_TIMELINE_TEMPORAL_FIRST_USE') == '1', 'requires public native runtime and existing ffmpeg/ffprobe/Pillow')
class TimelineTemporalFirstUseTests(unittest.TestCase):
    def test_trim_and_move_preserve_other_clip_audio_captions_and_source(self):
        from PIL import Image
        source = Path(os.environ.get('CRAFT_INSTALLED_TIMELINE_SKILL_ROOT', ROOT / 'skills/filmcraft-cli-timeline'))
        with tempfile.TemporaryDirectory(prefix='filmcraft-temporal-') as temporary:
            root = Path(temporary)
            skill = root / '.agents/skills/filmcraft-cli-timeline'
            shutil.copytree(source, skill, ignore=shutil.ignore_patterns('__pycache__'))
            spec = importlib.util.spec_from_file_location('temporal_workflow', skill / 'scripts/workflow.py')
            workflow = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(workflow)
            shot, audio = root / 'colors.mp4', root / 'voice.wav'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=red:s=320x180:r=12:d=1', '-f', 'lavfi', '-i', 'color=green:s=320x180:r=12:d=1', '-f', 'lavfi', '-i', 'color=blue:s=320x180:r=12:d=1', '-filter_complex', '[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]', '-map', '[v]', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(shot)], check=True)
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=2', '-ar', '48000', '-ac', '1', '-c:a', 'pcm_s16le', str(audio)], check=True)
            plan = json.loads((skill / 'examples/short-film.json').read_text())
            plan['assets'] = {name: {'path': str(path), 'sha256': workflow.sha(path)} for name, path in [('shot', shot), ('voice', audio)]}
            plan['operations'][2]['params']['duration'] = str(3 * TICKS // 2)
            plan['operations'].insert(3, {'command': 'timeline.place', 'params': {'item': {'$ref': 'shot.item'}, 'track': 'V1', 'time': str(3 * TICKS // 2), 'sourceIn': str(5 * TICKS // 2), 'duration': str(TICKS // 2), 'insert': False}, 'as': 'otherClip'})
            first = root / 'first'
            runtime = root / 'empty-runtime'
            self.assertFalse(runtime.exists())
            before_manifest = workflow.execute(plan, first, runtime_home=runtime)
            before = json.loads((first / 'native.json').read_text())['sequence']
            original_files = {str(p.relative_to(first)): workflow.sha(p) for p in first.rglob('*') if p.is_file()}
            # 从真实交付回执提取片段 ID，不猜测对象或数组引用语法。
            clip = before_manifest['bindings']['shotClip']['clips'][0]
            revision = {'expectedProjectSha256': before_manifest['files']['project.fcproj'], 'assets': {}, 'operations': [
                {'command': 'timeline.trim', 'params': {'clip': clip, 'edge': 'in', 'mode': 'regular', 'delta': str(TICKS // 2)}},
                {'command': 'timeline.move', 'params': {'moves': [{'clip': clip, 'track': 'V1', 'time': '0'}], 'insert': False}}],
                'frames': [str(TICKS // 4), str(3 * TICKS // 4), str(5 * TICKS // 4), str(7 * TICKS // 4)], 'export': {'audioRequired': True}}
            second = root / 'second'
            after_manifest = workflow.execute(revision, second, runtime_home=runtime, source=first)
            after = json.loads((second / 'native.json').read_text())['sequence']
            edited = after['video'][0]['items'][0]
            self.assertEqual((str(edited['start']), str(edited['sourceIn']), str(edited['duration'])), ('0', str(TICKS // 2), str(TICKS)))
            self.assertEqual(before['video'][0]['items'][1], after['video'][0]['items'][1])
            self.assertEqual(before['audio'], after['audio'])
            self.assertEqual((first / 'captions.json').read_bytes(), (second / 'captions.json').read_bytes())
            self.assertEqual(after['durationFrames'], 24)
            pixels = []
            for index in range(4):
                with Image.open(second / f'frame-{index:04d}.png') as frame:
                    pixels.append(frame.convert('RGB').getpixel((20, 20)))
            self.assertGreater(pixels[0][0], 200)
            self.assertGreater(pixels[1][1], 80)
            self.assertLess(max(pixels[2]), 10)
            self.assertGreater(pixels[3][2], 200)
            decoded = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(second / 'film.mp4'), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
            for frame, channel in [(3, 0), (9, 1), (21, 2)]:
                offset = (frame * 320 * 180 + 20 * 320 + 20) * 3
                pixel = decoded[offset:offset + 3]
                self.assertGreater(pixel[channel], 80)
                self.assertEqual(max(range(3), key=lambda c: pixel[c]), channel)
            self.assertLess(max(decoded[(15 * 320 * 180 + 20 * 320 + 20) * 3:(15 * 320 * 180 + 20 * 320 + 20) * 3 + 3]), 10)
            for name, digest in original_files.items():
                self.assertEqual(workflow.sha(first / name), digest)
            invalid = json.loads(json.dumps(revision))
            invalid['operations'][0]['params']['delta'] = TICKS // 2
            with self.assertRaisesRegex(ValueError, 'ticks_require_decimal_string'):
                workflow.execute(invalid, root / 'invalid-numeric-delta', runtime_home=runtime, source=first)
            self.assertFalse((root / 'invalid-numeric-delta/manifest.json').exists())
            self.assertEqual(workflow.sha(first / 'project.fcproj'), before_manifest['files']['project.fcproj'])
            self.assertFalse(list(skill.rglob('*.pyc')))
            if os.environ.get('CRAFT_TIMELINE_TEMPORAL_EVIDENCE'):
                proof = {'schema': 'filmcraft-temporal-timeline-first-use/v1', 'initialProjectSha256': before_manifest['files']['project.fcproj'], 'revisedProjectSha256': after_manifest['files']['project.fcproj'], 'editedClip': edited, 'previewPixels': pixels, 'runtimeSha256': after_manifest['runtimeSha256'], 'files': after_manifest['files'], 'sourceFilesPreserved': True, 'otherClipPreserved': True, 'audioPreserved': True, 'captionsPreserved': True, 'scope': 'single installed timeline skill; default public empty-runtime install; synthetic temporal colors and sine audio; no creative acceptance'}
                with Path(os.environ['CRAFT_TIMELINE_TEMPORAL_EVIDENCE']).open('x') as stream:
                    json.dump(proof, stream, indent=2)
