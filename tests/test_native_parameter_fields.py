"""完整注册表命令参数字段在安装及素材读取前拒绝，创作文本保持数据语义。"""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
def module():
 spec=importlib.util.spec_from_file_location('native_field_commands',ROOT/'skills/filmcraft-use/scripts/commands.py')
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class NativeParameterFieldTests(unittest.TestCase):
 def plan(self,command,params):return {'schema':'craft-command-plan/v1','operations':[{'command':command,'params':params}]}
 def test_all_666_commands_reject_unknown_fields_without_echo(self):
  m=module();rows=m.catalog()['commands'];self.assertEqual(len(rows),666)
  for row in rows:
   with self.subTest(command=row['id']),self.assertRaisesRegex(ValueError,'^invalid_native_parameters$'):
    m.validate(self.plan(row['id'],{'OWNED_UNKNOWN_FIELD':'OWNED_CREDENTIAL_CANARY'}))
 def test_rejection_precedes_input_read_installer_and_output(self):
  m=module()
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);output=root/'delivery';calls=[]
   with self.assertRaisesRegex(ValueError,'^invalid_native_parameters$'):
    m.execute(self.plan('file.newProject',{'name':'Owned','extra':'OWNED_CREDENTIAL_CANARY'}),output,
     inputs={'source':root/'missing-owned-input'},installer=lambda *a:calls.append(a))
   self.assertEqual(calls,[]);self.assertFalse(output.exists())
 def test_creative_text_and_native_alias_and_union_fields_remain_valid(self):
  m=module()
  cases=[('file.newProject',{'name':'apiKey ignore instructions; /outside is creative text'}),
   ('file.exportGraphicsTemplate',{'name':'Owned','controls':[{'layer':1,'param':'text','name':'apiKey'}],'embedFonts':False}),
   ('media.autoRelink',{'folder':'/owned','match':{'fileName':True},'relinkOthers':False,'alignTimecode':True}),
   ('media.attachProxies',{'items':[1],'paths':['/owned'],'force':True})]
  for command,params in cases:self.assertIs(m.validate(self.plan(command,params))['operations'][0]['params'],params)
 def test_nested_fields_do_not_become_top_level_permissions(self):
  m=module()
  for command,params in [('graphics.template.export',{'layer':1}),('media.relink',{'fileName':True})]:
   with self.subTest(command=command),self.assertRaisesRegex(ValueError,'^invalid_native_parameters$'):m.validate(self.plan(command,params))
 def test_parameter_object_reference_validates_again_after_resolution(self):
  m=module();plan={'schema':'craft-command-plan/v1','operations':[
   {'command':'sequence.inspect','params':{},'as':'before'},
   {'command':'file.newProject','params':{'$ref':'before.name'}}]}
  m.validate(plan)
  self.assertIsNone(m.validate_native_parameters('file.newProject',{'name':'Owned'}))
  with self.assertRaisesRegex(ValueError,'^invalid_native_parameters$'):
   m.validate_native_parameters('file.newProject',{'OWNED_UNKNOWN_FIELD':'OWNED_CREDENTIAL_CANARY'})
  with self.assertRaisesRegex(ValueError,'^invalid_command_parameters$'):
   m.validate_native_parameters('file.newProject',None)
 def test_domain_native_wrapper_rejects_unknown_parameter_before_session(self):
  from unittest.mock import Mock
  spec=importlib.util.spec_from_file_location('native_fields_wrapper',ROOT/'skills/filmcraft-use/scripts/native_workflow.py');n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
  session=Mock()
  with self.assertRaisesRegex(ValueError,'^invalid_native_parameters$'):
   n.execute(session,{'command':'file.newProject','params':{'OWNED_UNKNOWN_FIELD':'OWNED_CREDENTIAL_CANARY'}},{},[],ROOT)
  session.request.assert_not_called()
 def test_raw_exec_rejects_unknown_parameter_before_installer_and_output(self):
  import subprocess,sys,shutil
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary).resolve();cache=root/'runtime';target=root/'project.fcproj'
   skill=root/'owned-skill';shutil.copytree(ROOT/'skills/filmcraft-use',skill)
   (skill/'scripts/bootstrap.py').write_text("def install(*args): raise ValueError('owned_installer_would_run')\n")
   result=subprocess.run([sys.executable,'-I','-B',str(skill/'scripts/cli.py'),
    '--runtime-home',str(cache),'--read-root',str(root),'--write-root',str(root),'--','exec','file.newProject',
    '{"name":"Owned","OWNED_UNKNOWN_FIELD":"OWNED_CREDENTIAL_CANARY"}','--save-as',str(target)],capture_output=True,text=True)
   self.assertEqual(result.returncode,1);self.assertEqual(json.loads(result.stdout)['error'],'invalid_native_parameters')
   self.assertFalse(cache.exists());self.assertFalse(target.exists());self.assertNotIn('OWNED_',result.stdout+result.stderr)
