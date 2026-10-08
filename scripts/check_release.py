#!/usr/bin/env python3
"""离线发行检查：每个环境用例明确NOT_RUN，必需单元不能跳过。"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest
from urllib.parse import unquote,urlsplit
ROOT=Path(__file__).resolve().parents[1]


def validate_test_rows(rows,policy):
 ids=[r['id'] for r in rows]
 if len(ids)!=len(set(ids)) or not rows:raise ValueError('test_inventory_invalid')
 by_id={r['id']:r for r in rows};allowed={r['id']:r['reason'] for r in policy['environmentTests']}
 if not set(allowed).issubset(by_id):raise ValueError('environment_inventory_missing')
 if any(by_id.get(name,{}).get('status')!='PASS' for name in policy['requiredTests']):raise ValueError('required_test_not_passed')
 for row in rows:
  if row['status']=='NOT_RUN' and allowed.get(row['id'])!=row.get('reason'):raise ValueError('undeclared_environment_skip')
  if row['status'] not in ('PASS','NOT_RUN'):raise ValueError('test_failed')


def validate_links(root):
 root=Path(root).resolve();count=0
 for home in sorted((root/'skills').iterdir()):
  if not home.is_dir():continue
  for path in home.rglob('*.md'):
   for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',path.read_text()):
    parsed=urlsplit(target.strip('<>'))
    if parsed.scheme or not parsed.path:continue
    destination=(path.parent/unquote(parsed.path)).resolve()
    if destination.is_relative_to(root/'skills') and not destination.is_relative_to(home):raise ValueError('cross_skill_link: '+str(path.relative_to(root)))
    if not destination.is_relative_to(root) or not destination.exists():raise ValueError('broken_or_escaping_link: '+str(path.relative_to(root)))
    count+=1
 return count


def validate_workflow(text):
 if 'python3 -I -B scripts/check_release.py --output' not in text or any(word in text for word in ('hashFiles','continue-on-error')):raise ValueError('required_workflow_conditional')
 if any(line.strip()!='if: always()' for line in text.splitlines() if re.match(r'^\s*if:',line)):raise ValueError('required_workflow_conditional')


def metadata(root):
 validate_workflow((root/'.github/workflows/offline.yml').read_text())
 suite=json.loads((root/'skill-suite.json').read_text());manifest=json.loads((root/'.claude-plugin/plugin.json').read_text())
 if suite['version']!=manifest['version'] or manifest['name']!='filmcraft-skills':raise ValueError('metadata_identity_mismatch')
 names=[r['name'] for r in suite['skills']]
 if len(names)!=len(set(names)) or set(names)!={p.name for p in (root/'skills').iterdir() if p.is_dir()}:raise ValueError('skill_inventory_mismatch')
 for name in names:
  text=(root/'skills'/name/'SKILL.md').read_text()
  if len(text.splitlines())>=500 or not re.search(r'^name: '+re.escape(name)+r'\s*$',text,re.M) or not re.search(r'^description: .+',text,re.M):raise ValueError('skill_entry_invalid: '+name)
 for name in ('README.md','README.zh-CN.md'):
  if '`'+suite['version']+'`' not in (root/name).read_text():raise ValueError('readme_version_mismatch')
 return {'version':suite['version'],'skills':len(names)}


class EvidenceResult(unittest.TextTestResult):
 def __init__(self,*args):super().__init__(*args);self.rows=[]
 def addSuccess(self,test):super().addSuccess(test);self.rows.append({'id':test.id(),'status':'PASS'})
 def addSkip(self,test,reason):super().addSkip(test,reason);self.rows.append({'id':test.id(),'status':'NOT_RUN','reason':reason})
 def addFailure(self,test,err):super().addFailure(test,err);self.rows.append({'id':test.id(),'status':'FAIL'})
 def addError(self,test,err):super().addError(test,err);self.rows.append({'id':test.id(),'status':'FAIL'})
 def addSubTest(self,test,subtest,err):
  super().addSubTest(test,subtest,err)
  if err is not None:
   row=next((r for r in self.rows if r['id']==test.id()),None)
   if row is None:row={'id':test.id(),'status':'FAIL','failedSubtests':0};self.rows.append(row)
   row['failedSubtests']+=1
 def addExpectedFailure(self,test,err):super().addExpectedFailure(test,err);self.rows.append({'id':test.id(),'status':'FAIL','reason':'expected failure is not completed behavior'})
 def addUnexpectedSuccess(self,test):super().addUnexpectedSuccess(test);self.rows.append({'id':test.id(),'status':'FAIL'})


def verify(output):
 output=Path(output).absolute()
 if output.exists() or output.is_symlink():raise ValueError('output_exists')
 output.mkdir(parents=True,mode=0o700);checks=[]
 report={'schema':'filmcraft-source-offline-checks/v1','result':'FAIL','layer':'source','scope':'offline checks only; no native/host/platform acceptance',
         'revision':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),
         'pythonVersion':sys.version.split()[0],'checks':checks,'native':'NOT_RUN','host':'NOT_RUN','realMedia':'NOT_RUN','platformAcceptance':'NOT_RUN'}
 tracked=subprocess.check_output(['git','-C',str(ROOT),'ls-files','--cached','--others','--exclude-standard','-z'])
 report['sourceFilesSha256']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sorted(set(tracked.decode().split('\0')))
  if name and (ROOT/name).is_file() and (name.startswith(('scripts/','tests/','skills/','.github/')) or name in ('skill-suite.json','.claude-plugin/plugin.json'))}
 try:
  checks.append({'id':'metadata','status':'PASS','details':metadata(ROOT)})
  checks.append({'id':'links','status':'PASS','checked':validate_links(ROOT)})
  command=[sys.executable,'-I','-B',str(ROOT/'scripts/sync_skill_suite.py'),'--check']
  done=subprocess.run(command,capture_output=True,text=True,cwd=ROOT)
  text=(done.stdout+done.stderr).replace(str(ROOT),'[SOURCE_ROOT]');(output/'resources.log').write_text(text)
  checks.append({'id':'resources-catalog-entry','status':'PASS' if done.returncode==0 else 'FAIL','command':['python','-I','-B','scripts/sync_skill_suite.py','--check'],'log':'resources.log','logSha256':hashlib.sha256((output/'resources.log').read_bytes()).hexdigest()})
  if done.returncode:raise ValueError('resources_or_catalog_failed')
  suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'));stream=io.StringIO()
  result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=EvidenceResult).run(suite)
  text=stream.getvalue().replace(str(ROOT),'[SOURCE_ROOT]').replace(str(Path.home()),'[USER_HOME]')
  text=re.sub(r'(?:/private)?/var/folders/[^\s"\']+','[TEMP_PATH]',text);(output/'unittest.log').write_text(text)
  report['tests']=result.rows;report['counts']={'tests':result.testsRun,'pass':sum(r['status']=='PASS' for r in result.rows),'fail':sum(r['status']=='FAIL' for r in result.rows),'failureEvents':len(result.failures)+len(result.errors)+len(result.unexpectedSuccesses),'environmentNotRun':len(result.skipped)}
  validate_test_rows(result.rows,json.loads((ROOT/'scripts/offline-test-policy.json').read_text()))
  checks.append({'id':'offline-unit-scenario-contract-entry','status':'PASS','executor':'unittest.TextTestRunner discovery of tests/test_*.py','log':'unittest.log','logSha256':hashlib.sha256((output/'unittest.log').read_bytes()).hexdigest()})
  if not result.wasSuccessful():raise ValueError('unit_tests_failed')
  report['result']='PASS'
 except Exception as error:
  report['error']=str(error).replace(str(ROOT),'[SOURCE_ROOT]')
 finally:
  (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 return report


if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
 result=verify(parser.parse_args().output);print(json.dumps({'result':result['result'],'counts':result.get('counts'),'error':result.get('error')}));raise SystemExit(0 if result['result']=='PASS' else 1)
