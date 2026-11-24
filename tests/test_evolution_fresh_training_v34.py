import tempfile,unittest,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import evolution_fresh_training_v34 as m
class Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name)
 def test_requires_explicit_authority(self):
  with self.assertRaises(PermissionError):m.run(self.root,agents=1,steps=2)
 def test_real_training_and_continuation(self):
  a=m.run(self.root,agents=1,steps=2,authorize=True)[0]
  b=m.run(self.root,agents=1,steps=2,authorize=True)[0]
  self.assertEqual(a['parameter_count'],411000);self.assertEqual(a['generation'],1);self.assertEqual(b['generation'],2)
  self.assertEqual(b['source_sha256'],a['candidate_sha256']);self.assertNotEqual(a['source_sha256'],a['candidate_sha256'])
  self.assertFalse(b['historic_bank_recovered']);self.assertFalse(b['production_authority'])
  self.assertTrue(m.latest(self.root,1)['candidate_sha256']==b['candidate_sha256'])
 def test_corrupt_checkpoint_refused(self):
  m.run(self.root,agents=1,steps=2,authorize=True)
  p=self.root/'NEW-00001'/'000001'/'weights.fp16';raw=p.read_bytes();p.write_bytes(bytes([raw[0]^1])+raw[1:])
  with self.assertRaises(ValueError):m.latest(self.root,1)
 def test_invalid_budget(self):
  with self.assertRaises(ValueError):m.run(self.root,agents=9,steps=2,authorize=True)
  with self.assertRaises(ValueError):m.run(self.root,agents=1,steps=129,authorize=True)
if __name__=='__main__':unittest.main()
