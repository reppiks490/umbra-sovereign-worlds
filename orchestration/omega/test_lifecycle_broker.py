import tempfile,pathlib,unittest,json,hashlib,concurrent.futures
from omega_ledger import Ledger
from claim_broker import sign_request
from lifecycle_broker import LifecycleBroker,sign_transition
class LifecycleTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name);self.l=Ledger(self.root/'db.sqlite')
  self.l.add('a','ICARUS','a'*40,'task',(.5,)*5+(0,),'',[])
  self.keys={'worker':b'w'*32,'reviewer':b'r'*32,'outsider':b'o'*32}
  self.policy={'worker':['ICARUS'],'reviewer':['ICARUS'],'outsider':['UMBRA']}
  self.roles={'worker':'worker','reviewer':'reviewer','outsider':'worker'}
  self.b=LifecycleBroker(self.l,'isolated',self.keys,self.policy,self.roles)
  self.e=self.root/'evidence';self.e.mkdir()
 def tearDown(self):self.tmp.cleanup()
 def claim(self,**kw):
  r={'schema':1,'broker':'isolated','principal':'worker','action':'claim','lane':'ICARUS','task':'a','base':'a'*40,'issued_at':100,'nonce':'1'*32,**kw}
  return self.b.claim(r,sign_request(r,self.keys[r['principal']]),now=100)
 def receipt(self,a):
  f=self.e/'out.txt';f.write_text('fixture output')
  p=self.e/'receipt.json';p.write_text(json.dumps({'task':'a','base':'a'*40,'token':a['token'],'outcome':'passed','handle':None,'artifacts':[{'path':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}]}))
  return hashlib.sha256(p.read_bytes()).hexdigest()
 def report(self,a,**kw):
  return {'schema':1,'broker':'isolated','principal':'worker','action':'report','lane':'ICARUS','task':'a','base':'a'*40,'issued_at':100,'nonce':'2'*32,'token':a['token'],'receipt_path':'receipt.json','receipt_sha256':self.receipt(a),'detail':'observed fixture',**kw}
 def review(self,sha,**kw):
  return {'schema':1,'broker':'isolated','principal':'reviewer','action':'review','lane':'ICARUS','task':'a','base':'a'*40,'issued_at':100,'nonce':'3'*32,'worker':'worker','receipt_sha256':sha,'detail':'fixture review',**kw}
 def apply(self,r,signature=None,now=100):
  return self.b.transition(r,signature or sign_transition(r,self.keys[r['principal']]),now=now)
 def test_signed_lifecycle_and_dependency(self):
  a=self.claim();r=self.report(a)
  self.assertEqual(self.apply(r)['state'],'reported')
  self.assertEqual(self.apply(self.review(r['receipt_sha256']))['state'],'qualified')
  self.assertEqual(self.l.snapshot()[0]['verifier'],'reviewer')
 def test_report_tamper_and_wrong_owner(self):
  a=self.claim();r=self.report(a)
  with self.assertRaises(ValueError):self.apply({**r,'detail':'changed'},sign_transition(r,self.keys['worker']))
  with self.assertRaises(ValueError):self.apply({**r,'principal':'outsider'})
  self.assertEqual(self.l.snapshot()[0]['state'],'leased')
 def test_legacy_claim_is_not_broker_owned(self):
  a=self.l.claim('ICARUS','worker',100)
  with self.assertRaises(ValueError):self.apply(self.report(a))
 def test_review_before_report_and_worker_self_review(self):
  a=self.claim();r=self.report(a)
  with self.assertRaises(ValueError):self.apply(self.review(r['receipt_sha256']))
  self.apply(r)
  with self.assertRaises(ValueError):self.apply(self.review(r['receipt_sha256'],principal='worker'))
 def test_receipt_mutation_and_path_escape(self):
  a=self.claim();r=self.report(a)
  with self.assertRaises(ValueError):self.apply({**r,'receipt_path':'../evidence/receipt.json'})
  self.e.joinpath('out.txt').write_text('changed')
  with self.assertRaises(ValueError):self.apply(r)
 def test_review_revalidates_evidence(self):
  a=self.claim();r=self.report(a);self.apply(r)
  self.e.joinpath('out.txt').write_text('changed')
  with self.assertRaises(ValueError):self.apply(self.review(r['receipt_sha256']))
  self.assertEqual(self.l.snapshot()[0]['state'],'reported')
 def test_replay_cross_action_and_restart(self):
  a=self.claim();r=self.report(a)
  with self.assertRaisesRegex(ValueError,'replay'):self.apply({**r,'nonce':'1'*32})
  self.apply(r)
  self.b=LifecycleBroker(Ledger(self.root/'db.sqlite'),'isolated',self.keys,self.policy,self.roles)
  with self.assertRaisesRegex(ValueError,'replay'):self.apply(r)
 def test_active_handle_and_stale_request(self):
  a=self.claim();r=self.report(a)
  with self.assertRaises(ValueError):self.apply(r,now=161)
  self.l.handle('a',a['token'],'pid:123')
  with self.assertRaises(ValueError):self.apply(r)
 def test_review_role_cannot_claim(self):
  with self.assertRaises(ValueError):self.claim(principal='reviewer')
 def test_legacy_report_is_not_broker_report(self):
  a=self.claim();r=self.report(a)
  self.l.finish('a',a['token'],str(self.e/'receipt.json'),'legacy')
  with self.assertRaises(ValueError):self.apply(self.review(r['receipt_sha256']))
 def test_wrong_receipt_binding_does_not_consume_nonce(self):
  a=self.claim();r=self.report(a)
  with self.assertRaises(ValueError):self.apply({**r,'receipt_sha256':'b'*64})
  self.assertEqual(self.apply(r)['state'],'reported')
 def test_only_one_concurrent_report(self):
  a=self.claim();r=self.report(a)
  def call(i):
   try:return self.apply({**r,'nonce':f'{i+100:032x}'})
   except ValueError:return None
  with concurrent.futures.ThreadPoolExecutor(max_workers=8) as e:results=list(e.map(call,range(24)))
  self.assertEqual(sum(x is not None for x in results),1)
