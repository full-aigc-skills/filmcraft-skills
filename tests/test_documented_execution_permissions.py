"""公开可执行示例必须完整声明已授权目录，不能因文档漂移首次执行即失败。"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def examples(root):
    for path in sorted(Path(root).rglob('*.md')):
        if '.git' in path.parts:
            continue
        for block in re.findall(r'```(?:bash|sh|shell)\s*\n(.*?)```', path.read_text(), re.S):
            for line in block.replace('\\\n', ' ').splitlines():
                if ('scripts/workflow.py' in line or
                        (any('scripts/' + name + '.py' in line for name in ('commands', 'desktop'))
                         and ' run ' in line) or ('scripts/cli.py' in line and ' -- exec ' in line)):
                    yield path.relative_to(root).as_posix(), line, block


class DocumentedExecutionPermissionsTests(unittest.TestCase):
    def test_every_public_mutation_example_declares_trusted_roots_and_runtime(self):
        missing = []
        observed = list(examples(ROOT))
        self.assertTrue(observed)
        for path, line, block in observed:
            for flag in ('--read-root', '--write-root', '--runtime-home'):
                if flag not in line:
                    missing.append((path, flag))
        self.assertEqual(missing, [], 'Incomplete public examples: ' + str(missing[:12]))

    def test_policy_variables_are_required_before_documented_execution(self):
        missing = []
        for path, line, block in examples(ROOT):
            for variable in set(re.findall(r'\$(?:\{)?([A-Z_]*ROOT|RUNTIME_HOME|SKILL_DIR)\b', line)):
                if '${' + variable + ':?' not in block:
                    missing.append((path, variable))
        self.assertEqual(missing, [], 'Unguarded policy variables: ' + str(missing[:12]))


if __name__ == '__main__':
    unittest.main()
