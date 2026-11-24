import json,unittest
import evolution_proof_feedback_v90 as m

class Tests(unittest.TestCase):
    def correct(self,seed):
        return json.dumps([{'id':i,'certificate':m.proof.solve(q)} for i,q in enumerate(m.cases(seed))])
    def wrong(self,seed):
        rows=json.loads(self.correct(seed))
        for r in rows:r['certificate']['answer']+=1
        return json.dumps(rows)
    def test_matched_retry_with_feedback(self):
        seed=2;prompts=[]
        def ask(prompt):
            prompts.append(prompt)
            return self.correct(seed) if 'VERIFIER FEEDBACK:' in prompt else self.wrong(seed)
        r=m.experiment(seed,ask)
        self.assertEqual(len(prompts),3)
        self.assertEqual(r['summary']['initial']['certificate_correct'],0)
        self.assertEqual(r['summary']['control']['certificate_correct'],0)
        self.assertEqual(r['summary']['guided']['certificate_correct'],2)
        self.assertTrue(m.verify(r))
        self.assertNotIn('reference_answer',prompts[-1])
        self.assertFalse(r['semantic_mastery_certified'])
        self.assertFalse(r['production_authority'])
    def test_counterbalance_and_malformed_output(self):
        for seed in [2,3]:
            r=m.experiment(seed,lambda p:'not json')
            self.assertEqual(r['order'],['initial','control','guided'] if seed%2==0 else ['initial','guided','control'])
            self.assertEqual(r['summary']['guided']['certificate_correct'],0)
            self.assertEqual(r['summary']['guided']['parsed'],False)
            self.assertTrue(m.verify(r))
    def test_receipt_replay_even_after_rehash(self):
        r=m.experiment(4,lambda p:self.correct(4))
        r['summary']['guided']['certificate_correct']=0
        r['receipt_sha256']=m.digest({k:v for k,v in r.items() if k!='receipt_sha256'})
        self.assertFalse(m.verify(r))
    def test_failed_requests_retained(self):
        def ask(p):raise TimeoutError('not public')
        r=m.experiment(5,ask)
        self.assertEqual(len(r['calls']),3)
        self.assertTrue(all(x['status']=='failed' and x['error_class']=='TimeoutError' for x in r['calls']))
        self.assertNotIn('not public',str(r))
        self.assertTrue(m.verify(r))
    def test_invalid_seed_and_duplicate_ids(self):
        with self.assertRaises(ValueError):m.cases(True)
        rows=json.loads(self.correct(2));rows[1]['id']=rows[0]['id']
        s=m.score(m.cases(2),json.dumps(rows))
        self.assertFalse(s['parsed'])
    def test_feedback_does_not_emit_solution(self):
        q=m.cases(2);r=m.feedback(q,self.wrong(2))
        self.assertTrue(all(set(x)=={'id','diagnostic'} for x in r))
        self.assertTrue(all(x['diagnostic']!='valid_certificate' for x in r))
if __name__=='__main__':unittest.main()
