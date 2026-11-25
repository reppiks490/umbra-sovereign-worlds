import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from observed_research import evaluate,parse_airline,parse_market
class ObservedResearchTest(unittest.TestCase):
 def test_strict_month_order(self):
  self.assertEqual(parse_airline(b'Date,Passengers\n1949-01,112\n1949-02,118\n'),[112.,118.])
  with self.assertRaises(ValueError):parse_airline(b'Date,Passengers\n1949-02,118\n1949-01,112\n')
 def test_market_schema_and_order(self):
  h=b'timestamps,open,close,high,low,volume,amount\n'
  rows=h+b'2019/11/26 9:35,100,101,102,99,10,0\n2019/11/26 9:40,101,102,103,100,20,0\n'
  self.assertEqual(parse_market(rows)[0],[101.,102.])
  with self.assertRaises(ValueError):parse_market(rows+b'2019/11/26 9:40,101,102,103,100,20,0\n')
  with self.assertRaises(ValueError):parse_market(h+b'2019/11/26 9:35,100,101,99,100,10,0\n')
 def test_future_data_does_not_affect_fit(self):
  a=[float(100+i) for i in range(100)]
  b=a[:80]+[1000.]*20
  r=evaluate(a,80,1);s=evaluate(b,80,1)
  self.assertEqual(r['selected'],s['selected'])
  self.assertEqual(r['selection_mae'],s['selection_mae'])
  self.assertEqual(r['fit_digest'],s['fit_digest'])
  self.assertNotEqual(r['holdout_mae'],s['holdout_mae'])
 def test_no_execution_or_training_claim(self):
  r=evaluate([float(100+i) for i in range(100)],80,1)
  self.assertFalse(r['production_authority'])
  self.assertFalse(r['neural_weight_training'])
