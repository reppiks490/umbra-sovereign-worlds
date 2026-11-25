import unittest,tempfile,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from infinity import select_candidates,score_embeddings,run_cycle,empty_state
class Test(unittest.TestCase):
 def test_ranks_unqualified_supported_models_and_does_not_repeat_success(self):
  rows=[{'repo':'a/a','runtime':'catalog-only','digest':'a'*64},{'repo':'b/b','runtime':'numpy-bert','digest':'b'*64},{'repo':'c/c','runtime':'numpy-bert','digest':'c'*64}]
  state=empty_state();state['profiles']['b'*64]={'status':'qualified','score':1}
  self.assertEqual([x['repo'] for x in select_candidates(rows,state,100)],['c/c'])
 def test_retrieval_score_uses_actual_rankings(self):
  cases=[([1.,0.],[[1.,0.],[0.,1.]],0),([0.,1.],[[1.,0.],[0.,1.]],1)]
  self.assertEqual(score_embeddings(cases)['accuracy'],1)
  cases[1]=([1.,0.],[[1.,0.],[0.,1.]],1)
  self.assertEqual(score_embeddings(cases)['accuracy'],.5)
 def test_active_queue_blocks_all_weight_actions(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);(root/'active.lock').write_text('existing')
   def forbidden(*a,**k):raise AssertionError('must not run')
   r=run_cycle(root,discover=forbidden,qualify=forbidden)
   self.assertEqual(r['status'],'deferred_acquisition')
 def test_cycle_selects_and_records_real_result(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)
   row={'repo':'b/b','runtime':'numpy-bert','digest':'b'*64}
   r=run_cycle(root,discover=lambda:[row],qualify=lambda root,row:{'status':'qualified','score':1.0})
   self.assertEqual(r['status'],'completed')
   self.assertEqual(r['profiles']['b'*64]['status'],'qualified')
   r=run_cycle(root,discover=lambda:[row],qualify=lambda *a: self.fail('already qualified'))
   self.assertEqual(r['status'],'completed')
if __name__=='__main__':unittest.main()
class ServiceTest(unittest.TestCase):
 def test_initial_queue_gate(self):
  from infinity_service import queue_ready
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);self.assertEqual(queue_ready(p),'initial_queue_not_verified')
   (p/'active.lock').write_text('owner');self.assertEqual(queue_ready(p),'deferred_acquisition')
class GapScheduleTest(unittest.TestCase):
 def test_audit_mode_never_probes_during_initial_download(self):
  from infinity_service import gap_command
  p=pathlib.Path('C:/private')
  self.assertEqual(gap_command(p,'deferred_acquisition')[-1],'audit')
  self.assertEqual(gap_command(p,'ready')[-1],'probe')
 def test_discovery_covers_reasoning_and_multimodal_tasks(self):
  from infinity import DISCOVERY_TASKS
  self.assertTrue({'text-generation','question-answering','time-series-forecasting','image-classification','automatic-speech-recognition'}<=set(DISCOVERY_TASKS))

class SwarmScheduleTest(unittest.TestCase):
 def test_bootstrap_protects_live_inference_and_training(self):
  from infinity_service import swarm_command, native_training_plan
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);training=root/'training';training.mkdir()
   (training/'bootstrap.lock').write_text('active')
   self.assertEqual(swarm_command(root,training)[-1],'init')
   self.assertEqual(native_training_plan(root,training,'ready',10**10)['status'],'deferred_bootstrap')
   (training/'bootstrap.lock').unlink()
   self.assertEqual(swarm_command(root,training)[-1],'cycle')
   self.assertEqual(native_training_plan(root,training,'deferred_acquisition',10**10)['status'],'deferred_acquisition')
 def test_native_training_fails_closed_without_memory(self):
  from infinity_service import native_training_plan
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);training=root/'training';training.mkdir()
   (training/'ready.json').write_text('{"runtime_verified":true,"native_sources_verified":true}')
   self.assertEqual(native_training_plan(root,training,'ready',1)['status'],'deferred_memory')

class BootstrapRecoveryTest(unittest.TestCase):
 def test_retry_plan_preserves_active_jobs_and_reserves(self):
  from infinity_service import bootstrap_plan
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);training=root/'training';training.mkdir()
   (training/'bootstrap.lock').write_text('active')
   self.assertEqual(bootstrap_plan(training,'ready',60*10**9,0,100000)['status'],'running')
   (training/'bootstrap.lock').unlink()
   self.assertEqual(bootstrap_plan(training,'deferred_acquisition',50*10**9,0,100000)['status'],'deferred_storage')
   self.assertEqual(bootstrap_plan(training,'ready',20*10**9,0,100000)['status'],'eligible')
   self.assertEqual(bootstrap_plan(training,'ready',20*10**9,99999,100000)['status'],'deferred_cooldown')

class MarketScheduleTest(unittest.TestCase):
 def test_market_academy_defers_inference_during_acquisition_or_bootstrap(self):
  from infinity_service import market_command
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);training=root/'training';training.mkdir()
   self.assertEqual(market_command(root,training,'deferred_acquisition')[-1],'audit')
   self.assertEqual(market_command(root,training,'ready')[-1],'cycle')
   (training/'bootstrap.lock').write_text('active')
   self.assertEqual(market_command(root,training,'ready')[-1],'audit')

class OmniScheduleTest(unittest.TestCase):
 def test_omni_audits_until_acquisition_ready(self):
  from infinity_service import omni_command
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);training=root/'training';training.mkdir()
   self.assertEqual(omni_command(root,training,'deferred_acquisition')[-1],'audit')
   self.assertEqual(omni_command(root,training,'ready')[-1],'cycle')
   (training/'bootstrap.lock').write_text('active')
   self.assertEqual(omni_command(root,training,'ready')[-1],'audit')
