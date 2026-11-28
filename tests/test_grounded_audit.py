import sys,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from grounded_reasoning import grade_pair,audit_trial
from research_portfolio import command_for,normalize,LANES
from human_corpus import validate
import hashlib,json
class GroundedAuditTest(unittest.TestCase):
 def fixture(self):
  row=validate({'question':'Calculate 17x2.','answer':'#### 34'})
  m={'model':'qwen3:0.6b','digest':'a'*64,'protocol':'grounded-exact-arithmetic-paired-v1','offset':0,'count':1,'validation_records':[row['record_sha256']]}
  cid=row['record_sha256']
  r={'status':'completed','manifest':m,'manifest_sha256':hashlib.sha256(json.dumps(m,sort_keys=True).encode()).hexdigest(),'cases':1,'model_calls':2,'completed_calls':2,'direct_correct':0,'hybrid_correct':1,'wins':1,'losses':0,'test_partition_used_for_inference':False,'production_authority':False,'weight_training':False,'records':[{'case':cid,**grade_pair(row['question'],'34','ANSWER: 33','EXPR: 17*2')}],'calls':[{'case':cid,'arm':'direct','status':'evaluated','response':'ANSWER: 33','seconds':1.0},{'case':cid,'arm':'hybrid','status':'evaluated','response':'EXPR: 17*2','seconds':1.0}]}
  return r,[row]
 def test_replay_actual_proposal(self):
  r,rows=self.fixture();self.assertEqual(audit_trial(r,rows)['hybrid_correct'],1)
 def test_altered_score_or_response_rejected(self):
  r,rows=self.fixture();r['calls'][1]['response']='EXPR: 17+2'
  with self.assertRaises(ValueError):audit_trial(r,rows)
 def test_manifest_source_mismatch(self):
  r,rows=self.fixture();rows[0]['record_sha256']='c'*64
  with self.assertRaises(ValueError):audit_trial(r,rows)
 def test_scheduler_integration(self):
  self.assertIn('grounded_reasoning',LANES)
  cmd=command_for('grounded_reasoning',pathlib.Path('data'),pathlib.Path('python'),3)
  self.assertIn('102',cmd)
  self.assertEqual(normalize('grounded_reasoning',{'status':'completed','model_calls':4,'completed_calls':4}),'completed')
if __name__=='__main__':unittest.main()
