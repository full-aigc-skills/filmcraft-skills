"""真实原生短片、字幕、音画与单镜头替换验收。"""
import importlib.util
import sys

# 宿主技能快照必须保持不可变；动态导入也不写字节码。
sys.dont_write_bytecode = True
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path(os.environ['CRAFT_INSTALLED_SKILL_ROOT']).resolve() if os.environ.get('CRAFT_INSTALLED_SKILL_ROOT') else ROOT / 'skills/filmcraft-use'
spec = importlib.util.spec_from_file_location('workflow', SKILL / 'scripts/workflow.py')
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)


def ffmpeg(*args):
    return subprocess.check_output(['ffmpeg', '-v', 'error'] + list(args))


@unittest.skipUnless(os.environ.get('CRAFT_LIVE_TEST') == '1', 'requires real runtime, ffmpeg, ffprobe, Pillow')
class NativeWorkflowTests(unittest.TestCase):
    def test_editable_short_film_relocation_and_one_shot_revision(self):
        from PIL import Image, ImageChops
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            isolated = root / 'single-skill'
            shutil.copytree(SKILL, isolated, ignore=shutil.ignore_patterns('__pycache__'))
            isolated_spec = importlib.util.spec_from_file_location('isolated_workflow', isolated / 'scripts/workflow.py')
            workflow = importlib.util.module_from_spec(isolated_spec)
            isolated_spec.loader.exec_module(workflow)
            runtime = root / 'fresh-runtime'
            red, green, voice = root / 'red.mp4', root / 'green.mp4', root / 'voice.wav'
            for path, color in [(red, 'red'), (green, 'green')]:
                ffmpeg('-f', 'lavfi', '-i', f'color=c={color}:s=320x180:r=12:d=2', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(path))
            # 延迟 0.5 秒的测试音，可同时检查音轨存在和同步。
            with wave.open(str(voice), 'wb') as stream:
                stream.setnchannels(1); stream.setsampwidth(2); stream.setframerate(48000)
                stream.writeframes(b''.join(struct.pack('<h', 0 if n < 24000 else int(6000 * math.sin(2 * math.pi * 440 * n / 48000))) for n in range(96000)))
            plan = json.loads((isolated / 'examples/short-film.json').read_text())
            plan['assets'] = {key: {'path': str(path), 'sha256': workflow.sha(path)} for key, path in [('shot', red), ('voice', voice)]}
            plan['operations'][2]['params']['duration'] = str(workflow.TICKS)
            plan['operations'].insert(3, {'command': 'timeline.place', 'params': {'item': {'$ref': 'shot.item'}, 'track': 'V1', 'time': str(workflow.TICKS), 'sourceIn': str(workflow.TICKS), 'duration': str(workflow.TICKS), 'insert': False}, 'as': 'otherClip'})
            first = root / 'v1'
            delivered = workflow.execute(plan, first, runtime_home=runtime)
            before = json.loads((first / 'native.json').read_text())['sequence']
            self.assertEqual(before['durationFrames'], 24)
            caption = json.loads((first / 'captions.json').read_text())['tracks'][0]['captions'][0]
            self.assertEqual((caption['start'], caption['end'], caption['text']), ('0', str(workflow.TICKS), 'First scene'))
            self.assertIn('00:00:01,000', (first / 'captions.srt').read_text())
            with Image.open(first / 'frame-0000.png') as initial, Image.open(first / 'frame-0001.png') as clean:
                difference = ImageChops.difference(initial.convert('RGB'), clean.convert('RGB')).getbbox()
                self.assertIsNotNone(difference)
                self.assertGreater(difference[1], 100)  # 字幕只影响下部区域。
            metadata = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-of', 'json', str(first / 'film.mp4')]))
            video = next(x for x in metadata['streams'] if x['codec_type'] == 'video')
            audio = next(x for x in metadata['streams'] if x['codec_type'] == 'audio')
            self.assertEqual((video['width'], video['height'], video['avg_frame_rate'], video['nb_read_frames']), (320, 180, '12/1', '24'))
            self.assertLess(abs(float(audio['start_time']) - float(video['start_time'])), 1 / 12)
            decoded = ffmpeg('-i', str(first / 'film.mp4'), '-map', '0:a:0', '-f', 's16le', '-ac', '1', '-ar', '48000', '-')
            samples = struct.unpack('<' + str(len(decoded) // 2) + 'h', decoded)
            rms = lambda start, end: math.sqrt(sum(x*x for x in samples[start:end]) / (end-start))
            self.assertLess(rms(0, 18000), 10)
            self.assertGreater(rms(30000, 90000), 1000)
            onset = next(n for n in range(0, len(samples) - 480, 480) if rms(n, n+480) > 100)
            self.assertLessEqual(abs(onset / 48000 - .5), 1 / 12)
            # 移走交付目录并删除原始输入，恢复必须依靠包内摘要和原生重关联。
            moved = root / 'moved'
            first.rename(moved)
            red.unlink(); voice.unlink()
            revision = {'expectedProjectSha256': delivered['files']['project.fcproj'],
                        'assets': {'replacement': {'path': str(green), 'sha256': workflow.sha(green)}},
                        'operations': [{'command': 'asset.import', 'params': {'asset': 'replacement'}, 'as': 'replacement'},
                                       {'command': 'clip.replaceFromBin', 'params': {'clips': {'$ref': 'shotClip.clips'}, 'item': {'$ref': 'replacement.item'}}}],
                        'frames': ['127008000000', '381024000000'], 'export': {'audioRequired': True}}
            second = root / 'v2'
            workflow.execute(revision, second, runtime_home=runtime, source=moved)
            after = json.loads((second / 'native.json').read_text())['sequence']
            self.assertEqual(before['audio'], after['audio'])
            self.assertEqual(before['video'][0]['items'][1], after['video'][0]['items'][1])
            self.assertEqual(delivered['files']['project.fcproj'], workflow.sha(moved / 'project.fcproj'))
            self.assertEqual(delivered['files']['frame-0001.png'], workflow.sha(second / 'frame-0001.png'))
            self.assertNotEqual(delivered['files']['frame-0000.png'], workflow.sha(second / 'frame-0000.png'))
            self.assertEqual((moved / 'captions.json').read_bytes(), (second / 'captions.json').read_bytes())
            # 原生新导出的第一镜头确实改变，第二镜头仍为红色。
            pixels = ffmpeg('-i', str(second / 'film.mp4'), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-')
            def pixel(frame):
                offset = (frame * 320 * 180 + 20 * 320 + 20) * 3
                return pixels[offset:offset+3]
            self.assertGreater(pixel(0)[1], pixel(0)[0])
            self.assertGreater(pixel(18)[0], pixel(18)[1])
            # 坏素材、时间越界、缺字库和并发修订冲突不能发布成功目录。
            for error, broken in [('revision_conflict', dict(revision, expectedProjectSha256='0'*64)),
                                  ('asset_digest_mismatch', dict(revision, assets={'replacement': {'path': str(green), 'sha256': '0'*64}})),
                                  ('caption_out_of_range', dict(revision, assets={}, operations=[{'command': 'caption.add', 'params': {'text': 'bad', 'startTicks': str(2*workflow.TICKS), 'durationTicks': str(workflow.TICKS)}}])),
                                  ('missing_font', dict(revision, assets={}, operations=[{'command': 'captions.setStyle', 'params': {'font': 'MissingCraftFixtureFont', 'track': 'C1'}}])),
                                  ('clip_out_of_range', dict(revision, assets={}, operations=[{'command': 'timeline.place', 'params': {'item': {'$ref': 'shot.item'}, 'time': '0', 'sourceIn': '0', 'duration': str(3*workflow.TICKS), 'insert': False}}]))]:
                target = root / error
                with self.assertRaisesRegex(ValueError, error):
                    workflow.execute(broken, target, runtime_home=runtime, source=moved)
                self.assertFalse(target.exists())

if __name__ == '__main__':
    unittest.main()
