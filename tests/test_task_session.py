"""公开任务会话的跨计划状态、隔离身份和未知结果停止合同。"""
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/filmcraft-use/scripts/task_session.py'


def module():
    spec = importlib.util.spec_from_file_location('task_session_test', SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class TaskSessionTests(unittest.TestCase):
    def setup_session(self, m, root, mode='headless'):
        commands = m.load('commands')
        actual_load = commands.load
        guard = actual_load('execution_permissions')
        self.enter_context(patch.object(guard, 'ensure_available'))
        self.enter_context(patch.object(guard, 'command', side_effect=lambda argv, *a, **k: argv))
        self.enter_context(patch.object(commands, 'load', side_effect=lambda name: guard if name == 'execution_permissions' else actual_load(name)))
        binary = root / 'runtime/native'; binary.parent.mkdir(); binary.write_bytes(b'native')
        digest = m.sha(binary)
        self.starts = []; self.closes = []; self.edits = []; self.failure = False
        self.dead = False
        self.interrupted = False
        test = self
        class Process:
            pid = 12345
            def poll(self): return 1 if test.dead else None
        class Fake:
            def __init__(self, *args, **kwargs): self.process = Process(); test.starts.append(args)
            def request(self, method, params):
                if method == 'tools/list': return {'tools': [{'name': n} for n in commands.ROUTES['filmcraft'][:2]]}
                if params['name'] == commands.ROUTES['filmcraft'][0]:
                    return {'content': [{'type': 'text', 'text': json.dumps([dict(r, enabled=True) for r in commands.catalog()['commands']])}]}
                if test.interrupted: raise KeyboardInterrupt()
                if test.failure: raise TimeoutError('outcome_unknown')
                test.edits.append(params)
                return {'content': [{'type': 'text', 'text': json.dumps({'counter': len(test.edits)})}]}
            def close(self): test.closes.append(1); test.dead = True
        native = actual_load('mcp_session'); native.Session = Fake
        bootstrap = actual_load('bootstrap')
        self.installs = self.enter_context(patch.object(bootstrap, 'install', return_value={'executable':str(binary),'binarySha256':digest}))
        old_load = commands.load
        self.enter_context(patch.object(commands, 'load', side_effect=lambda n: native if n=='mcp_session' else bootstrap if n=='bootstrap' else old_load(n)))
        policy={'schema':guard.SCHEMA,'readRoots':[str(root)],'writeRoots':[str(root)]}
        return m.TaskSession(root/'task', root/'runtime', policy, mode=mode, commands=commands)

    def enter_context(self, context):
        value = context.__enter__(); self.addCleanup(context.__exit__, None, None, None); return value

    def plan(self):
        return {'schema':'craft-command-plan/v1','operations':[{'command':'state.inspect','params':{}}]}

    def test_two_plans_share_state_process_and_single_install_until_task_end(self):
        m=module()
        with tempfile.TemporaryDirectory() as d:
            s=self.setup_session(m,Path(d).resolve())
            with s:
                a=s.execute(self.plan(),'first'); b=s.execute(self.plan(),'second')
                self.assertEqual([a['steps'][0]['result']['counter'],b['steps'][0]['result']['counter']],[1,2])
                self.assertEqual(len(self.starts),1); self.assertEqual(self.closes,[])
                self.assertEqual(self.installs.call_count,1)
            self.assertEqual(len(self.closes),1)
            proof=json.loads((s.work/'task-session.json').read_text())
            self.assertEqual(proof['sessionsStarted'],1);self.assertTrue(proof['singleProcessIdentity'])
            self.assertTrue(proof['ownedProcessesStopped'])

    def test_unknown_stops_next_plan_without_restart_or_replay(self):
        m=module()
        with tempfile.TemporaryDirectory() as d:
            s=self.setup_session(m,Path(d).resolve())
            with s:
                s.execute(self.plan(),'first'); self.failure=True
                result=s.execute(self.plan(),'unknown'); self.assertEqual(result['result'],'unknown')
                with self.assertRaisesRegex(RuntimeError,'task_session_stopped'): s.execute(self.plan(),'later')
                self.assertFalse((s.work/'later').exists());self.assertEqual(len(self.starts),1)
            self.assertEqual(len(self.edits),1)

    def test_invalid_later_plan_never_starts_or_creates_stage(self):
        m=module()
        with tempfile.TemporaryDirectory() as d:
            s=self.setup_session(m,Path(d).resolve())
            with s:
                bad={'schema':'craft-command-plan/v1','operations':[{'command':'invented.command','params':{}}]}
                with self.assertRaisesRegex(ValueError,'unknown_command'):s.execute(bad,'bad')
                self.assertFalse((s.work/'bad').exists());self.assertEqual(self.starts,[])
                with self.assertRaisesRegex(RuntimeError,'task_session_stopped'):s.execute(self.plan(),'later')

    def test_process_exit_does_not_start_replacement(self):
        m=module()
        with tempfile.TemporaryDirectory() as d:
            s=self.setup_session(m,Path(d).resolve())
            with s:
                s.execute(self.plan(),'first');self.dead=True
                with self.assertRaisesRegex(RuntimeError,'task_process_exited'):s.execute(self.plan(),'later')
                self.assertFalse((s.work/'later').exists());self.assertEqual(len(self.starts),1)

    def test_model_identity_change_stops_before_later_stage(self):
        m=module()
        with tempfile.TemporaryDirectory() as d:
            s=self.setup_session(m,Path(d).resolve())
            with s:
                s.execute(self.plan(),'first')
                with patch.dict(os.environ,{'FILMCRAFT_DATA_DIR':d}):
                    with self.assertRaisesRegex(ValueError,'task_identity_changed'):s.execute(self.plan(),'later')
                self.assertFalse((s.work/'later').exists())

    def test_external_input_requires_startup_protection(self):
        m=module()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();s=self.setup_session(m,root);source=root/'source.fcproj';source.write_text('original')
            with s:
                with self.assertRaisesRegex(ValueError,'task_input_not_protected'):s.execute(self.plan(),'bad',{'source':str(source)})
                self.assertEqual(source.read_text(),'original');self.assertEqual(self.starts,[])

    def test_interrupt_preserves_unknown_journal_and_stops_later_edits(self):
        m=module()
        with tempfile.TemporaryDirectory() as d:
            s=self.setup_session(m,Path(d).resolve())
            with s:
                self.interrupted=True
                with self.assertRaises(KeyboardInterrupt):s.execute(self.plan(),'interrupted')
                r=json.loads((s.work/'interrupted/journal.json').read_text())
                self.assertEqual(r['result'],'unknown');self.assertEqual(r['steps'][-1]['state'],'unknown')
                self.assertEqual(json.loads((s.work/'interrupted/failure.json').read_text()),r)
                with self.assertRaisesRegex(RuntimeError,'task_session_stopped'):s.execute(self.plan(),'later')
            self.assertEqual(len(self.starts),1);self.assertEqual(len(self.closes),1)

    def test_binary_change_stops_before_new_stage(self):
        m=module()
        with tempfile.TemporaryDirectory() as d:
            s=self.setup_session(m,Path(d).resolve())
            with s:
                s.execute(self.plan(),'first'); (s.runtime/'native').write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError,'task_identity_changed'):s.execute(self.plan(),'later')
                self.assertFalse((s.work/'later').exists());self.assertEqual(len(self.starts),1)

    def test_permission_change_stops_without_widening_live_process(self):
        m=module()
        with tempfile.TemporaryDirectory() as d:
            s=self.setup_session(m,Path(d).resolve())
            with s:
                s.execute(self.plan(),'first');s.permissions['writeRoots'].append('/tmp')
                with self.assertRaisesRegex(ValueError,'task_identity_changed'):s.execute(self.plan(),'later')
                self.assertFalse((s.work/'later').exists())

    def test_eof_closes_and_task_cannot_be_reentered(self):
        m=module()
        with tempfile.TemporaryDirectory() as d:
            s=self.setup_session(m,Path(d).resolve())
            with s:
                self.assertEqual(m.serve(s,io.StringIO(json.dumps({'name':'one','plan':self.plan()})+'\n'),io.StringIO()),0)
            self.assertEqual(len(self.closes),1)
            with self.assertRaisesRegex(RuntimeError,'task_session_stopped'):s.__enter__()
            s.close();self.assertEqual(len(self.closes),1)

    def test_source_protection_cannot_include_task_output(self):
        m=module()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();s=self.setup_session(m,root);s.close()
            with self.assertRaisesRegex(ValueError,'task_output_protected'):
                m.TaskSession(root/'other',root/'runtime',s.permissions,protected_paths=[root],commands=s.commands)
            self.assertFalse((root/'other').exists())

    def test_line_protocol_keeps_one_instance_until_explicit_close(self):
        m=module()
        with tempfile.TemporaryDirectory() as d:
            s=self.setup_session(m,Path(d).resolve());out=io.StringIO()
            requests=[{'name':'first','plan':self.plan()},{'name':'second','plan':self.plan()},{'action':'close'}]
            with s: code=m.serve(s,io.StringIO('\n'.join(json.dumps(r) for r in requests)+'\n'),out)
            rows=[json.loads(line) for line in out.getvalue().splitlines()]
            self.assertEqual(code,0);self.assertEqual([r['result'] for r in rows],['PASS','PASS','CLOSED'])
            self.assertEqual(len(self.starts),1);self.assertEqual(len(self.closes),1)

    def test_malformed_line_stops_without_edit_or_restarting(self):
        m=module()
        with tempfile.TemporaryDirectory() as d:
            s=self.setup_session(m,Path(d).resolve());out=io.StringIO()
            with s: code=m.serve(s,io.StringIO('{"plan":NaN}\n'+json.dumps({'name':'later','plan':self.plan()})+'\n'),out)
            self.assertEqual(code,1);self.assertEqual(len(out.getvalue().splitlines()),1);self.assertEqual(self.starts,[])


if __name__=='__main__': unittest.main()
