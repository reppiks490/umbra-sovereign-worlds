import pathlib,sys,tempfile,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from generated_challenges import SKILLS, LIMIT, question, grade, Ledger, prompt, audit
from research_portfolio import LANES,command_for,normalize

class GeneratedChallengesTest(unittest.TestCase):
 def test_bounded_deterministic_distinct_questions(self):
  seen=set()
  for skill in SKILLS:
   for tier in range(4):
    for i in (0,1,2,999,1000,999999,LIMIT-1):
     q=question(skill,tier,i)
     self.assertEqual(q,question(skill,tier,i))
     self.assertNotIn(q['id'],seen);seen.add(q['id'])
     self.assertFalse(q['training_eligible'])
     self.assertEqual(q['source_kind'],'authored_generated_evaluation')
     self.assertNotIn('expected',prompt(q))
  with self.assertRaises(ValueError):question(SKILLS[0],0,LIMIT)
  with self.assertRaises(ValueError):question(SKILLS[0],True,0)
 def test_independent_exact_grading(self):
  q=question('arithmetic',3,0)
  self.assertEqual(q['expected'],'367181')
  self.assertEqual(grade(q,'ANSWER: 367181','stop'),'correct')
  self.assertEqual(grade(q,'ANSWER: 367181.0','stop'),'correct')
  self.assertEqual(grade(q,'ANSWER: 365181','stop'),'incorrect')
  self.assertEqual(grade(q,'ANSWER: 367181','length'),'truncated')
  self.assertEqual(grade(q,'ABSTAIN','stop'),'abstain')
  self.assertEqual(grade(q,'ANSWER: 367181\nOther answer','stop'),'format')
 def test_restarts_and_separate_checkpoints(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'test.sqlite3'
   with Ledger(p) as b:
    r=b.reserve('model-a','a'*64,'arithmetic',0)
    b.finish(r['attempt'], 'ANSWER: '+r['question']['expected'],'stop',3,1.0)
    pending=b.reserve('model-a','a'*64,'arithmetic',0)
    with self.assertRaises(ValueError):b.finish(r['attempt'],'ABSTAIN','stop',1,1.0)
   with Ledger(p) as b:
    nextq=b.reserve('model-a','a'*64,'arithmetic',0)
    self.assertEqual(nextq['question']['ordinal'],2)
    other=b.reserve('model-a','b'*64,'arithmetic',0)
    self.assertEqual(other['question']['ordinal'],0)
    result=b.audit()
    self.assertEqual(result['completed_calls'],1)
    self.assertEqual(result['reserved_unknown'],3)
    self.assertEqual(result['correct'],1)
    self.assertEqual(result['errors'],[])
 def test_promotion_requires_eight_distinct_completed_successes(self):
  with tempfile.TemporaryDirectory() as d:
   with Ledger(pathlib.Path(d)/'test.sqlite3') as b:
    for i in range(8):
     r=b.reserve('m','c'*64,'arithmetic',0)
     if i<7:self.assertEqual(b.tier('m','c'*64,'arithmetic'),0)
     b.finish(r['attempt'],'ANSWER: '+r['question']['expected'],'stop',2,1)
    self.assertEqual(b.tier('m','c'*64,'arithmetic'),1)
    self.assertEqual(b.tier('m','d'*64,'arithmetic'),0)
 def test_tampered_scores_fail_closed(self):
  with tempfile.TemporaryDirectory() as d:
   with Ledger(pathlib.Path(d)/'test.sqlite3') as b:
    r=b.reserve('m','e'*64,'arithmetic',0)
    b.finish(r['attempt'],'ABSTAIN','stop',1,1)
    with b.db:b.db.execute("update attempts set outcome='correct'")
    self.assertEqual(b.audit()['correct'],0)
    self.assertTrue(b.audit()['errors'])
 def test_portfolio_integration(self):
  self.assertIn('generated_challenges',LANES)
  self.assertIn('generated_challenges.py',pathlib.Path(command_for('generated_challenges',pathlib.Path('r'),pathlib.Path('p'),0)[1]).name)
  self.assertEqual(normalize('generated_challenges',{'status':'completed','model_calls':2,'completed_calls':2}),'completed')
  self.assertEqual(normalize('generated_challenges',{'status':'completed','model_calls':2,'completed_calls':1}),'partial')


 def test_tampered_correct_scores_cannot_promote(self):
  with tempfile.TemporaryDirectory() as d:
   with Ledger(pathlib.Path(d)/'test.sqlite3') as b:
    for _ in range(8):
     r=b.reserve('m','c'*64,'arithmetic',0)
     b.finish(r['attempt'],'ABSTAIN','stop',1,1.0)
    with b.db:b.db.execute("update attempts set outcome='correct'")
    self.assertEqual(b.tier('m','c'*64,'arithmetic'),0)
 def test_readonly_ledger_audit_never_creates_or_writes(self):
  import sqlite3
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'test.sqlite3'
   with self.assertRaises(sqlite3.OperationalError):Ledger(p,readonly=True)
   self.assertFalse(p.exists())
   with Ledger(p) as b:
    r=b.reserve('m','c'*64,'arithmetic',0)
    b.finish(r['attempt'],'ANSWER: '+r['question']['expected'],'stop',2,1)
   before=p.read_bytes()
   with Ledger(p,readonly=True) as b:
    self.assertEqual(b.audit()['correct'],1)
    with self.assertRaises(sqlite3.OperationalError):b.db.execute("delete from attempts")
   self.assertEqual(p.read_bytes(),before)

if __name__=='__main__':unittest.main()
