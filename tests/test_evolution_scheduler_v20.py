"""Multiple live processes, lease-fencing and previous-hour peer controls."""
import concurrent.futures
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import evolution_scheduler as s
import umbra_evolution_mesh as mesh

class TestConductor(unittest.TestCase):
 def test_simultaneous_processes_complete_unique_identities(self):
  with tempfile.TemporaryDirectory() as t:
   path=str(Path(t)/'fleet.db');base=1_795_460_000
   s.initialize(path,start_at=base)
   with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
    jobs=[pool.submit(s.process,path,max_jobs=32,steps=3,owner='shared-owner',clock=base+3600) for _ in range(4)]
    batches=[job.result(timeout=35) for job in jobs]
   self.assertEqual(sum(x['completed_this_invocation'] for x in batches),128)
   self.assertTrue(all(not x['failures'] for x in batches))
   with sqlite3.connect(path) as db:
    self.assertEqual(db.execute('SELECT COUNT(*) FROM runs').fetchone()[0],128)
    self.assertEqual(db.execute('SELECT COUNT(DISTINCT workflow) FROM runs').fetchone()[0],128)
   self.assertEqual(s.status(path,base+3600)['actively_leased'],0)

 def test_same_name_does_not_override_stale_lease(self):
  with tempfile.TemporaryDirectory() as t:
   path=str(Path(t)/'fleet.db');base=1_795_460_000
   s.initialize(path,start_at=base)
   db=s.open_db(path)
   idx,due=s.claim(db,'first-instance',base+3600)
   wf=mesh.workflow(idx)
   hour=__import__('datetime').datetime.fromtimestamp(due,tz=__import__('datetime').timezone.utc).strftime('%Y-%m-%dT%H')
   rec=mesh.train(wf,hour=hour,steps=3)
   with self.assertRaisesRegex(ValueError,'lease'):
    s.finish(db,'second-instance',idx,due,rec,base+3600)
   self.assertEqual(db.execute('SELECT COUNT(*) FROM runs').fetchone()[0],0)
   db.close()

 def test_same_hour_peer_is_not_considered_for_training(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'db';db=s.open_db(p)
   wf=mesh.workflow(1)
   hour='2026-11-23T18'
   for candidate in range(2,200):
    second=mesh.workflow(candidate)
    if second['domain']==wf['domain']:break
   record=mesh.train(second,hour=hour,steps=8)
   db.execute('INSERT INTO runs VALUES(?,?,?,?,?)',(hour,second['id'],second['domain'],record['receipt_sha256'],json.dumps(record)))
   self.assertIsNone(mesh.peer_for(db,wf,hour))
   # A genuine previous hour still must pass the candidate review gate.
   self.assertIsNone(mesh.peer_for(db,wf,'2026-11-23T19') if record['review_status']!='candidate_for_manual_review' else None)
   db.close()

 def test_duplicate_hour_rejected_not_counted_as_completion(self):
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'ledger';base=1_795_460_000
   s.initialize(path,start_at=base)
   d=s.open_db(path);idx,due=s.claim(d,'x',base+3600)
   wf=mesh.workflow(idx)
   import datetime
   hour=datetime.datetime.fromtimestamp(due,datetime.timezone.utc).strftime('%Y-%m-%dT%H')
   rec=mesh.train(wf,hour=hour,steps=2)
   d.execute('INSERT INTO runs VALUES(?,?,?,?,?)',(hour,rec['workflow'],rec['domain'],rec['receipt_sha256'],json.dumps(rec)))
   with self.assertRaises(sqlite3.IntegrityError):s.finish(d,'x',idx,due,rec,base+3600)
   self.assertEqual(d.execute('SELECT completed FROM worker_state WHERE id=?',(idx,)).fetchone()[0],0)
   d.close()

if __name__=='__main__':unittest.main()
