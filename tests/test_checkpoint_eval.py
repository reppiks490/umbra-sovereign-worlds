import json,math,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'mcp'))
import checkpoint_eval as m
import myriad_agent_bank_v51 as bank
class Tests(unittest.TestCase):
 def test_arguments(self):
  for a in ({'agent':True},{'agent':0},{'agent':1,'features':[0]*31},{'agent':1,'features':[math.nan]*32},{'agent':1,'features':[5]*32},{'agent':1,'path':'/tmp'}):
   with self.assertRaises(ValueError):m.validate(a)
 def test_real_weight_forward_and_tamper(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);bank.train(root,1,1)
   r=m.evaluate(root,{'agent':1,'features':[0.25]*32})
   self.assertTrue(r['replayed']);self.assertEqual(r['parameters'],1500000);self.assertEqual(len(r['prediction']),8)
   self.assertTrue(all(math.isfinite(v) for v in r['prediction']));self.assertFalse(r['production_authority'])
   p=root/'00001'/'weights.fp16';b=bytearray(p.read_bytes());b[0]^=1;p.write_bytes(b)
   with self.assertRaises(ValueError):m.evaluate(root,{'agent':1})
 def test_missing(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises((ValueError,OSError)):m.evaluate(Path(d),{'agent':1})
if __name__=='__main__':unittest.main()
