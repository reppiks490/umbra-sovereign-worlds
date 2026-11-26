import pathlib, sys, unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from council_qualification import evaluate

class CouncilQualificationTest(unittest.TestCase):
 def setUp(self):
  self.models={'alpha':'a'*64,'beta':'b'*64,'gamma':'c'*64}
  self.cases={'case1':'7','case2':'9','case3':'4'}
 def rows(self):
  return [{'case':c,'model':m,'digest':d,'status':'evaluated','prediction':p,'seconds':1.0}
          for c,ps in zip(self.cases,[['7','7','8'],['9','8',None],['3','4','4']])
          for (m,d),p in zip(self.models.items(),ps)]
 def test_paired_comparison_and_abstention(self):
  r=evaluate(self.cases,self.models,self.rows())
  self.assertEqual(r['ensemble']['correct'],2)
  self.assertEqual(r['ensemble']['answered'],2)
  self.assertEqual(r['ensemble']['cases'],3)
  self.assertEqual(r['baselines']['alpha']['correct'],2)
  self.assertEqual(r['paired']['alpha']['wins'],1)
  self.assertEqual(r['paired']['alpha']['losses'],1)
  self.assertEqual(r['inference_seconds'],9)
  self.assertFalse(r['production_authority'])
 def test_rejects_duplicate_or_missing_model_case(self):
  rows=self.rows()
  for bad in (rows[:-1],rows+[rows[0]]):
   with self.assertRaises(ValueError):evaluate(self.cases,self.models,bad)
 def test_rejects_wrong_or_duplicate_weight_identity(self):
  rows=self.rows();rows[0]['digest']='f'*64
  with self.assertRaises(ValueError):evaluate(self.cases,self.models,rows)
  with self.assertRaises(ValueError):evaluate(self.cases,{'alpha':'a'*64,'beta':'a'*64,'gamma':'c'*64},self.rows())
 def test_failure_cannot_cast_vote(self):
  rows=self.rows();rows[1]['status']='failed'
  r=evaluate(self.cases,self.models,rows)
  self.assertEqual(r['ensemble']['answered'],1)
  self.assertEqual(r['ensemble']['correct'],1)
 def test_rejects_invalid_latency_and_truth(self):
  rows=self.rows();rows[0]['seconds']=float('nan')
  with self.assertRaises(ValueError):evaluate(self.cases,self.models,rows)
  with self.assertRaises(ValueError):evaluate({'case1':'not a number',**{k:v for k,v in self.cases.items() if k!='case1'}},self.models,self.rows())
 def test_treats_all_abstentions_as_zero_accuracy(self):
  rows=self.rows()
  for row in rows:row['prediction']=None
  r=evaluate(self.cases,self.models,rows)
  self.assertEqual(r['ensemble']['accuracy'],0)
  self.assertIsNone(r['ensemble']['answered_accuracy'])
if __name__=='__main__':unittest.main()
