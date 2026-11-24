import unittest,tempfile
from pathlib import Path
import evolution_distill_v63 as m
class Tests(unittest.TestCase):
 def test_features_and_unseen_data(self):
  import torch
  x,y=m.data(torch,1,'train',32);u,v=m.data(torch,1,'final',32)
  self.assertFalse(torch.equal(x,u))
  self.assertEqual(m.features(torch,x,1).shape,(32,500))
  self.assertTrue(torch.isfinite(m.features(torch,x,1)).all())
 def test_train_and_replay(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);r=m.train(p,1,2,256)
   self.assertEqual(r['rows'],2);self.assertEqual(r['weight_bytes'],2000)
   self.assertEqual(m.verify(p/'00000001',True)['rows'],2)
   f=p/'00000001'/'weights.fp16';b=bytearray(f.read_bytes());b[0]^=1;f.write_bytes(b)
   with self.assertRaises(ValueError):m.verify(p/'00000001')
 def test_bounds(self):
  with self.assertRaises(ValueError):m.bounds(10000000,2,256)
  with self.assertRaises(ValueError):m.bounds(1,65,256)
if __name__=='__main__':unittest.main()
