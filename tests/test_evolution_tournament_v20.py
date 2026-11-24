"""Sealed candidate records from seven new optimizers, no self-promotion."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import evolution_umbra_tournament_v20 as t
import evolution_algorithms_v20 as optim
import umbra_evolution_mesh as mesh
from evolution_tribunal_v19 import verify_record

class Proposals(unittest.TestCase):
 def test_all_seven_qualified_under_v19_independent_replay(self):
  records=t.batch(start=1,count=7,budget=32)
  self.assertEqual({x['optimizer_evidence_v20']['method'] for x in records},set(optim.METHODS_V20))
  for x in records:
   self.assertTrue(verify_record(x)['replay_passed'])
   self.assertFalse(x['deployment_authorized'])
   self.assertFalse(x['real_model_weight_training'])
   self.assertFalse(x['optimizer_evidence_v20']['real_umbra_engine_training'])
   r=x.copy();sha=r.pop('receipt_sha256')
   self.assertEqual(mesh.digest(r),sha)
 def test_deterministic_and_budget_guard(self):
  self.assertEqual(t.batch(start=2,count=2,budget=24),t.batch(start=2,count=2,budget=24))
  with self.assertRaises(ValueError):t.batch(start=195000,count=2)
  with self.assertRaises(ValueError):t.batch(budget=129)

if __name__=='__main__':unittest.main()
