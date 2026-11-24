import unittest,tempfile,json
from pathlib import Path
import evolution_fleet_v46 as f
import evolution_fleet_integrity_v55 as m
class Tests(unittest.TestCase):
 def test_resealed_case_cannot_change_ground_truth(self):
  with tempfile.TemporaryDirectory() as t:
   db=f.connect(Path(t)/'db');f.enroll(db,16);ids=f.claim(db,'a',4,100,20)
   c=f.cases(db,ids,20);c[0]['expected']=next(x for x in 'ABC' if x!=c[0]['expected'])
   raw=json.dumps([{'id':x['id'],'decision':x['expected'],'evidence':x['evidence_id']} for x in c])
   with self.assertRaises(ValueError):m.check_cases(db,f.grade(c,raw),20,b'k'*32)
   db.close()
 def test_compact_decode_strict(self):
  c=[{'id':1},{'id':2}]
  self.assertEqual(json.loads(m.decode(c,'["A1","B2"]')),[{'id':1,'decision':'A','evidence':'E1'},{'id':2,'decision':'B','evidence':'E2'}])
  for x in ('["A1"]','["A1","A4"]','["A1",true]','{"A1":"B2"}'):
   with self.assertRaises(ValueError):m.decode(c,x)
 def test_audit_replays_and_detects_tamper(self):
  with tempfile.TemporaryDirectory() as t:
   db=f.connect(Path(t)/'db');f.enroll(db,16);ids=f.claim(db,'a',4,100,20);c=f.cases(db,ids,20)
   rows=f.grade(c,json.dumps([{'id':x['id'],'decision':x['expected'],'evidence':x['evidence_id']} for x in c]))
   m.check_cases(db,rows,20,b'k'*32)
   f.settle(db,'a',20,101,rows,'a'*64,'b'*64,b'k'*32)
   self.assertEqual(m.audit(db,b'k'*32)['verified_items'],4)
   db.execute("update receipts set correct=0 where worker=1")
   with self.assertRaises(ValueError):m.audit(db,b'k'*32)
   db.close()
class LedgerClosureTests(unittest.TestCase):
 def fixture(self,db):
  f.enroll(db,16);ids=f.claim(db,'a',4,100,20);c=f.cases(db,ids,20)
  rows=f.grade(c,json.dumps([{'id':x['id'],'decision':x['expected'],'evidence':x['evidence_id']} for x in c]))
  f.settle(db,'a',20,101,rows,f.DIGEST,'b'*64,b'k'*32)
 def test_missing_or_reset_worker_is_not_valid_completion(self):
  for sql in ("DELETE FROM workers WHERE id=1","UPDATE workers SET attempts=0,wins=0,last_hmac=NULL WHERE id=1","UPDATE workers SET wins=1 WHERE id=10","UPDATE workers SET last_hmac='orphan' WHERE id=10"):
   with self.subTest(sql=sql),tempfile.TemporaryDirectory() as t:
    db=f.connect(Path(t)/'db')
    try:
     self.fixture(db);db.execute(sql)
     with self.assertRaises(ValueError):m.audit(db,b'k'*32)
    finally:db.close()
 def test_audited_aggregate_reconciles_all_counters(self):
  import publish_telemetry_v48 as p
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'db';db=f.connect(path)
   try:
    self.fixture(db)
    self.assertEqual(p.verified_fleet(path,b'k'*32),(16,4,4,0,1))
    db.execute("UPDATE receipts SET correct=0 WHERE worker=1")
    with self.assertRaises(ValueError):p.verified_fleet(path,b'k'*32)
   finally:db.close()
 def test_registry_overlap_rejected(self):
  import publish_telemetry_v48 as p
  self.assertEqual(p.registry_count(({'a':len},{'b':sum})),2)
  with self.assertRaises(ValueError):p.registry_count(({'a':len},{'a':sum}))
if __name__=='__main__':unittest.main()
