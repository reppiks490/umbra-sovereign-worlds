import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from owner_probe import classify, replay, corrective_candidates, PROBE, EXPECTED, PINNED_SHA256
from human_corpus import validate

class OwnerProbeTests(unittest.TestCase):
 def test_original_expression_interpretations(self):
  self.assertEqual(EXPECTED,367181)
  self.assertEqual(17+42*372*47,734345)
  self.assertEqual(len(PINNED_SHA256),64)
 def test_truncation_not_arithmetic_training(self):
  self.assertEqual(classify('qwen3:4b','length','partial calculation')['diagnosis'],'truncated')
  self.assertIsNone(classify('qwen3:4b','length','partial calculation')['lesson_tier'])
 def test_specific_failures(self):
  for model,response,diagnosis in (
   ('phi4-mini:latest','So the answer is 365181.','incorrect_intermediate_arithmetic'),
   ('granite3.3:2b','So the answer is 367231.','incorrect_intermediate_arithmetic'),
   ('qwen3:1.7b',r'\boxed{369441}','incorrect_intermediate_arithmetic'),
   ('deepseek-r1:1.5b',r'\boxed{8759}','missing_operand'),
   ('qwen2.5-coder:1.5b',r'\boxed{10000x + 10000}','notation_interpretation')):
   self.assertEqual(classify(model,'stop',response)['diagnosis'],diagnosis)
 def test_unreviewed_output_rejected(self):
  for model,reason,response in [('unknown','stop','365181'),('phi4-mini:latest','stop','367181'),('qwen3:4b','stop','367181')]:
   with self.assertRaises(ValueError):classify(model,reason,response)
  with self.assertRaises(ValueError):replay(b'{}')
 def test_candidates_are_source_only_and_not_training(self):
  c={'train':[validate({'question':'Three groups of four and five more','answer':'<<3*4=12>> and <<12+5=17>>\n#### 17'})],'validation':[],'test':[]}
  r={'model':'phi4-mini:latest','digest':'a'*64,**classify('phi4-mini:latest','stop','365181')}
  p=corrective_candidates(c,[r])
  self.assertEqual(len(p[0]['lessons']),1)
  self.assertFalse(p[0]['training_authorized'])
  self.assertEqual(p[0]['new_model_calls'],0)
if __name__=='__main__':unittest.main()
