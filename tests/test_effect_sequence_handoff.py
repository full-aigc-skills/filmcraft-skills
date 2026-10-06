"""真实 Effect 动态输出到 Film 的双领域交接；不替代固定插件和 Art 验收。"""
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


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


def load(skill, name):
    spec = importlib.util.spec_from_file_location(name, skill/'scripts/workflow.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


@unittest.skipUnless(os.environ.get('CRAFT_EFFECT_FILM_SEQUENCE_FIRST_USE') == '1', 'requires two domain skills, public runtime downloads, Pillow and ffmpeg')
class EffectFilmSequenceTests(unittest.TestCase):
    def test_actual_animation_handoff_and_moved_film_text_revision(self):
        from PIL import Image, ImageChops
        effect_source = Path(os.environ['CRAFT_EFFECT_SEQUENCE_SKILL_ROOT']).resolve()
        film_source = Path(os.environ.get('CRAFT_FILM_SEQUENCE_SKILL_ROOT', ROOT/'skills/filmcraft-cli-media')).resolve()
        source_hashes = [hashes(effect_source), hashes(film_source)]
        with tempfile.TemporaryDirectory(prefix='effect-film-sequence-') as temporary:
            root = Path(temporary)
            effect_skill = root/'.agents/skills/effectcraft-cli-export'
            film_skill = root/'.agents/skills/filmcraft-cli-media'
            for source, target in [(effect_source, effect_skill), (film_source, film_skill)]:
                shutil.copytree(source, target, ignore=shutil.ignore_patterns('__pycache__'))
            copied_hashes = [hashes(effect_skill), hashes(film_skill)]
            effect, film = load(effect_skill, 'handoff_effect'), load(film_skill, 'handoff_film')
            runtime = root/'empty-runtime'; self.assertFalse(runtime.exists())
            effect_plan = json.loads((effect_skill/'examples/brand-intro.json').read_text())
            effect_plan['exports'] = [{'format': 'png-sequence'}]
            effect_out = root/'effect'; effect_delivery = effect.execute(effect_plan, effect_out, runtime_home=runtime)
            sequence = effect_delivery['imageSequence']
            metadata = json.loads((effect_out/sequence['path']).read_text())
            self.assertEqual(metadata['frameCount'], 12)
            self.assertEqual(metadata['frameRate'], {'num': 12, 'den': 1})
            background = root/'background.png'; Image.new('RGB', (320,180), (0,128,0)).save(background)
            plan = {'document': {'name': 'actual Effect handoff', 'width': 320, 'height': 180, 'frameRate': metadata['frameRate']},
                    'assets': {'background': {'path': str(background), 'sha256': film.sha(background)},
                               'overlay': {'kind': 'image-sequence', 'path': str(effect_out/sequence['path']), 'sha256': sequence['sha256']}},
                    'operations': [{'command': 'asset.import', 'params': {'asset': 'background'}, 'as': 'background'},
                                   {'command': 'asset.import', 'params': {'asset': 'overlay'}, 'as': 'overlay'},
                                   {'command': 'timeline.place', 'params': {'item': {'$ref': 'background.item'}, 'track': 'V1', 'duration': str(film.TICKS), 'insert': False}},
                                   {'command': 'timeline.place', 'params': {'item': {'$ref': 'overlay.item'}, 'track': 'V2', 'duration': str(film.TICKS), 'insert': False}, 'as': 'overlayClip'}],
                    'frames': ['0', str(film.TICKS//2)], 'export': {'audioRequired': False}}
            first = root/'film'; delivery = film.execute(plan, first, runtime_home=runtime)
            self.assertEqual(delivery['assets']['overlay']['probe']['kind'], 'ImageSequence')
            self.assertEqual(delivery['assets']['overlay']['probe']['duration'], str(film.TICKS))
            self.assertEqual(len([name for name in delivery['files'] if '/frame_' in name]), 12)
            # 独立解码实际导出，并以 Effect 原始帧验证背景透出、图形颜色和动画变化。
            raw = subprocess.check_output(['ffmpeg','-v','error','-i',str(first/'film.mp4'),'-f','rawvideo','-pix_fmt','rgb24','-'])
            self.assertEqual(len(raw), 12*320*180*3)
            for index in [0,6,11]:
                with Image.open(effect_out/'rgba-sequence'/metadata['frames'][index]['location']) as overlay:
                    expected = Image.alpha_composite(Image.new('RGBA',(320,180),(0,128,0,255)), overlay).convert('RGB')
                    for x,y in [(10,10),(60,85)]:
                        offset=(index*320*180+y*320+x)*3
                        self.assertLessEqual(max(abs(a-b) for a,b in zip(raw[offset:offset+3],expected.getpixel((x,y)))),20)
            with Image.open(first/'frame-0000.png') as a, Image.open(first/'frame-0001.png') as b:
                self.assertIsNotNone(ImageChops.difference(a.convert('RGB'),b.convert('RGB')).getbbox())
            effect_before = hashes(effect_out)
            revised_effect = root/'effect-revised'
            revised = effect.execute({'expectedProjectSha256': effect_delivery['files']['project.ecproj'],
                                      'operations': [{'command': 'layer.setText', 'params': {'layer': {'$ref': 'title.layer'}, 'text': 'NOVA PLUS'}}],
                                      'frames': [0,.5], 'exports': [{'format':'png-sequence'}]}, revised_effect, runtime_home=runtime, source=effect_out)
            self.assertEqual(hashes(effect_out), effect_before)
            moved=root/'moved-film'; first.rename(moved); background.unlink()
            # 删除原片头依赖，原 Film 工程重关联只能消费其收集包。
            shutil.rmtree(effect_out)
            before=hashes(moved); next_sequence=revised['imageSequence']
            change={'expectedProjectSha256':delivery['files']['project.fcproj'],
                    'assets':{'replacement':{'kind':'image-sequence','path':str(revised_effect/next_sequence['path']),'sha256':next_sequence['sha256']}},
                    'operations':[{'command':'asset.import','params':{'asset':'replacement'},'as':'replacement'},
                                  {'command':'clip.replaceFromBin','params':{'clips':{'$ref':'overlayClip.clips'},'item':{'$ref':'replacement.item'}}}],
                    'frames':['0',str(film.TICKS//2)],'export':{'audioRequired':False}}
            next_film=root/'film-revised'; result=film.execute(change,next_film,runtime_home=runtime,source=moved)
            self.assertEqual(hashes(moved),before)
            self.assertEqual(delivery['files']['frame-0000.png'],result['files']['frame-0000.png'])
            self.assertNotEqual(delivery['files']['frame-0001.png'],result['files']['frame-0001.png'])
            self.assertEqual(delivery['assets']['background']['sha256'],result['assets']['background']['sha256'])
            self.assertEqual([hashes(effect_skill),hashes(film_skill)],copied_hashes)
            self.assertEqual([hashes(effect_source),hashes(film_source)],source_hashes)
            if os.environ.get('CRAFT_EFFECT_FILM_SEQUENCE_EVIDENCE'):
                proof={'schema':'craft-effect-film-sequence-first-use/v1','result':'PASS',
                       'effectRuntimeSha256':effect_delivery['runtimeSha256'],'filmRuntimeSha256':delivery['runtimeSha256'],
                       'effectSequenceSha256':sequence['sha256'],'revisedEffectSequenceSha256':next_sequence['sha256'],
                       'copiedSkillHashes':{'effect':copied_hashes[0],'film':copied_hashes[1]},
                       'frameCount':12,'frameRate':metadata['frameRate'],'nativeFilmProbe':delivery['assets']['overlay']['probe'],
                       'independentlyDecodedFrames':12,'sourceSequenceRemoved':True,'movedProjectRevisionPassed':True,
                       'backgroundAndInitialFramePreserved':True,'animatedTextFrameChanged':True,'oldDeliveryAndSkillsPreserved':True,
                       'scope':'two copied source skills; empty runtime; public native installers; actual Effect output consumed by Film',
                       'excluded':['immutable new skill/plugin installation','Art mixed delivery','creative/color/GUI acceptance']}
                with Path(os.environ['CRAFT_EFFECT_FILM_SEQUENCE_EVIDENCE']).open('x') as stream:json.dump(proof,stream,indent=2)
