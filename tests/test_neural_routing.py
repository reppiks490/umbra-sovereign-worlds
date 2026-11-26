import sys,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from neural_routing import rank_candidates, select_route
class RoutingTest(unittest.TestCase):
 def test_cross_encoder_rank_not_cosine_average(self):
  sources=[{'repo':'a'},{'repo':'b'},{'repo':'c'}]
  r=rank_candidates(sources,[0.9,0.1,0.2],[0.1,0.9,0.2],[0.0,12.0,-9.0])
  self.assertEqual(r['cross_encoder'][0]['repo'],'b')
  self.assertEqual(r['cosine_mean'][0]['repo'],'a')
  self.assertEqual(set(r),{'cross_encoder','cosine_mean','rank_fusion'})
 def test_invalid_scores(self):
  for v in ([1,2],[1,float('nan'),2]):
   with self.assertRaises(ValueError):rank_candidates([{}, {}, {}],[0,0,0],[0,0,0],v)
 def test_fail_closed_without_new_evidence(self):
  self.assertEqual(select_route({},'cosine_mean'),'cosine_mean')
  self.assertEqual(select_route({'status':'completed','independent':False,'candidate':'cross_encoder','cases':100,'wins':100,'losses':0},'cosine_mean'),'cosine_mean')
 def test_admission_requires_evidence_and_no_production_authority(self):
  e={'status':'completed','independent':True,'candidate':'cross_encoder','cases':40,'wins':20,'losses':2,'production_authority':False}
  self.assertEqual(select_route(e,'cosine_mean'),'cross_encoder')
  e['production_authority']=True
  self.assertEqual(select_route(e,'cosine_mean'),'cosine_mean')
if __name__=='__main__':unittest.main()
