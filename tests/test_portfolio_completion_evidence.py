import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from research_portfolio import normalize, record_outcome

class CompletionEvidenceTest(unittest.TestCase):
 def result(self,**kw):
  return {'status':'completed','model_calls':2,'completed_calls':2,
          'production_authority':False,'weight_training':False,**kw}
 def test_valid_integer_call_counts(self):
  for lane in ('collective','authentic_retrieval','instruction_following','grounded_reasoning','generated_challenges'):
   with self.subTest(lane=lane):
    self.assertEqual(normalize(lane,self.result()),'completed')
 def test_boolean_counts_are_not_calls(self):
  self.assertEqual(normalize('generated_challenges',self.result(model_calls=True,completed_calls=True)),'partial')
 def test_float_counts_are_not_calls(self):
  self.assertEqual(normalize('collective',self.result(model_calls=2.0,completed_calls=2.0)),'partial')
 def test_mixed_numeric_types_are_not_calls(self):
  self.assertEqual(normalize('instruction_following',self.result(model_calls=1,completed_calls=True)),'partial')
 def test_missing_scope_cannot_advance(self):
  r=self.result();del r['weight_training']
  self.assertEqual(normalize('grounded_reasoning',r),'partial')
 def test_non_boolean_scope_cannot_advance(self):
  self.assertEqual(normalize('authentic_retrieval',self.result(production_authority=0)),'partial')
 def test_noninteger_result_does_not_advance_cursor(self):
  status=normalize('generated_challenges',self.result(model_calls=True,completed_calls=True))
  self.assertEqual(record_outcome({},'generated_challenges',100,status)['generated_challenges']['completed'],0)
 def test_negative_and_incomplete_not_completed(self):
  for a,b in ((-1,-1),(0,0),(2,1),(2,3)):
   self.assertEqual(normalize('collective',self.result(model_calls=a,completed_calls=b)),'partial')
 def test_authority_violation_still_rejected(self):
  with self.assertRaises(ValueError):normalize('collective',self.result(production_authority=True))
if __name__=='__main__':unittest.main()
