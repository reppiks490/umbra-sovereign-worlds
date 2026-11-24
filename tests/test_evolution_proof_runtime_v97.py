import hashlib,json,unittest
import evolution_proof_runtime_v97 as m

DIGEST='a'*64

def reply(**kw):
    x={'model':m.MODEL,'done':True,'done_reason':'stop','message':{'content':'[]'},'prompt_eval_count':500,'eval_count':42}
    x.update(kw);return x,json.dumps(x).encode()

class Tests(unittest.TestCase):
    def test_capture_reports_only_verified_completion(self):
        events=[]
        def pin(*a):events.append(('pin',a))
        def request(route,body,timeout):
            events.append(('request',route,body,timeout));return reply()
        call,meta=m.capture('initial','test',DIGEST,pin,request)
        self.assertEqual(call['raw'],'[]');self.assertEqual(meta['completion_tokens'],42)
        self.assertEqual(meta['prompt_tokens'],500);self.assertTrue(meta['pin_verified'])
        self.assertEqual([e[0] for e in events],['pin','request','pin'])
        self.assertEqual(events[1][2]['options']['num_predict'],m.CAP)
        self.assertTrue(m.validate_capture(call,meta))
    def test_bad_envelope_not_counted(self):
        for change in ({'model':'other'},{'done':1},{'done_reason':'length'},{'eval_count':257},{'prompt_eval_count':True},{'message':{'content':'x'*8193}}):
            with self.subTest(change=str(change)[:60]):
                c,r=m.capture('guided','test',DIGEST,lambda *a:None,lambda *a:reply(**change))
                self.assertEqual(c['status'],'failed');self.assertFalse(r['pin_verified']);self.assertTrue(r['request_started']);self.assertTrue(m.validate_capture(c,r))
    def test_pin_and_request_failures_distinguished(self):
        def boom(*a):raise OSError('private diagnostic')
        c,r=m.capture('control','test',DIGEST,boom,lambda *a:reply())
        self.assertFalse(r['request_started']);self.assertEqual(r['stage'],'pin_before')
        self.assertNotIn('private diagnostic',str((c,r)))
        c,r=m.capture('control','test',DIGEST,lambda *a:None,boom)
        self.assertTrue(r['request_started']);self.assertEqual(r['stage'],'request')
    def test_capture_metadata_tamper(self):
        c,r=m.capture('initial','test',DIGEST,lambda *a:None,lambda *a:reply())
        for changed in ({'completion_tokens':True},{'pin_verified':False},{'response_sha256':'bad'},{'seconds':float('nan')},{'arm':'guided'},{'request_started':False}):
            with self.subTest(changed=changed),self.assertRaises(ValueError):m.validate_capture(c,{**r,**changed})
    def test_capped_equal_generation_budget(self):
        bodies=[]
        for arm in ('initial','guided','control'):
            def request(route,body,timeout):bodies.append(body);return reply()
            m.capture(arm,arm,DIGEST,lambda *a:None,request)
        self.assertTrue(all(b['options']==bodies[0]['options'] for b in bodies))
        self.assertTrue(all(b['format']==bodies[0]['format'] for b in bodies))
    def test_admission_error_is_retained_without_inference(self):
        import sys
        from types import SimpleNamespace
        from unittest.mock import patch
        bench=SimpleNamespace(cases=lambda seed:[],order=lambda seed:list(m.ARMS),prompt=lambda q,arm,initial:arm,assemble=lambda seed,calls:{'calls':calls,'seed':seed})
        def unavailable():raise OSError('private details')
        def unexpected(*a):self.fail('model should not be called')
        with patch.dict(sys.modules,{'evolution_proof_feedback_v90':bench}):
            r=m.experiment(4,DIGEST,unexpected,unexpected,unavailable)
        self.assertEqual(r['status'],'failed')
        self.assertEqual([x['stage'] for x in r['captures']],['admission']*3)
        self.assertTrue(all(not x['request_started'] for x in r['captures']))
        self.assertNotIn('private details',str(r))
if __name__=='__main__':unittest.main()
