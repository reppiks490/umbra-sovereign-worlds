import pathlib,sys,unittest,math
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from chronos_tournament import simulate,tournament,synthetic,Config
class ChronosTest(unittest.TestCase):
 def test_signal_uses_previous_close_and_costs(self):
  r=simulate([100,101,102,103,104,105],Config('trend',2,0),2,6,10)
  self.assertEqual(r['trades'][0]['signal_index'],1)
  self.assertEqual(r['trades'][0]['fill_index'],2)
  self.assertGreater(r['cost'],0)
  self.assertLess(r['net_return'],r['gross_return'])
 def test_future_values_do_not_change_prefix(self):
  a=[100,101,102,103,104,105,106,107]
  b=a[:5]+[70,80,90]
  x=simulate(a,Config('trend',2,0),2,8,5)
  y=simulate(b,Config('trend',2,0),2,8,5)
  self.assertEqual(x['positions'][:3],y['positions'][:3])
 def test_holdout_not_used_in_selection(self):
  prices=synthetic(7,'trend',240)
  altered=prices[:180]+[100.0]*60
  a=tournament(prices,180,10)
  b=tournament(altered,180,10)
  self.assertEqual(a['selected'],b['selected'])
  self.assertEqual(a['selection_score'],b['selection_score'])
 def test_no_authority_and_stress_receipts(self):
  a=tournament(synthetic(8,'reversal',240),180,10)
  self.assertFalse(a['production_authority'])
  self.assertTrue(a['synthetic_only'])
  self.assertEqual(len(a['cost_stress']),3)
  self.assertGreaterEqual(a['holdout']['max_drawdown'],0)
 def test_invalid_data(self):
  for a in ([100,0,105],[100,math.nan,105],[100,-1,105]):
   with self.assertRaises(ValueError):simulate(a,Config('trend',2,0),2,len(a),5)
