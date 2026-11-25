import sys,pathlib,unittest,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from human_corpus import audit_records,ORIGINAL_ROWS
class HumanCorpusTest(unittest.TestCase):
 def test_original_source_identity(self):
  self.assertEqual(len(ORIGINAL_ROWS),2)
  self.assertEqual(sum(x['size'] for x in ORIGINAL_ROWS),4915944)
  self.assertEqual({r['split'] for r in ORIGINAL_ROWS},{'candidate_training','evaluation'})
 def test_original_solutions_and_holdout_exclusion(self):
  train=[{'question':'How many apples?','answer':'Two plus three.\n#### 5'},{'question':'  How MANY apples?  ','answer':'Two plus three.\n#### 5'},{'question':'What is the total?','answer':'One plus one.\n#### 2'}]
  test=[{'question':'How many apples?','answer':'Two plus three.\n#### 5'}]
  report,rows=audit_records(train,test)
  self.assertEqual(report['train_overlap_removed'],2)
  self.assertEqual(report['retained_training_pool'],1)
  self.assertEqual(report['holdout'],1)
  self.assertEqual(rows['test'][0]['answer'],test[0]['answer'])
  self.assertFalse(report['weight_training'])
 def test_bad_row_fails(self):
  with self.assertRaises(ValueError):audit_records([{'question':'x','answer':'no final answer'}],[{'question':'q','answer':'#### 1'}])
