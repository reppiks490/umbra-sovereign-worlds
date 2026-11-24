"""Transfer tasks distinguish common structure from arbitrary shifted labels."""
import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import evolution_transfer_curriculum_v19 as transfer
import evolution_algorithms_v19 as lab

class TransferTests(unittest.TestCase):
    def test_seed_separation_and_structural_transfer(self):
        a=lab.task('shifted-sphere',4,seed=100,structure='shared')
        b=lab.task('shifted-sphere',4,seed=101,structure='shared')
        unrelated=lab.task('shifted-sphere',4,seed=102,structure='independent')
        center=[.5]*4
        self.assertNotEqual(a(center),b(center))
        self.assertNotEqual(a(center),unrelated(center))
    def test_reproducibility_and_summary_certification(self):
        first=transfer.run(budgets=(32,),seeds=2,dimension=4)
        second=transfer.run(budgets=(32,),seeds=2,dimension=4)
        self.assertEqual(first,second)
        sig=first.pop('sha256');self.assertEqual(sig,lab.stable_hash(first))
        self.assertEqual(first['total_trials'],120)
        self.assertTrue(first['train_holdout_seed_separation'])
        self.assertFalse(first['real_world_validation'])
    def test_bad_curriculum_parameters(self):
        with self.assertRaises(ValueError):transfer.run(budgets=(0,))
        with self.assertRaises(ValueError):transfer.run(seeds=101)
        with self.assertRaises(ValueError):lab.task('shifted-sphere',structure='unsupported')
if __name__=='__main__':unittest.main()
