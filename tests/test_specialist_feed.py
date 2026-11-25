import unittest,sys,pathlib,math
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from specialist_feed import fuse_rankings
class FeedTest(unittest.TestCase):
 def test_all_candidates_and_provenance_preserved(self):
  s=[{'text':'first','sha256':'a'*64},{'text':'second','sha256':'b'*64},{'text':'third','sha256':'c'*64}]
  ranked=fuse_rankings(s,[{'model':'encoder1','scores':[.1,.8,.2]},{'model':'encoder2','scores':[.2,.6,.1]}])
  self.assertEqual([r['text'] for r in ranked],['second','first','third'])
  self.assertEqual(ranked[0]['specialist_scores'],{'encoder1':.8,'encoder2':.6})
  self.assertEqual(len(s[0]),2)
 def test_reject_incomplete_invalid_scores(self):
  s=[{'text':'a'},{'text':'b'}]
  for rows in ([{'model':'a','scores':[1]}],[{'model':'a','scores':[0,math.nan]}],[{'model':'a','scores':[0,2]}],[{'model':'a','scores':[0,1]},{'model':'a','scores':[1,0]}]):
   with self.assertRaises(ValueError):fuse_rankings(s,rows)
