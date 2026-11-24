import copy, unittest
import evolution_proof_curriculum_v84 as m

class Tests(unittest.TestCase):
    def test_exact_hand_solved(self):
        edges=[[0,1,3],[0,2,2],[1,2,1],[1,3,2],[2,3,3]]
        for family,answer in [('shortest_path',5),('max_flow',5)]:
            q={'family':family,'n':4,'source':0,'sink':3,'edges':edges}
            cert=m.solve(q)
            self.assertEqual(cert['answer'],answer)
            self.assertTrue(m.verify(q,cert))
    def test_curriculum_and_metamorphic(self):
        for family in m.FAMILIES:
            for n in m.SIZES:
                for seed in range(12):
                    q=m.generate(family,n,seed);self.assertEqual(q,m.generate(family,n,seed))
                    c=m.solve(q);self.assertTrue(m.verify(q,c))
                    t=m.transform(q,seed+100,3);d=m.solve(t)
                    self.assertTrue(m.verify(t,d));self.assertEqual(d['answer'],3*c['answer'])
    def test_corrupt_certificates(self):
        for family in m.FAMILIES:
            q=m.generate(family,8,1);c=m.solve(q)
            for value in (True,c['answer']+1,-1):
                with self.assertRaises(ValueError):m.verify(q,{**c,'answer':value})
            bad=copy.deepcopy(c)
            if family=='shortest_path':bad['potentials'][q['sink']]+=1
            else:bad['flows'][0]=q['edges'][0][2]+1
            with self.assertRaises(ValueError):m.verify(q,bad)
            with self.assertRaises(ValueError):m.verify(q,{**c,'extra':1})
    def test_bounds_and_edge_validation(self):
        for args in [('max_flow',True,1),('max_flow',64,1),('unknown',4,1),('max_flow',4,-1)]:
            with self.assertRaises(ValueError):m.generate(*args)
        q=m.generate('max_flow',4,2)
        for e in ([0,0,1],[0,4,1],[0,1,True],[0,1,0],q['edges'][0]):
            with self.assertRaises(ValueError):m.solve({**q,'edges':q['edges']+[e]})
    def test_reference_objectives_by_exhaustive_enumeration(self):
        import itertools
        for seed in range(12):
            for family in m.FAMILIES:
                q=m.generate(family,4,seed);c=m.solve(q);g={(u,v):w for u,v,w in q['edges']}
                if family=='max_flow':
                    value=min(sum(w for (u,v),w in g.items() if u in cut and v not in cut) for k in range(3) for mid in itertools.combinations((1,2),k) for cut in [{0,*mid}])
                else:
                    value=min(sum(g[u,v] for u,v in zip(path,path[1:])) for k in range(3) for mid in itertools.permutations((1,2),k) for path in [(0,*mid,3)] if all((u,v) in g for u,v in zip(path,path[1:])))
                self.assertEqual(c['answer'],value)
if __name__=='__main__':unittest.main()
