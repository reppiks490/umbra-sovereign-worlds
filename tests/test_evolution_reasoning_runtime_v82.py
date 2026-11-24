import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import evolution_novel_reasoning_v81 as bench
import evolution_reasoning_runtime_v82 as m
class Tests(unittest.TestCase):
 def fixture(self,seed=4):
  c=bench.cases(seed)
  raw=json.dumps([{'id':x['id'],**bench.reference(x)} for x in c])
  return m.completed(seed,raw,'a'*64,1.25)
 def test_authenticated_replay_rejects_resigned_false_score(self):
  key=b'k'*32;r=self.fixture()
  signed=m.seal(r,key);self.assertTrue(m.verify(signed,key))
  for field,value in [('seed',True),('status','other'),('production_authority',True),('case_sha256','b'*64),('response_sha256','bad'),('seconds',-1)]:
   with self.subTest(field=field):
    x={**r,field:value}
    with self.assertRaises(ValueError):m.verify(m.seal(x,key),key)
  x=copy.deepcopy(r);x['scores']['joint_correct']=0
  with self.assertRaises(ValueError):m.verify(m.seal(x,key),key)
 def test_failure_denominator(self):
  r=m.failed(5,'score','ValueError')
  self.assertEqual(m.aggregate(r)['attempted_tasks'],4)
  self.assertEqual(m.aggregate(r)['joint_correct'],0)
  self.assertTrue(m.verify(m.seal(r,b'k'*32),b'k'*32))
  with self.assertRaises(ValueError):m.failed(5,'unknown','ValueError')
 def test_at_most_once_private_claim(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   self.assertTrue(m.reserve(root,3));self.assertFalse(m.reserve(root,3));self.assertTrue(m.reserve(root,4))
   self.assertEqual(len(list((root/'reasoning-claims-v82').glob('*.claim'))),2)
 def test_resource_deferral_creates_no_claim(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   with patch.object(m.scale,'free_mb',return_value=100):
    r=m.run(root,9000)
   self.assertEqual(r['status'],'deferred_resource_guard')
   self.assertFalse((root/'reasoning-claims-v82').exists())
 def test_inference_envelope_and_score(self):
  c=bench.cases(4)
  raw=json.dumps([{'id':x['id'],**bench.reference(x)} for x in c])
  envelope={'model':m.MODEL,'done':True,'done_reason':'stop','message':{'content':raw}}
  with patch.object(m.native,'_pin'),patch.object(m.teacher,'request',return_value=(envelope,b'raw')):
   self.assertEqual(m.infer(4)['scores']['joint_correct'],4)
  envelope['done_reason']='length'
  with patch.object(m.native,'_pin'),patch.object(m.teacher,'request',return_value=(envelope,b'raw')):
   self.assertEqual(m.infer(4)['failure_stage'],'envelope')
if __name__=='__main__':unittest.main()
