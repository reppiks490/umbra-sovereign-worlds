import unittest,json
import evolution_model_tournament_v62 as m
class Tests(unittest.TestCase):
 def test_identical_cases_and_answer_order(self):
  a=m.cases(123,0);b=m.cases(123,1)
  self.assertEqual(len(a),8);self.assertEqual(len(b),8)
  self.assertEqual(len({x['specialty'] for x in a+b}),16)
  self.assertEqual(a,m.cases(123,0))
  raw=json.dumps([x['expected']+x['evidence_id'][1] for x in a])
  self.assertEqual(m.grade(a,raw)['joint_correct'],8)
  with self.assertRaises(ValueError):m.grade(a,'["A1"]')
 def test_paired_comparison_requires_same_cohort(self):
  x={'model':'a','cohort':1,'partition':0,'case_sha256':'a','joint_correct':2,'total':8,'seconds':2}
  y={**x,'model':'b','joint_correct':4,'seconds':3}
  self.assertEqual(m.compare([x,y])['partitions'][0]['leader'],'b')
  with self.assertRaises(ValueError):m.compare([x,{**y,'case_sha256':'b'}])
  self.assertFalse(m.compare([x,y])['routing_authorized'])
 def test_rotation_never_starves_failed_model(self):
  self.assertEqual(m.choose(['a','b','c'],{('a',0),('a',1)},{('b',0):1}),('b',1))
  self.assertEqual(m.choose(['a'],{('a',0),('a',1)},{}),None)
if __name__=='__main__':unittest.main()
