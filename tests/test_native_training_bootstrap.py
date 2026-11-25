import unittest,tempfile,pathlib,sys
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import native_training_bootstrap as b
class Test(unittest.TestCase):
 def test_monitor_tolerates_disappearing_pip_metadata(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);(root/'keep.bin').write_bytes(b'1234')
   with patch.object(b,'ROOT',root),patch.object(pathlib.Path,'rglob',side_effect=FileNotFoundError('pip removed temp metadata')),patch.object(b.os,'walk',return_value=iter([(str(root),[],['keep.bin','vanished.tmp'])])):
    self.assertEqual(b.used(),4)
if __name__=='__main__':unittest.main()

class DownloadTest(unittest.TestCase):
 def test_resumes_exact_partial_and_checks_hash(self):
  import io,hashlib
  raw=b'abcdef123456'
  class Response(io.BytesIO):
   status=206
   headers={'Content-Range':'bytes 4-11/12'}
  with tempfile.TemporaryDirectory() as d:
   target=pathlib.Path(d)/'asset.whl';part=target.with_name(target.name+'.part');part.write_bytes(raw[:4])
   def opener(req,timeout):
    self.assertEqual(req.get_header('Range'),'bytes=4-');return Response(raw[4:])
   with patch.object(b,'gate',return_value=None):
    b.download_verified('https://example.invalid/asset',target,len(raw),hashlib.sha256(raw).hexdigest(),opener=opener,attempts=1)
   self.assertEqual(target.read_bytes(),raw);self.assertFalse(part.exists())
 def test_bad_digest_does_not_promote(self):
  import io,hashlib
  class Response(io.BytesIO):
   status=200
   headers={}
  with tempfile.TemporaryDirectory() as d:
   target=pathlib.Path(d)/'asset.whl'
   with patch.object(b,'gate',return_value=None):
    self.assertRaises(ValueError,b.download_verified,'https://example.invalid/asset',target,3,hashlib.sha256(b'abc').hexdigest(),opener=lambda *a,**kw:Response(b'xyz'),attempts=1)
   self.assertFalse(target.exists())
