"""离线发行门禁负例不等于实际发行或原生验收。"""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))

class ReleaseChecksTests(unittest.TestCase):
 def test_required_workflow_is_unconditional(self):
  workflow=Path(__file__).resolve().parents[1]/".github/workflows/offline.yml"
  self.assertTrue(workflow.is_file(),"independent source CI must exist")
  text=workflow.read_text()
  self.assertIn("python3 -I -B scripts/check_release.py --output",text)
  self.assertNotIn("hashFiles",text)
  self.assertNotIn("continue-on-error",text)
  from check_release import validate_workflow
  validate_workflow(text)
  for bad in (text.replace('    runs-on:',"    if: hashFiles('package.json') != ''\n    runs-on:"),text.replace('run: python3 -I -B scripts/check_release.py','run: true')):
   with self.assertRaises(ValueError):validate_workflow(bad)
 def test_required_skip_unknown_skip_or_missing_test_cannot_pass(self):
  from check_release import validate_test_rows
  policy={'requiredTests':['unit'], 'environmentTests':[{'id':'native','reason':'explicit native'}]}
  valid=[{'id':'unit','status':'PASS'}, {'id':'native','status':'NOT_RUN','reason':'explicit native'}]
  validate_test_rows(valid,policy)
  for rows in [[{'id':'unit','status':'PASS'}],valid[1:], [{'id':'unit','status':'NOT_RUN','reason':'missing package'}], valid+[{'id':'other','status':'NOT_RUN','reason':'skip'}],valid+[valid[0]]]:
   with self.subTest(rows=rows),self.assertRaises(ValueError):validate_test_rows(rows,policy)
 def test_sibling_skill_link_is_refused_even_when_it_exists(self):
  from check_release import validate_links
  import tempfile
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);home=root/'skills/a';home.mkdir(parents=True);(root/'skills/b').mkdir();(root/'skills/b/SKILL.md').write_text('other')
   (home/'SKILL.md').write_text('[other](../b/SKILL.md)')
   with self.assertRaisesRegex(ValueError,'cross_skill'):validate_links(root)

 def test_failed_subtests_have_explicit_parent_failure_and_separate_event_count(self):
  import io
  from check_release import EvidenceResult
  class Example(unittest.TestCase):
   def test_failure(self):
    for item in range(2):
     with self.subTest(item=item):self.fail('expected synthetic failure')
  result=unittest.TextTestRunner(stream=io.StringIO(),resultclass=EvidenceResult).run(unittest.defaultTestLoader.loadTestsFromTestCase(Example))
  self.assertEqual(result.rows,[{'id':Example('test_failure').id(),'status':'FAIL','failedSubtests':2}])
  self.assertEqual(len(result.failures),2)
