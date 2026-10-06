"""维护版二进制的真实序列收集与动态透明合成；不是公开冷安装验收。"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get('CRAFT_FILM_SEQUENCE_CANDIDATE'), 'requires current checksum-bound candidate archive and Pillow')
class NativeSequenceCandidateTests(unittest.TestCase):
    def test_candidate_collects_animation_and_renders_after_source_is_unavailable(self):
        from PIL import Image
        archive = Path(os.environ['CRAFT_FILM_SEQUENCE_CANDIDATE'])
        receipt = json.loads(archive.with_name('build-receipt.json').read_text())
        patch = json.loads((ROOT/'runtime/sequence-rate-patch.json').read_text())
        sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
        self.assertEqual(sha(archive), receipt['archiveSha256'])
        self.assertEqual(receipt['provenance']['patchSha256'], patch['patchSha256'])
        with tempfile.TemporaryDirectory(prefix='film-sequence-candidate-') as temporary:
            root = Path(temporary); binary = root/'filmcraft-cli'
            with zipfile.ZipFile(archive) as package: binary.write_bytes(package.read('filmcraft-cli'))
            binary.chmod(0o700)
            self.assertEqual(sha(binary), receipt['binarySha256'])
            self.assertEqual(subprocess.check_output([str(binary),'--version'], text=True).strip(), 'filmcraft-cli 0.2.0-craft.2')
            spec = importlib.util.spec_from_file_location('candidate_mcp', ROOT/'skills/filmcraft-use/scripts/mcp_session.py')
            mcp = importlib.util.module_from_spec(spec); spec.loader.exec_module(mcp)
            inputs = root/'inputs'; inputs.mkdir()
            background = inputs/'background.png'; Image.new('RGB',(32,18),(0,128,0)).save(background)
            frames = inputs/'sequence'; frames.mkdir()
            for index in range(12):
                image = Image.new('RGBA',(32,18),(0,0,0,0))
                for y in range(2,12):
                    for x in range(2,12): image.putpixel((x,y),(index*20,0,0,255))
                image.putpixel((15,5),(255,0,0,128))
                image.save(frames/f'frame_{index:05d}.png')
            original = {str(p.relative_to(inputs)):sha(p) for p in inputs.rglob('*') if p.is_file()}
            with mcp.Session([str(binary),'mcp']) as session:
                def command(name, params):
                    result = session.request('tools/call', {'name':'command_run','arguments':{'id':name,'params':params}})
                    if result.get('isError'): raise RuntimeError(str(result))
                    return json.loads(next(x['text'] for x in result['content'] if x.get('type')=='text'))
                command('file.newProject',{'name':'Sequence candidate'})
                command('file.newSequence',{'name':'Sequence candidate','width':32,'height':18,'fps':12})
                bg = command('file.import',{'paths':[str(background)]})['items'][0]
                sequence = command('file.importImageSequence',{'path':str(frames/'frame_00000.png'),'frameRate':{'num':12,'den':1}})['items'][0]
                for item, track in [(bg,'V1'),(sequence,'V2')]:
                    command('timeline.place',{'item':item,'track':track,'time':0,'sourceIn':0,'duration':254016000000,'insert':False})
                collection = command('file.projectManager',{'destination':str(root/'delivery'),'projectName':'project','excludeUnused':False,'includeProxies':False,'wait':True})
                entry = next(x for x in collection['files'] if x['item']==sequence)
                self.assertEqual(len(entry['sequenceFiles']),12)
                for frame in entry['sequenceFiles']: self.assertEqual(sha(frame['from']),sha(frame['to']))
            moved_inputs = root/'inputs-gone'; inputs.rename(moved_inputs)
            project = root/'delivery/project.fcproj'
            rendered = []
            for index in [0,6,11]:
                output = root/f'render-{index}.png'
                subprocess.run([str(binary),'--project',str(project),'render','--seconds',str(index/12),'--out',str(output)],check=True,capture_output=True)
                with Image.open(output) as image:
                    rgb = image.convert('RGB'); rendered.append(sha(output))
                    self.assertEqual(rgb.getpixel((20,15)),(0,128,0))
                    self.assertLessEqual(max(abs(a-b) for a,b in zip(rgb.getpixel((5,5)),(index*20,0,0))),2)
                    partial=rgb.getpixel((15,5)); self.assertGreater(partial[0],0); self.assertGreater(partial[1],0)
            self.assertEqual(len(set(rendered)),3)
            self.assertEqual(original,{str(p.relative_to(moved_inputs)):sha(p) for p in moved_inputs.rglob('*') if p.is_file()})
            if os.environ.get('CRAFT_FILM_SEQUENCE_CANDIDATE_EVIDENCE'):
                evidence={'schema':'craft-native-sequence-binary-candidate/v1','result':'passed','archiveSha256':receipt['archiveSha256'],'binarySha256':receipt['binarySha256'],'patchSha256':patch['patchSha256'],'frameCount':12,'sampledFrames':[0,6,11],'renderSha256':rendered,'projectSha256':sha(project),'sourceBytesPreserved':True,'sourceDirectoryUnavailable':True,'dynamicOpaqueAndPartialAlphaChecks':True,'scope':'private maintained binary; native MCP collection and rendering; not public installation, independent workflow, export or Art acceptance'}
                with Path(os.environ['CRAFT_FILM_SEQUENCE_CANDIDATE_EVIDENCE']).open('x') as stream: json.dump(evidence,stream,indent=2)
