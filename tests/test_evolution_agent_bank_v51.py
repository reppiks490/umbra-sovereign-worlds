import unittest,tempfile
from pathlib import Path
import evolution_agent_bank_v51 as m
class Tests(unittest.TestCase):
 def test_geometry(self):
  import torch
  net=m.model(torch,1)
  self.assertEqual(sum(p.numel() for p in net.parameters()),1500000)
  self.assertEqual(m.TARGET*m.WIDTH,30000000000)
 def test_training_and_tampering(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);r=m.train(root,1,2)
   self.assertEqual(r['parameters'],1500000)
   self.assertEqual(m.verify(root/'00001')['agent'],1)
   with self.assertRaises(FileExistsError):m.train(root,1,2)
   f=root/'00001'/'weights.fp16';b=bytearray(f.read_bytes());b[0]^=1;f.write_bytes(b)
   with self.assertRaises(ValueError):m.verify(root/'00001')
if __name__=='__main__':unittest.main()
