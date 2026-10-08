"""素材和精确时间线计划的边界。"""
import importlib.util
from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'skills/filmcraft-use/scripts/workflow.py'

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('workflow', SOURCE)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_all_asset_issues_reported_without_installation_or_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            changed = root / 'changed.png'; changed.write_bytes(b'owned changed fixture')
            plan = {'document': {'name': 'Test', 'width': 32, 'height': 32, 'frameRate': {'num': 12, 'den': 1}},
                    'assets': {'missingOne': {'path': str(root/'one.png'), 'sha256': 'a'*64},
                               'missingTwo': {'path': str(root/'two.wav'), 'sha256': 'b'*64},
                               'changed': {'path': str(changed), 'sha256': 'c'*64}}, 'operations': []}
            with patch.object(self.module, 'load_module', side_effect=AssertionError('runtime reached')):
                with self.assertRaisesRegex(ValueError, 'asset_digest_mismatch: missingOne') as caught:
                    self.module.execute(plan, root/'delivery', root/'runtime')
            self.assertEqual(getattr(caught.exception, 'asset_issues', None), [
                {'alias':'missingOne','origin':'plan','reason':'missing_file'},
                {'alias':'missingTwo','origin':'plan','reason':'missing_file'},
                {'alias':'changed','origin':'plan','reason':'digest_mismatch'}])
            self.assertFalse((root/'delivery').exists()); self.assertFalse((root/'runtime').exists())
            self.assertEqual(changed.read_bytes(), b'owned changed fixture')

    def test_source_and_new_asset_issues_keep_origin_without_local_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            with self.assertRaises(ValueError) as caught:
                self.module.preflight_assets({'new': {'path':str(root/'new.wav'),'sha256':'a'*64}},
                    {'prior':{'path':'assets/old.png','sha256':'b'*64}}, root)
            self.assertEqual(getattr(caught.exception, 'asset_issues', None), [
                {'alias':'prior','origin':'source','reason':'missing_file'},
                {'alias':'new','origin':'plan','reason':'missing_file'}])
            self.assertNotIn(str(root), str(caught.exception))

    def test_public_workflow_reports_asset_list_before_runtime_creation(self):
        import json, subprocess, sys
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); plan=root/'plan.json'
            plan.write_text(json.dumps({'document':{'name':'Test','width':32,'height':32,'frameRate':{'num':12,'den':1}},
                'operations':[], 'assets':{'first':{'path':str(root/'first.png'),'sha256':'a'*64},
                                          'second':{'path':str(root/'second.wav'),'sha256':'b'*64}}}))
            result=subprocess.run([sys.executable,'-I','-B',str(SOURCE),str(plan),'--output',str(root/'delivery'),
                                   '--runtime-home',str(root/'runtime')],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,1)
            body=json.loads(result.stdout)
            self.assertEqual(body.get('assetIssues'),[{'alias':'first','origin':'plan','reason':'missing_file'},
                                                     {'alias':'second','origin':'plan','reason':'missing_file'}])
            self.assertNotIn(str(root),result.stdout)
            self.assertFalse((root/'runtime').exists());self.assertFalse((root/'delivery').exists())

    def test_symlink_issues_are_aggregated_without_reading_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve(); link=root/'link.png'; link.symlink_to(root/'absent-private.png')
            with patch.object(self.module, 'sha', side_effect=AssertionError('symlink target read')):
                with self.assertRaises(ValueError) as caught:
                    self.module.preflight_assets({'new':{'path':str(link),'sha256':'a'*64}},
                                                 {'prior':{'path':'link.png','sha256':'b'*64}},root)
            self.assertEqual(getattr(caught.exception,'asset_issues',None),[
                {'alias':'prior','origin':'source','reason':'invalid_path'},
                {'alias':'new','origin':'plan','reason':'invalid_path'}])
            self.assertNotIn('absent-private',str(caught.exception))

    def test_invalid_source_asset_fails_before_install_or_recovery_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            asset = root / 'voice.wav'
            asset.write_bytes(b'invalid digest')
            plan = {'document': {'name': 'Test', 'width': 320, 'height': 180, 'frameRate': {'num': 12, 'den': 1}},
                    'assets': {'voice': {'path': str(asset), 'sha256': '0' * 64}}, 'operations': []}
            with patch.object(self.module, 'load_module', side_effect=AssertionError('runtime or stage reached')):
                with self.assertRaisesRegex(ValueError, 'asset_digest_mismatch'):
                    self.module.execute(plan, root / 'output', runtime_home=root / 'runtime')
            self.assertFalse((root / 'output').exists())
            self.assertFalse((root / 'runtime').exists())
            self.assertEqual(asset.read_bytes(), b'invalid digest')

    def test_audio_tail_accepts_only_exact_native_frame_padding(self):
        clip = {'sourceIn': 0, 'duration': 571536000000, 'speed': 1}
        probe = {'duration': '561714048000', 'kind': 'AudioOnly', 'audio': {'channels': 1}, 'video': None}
        rate = {'num': 12, 'den': 1}
        self.assertTrue(self.module.source_range_valid(clip, probe, rate))
        for changed in [dict(clip, duration=clip['duration'] + 1), dict(clip, speed=2),
                        dict(clip, sourceIn=561714048000), dict(clip, sourceIn=-1), dict(clip, duration=0)]:
            self.assertFalse(self.module.source_range_valid(changed, probe, rate))
        for changed in [dict(probe, kind='Video'), dict(probe, audio=None), dict(probe, video={'width': 320})]:
            self.assertFalse(self.module.source_range_valid(clip, changed, rate))
        self.assertTrue(self.module.source_range_valid(dict(clip, duration=508032000000), probe, rate))

    def test_short_audio_native_minimum_frame_and_invalid_speed(self):
        rate = {'num': 12, 'den': 1}
        clip = {'sourceIn': 0, 'duration': 21168000000, 'speed': 1}
        probe = {'duration': '254016000', 'kind': 'AudioOnly', 'audio': {'channels': 1}}
        self.assertTrue(self.module.source_range_valid(clip, probe, rate))
        for speed in (0, True, float('nan'), float('inf')):
            with self.assertRaisesRegex(ValueError, 'invalid_clip_speed'):
                self.module.source_range_valid(dict(clip, speed=speed), probe, rate)

    def test_visible_captions_are_burned_unless_explicitly_disabled(self):
        state={'tracks':[{'enabled':True}]}
        self.assertEqual(self.module.export_settings({},state),{'burnCaptions':True})
        self.assertEqual(self.module.export_settings({'export':{'burnCaptions':False}},state),{'burnCaptions':False})
        self.assertEqual(self.module.export_settings({}, {'tracks':[]}),{'burnCaptions':False})
        self.assertEqual(self.module.export_settings({}, {'tracks':[{'enabled':False}]}),{'burnCaptions':False})

    def test_export_flags_require_real_booleans(self):
        for value in ('false',0,None):
            with self.assertRaisesRegex(ValueError,'invalid_export'):
                self.module.validate({'operations':[],'export':{'burnCaptions':value}})
        self.module.validate({'operations':[],'export':{'burnCaptions':True}})

    def test_ticks_are_decimal_strings(self):
        self.assertEqual(self.module.ticks('508032000000'), 508032000000)
        for value in (508032000000, 1.2, True, '-1', '1e3', '00', '1.2'):
            with self.assertRaises(ValueError):
                self.module.ticks(value)

    def test_unresolved_reference_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unresolved_reference'):
            self.module.resolve({'$ref': 'unknown.item'}, {})

    def test_side_effect_command_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unsupported_command'):
            self.module.validate({'operations': [{'command': 'media.makeOffline'}]})

    def test_static_track_gain_is_supported_and_rejects_invalid_values(self):
        def plan(params):
            return {'operations': [{'command': 'mixer.setStrip', 'params': params}]}
        self.module.validate(plan({'strip': 'A1', 'volumeDb': -6.0}))
        for value in (True, '6', float('nan'), float('inf'), 10**1000):
            with self.assertRaisesRegex(ValueError, 'invalid_track_gain'):
                self.module.validate(plan({'strip': 'A1', 'volumeDb': value}))
        for params in ({'strip': 'Mix', 'volumeDb': 0}, {'strip': 'A1', 'volumeDb': 0, 'recordArm': True}, {'strip': 'A1'}):
            with self.assertRaisesRegex(ValueError, 'invalid_track_gain'):
                self.module.validate(plan(params))

    def test_duplicate_alias_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate_alias'):
            self.module.validate({'operations': [{'command': 'asset.import', 'as': 'shot'}, {'command': 'asset.import', 'as': 'shot'}]})

    def test_revision_output_preserves_existing_directory(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'user.txt'
            marker.write_text('original')
            with self.assertRaisesRegex(ValueError, 'output_exists'):
                self.module.execute({'operations': []}, directory)
            self.assertEqual(marker.read_text(), 'original')

if __name__ == '__main__':
    unittest.main()
