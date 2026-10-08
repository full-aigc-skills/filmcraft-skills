"""桌面首用 preflight 与拥有的进程清理合同。原生应用首用需单独运行。"""
import importlib.util,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load():
 d=next(p for p in (ROOT/'skills').iterdir() if p.name.endswith('-use'));s=importlib.util.spec_from_file_location('desktop_session',d/'scripts/desktop_session.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class DesktopSessionTests(unittest.TestCase):
 def test_invalid_plan_does_not_create_output_or_install(self):
  m=load()
  with tempfile.TemporaryDirectory() as td,patch.object(m.subprocess,'Popen',side_effect=AssertionError('spawned')):
   out=Path(td)/'output'
   with self.assertRaises(ValueError):m.run({'schema':'craft-command-plan/v1','operations':[{'command':'invented.command','params':{}}]},out)
   self.assertFalse(out.exists())
 def test_owned_session_start_failure_terminates_only_its_process(self):
  m=load()
  class Process:
   pid=123;returncode=None;terminated=0
   def poll(self):return self.returncode
   def terminate(self):self.terminated+=1;self.returncode=0
   def wait(self,timeout):return self.returncode
  p=Process()
  with tempfile.TemporaryDirectory() as td,patch.object(m.subprocess,'Popen',return_value=p),patch.object(m,'owned_listener',side_effect=RuntimeError('readiness failure')):
   session=m.OwnedSession(['native','mcp'],{'executable':'app'},'effectcraft',Path(td),1234)
   with self.assertRaisesRegex(RuntimeError,'readiness failure'):session.__enter__()
   self.assertEqual(p.terminated,1);self.assertTrue(session.stopped)
 def test_unsupported_platform_has_no_output(self):
  m=load();commands=m.load('commands');command=commands.catalog()['commands'][0]['id']
  with tempfile.TemporaryDirectory() as td,patch.object(m.platform,'system',return_value='Linux'):
   out=Path(td)/'output'
   with self.assertRaisesRegex(ValueError,'unsupported_desktop_platform'):m.run({'schema':'craft-command-plan/v1','operations':[{'command':command,'params':{}}]},out)
   self.assertFalse(out.exists())

import os,json,hashlib,shutil,subprocess
@unittest.skipUnless(os.environ.get('CRAFT_DESKTOP_SESSION_FIRST_USE')=='1','native desktop first use is opt-in')
class OwnedDesktopPublicFirstUse(unittest.TestCase):
 def test_single_skill_empty_cache_install_launch_save_reopen_and_cleanup(self):
  source=Path(os.environ['CRAFT_DESKTOP_SESSION_SKILL'])
  def hashes(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
  original=hashes(source)
  with tempfile.TemporaryDirectory(prefix='craft-owned-desktop-test-') as td:
   root=Path(td);skill=root/'.agents/skills'/source.name;skill.parent.mkdir(parents=True);shutil.copytree(source,skill);before=hashes(skill);out=root/'output';runtime=root/'runtime';plan=skill/'examples/desktop-first-use.json'
   result=subprocess.run(['/opt/anaconda3/bin/python3','-I','-B',str(skill/'scripts/desktop.py'),'run',str(plan),'--read-root',str(root.resolve()),'--write-root',str(root.resolve()),'--output',str(out),'--runtime-home',str(runtime)],capture_output=True,text=True,timeout=700,env=dict(os.environ,PATH='/usr/bin:/bin'))
   self.assertEqual(result.returncode,0,result.stdout+result.stderr)
   commands=json.loads((out/'success.json').read_text());desktop=json.loads((out/'desktop-session.json').read_text());self.assertEqual(commands['result'],'PASS');self.assertTrue(desktop['ownedProcessesStopped']);self.assertTrue(desktop['listenerOwnedByPID']);self.assertEqual(desktop['sessionsStarted'],1);self.assertFalse(desktop['desktop']['reused']);self.assertEqual(hashes(source),original);self.assertEqual(hashes(skill),before)
   capabilities=commands['capabilitySnapshot'];self.assertEqual(capabilities['mode'],'bridge');self.assertEqual(capabilities['desktop']['status'],'verified');self.assertEqual(capabilities['desktop']['binarySha256'],desktop['desktop']['binarySha256']);self.assertEqual(capabilities['runtime']['binarySha256'],commands['runtimeSha256']);used={step['command'] for step in commands['steps']};self.assertTrue(all(row['parameterStatus']=='match' for row in capabilities['commands'] if row['id'] in used))
   projects=[p for p in out.iterdir() if p.suffix in ('.fcproj','.ecproj','.pcraft','.vectorcraft')];self.assertEqual(len(projects),1);self.assertGreater(projects[0].stat().st_size,0);self.assertEqual(commands['steps'][-1]['state'],'succeeded')
   proof={'schema':'craft-owned-desktop-public-first-use/v1','result':'PASS','skill':source.name,'domain':desktop['domain'],'emptyPublicRuntime':True,'standaloneSkillUnchanged':True,'ownedListenerVerified':True,'ownedProcessesStopped':True,'desktopBinarySha256':desktop['desktop']['binarySha256'],'cliBinarySha256':commands['runtimeSha256'],'nativeProject':{'name':projects[0].name,'sha256':hashlib.sha256(projects[0].read_bytes()).hexdigest(),'bytes':projects[0].stat().st_size},'operations':len(commands['steps']),'finalInspection':commands['steps'][-1]['result'],'installerSha256':before['scripts/desktop.py'],'sessionSha256':before['scripts/desktop_session.py'],'scope':'single source skill copy, public desktop+CLI cold install, owned GUI command workflow native save/reopen and cleanup; not fixed released skill or all commands'}
   proof['capabilitySnapshot']=capabilities;proof['skillFiles']=before
   proof['contractDifferences']=[row for row in capabilities['commands'] if row['parameterStatus']!='match'];proof['fullPerCommandAcceptance']='NOT_RUN'
   if desktop['domain']=='filmcraft':
    from PIL import Image
    frame=root/'frame0001.png';Image.new('RGB',(32,32),'red').save(frame)
    rejected_plan=root/'bridge-contract.json';rejected_plan.write_text(json.dumps({'schema':'craft-command-plan/v1','operations':[{'command':'file.newProject','params':{'name':'must-not-create'}},{'command':'file.importImageSequence','params':{'path':str(frame)}}]}));rejected_output=root/'rejected'
    rejected=subprocess.run(['/opt/anaconda3/bin/python3','-I','-B',str(skill/'scripts/desktop.py'),'run',str(rejected_plan),'--read-root',str(root.resolve()),'--write-root',str(root.resolve()),'--output',str(rejected_output),'--runtime-home',str(runtime)],capture_output=True,text=True,timeout=120,env=dict(os.environ,PATH='/usr/bin:/bin'))
    self.assertEqual(rejected.returncode,1,rejected.stdout+rejected.stderr);failure=json.loads((rejected_output/'failure.json').read_text());cleanup=json.loads((rejected_output/'desktop-session.json').read_text());self.assertIn('capability_contract_drift: file.importImageSequence',failure['error']);self.assertEqual(failure['steps'],[]);self.assertTrue(cleanup['ownedProcessesStopped']);self.assertFalse(list(rejected_output.glob('*.fcproj')));self.assertEqual(hashes(skill),before)
    proof['bridgeContractRejection']={'result':'PASS','command':'file.importImageSequence','error':failure['error'],'edits':0,'ownedProcessesStopped':cleanup['ownedProcessesStopped'],'parameterCheck':next(row for row in failure['capabilitySnapshot']['commands'] if row['id']=='file.importImageSequence')}
   if (out/'preview.svg').exists():proof['svgSha256']=hashlib.sha256((out/'preview.svg').read_bytes()).hexdigest()
   Path(os.environ['CRAFT_DESKTOP_SESSION_REPORT']).write_text(json.dumps(proof,indent=2)+'\n')

class DesktopPlanAndInterruptTests(unittest.TestCase):
 def test_duplicate_and_nonfinite_plan_json_rejected(self):
  m=load()
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'plan.json'
   for text in ['{"schema":"bad","schema":"craft-command-plan/v1","operations":[]}', '{"schema":"craft-command-plan/v1","operations":[],"extra":NaN}']:
    p.write_text(text)
    with self.assertRaises(ValueError):m.read_plan(p)
 def test_interruption_preserves_completed_step_and_unknown_request(self):
  m=load();commands=m.load('commands');identifier=commands.catalog()['commands'][0]['id']
  def interrupted(plan,output,*args,**kwargs):
   output.mkdir();commands.write(output/'journal.json',{'schema':'craft-command-receipt/v1','result':'running','steps':[{'state':'succeeded'},{'state':'started'}]});raise KeyboardInterrupt()
  original=m.load
  with tempfile.TemporaryDirectory() as td,patch.object(m,'load',side_effect=lambda name:commands if name=='commands' else original(name)),patch.object(commands,'execute',side_effect=interrupted),patch.object(m.platform,'system',return_value='Darwin'),patch.object(m.platform,'machine',return_value='arm64'):
   out=Path(td)/'output'
   with self.assertRaises(KeyboardInterrupt):m.run({'schema':'craft-command-plan/v1','operations':[{'command':identifier,'params':{}}]},out)
   import json
   receipt=json.loads((out/'failure.json').read_text());self.assertEqual(receipt['result'],'unknown');self.assertEqual([s['state'] for s in receipt['steps']],['succeeded','unknown']);proof=json.loads((out/'desktop-session.json').read_text());self.assertTrue(proof['ownedProcessesStopped']);self.assertEqual(proof['result'],'unknown')

class ReservedDesktopOutputTests(unittest.TestCase):
 def test_desktop_metadata_cannot_be_named_as_deliverable(self):
  commands=load().load('commands')
  for name in ['desktop-session.json','desktop.log','.desktop-data/preferences.json','artcraft-domain-command.json']:
   with self.subTest(name=name):
    with self.assertRaisesRegex(ValueError,'invalid_output_path'):commands.output_path(name)
  self.assertEqual(commands.output_path('assets/desktop.log'),'assets/desktop.log')
