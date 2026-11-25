import unittest,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from neural_priority import can_admit,rank_candidates,CAP
class Test(unittest.TestCase):
 def test_expanded_cap_and_storage_protection(self):
  self.assertEqual(CAP,28000000000)
  self.assertTrue(can_admit(12000000000,1000000000,12000000000,2000000000))
  self.assertFalse(can_admit(27900000000,200000000,20000000000,0))
  self.assertFalse(can_admit(12000000000,1000000000,5999999999,2000000000))
 def test_rank_new_capabilities_and_skip_duplicates(self):
  rows=[{'repo':'old','digest':'a','total':100,'domain':'vision','value':10},{'repo':'audio','digest':'b','total':200,'domain':'audio','value':9},{'repo':'vision','digest':'c','total':100,'domain':'vision','value':9}]
  self.assertEqual([x['repo'] for x in rank_candidates(rows,{'a'},{'vision'})],['audio','vision'])

 def test_schedule_does_not_compete_or_repeat_completed_pass(self):
  from neural_priority import priority_plan
  self.assertEqual(priority_plan('deferred_acquisition',False,False,0,10000,{}),'deferred_original')
  self.assertEqual(priority_plan('ready',True,False,0,10000,{}),'deferred_bootstrap')
  self.assertEqual(priority_plan('ready',False,True,0,10000,{}),'running')
  self.assertEqual(priority_plan('ready',False,False,0,10000,{}),'eligible')
  self.assertEqual(priority_plan('ready',False,False,9999,10000,{}),'cooldown')
  self.assertEqual(priority_plan('ready',False,False,0,10000,{'status':'pass_finished','results':[{'status':'verified'}]}),'complete')
  self.assertEqual(priority_plan('ready',False,False,0,10000,{'status':'pass_finished','results':[{'status':'deferred_storage'}],'timestamp':9999}),'cooldown')

 def test_storage_deferral_does_not_starve_training_bootstrap(self):
  from neural_priority import priority_plan
  self.assertEqual(priority_plan('ready',False,False,0,10000,{'status':'pass_finished','results':[{'status':'deferred_storage'}],'timestamp':8000}),'cooldown')

 def test_expanded_allocation_reopens_prior_cap_deferral(self):
  from neural_priority import priority_plan
  old={'cap_bytes':15000000000,'status':'pass_finished','timestamp':9999,'results':[{'status':'deferred_storage'}]}
  self.assertEqual(CAP,28000000000)
  self.assertEqual(priority_plan('ready',False,False,9999,10000,old),'eligible')
  self.assertEqual(priority_plan('ready',True,False,9999,10000,old),'deferred_bootstrap')
  self.assertTrue(can_admit(14736604255,3137246852,6700000000,0))
  self.assertFalse(can_admit(14736604255,3137246852,6100000000,0))

 def test_new_cap_and_manifest_extension(self):
  from neural_priority import pending_candidates,CANDIDATES
  self.assertEqual(CAP,28000000000)
  self.assertTrue(can_admit(14736604255,13200000000,21800000000,2850000000))
  self.assertFalse(can_admit(14736604255,13200000000,18000000000,2850000000))
  previous=[{'repo':'openai/whisper-base'},{'repo':'google/siglip2-base-patch16-224'}]
  pending=pending_candidates(CANDIDATES,previous,[])
  self.assertNotIn('openai/whisper-base',[r[0] for r in pending])
  self.assertIn('microsoft/trocr-base-printed',[r[0] for r in pending])
