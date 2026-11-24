"""Durable, bounded real-model evaluation queue: independent ownership and safety."""
import json,sys,tempfile,threading,unittest,os,random,hashlib,types
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import evolution_model_queue_v26 as q


def evidence_module():
    # CI uses the real v2.2 adapter. Local-only reconstruction uses its exact
    # deterministic task generator, without external model or network calls.
    try:
        import evolution_local_model_v22
    except ImportError:
        m=types.ModuleType('evolution_local_model_v22')
        def tasks(seed,count):
            rng=random.Random(seed);rows=[]
            for i in range(count):
                a,b=rng.randint(11,99),rng.randint(11,99)
                op=('+','-','*')[i%3]
                rows.append((f'Return only the integer result of {a} {op} {b}.',str({'+':a+b,'-':a-b,'*':a*b}[op])))
            return rows
        m.tasks=tasks
        m.config=lambda *a:None
        m.request=lambda *a: (_ for _ in ()).throw(AssertionError('No external calls authorized'))
        sys.modules['evolution_local_model_v22']=m
    import evolution_model_evidence_v24 as e
    return e

class WorkerQueueTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.db=Path(self.tmp.name)/'jobs.sqlite3';self.clock=1795482000
  self.env=patch.dict(os.environ,{'MYRIAD_EVIDENCE_HMAC_KEY':'unit-test-private-secret-key-32chars-minimum','MYRIAD_LOCAL_MODEL_TOKEN':'fixture-token'})
  self.env.start();self.addCleanup(self.env.stop)
 def test_registry_does_not_autostart_full_fleet(self):
  r=q.status(self.db,self.clock)
  self.assertEqual(r['enrolled_model_workers'],0)
  self.assertFalse(r['fleet_hourly_model_sla_verified'])
 def test_enrollment_budget_and_address_limits(self):
  for start,count in [(0,1),(195001,1),(195000,2),(1,0),(1,129)]:
   with self.subTest(start=start,count=count):
    with self.assertRaises(ValueError):q.enroll(self.db,start,count,self.clock)
  self.assertEqual(q.status(self.db,self.clock)['enrolled_model_workers'],0)
 def test_exact_identity_enrollment_and_duplicate_rejection(self):
  r=q.enroll(self.db,1,4,self.clock,repeat=True)
  self.assertEqual(r['enrolled'],4)
  self.assertEqual(q.status(self.db,self.clock)['ready'],4)
  with self.assertRaises(ValueError):q.enroll(self.db,4,1,self.clock)
  self.assertEqual(q.status(self.db,self.clock)['enrolled_model_workers'],4)
 def test_two_owners_claim_distinct_due_workers(self):
  q.enroll(self.db,1,4,self.clock)
  results=[]
  def work(owner):
   db=q.open_db(self.db)
   try:
    item=q.claim(db,owner,self.clock)
    results.append(item[0] if item else None)
   finally:db.close()
  t1=threading.Thread(target=work,args=('alpha',));t2=threading.Thread(target=work,args=('beta',))
  t1.start();t2.start();t1.join();t2.join()
  self.assertEqual(len(set(results)),2)
 def test_non_owner_cannot_finish_lease(self):
  q.enroll(self.db,1,1,self.clock)
  db=q.open_db(self.db)
  try:
   item=q.claim(db,'owner1',self.clock)
   with self.assertRaises(ValueError):q.complete(db,'owner2',item[0],item[1],Path(self.tmp.name)/'missing.json',self.clock)
   self.assertEqual(q.status(self.db,self.clock)['completed_occurrences'],0)
  finally:db.close()
 def test_signed_private_evidence_required(self):
  q.enroll(self.db,1,1,self.clock)
  db=q.open_db(self.db)
  try:
   item=q.claim(db,'owner1',self.clock)
   proof=Path(self.tmp.name)/'bogus.json';proof.write_text('{"status":"completed"}')
   with self.assertRaises((ValueError,PermissionError,KeyError,ImportError)):
    q.complete(db,'owner1',item[0],item[1],proof,self.clock)
   self.assertEqual(q.status(self.db,self.clock)['completed_occurrences'],0)
  finally:db.close()
 def test_quarantine_failed_attempt_not_auto_retry(self):
  q.enroll(self.db,1,1,self.clock,repeat=True)
  db=q.open_db(self.db)
  try:
   item=q.claim(db,'owner1',self.clock)
   q.quarantine(db,'owner1',item[0],item[1],self.clock,'ModelEndpointError')
   self.assertEqual(q.status(self.db,self.clock)['quarantined'],1)
   self.assertIsNone(q.claim(db,'owner2',self.clock+500))
  finally:db.close()
 def test_expired_lease_cannot_approve_result(self):
  q.enroll(self.db,1,1,self.clock)
  db=q.open_db(self.db)
  try:
   item=q.claim(db,'owner1',self.clock,lease_seconds=30)
   with self.assertRaises(ValueError):q.complete(db,'owner1',item[0],item[1],Path(self.tmp.name)/'missing.json',self.clock+31)
  finally:db.close()
 def test_processing_requires_explicit_owner_authorization(self):
  q.enroll(self.db,1,1,self.clock)
  with self.assertRaises(PermissionError):q.process(self.db,Path(self.tmp.name)/'raw',model='fixture',port=1234,
    max_jobs=1,count=1,max_tokens=8,budget=8,timeout=2,deadline_seconds=5,clock=self.clock)
  self.assertEqual(q.status(self.db,self.clock)['completed_occurrences'],0)
 def signed_fixture(self,idx,due,*,other_idx=None,incorrect_name=False):
  e=evidence_module()
  effective=other_idx or idx
  seed=(effective*65537+(due//3600))%(2**32)
  rows=[]
  for i,(prompt,answer) in enumerate(e.base.tasks(seed,2),1):
   rows.append({'task':i,'prompt_sha256':e.sha(prompt.encode()),
     'expected_answer':answer,'content':answer,'completion_sha256':e.sha(answer.encode()),
     'response_sha256':e.sha(('server-response:'+str(i)).encode()),
     'reported_completion_tokens':2,'exact_match':True})
  payload={'schema':e.SCHEMA,'status':'completed','error_class':None,
    'model':'deterministic-fixture','seed':seed,'planned_requests':2,
    'max_tokens_per_request':8,'requested_completion_budget':16,
    'deadline_seconds':5,'completed_requests':2,'reported_completion_tokens':4,
    'correct':2,'rows':rows,'endpoint_identity_authenticated':False,
    'trained_parameters':0,'production_authority':False,'auto_promote':False,
    'data_scope':'deterministic toy arithmetic; private raw outputs'}
  payload['hmac_sha256']=e.sign(payload,e.secret())
  hour=q.datetime.fromtimestamp(due,q.timezone.utc).strftime('%Y%m%dT%H')
  basename=f'E{idx:06d}_{hour}.private.json' if not incorrect_name else 'unscoped.json'
  file=Path(self.tmp.name)/basename
  file.write_text(json.dumps(payload))
  return file
 def test_valid_signed_evidence_completes_and_schedules_next_hour(self):
  q.enroll(self.db,1,1,self.clock,repeat=True)
  db=q.open_db(self.db)
  try:
   idx,due=q.claim(db,'worker-A',self.clock)
   path=self.signed_fixture(idx,due)
   result=q.complete(db,'worker-A',idx,due,path,self.clock)
   self.assertEqual((result['score'],result['requests']),(2,2))
   self.assertEqual(q.status(self.db,self.clock)['completed_occurrences'],1)
   self.assertEqual(q.status(self.db,self.clock)['ready'],1)
   self.assertIsNone(q.claim(db,'worker-B',self.clock))
   next_item=q.claim(db,'worker-B',self.clock+3600)
   self.assertEqual(next_item,(idx,due+3600))
   with self.assertRaises(ValueError):q.complete(db,'worker-A',idx,due,path,self.clock+3600)
  finally:db.close()
 def test_cross_worker_signed_evidence_must_not_complete_another_worker(self):
  q.enroll(self.db,1,2,self.clock)
  db=q.open_db(self.db)
  try:
   idx,due=q.claim(db,'worker-A',self.clock)
   self.assertEqual(idx,1)
   path=self.signed_fixture(idx,due,other_idx=2)
   with self.assertRaises(ValueError):q.complete(db,'worker-A',idx,due,path,self.clock)
   self.assertEqual(q.status(self.db,self.clock)['completed_occurrences'],0)
  finally:db.close()
 def test_unscoped_signed_evidence_file_must_not_complete_occurrence(self):
  q.enroll(self.db,1,1,self.clock)
  db=q.open_db(self.db)
  try:
   idx,due=q.claim(db,'worker-A',self.clock)
   path=self.signed_fixture(idx,due,incorrect_name=True)
   with self.assertRaises(ValueError):q.complete(db,'worker-A',idx,due,path,self.clock)
   self.assertEqual(q.status(self.db,self.clock)['completed_occurrences'],0)
  finally:db.close()
 def test_expired_owner_cannot_complete_reclaimed_lease(self):
  q.enroll(self.db,1,1,self.clock)
  db=q.open_db(self.db)
  try:
   idx,due=q.claim(db,'old',self.clock,lease_seconds=30)
   self.assertEqual(q.claim(db,'new',self.clock+31), (idx,due))
   path=self.signed_fixture(idx,due)
   with self.assertRaises(ValueError):q.complete(db,'old',idx,due,path,self.clock+31)
   self.assertEqual(q.status(self.db,self.clock+31)['completed_occurrences'],0)
  finally:db.close()
 def test_opt_in_process_records_two_distinct_signed_occurrences(self):
  e=evidence_module()
  q.enroll(self.db,1,2,self.clock,repeat=True)
  output_dir=Path(self.tmp.name)/'private-model-receipts'
  def simulate_local_evaluation(port,model,seed,count,max_tokens,budget,timeout,deadline_seconds,out,authorize=False):
   target=Path(out)
   idx=int(target.name[1:7]);due=self.clock
   expected_seed=(idx*65537+(due//3600))%(2**32)
   self.assertEqual(seed,expected_seed)
   source=self.signed_fixture(idx,due)
   payload=json.loads(source.read_text())
   target.write_text(json.dumps(payload))
   return payload
  with patch.object(e,'run',side_effect=simulate_local_evaluation) as run:
   r=q.process(self.db,output_dir,model='deterministic-fixture',port=1234,max_jobs=2,
     count=2,max_tokens=8,budget=16,timeout=2,deadline_seconds=5,
     clock=self.clock,authorize=True)
  self.assertEqual(run.call_count,2)
  self.assertEqual(r['model_evaluation_occurrences'],2)
  self.assertEqual(r['quarantined_or_failed'],[])
  self.assertEqual({x['workflow'] for x in r['completed']},{'E000001','E000002'})
  self.assertEqual(q.status(self.db,self.clock)['completed_occurrences'],2)
  self.assertEqual(q.status(self.db,self.clock)['ready'],2)
  self.assertEqual(q.status(self.db,self.clock)['overdue_ready'],0)
  self.assertEqual(len(list(output_dir.glob('*.private.json'))),2)
 def test_model_failure_quarantines_without_auto_retry(self):
  e=evidence_module()
  q.enroll(self.db,1,1,self.clock,repeat=True)
  with patch.object(e,'run',side_effect=ConnectionError('not stored in failure ledger')):
   r=q.process(self.db,Path(self.tmp.name)/'private',model='deterministic-fixture',port=1234,
     max_jobs=1,count=2,max_tokens=8,budget=16,timeout=2,deadline_seconds=5,
     clock=self.clock,authorize=True)
  self.assertEqual(r['model_evaluation_occurrences'],0)
  self.assertEqual(r['quarantined_or_failed'][0]['error_class'],'ConnectionError')
  self.assertEqual(q.status(self.db,self.clock)['quarantined'],1)
  self.assertEqual(q.status(self.db,self.clock)['completed_occurrences'],0)
 def test_bad_run_budget_fails_before_any_claim(self):
  q.enroll(self.db,1,1,self.clock)
  with self.assertRaises(ValueError):q.process(self.db,Path(self.tmp.name)/'raw',model='fixture',port=1234,
    max_jobs=5,count=1,max_tokens=8,budget=8,timeout=2,deadline_seconds=5,clock=self.clock,authorize=True)
  self.assertEqual(q.status(self.db,self.clock)['ready'],1)

if __name__=='__main__':unittest.main()
