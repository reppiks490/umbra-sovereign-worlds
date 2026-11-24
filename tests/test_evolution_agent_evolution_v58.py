import tempfile,unittest
from pathlib import Path
import evolution_agent_bank_v51 as old
import evolution_agent_evolution_v58 as m
class Tests(unittest.TestCase):
 def test_generation_lineage_and_replay(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);old.train(p/'source',1,2)
   r=m.train(p/'source',p/'evolved',1,2)
   self.assertEqual(r['generation'],1)
   self.assertEqual(r['parent_sha256'],old.verify(p/'source'/'00001')['weight_sha256'])
   self.assertEqual(m.latest(p/'source',p/'evolved',1,True)['generation'],1)
   r2=m.train(p/'source',p/'evolved',1,2)
   self.assertEqual(r2['generation'],2)
   self.assertEqual(r2['parent_sha256'],r['weight_sha256'])
   f=p/'evolved'/'00001'/'000002'/'weights.fp16';raw=bytearray(f.read_bytes());raw[0]^=1;f.write_bytes(raw)
   with self.assertRaises(ValueError):m.latest(p/'source',p/'evolved',1)
 def test_new_teacher_disjoint(self):
  import torch
  x,y=m.data(torch,1,1,'train',32);u,v=m.data(torch,1,1,'holdout',32)
  self.assertFalse(torch.equal(x,u))
  self.assertEqual(y.shape,(32,8))
if __name__=='__main__':unittest.main()
