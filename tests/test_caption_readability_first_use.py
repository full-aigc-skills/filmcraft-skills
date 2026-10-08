"""真实小尺寸模板字幕像素验收；未启用不能计为首次使用通过。"""
import hashlib,json,os,shutil,subprocess,sys,tempfile,unittest,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(os.environ.get('CRAFT_CAPTION_READABILITY_FIRST_USE')=='1','requires public native download, declared shot and Pillow')
class CaptionReadabilityFirstUseTests(unittest.TestCase):
 def test_single_subtitle_skill_template_exports_readable_caption(self):
  from PIL import Image
  source=Path(os.environ.get('CRAFT_CAPTION_SKILL',ROOT/'skills/filmcraft-cli-subtitles'));shot=Path(os.environ['CRAFT_CAPTION_SHOT']).resolve(strict=True)
  with tempfile.TemporaryDirectory(prefix='craft-caption-readability-') as temporary:
   root=Path(temporary);skill=root/'.agents/skills/filmcraft-cli-subtitles';shutil.copytree(source,skill,ignore=shutil.ignore_patterns('__pycache__'))
   files={str(p.relative_to(skill)):hashlib.sha256(p.read_bytes()).hexdigest() for p in skill.rglob('*') if p.is_file()};voice=root/'voice.wav'
   with wave.open(str(voice),'wb') as stream:
    stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(48000);stream.writeframes(b'\0\0'*96000)
   runtime=root/'empty-runtime';output=root/'delivery';env=dict(os.environ,PATH='/usr/bin:/bin')
   for key in ('CRAFT_RUNTIME_HOME','CRAFT_NODE_ARCHIVE','CRAFT_BUNDLE_DIRECTORY','CRAFT_NATIVE_ARCHIVE_DIRECTORY'):env.pop(key,None)
   result=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts/workflow.py'),str(skill/'examples/short-film.json'),'--asset','shot='+str(shot),'--asset','voice='+str(voice),'--read-root',str(root.resolve()),'--write-root',str(root.resolve()),'--output',str(output),'--runtime-home',str(runtime)],env=env,text=True,capture_output=True,timeout=600)
   self.assertEqual(result.returncode,0,result.stdout+result.stderr)
   with Image.open(output/'frame-0000.png') as im:
    im=im.convert('RGB');points=[(x,y) for y in range(150,180) for x in range(320) if min(im.getpixel((x,y)))>180]
   self.assertTrue(points,'export has no visible bright caption pixels');box=[min(x for x,y in points),min(y for x,y in points),max(x for x,y in points)+1,max(y for x,y in points)+1]
   self.assertGreaterEqual(box[3]-box[1],8,'small-frame caption glyph is too small to read');self.assertTrue((output/'project.fcproj').is_file());self.assertTrue((output/'film.mp4').is_file())
   self.assertEqual(files,{str(p.relative_to(skill)):hashlib.sha256(p.read_bytes()).hexdigest() for p in skill.rglob('*') if p.is_file()})
   if os.environ.get('CRAFT_CAPTION_EVIDENCE'):
    proof={'schema':'craft-caption-readability-first-use/v1','result':'PASS','scope':'single copied subtitle skill, empty public native runtime, shipped short-film template, actual saved/reopened project and rendered pixels','skillFiles':files,'glyphBounds':box,'projectSha256':hashlib.sha256((output/'project.fcproj').read_bytes()).hexdigest(),'filmSha256':hashlib.sha256((output/'film.mp4').read_bytes()).hexdigest(),'shotSha256':hashlib.sha256(shot.read_bytes()).hexdigest(),'voiceIsTestPCM':True,'humanAcceptance':'NOT_RUN'}
    Path(os.environ['CRAFT_CAPTION_EVIDENCE']).write_text(json.dumps(proof,indent=2)+'\n');shutil.copyfile(output/'frame-0000.png',Path(os.environ['CRAFT_CAPTION_EVIDENCE']).with_suffix('.png'))
if __name__=='__main__':unittest.main()
