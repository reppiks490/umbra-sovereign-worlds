import unittest,tempfile,pathlib,hashlib,json,struct,io,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from hf_weight_cache import Cache,MIN_FREE
class Test(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name);self.repo='test/model';self.rev='a'*40
  self.folder=self.root/'tiny'/('test--model--'+self.rev[:12]);self.folder.mkdir(parents=True)
  self.weight=self.folder/'model.safetensors';header=json.dumps({'x':{'dtype':'F32','shape':[1],'data_offsets':[0,4]}}).encode();self.raw=struct.pack('<Q',len(header))+header+struct.pack('<f',1.0);self.weight.write_bytes(self.raw)
  self.sha=hashlib.sha256(self.raw).hexdigest();self.receipt={'repo':self.repo,'revision':self.rev,'license':'apache-2.0','native_verified':True,'digest':self.sha,'total':len(self.raw),'files':[{'name':'model.safetensors','size':len(self.raw),'sha':self.sha}]}
  (self.folder/'receipt.json').write_text(json.dumps(self.receipt))
  self.remote={'id':self.repo,'sha':self.rev,'private':False,'gated':False,'cardData':{'license':'apache-2.0'},'siblings':[{'rfilename':'model.safetensors','size':len(self.raw),'lfs':{'sha256':self.sha}}]}
  self.cache=Cache(self.root,metadata=lambda repo,rev:self.remote,stream=lambda repo,rev:io.BytesIO(self.raw),free=lambda:MIN_FREE+100000)
 def tearDown(self):self.tmp.cleanup()
 def test_exact_roundtrip_and_keep_receipt(self):
  self.assertEqual(self.cache.list()[0]['status'],'local')
  self.cache.evict(self.sha);self.assertFalse(self.weight.exists());self.assertTrue((self.folder/'receipt.json').exists());self.assertEqual(self.cache.list()[0]['status'],'remote')
  self.cache.ensure(self.sha);self.assertEqual(self.weight.read_bytes(),self.raw);self.assertEqual(self.cache.list()[0]['status'],'local')
 def test_modified_weight_and_changed_remote_are_preserved(self):
  self.weight.write_bytes(b'changed');self.assertRaises(ValueError,self.cache.evict,self.sha);self.assertEqual(self.weight.read_bytes(),b'changed')
  self.weight.write_bytes(self.raw);self.remote['private']=True;self.assertRaises(ValueError,self.cache.evict,self.sha);self.assertTrue(self.weight.exists())
 def test_active_acquisition_blocks_mutation(self):
  (self.root/'active.lock').write_text('queue');self.assertRaises(FileExistsError,self.cache.evict,self.sha);self.assertTrue(self.weight.exists())
 def test_failed_restore_no_partial_or_overwrite(self):
  self.cache.evict(self.sha);self.cache.stream=lambda a,b:io.BytesIO(b'x'*len(self.raw));self.assertRaises(ValueError,self.cache.ensure,self.sha);self.assertFalse(self.weight.exists());self.assertEqual(self.cache.list()[0]['status'],'remote')
 def test_storage_reserve(self):
  self.cache.evict(self.sha);self.cache.free=lambda:MIN_FREE;self.assertRaises(ValueError,self.cache.ensure,self.sha);self.assertFalse(self.weight.exists())
if __name__=='__main__':unittest.main()
