import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from verified_reasoner import calculate,ReasoningError
from source_curriculum import trace_audit
from grounded_reasoning import verify_expression
class SourceNotationTest(unittest.TestCase):
 def test_original_decimal(self):
  self.assertEqual(calculate('300*.50')['value'],'150')
  self.assertEqual(calculate('.1+.2')['value'],'3/10')
  self.assertEqual(calculate('-.5/2')['value'],'-1/4')
 def test_floor_division(self):
  self.assertEqual(calculate('180//3')['value'],'60')
  self.assertEqual(calculate('-7//2')['value'],'-4')
  self.assertEqual(calculate('5+7//2*3')['value'],'14')
  with self.assertRaises(ReasoningError):calculate('1//0')
 def test_audit_original_forms(self):
  self.assertEqual(trace_audit([{'answer':'<<300*.50=150>> <<180//3=60>>'}])['verified'],2)
 def test_grounded_decimal(self):
  self.assertEqual(verify_expression('What is 300 times .50?','EXPR: 300*.50')['value'],'150')
 def test_reject_malformed_decimal(self):
  for v in ('..5','.','1..2','1///2'):
   with self.assertRaises(ReasoningError):calculate(v)
if __name__=='__main__':unittest.main()
