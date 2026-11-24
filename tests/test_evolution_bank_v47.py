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
class ReceiptIntegrityTests(unittest.TestCase):
 def fixture(self,root):
  p=root/'00000001';p.mkdir()
  raw=bytes(8000);(p/'weights.fp16').write_bytes(raw)
  r={'schema':'myriad.synthetic_ability_shard.v47','start':1,'trained_rows':8,'parameters_per_row':500,'weight_bytes':8000,'gradient_steps_per_row':4,'gradient_row_updates':32,'weight_sha256':m.sha(raw),'heldout_projections_per_row':12,'mean_mse':.1,'zero_mean_mse':.2,'improved_rows':8,'semantic_skills_certified':0,'production_authority':False,'historical_bank_recovered':False}
  self.write(p,r);return p,r
 def write(self,p,r):
  r=dict(r);r.pop('receipt_sha256',None);r['receipt_sha256']=m.sha(m.canonical(r))
  (p/'receipt.json').write_bytes(m.canonical(r))
 def test_recomputed_checksum_cannot_inflate_counters(self):
  with tempfile.TemporaryDirectory() as t:
   p,r=self.fixture(Path(t))
   self.assertEqual(m.status(Path(t))['row_updates'],32)
   for k,v in [('gradient_row_updates',1000000000),('weight_bytes',999999),('parameters_per_row',600),('heldout_projections_per_row',0),('improved_rows',9),('improved_rows',-1),('improved_rows',True),('semantic_skills_certified',False),('historical_bank_recovered',True),('mean_mse',-1),('zero_mean_mse',True),('extra',1)]:
    with self.subTest(field=k,value=v):
     self.write(p,{**r,k:v})
     with self.assertRaises(ValueError):m.verify(p)
 def test_duplicate_receipt_fields_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   p,r=self.fixture(Path(t));f=p/'receipt.json';f.write_text(f.read_text().replace('"trained_rows":8','"trained_rows":7,"trained_rows":8'))
   with self.assertRaises(ValueError):m.verify(p)
if __name__=='__main__':unittest.main()
