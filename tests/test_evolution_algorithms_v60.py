import cmath,itertools,math,random,unittest
import evolution_algorithms_v60 as a
class Tests(unittest.TestCase):
 def test_graph_optimization(self):
  self.assertEqual(a.scc({0:[1],1:[0,2],2:[3],3:[2]}),[{2,3},{0,1}])
  self.assertEqual(a.astar({0:{1:2,2:7},1:{2:1},2:{}},0,2,lambda x:0),(3,[0,1,2]))
  self.assertEqual(len(a.hopcroft_karp({0:[1,2],1:[1],2:[2,3]})),3)
  for seed in range(20):
   rng=random.Random(seed);m=[[rng.randrange(-9,10) for _ in range(4)] for _ in range(4)]
   cost,p=a.hungarian(m)
   self.assertEqual(cost,min(sum(m[i][j] for i,j in enumerate(q)) for q in itertools.permutations(range(4))))
   self.assertEqual(len(set(p)),4)
  self.assertEqual(a.weighted_intervals([(0,2,4),(1,4,10),(2,5,8)])[0],12)
  self.assertEqual(a.stable_matching([[0,1],[0,1]],[[1,0],[0,1]]),[1,0])
 def test_sequences(self):
  self.assertEqual(a.aho_corasick('ushers',['he','she','hers']),[(1,'she'),(2,'he'),(2,'hers')])
  self.assertEqual(a.dtw([1,2,3],[1,1,2,3]),0)
  rng=random.Random(60)
  for n in range(1,50):
   x=[rng.randrange(8) for _ in range(n)]
   self.assertEqual(a.inversions(x),sum(v>w for i,v in enumerate(x) for w in x[i+1:]))
   self.assertEqual(a.radix_sort(x),sorted(x))
   self.assertEqual(a.counting_sort(x),sorted(x))
  self.assertEqual(a.manacher('babad'),(0,3))
  self.assertEqual(a.z_search('ababa','aba'),[0,2])
 def test_numerical(self):
  self.assertAlmostEqual(a.logsumexp([1000,1000]),1000+math.log(2))
  self.assertEqual(a.kahan([1e16,1,1,-1e16]),2)
  L=a.cholesky([[4,2],[2,3]])
  self.assertAlmostEqual(L[1][0]**2+L[1][1]**2,3)
  x=a.conjugate_gradient([[4,1],[1,3]],[1,2])
  self.assertAlmostEqual(x[0],1/11);self.assertAlmostEqual(x[1],7/11)
  for n in (2,4,8,16):
   v=list(range(n));w=a.fft(v)
   for k in range(n):self.assertAlmostEqual(abs(w[k]-sum(x*cmath.exp(-2j*math.pi*k*i/n) for i,x in enumerate(v))),0,places=9)
  self.assertAlmostEqual(a.goertzel([1,0,-1,0],1),4)
  self.assertEqual(a.pava([3,1,2,5,4]),[2,2,2,4.5,4.5])
  self.assertAlmostEqual(a.huber_location([0,0,0,100],1),1/3,places=5)
 def test_statistics(self):
  self.assertEqual(a.hampel([1,1,9,1,1],1),[1,1,1,1,1])
  self.assertIn(4,a.page_hinkley([0,0,0,0,10],.01,2))
  self.assertAlmostEqual(a.ewma_variance([1,2],.5),2.5)
  self.assertAlmostEqual(a.roc_auc([0,1,1,0],[.1,.9,.8,.2]),1)
  self.assertEqual(a.kaplan_meier([(1,1),(2,0),(3,1)]),[(1,2/3),(3,0.)])
  self.assertEqual(a.bh([.01,.04,.2],.05),[0])
  lo,hi=a.wilson(5,10);self.assertTrue(lo<.5<hi)
  self.assertEqual(a.reservoir(range(10),10,1),list(range(10)))
  self.assertEqual(a.bootstrap_mean([4]*10,100,1),(4.,4.))
  self.assertEqual(a.permutation_difference([1,1],[1,1],100,1),1.)
 def test_number_theory_and_registry(self):
  for n in range(2,1000):self.assertEqual(a.miller_rabin(n),all(n%d for d in range(2,math.isqrt(n)+1)))
  g,x,y=a.extended_gcd(240,46);self.assertEqual((g,240*x+46*y),(2,2))
  self.assertEqual(a.modular_power(7,100,23),pow(7,100,23))
  self.assertEqual(len(a.REGISTRY),34);self.assertEqual(len(set(a.REGISTRY.values())),34)
  with self.assertRaises(ValueError):a.cholesky([[1,2],[2,1]])
  with self.assertRaises(ValueError):a.fft([1,2,3])
  with self.assertRaises(ValueError):a.hungarian([[1,2]])
if __name__=='__main__':unittest.main()
