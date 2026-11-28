import pathlib,sys,unittest,math
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from native_student import promotion,TRAINABLE
class NativeStudentTest(unittest.TestCase):
 def test_validation_gate(self):
  self.assertTrue(promotion([1.]*8,[.98]*8))
  self.assertFalse(promotion([1.]*8,[.995]*8))
  self.assertFalse(promotion([1.]*8,[.5]*7+[1.2]))
  self.assertFalse(promotion([1.]*8,[math.nan]*8))
  self.assertFalse(promotion([1.]*7,[.5]*7))
 def test_source_checkpoints(self):
  self.assertIn('granite4:350m',TRAINABLE)
  self.assertIn('qwen3:0.6b',TRAINABLE)
  self.assertIn('HuggingFaceTB/SmolLM2-360M-Instruct',TRAINABLE)
