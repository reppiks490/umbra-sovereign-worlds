import tempfile,unittest,pathlib,concurrent.futures,json,hashlib
import omega_ledger as m
class LedgerTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.p=pathlib.Path(self.tmp.name)/'ledger.sqlite'
  self.l=m.Ledger(self.p)
 def tearDown(self):self.tmp.cleanup()
 def add(self,k,lane='ICARUS',deps=(),priority=(.5,.5,.5,.5,.5,0),resource=''):
  return self.l.add(k,lane,'a'*40,k,priority,resource,list(deps))
 def complete(self,k,claim,handle=None):
  e=self.p.parent/'evidence';e.mkdir(exist_ok=True);f=e/(k+'.txt');f.write_text('fixture output')
  r=e/(k+'.json');r.write_text(json.dumps({'task':k,'base':'a'*40,'token':claim['token'],'outcome':'passed','handle':handle,'artifacts':[{'path':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}]}))
  self.l.finish(k,claim['token'],str(r),'fixture reported')
  self.l.accept(k,'reviewer','fixture reviewed', 'fixture process completed' if handle else None)
 def test_idempotency_and_changed_identity(self):
  self.add('a');self.add('a')
  self.assertEqual(len(self.l.snapshot()),1)
  with self.assertRaises(ValueError):self.l.add('a','UMBRA','a'*40,'a',(.5,)*5+(0,),'',[])
 def test_dependency_and_priority(self):
  self.add('parent',priority=(0,0,0,0,0,0));self.add('child',deps=('parent',),priority=(1,1,1,1,1,0));self.add('other',priority=(.5,.5,.5,.5,.5,0))
  self.assertEqual(self.l.claim('ICARUS','one',100)['id'],'other')
  self.assertEqual(self.l.claim('ICARUS','two',100)['id'],'parent')
  self.assertIsNone(self.l.claim('ICARUS','three',100))
 def test_concurrent_claim_exactly_once(self):
  self.add('a')
  def claim(i):return m.Ledger(self.p).claim('ICARUS',str(i),100)
  with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:r=list(ex.map(claim,range(24)))
  self.assertEqual(sum(x is not None for x in r),1)
 def test_resource_exclusion_cross_lane(self):
  self.add('a',resource='model-compute');self.add('b','EXASOVEREIGN',resource='model-compute')
  self.assertIsNotNone(self.l.claim('ICARUS','one',100));self.assertIsNone(self.l.claim('EXASOVEREIGN','two',10000))
 def test_expiration_does_not_reclaim_live_or_unknown(self):
  self.add('a');a=self.l.claim('ICARUS','one',100)
  self.assertIsNone(m.Ledger(self.p).claim('ICARUS','two',100000))
  self.assertEqual(m.Ledger(self.p).snapshot()[0]['token'],a['token'])
 def test_persistent_handle_and_fenced_receipt(self):
  self.add('a');a=self.l.claim('ICARUS','one',100)
  self.l.handle('a',a['token'],'pid:123')
  self.assertEqual(m.Ledger(self.p).snapshot()[0]['handle'],'pid:123')
  with self.assertRaises(ValueError):self.l.finish('a','wrong','b'*64,'passed')
  with self.assertRaises(ValueError):self.l.finish('a',a['token'],'invalid','passed')
  self.complete('a',a,'pid:123')
  self.assertEqual(m.Ledger(self.p).snapshot()[0]['state'],'qualified')
 def test_blocked_requires_explicit_retry(self):
  self.add('a');a=self.l.claim('ICARUS','one',100)
  self.l.block('a',a['token'],'network unavailable','network restored')
  self.assertIsNone(self.l.claim('ICARUS','two',1000))
  self.l.retry('a','verified network restored')
  self.assertIsNotNone(self.l.claim('ICARUS','two',1000))
 def test_dependencies_qualified_only(self):
  self.add('a');self.add('b',deps=('a',))
  a=self.l.claim('ICARUS','one',100);self.l.block('a',a['token'],'x','y')
  self.assertIsNone(self.l.claim('ICARUS','two',200))
  self.l.retry('a','condition observed');a=self.l.claim('ICARUS','two',200)
  self.complete('a',a)
  self.assertEqual(self.l.claim('ICARUS','three',300)['id'],'b')
 def test_reject_unknown_dependency_and_nan(self):
  with self.assertRaises(ValueError):self.add('a',deps=('missing',))
  with self.assertRaises(ValueError):self.add('b',priority=(float('nan'),0,0,0,0,0))
 def test_no_release_of_active_handle_on_block(self):
  self.add('a',resource='model-compute');a=self.l.claim('ICARUS','one',100);self.l.handle('a',a['token'],'pid:123')
  with self.assertRaises(ValueError):self.l.block('a',a['token'],'timeout','later')
  self.assertEqual(self.l.snapshot()[0]['state'],'leased')
