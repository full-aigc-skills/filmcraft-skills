"""登记的动画序列必须绑定完整帧集、真实像素与有理时间基。"""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import shutil
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT/'skills/filmcraft-use/scripts/sequence_assets.py'


def png(path):
    def chunk(kind, data): return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
    pixels=bytes([255,0,0,128,0,0,0,0])
    path.write_bytes(bytes.fromhex('89504e470d0a1a0a')+chunk(b'IHDR',struct.pack('>IIBBBBB',2,1,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0'+pixels))+chunk(b'IEND',b''))
    return hashlib.sha256(pixels).hexdigest()


def fixture(root):
    frames=[]
    for index in range(2):
        path=root/f'frame_{index:05d}.png'; pixels=png(path)
        frames.append({'index':index,'location':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'alphaExtrema':[0,128],'rgbaSha256':pixels})
    value={'schema':'craft-image-sequence/v1','encoding':'png','width':2,'height':1,'bitDepth':8,'channels':'rgba','alphaRepresentation':'straight-png','colorSpace':'unknown','frameRate':{'num':12,'den':1},'frameCount':2,'durationTicks':'2','timeBase':{'num':1,'den':12},'frames':frames}
    path=root/'sequence.json';path.write_text(json.dumps(value));return path,value


class SequenceAssetTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('sequence_assets',MODULE)
        self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)

    def verify(self,path): return self.module.validate_sequence(path,hashlib.sha256(path.read_bytes()).hexdigest())

    def test_real_frames_and_rational_timebase_and_copy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); source=root/'source';source.mkdir();path,value=fixture(source)
            self.assertEqual(self.verify(path),value)
            target=root/'copy';copied=self.module.copy_sequence(path,hashlib.sha256(path.read_bytes()).hexdigest(),target)
            self.assertEqual(copied,target/'sequence.json');self.assertEqual(self.verify(copied),value)
            with self.assertRaisesRegex(ValueError,'sequence_output_exists'):self.module.copy_sequence(path,hashlib.sha256(path.read_bytes()).hexdigest(),target)

    def test_missing_extra_symlink_and_digest_conflict_are_rejected(self):
        for fault in ['missing','extra','symlink','digest']:
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary);path,value=fixture(root);frame=root/'frame_00001.png'
                if fault=='missing':frame.unlink()
                elif fault=='extra':png(root/'frame_00002.png')
                elif fault=='symlink':frame.unlink();frame.symlink_to(root/'frame_00000.png')
                else:frame.write_bytes(frame.read_bytes()+b'bad')
                with self.assertRaises(ValueError):self.verify(path)

    def test_wrong_duration_rate_pixels_and_resource_budget_rejected(self):
        for key,bad in [('durationTicks','1'),('timeBase',{'num':1,'den':30}),('frameRate',{'num':241,'den':1}),('frameCount',True),('width',16384)]:
            with self.subTest(key=key),tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary);path,value=fixture(root);value[key]=bad;path.write_text(json.dumps(value))
                with self.assertRaises(ValueError):self.verify(path)
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);path,value=fixture(root);value['frames'][0]['alphaExtrema']=[0,255];path.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError,'sequence_frame_metadata_mismatch'):self.verify(path)

    def test_single_installed_skill_has_no_sibling_resource_dependency(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);installed=root/'.agents/skills/filmcraft-cli-media'
            shutil.copytree(ROOT/'skills/filmcraft-cli-media',installed,ignore=shutil.ignore_patterns('__pycache__'))
            original={str(p.relative_to(installed)):hashlib.sha256(p.read_bytes()).hexdigest() for p in installed.rglob('*') if p.is_file()}
            spec=importlib.util.spec_from_file_location('installed_sequence_assets',installed/'scripts/sequence_assets.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            source=root/'source';source.mkdir();path,value=fixture(source)
            self.assertEqual(module.validate_sequence(path,hashlib.sha256(path.read_bytes()).hexdigest()),value)
            self.assertEqual(original,{str(p.relative_to(installed)):hashlib.sha256(p.read_bytes()).hexdigest() for p in installed.rglob('*') if p.is_file()})

    def test_budget_and_noninteger_timebase_rejected_without_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'source';source.mkdir();path,value=fixture(source)
            value['width']=16384;value['height']=16384;path.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError,'sequence_frame_budget_exceeded'):self.module.copy_sequence(path,hashlib.sha256(path.read_bytes()).hexdigest(),root/'output')
            self.assertFalse((root/'output').exists())
            path,value=fixture(source);value['timeBase']['num']=True;path.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError,'sequence_timing_mismatch'):self.verify(path)

    def test_manifest_digest_and_duplicate_fields_rejected_before_copy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'source';source.mkdir();path,value=fixture(source)
            with self.assertRaisesRegex(ValueError,'sequence_manifest_digest_mismatch'):self.module.copy_sequence(path,'0'*64,root/'target')
            self.assertFalse((root/'target').exists())
            path.write_text('{"schema":"craft-image-sequence/v1","schema":"fake"}')
            with self.assertRaisesRegex(ValueError,'sequence_duplicate_field'):self.verify(path)
