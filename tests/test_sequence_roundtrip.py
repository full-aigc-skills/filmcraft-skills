"""持久化序列比较不能混入顶层会话状态，也不能放宽工程字段。"""
import copy
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'skills/filmcraft-use/scripts/workflow.py'
spec = importlib.util.spec_from_file_location('roundtrip_workflow', SOURCE)
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)


class SequenceRoundtripTests(unittest.TestCase):
    def setUp(self):
        self.sequence = {'duration': 254016000000, 'durationFrames': 24,
            'settings': {'width': 32, 'height': 32, 'frame_rate': {'num': 24, 'den': 1}},
            'video': [{'items': [{'item': 9, 'duration': 254016000000,
                'effects': {'selection': [1], 'playhead': 10}}]}],
            'audio': [], 'selection': [9], 'playhead': 0}

    def test_missing_reopened_playhead_and_changed_selection_are_session_only(self):
        actual = copy.deepcopy(self.sequence)
        actual.pop('playhead'); actual['selection'] = []
        workflow.validate_sequence_roundtrip(actual, self.sequence)

    def test_nondefault_or_one_sided_session_fields_do_not_change_persistence(self):
        for before, after in [(0, 254016000000), (254016000000, 0)]:
            with self.subTest(before=before, after=after):
                actual = copy.deepcopy(self.sequence); actual['playhead'] = after
                expected = copy.deepcopy(self.sequence); expected['playhead'] = before
                workflow.validate_sequence_roundtrip(actual, expected)
        actual = copy.deepcopy(self.sequence); actual.pop('selection'); actual.pop('playhead')
        workflow.validate_sequence_roundtrip(self.sequence, actual)

    def test_every_persistent_field_and_nested_session_named_field_stays_strict(self):
        mutations = [lambda v: v.update(duration=1), lambda v: v.update(durationFrames=1),
            lambda v: v['settings'].update(width=64),
            lambda v: v['settings']['frame_rate'].update(num=12),
            lambda v: v['video'][0]['items'][0].update(duration=1),
            lambda v: v['video'][0]['items'][0]['effects'].update(selection=[]),
            lambda v: v['video'][0]['items'][0]['effects'].update(playhead=0),
            lambda v: v.update(audio=[{'items': []}]),
            lambda v: v.update(unrecognizedPersistentField=True),
            lambda v: v.pop('duration')]
        for index, mutate in enumerate(mutations):
            with self.subTest(mutation=index):
                actual = copy.deepcopy(self.sequence); mutate(actual)
                with self.assertRaisesRegex(ValueError, '^sequence_roundtrip_mismatch$'):
                    workflow.validate_sequence_roundtrip(actual, self.sequence)

    def test_inputs_remain_unchanged(self):
        actual = copy.deepcopy(self.sequence); actual['selection'] = []
        before = copy.deepcopy(actual); expected = copy.deepcopy(self.sequence)
        workflow.validate_sequence_roundtrip(actual, self.sequence)
        self.assertEqual(actual, before); self.assertEqual(self.sequence, expected)
