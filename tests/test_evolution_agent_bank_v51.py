import unittest,tempfile,json,copy
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
class IntegrityTests(unittest.TestCase):
 def fixture(self,root):
  folder=root/'00001';folder.mkdir()
  raw=bytes(m.WIDTH);(folder/'weights.fp16').write_bytes(raw)
  before={s:{'mse':2.0,'zero_mse':1.0} for s in ('holdout','shift')}
  after={s:{'mse':0.5,'zero_mse':1.0} for s in ('holdout','shift')}
  r={'schema':'myriad.fresh_agent_bank.v51','agent':1,'parameters':m.PARAMETERS,
     'weight_bytes':m.WIDTH,'source_sha256':'a'*64,'weight_sha256':m.sha(raw),
     'steps':32,'before':before,'after':after,'review_eligible_synthetic':True,
     'scope':'synthetic regression only; no historical weights recovered',
     'production_authority':False,'auto_promote':False}
  self.write(folder,r)
  return folder,r
 def write(self,folder,r):
  r=dict(r);r.pop('receipt_sha256',None);r['receipt_sha256']=m.sha(m.canonical(r))
  (folder/'receipt.json').write_bytes(m.canonical(r))
 def test_valid_structural_fixture(self):
  with tempfile.TemporaryDirectory() as t:
   folder,r=self.fixture(Path(t));self.assertEqual(m.verify(folder)['steps'],32)
 def test_resigned_inconsistent_metadata_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   folder,base=self.fixture(Path(t))
   for field,value in [('agent',True),('parameters',float(m.PARAMETERS)),('steps',0),('steps',129),('steps',True),('weight_bytes',0),('source_sha256','broken'),('review_eligible_synthetic','true'),('review_eligible_synthetic',False),('scope','semantic mastery'),('extra',1)]:
    with self.subTest(field=field,value=value):
     r=copy.deepcopy(base);r[field]=value;self.write(folder,r)
     with self.assertRaises(ValueError):m.verify(folder)
 def test_inconsistent_metrics_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   folder,base=self.fixture(Path(t))
   for field,value in [('mse',-0.5),('mse',True),('zero_mse',2.0)]:
    with self.subTest(field=field,value=value):
     r=copy.deepcopy(base);r['after']['holdout'][field]=value;self.write(folder,r)
     with self.assertRaises(ValueError):m.verify(folder)
 def test_replay_reconstructs_initial_checkpoint(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);r=m.train(root,1,2);folder=root/'00001'
   self.assertEqual(m.verify(folder,True)['agent'],1)
   r['source_sha256']='a'*64;self.write(folder,r)
   with self.assertRaises(ValueError):m.verify(folder,True)
if __name__=='__main__':unittest.main()
