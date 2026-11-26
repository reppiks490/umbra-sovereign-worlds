import tempfile,pathlib,unittest,json,hashlib
from omega_ledger import Ledger
class EvidenceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name);self.l=Ledger(self.root/'db.sqlite')
  self.l.add('a','ICARUS','a'*40,'test',(.5,)*5+(0,),'compute',[])
  self.l.add('b','MYRIAD','b'*40,'child',(.5,)*5+(0,),'compute',['a'])
  self.claim=self.l.claim('ICARUS','worker',100);self.token=self.claim['token']
  self.e=self.root/'evidence';self.e.mkdir();self.artifact=self.e/'result.txt';self.artifact.write_text('real fixture result')
 def tearDown(self):self.tmp.cleanup()
 def receipt(self,**kw):
  r={'task':'a','token':self.token,'base':'a'*40,'outcome':'passed','handle':None,'artifacts':[{'path':'result.txt','sha256':hashlib.sha256(self.artifact.read_bytes()).hexdigest()}],**kw}
  p=self.e/'receipt.json';p.write_text(json.dumps(r));return p
 def test_bare_hash_does_not_qualify(self):
  with self.assertRaises(ValueError):self.l.finish('a',self.token,'b'*64,'claimed')
  self.assertEqual(self.l.snapshot()[0]['state'],'leased')
 def test_worker_report_and_independent_acceptance(self):
  p=self.receipt();self.l.finish('a',self.token,str(p),'reported')
  self.assertEqual(self.l.snapshot()[0]['state'],'reported')
  self.assertIsNone(self.l.claim('MYRIAD','another',200))
  with self.assertRaises(ValueError):self.l.accept('a','worker','review')
  self.l.accept('a','reviewer','reviewed exact source and output')
  self.assertEqual(self.l.snapshot()[0]['state'],'qualified')
  self.assertEqual(self.l.claim('MYRIAD','another',200)['id'],'b')
 def test_tamper_rejected_on_report_and_acceptance(self):
  p=self.receipt();self.artifact.write_text('changed')
  with self.assertRaises(ValueError):self.l.finish('a',self.token,str(p),'reported')
  p=self.receipt();self.l.finish('a',self.token,str(p),'reported')
  self.artifact.write_text('changed again')
  with self.assertRaises(ValueError):self.l.accept('a','reviewer','review')
  self.assertEqual(self.l.snapshot()[0]['state'],'reported')
 def test_active_handle_requires_matching_receipt_and_review(self):
  self.l.handle('a',self.token,'pid:123')
  with self.assertRaises(ValueError):self.l.finish('a',self.token,str(self.receipt()),'reported')
  self.l.finish('a',self.token,str(self.receipt(handle='pid:123')),'reported')
  self.assertEqual(self.l.snapshot()[0]['handle'],'pid:123')
  with self.assertRaises(ValueError):self.l.accept('a','reviewer','review')
  self.l.accept('a','reviewer','reviewed','observed process exit 0')
  self.assertIsNone(self.l.snapshot()[0]['handle'])
 def test_path_escape_and_wrong_base(self):
  p=self.receipt(base='b'*40)
  with self.assertRaises(ValueError):self.l.finish('a',self.token,str(p),'reported')
  p=self.receipt(artifacts=[{'path':'../db.sqlite','sha256':'b'*64}])
  with self.assertRaises(ValueError):self.l.finish('a',self.token,str(p),'reported')
