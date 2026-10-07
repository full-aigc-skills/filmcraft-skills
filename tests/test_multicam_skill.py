"""多机位请求必须路由到可独立安装的专项技能。"""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class MulticamSkillTests(unittest.TestCase):
    def test_multicam_commands_have_independent_scenario_owner(self):
        suite = json.loads((ROOT / 'skill-suite.json').read_text())
        name = 'filmcraft-cli-multicam'
        skills = {row['name']: row for row in suite['skills']}
        self.assertIn(name, skills)
        self.assertEqual(skills[name]['kind'], 'scenario')
        coverage = json.loads((ROOT / 'skills/filmcraft-use/references/command-coverage.json').read_text())['commands']
        commands = [row for row in coverage if row['id'].startswith('multicam.')]
        self.assertEqual(len(commands), 35)
        self.assertTrue(all(row['ownerSkill'] == name for row in commands))
        home = ROOT / 'skills' / name
        for path in ['SKILL.md', 'scripts/bootstrap.py', 'scripts/cli.py', 'scripts/commands.py', 'scripts/runtime.lock.json', 'references/multicam-scene.md']:
            self.assertTrue((home / path).is_file(), path)


if __name__ == '__main__':
    unittest.main()
