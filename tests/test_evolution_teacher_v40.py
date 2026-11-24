import unittest,tempfile,json
from pathlib import Path
import evolution_teacher_v40 as m
class TeacherTests(unittest.TestCase):
 def test_memory_gate(self):
  self.assertFalse(m.admit_teacher(2500,10000,False))
  self.assertFalse(m.admit_teacher(7000,10000,True))
  self.assertTrue(m.admit_teacher(7000,10000,False))
 def test_bad_teacher_answers_not_admitted(self):
  t=m.cases(42,0)
  raw=json.dumps([{"id":c["id"],"label":c["label"]} for c in t])
  self.assertEqual(len(m.accept(t,raw)),len(t))
  r=json.loads(raw);r[0]["label"]=1-r[0]["label"]
  self.assertEqual(len(m.accept(t,json.dumps(r))),len(t)-1)
  with self.assertRaises(ValueError):m.accept(t,json.dumps(r+[r[0]]))
 def test_disjoint_cases_and_deterministic(self):
  a=m.cases(42,0);b=m.cases(42,1)
  self.assertEqual(a,m.cases(42,0))
  self.assertFalse(set(x['id'] for x in a)&set(x['id'] for x in b))
 def test_similarity(self):
  self.assertAlmostEqual(m.cosine([1,0],[1,0]),1)
  self.assertAlmostEqual(m.cosine([1,0],[0,1]),0)
  with self.assertRaises(ValueError):m.cosine([0,0],[1,0])
 def test_source_bounds(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);(p/'evolution_model_queue_v26.py').write_text('def claim():\n    return 1\n')
   docs=m.documents(p);self.assertEqual(len(docs),1);self.assertEqual(docs[0]['function'],'claim')
   self.assertIn('return 1',docs[0]['text'])
if __name__=='__main__':unittest.main()
