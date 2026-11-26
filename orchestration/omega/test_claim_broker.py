import tempfile,pathlib,unittest,concurrent.futures
from omega_ledger import Ledger
from claim_broker import ClaimBroker,sign_request
class BrokerTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=pathlib.Path(self.tmp.name)/'ledger.sqlite';self.l=Ledger(self.path)
  self.keys={'worker':b'w'*32,'other':b'o'*32}
  self.policy={'worker':['ICARUS'],'other':['UMBRA']}
  self.b=ClaimBroker(self.l,'sandbox-1',self.keys,self.policy)
  self.add('a')
 def tearDown(self):self.tmp.cleanup()
 def add(self,k,lane='ICARUS',resource='',deps=()):
  self.l.add(k,lane,'a'*40,k,(.5,)*5+(0,),resource,list(deps))
 def req(self,**kw):
  return {'schema':1,'broker':'sandbox-1','principal':'worker','action':'claim','lane':'ICARUS','task':'a','base':'a'*40,'issued_at':100,'nonce':'1'*32,**kw}
 def call(self,r=None,key=None,now=100):
  r=self.req() if r is None else r
  return self.b.claim(r,sign_request(r,key or self.keys[r['principal']]),now=now)
 def test_authenticated_claim(self):
  x=self.call();self.assertEqual(x['owner'],'worker');self.assertEqual(self.l.snapshot()[0]['state'],'leased')
 def test_wrong_signature_or_tampering(self):
  r=self.req()
  with self.assertRaises(ValueError):self.call(r,b'x'*32)
  sig=sign_request(r,self.keys['worker'])
  with self.assertRaises(ValueError):self.b.claim({**r,'nonce':'2'*32},sig,now=100)
 def test_lane_and_broker_scope(self):
  for r in (self.req(lane='UMBRA'),self.req(broker='other-broker'),self.req(principal='other')):
   with self.assertRaises(ValueError):self.call(r)
 def test_expired_future_and_schema(self):
  for r in (self.req(issued_at=0),self.req(issued_at=101),self.req(schema=True),self.req(extra='x')):
   with self.assertRaises(ValueError):self.call(r)
 def test_exact_base_and_resource_gate(self):
  self.add('b',resource='compute')
  with self.assertRaises(ValueError):self.call(self.req(base='b'*40))
  with self.assertRaises(ValueError):self.call(self.req(task='b'))
  self.assertTrue(all(x['state']=='ready' for x in self.l.snapshot()))
 def test_dependency_gate(self):
  self.add('b',deps=('a',))
  with self.assertRaises(ValueError):self.call(self.req(task='b'))
 def test_replay_persists_across_restart(self):
  self.call();self.b=ClaimBroker(Ledger(self.path),'sandbox-1',self.keys,self.policy)
  with self.assertRaisesRegex(ValueError,'replay'):self.call()
 def test_replay_and_claim_atomic(self):
  with self.assertRaises(ValueError):self.call(self.req(task='missing'))
  self.assertEqual(self.call()['id'],'a')
 def test_concurrent_signed_requests(self):
  def work(i):
   try:return self.call(self.req(nonce=f'{i:032x}'))
   except ValueError:return None
  with concurrent.futures.ThreadPoolExecutor(max_workers=8) as e:rows=list(e.map(work,range(24)))
  self.assertEqual(sum(x is not None for x in rows),1)
 def test_invalid_key_configuration(self):
  with self.assertRaises(ValueError):ClaimBroker(self.l,'sandbox-1',{'worker':b'short'},self.policy)
  with self.assertRaises(ValueError):ClaimBroker(self.l,'sandbox-1',{'worker':b'x'*32,'other':b'x'*32},self.policy)
