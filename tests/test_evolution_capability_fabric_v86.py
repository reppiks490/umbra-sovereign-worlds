import tempfile,unittest,json
from pathlib import Path
import evolution_capability_fabric_v86 as m

class Tests(unittest.TestCase):
    def test_registry_is_read_only_and_covers_discovery(self):
        a=m.list_tools()
        self.assertEqual({x['name'] for x in a},set(m.SPECS))
        self.assertEqual(len(a),7)
        self.assertTrue(all(x['read_only'] and not x['execution_authorized'] for x in a))
    def test_github_and_hub_public_queries(self):
        url=m.request_url('github.search',{'query':'agent tools','limit':5})
        self.assertEqual(url,'https://api.github.com/search/repositories?q=agent+tools&per_page=5')
        url=m.request_url('hf.spaces',{'query':'reasoning','limit':3})
        self.assertEqual(url,'https://huggingface.co/api/spaces?search=reasoning&limit=3')
        for args in ({'query':'a','limit':True},{'query':'a','limit':21},{'query':'a','limit':2,'url':'http://localhost'},{'query':'a\nb','limit':2}):
            with self.assertRaises(ValueError):m.request_url('github.search',args)
        with self.assertRaises(ValueError):m.request_url('arbitrary.run',{})
    def test_market_symbols_and_quotes(self):
        a=m.normalize('coinbase.spot',{'symbol':'BTC-USD'}, {'data':{'base':'BTC','currency':'USD','amount':'100.12'}})
        self.assertEqual(a,{'symbol':'BTC-USD','price':'100.12','quote_currency':'USD'})
        b=m.normalize('bybit.spot',{'symbol':'BTCUSDT'},{'retCode':0,'result':{'category':'spot','list':[{'symbol':'BTCUSDT','lastPrice':'101.2'}]},'time':1000})
        self.assertEqual(b['quote_currency'],'USDT')
        self.assertEqual(b['source_time_ms'],1000)
        for s in ['BTC-USD/../../','BTCUSDT?x=1','btc-usd']:
            with self.assertRaises(ValueError):m.request_url('coinbase.spot',{'symbol':s})
        for v in ['NaN','Infinity','0','-1']:
            with self.assertRaises(ValueError):m.normalize('coinbase.spot',{'symbol':'BTC-USD'},{'data':{'base':'BTC','currency':'USD','amount':v}})
        with self.assertRaises(ValueError):m.normalize('bybit.spot',{'symbol':'BTCUSDT'},{'retCode':1})
    def test_duplicate_json_and_size_fail_closed(self):
        for raw in [b'{"x":1,"x":2}',b'{"x":NaN}',b'x'*1048577]:
            with self.assertRaises(ValueError):m.decode(raw)
    def test_persistent_cache_budget_and_freshness(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);calls=[]
            def fake(url):
                calls.append(url)
                return b'{"data":{"base":"BTC","currency":"USD","amount":"100"}}'
            f=m.Fabric(p,transport=fake,clock=lambda:1000)
            a=f.invoke('coinbase.spot',{'symbol':'BTC-USD'})
            self.assertFalse(a['cache_hit']);self.assertEqual(a['observed_at'],1000)
            f=m.Fabric(p,transport=fake,clock=lambda:1005)
            self.assertTrue(f.invoke('coinbase.spot',{'symbol':'BTC-USD'})['cache_hit'])
            self.assertEqual(len(calls),1)
            f=m.Fabric(p,transport=fake,clock=lambda:1061)
            self.assertFalse(f.invoke('coinbase.spot',{'symbol':'BTC-USD'})['cache_hit'])
            self.assertEqual(len(calls),2)
            with self.assertRaises(m.BudgetError):f.invoke('coinbase.spot',{'symbol':'ETH-USD'})
            self.assertEqual(len(calls),2)
    def test_failed_request_consumes_provider_budget(self):
        with tempfile.TemporaryDirectory() as t:
            def fake(url):raise OSError('synthetic failure')
            f=m.Fabric(Path(t),transport=fake,clock=lambda:1000)
            with self.assertRaises(OSError):f.invoke('hf.models',{'query':'qwen','limit':1})
            with self.assertRaises(m.BudgetError):f.invoke('hf.spaces',{'query':'qwen','limit':1})
    def test_metadata_minimization(self):
        rows=m.normalize('hf.models',{'query':'qwen','limit':1},[{'id':'Qwen/test','sha':'a'*40,'private':False,'tags':['license:apache-2.0'],'secret':'do not retain'}])
        self.assertEqual(rows,[{'id':'Qwen/test','revision':'a'*40,'license':'apache-2.0'}])
        self.assertNotIn('secret',str(rows))
if __name__=='__main__':unittest.main()
