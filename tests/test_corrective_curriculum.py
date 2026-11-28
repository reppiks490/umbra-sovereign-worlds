import pathlib,sys,tempfile,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from corrective_curriculum import read_failures,select_lessons,plan
from generated_challenges import Ledger
from human_corpus import validate

def record(q,a):return validate({'question':q,'answer':a})
def corpus():
 return {'train':[record('Five groups with three members?','<<5*3=15>>\n#### 15'),record('Total of two and seven?','<<2+7=9>>\n#### 9'),record('An incorrect worked product','<<2*3=7>>\n#### 7'),record('A product then add four','<<3*2=6>> and <<6+4=10>>\n#### 10')],
 'validation':[record('Other example','<<4*7=28>>\n#### 28')],
 'test':[record('Held-out example','<<5*7=35>>\n#### 35')]}

class CorrectionTests(unittest.TestCase):
 def test_only_source_train_and_verified_operations(self):
  c=corpus();r=select_lessons(c,'arithmetic',1,4)
  self.assertEqual(len(r),1)
  self.assertEqual(r[0]['record_sha256'],c['train'][3]['record_sha256'])
  self.assertNotIn('answer',r[0]);self.assertNotIn('question',r[0])
  self.assertEqual(r[0]['source_kind'],'verified_original_training')
 def test_split_overlap_fails_closed(self):
  c=corpus();c['test'].append(c['train'][0])
  with self.assertRaises(ValueError):select_lessons(c,'arithmetic',1,4)
 def test_individualized_failure_replay_and_format_separation(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'ledger.sqlite3'
   with Ledger(p) as b:
    r=b.reserve('m','a'*64,'arithmetic',1);b.finish(r['attempt'],'ANSWER: -10000000','stop',5,1.)
    r=b.reserve('m','b'*64,'arithmetic',1);b.finish(r['attempt'],'ABSTAIN','stop',1,1.)
    r=b.reserve('m','a'*64,'arithmetic',1)
   rows=read_failures(p)
   self.assertEqual(len(rows),2)
   self.assertEqual({x['digest'] for x in rows},{'a'*64,'b'*64})
   a=plan(corpus(),rows)
   self.assertEqual(len(a['clusters']),2)
   mapped={x['outcome']:x for x in a['clusters']}
   self.assertEqual(mapped['incorrect']['status'],'source_prerequisite_candidates')
   self.assertEqual(mapped['abstain']['status'],'diagnose_before_training')
   self.assertFalse(a['weight_training']);self.assertFalse(a['production_authority'])
 def test_tampering_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'ledger.sqlite3'
   with Ledger(p) as b:
    r=b.reserve('m','a'*64,'arithmetic',1);b.finish(r['attempt'],'ABSTAIN','stop',1,1.)
    with b.db:b.db.execute("update attempts set outcome='incorrect'")
   with self.assertRaises(ValueError):read_failures(p)
 def test_missing_ledger_is_not_completed_inference(self):
  with tempfile.TemporaryDirectory() as d:
   self.assertEqual(read_failures(pathlib.Path(d)/'missing.sqlite3'),[])
   result=plan(corpus(),[])
   self.assertEqual(result['status'],'no_verified_failures')
   self.assertEqual(result['clusters'],[])
if __name__=='__main__':unittest.main()
