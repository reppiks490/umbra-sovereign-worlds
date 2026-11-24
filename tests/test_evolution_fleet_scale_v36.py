import unittest,tempfile,sqlite3,time
from pathlib import Path
import evolution_model_queue_v26 as q
import evolution_fleet_scale_v36 as s
class ScaleTests(unittest.TestCase):
 def test_expansion_preserves_existing_and_is_idempotent(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'queue.db';q.enroll(p,1,8,3600,True)
   self.assertEqual(s.expand(p,128,3600),120)
   self.assertEqual(s.expand(p,128,3600),0)
   db=q.open_db(p)
   self.assertEqual(db.execute('select count(*) from model_jobs').fetchone()[0],128)
   self.assertEqual(db.execute('select next_due from model_jobs where worker_id=1').fetchone()[0],3600)
   db.close()
 def test_expansion_rejects_oversize(self):
  with tempfile.TemporaryDirectory() as t:
   with self.assertRaises(ValueError):s.expand(Path(t)/'q.db',4097,3600)
 def test_budget_is_bounded_by_deadline_and_resources(self):
  self.assertEqual(s.batch_limit(128,0.25,0,1000),0)
  self.assertEqual(s.batch_limit(128,0.25,60,3000),128)
  self.assertEqual(s.batch_limit(128,2,60,3000),30)
  self.assertEqual(s.batch_limit(128,2,60,1000),0)
 def test_signed_receipts_preserved_on_expansion(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'q.db';q.enroll(p,1,1,3600,True);db=q.open_db(p)
   db.execute("update model_jobs set state='quarantined',last_receipt='old',failures=1 where worker_id=1");db.close()
   s.expand(p,64,7200)
   db=q.open_db(p);self.assertEqual(db.execute('select state,last_receipt,failures from model_jobs where worker_id=1').fetchone(),('quarantined','old',1));db.close()
if __name__=='__main__':unittest.main()
