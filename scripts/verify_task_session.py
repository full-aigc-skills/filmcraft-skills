#!/usr/bin/env python3
"""公开JSONL任务入口真实连续运行验收；每个模式一次启动，来源只读。"""
import argparse
import hashlib
import json
from pathlib import Path
import select
import subprocess
import sys


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def project(path):
    value=json.loads(path.read_text());value['project']['name']='SAVE_AS_NAME'
    value['project']['root']['name']='SAVE_AS_NAME';return value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill',type=Path,required=True)
    parser.add_argument('--runtime-home',type=Path,required=True)
    parser.add_argument('--fixture-audit',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();skill=args.skill.resolve();home=args.runtime_home.resolve();audit=args.fixture_audit.resolve();root=args.output.resolve()
    if root.exists():raise ValueError('output_exists')
    root.mkdir(mode=0o700);results=[]
    for mode in ['headless','bridge']:
        work=root/mode;fixture=audit/mode/'fixture/baseline.fcproj';source_sha=sha(fixture)
        argv=[sys.executable,'-I','-B','-u',str(skill/'scripts/task_session.py'),'--output',str(work),'--runtime-home',str(home),
              '--read-root',str(skill),'--read-root',str(audit),'--write-root',str(root),'--write-root',str(home),
              '--protect-input',str(audit),'--mode',mode]
        with (root/(mode+'-stderr.private.log')).open('w') as errors:
            child=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=errors,text=True,bufsize=1)
            def receive():
                if not select.select([child.stdout],[],[],180)[0]:raise TimeoutError('task_receipt_timeout: no replay')
                line=child.stdout.readline()
                if not line:raise RuntimeError('task_cli_exited: '+str(child.poll()))
                return json.loads(line)
            def send(name,operations,inputs=None):
                request={'name':name,'plan':{'schema':'craft-command-plan/v1','operations':operations}}
                if inputs:request['inputs']=inputs
                child.stdin.write(json.dumps(request)+'\n');child.stdin.flush();receipt=receive()
                (root/(mode+'-'+name+'-receipt.private.json')).write_text(json.dumps(receipt,indent=2)+'\n')
                assert receipt['result']=='PASS',receipt.get('error')
                return receipt
            def op(command,params):return {'command':command,'params':params}
            try:
                assert receive()['result']=='READY'
                first=send('open',[op('file.open',{'path':{'$ref':'source.path'}}),op('sequence.inspect',{}),
                    op('file.saveAs',{'path':{'$output':'baseline.fcproj'}})],{'source':str(fixture)})
                state=first['steps'][1]['result'];target=state['video'][1]['items'][0]['clip']
                base=project(work/'open/baseline.fcproj')
                seq=next(v['kind']['Sequence'] for v in base['project']['items'].values() if 'Sequence' in v['kind'])
                target_clip=next(c for t in seq['video_tracks'] for c in t['items'] if c['id']==target)
                original_name=target_clip['name']
                send('edit',[op('sequence.inspect',{}),op('clip.rename',{'clip':target,'name':'Task revision'}),
                    op('file.saveAs',{'path':{'$output':'changed.fcproj'}})])
                expected=json.loads(json.dumps(base));expected_seq=next(v['kind']['Sequence'] for v in expected['project']['items'].values() if 'Sequence' in v['kind'])
                next(c for t in expected_seq['video_tracks'] for c in t['items'] if c['id']==target)['name']='Task revision'
                assert project(work/'edit/changed.fcproj')==expected
                send('reopen',[op('file.closeAllProjects',{'force':True}),op('file.open',{'path':{'$ref':'source.path'}}),
                    op('sequence.inspect',{}),op('file.saveAs',{'path':{'$output':'reopened.fcproj'}})],{'source':str(work/'edit/changed.fcproj')})
                assert project(work/'reopen/reopened.fcproj')==expected
                send('restore',[op('clip.rename',{'clip':target,'name':original_name}),
                    op('file.saveAs',{'path':{'$output':'restored.fcproj'}}),op('file.closeAllProjects',{'force':True}),
                    op('file.open',{'path':str(work/'restore/restored.fcproj')}),op('sequence.inspect',{})])
                assert project(work/'restore/restored.fcproj')==base
                assert sha(fixture)==source_sha
                if mode=='bridge':
                    child.stdin.write('{"action":"close"}\n');child.stdin.flush();assert receive()=={'result':'CLOSED'}
                child.stdin.close();assert child.wait(timeout=30)==0
                proof=json.loads((work/'task-session.json').read_text())
                assert proof['sessionsStarted']==1 and proof['singleProcessIdentity'] and proof['ownedProcessesStopped']
                assert proof['closed'] and not proof['stopped'] and len(proof['plans'])==4
                result={'mode':mode,'result':'PASS','stages':4,'cliPid':child.pid,'session':proof,
                    'sourceSha256':source_sha,'baselineSha256':sha(work/'open/baseline.fcproj'),
                    'changedSha256':sha(work/'edit/changed.fcproj'),'reopenedSha256':sha(work/'reopen/reopened.fcproj'),
                    'restoredSha256':sha(work/'restore/restored.fcproj')}
                results.append(result);print(json.dumps({'mode':mode,'result':'PASS','stages':4}),flush=True)
            finally:
                if child.poll() is None:
                    child.stdin.close();child.wait(timeout=30)
    report={'schema':'filmcraft-public-task-session-native/v1','result':'PASS','results':results,
        'skillFilesSha256':{str(p.relative_to(skill)):sha(p) for p in sorted((skill/'scripts').glob('*')) if p.is_file()},
        'driverSha256':sha(Path(__file__)),'fullV1':'NOT_PROVEN',
        'scope':'Candidate public JSONL entry; 4 continuous plans per mode, one MCP and optional signed desktop. Full project comparison normalizes only saveAs project/root names; original fixture hash unchanged. EOF and explicit close clean owned processes. Fixed-release installation acceptance separate.'}
    (root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
