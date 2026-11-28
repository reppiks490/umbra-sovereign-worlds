import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from capability_frontier import classify_route,ROUTES,make_frontier
class FrontierTest(unittest.TestCase):
 def test_evidence_gates(self):
  self.assertEqual(classify_route(False,False,False,False),'missing')
  self.assertEqual(classify_route(True,False,False,False),'installed_only')
  self.assertEqual(classify_route(True,True,False,False),'connected')
  self.assertEqual(classify_route(True,True,True,False),'executed')
  self.assertEqual(classify_route(True,True,True,True),'evaluated')
  with self.assertRaises(ValueError):classify_route(False,True,True,True)
 def test_frontier_counts_no_implied_proof(self):
  r=make_frontier({'native_bundles':33,'students':16,'source_repos':23,'human_records':8792,'student_feeds':3,'optimizer_steps':4,'accepted_adapters':0,'icarus_repos':10,'resource_files':71})
  self.assertGreaterEqual(len(ROUTES),20)
  self.assertEqual(r['counts']['student_specialist_pairs'],528)
  self.assertFalse(r['exhausted'])
  self.assertEqual(r['counts']['accepted_adapters'],0)
  self.assertGreater(len(r['gaps']),0)
