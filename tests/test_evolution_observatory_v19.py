"""Real localhost HTTP smoke: new methods/tribunal remain purely read-only."""
import json,sys,threading,unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import evolution_api as api

class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),api.Handler)
        cls.url=f'http://127.0.0.1:{cls.server.server_port}'
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=3)

    def get(self,path):
        with urlopen(self.url+path,timeout=3) as r:
            self.assertEqual(r.headers['X-Content-Type-Options'],'nosniff')
            return json.load(r)

    def test_twelve_real_algorithms_exposed(self):
        m=self.get('/api/methods')
        self.assertEqual(m['count'],12)
        self.assertEqual(len({x['id'] for x in m['independent_implementations']}),12)
        self.assertEqual(m['automated_code_merges'],0)

    def test_195k_audit_is_stored_evidence_not_live_agents(self):
        a=self.get('/api/tribunal')
        self.assertEqual(a['independently_verified_receipt_records'],195000)
        self.assertTrue(a['synthetic_only'])
        self.assertEqual(a['production_integrations'],0)
        m=self.get('/api/metrics')
        self.assertEqual(m['implemented_independent_algorithms_v19'],12)
        self.assertEqual(m['live_dedicated_worker_processes'],0)

    def test_mutations_are_denied(self):
        with self.assertRaises(HTTPError) as e:
            urlopen(Request(self.url+'/api/methods',data=b'{}',method='POST'),timeout=3)
        self.assertEqual(e.exception.code,403)

if __name__=='__main__':unittest.main()
