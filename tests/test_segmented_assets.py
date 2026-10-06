"""分段生产检查点的有界消费、来源保留及完整性失败。"""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from test_sequence_assets import fixture

def segmented(root):
    records=[];parts=[]
    for i in range(2):
        child=root/f'segment_{i:05d}';child.mkdir();path,value=fixture(child)
        part={'firstFrame':i*2,'frameCount':2,'start':{'num':i,'den':6},'end':{'num':i+1,'den':6}}
        # 最终有理秒数必须约分。
        from fractions import Fraction
        for k in ['start','end']:
            q=Fraction(part[k]['num'],part[k]['den']);part[k]={'num':q.numerator,'den':q.denominator}
        parts.append(part);records.append(dict(part,location=f'{child.name}/sequence.json',sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    value={'schema':'craft-segmented-render-checkpoint/v1','state':'verified','binding':{'projectSha256':'a'*64,'runtimeSha256':'b'*64,'composition':{'name':'Intro','width':2,'height':1,'frameRate':12,'duration':'1/3'},'chunkBytes':16,'parts':parts},'frameCount':4,'frameRate':{'num':12,'den':1},'segments':records}
    path=root/'segments.json';path.write_text(json.dumps(value));return path,value

class SegmentedAssetTests(unittest.TestCase):
    def setUp(self):
        import importlib.util
        path=Path(__file__).resolve().parents[1]/'skills/filmcraft-use/scripts/sequence_assets.py'
        spec=importlib.util.spec_from_file_location('segment_assets',path);self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
    def verify(self,path):return self.module.validate_sequence(path,self.module.digest(path))
    def test_copy_segments_normalizes_global_frames_and_preserves_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();source=root/'source';source.mkdir();path,value=segmented(source);expected=self.module.digest(path)
            before={p.relative_to(source).as_posix():self.module.digest(p) for p in source.rglob('*') if p.is_file()}
            target=self.module.copy_segmented_sequence(path,expected,root/'copy');result=self.verify(target)
            self.assertEqual(result['schema'],'filmcraft-collected-sequence/v1');self.assertEqual(result['frameCount'],4);self.assertEqual(result['sourceSequenceSha256'],expected)
            self.assertEqual([f['index'] for f in result['frames']],[0,1,2,3]);self.assertEqual([s['firstFrame'] for s in result['segments']],[0,2])
            self.assertEqual(before,{p.relative_to(source).as_posix():self.module.digest(p) for p in source.rglob('*') if p.is_file()})
            moved=root/'moved';target.parent.rename(moved);self.assertEqual(self.verify(moved/'sequence.json'),result)

    def test_gap_overlap_wrong_rational_and_child_digest_rejected_before_output(self):
        for fault in ['gap','overlap','time','childHash']:
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as temp:
                root=Path(temp).resolve();source=root/'source';source.mkdir();path,value=segmented(source)
                if fault=='gap':value['segments'][1]['firstFrame']=3
                elif fault=='overlap':value['segments'][1]['firstFrame']=1
                elif fault=='time':value['segments'][1]['start']={'num':1,'den':12}
                else:value['segments'][1]['sha256']='0'*64
                path.write_text(json.dumps(value))
                with self.assertRaises(ValueError):self.module.copy_segmented_sequence(path,self.module.digest(path),root/'copy')
                self.assertFalse((root/'copy').exists())

    def test_bad_frame_symlink_and_unverified_checkpoint_rejected(self):
        for fault in ['badFrame','symlink','state']:
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as temp:
                root=Path(temp).resolve();source=root/'source';source.mkdir();path,value=segmented(source)
                if fault=='badFrame':(source/'segment_00001/frame_00000.png').write_bytes(b'bad')
                elif fault=='symlink':p=source/'segment_00001/frame_00000.png';p.unlink();p.symlink_to(source/'segment_00000/frame_00000.png')
                else:value['state']='partial';path.write_text(json.dumps(value))
                with self.assertRaises(ValueError):self.module.copy_segmented_sequence(path,self.module.digest(path),root/'copy')
                self.assertFalse((root/'copy').exists())

    def test_malformed_binding_shapes_return_domain_error_without_output(self):
        for fault in ['missingDuration','partsBoolean','startString','booleanRate']:
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as temp:
                root=Path(temp).resolve();source=root/'source';source.mkdir();path,value=segmented(source)
                if fault=='missingDuration':del value['binding']['composition']['duration']
                elif fault=='partsBoolean':value['binding']['parts']=True
                elif fault=='startString':value['segments'][0]['start']='0'
                else:value['frameRate']={'num':True,'den':1}
                path.write_text(json.dumps(value))
                with self.assertRaises(ValueError):self.module.copy_segmented_sequence(path,self.module.digest(path),root/'copy')
                self.assertFalse((root/'copy').exists())
