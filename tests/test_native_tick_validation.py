"""原生 ticks 不能被错误类型静默替换成播放头。"""
from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tick_gateway', ROOT / 'skills/filmcraft-use/scripts/commands.py')
gateway = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gateway)


class NativeTickValidationTests(unittest.TestCase):
    def plan(self, value):
        return {'schema': 'craft-command-plan/v1', 'operations': [
            {'command': 'multicam.cutToCamera', 'params': {'camera': 2, 'time': value}}
        ]}

    def test_invalid_literal_ticks_are_rejected_before_execution(self):
        for value in ['254016000000', 1.5, True, 2 ** 63]:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'invalid_tick_parameter'):
                gateway.validate(self.plan(value))

    def test_exact_large_integer_is_preserved(self):
        value = 2 ** 53 + 1
        self.assertEqual(gateway.validate(self.plan(value))['operations'][0]['params']['time'], value)

    def test_resolved_reference_is_rechecked(self):
        with self.assertRaisesRegex(ValueError, 'invalid_tick_parameter'):
            gateway.validate_tick_parameters('multicam.cutToCamera', {'time': '254016000000'})


if __name__ == '__main__':
    unittest.main()
