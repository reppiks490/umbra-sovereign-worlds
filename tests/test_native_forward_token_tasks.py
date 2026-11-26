import pathlib,sys,tempfile,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import native_forward_qualification as q
def receipt(folder,task):
 return {'task':task,'files':[{'name':p.name} for p in folder.iterdir() if p.is_file()]}
class Routes(unittest.TestCase):
 def row(self,task,tokenizer):
  return {'task':task,'files':[{'name':x} for x in ('config.json','model.safetensors',tokenizer)]}
 def test_masked_language_model(self):
  self.assertEqual(q.route(self.row('fill-mask','tokenizer.json'),{'model_type':'bert'}),'masked')
 def test_bert_vocab_only_token_classifier(self):
  self.assertEqual(q.route(self.row('token-classification','vocab.txt'),{'model_type':'bert'}),'token_classification')
 def test_vocab_only_not_generic_causal_tokenizer(self):
  self.assertIsNone(q.route(self.row('text-generation','vocab.txt'),{'model_type':'qwen2'}))
class RealOffline(unittest.TestCase):
 def prepare(self,folder):
  from transformers import BertTokenizer
  vocab=['[PAD]','[UNK]','[CLS]','[SEP]','[MASK]','chronological','validation','separates','observations','from','future','evidence','.']
  (folder/'vocab.txt').write_text('\n'.join(vocab)+'\n',encoding='utf8')
  BertTokenizer(vocab_file=str(folder/'vocab.txt'),do_lower_case=True).save_pretrained(folder)
  self.assertFalse((folder/'tokenizer.json').exists())
  return len(vocab)
 def test_masked_bert_forward(self):
  import torch
  from transformers import BertConfig,BertForMaskedLM
  with tempfile.TemporaryDirectory() as tmp:
   folder=pathlib.Path(tmp);n=self.prepare(folder);torch.manual_seed(17)
   BertForMaskedLM(BertConfig(vocab_size=n,hidden_size=8,num_hidden_layers=1,num_attention_heads=2,intermediate_size=16,max_position_embeddings=64)).save_pretrained(folder,safe_serialization=True)
   r=q.forward(folder,receipt(folder,'fill-mask'),'masked')
   self.assertEqual(r['shape'],[1,n])
 def test_token_classifier_forward(self):
  import torch
  from transformers import BertConfig,BertForTokenClassification
  with tempfile.TemporaryDirectory() as tmp:
   folder=pathlib.Path(tmp);n=self.prepare(folder);torch.manual_seed(17)
   BertForTokenClassification(BertConfig(vocab_size=n,hidden_size=8,num_hidden_layers=1,num_attention_heads=2,intermediate_size=16,max_position_embeddings=64,num_labels=3)).save_pretrained(folder,safe_serialization=True)
   r=q.forward(folder,receipt(folder,'token-classification'),'token_classification')
   self.assertEqual(r['shape'][-1],3)
   self.assertGreater(r['shape'][1],1)
