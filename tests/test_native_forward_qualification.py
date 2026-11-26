import sys,pathlib,unittest,tempfile,json
from unittest.mock import patch
from contextlib import nullcontext
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import native_forward_qualification as q

class QualificationTest(unittest.TestCase):
 def row(self):
  return {'repo':'test/encoder','revision':'a'*40,'digest':'b'*64,'total':1000,'native_verified':True,'task':'feature-extraction','files':[{'name':'config.json'},{'name':'tokenizer.json'},{'name':'model.safetensors'}]}
 def test_explicit_architecture_and_task_routing(self):
  r=self.row()
  self.assertEqual(q.route(r,{'model_type':'bert'}),'encoder')
  self.assertEqual(q.route({**r,'task':'text-generation'},{'model_type':'qwen2'}),'causal')
  self.assertEqual(q.route({**r,'task':'text-classification'},{'model_type':'roberta'}),'classification')
  self.assertEqual(q.route({**r,'task':'image-classification'},{'model_type':'vit'}),'vision')
  self.assertIsNone(q.route(r,{'model_type':'bert','auto_map':{'AutoModel':'remote.Code'}}))
  self.assertIsNone(q.route({**r,'task':'image-classification'},{'architecture':'resnet18'}))
 def test_catalog_does_not_claim_inference_or_deduplicate_revisions(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp)
   for rev in ('a'*40,'c'*40):
    p=root/'tiny'/('test--encoder--'+rev[:12]);p.mkdir(parents=True)
    (p/'receipt.json').write_text(json.dumps({**self.row(),'revision':rev}))
    (p/'config.json').write_text('{"model_type":"bert"}')
   rows=q.catalog(root)
   self.assertEqual(len(rows),2)
   self.assertTrue(all(r['status']=='candidate' and not r['inference_verified'] for r in rows))
 def test_bootstrap_lock_prevents_any_backend_execution(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp);training=root/'training';training.mkdir()
   (training/'bootstrap.lock').write_text('busy')
   result=q.execute(root,training,'test/encoder','a'*40)
   self.assertEqual(result['status'],'deferred_busy')
   self.assertFalse(result['inference_verified'])
 def test_output_validation_rejects_nonfinite_or_empty_or_constant(self):
  for values in ([],[1.,float('nan')],[2.,2.],[float('inf'),1.]):
   with self.assertRaises(ValueError):q.output_evidence(values,[len(values)])
  r=q.output_evidence([1.,2.,3.,4.],[2,2])
  self.assertEqual(r['elements'],4)
  self.assertEqual(len(r['output_sha256']),64)
 def test_receipt_mismatch_cannot_reach_backend(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp);training=root/'training';training.mkdir();(root/'experience').mkdir()
   p=root/'tiny'/'test--encoder--aaaaaaaaaaaa';p.mkdir(parents=True)
   row={**self.row(),'folder':str(p.relative_to(root)),'route':'encoder','status':'candidate'}
   with patch.object(q,'catalog',return_value=[row]),patch.object(q,'available_ram',return_value=10**10),patch.object(q,'local_api',return_value={'models':[]}),patch.object(q,'lock',side_effect=lambda p:nullcontext()),patch.object(q,'read_receipt',return_value={**self.row(),'digest':'c'*64}),patch.object(q,'forward',side_effect=AssertionError('wrong identity')):
    r=q.execute(root,training,'test/encoder','a'*40)
   self.assertEqual(r['status'],'failed')
   self.assertFalse(r['inference_verified'])
 def test_successful_forward_still_not_research_or_training_qualified(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp);training=root/'training';training.mkdir();(root/'experience').mkdir()
   p=root/'tiny'/'test--encoder--aaaaaaaaaaaa';p.mkdir(parents=True)
   row={**self.row(),'folder':str(p.relative_to(root)),'route':'encoder','status':'candidate'}
   with patch.object(q,'catalog',return_value=[row]),patch.object(q,'available_ram',return_value=10**10),patch.object(q,'local_api',return_value={'models':[]}),patch.object(q,'lock',side_effect=lambda p:nullcontext()),patch.object(q,'read_receipt',return_value=self.row()),patch.object(q,'forward',return_value={'shape':[1,2],'elements':2,'output_sha256':'d'*64}):
    r=q.execute(root,training,'test/encoder','a'*40)
   self.assertTrue(r['inference_verified'])
   self.assertFalse(r['research_qualified'])
   self.assertFalse(r['weight_training'])
   self.assertFalse(r['production_authority'])

class OfflineLoaderIntegration(unittest.TestCase):
 def test_real_tiny_bert_forward_without_network(self):
  import torch
  from transformers import BertConfig,BertModel,PreTrainedTokenizerFast
  from tokenizers import Tokenizer
  from tokenizers.models import WordLevel
  from tokenizers.pre_tokenizers import Whitespace
  with tempfile.TemporaryDirectory() as tmp:
   folder=pathlib.Path(tmp)
   tok=Tokenizer(WordLevel({'[UNK]':0,'[PAD]':1,'Chronological':2,'validation':3,'separates':4,'observations':5,'from':6,'future':7,'evidence':8,'.':9},unk_token='[UNK]'))
   tok.pre_tokenizer=Whitespace()
   PreTrainedTokenizerFast(tokenizer_object=tok,unk_token='[UNK]',pad_token='[PAD]',model_input_names=['input_ids','attention_mask']).save_pretrained(folder)
   torch.manual_seed(17)
   BertModel(BertConfig(vocab_size=10,hidden_size=8,num_hidden_layers=1,num_attention_heads=2,intermediate_size=16,max_position_embeddings=64)).save_pretrained(folder,safe_serialization=True)
   receipt={'task':'feature-extraction','files':[{'name':p.name} for p in folder.iterdir() if p.is_file()]}
   r=q.forward(folder,receipt,'encoder')
   self.assertEqual(r['shape'],[1,8])
   self.assertEqual(r['elements'],8)
