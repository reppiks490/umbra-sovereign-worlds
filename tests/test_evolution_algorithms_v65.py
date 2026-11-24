import math,unittest
import evolution_algorithms_v65 as m
class Tests(unittest.TestCase):
 def test_graph(self):
  self.assertEqual(m.bridges({0:[1,2],1:[0,2],2:[0,1,3],3:[2]}),[(2,3)])
  p=m.pagerank({0:[1],1:[0]});self.assertAlmostEqual(p[0],.5)
  self.assertEqual(m.components({0:[1],1:[0],2:[]}),[{0,1},{2}])
 def test_sequences_and_clustering(self):
  self.assertEqual(m.longest_palindromic_subsequence('bbbab'),4)
  self.assertEqual(m.edit_script('abc','ab'),[('delete','c')])
  self.assertEqual(m.otsu([0,0,1,1,9,9,10,10]),1)
  labels=m.dbscan([[0],[.1],[.2],[8]],.25,2);self.assertEqual(labels,[0,0,0,-1])
  centers,labels=m.kmeans([[0.],[.2],[9.],[10.]],[[0.],[10.]])
  self.assertEqual(labels,[0,0,1,1]);self.assertAlmostEqual(centers[1][0],9.5)
 def test_probability(self):
  self.assertAlmostEqual(m.entropy([1,1]),1)
  self.assertAlmostEqual(m.mutual_information([[5,0],[0,5]]),1)
  p=m.bayes([.5,.5],[.2,.8]);self.assertAlmostEqual(p[1],.8)
  self.assertEqual(m.viterbi([.5,.5],[[.9,.1],[.1,.9]],[[.9,.1],[.1,.9]],[0,0,1]),[0,0,0])
  self.assertAlmostEqual(m.forward([.5,.5],[[.9,.1],[.1,.9]],[[.9,.1],[.1,.9]],[0]),.5)
 def test_numeric(self):
  self.assertAlmostEqual(m.newton(lambda x:x*x-2,lambda x:2*x,1),math.sqrt(2))
  self.assertAlmostEqual(m.trapezoid(lambda x:x,0,2,10),2)
  self.assertEqual(m.gauss_jordan([[2,0],[0,4]],[4,8]),[2.,2.])
  self.assertEqual(m.poly_eval([1,2,3],2),11)
  self.assertAlmostEqual(m.ema([1,3],.5)[1],2)
  self.assertAlmostEqual(m.ljung_box([1,-1,1,-1],1),4.5)
  self.assertEqual(len(m.REGISTRY),19)
 def test_invalid(self):
  with self.assertRaises(ValueError):m.gauss_jordan([[1,1],[1,1]],[1,2])
  with self.assertRaises(ValueError):m.entropy([0,0])
  with self.assertRaises(ValueError):m.dbscan([[0]],-1,1)
class AdversarialTests(unittest.TestCase):
 def test_nonfinite_clustering_controls(self):
  for eps in (float('nan'),float('inf')):
   with self.assertRaises(ValueError):m.dbscan([[0.],[1.]],eps,1)
 def test_zero_likelihood_viterbi_rejected(self):
  with self.assertRaises(ValueError):m.viterbi([1.,0.],[[1.,0.],[0.,1.]],[[1.,0.],[1.,0.]],[1])
 def test_nonfinite_matrix_rejected(self):
  for bad in (float('nan'),float('inf')):
   with self.assertRaises(ValueError):m.gauss_jordan([[bad]],[1.])
   with self.assertRaises(ValueError):m.gauss_jordan([[1.]],[bad])
 def test_hmm_probability_rows(self):
  with self.assertRaises(ValueError):m.forward([.8,.8],[[1.,0.],[0.,1.]],[[1.],[1.]],[0])
  with self.assertRaises(ValueError):m.forward([.5,.5],[[.3,.3],[0.,1.]],[[1.],[1.]],[0])
 def test_positive_iteration_budget(self):
  with self.assertRaises(ValueError):m.kmeans([[1.]],[[0.]],steps=0)
class ScaleAndPrecisionTests(unittest.TestCase):
 def test_deep_graph_without_recursion(self):
  n=2400
  g={i:[j for j in (i-1,i+1) if 0<=j<n] for i in range(n)}
  self.assertEqual(m.bridges(g),[(i,i+1) for i in range(n-1)])
 def test_parallel_edges_are_not_simple_graph(self):
  with self.assertRaises(ValueError):m.bridges({0:[1,1],1:[0,0]})
 def test_scale_invariant_linear_system(self):
  for k in (1e-120,1e-20,1.0,1e120):
   with self.subTest(scale=k):
    x=m.gauss_jordan([[2*k,k],[k,3*k]],[5*k,7*k])
    self.assertAlmostEqual(x[0],1.6)
    self.assertAlmostEqual(x[1],1.8)
 def test_viterbi_does_not_round_away_real_advantage(self):
  self.assertEqual(m.viterbi([.5-1e-15,.5+1e-15],[[1.,0.],[0.,1.]],[[1.],[1.]],[0]),[1])
 def test_viterbi_long_sequence(self):
  self.assertEqual(m.viterbi([1.],[[1.]],[[1.]],[0]*6000),[0]*6000)
if __name__=='__main__':unittest.main()
