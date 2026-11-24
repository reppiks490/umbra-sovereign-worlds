import tempfile,unittest,json
from pathlib import Path
import evolution_bank_v47 as m
class Tests(unittest.TestCase):
 def test_geometry(self):
  self.assertEqual(m.ABILITIES*m.WIDTH*2,10000000000)
  self.assertEqual(m.AGENTS*m.AGENT_WIDTH*2,30000000000)
 def test_training_is_independent_and_replays(self):
  import torch
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);r=m.train(p,1,32,8)
   self.assertEqual(r['trained_rows'],32);self.assertEqual(r['weight_bytes'],32000)
   self.assertEqual(r['gradient_steps_per_row'],8)
   self.assertEqual(m.verify(p/'00000001',True)['trained_rows'],32)
   self.assertTrue(r['improved_rows']>0)
   with self.assertRaises(FileExistsError):m.train(p,1,32,8)
 def test_no_overlap(self):
  self.assertRaises(ValueError,m.bounds,2,32,8)
  self.assertRaises(ValueError,m.bounds,10000001,1,8)
 def test_tamper(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);m.train(p,1,8,4)
   f=p/'00000001'/'weights.fp16';b=bytearray(f.read_bytes());b[0]^=1;f.write_bytes(b)
   with self.assertRaises(ValueError):m.verify(p/'00000001',False)
if __name__=='__main__':unittest.main()
