import unittest,tempfile,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from neural_priority import can_admit,FLOOR
from learning_workspace import FLOOR as WORKSPACE_FLOOR
from hf_weight_cache import MIN_FREE
from infinity_service import bootstrap_plan
class ReserveTest(unittest.TestCase):
 def test_shared_three_gb_floor(self):
  self.assertEqual(FLOOR,3000000000)
  self.assertEqual(WORKSPACE_FLOOR,FLOOR)
  self.assertEqual(MIN_FREE,FLOOR)
  self.assertTrue(can_admit(12000000000,1000000000,6000000000,2000000000))
  self.assertFalse(can_admit(12000000000,1000000000,5999999999,2000000000))
 def test_bootstrap_keeps_remaining_install_budget(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)
   self.assertEqual(bootstrap_plan(p,'ready',6000000000,0,100000,1500000000)['status'],'eligible')
   self.assertEqual(bootstrap_plan(p,'ready',5999999999,0,100000,1500000000)['status'],'deferred_storage')
