import copy, unittest, json, hashlib, tempfile
from pathlib import Path
from unittest.mock import patch
import evolution_research_protocol_v67 as p
from test_evolution_protocol_receipt_v69 import KEY, signed, fixture, correct_result
import evolution_paired_audit_v71 as m

def receipt(seed, compact_ok=True, explicit_ok=True):
    r=fixture(); r['seed']=seed; cases=p.cases(seed)
    for v,ok in zip(r['results'],(compact_ok,explicit_ok)):
        answers=[(c['expected'] if ok else next(x for x in 'ABC' if x!=c['expected']),c['evidence_id']) for c in cases]
        v['raw']=json.dumps([a+b[1] for a,b in answers] if v['protocol']=='compact' else [{'n':i+1,'action':a,'fact':b} for i,(a,b) in enumerate(answers)])
        v['case_sha256']=hashlib.sha256(p.ev.canonical(cases)).hexdigest()
        v.update(p.score(cases,v['raw'],v['protocol']))
    r['comparison']=p.compare(*r['results'])
    return signed(r)

class AuditTests(unittest.TestCase):
    def test_eight_windows_cover_full_factorial(self):
        a=[m.plan(i*14400+300) for i in range(8)]
        self.assertEqual({(x['family'],x['first']) for x in a},{(f,o) for f in range(4) for o in ('compact','explicit')})
        self.assertEqual(m.plan(300),m.plan(301))
        self.assertNotEqual(m.plan(300),m.plan(14700))
    def test_paired_summary_and_independent_seed_units(self):
        r=m.audit([receipt(i,False,True) for i in range(8)],KEY)
        self.assertEqual(r['completed_pairs'],8)
        self.assertEqual(r['explicit_only_cases'],32)
        self.assertEqual(r['seed_wins'],8)
        self.assertAlmostEqual(r['two_sided_sign_p'],2/256)
        self.assertFalse(r['routing_authorized'])
    def test_duplicate_and_tampering_rejected(self):
        a=receipt(0)
        with self.assertRaises(ValueError):m.audit([a,a],KEY)
        b=copy.deepcopy(a);b['comparison']['joint_delta']=100
        with self.assertRaises(ValueError):m.audit([b],KEY)
    def test_failed_pairs_in_denominator(self):
        a=receipt(0);a.pop('hmac_sha256');a['status']='failed';a.pop('comparison');a['results'].pop();a['errors']=[{'protocol':'explicit','error_class':'TimeoutError'}]
        r=m.audit([signed(a),receipt(1)],KEY)
        self.assertEqual((r['attempted_pairs'],r['completed_pairs'],r['failed_pairs']),(2,1,1))
        self.assertEqual(r['two_sided_sign_p'],1.0)
    def test_bad_clock(self):
        for x in (True,-1,1.5):
            with self.assertRaises(ValueError):m.plan(x)

def versioned(seed=4):
    r=receipt(seed);r.pop('hmac_sha256')
    design=m.plan(seed*14400)
    r['schema']='myriad.research_protocol.v73'
    r['design']={'revision':'counterbalanced-v73',**design}
    r['attempt_order']=[design['first'],'explicit' if design['first']=='compact' else 'compact']
    r['results'].sort(key=lambda v:r['attempt_order'].index(v['protocol']))
    return r

class ProvenanceTests(unittest.TestCase):
    def test_versioned_and_legacy_receipts_replay(self):
        self.assertTrue(p.verify(signed(versioned()),KEY))
        self.assertTrue(p.verify(receipt(4),KEY))
    def test_reject_inconsistent_design_or_attempt_order(self):
        for change in ('family','revision','order','results','bool_family'):
            r=versioned()
            if change=='family':r['design']['family']=3
            elif change=='revision':r['design']['revision']='unknown'
            elif change=='order':r['attempt_order'].reverse()
            elif change=='results':r['results'].reverse()
            else:r['design']['family']=False
            with self.subTest(change=change),self.assertRaises(ValueError):
                p.verify(signed(r),KEY)
    def test_separate_cohorts_and_reject_mixed_audit(self):
        old=receipt(1,False,True);new=signed(versioned(4))
        with self.assertRaises(ValueError):m.audit([old,new],KEY)
        a=m.audit_cohorts([old,new],KEY)
        self.assertEqual(a['legacy_unversioned']['completed_pairs'],1)
        self.assertEqual(a['counterbalanced_v73']['completed_pairs'],1)
        self.assertFalse(a['routing_authorized'])
    def test_failed_order_is_authenticated_and_counted(self):
        r=versioned();r.pop('comparison');r['status']='failed';r['results'].pop(0)
        r['errors']=[{'protocol':'explicit','error_class':'ValueError','stage':'score'}]
        self.assertTrue(p.verify(signed(r),KEY))
        a=m.audit([signed(r)],KEY)
        self.assertEqual(a['family_coverage']['0']['explicit_first'],1)
        self.assertEqual(a['failed_pairs'],1)
        r['errors'][0]['stage']='private data'
        with self.assertRaises(ValueError):p.verify(signed(r),KEY)
    def test_live_runner_persists_version_and_safe_error_stage(self):
        def simulated(c,protocol):
            if protocol=='explicit':raise p.ProtocolFailure('score','ValueError')
            return correct_result(c,protocol)
        with tempfile.TemporaryDirectory() as tmp, patch.object(p.scale,'free_mb',return_value=4000), patch.object(p.teacher,'request',return_value=({'models':[]},b'')),patch.object(p.ev,'secret',return_value=KEY),patch.object(p.time,'time',return_value=4*14400+300),patch.object(p,'infer',side_effect=simulated):
            root=Path(tmp);out=p.run(root,7000)
            self.assertEqual(out['schema'],'myriad.research_protocol.v73')
            self.assertEqual(out['attempt_order'],['explicit','compact'])
            self.assertEqual(out['errors'],[{'protocol':'explicit','error_class':'ValueError','stage':'score'}])
            r=json.loads(next((root/'teacher-v40').glob('protocol-v67-*.json')).read_text())
            self.assertTrue(p.verify(r,KEY))
            self.assertNotIn('raw',json.dumps(out))
    def test_inference_failure_stage_is_specific(self):
        c=p.cases(4)
        for body,stage in [({'model':p.MODEL,'done':False},'envelope'),({'model':p.MODEL,'done':True,'done_reason':'stop','message':{}},'message'),({'model':p.MODEL,'done':True,'done_reason':'stop','message':{'content':'[]'}},'score')]:
            with self.subTest(stage=stage),patch.object(p.native,'_pin'),patch.object(p.teacher,'request',return_value=(body,b'{}')):
                with self.assertRaises(p.ProtocolFailure) as cm:p.infer(c,'explicit')
                self.assertEqual(cm.exception.stage,stage)

if __name__=='__main__':unittest.main()
