"""Independent, deterministic and negative-case coverage for 12 real optimizers."""
import json, math, sys, tempfile, unittest
from dataclasses import asdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import evolution_algorithms_v19 as lab
import evolution_tournament_v19 as tournament
import umbra_evolution_mesh as mesh

class IndependentAlgorithmTests(unittest.TestCase):
    def test_twelve_separate_algorithm_implementations(self):
        self.assertEqual(len(lab.METHODS),12)
        self.assertEqual(len(set(lab.METHODS)),12)
        self.assertEqual(set(lab.METHODS),set(lab.REFERENCE))
        self.assertTrue(all(x.startswith('https://') for x in lab.REFERENCE.values()))

    def test_every_method_deterministic_bounded_and_improves_baseline(self):
        for i,algo in enumerate(lab.METHODS):
            fn=lab.task('shifted-sphere',dimension=4,seed=128+i)
            x=lab.optimize(algo,fn,dimension=4,budget=90,seed=341+i)
            y=lab.optimize(algo,fn,dimension=4,budget=90,seed=341+i)
            self.assertEqual(x,y,algo)
            self.assertGreaterEqual(x.score,fn([.5]*4)-1e-8,algo)
            self.assertLessEqual(x.evaluations,x.budget,algo)
            self.assertGreaterEqual(x.evaluations,1,algo)
            self.assertTrue(all(0<=v<=1 for v in x.best),algo)
            self.assertFalse(x.real_model_weights_changed)
            self.assertEqual(x.live_trades,0)
            self.assertEqual(len(x.best),4)

    def test_multitask_multiseed_suite_has_receipt(self):
        a=lab.suite(budget=32,seeds=2,dimensions=4)
        b=lab.suite(budget=32,seeds=2,dimensions=4)
        self.assertEqual(a,b)
        self.assertEqual(a['case_count'],12*5*2)
        sig=a.pop('sha256')
        self.assertEqual(sig,lab.stable_hash(a))
        self.assertTrue(all(math.isfinite(c['best_score']) for c in a['results']))
        self.assertEqual(a['real_model_weight_updates'],0)

    def test_invalid_or_unbounded_methods_rejected(self):
        with self.assertRaises(ValueError):lab.optimize('not-an-algorithm',lambda _:1)
        with self.assertRaises(ValueError):lab.optimize(lab.METHODS[0],lambda _:1,budget=10**7)
        with self.assertRaises(ValueError):lab.optimize(lab.METHODS[0],lambda _:1,dimension=0)
        with self.assertRaises(ValueError):lab.optimize(lab.METHODS[0],lambda _:float('nan'))
        with self.assertRaises(ValueError):lab.optimize(lab.METHODS[0],lambda _:1,seed=-1)

    def test_all_twelve_worker_methods_bridge_compatible(self):
        proposals=tournament.batch(start=1,count=12,budget=32)
        self.assertEqual(len({x['optimizer_evidence_v19']['method'] for x in proposals}),12)
        for x in proposals:
            signature=x.pop('receipt_sha256')
            self.assertEqual(mesh.digest(x),signature)
            self.assertEqual(x['schema'],mesh.SCHEMA)
            self.assertEqual(len(x['parameters']),8)
            self.assertFalse(x['deployment_authorized'])
            self.assertFalse(x['real_model_weight_training'])
            self.assertEqual(x['optimizer_evidence_v19']['training_protocol'],'synthetic_fixture_only')

    def test_repeat_eval_and_no_autopromote(self):
        x=tournament.proposal(74,budget=48)
        self.assertEqual(x,tournament.proposal(74,budget=48))
        self.assertIn(x['review_status'],('candidate_for_manual_review','rejected_synthetic'))
        self.assertFalse(x['deployment_authorized'])
        with self.assertRaises(ValueError):tournament.batch(start=195000,count=2)
        with self.assertRaises(ValueError):tournament.batch(start=1,count=501)

if __name__=='__main__':unittest.main()
