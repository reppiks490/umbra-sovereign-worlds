import io,json,tempfile,unittest
from pathlib import Path
import evolution_mcp_bridge_v92 as m
import evolution_capability_fabric_v86 as f
def req(i,method,params=None):
    r={'jsonrpc':'2.0','id':i,'method':method}
    if params is not None:r['params']=params
    return r
def init():
    return req(1,'initialize',{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'test','version':'1'}})
class Tests(unittest.TestCase):
    def ready(self,local):
        b=m.Bridge(local,('graph reasoning',),True)
        self.assertEqual(b.handle(init())['result']['protocolVersion'],'2025-11-25')
        self.assertIsNone(b.handle({'jsonrpc':'2.0','method':'notifications/initialized'}))
        return b
    def test_lifecycle_and_schema(self):
        b=m.Bridge(None,('graph reasoning',),False)
        self.assertIn('error',b.handle(req(0,'tools/list')))
        self.assertEqual(b.handle(init())['result']['capabilities'],{'tools':{'listChanged':False}})
        self.assertIn('error',b.handle(req(2,'tools/list')))
        b.handle({'jsonrpc':'2.0','method':'notifications/initialized'})
        tools=b.handle(req(3,'tools/list'))['result']['tools']
        self.assertEqual(len(tools),7)
        g=next(x for x in tools if x['name']=='github.search')
        self.assertEqual(g['inputSchema']['properties']['query']['enum'],['graph reasoning'])
        self.assertEqual(b.handle(req(4,'shell.execute'))['error']['code'],-32601)
    def test_no_egress_without_approved_query_and_authorization(self):
        class Never:
            def invoke(self,*a):raise AssertionError('unexpected egress')
        b=self.ready(Never())
        for params in [
            {'name':'github.search','arguments':{'query':'private project','limit':1}},
            {'name':'github.search','arguments':{'query':'graph reasoning','limit':1,'url':'http://localhost'}},
            {'name':'shell.execute','arguments':{}},
        ]:self.assertIn('error',b.handle(req(2,'tools/call',params)))
        b=m.Bridge(Never(),('graph reasoning',),False)
        b.handle(init());b.handle({'jsonrpc':'2.0','method':'notifications/initialized'})
        self.assertTrue(b.handle(req(3,'tools/call',{'name':'github.search','arguments':{'query':'graph reasoning','limit':1}}))['result']['isError'])
    def test_real_fabric_and_cached_output(self):
        calls=[]
        def transport(url):
            calls.append(url);return b'{"items":[{"full_name":"example/repo","private":false,"license":{"spdx_id":"MIT"}}]}'
        with tempfile.TemporaryDirectory() as d:
            b=self.ready(f.Fabric(Path(d),transport=transport,clock=lambda:1000))
            p={'name':'github.search','arguments':{'query':'graph reasoning','limit':1}}
            for i in (2,3):
                r=b.handle(req(i,'tools/call',p))['result']
                self.assertFalse(r['isError'])
                data=json.loads(r['content'][0]['text'])
                self.assertEqual(data['data'][0]['id'],'example/repo')
                self.assertEqual(data['cache_hit'],i==3)
            self.assertEqual(len(calls),1)
    def test_no_notifications_trigger_reads(self):
        class Never:
            def invoke(self,*a):raise AssertionError('notification read')
        b=self.ready(Never())
        self.assertIsNone(b.handle({'jsonrpc':'2.0','method':'tools/call','params':{'name':'github.search','arguments':{'query':'graph reasoning','limit':1}}}))
    def test_stdio_framing_and_duplicate_json(self):
        rows=[json.dumps(init()),json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'}),json.dumps(req(2,'tools/list')),'{"jsonrpc":"2.0","id":3,"id":4,"method":"ping"}']
        out=io.BytesIO();m.serve(m.Bridge(None,('graph reasoning',),False),io.BytesIO(('\n'.join(rows)+'\n').encode()),out)
        r=[json.loads(x) for x in out.getvalue().splitlines()]
        self.assertEqual(len(r),3)
        self.assertEqual(r[-1]['error']['code'],-32700)
    def test_errors_are_sanitized(self):
        class F:
            def invoke(self,*a):raise OSError('private raw traceback')
        b=self.ready(F());r=b.handle(req(2,'tools/call',{'name':'github.search','arguments':{'query':'graph reasoning','limit':1}}))
        self.assertTrue(r['result']['isError'])
        self.assertNotIn('private raw',str(r))
if __name__=='__main__':unittest.main()
