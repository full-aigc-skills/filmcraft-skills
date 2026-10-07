"""转录任务应有独立安装入口和完整命令归属。"""
from pathlib import Path
import json,unittest
ROOT=Path(__file__).resolve().parents[1]
class TranscriptSkillTests(unittest.TestCase):
 def test_transcript_commands_have_local_scene_resources(self):
  name='filmcraft-cli-transcript';suite=json.loads((ROOT/'skill-suite.json').read_text());skills={x['name']:x for x in suite['skills']};self.assertIn(name,skills);self.assertEqual(skills[name]['kind'],'scenario')
  rows=json.loads((ROOT/'skills/filmcraft-use/references/command-coverage.json').read_text())['commands'];commands=[x for x in rows if x['id'].startswith('transcript.')];self.assertEqual(len(commands),14);self.assertTrue(all(x['ownerSkill']==name for x in commands))
  home=ROOT/'skills'/name
  for path in ['SKILL.md','scripts/bootstrap.py','scripts/cli.py','scripts/commands.py','scripts/runtime.lock.json','references/transcript-scene.md']:
   self.assertTrue((home/path).is_file(),path)
if __name__=='__main__':unittest.main()
