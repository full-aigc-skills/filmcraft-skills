"""可信根必须隔离实际进程，且不携带宿主秘密或注入环境。"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/'skills/filmcraft-use/scripts/execution_permissions.py'

class ExecutionPermissionsTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('execution_permissions_test',SCRIPT)
        self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)

    def test_unknown_policy_fields_and_broad_roots_fail_without_echo(self):
        with tempfile.TemporaryDirectory() as temporary:
            valid={'schema':'filmcraft-execution-permissions/v1','readRoots':[str(Path(temporary).resolve())],'writeRoots':[str(Path(temporary).resolve())]}
            for policy in [dict(valid,metadata='OWNED_TEST_CANARY'),dict(valid,writeRoots=['/']),dict(valid,readRoots=[]),dict(valid,readRoots=[7])]:
                with self.subTest(policy=policy),self.assertRaisesRegex(ValueError,'^invalid_execution_permissions$'):
                    self.module.validate(policy)

    def test_policy_identity_canonicalizes_roots_but_rejects_symlink_grants(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();read=root/'read';read.mkdir();write=root/'write';write.mkdir();link=root/'link';link.symlink_to(read)
            p={'schema':'filmcraft-execution-permissions/v1','readRoots':[str(read)],'writeRoots':[str(write)]}
            self.assertEqual(self.module.validate(p),p)
            with self.assertRaisesRegex(ValueError,'^invalid_execution_permissions$'):self.module.validate(dict(p,readRoots=[str(link)]))
            with self.assertRaisesRegex(ValueError,'^permission_read_denied$'):self.module.require_read(root/'outside',p)
            with self.assertRaisesRegex(ValueError,'^permission_write_denied$'):self.module.require_write(root/'outside',p)

    def test_parent_link_replacement_does_not_reauthorize_an_outside_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();parent=root/'parent';parent.mkdir();read=parent/'read';read.mkdir()
            outside=root/'outside';outside.mkdir();(outside/'read').mkdir();write=root/'write';write.mkdir()
            policy={'schema':self.module.SCHEMA,'readRoots':[str(read)],'writeRoots':[str(write)]}
            accepted=self.module.validate(policy);parent.rename(root/'old-parent');parent.symlink_to(outside)
            with self.assertRaisesRegex(ValueError,'^invalid_execution_permissions$'):self.module.validate(accepted)

    def test_minimal_environment_excludes_host_keys_proxies_and_interpreter_injection(self):
        env={'PATH':'/usr/bin:/bin','HOME':'/owned/home','TMPDIR':'/owned/temp','LANG':'zh_CN.UTF-8','FILMCRAFT_DATA_DIR':'/owned/data',
             'OPENAI_API_KEY':'OWNED_TEST_CANARY','HTTP_PROXY':'https://user:OWNED_TEST_CANARY@proxy.invalid','PYTHONPATH':'/owned/injection',
             'DYLD_INSERT_LIBRARIES':'/owned/injection.dylib','NODE_OPTIONS':'--require /owned/injection','FILMCRAFT_EXECUTION_CONTEXT':'PRIVATE_CONTEXT'}
        actual=self.module.child_environment(env)
        self.assertEqual(actual,{'PATH':'/usr/bin:/bin','HOME':'/owned/home','TMPDIR':'/owned/temp','LANG':'zh_CN.UTF-8','FILMCRAFT_DATA_DIR':'/owned/data'})

    def test_unsupported_platform_refuses_instead_of_unisolated_fallback(self):
        with tempfile.TemporaryDirectory() as temporary:
            policy={'schema':'filmcraft-execution-permissions/v1','readRoots':[str(Path(temporary).resolve())],'writeRoots':[str(Path(temporary).resolve())]}
            with self.assertRaisesRegex(ValueError,'^execution_isolation_unavailable$'):
                self.module.command([sys.executable,'-I','-B','-c','print(1)'],policy,platform='unsupported')

    def test_actual_mcp_session_does_not_inherit_host_secret_or_injection(self):
        from unittest.mock import patch
        path=SCRIPT.with_name('mcp_session.py')
        spec=importlib.util.spec_from_file_location('permissions_actual_session',path)
        session=importlib.util.module_from_spec(spec);spec.loader.exec_module(session)
        code="""import sys,json,os
for line in sys.stdin:
 value=json.loads(line)
 if 'id' not in value:continue
 result={} if value['method']=='initialize' else {'secretAbsent':'OPENAI_API_KEY' not in os.environ,'injectionAbsent':'PYTHONPATH' not in os.environ}
 print(json.dumps({'jsonrpc':'2.0','id':value['id'],'result':result}),flush=True)
"""
        with patch.dict(os.environ,{'OPENAI_API_KEY':'OWNED_TEST_CANARY','PYTHONPATH':'/owned/injection'}):
            with session.Session([sys.executable,'-I','-B','-c',code]) as actual:
                self.assertEqual(actual.request('owned/environment',{}),{'secretAbsent':True,'injectionAbsent':True})

    @unittest.skipUnless(sys.platform=='darwin' and Path('/usr/bin/sandbox-exec').is_file(),'requires actual macOS system sandbox')
    def test_actual_child_read_write_and_environment_boundaries(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();read=root/'read';read.mkdir();write=root/'write';write.mkdir();outside=root/'outside';outside.mkdir()
            (read/'asset.txt').write_text('owned media');(outside/'secret.txt').write_text('OWNED_TEST_CANARY')
            policy={'schema':'filmcraft-execution-permissions/v1','readRoots':[str(read)],'writeRoots':[str(write)]}
            code='''from pathlib import Path
import os,json
read,write,outside=map(Path,__import__('sys').argv[1:])
assert (read/'asset.txt').read_text()=='owned media'
assert 'OPENAI_API_KEY' not in os.environ and 'PYTHONPATH' not in os.environ
(write/'project.fcproj').write_text('owned project')
blocked=[]
for mode,path in [('read',outside/'secret.txt'),('write',outside/'escaped.fcproj'),('write',read/'asset.txt')]:
 try:path.read_bytes() if mode=='read' else path.write_bytes(b'escape')
 except PermissionError:blocked.append(mode)
assert blocked==['read','write','write'],blocked
print(json.dumps({'read':True,'write':True,'outsideReadDenied':True,'outsideWriteDenied':True,'readOnlyInputPreserved':True,'hostSecretAbsent':True}))'''
            argv=self.module.command([sys.executable,'-I','-B','-c',code,str(read),str(write),str(outside)],policy)
            result=subprocess.run(argv,env=self.module.child_environment({**os.environ,'OPENAI_API_KEY':'OWNED_TEST_CANARY'}),capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertTrue(all(json.loads(result.stdout).values()));self.assertEqual((read/'asset.txt').read_text(),'owned media')
            self.assertFalse((outside/'escaped.fcproj').exists())

    @unittest.skipUnless(sys.platform=='darwin' and Path('/usr/bin/sandbox-exec').is_file(),'requires actual macOS system sandbox')
    def test_owned_bridge_control_port_does_not_grant_other_network_access(self):
        import socket
        with tempfile.TemporaryDirectory() as temporary, socket.socket() as forbidden:
            root=Path(temporary).resolve();policy={'schema':self.module.SCHEMA,'readRoots':[str(root)],'writeRoots':[str(root)]}
            forbidden.bind(('127.0.0.1',0));forbidden.listen();blocked_port=forbidden.getsockname()[1]
            with socket.socket() as probe:probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
            code="import socket,sys\nport,blocked=map(int,sys.argv[1:]);s=socket.socket();s.bind(('127.0.0.1',port));s.listen();print('READY',flush=True)\nc,a=s.accept();c.sendall(b'owned');c.close();s.close()\ntry:\n with socket.socket() as denied:denied.connect(('127.0.0.1',blocked))\nexcept PermissionError:print('OUTSIDE_DENIED',flush=True)\nelse:raise AssertionError('outside network allowed')\n"
            argv=self.module.command([sys.executable,'-I','-B','-c',code,str(port),str(blocked_port)],policy,control_port=port,graphics=True)
            child=subprocess.Popen(argv,env=self.module.child_environment(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try:
                self.assertEqual(child.stdout.readline().strip(),'READY')
                with socket.create_connection(('127.0.0.1',port),timeout=3) as client:self.assertEqual(client.recv(20),b'owned')
                out,err=child.communicate(timeout=10);self.assertEqual(child.returncode,0,err);self.assertEqual(out.strip(),'OUTSIDE_DENIED')
            finally:
                if child.poll() is None:child.kill();child.wait(timeout=5)
