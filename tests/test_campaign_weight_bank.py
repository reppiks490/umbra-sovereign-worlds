import sys,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from campaign_weight_bank import admission,MAX_AGENTS
class BankTest(unittest.TestCase):
 def test_admission_prioritizes_existing_allocations(self):
  self.assertEqual(admission(0,0,30000000000,4000000000,False,False),4)
  self.assertEqual(admission(0,0,30000000000,2999999999,False,False),0)
  self.assertEqual(admission(0,0,5999999999,4000000000,False,False),0)
  self.assertEqual(admission(0,0,30000000000,4000000000,True,False),0)
  self.assertEqual(admission(0,0,30000000000,4000000000,False,True),0)
 def test_bounded_bank_and_learning_workspace(self):
  self.assertEqual(admission(MAX_AGENTS-1,0,30000000000,4000000000,False,False),1)
  self.assertEqual(admission(MAX_AGENTS,0,30000000000,4000000000,False,False),0)
  self.assertEqual(admission(0,2999000000,30000000000,4000000000,False,False),0)
