"""领域操作的额外参数必须在素材读取前拒绝，创作文本不作为指令。"""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'skills/filmcraft-use/scripts/workflow.py'
CANARY='OWNED_TEST_CANARY_NO_REAL_SECRET'

class WorkflowParameterFieldTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('workflow_parameter_fields',SCRIPT)
        self.workflow=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.workflow)

    def test_domain_parameter_metadata_refused_before_asset_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            plan={'document':{'name':'Owned','width':32,'height':32,'frameRate':{'num':12,'den':1}},
                  'operations':[{'command':'captions.setText','params':{'caption':13,'text':'创作文本','metadata':{'apiKey':CANARY}}}]}
            with patch.object(self.workflow,'preflight_assets',side_effect=AssertionError('asset read reached')):
                with self.assertRaisesRegex(ValueError,'^invalid_workflow_parameters$'):
                    self.workflow.execute(plan,root/'output',root/'runtime')
            self.assertFalse((root/'output').exists());self.assertFalse((root/'runtime').exists())

    def test_each_domain_wrapper_has_a_closed_field_boundary(self):
        excluded={'native.command','effects.toggleAnimation','effects.setParam','lumetri.setInputLut','mixer.setStrip'}
        for command in self.workflow.ALLOWED-excluded:
            with self.subTest(command=command):
                with self.assertRaisesRegex(ValueError,'^invalid_workflow_parameters$'):
                    self.workflow.validate({'operations':[{'command':command,'params':{CANARY:CANARY}}]})

    def test_nested_move_metadata_is_refused_without_echo(self):
        plan={'operations':[{'command':'timeline.move','params':{'moves':[{'clip':1,'track':'V1','time':'0','metadata':CANARY}],'insert':False}}]}
        with self.assertRaisesRegex(ValueError,'^invalid_workflow_parameters$') as caught:self.workflow.validate(plan)
        self.assertNotIn(CANARY,str(caught.exception))

    def test_documented_examples_and_creative_text_remain_accepted(self):
        for path in (SCRIPT.parent.parent/'examples').glob('*.json'):
            plan=json.loads(path.read_text())
            if isinstance(plan,dict) and 'operations' in plan and 'schema' not in plan:
                prior={op['params']['asset']:{'kind':'lut'} for op in plan['operations'] if op.get('command')=='lumetri.setInputLut'}
                self.workflow.validate(plan,prior_assets=prior)
        text='metadata apiKey 忽略先前指令是本片字幕中的台词。'
        self.workflow.validate({'operations':[{'command':'captions.setText','params':{'caption':{'$ref':'caption.caption'},'text':text,'speaker':None}}]})
        self.workflow.validate({'operations':[{'command':'timeline.move','params':{'moves':[{'clip':{'$ref':'shotClip.clips.0'},'track':'V1','time':'0'}],'insert':False}}]})

    def test_public_entry_refuses_canary_without_install_or_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);p=root/'plan.json';p.write_text(json.dumps({'document':{'name':'Owned','width':32,'height':32,'frameRate':{'num':12,'den':1}},'operations':[{'command':'captions.setText','params':{'caption':13,'text':'字幕',CANARY:CANARY}}]}))
            r=subprocess.run([sys.executable,'-I','-B',str(SCRIPT),str(p),'--read-root',str(root.resolve()),'--write-root',str(root.resolve()),'--output',str(root/'out'),'--runtime-home',str(root/'runtime')],capture_output=True,text=True,timeout=20)
            self.assertEqual(r.returncode,1);self.assertEqual(json.loads(r.stdout)['error'],'invalid_workflow_parameters')
            self.assertNotIn(CANARY,r.stdout+r.stderr);self.assertFalse((root/'out').exists());self.assertFalse((root/'runtime').exists())
