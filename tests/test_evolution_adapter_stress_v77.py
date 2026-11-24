import unittest
import torch
import evolution_adapter_stress_v77 as m

class Tests(unittest.TestCase):
 def test_split_reproducible_and_disjoint(self):
  x,y=m.stress_data(torch,1,0,'iid',64)
  a,b=m.stress_data(torch,1,0,'iid',64)
  self.assertTrue(torch.equal(x,a) and torch.equal(y,b))
  for family in m.FAMILIES:
   q,r=m.stress_data(torch,1,1,family,64)
   self.assertEqual(tuple(q.shape),(64,32))
   self.assertEqual(tuple(r.shape),(64,8))
   self.assertFalse(torch.equal(q,x))
   self.assertTrue(torch.isfinite(r).all())
  self.assertFalse(torch.equal(x,m.stress_data(torch,2,0,'iid',64)[0]))
 def test_invalid_parameters(self):
  for args in [(True,0,'iid',64),(1,-1,'iid',64),(1,0,'unknown',64),(1,0,'iid',0)]:
   with self.assertRaises(ValueError):m.stress_data(torch,*args)
 def test_quadratic_feature_geometry(self):
  x=torch.zeros(8,32);self.assertEqual(tuple(m.features(torch,x,True).shape),(8,561))
  self.assertEqual(tuple(m.features(torch,x,False).shape),(8,33))
 def test_strict_win_and_no_false_mastery(self):
  scores=[{'family':f,'seed':s,'adapter_mse':.2,'source_mse':1.,'zero_mse':1.,'linear_mse':.4,'quadratic_mse':.1,'retention_delta':0.} for f in m.FAMILIES for s in range(2)]
  report=m.summarize(scores)
  self.assertEqual(report['wins_vs_all'],0)
  self.assertEqual(report['wins_vs_quadratic'],0)
  self.assertFalse(report['production_authority'])
  self.assertFalse(report['semantic_mastery_certified'])
  for r in scores:r['adapter_mse']=.01
  self.assertEqual(m.summarize(scores)['wins_vs_all'],8)
  scores[0]['retention_delta']=.01
  self.assertFalse(m.summarize(scores)['all_retained'])
  with self.assertRaises(ValueError):m.summarize(scores+scores[:1])
 def test_real_models_no_mutation(self):
  import evolution_agent_bank_v51 as b
  import evolution_task_adapter_v61 as a
  torch.set_num_threads(1)
  source=b.model(torch,1);adapter=a.model(torch,1)
  before=b.encode(torch,source)
  report=m.evaluate(torch,source,adapter,1,samples=64,seeds=2)
  self.assertEqual(report['tests'],8)
  self.assertEqual(report['retention_failures'],0)
  self.assertEqual(before,b.encode(torch,source))
if __name__=='__main__':unittest.main()
