"""领域交付使用所属会话，而非为重开和渲染再次启动编辑器。"""
import base64
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('workflow_reuse',ROOT/'skills/filmcraft-use/scripts/workflow.py')
workflow=importlib.util.module_from_spec(spec);spec.loader.exec_module(workflow)


class WorkflowSessionReuseTests(unittest.TestCase):
    def test_reopen_reads_fresh_persisted_state_in_original_session(self):
        events=[]
        def command(name,params):events.append((name,params));return {'tracks':[]} if name=='captions.list' else None
        def call(name,params):events.append((name,params));return {'fresh':name}
        native,captions=workflow.reopen_project(command,call,Path('/owned/project.fcproj'))
        self.assertEqual(events,[('file.closeAllProjects',{'force':True}),('file.open',{'path':'/owned/project.fcproj'}),('project_inspect',{}),('sequence_inspect',{}),('captions.list',{})])
        self.assertEqual(native,{'project':{'fresh':'project_inspect'},'sequence':{'fresh':'sequence_inspect'}})
        self.assertEqual(captions,{'tracks':[]})

    def test_render_uses_same_session_and_keeps_lossless_png_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'frame.png';data=b'\x89PNG\r\n\x1a\nowned bytes'
            session=Mock();session.request.return_value={'content':[{'type':'image','mimeType':'image/png','data':base64.b64encode(data).decode()},{'type':'text','text':'rendered frame'}]}
            record={};workflow.render_native_frame(session,2.5,target,32,record)
            self.assertEqual(target.read_bytes(),data)
            session.request.assert_called_once_with('tools/call',{'name':'render_frame','arguments':{'seconds':2.5,'max_side':32}})
            self.assertEqual(record['lastAttempt']['phase'],'reply_received')

    def test_render_invalid_or_ambiguous_image_is_unknown_without_output(self):
        for content in [[],[{'type':'text','text':'not image'}],[{'type':'image','mimeType':'image/png','data':'bad!'}],
                        [{'type':'image','mimeType':'image/jpeg','data':'YWJj'}],
                        [{'type':'image','mimeType':'image/png','data':'YWJj'}],
                        [{'type':'image','mimeType':'image/png','data':'YWJj'}]*2]:
            with self.subTest(content=content),tempfile.TemporaryDirectory() as d:
                target=Path(d)/'frame.png';session=Mock();session.request.return_value={'content':content}
                with self.assertRaisesRegex(RuntimeError,'outcome_unknown'):
                    workflow.render_native_frame(session,0,target,32,{})
                self.assertFalse(target.exists());self.assertEqual(session.request.call_count,1)

    def test_nonboolean_error_flag_is_unknown(self):
        session=Mock();session.request.return_value={'isError':'false','content':[]}
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(RuntimeError,'outcome_unknown'):
                workflow.render_native_frame(session,0,Path(d)/'frame.png',32,{})

    def test_render_timeout_is_not_replayed(self):
        session=Mock();session.request.side_effect=TimeoutError('outcome_unknown')
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(TimeoutError):workflow.render_native_frame(session,0,Path(d)/'frame.png',32,{})
        self.assertEqual(session.request.call_count,1)
