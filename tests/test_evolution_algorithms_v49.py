import unittest,math
import evolution_algorithms_v49 as m
class Tests(unittest.TestCase):
 def test_sort_selection(self):
  self.assertEqual(m.mergesort([3,1,2,1]),[1,1,2,3])
  self.assertEqual(m.quickselect([3,1,2,1],2),2)
 def test_graph(self):
  g={'a':{'b':2,'c':5},'b':{'c':1},'c':{}}
  self.assertEqual(m.dijkstra(g,'a')['c'],3)
  self.assertEqual(m.bellman_ford(g,'a')['c'],3)
  with self.assertRaises(ValueError):m.bellman_ford({'a':{'b':-1},'b':{'a':-1}},'a')
  self.assertEqual(m.topological({'a':['b'],'b':['c'],'c':[]}),['a','b','c'])
  with self.assertRaises(ValueError):m.topological({'a':['a']})
 def test_signal(self):
  self.assertAlmostEqual(m.kalman([2,2,2],1,1)[-1],2,places=1)
  self.assertEqual(m.cusum([0,0,4,0],0,2),[2])
  self.assertEqual(m.autocorr([1,-1,1,-1],1),-.75)
 def test_sequence(self):
  self.assertEqual(m.levenshtein('kitten','sitting'),3)
  self.assertEqual(m.lis([3,1,2,5,4]),3)
 def test_rolling_and_drawdown(self):
  self.assertEqual(m.rolling_median([3,1,4,2],3),[3,2])
  self.assertAlmostEqual(m.max_drawdown([100,120,90,130]),.25)
 def test_registry_distinct(self):
  self.assertEqual(len(m.REGISTRY),12)
  self.assertEqual(len(set(m.REGISTRY.values())),12)
if __name__=='__main__':unittest.main()
