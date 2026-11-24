"""Determinism, budget, numerical safety and method separation for seven optimizers."""
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from evolution_algorithms_v20 import METHODS_V20, REFERENCES, benchmark, optimize_v20, chol, triangular_solve
from evolution_algorithms_v19 import task

class TestV20Methods(unittest.TestCase):
 def test_seven_different_named_algorithms_provenance(self):
  self.assertEqual(len(METHODS_V20),7)
  self.assertEqual(len(set(METHODS_V20)),7)
  self.assertEqual(set(METHODS_V20),set(REFERENCES))
  self.assertTrue(all(u.startswith('https://') for u in REFERENCES.values()))

 def test_every_method_reproducible_and_no_authority(self):
  fn=task('shifted-sphere',dimension=5,seed=17)
  for name in METHODS_V20:
   with self.subTest(algorithm=name):
    a=optimize_v20(name,fn,dimension=5,budget=36,seed=11)
    b=optimize_v20(name,fn,dimension=5,budget=36,seed=11)
    self.assertEqual(a,b)
    self.assertEqual(a.schema,'umbra.independent.optimizer.v2')
    self.assertLessEqual(a.evaluations,36)
    self.assertGreaterEqual(a.evaluations,1)
    self.assertGreaterEqual(a.score,fn([.5]*5)-1e-9)
    self.assertFalse(a.real_model_weights_changed)
    self.assertFalse(a.original_invention_claim)
    self.assertEqual(a.live_trades,0)
    self.assertTrue(all(math.isfinite(x) and 0<=x<=1 for x in a.best))

 def test_invalid_objectives_and_budgets_fail(self):
  with self.assertRaises(ValueError):optimize_v20('made-up',lambda v:0)
  with self.assertRaises(ValueError):optimize_v20('halton-qmc',lambda v:0,budget=1000)
  with self.assertRaises(ValueError):optimize_v20('halton-qmc',lambda v:0,dimension=17)
  with self.assertRaises(ValueError):optimize_v20('halton-qmc',lambda v:float('nan'))

 def test_cholesky_linear_solve(self):
  A=[[2.,.5],[.5,3.]];L=chol(A);x=triangular_solve(L,[1.,-2.])
  self.assertAlmostEqual(2*x[0]+.5*x[1],1,places=6)
  self.assertAlmostEqual(.5*x[0]+3*x[1],-2,places=6)

 def test_benchmark_reproducible_with_unique_case_ids(self):
  a=benchmark(budget=24,seeds=1,dimension=3)
  b=benchmark(budget=24,seeds=1,dimension=3)
  self.assertEqual(a,b)
  self.assertEqual(a['case_count'],35)
  self.assertFalse(a['production_merge_authorized'])
  self.assertTrue(a['synthetic_only'])

if __name__=='__main__':unittest.main()
