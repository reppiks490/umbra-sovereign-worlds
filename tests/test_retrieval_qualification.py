import sys,pathlib,unittest,math
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from retrieval_qualification import rank_metrics,compare_vectors,rank_fusion
class QualificationTest(unittest.TestCase):
 def test_rank_metrics(self):
  self.assertEqual(rank_metrics(['a','b','c'],{'b'}),{'reciprocal_rank':.5,'hit_at_1':False,'hit_at_3':True})
  self.assertEqual(rank_metrics(['a','b'],{'c'})['reciprocal_rank'],0)
  with self.assertRaises(ValueError):rank_metrics(['a','a'],{'a'})
 def test_parity_not_just_shape(self):
  self.assertTrue(compare_vectors([1.,0.],[1.,0.])['passed'])
  self.assertFalse(compare_vectors([1.,0.],[0.,1.])['passed'])
  with self.assertRaises(ValueError):compare_vectors([math.nan],[1.])
 def test_rank_fusion_is_scale_independent(self):
  self.assertEqual(rank_fusion({'a':[.99,.98,.01],'b':[0.,10.,1.]}),[1,0,2])
  with self.assertRaises(ValueError):rank_fusion({'a':[1,2],'b':[1]})

 def test_serialized_fixed_padding_removed_before_native_forward(self):
  from tokenizers import Tokenizer
  from tokenizers.models import WordLevel
  from tokenizers.pre_tokenizers import Whitespace
  from agentic_native import configure_tokenizer
  t=Tokenizer(WordLevel({'[UNK]':0,'[PAD]':1,'real':2,'research':3},unk_token='[UNK]'))
  t.pre_tokenizer=Whitespace();t.enable_padding(length=128,pad_id=1,pad_token='[PAD]')
  self.assertEqual(len(t.encode('real research').ids),128)
  configure_tokenizer(t,96)
  self.assertEqual(t.encode('real research').ids,[2,3])
