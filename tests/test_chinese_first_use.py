"""中文字幕及本地合成真实语音的首次使用与局部修订验收。"""
import hashlib
import io
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
ROOT=Path(__file__).resolve().parents[1]
TICKS=254016000000

class ChineseTemplateContractTests(unittest.TestCase):
    def test_subtitle_skill_has_own_chinese_template(self):
        plan=json.loads((ROOT/'skills/filmcraft-cli-subtitles/examples/chinese-short-film.json').read_text())
        text=next(o['params']['text'] for o in plan['operations'] if o['command']=='caption.add')
        self.assertEqual(text,'新品上市，轻松剪辑。')
        self.assertEqual(next(o['params']['language'] for o in plan['operations'] if o['command']=='captions.newTrack'),'zh-CN')
        self.assertNotEqual(next(o['params']['font'] for o in plan['operations'] if o['command']=='captions.setStyle'),'Arial')

@unittest.skipUnless(os.environ.get('CRAFT_CN_FIRST_USE')=='1','requires declared macOS voice, ffmpeg/ffprobe and Pillow')
class ChineseFirstUseTests(unittest.TestCase):
    def test_isolated_skill_installs_renders_chinese_and_preserves_spoken_audio(self):
        from PIL import Image,ImageChops
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);skill=root/'.agents/skills/filmcraft-cli-subtitles'
            shutil.copytree(ROOT/'skills/filmcraft-cli-subtitles',skill,ignore=shutil.ignore_patterns('__pycache__'))
            runtime=root/'runtime';shot=root/'shot.mp4';voice=root/'voice.wav';speech=root/'speech.aiff'
            if os.environ.get('CRAFT_CN_ARCHIVE'):
                subprocess.run([sys.executable,'-I','-B',str(skill/'scripts/bootstrap.py'),'--runtime-home',str(runtime),'--archive',os.environ['CRAFT_CN_ARCHIVE']],check=True,capture_output=True,text=True,timeout=120)
            def command(args):
                result=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=240)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr);return result.stdout
            # 只使用显式指定且已存在的系统声音；不安装或下载声音，不调用付费服务。
            command(['/usr/bin/say','-v',os.environ['CRAFT_CN_VOICE'],'-o',speech,'新品上市，轻松剪辑。'])
            command(['ffmpeg','-v','error','-i',speech,'-af','apad','-t','3','-ar','48000','-ac','1','-c:a','pcm_s16le',voice])
            command(['ffmpeg','-v','error','-f','lavfi','-i','color=c=0x1d3449:s=640x360:r=24:d=3','-c:v','libx264','-pix_fmt','yuv420p',shot])
            with wave.open(str(voice),'rb') as stream:source_pcm=struct.unpack('<'+str(stream.getnframes())+'h',stream.readframes(stream.getnframes()))
            self.assertGreater(math.sqrt(sum(s*s for s in source_pcm)/len(source_pcm)),100)
            plan=json.loads((skill/'examples/chinese-short-film.json').read_text())
            def run(plan,out,source=None):
                path=root/(out.name+'.json');path.write_text(json.dumps(plan,ensure_ascii=False))
                args=[sys.executable,'-I','-B',skill/'scripts/workflow.py',path,'--read-root',str(root.resolve()),'--write-root',str(root.resolve()),'--output',out,'--runtime-home',runtime]
                if source:args+=['--source',source]
                else:args+=['--asset','shot='+str(shot),'--asset','voice='+str(voice)]
                result=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=240,env=dict(os.environ,PATH='/usr/bin:/bin'))
                self.assertEqual(result.returncode,0,result.stdout+result.stderr);return json.loads(result.stdout)
            first=root/'v1';delivered=run(plan,first)
            captions=json.loads((first/'captions.json').read_text());caption=captions['tracks'][0]['captions'][0]
            self.assertEqual((caption['text'],caption['start'],caption['end']),('新品上市，轻松剪辑。','0',str(2*TICKS)))
            self.assertIn('新品上市，轻松剪辑。',(first/'captions.srt').read_text())
            with Image.open(first/'frame-0000.png') as subtitle,Image.open(first/'frame-0001.png') as clean:
                box=ImageChops.difference(subtitle.convert('RGB'),clean.convert('RGB')).getbbox()
                self.assertIsNotNone(box);self.assertGreater(box[1],180)
            # 检查真正的成片抽帧；预览有字不代表导出启用了字幕烧录。
            burned=[]
            for second in ('1','2.5'):
                data=subprocess.check_output(['ffmpeg','-v','error','-ss',second,'-i',str(first/'film.mp4'),'-frames:v','1','-f','image2pipe','-vcodec','png','-'])
                with Image.open(io.BytesIO(data)) as frame:burned.append(frame.convert('RGB').copy())
            export_box=ImageChops.difference(*burned).getbbox()
            self.assertIsNotNone(export_box,'movie export omitted burned subtitles')
            self.assertGreater(export_box[1],180)
            metadata=json.loads(command(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',first/'film.mp4']))['streams']
            video=next(s for s in metadata if s['codec_type']=='video');audio=next(s for s in metadata if s['codec_type']=='audio')
            self.assertEqual((video['width'],video['height'],video['nb_read_frames']),(640,360,'72'))
            self.assertLess(abs(float(audio['start_time'])-float(video['start_time'])),1/24)
            raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(first/'film.mp4'),'-map','0:a:0','-f','s16le','-ac','1','-ar','48000','-'])
            pcm=struct.unpack('<'+str(len(raw)//2)+'h',raw);length=min(len(pcm),len(source_pcm));a=source_pcm[:length];b=pcm[:length]
            correlation=sum(x*y for x,y in zip(a,b))/math.sqrt(sum(x*x for x in a)*sum(y*y for y in b))
            self.assertGreater(correlation,.95)
            old_native=json.loads((first/'native.json').read_text());old_sha=hashlib.sha256((first/'project.fcproj').read_bytes()).hexdigest()
            revised=root/'v2';run({'expectedProjectSha256':old_sha,'operations':[{'command':'captions.setText','params':{'caption':{'$ref':'caption.caption'},'text':'新品上市｜轻松剪辑'}}],'frames':[str(TICKS)],'export':{'audioRequired':True}},revised,first)
            self.assertEqual(hashlib.sha256((first/'project.fcproj').read_bytes()).hexdigest(),old_sha)
            self.assertEqual(old_native['sequence']['audio'],json.loads((revised/'native.json').read_text())['sequence']['audio'])
            self.assertEqual(json.loads((revised/'captions.json').read_text())['tracks'][0]['captions'][0]['text'],'新品上市｜轻松剪辑')
            # 同字数不同汉字必须产生不同字幕像素；非空图片仍可能全是缺字方框。
            glyph_outputs=[]
            for index,text in enumerate(('新品上市','轻松剪辑')):
                output=root/('glyph-'+str(index))
                run({'expectedProjectSha256':old_sha,'operations':[{'command':'captions.setText','params':{'caption':{'$ref':'caption.caption'},'text':text}}],'frames':[str(TICKS)],'export':{'audioRequired':True}},output,first)
                with Image.open(output/'frame-0000.png') as frame:
                    glyph_outputs.append(frame.convert('RGB').copy())
            self.assertIsNotNone(ImageChops.difference(*glyph_outputs).getbbox(),'distinct Chinese captions rendered as identical replacement glyphs')
            if os.environ.get('CRAFT_CN_EVIDENCE_DIR'):
                evidence=Path(os.environ['CRAFT_CN_EVIDENCE_DIR']);evidence.mkdir(parents=True,exist_ok=False)
                shutil.copytree(first,evidence/'v1');shutil.copytree(revised,evidence/'v2')
                (evidence/'receipt.json').write_text(json.dumps({'font':'Heiti SC','voice':os.environ['CRAFT_CN_VOICE'],'correlation':correlation,'sourceProjectSha256':old_sha,'delivery':delivered},ensure_ascii=False,indent=2)+'\n')
            self.assertFalse(any(skill.rglob('*.pyc')))
