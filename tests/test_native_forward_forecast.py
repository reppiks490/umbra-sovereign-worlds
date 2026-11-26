import pathlib,sys,tempfile,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import native_forward_qualification as q

class ForecastRouteTests(unittest.TestCase):
 def row(self):return {'task':'time-series-forecasting','files':[{'name':n} for n in ('config.json','model.safetensors')]}
 def config(self,kind,arch):return {'model_type':kind,'architectures':[arch],'context_length':16,'prediction_length':4,'num_input_channels':2,'loss':'mse'}
 def test_pinned_builtin_forecasters(self):
  self.assertEqual(q.route(self.row(),self.config('patchtst','PatchTSTForPrediction')),'forecast')
  self.assertEqual(q.route(self.row(),self.config('patchtsmixer','PatchTSMixerForPrediction')),'forecast')
 def test_no_forecasting_alias_or_remote_code(self):
  self.assertIsNone(q.route(self.row(),self.config('t5','ChronosBoltModelForForecasting')))
  self.assertIsNone(q.route(self.row(),self.config('patchtst','PatchTSTForPretraining')))
  self.assertIsNone(q.route(self.row(),{**self.config('patchtst','PatchTSTForPrediction'),'auto_map':{'AutoModel':'remote.Code'}}))
 def test_forecast_budget_rejects_unbounded_input_and_probabilistic_head(self):
  c=self.config('patchtst','PatchTSTForPrediction')
  for change in ({'context_length':8192},{'prediction_length':1024},{'num_input_channels':128},{'loss':'nll'}):
   self.assertIsNone(q.route(self.row(),{**c,**change}))

class ForecastForwardTests(unittest.TestCase):
 def check(self,model,folder):
  model.save_pretrained(folder,safe_serialization=True)
  receipt={'task':'time-series-forecasting','files':[{'name':x.name} for x in folder.iterdir() if x.is_file()]}
  self.assertEqual(q.route(receipt,q.read_json(folder/'config.json')),'forecast')
  r=q.forward(folder,receipt,'forecast')
  self.assertEqual(r['shape'],[1,4,2])
  self.assertEqual(r['elements'],8)
 def test_patchtst_real_forward(self):
  import torch
  from transformers import PatchTSTConfig,PatchTSTForPrediction
  with tempfile.TemporaryDirectory() as d:
   torch.manual_seed(17)
   self.check(PatchTSTForPrediction(PatchTSTConfig(context_length=16,prediction_length=4,num_input_channels=2,patch_length=4,patch_stride=4,d_model=8,num_attention_heads=2,num_hidden_layers=1,ffn_dim=16,loss='mse')),pathlib.Path(d))
 def test_patchtsmixer_real_forward(self):
  import torch
  from transformers import PatchTSMixerConfig,PatchTSMixerForPrediction
  with tempfile.TemporaryDirectory() as d:
   torch.manual_seed(17)
   self.check(PatchTSMixerForPrediction(PatchTSMixerConfig(context_length=16,prediction_length=4,num_input_channels=2,patch_length=4,patch_stride=4,d_model=8,num_layers=1,expansion_factor=2,loss='mse')),pathlib.Path(d))
