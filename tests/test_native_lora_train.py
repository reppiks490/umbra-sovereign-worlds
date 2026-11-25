import unittest,sys,pathlib,hashlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from native_lora_train import validate_corpus, promotion_gate, required_memory
def row(i):
 p='probe '+str(i)
 return {'prompt':p,'answer':'A','options':['A','B','C','D'],'domain':'arithmetic','seed':i+1,'prompt_sha256':hashlib.sha256(p.encode()).hexdigest(),'source':'symbolic_verified'}
class Test(unittest.TestCase):
 def test_separated_prompts_and_schema(self):
  x={'schema':'umbra.swarm.corpus.v1','model':'qwen3:0.6b','training':[row(i) for i in range(32)],'retention':[row(i) for i in range(32,48)],'transfer':[row(i) for i in range(48,64)]}
  self.assertEqual(len(validate_corpus(x,'qwen3:0.6b')['training']),32)
  x['transfer'][0]=x['training'][0];self.assertRaises(ValueError,validate_corpus,x,'qwen3:0.6b')
 def test_gate_preserves_retention_and_requires_improvement(self):
  self.assertFalse(promotion_gate({'retention':1,'transfer':2},{'retention':1.2,'transfer':1}))
  self.assertFalse(promotion_gate({'retention':1,'transfer':2},{'retention':1,'transfer':2}))
  self.assertTrue(promotion_gate({'retention':1,'transfer':2},{'retention':1.01,'transfer':1.8}))
  self.assertGreater(required_memory('qwen3:0.6b'),required_memory('granite4:350m'))
if __name__=='__main__':unittest.main()
