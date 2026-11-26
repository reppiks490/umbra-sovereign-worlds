import hashlib, io, pathlib, re, tempfile, unittest
from unittest.mock import patch
import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
import native_training_bootstrap as b

class RepeatedTruncation(unittest.TestCase):
    def test_server_closes_large_ranges_but_small_ranges_complete(self):
        raw = bytes(range(256)) * (24 * 1024 * 1024 // 256)
        calls = []
        class Response(io.BytesIO):
            status = 206
            def __init__(self, start, end):
                super().__init__(raw[start:min(end+1,start+3*1024*1024)])
                self.headers = {'Content-Range':f'bytes {start}-{end}/{len(raw)}'}
        def opener(req, timeout):
            m = re.fullmatch(r'bytes=(\d+)-(\d+)', req.get_header('Range') or '')
            self.assertIsNotNone(m)
            start,end = map(int,m.groups())
            calls.append((start,end))
            return Response(start,end)
        with tempfile.TemporaryDirectory() as d, patch.object(b,'log'), patch.object(b.time,'sleep'):
            p=pathlib.Path(d)/'weights'
            p.with_name('weights.part').write_bytes(raw[:1024])
            b.download_verified('https://example.invalid/weights',p,len(raw),hashlib.sha256(raw).hexdigest(),opener=opener,gate_fn=lambda n:None)
            self.assertEqual(p.read_bytes(),raw)
            self.assertFalse(p.with_name('weights.part').exists())
            self.assertLess(len(calls),30)
    def test_no_progress_is_still_bounded(self):
        raw=b'abcdefghi'
        calls=[]
        class Response(io.BytesIO):
            status=206
            def __init__(self,start,end):
                super().__init__(b'')
                self.headers={'Content-Range':f'bytes {start}-{end}/{len(raw)}'}
        def opener(req,timeout):
            m=re.fullmatch(r'bytes=(\d+)-(\d+)',req.get_header('Range') or '')
            start,end=map(int,m.groups());calls.append((start,end))
            return Response(start,end)
        with tempfile.TemporaryDirectory() as d,patch.object(b,'log'),patch.object(b.time,'sleep'):
            p=pathlib.Path(d)/'weights'
            with self.assertRaises(OSError):
                b.download_verified('https://example.invalid/weights',p,len(raw),hashlib.sha256(raw).hexdigest(),opener=opener,gate_fn=lambda n:None,attempts=3,range_bytes=4)
            self.assertEqual(len(calls),3)
            self.assertFalse(p.exists())
if __name__=='__main__':unittest.main()
