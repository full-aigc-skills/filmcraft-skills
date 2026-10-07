"""素材和精确时间线计划的边界。"""
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'skills/filmcraft-use/scripts/workflow.py'

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('workflow', SOURCE)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

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
