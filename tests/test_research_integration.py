import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from research_portfolio import service_due, normalize, evidence_snapshot
class IntegrationTest(unittest.TestCase):
 def test_alternate_research_cycles(self):
  self.assertTrue(service_due(0))
  self.assertFalse(service_due(1800))
  self.assertTrue(service_due(3600))
 def test_unverified_counts_are_not_success(self):
  self.assertEqual(normalize('collective',{'status':'completed','model_calls':6,'completed_calls':2}),'partial')
  self.assertEqual(normalize('neural_routing',{'status':'completed','specialists':[{}, {}, {}],'candidate_answer':{}}),'partial')
 def test_snapshot_empty(self):
  import tempfile
  with tempfile.TemporaryDirectory() as d:
   r=evidence_snapshot(pathlib.Path(d))
   self.assertEqual(r['collective']['cases'],0)
   self.assertEqual(r['lesson_retrieval']['cases'],0)
   self.assertEqual(r['instruction_following']['cases'],0)
   self.assertFalse(r['production_authority'])
if __name__=='__main__':unittest.main()
