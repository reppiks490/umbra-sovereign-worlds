import tempfile,unittest
from pathlib import Path
import evolution_agent_bank_v51 as base
import evolution_task_adapter_v61 as m
class Tests(unittest.TestCase):
 def test_frozen_source_and_exact_retention(self):
  import torch
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);base.train(p/'source',1,2)
   r=m.train(p/'source',p/'adapters',1,4)
   self.assertEqual(r['source_sha256'],base.verify(p/'source'/'00001')['weight_sha256'])
   self.assertEqual(r['retention_max_delta'],0.)
   self.assertEqual(m.verify(p/'source',p/'adapters'/'00001',True)['agent'],1)
   self.assertGreater(r['parameters'],0)
   with self.assertRaises(FileExistsError):m.train(p/'source',p/'adapters',1,4)
   f=p/'adapters'/'00001'/'adapter.fp16';b=bytearray(f.read_bytes());b[0]^=1;f.write_bytes(b)
   with self.assertRaises(ValueError):m.verify(p/'source',p/'adapters'/'00001')
 def test_task_selection_fail_closed(self):
  import torch
  x=torch.zeros(1,32);s=base.model(torch,1);a=m.model(torch,1)
  self.assertTrue(torch.equal(m.predict(s,a,x,'original'),s(x)))
  with self.assertRaises(ValueError):m.predict(s,a,x,'unknown')
if __name__=='__main__':unittest.main()
