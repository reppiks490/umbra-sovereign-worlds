import unittest,json
import evolution_compact_teacher_v45 as m
import evolution_teacher_v40 as t
class Tests(unittest.TestCase):
 def test_compact_labels_bind_to_exact_case_order(self):
  cases=t.cases(10,0);raw=json.dumps([c['label'] for c in cases])
  canon=m.decode(cases,raw)
  self.assertEqual(len(t.accept(cases,canon)),12)
  with self.assertRaises(ValueError):m.decode(cases,'[1]')
  with self.assertRaises(ValueError):m.decode(cases,json.dumps([True]*12))
 def test_prompt_does_not_include_answer_key(self):
  cases=t.cases(3,0);p=m.prompt(cases)
  self.assertIn('facts',p)
  self.assertNotIn('"label":',p)
  self.assertNotIn('"features":',p)
 def test_rotation_not_starved_by_model_failure(self):
  self.assertEqual(m.choose(['a','b','c'],{'a':1,'b':1,'c':0},1),'c')
  self.assertEqual(m.choose(['a','b','c'],{'a':2,'b':1,'c':2},1),'b')
  self.assertIsNone(m.choose([],{},0))
if __name__=='__main__':unittest.main()
