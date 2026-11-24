import json,tempfile,unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import evolution_research_v37 as r
class ResearchTests(unittest.TestCase):
 def test_all_specialties_and_answer_keys(self):
  cases=[r.task(i,0) for i in range(1,129)]
  self.assertEqual(len({c['specialty'] for c in cases}),16)
  self.assertEqual(len({c['worker'] for c in cases}),128)
  self.assertEqual(len({c['task_sha256'] for c in cases}),128)
  self.assertTrue(all(c['expected'] in 'ABC' and c['evidence_id'] in ('E1','E2','E3') for c in cases))
 def test_score_does_not_execute_or_reward_prose(self):
  c=r.task(1,0)
  ans={'decision':c['expected'],'evidence':c['evidence_id'],'next_test':'Repeat with an independent holdout.'}
  self.assertTrue(r.score(c,json.dumps(ans))['passed'])
  ans['decision']=next(x for x in 'ABC' if x!=c['expected'])
  self.assertFalse(r.score(c,json.dumps(ans))['passed'])
  self.assertFalse(r.score(c,'{"decision":"A","decision":"B","evidence":"E1","next_test":"x"}')['valid'])
  self.assertFalse(r.score(c,'{"decision":"A","evidence":"E1","next_test":"x","command":"run"}')['valid'])
 def test_deterministic_rotation(self):
  self.assertEqual(r.task(17,11),r.task(17,11))
  self.assertNotEqual(r.task(17,11)['task_sha256'],r.task(17,12)['task_sha256'])
  self.assertEqual(r.task(17,11)['specialty'],r.task(17,12)['specialty'])
 def test_durable_identity_and_receipt_tamper(self):
  with tempfile.TemporaryDirectory() as t:
   db=r.connect(Path(t)/'research.db')
   self.assertEqual(r.enroll(db,128,10),128)
   self.assertEqual(r.enroll(db,128,10),0)
   row=r.claim(db,'one',10,100)
   self.assertEqual(row,(1,10))
   self.assertEqual(r.claim(db,'two',10,100),(2,10))
   c=r.task(*row)
   receipt=r.make_receipt(c,'model','a'*64,json.dumps({'decision':c['expected'],'evidence':c['evidence_id'],'next_test':'Replay independently.'}),'b'*64,10,None,b'k'*32)
   r.settle(db,'one',row,receipt,101,b'k'*32)
   self.assertEqual(r.status(db)['completed_occurrences'],1)
   receipt['raw']='changed'
   with self.assertRaises(ValueError):r.verify(receipt,b'k'*32)
   db.close()
 def test_invalid_bounds(self):
  with tempfile.TemporaryDirectory() as t:
   db=r.connect(Path(t)/'db')
   for n in (0,4097):
    with self.assertRaises(ValueError):r.enroll(db,n,0)
   db.close()
if __name__=='__main__':unittest.main()
