import unittest,sys,pathlib,tempfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from intelligence_resources import BUDGETS,admit,neural_complete,dataset_rows
class ResourcesTest(unittest.TestCase):
 def test_budget_and_protection(self):
  self.assertEqual(sum(BUDGETS.values()),15000000000)
  self.assertTrue(admit(0,0,1000000000,12000000000,2000000000,3000000000,2000000000))
  self.assertFalse(admit(0,0,1000000000,8999999999,2000000000,3000000000,2000000000))
  self.assertFalse(admit(14900000000,0,200000000,30000000000,0,0,2000000000))
  self.assertFalse(admit(0,1900000000,200000000,30000000000,0,0,2000000000))
 def test_neural_first(self):
  self.assertFalse(neural_complete({'cap_bytes':15000000000,'status':'pass_finished','results':[]}))
  self.assertFalse(neural_complete({'cap_bytes':28000000000,'status':'pass_finished','results':[{'status':'retry_needed'}]}))
  self.assertTrue(neural_complete({'cap_bytes':28000000000,'status':'pass_finished','results':[{'status':'deferred_storage'}]}))
 def test_dataset_metadata_requires_license_pinned_hash_safe_path(self):
  m={'id':'openai/gsm8k','sha':'a'*40,'private':False,'gated':False,'cardData':{'license':'mit'},'siblings':[{'rfilename':'main/train.parquet','size':100,'lfs':{'sha256':'b'*64}},{'rfilename':'../evil.parquet','size':100,'lfs':{'sha256':'b'*64}},{'rfilename':'data/script.py','size':100,'lfs':{'sha256':'b'*64}},{'rfilename':'main/test.parquet','size':101,'lfs':{'sha256':'c'*64}}]}
  r=dataset_rows('openai/gsm8k','reasoning',m)
  self.assertEqual([x['path'] for x in r],['main/train.parquet','main/test.parquet'])
  self.assertEqual(dataset_rows('openai/gsm8k','reasoning',{**m,'gated':True}),[])
  self.assertEqual(dataset_rows('openai/gsm8k','reasoning',{**m,'cardData':{}}),[])
