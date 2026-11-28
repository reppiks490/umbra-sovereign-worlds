import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from grounded_reasoning import source_numbers,verify_expression,grade_pair,choose_records,GroundingError
class GroundedReasoningTest(unittest.TestCase):
 def test_user_arithmetic(self):
  r=verify_expression('What is half of 2x17+42(372x47)?','EXPR: (2x17+42(372x47))/2')
  self.assertEqual(r['value'],'367181')
  self.assertTrue(r['literal_grounding'])
 def test_unbound_number_and_answer_shortcut(self):
  for response in ('EXPR: 17+400','EXPR: 17','EXPR: 17+2\nANSWER: 19','EXPR: 17+1'):
   with self.subTest(response=response),self.assertRaises(GroundingError):verify_expression('There are 17 apples and 2 pears.',response)
 def test_abstention(self):
  self.assertIsNone(verify_expression('Unknown values.','ABSTAIN'))
 def test_explicit_conversions_only(self):
  self.assertEqual(verify_expression('What is 15 percent of 80?','EXPR: 15*80/100')['value'],'12')
  with self.assertRaises(GroundingError):verify_expression('15 boxes of 80','EXPR: 15*80/100')
 def test_source_tokens(self):
  self.assertEqual(source_numbers('2,500.50 dollars plus 0.25; 2x17.'),{'5001/2','1/4','2','17'})
 def test_matched_scoring(self):
  p=grade_pair('2x17','34','ANSWER: 35','EXPR: 2*17')
  self.assertFalse(p['direct_correct']);self.assertTrue(p['hybrid_correct']);self.assertEqual(p['outcome'],'win')
 def test_scope_wrong_but_computation_valid(self):
  p=grade_pair('What is half of 2x17+42(372x47)?','367181','ANSWER: 367181','EXPR: 2*17/2+42*(372*47)')
  self.assertFalse(p['hybrid_correct']);self.assertEqual(p['outcome'],'loss')
 def test_selection_no_labels(self):
  rows=[{'question':'2x17','record_sha256':'a'*64,'answer':'hidden'}, {'question':'4+6','record_sha256':'b'*64,'answer':'hidden'}]
  self.assertEqual([r['record_sha256'] for r in choose_records(rows,0,2)],['a'*64,'b'*64])
  with self.assertRaises(ValueError):choose_records(rows,1,2)
if __name__=='__main__':unittest.main()
