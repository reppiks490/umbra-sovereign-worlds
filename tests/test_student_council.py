import pathlib,sys,unittest,tempfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from student_council import OLLAMA,NATIVE,choose_student,answer_value,grade_answer,load_corpus
class CouncilTest(unittest.TestCase):
 def test_all_named_models_are_registered(self):
  self.assertEqual(len(OLLAMA),12)
  self.assertIn('qwen3:8b',OLLAMA)
  self.assertIn('hf.co/bartowski/Qwen_Qwen3-8B-GGUF:IQ2_M',OLLAMA)
  self.assertIn('HuggingFaceTB/SmolLM2-360M-Instruct',NATIVE)
  self.assertIn('Qwen/Qwen2.5-Coder-1.5B-Instruct',NATIVE)
 def test_fair_admission(self):
  a=[{'name':'a','required_ram':2,'present':True},{'name':'b','required_ram':4,'present':True},{'name':'c','required_ram':2,'present':False}]
  self.assertEqual(choose_student(a,{'a':{'last_attempt':100}},5)['name'],'b')
  self.assertEqual(choose_student(a,{'a':{'last_attempt':100}},3)['name'],'a')
  self.assertIsNone(choose_student(a,{},1))
 def test_numeric_verifier(self):
  self.assertEqual(answer_value('work\n#### 1,250'),'1250')
  self.assertEqual(answer_value('#### -4.50'),'-4.5')
  self.assertTrue(grade_answer('#### 5.00','x\n#### 5'))
  self.assertFalse(grade_answer('Maybe 5','#### 5'))
  self.assertFalse(grade_answer('#### 5\n#### 6','#### 5'))
 def test_missing_corpus_fails_closed(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises((ValueError,FileNotFoundError)):load_corpus(pathlib.Path(d))

 def test_icarus_priority_for_each_student(self):
  from student_council import QUERIES
  self.assertTrue(QUERIES[0].startswith('ICARUS'))
  self.assertTrue(any('quantitative investment' in x for x in QUERIES))
  self.assertGreaterEqual(len(set(QUERIES)),7)
