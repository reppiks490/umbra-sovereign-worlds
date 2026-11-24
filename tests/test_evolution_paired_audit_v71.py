import copy, unittest, json, hashlib
import evolution_research_protocol_v67 as p
from test_evolution_protocol_receipt_v69 import KEY, signed, fixture
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

if __name__=='__main__':unittest.main()
