import unittest,tempfile,json
from pathlib import Path
import evolution_fleet_v46 as m
class Tests(unittest.TestCase):
 def test_all_ids_and_idempotence(self):
  with tempfile.TemporaryDirectory() as t:
   db=m.connect(Path(t)/'fleet.db')
   self.assertEqual(m.enroll(db,195000),195000)
   self.assertEqual(m.enroll(db,195000),0)
   self.assertEqual(m.status(db)['enrolled'],195000);db.close()
 def test_independent_occurrence_and_replay(self):
  with tempfile.TemporaryDirectory() as t:
   db=m.connect(Path(t)/'fleet.db');m.enroll(db,16)
   ids=m.claim(db,'a',8,100,20);self.assertEqual(ids,list(range(1,9)))
   self.assertEqual(m.claim(db,'b',8,100,20),list(range(9,17)))
   cases=m.cases(db,ids,20)
   raw=json.dumps([{'id':c['id'],'decision':c['expected'],'evidence':c['evidence_id']} for c in cases])
   rows=m.grade(cases,raw)
   m.settle(db,'a',20,101,rows,'a'*64,'b'*64,b'k'*32)
   self.assertEqual(m.status(db)['distinct_completed'],8)
   with self.assertRaises(ValueError):m.settle(db,'a',20,101,rows,'a'*64,'b'*64,b'k'*32)
   db.close()
 def test_missing_duplicate_and_wrong_label(self):
  with tempfile.TemporaryDirectory() as t:
   db=m.connect(Path(t)/'db');m.enroll(db,8);c=m.cases(db,[1,2],0)
   with self.assertRaises(ValueError):m.grade(c,'[]')
   with self.assertRaises(ValueError):m.grade(c,'[{"id":1,"decision":"A","evidence":"E1"},{"id":1,"decision":"A","evidence":"E1"}]')
   db.close()
 def test_peer_only_from_preceding_slots(self):
  with tempfile.TemporaryDirectory() as t:
   db=m.connect(Path(t)/'db');m.enroll(db,32)
   ids=m.claim(db,'a',8,100,20);cases=m.cases(db,ids,20)
   raw=json.dumps([{'id':c['id'],'decision':c['expected'],'evidence':c['evidence_id']} for c in cases])
   m.settle(db,'a',20,101,m.grade(cases,raw),'a'*64,'b'*64,b'k'*32)
   self.assertIsNone(m.cases(db,[17],20)[0]['peer'])
   self.assertEqual(m.cases(db,[17],21)[0]['peer']['worker'],1)
   db.close()
if __name__=='__main__':unittest.main()
