import sys,pathlib,unittest,math,tempfile,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from campaign_baselines import execute,benchmark,LANES
class ScientificBaselines(unittest.TestCase):
 def test_causal_stratification_counterexample(self):
  # Treatment assignment is confounded; within each stratum true effect +1.
  rows=[['a',1,2],['a',0,1],['a',0,1],['b',1,11],['b',1,11],['b',0,10]]
  r=execute('stratified_effect',{'rows':rows})
  self.assertAlmostEqual(r['estimate'],1)
  self.assertNotAlmostEqual(r['naive'],1)
  self.assertRaises(ValueError,execute,'stratified_effect',{'rows':[['a',1,2]]})
 def test_forecast_chronological_holdout(self):
  r=execute('forecast',{'train':[1,3,5,7],'horizon':2})
  self.assertEqual(r['prediction'],[9,11])
  self.assertRaises(ValueError,execute,'forecast',{'train':[1,float('nan')],'horizon':1})
 def test_exact_calculation(self):
  self.assertEqual(execute('rational',{'terms':[[1,3],[1,6],[-1,2]]})['value'],'0')
  self.assertRaises(ValueError,execute,'rational',{'terms':[[1,0]]})
 def test_graph_shortest_path(self):
  self.assertEqual(execute('shortest_path',{'edges':[['a','b',5],['a','c',1],['c','b',2]],'source':'a','target':'b'})['cost'],3)
  self.assertRaises(ValueError,execute,'shortest_path',{'edges':[['a','b',-1]],'source':'a','target':'b'})
 def test_evolution_optimization_reference(self):
  self.assertEqual(execute('knapsack',{'items':[[2,3],[3,4],[4,5]],'capacity':5})['value'],7)
 def test_bayesian_inference(self):
  self.assertAlmostEqual(execute('bayes',{'prior':.1,'sensitivity':.9,'false_positive':.1})['posterior'],.5)
 def test_suite_records_real_results_not_neural_claims(self):
  r=benchmark()
  self.assertEqual(set(r['lanes']),set(LANES))
  self.assertTrue(all(v['passed']==v['cases'] and v['cases']>=3 for v in r['lanes'].values()))
  self.assertFalse(r['neural_inference_verified'])
  self.assertFalse(r['training_verified'])
