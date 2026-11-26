import tempfile,pathlib,unittest,hashlib
from omega_ledger import Ledger
from queue_observer import observe
class QueueObserverTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.p=pathlib.Path(self.tmp.name)/'q.sqlite';self.l=Ledger(self.p)
 def tearDown(self):self.tmp.cleanup()
 def add(self,k,lane='ICARUS',resource='',deps=()):
  self.l.add(k,lane,'a'*40,k,(.5,.5,.5,.5,.5,0),resource,list(deps))
 def test_missing_db_never_created(self):
  p=self.p.parent/'missing.sqlite'
  with self.assertRaises(ValueError):observe(p,'ICARUS')
  self.assertFalse(p.exists())
 def test_only_requested_lane_and_redacted(self):
  self.add('a');self.add('b','UMBRA');claim=self.l.claim('ICARUS','owner',100)
  self.l.handle('a',claim['token'],'private-handle')
  r=observe(self.p,'ICARUS');self.assertEqual([x['id'] for x in r['tasks']],['a'])
  self.assertNotIn(claim['token'],str(r));self.assertNotIn('private-handle',str(r));self.assertNotIn('token',r['tasks'][0])
 def test_dependencies_and_resources_cross_lane(self):
  self.add('a','UMBRA','compute');self.add('b',resource='compute');self.add('c',deps=('a',));self.add('d')
  self.l.claim('UMBRA','owner',100)
  r=observe(self.p,'ICARUS');x={i['id']:i for i in r['tasks']}
  self.assertEqual(x['b']['eligibility'],'resource-busy')
  self.assertEqual(x['c']['eligibility'],'dependency-pending')
  self.assertEqual(x['d']['eligibility'],'candidate')
  self.assertEqual(r['candidate_count'],1)
 def test_read_only_and_unknown_lane(self):
  self.add('a');before=hashlib.sha256(self.p.read_bytes()).hexdigest()
  observe(self.p,'ICARUS')
  self.assertEqual(before,hashlib.sha256(self.p.read_bytes()).hexdigest())
  with self.assertRaises(ValueError):observe(self.p,'OTHER')
 def test_no_false_resource_release_from_report(self):
  self.add('a','UMBRA','compute');self.add('b',resource='compute')
  a=self.l.claim('UMBRA','w',100)
  e=self.p.parent/'evidence';e.mkdir();out=e/'r.txt';out.write_text('fixture')
  import json
  rec=e/'r.json';rec.write_text(json.dumps({'task':'a','base':'a'*40,'token':a['token'],'outcome':'passed','handle':None,'artifacts':[{'path':'r.txt','sha256':hashlib.sha256(out.read_bytes()).hexdigest()}]}))
  self.l.finish('a',a['token'],str(rec),'fixture')
  self.assertEqual(observe(self.p,'ICARUS')['tasks'][0]['eligibility'],'resource-busy')
 def test_nonready_is_not_candidate(self):
  self.add('a');a=self.l.claim('ICARUS','w',100);self.l.block('a',a['token'],'blocked','condition')
  r=observe(self.p,'ICARUS');self.assertEqual(r['candidate_count'],0);self.assertEqual(r['tasks'][0]['eligibility'],'blocked')
