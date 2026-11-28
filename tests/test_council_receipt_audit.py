import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from council_qualification import evaluate
from council_receipt_audit import replay_trial
class ReplayTest(unittest.TestCase):
 def fixture(self):
  models={'a':'a'*64,'b':'b'*64,'c':'c'*64}
  cid='d'*64
  rows=[{'case':cid,'model':m,'digest':d,'prediction':p,'status':'evaluated','seconds':1.0} for (m,d),p in zip(models.items(),['8','8','9'])]
  r=evaluate({cid:'8'},models,rows)
  r.update(status='completed',manifest={'models':models,'offset':0,'count':1,'validation_records':[cid],'protocol':'fixed-one-human-example-strict-majority-v1'},rows=rows,model_calls=3,completed_calls=3,test_partition_used_for_inference=False)
  return r,{cid:'8'}
 def test_replay_valid(self):
  r,t=self.fixture();self.assertEqual(replay_trial(r,t)['correct'],1)
 def test_wrong_source_identity(self):
  r,t=self.fixture()
  with self.assertRaises(ValueError):replay_trial(r,{'e'*64:'8'})
 def test_forged_prediction_even_if_receipt_rehashed(self):
  r,t=self.fixture();r['rows'][0]['prediction']='9'
  with self.assertRaises(ValueError):replay_trial(r,t)
 def test_missing_rows_fails(self):
  r,t=self.fixture();del r['rows']
  with self.assertRaises(ValueError):replay_trial(r,t)
 def test_reject_different_gold(self):
  r,t=self.fixture()
  with self.assertRaises(ValueError):replay_trial(r,{next(iter(t)):'9'})
if __name__=='__main__':unittest.main()
