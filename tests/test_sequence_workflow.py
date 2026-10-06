"""序列工作流使用实际维护版 CLI；候选安装注入不算公开冷安装。"""
import hashlib
from contextlib import nullcontext
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get('CRAFT_FILM_SEQUENCE_CANDIDATE') or os.environ.get('CRAFT_FILM_SEQUENCE_FIRST_USE')=='1','requires sequence runtime acceptance, Pillow and ffmpeg')
class SequenceWorkflowTests(unittest.TestCase):
    def test_sequence_import_collection_and_moved_project_revision(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);skill=root/'.agents/skills/filmcraft-cli-media'
            shutil.copytree(ROOT/'skills/filmcraft-cli-media',skill,ignore=shutil.ignore_patterns('__pycache__'))
            spec=importlib.util.spec_from_file_location('isolated_sequence_workflow',skill/'scripts/workflow.py');workflow=importlib.util.module_from_spec(spec);spec.loader.exec_module(workflow)
            skill_hashes={str(p.relative_to(skill)):workflow.sha(p) for p in skill.rglob('*') if p.is_file()}
            public=os.environ.get('CRAFT_FILM_SEQUENCE_FIRST_USE')=='1'
            runtime=root/'fresh-runtime'
            self.assertFalse(runtime.exists())
            lock=json.loads((skill/'scripts/runtime.lock.json').read_text())
            patch_sha=json.loads((ROOT/'runtime/sequence-rate-patch.json').read_text())['patchSha256']
            if public:
                receipt=lock['artifacts']['darwin-arm64']
                self.assertEqual(lock['resolvedVersion'],'0.2.0-craft.2')
            else:
                archive=Path(os.environ['CRAFT_FILM_SEQUENCE_CANDIDATE']);receipt=json.loads(archive.with_name('build-receipt.json').read_text())
                self.assertEqual(workflow.sha(archive),receipt['archiveSha256'])
                self.assertEqual(receipt['provenance']['patchSha256'],patch_sha)
                binary=root/'filmcraft-cli'
                with zipfile.ZipFile(archive) as z:binary.write_bytes(z.read('filmcraft-cli'))
                binary.chmod(0o700);self.assertEqual(workflow.sha(binary),receipt['binarySha256'])
            seq=root/'input';seq.mkdir();frames=[]
            for index in range(12):
                image=Image.new('RGBA',(32,18),(0,0,0,0))
                for y in range(2,12):
                    for x in range(2,12):image.putpixel((x,y),(index*20,0,0,255))
                p=seq/f'frame_{index:05d}.png';image.save(p)
                frames.append({'index':index,'location':p.name,'sha256':workflow.sha(p),'bytes':p.stat().st_size,'alphaExtrema':[0,255],'rgbaSha256':hashlib.sha256(image.tobytes()).hexdigest()})
            descriptor={'schema':'craft-image-sequence/v1','encoding':'png','width':32,'height':18,'bitDepth':8,'channels':'rgba','alphaRepresentation':'straight-png','colorSpace':'unknown','frameRate':{'num':12,'den':1},'frameCount':12,'durationTicks':'12','timeBase':{'num':1,'den':12},'frames':frames}
            manifest=seq/'sequence.json';manifest.write_text(json.dumps(descriptor))
            background=root/'background.png';Image.new('RGB',(32,18),(0,128,0)).save(background)
            plan={'document':{'name':'sequence workflow','width':32,'height':18,'frameRate':{'num':12,'den':1}},'assets':{'background':{'path':str(background),'sha256':workflow.sha(background)},'overlay':{'kind':'image-sequence','path':str(manifest),'sha256':workflow.sha(manifest)}},'operations':[{'command':'asset.import','params':{'asset':'background'},'as':'background'},{'command':'asset.import','params':{'asset':'overlay'},'as':'overlay'},{'command':'timeline.place','params':{'item':{'$ref':'background.item'},'track':'V1','duration':str(workflow.TICKS),'insert':False}},{'command':'timeline.place','params':{'item':{'$ref':'overlay.item'},'track':'V2','duration':str(workflow.TICKS),'insert':False},'as':'overlayClip'}],'frames':['0',str(workflow.TICKS//2)],'export':{'audioRequired':False}}
            original_loader=workflow.load_module
            def loader(name):
                if name=='bootstrap':return SimpleNamespace(install=lambda *args:{'executable':str(binary),'binarySha256':receipt['binarySha256']})
                return original_loader(name)
            # 公开模式保留真实安装器；候选模式明确只验证已绑定的私有程序。
            with nullcontext() if public else patch.object(workflow,'load_module',side_effect=loader):
                first=root/'first';delivery=workflow.execute(plan,first,runtime_home=runtime)
                if public:
                    installed=original_loader('bootstrap').install(lock,runtime)
                    self.assertTrue(installed['reused'])
                    self.assertEqual(installed['binarySha256'],receipt['binarySha256'])
                    self.assertEqual(delivery['runtimeSha256'],receipt['binarySha256'])
                self.assertEqual(delivery['assets']['overlay']['probe']['kind'],'ImageSequence')
                self.assertEqual(delivery['assets']['overlay']['probe']['duration'],str(workflow.TICKS))
                self.assertEqual(len([x for x in delivery['files'] if '/frame_' in x]),12)
                moved=root/'moved';first.rename(moved);shutil.rmtree(seq);background.unlink()
                change={'expectedProjectSha256':delivery['files']['project.fcproj'],'operations':[{'command':'timeline.move','params':{'moves':[{'clip':delivery['bindings']['overlayClip']['clips'][0],'track':'V2','time':str(workflow.TICKS//12)}],'insert':False}}],'frames':['0',str(workflow.TICKS//2)],'export':{'audioRequired':False}}
                second=root/'second';revision=workflow.execute(change,second,runtime_home=runtime,source=moved)
                self.assertEqual(workflow.sha(moved/'project.fcproj'),delivery['files']['project.fcproj'])
                for name,digest in delivery['files'].items():self.assertEqual(workflow.sha(moved/name),digest)
                self.assertEqual(delivery['assets']['overlay']['sha256'],revision['assets']['overlay']['sha256'])
                self.assertNotEqual(delivery['files']['frame-0000.png'],revision['files']['frame-0000.png'])
                for folder in [moved,second]:
                    with Image.open(folder/'frame-0001.png') as frame:self.assertEqual(frame.convert('RGB').getpixel((20,15)),(0,128,0))
                export_frames=[]
                for folder, shifted in [(moved,False),(second,True)]:
                    pixels=subprocess.check_output(['ffmpeg','-v','error','-i',str(folder/'film.mp4'),'-f','rawvideo','-pix_fmt','rgb24','-'])
                    count=len(pixels)//(32*18*3);self.assertEqual(count,13 if shifted else 12);export_frames.append(count)
                    offset=(6*32*18+5*32+5)*3
                    expected=100 if shifted else 120
                    self.assertLessEqual(max(abs(a-b) for a,b in zip(pixels[offset:offset+3],bytes([expected,0,0]))),20)
                bad=root/'bad-source';shutil.copytree(moved,bad)
                frame=bad/Path(delivery['assets']['overlay']['path']).parent/'frame_00006.png'
                frame.write_bytes(frame.read_bytes()+b'corrupt');bad_hash=workflow.sha(frame)
                with self.assertRaisesRegex(ValueError,'sequence_frame_digest_mismatch'):
                    workflow.execute(change,root/'bad-output',runtime_home=runtime,source=bad)
                self.assertFalse((root/'bad-output').exists());self.assertEqual(workflow.sha(frame),bad_hash)
                self.assertEqual(skill_hashes,{str(p.relative_to(skill)):workflow.sha(p) for p in skill.rglob('*') if p.is_file()})
                if os.environ.get('CRAFT_FILM_SEQUENCE_WORKFLOW_EVIDENCE'):
                    value={'schema':'craft-sequence-workflow-first-use/v1' if public else 'craft-sequence-workflow-candidate/v1','result':'passed','runtimeSha256':receipt['binarySha256'],'patchSha256':patch_sha,'sequenceManifestSha256':delivery['assets']['overlay']['sha256'],'collectedFrames':12,'independentlyDecodedExportFrames':export_frames,'sourceDirectoryRemoved':True,'corruptDependencyRejected':True,'isolatedSkillBytesUnchanged':True,'movedRevisionPassed':True,'originalDeliveryPreserved':True,'nativeProbe':delivery['assets']['overlay']['probe'],'sourceProjectSha256':delivery['files']['project.fcproj'],'revisedProjectSha256':revision['files']['project.fcproj'],'runtimeLockSha256':workflow.sha(skill/'scripts/runtime.lock.json'),'scope':'single copied source skill; empty runtime; unchanged installer; public fixed native download; not immutable plugin or Art mixed acceptance' if public else 'isolated skill workflow and actual native CLI; installer overridden to verified candidate; not public cold installation or Art mixed acceptance'}
                    with Path(os.environ['CRAFT_FILM_SEQUENCE_WORKFLOW_EVIDENCE']).open('x') as stream:json.dump(value,stream,indent=2)
