import unittest,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from corpus_overlap import scan
class Overlap(unittest.TestCase):
 def test_template(self):
  r=scan(['Alice has 12 red apples and buys 4 more apples.'],['Alice has 20 red apples and buys 7 more apples.'])
  self.assertEqual(r['template_exact_pairs'],1)
 def test_unrelated(self):
  self.assertEqual(scan(['red apples grow on trees'],['a train travels west'])['near_pairs'],0)
 def test_near(self):
  self.assertEqual(scan(['Alice buys red apples from the local grocery store'],['Alice buys red apples from the local grocery store today'])['near_pairs'],1)
