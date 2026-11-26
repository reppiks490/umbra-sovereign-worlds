import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from verified_reasoner import calculate,execute_plan,verify_receipt,ReasoningError
class ExactReasoningTest(unittest.TestCase):
 def test_owner_expression(self):
  self.assertEqual(calculate('(2x17+42(372x47))/2')['value'],'367181')
 def test_exact_decimal_and_fraction(self):
  self.assertEqual(calculate('0.1+0.2')['value'],'3/10')
  self.assertEqual(calculate('2/3+1/6')['value'],'5/6')
 def test_invalid_inputs(self):
  for expr in ('1/0','2**99999','__import__("os")','1;2','3abc','1e500','1+','2(3)(4)'):
   with self.subTest(expr=expr):
    with self.assertRaises(ReasoningError):calculate(expr)
 def test_scope_not_guessed(self):
  with self.assertRaises(ReasoningError):calculate('half of 2x17+42(372x47)')
 def test_typed_plan(self):
  plan={'nodes':[{'id':'a','op':'literal','value':'17'},{'id':'b','op':'literal','value':'2'},{'id':'c','op':'mul','args':['a','b']},{'id':'d','op':'div','args':['c','b']}],'output':'d'}
  receipt=execute_plan(plan)
  self.assertEqual(receipt['value'],'17')
  self.assertTrue(verify_receipt(plan,receipt))
  receipt['value']='18'
  self.assertFalse(verify_receipt(plan,receipt))
 def test_causal_dependencies_and_schema(self):
  for nodes in ([{'id':'a','op':'add','args':['b','b']},{'id':'b','op':'literal','value':'1'}],[{'id':'a','op':'literal','value':'1'},{'id':'a','op':'literal','value':'2'}],[{'id':'a','op':'literal','value':'1','shell':'cmd'}],[{'id':'a','op':'unknown'}]):
   with self.assertRaises(ReasoningError):execute_plan({'nodes':nodes,'output':'a'})
 def test_budget_and_unreachable_nodes(self):
  with self.assertRaises(ReasoningError):execute_plan({'nodes':[{'id':'a','op':'literal','value':'1'},{'id':'b','op':'literal','value':'2'}],'output':'a'})
  with self.assertRaises(ReasoningError):calculate('1+'*129+'1')
 def test_financial_quantities(self):
  p={'nodes':[{'id':'start','op':'literal','value':'100'},{'id':'end','op':'literal','value':'107.5'},{'id':'r','op':'return_pct','args':['start','end']}],'output':'r'}
  self.assertEqual(execute_plan(p)['value'],'15/2')
if __name__=='__main__':unittest.main()
