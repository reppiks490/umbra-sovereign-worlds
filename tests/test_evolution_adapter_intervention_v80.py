import tempfile,unittest,json
from pathlib import Path
import torch
import evolution_agent_bank_v51 as base
import evolution_task_adapter_v61 as prior
import evolution_adapter_intervention_v80 as m
class Tests(unittest.TestCase):
 def test_disjoint_frozen_design(self):
  torch.set_num_threads(1)
  x,y=m.dataset(torch,1,'mixed',64)
  a,b=m.dataset(torch,1,'iid',64)
  self.assertEqual(x.shape,a.shape);self.assertEqual(y.shape,b.shape)
  self.assertFalse(torch.equal(x,a))
  for f in m.TEST_FAMILIES:
   u,v=m.test_data(torch,1,f,0,64)
   self.assertEqual(u.shape,(64,32));self.assertEqual(v.shape,(64,8))
   self.assertTrue(torch.isfinite(v).all())
   self.assertFalse(torch.equal(u,x[:64]))
   self.assertFalse(torch.equal(u,m.test_data(torch,1,f,1,64)[0]))
 def test_bounds(self):
  for args in [(True,4),(1,0),(1,513),(0,4)]:
   with self.assertRaises(ValueError):m.bounds(*args)
 def test_actual_matched_training_replay_and_tamper(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);base.train(p/'source',1,2);prior.train(p/'source',p/'prior',1,4)
   source_path=p/'source'/'00001'/'weights.fp16';prior_path=p/'prior'/'00001'/'adapter.fp16'
   source_hash=base.sha(source_path.read_bytes());prior_hash=base.sha(prior_path.read_bytes())
   r=m.train_compare(p/'source',p/'prior',p/'out',1,4)
   self.assertEqual(r['steps_per_arm'],4)
   self.assertEqual(r['summary']['observations'],16)
   self.assertEqual(r['summary']['retention_failures'],0)
   self.assertFalse(r['production_authority']);self.assertFalse(r['auto_promote'])
   self.assertEqual(base.sha(source_path.read_bytes()),source_hash)
   self.assertEqual(base.sha(prior_path.read_bytes()),prior_hash)
   dest=p/'out'/'00001'
   self.assertEqual(m.verify(p/'source',p/'prior',dest,True)['receipt_sha256'],r['receipt_sha256'])
   with self.assertRaises(FileExistsError):m.train_compare(p/'source',p/'prior',p/'out',1,4)
   f=dest/'mixed.fp16';b=bytearray(f.read_bytes());b[0]^=1;f.write_bytes(b)
   with self.assertRaises(ValueError):m.verify(p/'source',p/'prior',dest)
 def test_summary_does_not_count_ties(self):
  rows=[dict(family=f,seed=s,mixed=1.,iid=1.,prior=1.,quadratic=1.,source=1.,zero=1.,retention_delta=0.) for f in m.TEST_FAMILIES for s in range(4)]
  self.assertEqual(m.summarize(rows)['mixed_wins_vs_iid'],0)
  self.assertEqual(m.summarize(rows)['mixed_wins_vs_all'],0)
  rows[0]['mixed']=.5
  self.assertEqual(m.summarize(rows)['mixed_wins_vs_all'],1)
  with self.assertRaises(ValueError):m.summarize(rows[:-1])
  with self.assertRaises(ValueError):m.summarize(rows+rows[:1])
if __name__=='__main__':unittest.main()
