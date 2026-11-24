import pathlib,sys,tempfile,json,unittest,importlib.util
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import evolution_multitask_v32 as m

class CurriculumTests(unittest.TestCase):
 @unittest.skipUnless(importlib.util.find_spec("torch") is not None,"PyTorch not installed in source-only CI")
 def test_seed_families_disjoint(self):
  import torch
  a=m.batch(torch,100,1,'train',16)
  b=m.batch(torch,100,1,'cross',16)
  c=m.batch(torch,100,1,'novel',16)
  self.assertNotEqual(m.sha(a[0].numpy().tobytes()),m.sha(b[0].numpy().tobytes()))
  self.assertNotEqual(m.sha(a[0].numpy().tobytes()),m.sha(c[0].numpy().tobytes()))
 @unittest.skipUnless(importlib.util.find_spec("torch") is not None,"PyTorch not installed in source-only CI")
 def test_training_has_compositional_factor_diversity_without_blind_pair(self):
  import torch
  x,_=m.batch(torch,100,1,'train',512)
  a,b,c=x[:,8:16].sign(),x[:,16:24].sign(),x[:,24:32].sign()
  sb=(a[:,0]!=b[:,0]);sc=(a[:,0]!=c[:,0])
  self.assertTrue(sb.any())
  self.assertTrue(sc.any())
  self.assertFalse((sb & sc).any(), 'Blind double-opposition combination leaked into training')
 @unittest.skipUnless(importlib.util.find_spec("torch") is not None,"PyTorch not installed in source-only CI")
 def test_baseline_nontrivial(self):
  import torch
  x,y=m.batch(torch,100,1,'cross',100)
  self.assertGreater(torch.mean((y-x[:,8:16]*x[:,0:8])**2).item(),.1)
 @unittest.skipUnless(importlib.util.find_spec("torch") is not None,"PyTorch not installed in source-only CI")
 def test_unknown_family_rejected(self):
  import torch
  with self.assertRaises(ValueError):m.batch(torch,100,1,'fake',32)
 def test_budgets_guard(self):
  for n,steps,seed in ((0,12,8),(11,12,8),(10,0,8),(10,257,8),(1,20,-1)):
   with self.assertRaises(ValueError):m.valid(n,steps,seed)
 def test_training_requires_permission(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(PermissionError):m.train('missing.zip',d,agents=1,steps=2,authorize=False)
 @unittest.skipUnless(importlib.util.find_spec("torch") is not None,"PyTorch not installed in source-only CI")
 def test_holdout_teacher_algebra(self):
  import torch
  x,y=m.batch(torch,100,1,'train',64)
  z,a,b,c=x[:,0:8],x[:,8:16],x[:,16:24],x[:,24:32]
  self.assertTrue(torch.allclose(y,a*z+b*torch.tanh(z)+c*(z*z-1)))
 @unittest.skipUnless(importlib.util.find_spec("torch") is not None,"PyTorch not installed in source-only CI")
 def test_novel_teacher_not_same(self):
  import torch
  x,y=m.batch(torch,100,1,'novel',64)
  z,a,b,c=x[:,0:8],x[:,8:16],x[:,16:24],x[:,24:32]
  self.assertFalse(torch.allclose(y,a*z+b*torch.tanh(z)+c*(z*z-1)))
if __name__=='__main__':unittest.main()
