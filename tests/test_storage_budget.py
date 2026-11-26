import json,pathlib,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from storage_budget import budget,LEGACY,RETIRED,expansion_lane,incremental_usage
from acquisition_receipt import TAG,DIGEST
from neural_priority import can_admit,priority_plan,protected_remaining
from intelligence_resources import admit,neural_complete

class StorageBudgetTest(unittest.TestCase):
 def test_retirement_gate_and_exact_balances(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);self.assertEqual(budget(root),LEGACY)
   p=root/'experience'/'large-model-retirement-20261126.json';p.parent.mkdir()
   r={'removed':TAG,'digest':DIGEST,'free_before':5862600704,'free_after':35840958464,
      'reclaimed':29978357760,'queue_status':'ready','historical_receipt':True,
      'task_trigger_preserved':True,'deployed_revision':'b'*40}
   p.write_text(json.dumps(r))
   with patch('storage_budget.completed_receipt',return_value=True):
    self.assertEqual(budget(root),RETIRED)
    r['reclaimed']=1;p.write_text(json.dumps(r))
    with self.assertRaises(ValueError):budget(root)
 def test_reserve_and_expansion_caps(self):
  b=RETIRED
  self.assertEqual(b.native_additional+b.specialist_additional,18000000000)
  self.assertEqual(b.floor,7800000000)
  self.assertFalse(can_admit(42000000000,1000000000,8799999999,0,cap=b.neural_cap,floor=b.floor))
  self.assertTrue(can_admit(42000000000,1000000000,8800000000,0,cap=b.neural_cap,floor=b.floor))
  self.assertFalse(can_admit(59900000000,200000000,35000000000,0,cap=b.neural_cap,floor=b.floor))
  self.assertEqual(priority_plan('ready',False,False,9999,10000,{'cap_bytes':42000000000,'status':'pass_finished','results':[]},cap=b.neural_cap),'eligible')
  self.assertEqual(protected_remaining(4500000000,500000000,resource_cap=b.resource_cap,learning_reserve=b.learning_reserve),10000000000)
 def test_resource_gate_no_reserve_override(self):
  b=RETIRED
  self.assertTrue(admit(1500000000,0,1000000000,13800000000,0,5000000000,3000000000,cap=b.resource_cap,floor=b.floor))
  self.assertFalse(admit(1500000000,0,1000000000,13799999999,0,5000000000,3000000000,cap=b.resource_cap,floor=b.floor))
  self.assertFalse(neural_complete({'status':'pass_finished','cap_bytes':42000000000,'results':[]},cap=b.neural_cap))
 def test_lane_growth_accounts_for_existing_partials(self):
  self.assertEqual(expansion_lane('code_generation'),'native')
  self.assertEqual(expansion_lane('visual_features'),'specialist')
  self.assertEqual(incremental_usage({'old':10,'partial':20},{'old':10,'partial':35,'new':7},{'partial':'native','new':'specialist'}),{'native':15,'specialist':7})
  with self.assertRaises(ValueError):incremental_usage({'old':10},{'old':9},{})
if __name__=='__main__':unittest.main()
