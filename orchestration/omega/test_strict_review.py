import hashlib,json,pathlib,subprocess,sys,tempfile,unittest
from omega_ledger import Ledger,canonical
from local_process import capture
from strict_review import accept_pinned
class StrictReviewTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name);self.l=Ledger(self.root/'db.sqlite')
  self.l.add('a','ICARUS','a'*40,'test',(.5,)*5+(0,),'compute',[])
  self.l.add('b','MYRIAD','b'*40,'dependent',(.5,)*5+(0,),'compute',['a'])
  self.a=self.l.claim('ICARUS','worker',100);self.token=self.a['token']
  self.e=self.root/'evidence';self.e.mkdir();self.r=self.root/'review';self.r.mkdir();(self.r/'locks').mkdir()
  self.policy={'schema':1,'reviewers':{'reviewer':['ICARUS']},'resource_locks':{'compute':['compute.lock']}}
 def tearDown(self):self.tmp.cleanup()
 def put(self,p,obj):
  p.write_text(json.dumps(obj),encoding='utf8');return hashlib.sha256(p.read_bytes()).hexdigest()
 def report(self,handle=None):
  if handle:self.l.handle('a',self.token,handle)
  f=self.e/'out.txt';f.write_text('actual fixture result')
  p=self.e/'receipt.json';self.put(p,{'task':'a','base':'a'*40,'token':self.token,'outcome':'passed','handle':handle,'artifacts':[{'path':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}]})
  self.l.finish('a',self.token,str(p),'reported')
  a=self.l.snapshot()[0]
  return {'schema':1,'task':'a','base':a['base'],'worker':a['owner'],'receipt_sha256':a['receipt'],'handle':handle,'verifier':'reviewer','outcome':'approved','detail':'fixture review'}
 def apply(self,review,policy=None):
  pp=self.put(self.r/'policy.json',self.policy if policy is None else policy);rp=self.put(self.r/'review.json',review)
  return accept_pinned(self.l,self.r,pp,rp)
 def test_real_ledger_transition_and_dependency(self):
  r=self.report();self.apply(r)
  self.assertEqual(self.l.snapshot()[0]['state'],'qualified')
  self.assertEqual(self.l.claim('MYRIAD','other',200)['id'],'b')
 def test_unapproved_or_same_reviewer(self):
  r=self.report()
  for v in ('not-allowed','worker'):
   with self.assertRaises(ValueError):self.apply({**r,'verifier':v})
  self.assertEqual(self.l.snapshot()[0]['state'],'reported')
 def test_wrong_base_or_receipt(self):
  r=self.report()
  for k,v in [('base','c'*40),('receipt_sha256','c'*64),('worker','other'),('handle','bogus')]:
   with self.assertRaises(ValueError):self.apply({**r,k:v})
 def test_policy_and_review_pin_mismatch(self):
  r=self.report();pp=self.put(self.r/'policy.json',self.policy);rp=self.put(self.r/'review.json',r)
  with self.assertRaises(ValueError):accept_pinned(self.l,self.r,'c'*64,rp)
  with self.assertRaises(ValueError):accept_pinned(self.l,self.r,pp,'c'*64)
 def test_external_lock_blocks_release(self):
  r=self.report();(self.r/'locks'/'compute.lock').write_text('active')
  with self.assertRaises(ValueError):self.apply(r)
  self.assertIsNone(self.l.claim('MYRIAD','other',200))
 def test_unconfigured_resource_fails_closed(self):
  r=self.report()
  with self.assertRaises(ValueError):self.apply(r,{**self.policy,'resource_locks':{}})
 def test_active_process_prevents_release(self):
  p=subprocess.Popen([sys.executable,'-c','import sys; sys.stdin.read()'],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  try:
   r=self.report(canonical(capture(p.pid)))
   with self.assertRaises(ValueError):self.apply(r)
   p.stdin.close();p.wait(timeout=10)
   self.apply(r)
   self.assertEqual(self.l.snapshot()[0]['state'],'qualified')
  finally:
   if p.poll() is None:p.terminate();p.wait(timeout=10)
 def test_legacy_handle_cannot_be_strictly_released(self):
  r=self.report('pid:123')
  with self.assertRaises(ValueError):self.apply(r)
 def test_changed_worker_output_prevents_release(self):
  r=self.report();(self.e/'out.txt').write_text('tampered')
  with self.assertRaises(ValueError):self.apply(r)
