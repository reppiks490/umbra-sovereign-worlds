import json,unittest
import evolution_proof_runtime_v97 as m
import evolution_proof_feedback_v90 as bench
import evolution_proof_curriculum_v84 as proof
import evolution_model_evidence_v24 as ev

class Integration(unittest.TestCase):
    def test_authentication_and_actual_certificate_replay_with_fixture_model(self):
        seed=4;d='a'*64;calls=[]
        raw=json.dumps([{'id':i,'certificate':proof.solve(q)} for i,q in enumerate(bench.cases(seed))])
        def request(route,body,timeout):
            calls.append(body)
            v={'model':m.MODEL,'done':True,'done_reason':'stop','message':{'content':raw},'prompt_eval_count':512,'eval_count':120}
            return v,json.dumps(v).encode()
        r=m.experiment(seed,d,lambda *a:None,request,lambda:True)
        self.assertTrue(m.validate(r,d));self.assertEqual(len(calls),3)
        report=m.aggregate(r);self.assertEqual(report['verified_completions'],3)
        self.assertEqual(report['scores']['guided']['certificate_correct'],2)
        self.assertEqual(report['reported_completion_tokens'],360)
        key=b'synthetic-test-key-only';signed={**r,'hmac_sha256':ev.sign(r,key)}
        self.assertTrue(m.verify(signed,key,d))
        with self.assertRaises(ValueError):m.verify({**signed,'status':'failed'},key,d)
        self.assertFalse(r['origin_authenticated'])
    def test_resource_block_does_not_count_model_calls(self):
        def unexpected(*a):self.fail('unexpected model request')
        r=m.experiment(5,'a'*64,unexpected,unexpected,lambda:False)
        self.assertTrue(m.validate(r,'a'*64))
        self.assertEqual(m.aggregate(r)['request_attempts'],0)
        self.assertEqual(m.aggregate(r)['verified_completions'],0)
if __name__=='__main__':unittest.main()
