"""v3.0: fail-closed evidence gate cannot mistake self-certified accuracy for transfer."""
import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import evolution_cross_task_gate_v30 as gate
import evolution_transfer_ood_v28 as ood

class PromotionGateTests(unittest.TestCase):
    def sample(self, seed, winner=False):
        rows=[]
        for family in ood.FAMILIES:
            for i in range(1,11):
                row={'subject':'agent','identity':i,'family':family,
                     'inputs_sha256':'a'*64,'target_sha256':'b'*64,
                     **ood.score(1.0,0.2 if winner else 2.0,0.3)}
                rows.append(row)
            rows.append({'subject':'ability_bank','identity':10000,'family':family,
                         'inputs_sha256':'a'*64,'target_sha256':'b'*64,
                         **ood.score(1.0,0.2 if winner else 2.0,0.3)})
        count=11 if winner else 0
        return ood.seal({'schema':ood.SCHEMA,'seed':seed,'families':list(ood.FAMILIES),
          'source_archive_sha256':'c'*64,'source_import_status':'imported_unverified',
          'v25_training_receipt_sha256':'d'*64,'candidate_agent_count':10,'candidate_adapter_count':10000,
          'rows':rows,'summary':{family:{'comparisons':11,'beats_source':count,
            'beats_zero':count,'wins_both':count} for family in ood.FAMILIES},
          'precommitted_seeds':list(ood.PREREGISTERED_SEEDS),'unseen_target_families':3,
          'selection_rule':'all 3 families; 10 agents and full ability adapter bank; zero baseline included',
          'scope':'cross-task synthetic targets; no real-world OOD or trading transfer',
          'production_authority':False,'trading_alpha_certified':False,'model_promotion':False})
    def test_fail_closed_on_negative_realistic_evidence(self):
        a=gate.assess([self.sample(980004),self.sample(980005)])
        self.assertEqual(a['status'],'BLOCKED_TRANSFER_EVIDENCE')
        self.assertEqual(a['wins_both'],0)
        self.assertFalse(a['production_authority'])
        self.assertEqual(a['production_release_gates_verified'],0)
    def test_passing_synthetic_evidence_only_qualifies_for_research_review(self):
        a=gate.assess([self.sample(980004,True),self.sample(980005,True)])
        self.assertEqual(a['status'],'RESEARCH_REVIEW_ELIGIBLE')
        self.assertFalse(a['production_authority'])
        self.assertFalse(a['automatic_promotion'])
        self.assertEqual(a['production_release_gates_verified'],0)
    def test_absent_seed_or_duplicate_seed_is_rejected(self):
        for rows in ([self.sample(980004)],[self.sample(980004)]*2):
            with self.subTest(rows=len(rows)),self.assertRaises(ValueError):gate.assess(rows)
    def test_wrong_agent_identity_or_duplicate_row_rejected_even_if_resealed(self):
        a=self.sample(980004)
        a['rows'][1]['identity']=1
        a=ood.seal(a)
        with self.assertRaises(ValueError):gate.assess([a,self.sample(980005)])
    def test_fake_aggregate_is_rejected_even_if_resealed(self):
        a=self.sample(980004)
        a['summary']['antipodal']['wins_both']=11
        a=ood.seal(a)
        with self.assertRaises(ValueError):gate.assess([a,self.sample(980005)])
    def test_cross_seed_source_mismatch_rejected(self):
        a=self.sample(980004);b=self.sample(980005)
        b['source_archive_sha256']='e'*64
        b=ood.seal(b)
        with self.assertRaises(ValueError):gate.assess([a,b])
    def test_changed_receipt_hash_rejected(self):
        a=self.sample(980004);a['receipt_sha256']='0'*64
        with self.assertRaises(ValueError):gate.assess([a,self.sample(980005)])
    def test_invalid_model_provenance_claim_rejected(self):
        a=self.sample(980004)
        a['source_import_status']='verified_training'
        a=ood.seal(a)
        with self.assertRaises(ValueError):gate.assess([a,self.sample(980005)])
    def test_no_execution_without_authorization(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(PermissionError):gate.run('missing.zip','missing',[Path(d)/'a',Path(d)/'b'],Path(d)/'out',authorize=False)
    def test_no_output_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            o=Path(d)/'receipt';o.write_text('original')
            with self.assertRaises(FileExistsError):gate.run('missing','missing',[],o,authorize=True)
            self.assertEqual(o.read_text(),'original')
    def test_receipt_seal_and_authority_integrity(self):
        report=gate.seal({'schema':gate.SCHEMA,'status':'BLOCKED_TRANSFER_EVIDENCE',
                          'production_authority':False,'automatic_promotion':False,'market_alpha_certified':False,
                          'production_release_gates_verified':0})
        self.assertTrue(gate.verify_seal(report))
        report['production_authority']=True
        report=gate.seal(report)
        with self.assertRaises(ValueError):gate.verify_seal(report)
if __name__=='__main__':unittest.main()
