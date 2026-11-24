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
if __name__=='__main__':unittest.main()
