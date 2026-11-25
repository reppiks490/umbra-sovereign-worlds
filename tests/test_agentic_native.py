import unittest,tempfile,pathlib,struct,json,hashlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from agentic_native import inventory,SafeWeights,bert_forward
import numpy as np
def make_weights(p,arrays):
 h={};data=b''
 for name,v in arrays.items():
  v=np.asarray(v,dtype='<f4');raw=v.tobytes();h[name]={'dtype':'F32','shape':list(v.shape),'data_offsets':[len(data),len(data)+len(raw)]};data+=raw
 header=json.dumps(h).encode();p.write_bytes(struct.pack('<Q',len(header))+header+data)
class Test(unittest.TestCase):
 def test_catalog_checksums_and_non_executable_receipts(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);p=root/'tiny'/'sample';p.mkdir(parents=True);w=p/'model.safetensors';make_weights(w,{'x':np.ones((2,2))});h=hashlib.sha256(w.read_bytes()).hexdigest()
   r={'repo':'example/model','revision':'a'*40,'license':'apache-2.0','task':'feature-extraction','digest':h,'native_verified':True,'files':[{'name':'model.safetensors','size':w.stat().st_size,'sha':h}],'total':w.stat().st_size}
   (p/'receipt.json').write_text(json.dumps(r));self.assertEqual(inventory(root)[0]['digest'],h);w.write_bytes(w.read_bytes()[:-1]+b'X');self.assertEqual(inventory(root),[])
 def test_safe_weights_and_pooling(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'x.safetensors';make_weights(p,{'x':[[1,2],[3,4]]})
   with SafeWeights(p) as w: self.assertTrue(np.array_equal(w.get('x'),[[1,2],[3,4]]))
   with self.assertRaises(ValueError):
    with SafeWeights(p) as w:w.get('absent')
 def test_actual_tiny_bert_forward(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'x.safetensors';z=np.zeros((2,2));o=np.ones(2);b=np.zeros(2)
   a={'embeddings.word_embeddings.weight':[[1,0],[0,1]],'embeddings.position_embeddings.weight':z,'embeddings.token_type_embeddings.weight':z,'embeddings.LayerNorm.weight':o,'embeddings.LayerNorm.bias':b}
   for n in ('attention.self.query','attention.self.key','attention.self.value','attention.output.dense','intermediate.dense','output.dense'):
    a['encoder.layer.0.'+n+'.weight']=z;a['encoder.layer.0.'+n+'.bias']=b
   for n in ('attention.output.LayerNorm','output.LayerNorm'):
    a['encoder.layer.0.'+n+'.weight']=o;a['encoder.layer.0.'+n+'.bias']=b
   make_weights(p,a)
   with SafeWeights(p) as w:
    v=bert_forward(w,{'hidden_size':2,'num_hidden_layers':1,'num_attention_heads':1,'intermediate_size':2,'layer_norm_eps':1e-12},[0],'mean')
    self.assertAlmostEqual(float(np.linalg.norm(v)),1,places=5);self.assertGreater(v[0],0);self.assertLess(v[1],0)
if __name__=='__main__':unittest.main()
