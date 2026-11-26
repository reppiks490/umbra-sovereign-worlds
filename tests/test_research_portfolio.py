import sys,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from ifeval_local import check, score
from research_portfolio import choose_lane, record_outcome, LANES
class InstructionTest(unittest.TestCase):
 def test_constraints(self):
  self.assertTrue(check('punctuation:no_comma',{},'A plain answer.'))
  self.assertFalse(check('punctuation:no_comma',{},'A, plain answer.'))
  self.assertTrue(check('change_case:english_lowercase',{},'abc 123'))
  self.assertFalse(check('change_case:english_lowercase',{},'ABC'))
  self.assertFalse(check('change_case:english_capital',{},'123'))
  self.assertTrue(check('startend:quotation',{},'"hello"'))
  self.assertFalse(check('startend:quotation',{},'"hello" trailing'))
  self.assertTrue(check('detectable_format:json_format',{},'{"a":2}'))
  self.assertFalse(check('detectable_format:json_format',{},'{"a":NaN}'))
  self.assertTrue(check('detectable_format:title',{},'<<Title>>\nBody'))
  self.assertFalse(check('detectable_format:title',{},'<<>>'))
 def test_unknown_and_empty_rejected(self):
  self.assertIsNone(check('unknown',{},'hello'))
  self.assertFalse(check('punctuation:no_comma',{},' '))
  self.assertIsNone(check('punctuation:no_comma',{'surprise':1},'hello'))
 def test_complete_constraint_coverage(self):
  self.assertEqual(score({'instruction_id_list':['punctuation:no_comma','change_case:english_lowercase'],'kwargs':[{},{}]},'abc')['passed'],True)
  self.assertEqual(score({'instruction_id_list':['punctuation:no_comma','unknown'],'kwargs':[{},{}]},'abc')['status'],'unsupported')
  with self.assertRaises(ValueError):score({'instruction_id_list':['punctuation:no_comma'],'kwargs':[]},'abc')
class PortfolioTest(unittest.TestCase):
 def test_fairness(self):
  names=list(LANES)
  s={}
  for i in range(len(names)):
   p=choose_lane(s,10000+i,10**10,10**10,False)
   self.assertIsNotNone(p)
   s=record_outcome(s,p,10000+i,'completed')
  self.assertEqual(set(s),set(names))
 def test_busy_storage_and_cooldown(self):
  self.assertIn(choose_lane({},10000,10**10,10**10,True),{'receipt_replay','corrective_curriculum'})
  self.assertIsNone(choose_lane({},10000,10**10,1,False))
  self.assertIsNone(choose_lane({},10000,1,10**10,False))
  s={k:{'attempts':1,'last_attempt':10000,'next_due':20000,'completed':1} for k in LANES}
  self.assertIsNone(choose_lane(s,10001,10**10,10**10,False))
 def test_compute_contention_allows_only_due_evidence_lanes(self):
  state={}
  for i in range(2):
   lane=choose_lane(state,10000+i,10**10,10**10,True)
   self.assertIn(lane,{'receipt_replay','corrective_curriculum'})
   state=record_outcome(state,lane,10000+i,'completed')
  self.assertEqual(set(state),{'receipt_replay','corrective_curriculum'})
  self.assertIsNone(choose_lane(state,10002,10**10,10**10,True))
  self.assertIn(choose_lane(state,10002,10**10,10**10,False),set(LANES)-set(state))
 def test_evidence_work_retains_storage_memory_reserves(self):
  self.assertIsNone(choose_lane({},10000,1499999999,10**10,True))
  self.assertIsNone(choose_lane({},10000,10**10,5999999999,True))
 def test_failed_and_deferred_not_completed(self):
  k=next(iter(LANES))
  s=record_outcome({},k,10000,'deferred_busy')
  self.assertEqual(s[k]['completed'],0)
  s=record_outcome(s,k,20000,'failed')
  self.assertEqual(s[k]['completed'],0)
  self.assertGreater(s[k]['next_due'],20000)
if __name__=='__main__':unittest.main()
