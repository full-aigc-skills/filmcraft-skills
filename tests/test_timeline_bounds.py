"""显式裁切源范围不得被原生钳制掩盖，诊断保留精确片段身份。"""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TimelineBoundsTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('timeline_bounds_workflow', ROOT/'skills/filmcraft-use/scripts/workflow.py')
        self.workflow = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.workflow)

    def test_literal_invalid_trim_ticks_refuse_with_clip_identity(self):
        for delta in (0.1, True, '1.5', str(2**63), str(-2**63-1)):
            with self.subTest(delta=delta):
                with self.assertRaises(ValueError) as caught:
                    self.workflow.validate({'operations':[{'command':'timeline.trim', 'params':{'clip':2**64-1, 'edge':'out', 'mode':'regular', 'delta':delta}}]})
                self.assertEqual(caught.exception.clip_timing['clipIds'], [str(2**64-1)])

    def test_exact_trim_range_and_native_audio_padding_remain_distinct(self):
        clip = {'clip':11, 'item':9, 'sourceIn':0, 'duration':100, 'start':0, 'speed':1}
        sequence = {'video':[{'items':[clip]}], 'audio':[]}
        assets = {'source':{'item':9, 'probe':{'duration':'100'}}}
        params = {'clip':11, 'edge':'out', 'mode':'regular', 'delta':'1'}
        with self.assertRaisesRegex(ValueError, 'clip_out_of_range') as caught:
            self.workflow.preflight_trim(params, sequence, assets)
        self.assertEqual(caught.exception.clip_timing, {'reason':'clip_out_of_range','clipIds':['11']})
        self.assertEqual(self.workflow.preflight_trim(dict(params, delta='-1'), sequence, assets), -1)
        clip['duration'] = 90
        self.assertEqual(self.workflow.preflight_trim(dict(params, delta='10'), sequence, assets), 10)

    def test_trim_in_uses_speed_and_refuses_non_integral_source_ticks(self):
        clip = {'clip':11, 'item':9, 'sourceIn':10, 'duration':20, 'start':10, 'speed':1.5}
        sequence = {'video':[{'items':[clip]}], 'audio':[]}
        assets = {'source':{'item':9, 'probe':{'duration':'100'}}}
        params = {'clip':11, 'edge':'in', 'mode':'regular', 'delta':'1'}
        with self.assertRaisesRegex(ValueError, 'ticks_not_exact') as caught:
            self.workflow.preflight_trim(params, sequence, assets)
        self.assertEqual(caught.exception.clip_timing['clipIds'], ['11'])
        with self.assertRaisesRegex(ValueError, 'ticks_not_exact'):
            self.workflow.preflight_trim(dict(params, edge='out'), sequence, assets)
        self.assertEqual(self.workflow.preflight_trim(dict(params, delta='2'), sequence, assets), 2)
        with self.assertRaisesRegex(ValueError, 'clip_out_of_range'):
            self.workflow.preflight_trim(dict(params, delta='-8'), sequence, assets)

    def test_literal_move_time_has_target_identity(self):
        with self.assertRaisesRegex(ValueError, 'ticks_require_decimal_string') as caught:
            self.workflow.validate({'operations':[{'command':'timeline.move','params':{'moves':[{'clip':11,'track':'V1','time':'0.5'}]}}]})
        self.assertEqual(caught.exception.clip_timing, {'reason':'ticks_require_decimal_string','clipIds':['11']})

    def test_valid_trim_and_move_and_deferred_reference_remain_accepted(self):
        self.workflow.validate({'operations':[
            {'command':'timeline.trim','params':{'clip':11,'edge':'in','mode':'regular','delta':'-5'}},
            {'command':'timeline.move','params':{'moves':[{'clip':11,'track':'V1','time':'5'}]}},
            {'command':'timeline.trim','params':{'clip':{'$ref':'newClip.clips.0'},'edge':'out','delta':'5'}}]})

    def test_zero_trim_keeps_existing_audio_frame_padding(self):
        clip = {'clip':11, 'item':9, 'sourceIn':0, 'duration':21168000000, 'start':0, 'speed':1}
        sequence = {'video':[], 'audio':[{'items':[clip]}], 'settings':{'frame_rate':{'num':12,'den':1}}}
        assets = {'source':{'item':9,'probe':{'duration':'254016000','kind':'AudioOnly','audio':{'channels':1}}}}
        self.assertEqual(self.workflow.preflight_trim({'clip':11,'edge':'out','delta':'0'}, sequence, assets), 0)
        with self.assertRaisesRegex(ValueError, 'clip_out_of_range'):
            self.workflow.preflight_trim({'clip':11,'edge':'out','delta':'1'}, sequence, assets)

    def test_failed_stage_has_separate_safe_clip_diagnostic_without_protocol_expansion(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(ValueError, 'clip_out_of_range'):
                with self.workflow.load_module('preserved_stage').preserved_stage(root/'delivery', '.test-') as stage:
                    raise self.workflow.ClipTimingError('clip_out_of_range', 2**64-1)
            detail = json.loads((Path(stage)/'clip-timing.json').read_text())
            self.assertEqual(detail, {'reason':'clip_out_of_range','clipIds':[str(2**64-1)]})
            failure = json.loads((root/'delivery/failure.json').read_text())
            self.assertNotIn('clipTiming', failure)
            self.assertIn('clip-timing.json', failure['files'])


if __name__ == '__main__':
    unittest.main()
