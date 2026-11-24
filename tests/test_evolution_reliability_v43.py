import tempfile,unittest,sqlite3,json
from pathlib import Path
import evolution_reliability_v43 as m
import evolution_model_queue_v26 as q
class ReliabilityTests(unittest.TestCase):
 def test_only_transient_quarantine_can_recover(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'db';q.enroll(p,1,3,3600,True);db=q.open_db(p)
   db.execute("update model_jobs set state='quarantined',failure_class='TimeoutError',failures=1 where worker_id=1")
   db.execute("update model_jobs set state='quarantined',failure_class='ValueError',failures=1 where worker_id=2")
   db.execute("update model_jobs set state='quarantined',failure_class='TimeoutError',failures=3 where worker_id=3");db.close()
   results=m.recover(p,7200,lambda i,d:'a'*64,b'k'*32)
   self.assertEqual([r['worker'] for r in results],[1])
   db=q.open_db(p);self.assertEqual(db.execute('select state,next_due,failures from model_jobs where worker_id=1').fetchone(),('ready',7200,1));db.close()
   self.assertEqual(m.recover(p,7200,lambda i,d:'a'*64,b'k'*32),[])
 def test_no_evidence_no_recovery(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'db';q.enroll(p,1,1,3600,True);db=q.open_db(p)
   db.execute("update model_jobs set state='quarantined',failure_class='TimeoutError',failures=1");db.close()
   self.assertEqual(m.recover(p,7200,lambda i,d:None,b'k'*32),[])
 def test_same_hour_never_retries_existing_filename(self):
  self.assertEqual(m.next_hour(3600,3610),7200)
  self.assertEqual(m.next_hour(3600,10810),10800)
 def test_paired_rubric_rejects_missing_and_duplicates(self):
  cases=m.benchmark_cases(701)
  raw=json.dumps([{'id':c['id'],'decision':c['decision'],'evidence':c['evidence']} for c in cases])
  self.assertEqual(m.grade(cases,raw)['correct'],len(cases))
  with self.assertRaises(ValueError):m.grade(cases,'[]')
  rows=json.loads(raw);rows[1]=rows[0]
  with self.assertRaises(ValueError):m.grade(cases,json.dumps(rows))
 def test_ranking_is_paired_and_no_automatic_promotion(self):
  a={'model':'a','case_hash':'x','correct':3,'total':4}
  b={'model':'b','case_hash':'x','correct':2,'total':4}
  self.assertEqual(m.compare([a,b])['leader'],'a')
  self.assertFalse(m.compare([a,b])['production_authority'])
  b['case_hash']='y'
  with self.assertRaises(ValueError):m.compare([a,b])
if __name__=='__main__':unittest.main()
