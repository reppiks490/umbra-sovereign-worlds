import tempfile,unittest
from pathlib import Path
import evolution_capability_fabric_v86 as fabric
import evolution_skill_composition_v88 as m

class Tests(unittest.TestCase):
    def plan(self):
        return {'nodes':[
          {'id':'papers','op':'read','tool':'crossref.search','args':{'query':'graph reasoning','limit':2}},
          {'id':'repos','op':'read','tool':'github.search','args':{'query':'graph reasoning','limit':2}},
          {'id':'count','op':'count','input':'papers'},
          {'id':'joined','op':'join','inputs':['papers','repos','count']}],
          'output':'joined'}
    def test_real_fabric_with_transport_fixture(self):
        def transport(url):
            if 'crossref' in url:return b'{"message":{"items":[{"DOI":"10.1/example","title":["Proof"]}]}}'
            return b'{"items":[{"full_name":"example/repo","private":false,"license":{"spdx_id":"MIT"}}]}'
        with tempfile.TemporaryDirectory() as d:
            f=fabric.Fabric(Path(d),transport=transport,clock=lambda:1000)
            r=m.execute(self.plan(),f)
            self.assertEqual(r['status'],'completed')
            self.assertEqual(r['output']['count'],1)
            self.assertEqual(r['output']['papers']['data'][0]['doi'],'10.1/example')
            self.assertEqual(r['reads'],2)
            self.assertTrue(m.verify(r,self.plan()))
            r['output']['count']=900
            self.assertFalse(m.verify(r,self.plan()))
    def test_whole_plan_preflight_before_network(self):
        class F:
            def invoke(self,*a):raise AssertionError('network must not be reached')
        for node in [
            {'id':'evil','op':'read','tool':'shell.execute','args':{}},
            {'id':'evil','op':'count','input':'joined'},
            {'id':'evil','op':'read','tool':'github.search','args':{'query':{'ref':'papers'},'limit':1}},
            {'id':'papers','op':'count','input':'repos'}]:
            p=self.plan();p['nodes'].append(node)
            with self.assertRaises(ValueError):m.execute(p,F())
    def test_failure_blocks_dependents_not_independent(self):
        def transport(url):
            if 'crossref' in url:raise OSError('do not leak raw provider error')
            return b'{"items":[{"full_name":"example/repo","private":false,"license":{"spdx_id":"MIT"}}]}'
        with tempfile.TemporaryDirectory() as d:
            f=fabric.Fabric(Path(d),transport=transport,clock=lambda:1000)
            r=m.execute(self.plan(),f)
            self.assertEqual(r['status'],'failed')
            self.assertEqual(r['nodes']['papers']['error_class'],'OSError')
            self.assertEqual(r['nodes']['repos']['status'],'completed')
            self.assertEqual(r['nodes']['count']['status'],'blocked')
            self.assertEqual(r['nodes']['joined']['status'],'blocked')
            self.assertIsNone(r['output'])
            self.assertNotIn('do not leak',str(r))
            self.assertTrue(m.verify(r,self.plan()))
    def test_provider_budget_preflight(self):
        p={'nodes':[{'id':'a','op':'read','tool':'hf.models','args':{'query':'x','limit':1}},
                    {'id':'b','op':'read','tool':'hf.spaces','args':{'query':'x','limit':1}}],'output':'b'}
        with self.assertRaises(ValueError):m.validate(p)
    def test_scope_and_dead_nodes(self):
        p=self.plan();p['output']='count'
        with self.assertRaises(ValueError):m.validate(p)
        p=self.plan();p['output']='missing'
        with self.assertRaises(ValueError):m.validate(p)
    def test_nested_join_amplification_rejected(self):
        p=self.plan()
        p['nodes'].append({'id':'nested','op':'join','inputs':['joined','count']})
        p['output']='nested'
        with self.assertRaises(ValueError):m.validate(p)
if __name__=='__main__':unittest.main()
