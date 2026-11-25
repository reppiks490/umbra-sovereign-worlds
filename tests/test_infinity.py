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
