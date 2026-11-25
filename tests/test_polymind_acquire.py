import unittest
from scripts.polymind_acquire import select_bundle, admissible, count_unique, reserve_bytes
H='a'*64
def file(name,size,sha=None):
 return {'rfilename':name,'size':size,**({'lfs':{'sha256':sha,'size':size}} if sha else {})}
def meta(files,license='apache-2.0',task='feature-extraction'):
 return {'id':'Xenova/example','sha':'b'*40,'cardData':{'license':license},'pipeline_tag':task,'siblings':files}
class TestPolyMind(unittest.TestCase):
 def test_selects_one_small_pinned_quantized_bundle(self):
  r=select_bundle(meta([file('onnx/model.onnx',90000000,H),file('onnx/model_int8.onnx',20000000,'c'*64),file('tokenizer.json',1000),file('config.json',100)]))
  self.assertEqual(r['weight'],'onnx/model_int8.onnx')
  self.assertEqual(r['revision'],'b'*40)
 def test_rejects_unlicensed_unpinned_external_and_missing_tokenizer(self):
  files=[file('onnx/model_int8.onnx',2000,H),file('tokenizer.json',100)]
  self.assertIsNone(select_bundle(meta(files,'unknown')))
  self.assertIsNone(select_bundle(meta(files+[file('onnx/model_int8.onnx_data',5000,H)])))
  self.assertIsNone(select_bundle(meta(files[:1])))
  m=meta(files);m['sha']='main';self.assertIsNone(select_bundle(m))
 def test_disk_guard(self):
  self.assertFalse(admissible(4*1024**3,1024**3))
  self.assertTrue(admissible(5*1024**3,1024**3))
 def test_explicit_owner_reserve(self):
  r=reserve_bytes(1024,756)
  self.assertEqual(r,1780*1024**2)
  self.assertTrue(admissible(r+100,100,r))
  self.assertFalse(admissible(r+99,100,r))
  for x,y in [(0,756),(1024,-1),(True,756)]:
   with self.assertRaises(ValueError): reserve_bytes(x,y)
 def test_dedup(self):
  self.assertEqual(count_unique([H,H,'b'*64]),2)
if __name__=='__main__': unittest.main()
