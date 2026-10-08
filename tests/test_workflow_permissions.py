"""公开工作流目录策略必须在读取与安装前生效。"""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT=Path(__file__).resolve().parents[1]/'skills/filmcraft-use/scripts/workflow.py'

class WorkflowPermissionsTests(unittest.TestCase):
 def setUp(self):
  spec=importlib.util.spec_from_file_location('permission_workflow',SCRIPT)
  self.workflow=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.workflow)
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name).resolve();self.allowed=self.root/'allowed';self.allowed.mkdir()
  self.outside=self.root/'outside';self.outside.mkdir()
  self.policy={'schema':'filmcraft-execution-permissions/v1','readRoots':[str(self.allowed)],'writeRoots':[str(self.allowed)]}
  self.plan={'document':{'name':'Owned permission test','width':640,'height':360,'frameRate':{'num':24,'den':1}},'operations':[]}
 def test_public_cli_requires_independent_policy_before_plan_read(self):
  run=subprocess.run([sys.executable,'-I','-B',str(SCRIPT),str(self.outside/'missing.json'),'--output',str(self.allowed/'delivery')],capture_output=True,text=True)
  self.assertEqual(run.returncode,1);self.assertEqual(json.loads(run.stdout)['error'],'execution_permissions_required')
 def test_public_cli_refuses_plan_outside_roots_without_reading_it(self):
  run=subprocess.run([sys.executable,'-I','-B',str(SCRIPT),str(self.outside/'missing.json'),'--output',str(self.allowed/'delivery'),'--read-root',str(self.allowed),'--write-root',str(self.allowed)],capture_output=True,text=True)
  self.assertEqual(run.returncode,1);self.assertEqual(json.loads(run.stdout)['error'],'permission_read_denied')
 def test_outside_output_refused_before_install_or_creation(self):
  with self.assertRaisesRegex(ValueError,'^permission_write_denied$'):
   self.workflow.execute(self.plan,self.outside/'delivery',permissions=self.policy)
  self.assertFalse((self.outside/'delivery').exists())
 def test_outside_asset_refused_before_hash_or_install(self):
  self.plan['assets']={'still':{'path':str(self.outside/'missing.png'),'sha256':'0'*64}}
  with self.assertRaisesRegex(ValueError,'^permission_read_denied$'):
   self.workflow.execute(self.plan,self.allowed/'delivery',permissions=self.policy)
  self.assertFalse((self.allowed/'delivery').exists())
 def test_outside_source_refused_before_manifest_read(self):
  with self.assertRaisesRegex(ValueError,'^permission_read_denied$'):
   self.workflow.execute(self.plan,self.allowed/'delivery',source=self.outside/'source',permissions=self.policy)
 def test_cli_asset_assignment_checked_before_digest_read(self):
  path=self.allowed/'plan.json';path.write_text(json.dumps(self.plan))
  run=subprocess.run([sys.executable,'-I','-B',str(SCRIPT),str(path),'--output',str(self.allowed/'delivery'),'--read-root',str(self.allowed),'--write-root',str(self.allowed),'--asset','still='+str(self.outside/'missing.png')],capture_output=True,text=True)
  self.assertEqual(run.returncode,1);self.assertEqual(json.loads(run.stdout)['error'],'permission_read_denied')

 def test_full_command_public_run_requires_policy_before_plan_read(self):
  script=SCRIPT.with_name('commands.py')
  run=subprocess.run([sys.executable,'-I','-B',str(script),'run',str(self.outside/'missing.json'),'--output',str(self.allowed/'delivery')],capture_output=True,text=True)
  self.assertEqual(run.returncode,1);self.assertEqual(json.loads(run.stdout)['error'],'execution_permissions_required')
 def test_full_command_public_run_refuses_plan_outside_roots(self):
  script=SCRIPT.with_name('commands.py')
  run=subprocess.run([sys.executable,'-I','-B',str(script),'run',str(self.outside/'missing.json'),'--output',str(self.allowed/'delivery'),'--read-root',str(self.allowed),'--write-root',str(self.allowed)],capture_output=True,text=True)
  self.assertEqual(run.returncode,1);self.assertEqual(json.loads(run.stdout)['error'],'permission_read_denied')
