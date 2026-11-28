import sys,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from lesson_retrieval import LessonIndex, template_similarity
from human_corpus import validate
def row(q,a='3'):
 return validate({'question':q,'answer':'Human solution\n#### '+a})
class RetrievalTest(unittest.TestCase):
 def test_relevant_source_and_template_exclusion(self):
  near=row('Maria buys 4 boxes containing 7 pencils each. How many pencils does she buy?')
  relevant=row('A shop sells pencils in bundles. Calculate the total number of pencils from the number of bundles.')
  unrelated=row('The train travels at a constant speed for five hours.')
  v=row('Maria buys 3 boxes containing 8 pencils each. How many pencils does she buy?','24')
  index=LessonIndex([near,relevant,unrelated])
  found=index.select(v['question'],v['question_sha256'])
  self.assertEqual(found['record']['record_sha256'],relevant['record_sha256'])
  self.assertGreaterEqual(template_similarity(near['question'],v['question']),.65)
 def test_no_label_access_and_determinism(self):
  a=row('How many apples remain after selling some fruit?')
  b=row('How many oranges remain after selling some fruit?')
  v=row('Calculate remaining fruit after a sale.')
  self.assertEqual(LessonIndex([a,b]).select(v['question'],v['question_sha256']),LessonIndex([b,a]).select(v['question'],v['question_sha256']))
 def test_reject_duplicate_source_and_no_safe_match(self):
  a=row('A person owns 2 books and buys 3 more books.')
  with self.assertRaises(ValueError): LessonIndex([a,a])
  self.assertIsNone(LessonIndex([a]).select(a['question'],a['question_sha256']))
 def test_reject_identity_mismatch(self):
  a=row('A person owns 2 books and buys 3 more books.')
  with self.assertRaises(ValueError):LessonIndex([a]).select(a['question'],'0'*64)
if __name__=='__main__':unittest.main()
