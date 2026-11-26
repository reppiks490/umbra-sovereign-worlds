import pathlib,sys,tempfile,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import native_forward_qualification as q

def receipt(folder,task):
 return {'task':task,'files':[{'name':p.name} for p in folder.iterdir() if p.is_file()]}

class ExtendedRouteTest(unittest.TestCase):
 def row(self,task):
  return {'task':task,'files':[{'name':x} for x in ('config.json','model.safetensors','tokenizer.json')]}
 def test_t5_generation_not_forecasting(self):
  self.assertEqual(q.route(self.row(None),{'model_type':'t5','architectures':['T5ForConditionalGeneration']}),'seq2seq')
  self.assertIsNone(q.route(self.row('time-series-forecasting'),{'model_type':'t5','architectures':['T5ForConditionalGeneration']}))
 def test_bart_classification_and_generation(self):
  self.assertEqual(q.route(self.row('zero-shot-classification'),{'model_type':'bart'}),'classification')
  self.assertEqual(q.route(self.row('summarization'),{'model_type':'bart'}),'seq2seq')
 def test_image_features_and_audio_are_explicit(self):
  self.assertEqual(q.route(self.row('image-feature-extraction'),{'model_type':'dinov2'}),'vision_features')
  self.assertEqual(q.route(self.row('automatic-speech-recognition'),{'model_type':'whisper'}),'whisper')
  self.assertEqual(q.route(self.row('automatic-speech-recognition'),{'model_type':'wav2vec2'}),'ctc')
  self.assertIsNone(q.route(self.row('automatic-speech-recognition'),{'model_type':'bert'}))

class RealOfflineIntegration(unittest.TestCase):
 def test_seq2seq_real_forward(self):
  from transformers import T5Config,T5ForConditionalGeneration
  import torch
  with tempfile.TemporaryDirectory() as tmp:
   folder=pathlib.Path(tmp)
   self.tokenizer(folder)
   torch.manual_seed(17)
   T5ForConditionalGeneration(T5Config(vocab_size=16,d_model=8,d_kv=4,d_ff=16,num_layers=1,num_decoder_layers=1,num_heads=2,decoder_start_token_id=1,pad_token_id=1,eos_token_id=2)).save_pretrained(folder,safe_serialization=True)
   self.assertEqual(q.forward(folder,receipt(folder,'text2text-generation'),'seq2seq')['shape'],[1,16])
 def tokenizer(self,folder):
  from transformers import PreTrainedTokenizerFast
  from tokenizers import Tokenizer
  from tokenizers.models import WordLevel
  from tokenizers.pre_tokenizers import Whitespace
  t=Tokenizer(WordLevel({'[UNK]':0,'[PAD]':1,'[EOS]':2,'Chronological':3,'validation':4,'separates':5,'observations':6,'from':7,'future':8,'evidence':9,'.':10},unk_token='[UNK]'));t.pre_tokenizer=Whitespace()
  PreTrainedTokenizerFast(tokenizer_object=t,unk_token='[UNK]',pad_token='[PAD]',eos_token='[EOS]',model_input_names=['input_ids','attention_mask']).save_pretrained(folder)
 def test_vision_features_real_forward(self):
  from transformers import ViTConfig,ViTModel
  import torch
  with tempfile.TemporaryDirectory() as tmp:
   folder=pathlib.Path(tmp);torch.manual_seed(17)
   ViTModel(ViTConfig(image_size=32,patch_size=8,hidden_size=8,num_hidden_layers=1,num_attention_heads=2,intermediate_size=16)).save_pretrained(folder,safe_serialization=True)
   self.assertEqual(q.forward(folder,receipt(folder,'image-feature-extraction'),'vision_features')['shape'],[1,8])
 def test_whisper_real_forward(self):
  from transformers import WhisperConfig,WhisperForConditionalGeneration
  import torch
  with tempfile.TemporaryDirectory() as tmp:
   folder=pathlib.Path(tmp);torch.manual_seed(17)
   WhisperForConditionalGeneration(WhisperConfig(vocab_size=16,num_mel_bins=8,d_model=8,encoder_layers=1,decoder_layers=1,encoder_attention_heads=2,decoder_attention_heads=2,encoder_ffn_dim=16,decoder_ffn_dim=16,max_source_positions=16,max_target_positions=16,pad_token_id=1,bos_token_id=2,eos_token_id=3,decoder_start_token_id=2)).save_pretrained(folder,safe_serialization=True)
   self.assertEqual(q.forward(folder,receipt(folder,'automatic-speech-recognition'),'whisper')['shape'],[1,16])
 def test_ctc_real_forward(self):
  from transformers import Wav2Vec2Config,Wav2Vec2ForCTC
  import torch
  with tempfile.TemporaryDirectory() as tmp:
   folder=pathlib.Path(tmp);torch.manual_seed(17)
   Wav2Vec2ForCTC(Wav2Vec2Config(vocab_size=16,hidden_size=8,num_hidden_layers=1,num_attention_heads=2,intermediate_size=16,conv_dim=(8,8,8),conv_stride=(4,4,4),conv_kernel=(8,4,4),num_conv_pos_embeddings=8,num_conv_pos_embedding_groups=2,mask_time_prob=0.)).save_pretrained(folder,safe_serialization=True)
   self.assertEqual(q.forward(folder,receipt(folder,'automatic-speech-recognition'),'ctc')['shape'],[1,16])
