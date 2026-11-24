"""v2.8 adversarial tests: new tasks, baselines, replay and provenance."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import evolution_transfer_ood_v28 as ood

class TransferGate(unittest.TestCase):
    def test_precommitted_families_and_distinct_targets(self):
        self.assertEqual(ood.FAMILIES,('antipodal','nonlinear_interaction','independent_linear'))
        self.assertFalse('synthetic_v25_teacher' in ood.FAMILIES)
        self.assertEqual(len(set(ood.FAMILIES)),3)
    def test_seed_guards(self):
        for bad in [False,-1,0,1337,900000,900001,999999999999]:
            with self.subTest(bad=bad),self.assertRaises(ValueError):ood.validate_seed(bad)
        self.assertEqual(ood.validate_seed(980004),980004)
    def test_score_requires_finite_nonnegative_and_zero_baseline(self):
        d=ood.score(0.4,0.2,0.3)
        self.assertTrue(d['beats_source'])
        self.assertTrue(d['beats_zero'])
        self.assertEqual(d['candidate_mse'],0.2)
        self.assertFalse(ood.score(0.4,0.3,0.1)['beats_zero'])
        for vals in [(0.3,float('nan'),0.3),(0.3,-0.1,0.3),(float('inf'),0.2,0.3),(0.2,0.1,True)]:
            with self.subTest(vals=vals),self.assertRaises(ValueError):ood.score(*vals)
    def test_no_default_authority(self):
        with self.assertRaises(PermissionError):ood.run('missing.zip','missing', 'output',seed=980004,authorize=False)
    def test_nonoverwriting_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.json'
            path.write_text('immutable')
            with self.assertRaises(FileExistsError):ood.run('missing.zip','missing',path,seed=980004,authorize=True)
            self.assertEqual(path.read_text(),'immutable')
    def test_resealed_score_and_baseline_forgery_caught(self):
        row={'source_mse':0.6,'candidate_mse':0.2,'zero_mse':0.1,'beats_source':True,'beats_zero':False}
        proof=ood.seal({'schema':ood.SCHEMA,'seed':980004,'families':list(ood.FAMILIES),'rows':[row],'production_authority':False,'trading_alpha_certified':False,'model_promotion':False})
        self.assertTrue(ood.verify_seal(proof))
        forged=dict(proof);forged['rows']=[{**row,'beats_zero':True}]
        forged=ood.seal({k:v for k,v in forged.items() if k!='receipt_sha256'})
        with self.assertRaises(ValueError):ood.verify_seal(forged)
    def test_no_inflated_claims(self):
        row={'source_mse':0.6,'candidate_mse':0.2,'zero_mse':0.1,'beats_source':True,'beats_zero':False}
        for flag in ('production_authority','trading_alpha_certified','model_promotion'):
            with self.subTest(flag=flag):
                p=ood.seal({'schema':ood.SCHEMA,'seed':980004,'families':list(ood.FAMILIES),'rows':[row],'production_authority':False,'trading_alpha_certified':False,'model_promotion':False,flag:True})
                with self.assertRaises(ValueError):ood.verify_seal(p)
if __name__=='__main__':unittest.main()
