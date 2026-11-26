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


class BoundedRangeTests(unittest.TestCase):
 def test_large_transfer_uses_bounded_ranges_and_resumes_interrupted_chunk(self):
  import io,hashlib,http.client
  raw=b'abcdefghijklmnop'
  requests=[]
  class Response(io.BytesIO):
   status=206
   def __init__(self,start,end,interrupt=False):
    super().__init__(raw[start:end+1]);self.headers={'Content-Range':f'bytes {start}-{end}/{len(raw)}'};self.interrupt=interrupt
   def read(self,n=-1):
    if self.interrupt:
     self.interrupt=False
     raise http.client.IncompleteRead(super().read(2),2)
    return super().read(n)
  def opener(req,timeout):
   import re
   m=re.fullmatch(r'bytes=(\d+)-(\d+)',req.get_header('Range') or '')
   self.assertIsNotNone(m)
   start,end=map(int,m.groups());requests.append((start,end))
   return Response(start,end,interrupt=len(requests)==1)
  with tempfile.TemporaryDirectory() as d,patch.object(b,'log'),patch.object(b.time,'sleep'):
   target=pathlib.Path(d)/'weights';part=target.with_name(target.name+'.part');part.write_bytes(raw[:3])
   b.download_verified('https://example.invalid/weights',target,len(raw),hashlib.sha256(raw).hexdigest(),opener=opener,attempts=2,gate_fn=lambda n:None,range_bytes=4)
   self.assertEqual(target.read_bytes(),raw);self.assertFalse(part.exists())
   self.assertEqual(requests,[(3,6),(5,8),(9,12),(13,15)])
 def test_wrong_range_does_not_append(self):
  import io,hashlib
  class Response(io.BytesIO):
   status=206
   headers={'Content-Range':'bytes 0-3/8'}
  with tempfile.TemporaryDirectory() as d:
   target=pathlib.Path(d)/'weights';part=target.with_name(target.name+'.part');part.write_bytes(b'ab')
   with self.assertRaises(ValueError):
    b.download_verified('https://example.invalid/weights',target,8,hashlib.sha256(b'abcdefgh').hexdigest(),opener=lambda *a,**kw:Response(b'cdef'),gate_fn=lambda n:None,range_bytes=4)
   self.assertEqual(part.read_bytes(),b'ab');self.assertFalse(target.exists())
 def test_short_response_keeps_progress_and_exhausts_retry_budget(self):
  import io,hashlib
  class Response(io.BytesIO):
   status=206
   headers={'Content-Range':'bytes 0-3/8'}
  with tempfile.TemporaryDirectory() as d,patch.object(b,'log'),patch.object(b.time,'sleep'):
   target=pathlib.Path(d)/'weights'
   with self.assertRaises(OSError):
    b.download_verified('https://example.invalid/weights',target,8,hashlib.sha256(b'abcdefgh').hexdigest(),opener=lambda *a,**kw:Response(b'ab'),attempts=1,gate_fn=lambda n:None,range_bytes=4)
   self.assertEqual(target.with_name('weights.part').read_bytes(),b'ab');self.assertFalse(target.exists())
 def test_overlong_range_rejected_before_write(self):
  import io,hashlib
  class Response(io.BytesIO):
   status=206
   headers={'Content-Range':'bytes 0-3/8'}
  with tempfile.TemporaryDirectory() as d:
   target=pathlib.Path(d)/'weights'
   with self.assertRaises(ValueError):
    b.download_verified('https://example.invalid/weights',target,8,hashlib.sha256(b'abcdefgh').hexdigest(),opener=lambda *a,**kw:Response(b'abcde'),gate_fn=lambda n:None,range_bytes=4)
   self.assertFalse(target.exists());self.assertEqual(target.with_name('weights.part').stat().st_size,0)
