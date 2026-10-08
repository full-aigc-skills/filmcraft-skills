"""单运动技能公开冷安装、LUT 与关键帧原生返工验收。"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(os.environ.get('CRAFT_MOTION_LUT_FIRST_USE')=='1','requires public runtime and existing ffmpeg/Pillow')
class MotionLutFirstUseTests(unittest.TestCase):
    def test_motion_lut_relocation_revision_and_source_preservation(self):
        from PIL import Image, ImageChops
        with tempfile.TemporaryDirectory(prefix='filmcraft-motion-lut-') as temporary:
            root=Path(temporary);skill=root/'.agents/skills/filmcraft-cli-motion'
            source=Path(os.environ.get('CRAFT_INSTALLED_MOTION_SKILL_ROOT',ROOT/'skills/filmcraft-cli-motion'))
            shutil.copytree(source,skill,ignore=shutil.ignore_patterns('__pycache__'))
            spec=importlib.util.spec_from_file_location('motion_first_use',skill/'scripts/workflow.py')
            w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
            skill_hashes={str(p.relative_to(skill)):w.sha(p) for p in skill.rglob('*') if p.is_file()}
            shot,voice,cube=root/'shot.mp4',root/'voice.wav',root/'swap.cube'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=red:s=320x180:r=12:d=2','-c:v','libx264','-pix_fmt','yuv420p',str(shot)],check=True)
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=440:duration=2:sample_rate=48000','-c:a','pcm_s16le',str(voice)],check=True)
            cube.write_text('TITLE "Swap red and green"\nLUT_3D_SIZE 2\n'+''.join(f'{g} {r} {b}\n' for b in (0,1) for g in (0,1) for r in (0,1)))
            plan=json.loads((skill/'examples/short-film.json').read_text())
            plan['assets']={name:{'path':str(path),'sha256':w.sha(path)} for name,path in [('shot',shot),('voice',voice)]}
            plan['assets']['grade']={'kind':'lut','path':str(cube),'sha256':w.sha(cube)}
            clip={'$ref':'shotClip.clips.0'}; common={'clip':clip,'effect':'motion','param':'position'}
            plan['operations'] += [
                {'command':'effects.toggleAnimation','params':common},
                {'command':'effects.setParam','params':{**common,'value':[100,90],'time':'0'}},
                {'command':'effects.setParam','params':{**common,'value':[200,90],'time':str(w.TICKS)}},
                {'command':'lumetri.setInputLut','params':{'clip':clip,'asset':'grade'}}]
            plan['frames']=['0',str(w.TICKS*3//2)]
            runtime=root/'empty-runtime'; self.assertFalse(runtime.exists())
            first=root/'first'; plan_path=root/'plan.json'
            cli_plan=json.loads(json.dumps(plan));del cli_plan['assets']['grade'];plan_path.write_text(json.dumps(cli_plan))
            completed=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts/workflow.py'),str(plan_path),'--read-root',str(root.resolve()),'--write-root',str(root.resolve()),'--output',str(first),'--runtime-home',str(runtime),'--lut-asset','grade='+str(cube)],capture_output=True,text=True,check=True)
            manifest=json.loads(completed.stdout)
            cube.unlink()
            cli=str(runtime/'filmcraft'/json.loads((skill/'scripts/runtime.lock.json').read_text())['resolvedVersion']/'filmcraft-cli')
            w.run(cli,['--project',str(first/'project.fcproj'),'--data-dir',str(root/'empty-library'),'render','--seconds','1.5','--out',str(root/'reopened.png')])
            with Image.open(root/'reopened.png') as image:
                red,green,blue=image.convert('RGB').getpixel((160,20));self.assertGreater(green,200);self.assertLess(red,25)
            with Image.open(first/'frame-0000.png') as a,Image.open(first/'frame-0001.png') as b:
                self.assertIsNotNone(ImageChops.difference(a.convert('RGB'),b.convert('RGB')).getbbox())
            moved=root/'moved';first.rename(moved)
            original={str(p.relative_to(moved)):w.sha(p) for p in moved.rglob('*') if p.is_file()}
            revision={'expectedProjectSha256':manifest['files']['project.fcproj'],'operations':[
                {'command':'effects.setParam','params':{**common,'value':[260,90],'time':str(w.TICKS)}},
                {'command':'lumetri.setInputLut','params':{'clip':clip,'asset':'grade'}}],
                'frames':['0',str(w.TICKS*3//2)],'export':{'audioRequired':True}}
            second=root/'second'; revised=w.execute(revision,second,runtime_home=runtime,source=moved)
            before=json.loads((moved/'native.json').read_text())['sequence'];after=json.loads((second/'native.json').read_text())['sequence']
            self.assertEqual(before['audio'],after['audio'])
            self.assertEqual((moved/'captions.json').read_bytes(),(second/'captions.json').read_bytes())
            effects=after['video'][0]['items'][0]['effects']
            motion=next(e for e in effects if e['effect']=='motion');self.assertEqual(motion['params']['position']['keyframes'],2)
            self.assertEqual(next(e for e in before['video'][0]['items'][0]['effects'] if e['effect']=='lumetri'),next(e for e in effects if e['effect']=='lumetri'))
            with Image.open(moved/'frame-0001.png') as a,Image.open(second/'frame-0001.png') as b:
                self.assertIsNotNone(ImageChops.difference(a.convert('RGB'),b.convert('RGB')).getbbox())
            streams=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(second/'film.mp4')]))['streams']
            video=next(s for s in streams if s['codec_type']=='video');self.assertEqual(video['nb_read_frames'],'24')
            self.assertTrue(any(s['codec_type']=='audio' for s in streams))
            raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(second/'film.mp4'),'-frames:v','24','-f','rawvideo','-pix_fmt','rgb24','-'])
            self.assertEqual(len(raw),24*320*180*3)
            pixel=list(raw[18*320*180*3+(20*320+160)*3:18*320*180*3+(20*320+160)*3+3])
            self.assertGreater(pixel[1],180);self.assertLess(pixel[0],35)
            def decoded_audio(path):
                return subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-map','0:a:0','-f','s16le','-'])
            self.assertEqual(decoded_audio(moved/'film.mp4'),decoded_audio(second/'film.mp4'))
            # 不合法返工应在执行前失败，既不修改旧包，也不创建新交付。
            invalid={**revision,'operations':[{'command':'effects.setParam','params':{**common,'value':[float('nan'),90]}}]}
            with self.assertRaisesRegex(ValueError,'invalid_effect_params'):w.execute(invalid,root/'bad',runtime_home=runtime,source=moved)
            self.assertFalse((root/'bad').exists())
            corrupted=root/'corrupted-source';shutil.copytree(moved,corrupted)
            (corrupted/manifest['assets']['grade']['path']).write_text('changed LUT')
            with self.assertRaisesRegex(ValueError,'asset_digest_mismatch'):
                w.execute(revision,root/'bad-lut',runtime_home=runtime,source=corrupted)
            self.assertFalse((root/'bad-lut').exists())
            self.assertEqual(original,{str(p.relative_to(moved)):w.sha(p) for p in moved.rglob('*') if p.is_file()})
            self.assertEqual(skill_hashes,{str(p.relative_to(skill)):w.sha(p) for p in skill.rglob('*') if p.is_file()})
            if os.environ.get('CRAFT_MOTION_LUT_EVIDENCE'):
                evidence={'schema':'filmcraft-motion-lut-first-use/v1','result':'PASS','scope':'candidate single copied motion skill; empty runtime; public download; synthetic existing media; native LUT/keyframes and moved revision; not immutable plugin or Art acceptance','runtimeSha256':revised['runtimeSha256'],'independentlyDecodedFrames':24,'lutSourceRemoved':True,'lutPixel':{'red':red,'green':green,'blue':blue},'motionKeyframes':2,'sourcePreserved':True,'captionsPreserved':True,'audioClipsPreserved':True,'decodedAudioPreserved':True,'decodedLutPixel':pixel,'nonTargetLumetriPreserved':True,'invalidRevisionRejected':True,'corruptedPackagedLutRejected':True,'publicLutAssetArgumentVerified':True,'skillFilesPreserved':True,'initialProjectSha256':manifest['files']['project.fcproj'],'revisedFiles':revised['files']}
                with Path(os.environ['CRAFT_MOTION_LUT_EVIDENCE']).open('x') as stream:json.dump(evidence,stream,indent=2)

if __name__=='__main__':unittest.main()
