import concurrent.futures, hashlib, hmac, json, tempfile, unittest
from pathlib import Path
import evolution_window_claim_v96 as m

KEY=b'test-key-only-not-production'

def signed(seed,status='completed'):
    row={'seed':seed,'status':status}
    payload=json.dumps(row,sort_keys=True,separators=(',',':')).encode()
    return {**row,'signature':hmac.new(KEY,payload,hashlib.sha256).hexdigest()}

def verify(row,key):
    body=dict(row);sig=body.pop('signature',None)
    if set(body)!={'seed','status'} or type(body['seed']) is not int or body['status'] not in ('completed','failed'):raise ValueError('invalid receipt')
    payload=json.dumps(body,sort_keys=True,separators=(',',':')).encode()
    if not isinstance(sig,str) or not hmac.compare_digest(hmac.new(key,payload,hashlib.sha256).hexdigest(),sig):raise ValueError('invalid authentication')
    return True

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.history=self.root/'teacher-v40';self.history.mkdir()
    def tearDown(self):self.tmp.cleanup()
    def put(self,name,row):
        (self.history/name).write_text(json.dumps(row),encoding='utf-8')
    def claim(self,seed):return m.reserve(self.root,seed,KEY,verify)
    def test_concurrent_exclusive_claim(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:r=list(pool.map(lambda _:self.claim(7),range(24)))
        self.assertEqual(r.count(True),1);self.assertEqual(r.count(False),23)
        self.assertFalse(self.claim(7));self.assertTrue(self.claim(8))
    def test_legacy_completed_failed_and_duplicate_seeds(self):
        self.put('tool-research-v64-a.json',signed(3))
        self.put('tool-research-v64-b.json',signed(3))
        self.put('tool-research-v64-c.json',signed(4,'failed'))
        self.assertFalse(self.claim(3));self.assertFalse(self.claim(4));self.assertTrue(self.claim(5))
        self.assertEqual(len(list(self.history.iterdir())),3)
    def test_authenticate_all_history_even_if_duplicate_found(self):
        self.put('tool-research-v64-a.json',signed(3))
        self.put('tool-research-v64-b.json',{**signed(4),'seed':5})
        with self.assertRaises(ValueError):self.claim(3)
        self.assertFalse((self.root/m.CLAIMS).exists())
    def test_duplicate_json_and_oversize(self):
        p=self.history/'tool-research-v64-a.json'
        p.write_text('{"seed":1,"seed":2}',encoding='utf-8')
        with self.assertRaises(ValueError):self.claim(9)
        p.write_bytes(b'x'*(m.MAX_RECEIPT+1))
        with self.assertRaises(ValueError):self.claim(9)
    def test_invalid_seed_and_unsafe_path(self):
        for x in (True,-1,2**63,'1'):
            with self.subTest(x=x),self.assertRaises(ValueError):self.claim(x)
        target=self.root/'other';target.mkdir();self.history.rmdir()
        try:self.history.symlink_to(target,target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest('symlinks unavailable')
        with self.assertRaises(ValueError):self.claim(1)
    def test_bounded_scan_and_corrupt_claim(self):
        from unittest.mock import patch
        for i in range(3):self.put(f'tool-research-v64-{i}.json',signed(i))
        with patch.object(m,'MAX_HISTORY',2),self.assertRaises(ValueError):self.claim(9)
        self.assertTrue(self.claim(9));p=self.root/m.CLAIMS/'9.claim';p.write_text('corrupt',encoding='utf-8')
        self.assertFalse(self.claim(9)) # even incomplete markers consume the window
if __name__=='__main__':unittest.main()
