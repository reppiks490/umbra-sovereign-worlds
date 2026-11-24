import unittest,tempfile
from pathlib import Path
import evolution_algorithm_distill_v57 as m
class Tests(unittest.TestCase):
 def test_targets(self):
  for i in range(8):
   self.assertIsInstance(m.target(i,[float(x+1) for x in range(16)]),float)
 def test_distinct_split_and_model(self):
  import torch
  a,b=m.data(torch,1,'train',32);c,d=m.data(torch,1,'holdout',32)
  self.assertEqual(a.shape,(32,16));self.assertFalse(torch.equal(a,c))
  self.assertFalse(torch.equal(m.features(torch,a,1),m.features(torch,a,2)))
 def test_train_verify_and_tamper(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);r=m.train(p,1,2,4)
   self.assertEqual(r['rows'],2);self.assertEqual(r['weight_bytes'],2000)
   self.assertEqual(m.verify(p/'00001',True)['rows'],2)
   f=p/'00001'/'weights.fp16';b=bytearray(f.read_bytes());b[0]^=1;f.write_bytes(b)
   with self.assertRaises(ValueError):m.verify(p/'00001')
if __name__=='__main__':unittest.main()
