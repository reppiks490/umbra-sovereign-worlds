import unittest,tempfile,json
from pathlib import Path
import evolution_fleet_v46 as f
import evolution_collective_v54 as m
class Tests(unittest.TestCase):
 def test_feedback_replays_prior_receipt_and_rejects_tampering(self):
  with tempfile.TemporaryDirectory() as t:
   db=f.connect(Path(t)/'f');f.enroll(db,32);ids=f.claim(db,'owner',8,100,20);cases=f.cases(db,ids,20)
   rows=f.grade(cases,json.dumps([{'id':c['id'],'decision':c['expected'],'evidence':c['evidence_id']} for c in cases]))
   f.settle(db,'owner',20,101,rows,'a'*64,'b'*64,b'k'*32)
   a=m.advice(db,17,21,b'k'*32)
   self.assertEqual(a['worker'],1);self.assertIn('prior_action',a);self.assertIn('prior_evidence',a)
   self.assertIsNone(m.advice(db,17,20,b'k'*32))
   db.execute("update receipts set record='{}' where worker=1")
   with self.assertRaises(ValueError):m.advice(db,17,21,b'k'*32)
   db.close()
 def test_ablation_is_deterministic(self):
  self.assertEqual(m.use_peer(17,21),m.use_peer(17,21))
  self.assertEqual(sum(m.use_peer(i,21) for i in range(1,101)),50)
if __name__=='__main__':unittest.main()
