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
