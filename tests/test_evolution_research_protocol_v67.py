import unittest,json
import evolution_research_protocol_v67 as m
import evolution_research_v37 as r
class Tests(unittest.TestCase):
 def test_explicit_labels_and_no_answer_leak(self):
  cases=[r.task(i,991) for i in range(1,5)]
  p=m.prompt(cases,'explicit')
  self.assertNotIn('"expected"',p);self.assertNotIn('"evidence_id"',p)
  for c in cases:
   for k,v in c['evidence'].items():self.assertIn(k+': '+v,p)
   for k,v in c['choices'].items():self.assertIn(k+': '+v,p)
 def test_strict_identity_and_score(self):
  cases=[r.task(i,991) for i in range(1,5)]
  raw=json.dumps([{'n':i+1,'action':c['expected'],'fact':c['evidence_id']} for i,c in enumerate(cases)])
  self.assertEqual(m.score(cases,raw,'explicit')['joint_correct'],4)
  with self.assertRaises(ValueError):m.score(cases,raw.replace('"n": 2','"n": 1'),'explicit')
 def test_pair_requires_identical_cases(self):
  a={'case_sha256':'x','protocol':'compact','joint_correct':1,'total':4,'seconds':2}
  b={**a,'protocol':'explicit','joint_correct':3}
  self.assertEqual(m.compare(a,b)['joint_delta'],2)
  with self.assertRaises(ValueError):m.compare(a,{**b,'case_sha256':'y'})
  self.assertFalse(m.compare(a,b)['routing_authorized'])
if __name__=='__main__':unittest.main()
