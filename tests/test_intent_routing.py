"""FC-SK-003：路由语料和渐进式业务指南；不冒充宿主模型路由验收。"""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class IntentRoutingTests(unittest.TestCase):
    def test_corpus_covers_all_skills_with_positive_and_negative_intents(self):
        path = ROOT / 'docs/routing-corpus.json'
        self.assertTrue(path.is_file(), 'intent routing corpus is missing')
        corpus = json.loads(path.read_text())
        names = {x['name'] for x in json.loads((ROOT / 'skill-suite.json').read_text())['skills']}
        self.assertEqual({x['expectedSkill'] for x in corpus['cases']}, names)
        for name in names:
            self.assertTrue(any(x['expectedSkill'] == name and x['rejectSkills'] for x in corpus['cases']))
            self.assertTrue(any(name in x['rejectSkills'] for x in corpus['cases']))
        self.assertEqual(corpus['hostRoutingAcceptance'], 'NOT_RUN')
        self.assertEqual(len({x['id'] for x in corpus['cases']}), len(corpus['cases']))

    def test_generic_cli_does_not_claim_primary_multicam_intent(self):
        name = 'filmcraft-cli'
        text = (ROOT / 'skills' / name / 'SKILL.md').read_text()
        description = re.search(r'^description: (.*)$', text, re.M)[1]
        self.assertNotIn('多机位', description)
        self.assertNotIn('主录音连续性', description)

    def test_each_skill_has_a_task_specific_local_playbook(self):
        suite = json.loads((ROOT / 'skill-suite.json').read_text())
        guides = []
        for skill in suite['skills']:
            name = skill['name']
            with self.subTest(skill=name):
                home = ROOT / 'skills' / name
                guide = home / 'references/task-scene.md'
                self.assertTrue(guide.is_file(), 'business playbook is missing')
                text = guide.read_text()
                guides.append(text)
                self.assertIn('(references/task-scene.md)', (home / 'SKILL.md').read_text())
                for section in ('输入', '首次任务', '失败', '局部修订', '核验'):
                    self.assertIn('## ' + section, text)
                self.assertNotRegex(text, r'\]\(\.\./')
        self.assertEqual(len(set(guides)), len(guides))

    def test_unrelated_skills_do_not_load_multicam_tail(self):
        suite = json.loads((ROOT / 'skill-suite.json').read_text())
        for skill in suite['skills']:
            if skill['name'] in ('filmcraft-use', 'filmcraft-cli-multicam'):
                continue
            with self.subTest(skill=skill['name']):
                text = (ROOT / 'skills' / skill['name'] / 'SKILL.md').read_text()
                self.assertNotIn('[多机位场景]', text)


if __name__ == '__main__':
    unittest.main()
