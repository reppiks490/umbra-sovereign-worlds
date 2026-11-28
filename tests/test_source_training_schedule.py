import sys,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from source_training_schedule import select_candidate
class ScheduleTest(unittest.TestCase):
 def test_fair_and_bounded(self):
  a=[{'name':'a','required_ram':4500000000,'present':True,'state':{'attempts':1,'timestamp':1000}},{'name':'b','required_ram':5000000000,'present':True,'state':{}},{'name':'c','required_ram':4000000000,'present':False,'state':{}}]
  self.assertEqual(select_candidate(a,6000000000,5000)['name'],'b')
  self.assertEqual(select_candidate(a,4500000000,5000)['name'],'a')
  self.assertIsNone(select_candidate(a,4500000000,2000))
  a[0]['state']['attempts']=20
  self.assertIsNone(select_candidate(a,4500000000,5000))
