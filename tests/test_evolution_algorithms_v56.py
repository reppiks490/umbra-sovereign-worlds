import math,unittest
import evolution_algorithms_v56 as m
class Tests(unittest.TestCase):
 def test_graph(self):
  self.assertEqual(m.floyd_warshall([[0,2,math.inf],[math.inf,0,3],[1,math.inf,0]])[0][2],5)
  self.assertEqual(m.kruskal(4,[(0,1,1),(1,2,2),(2,3,3),(0,3,10)])[0],6)
  self.assertEqual(m.bfs_path({0:[1,2],1:[3],2:[3],3:[]},0,3),[0,1,3])
  self.assertEqual(m.max_flow({0:{1:3,2:2},1:{2:1,3:2},2:{3:3},3:{}},0,3),5)
 def test_sequences(self):
  self.assertEqual(m.kmp('ababa','aba'),[0,2])
  self.assertEqual(m.longest_common_subsequence('ABCBDAB','BDCABA'),4)
  self.assertEqual(m.knapsack([2,3,4],[4,5,7],5),9)
  self.assertEqual(m.huffman_lengths({'a':4,'b':2,'c':1,'d':1}),{'a':1,'b':2,'c':3,'d':3})
 def test_numeric(self):
  self.assertEqual(m.sieve(20),[2,3,5,7,11,13,17,19])
  self.assertAlmostEqual(m.bisection(lambda x:x*x-2,0,2),math.sqrt(2),places=8)
  self.assertAlmostEqual(m.simpson(lambda x:x*x,0,1,10),1/3)
  self.assertAlmostEqual(m.welford([1,2,3,4])[1],5/3)
 def test_signal(self):
  for a,b in zip(m.haar([1,1,3,3]),[4.,-2.,0.,0.]):self.assertAlmostEqual(a,b,places=12)
  self.assertEqual(m.mann_kendall([1,2,3,4]),6)
  self.assertAlmostEqual(m.theil_sen([0,1,2],[1,3,5]),2)
  self.assertAlmostEqual(m.js_divergence([1,0],[0,1]),1)
 def test_registry(self):
  self.assertEqual(len(m.REGISTRY),16)
  self.assertEqual(len(set(m.REGISTRY.values())),16)
 def test_invalid(self):
  with self.assertRaises(ValueError):m.bisection(lambda x:x*x+1,-1,1)
  with self.assertRaises(ValueError):m.simpson(lambda x:x,0,1,3)
  with self.assertRaises(ValueError):m.max_flow({0:{1:-1},1:{}},0,1)
  with self.assertRaises(ValueError):m.haar([1,2,3])
if __name__=='__main__':unittest.main()
