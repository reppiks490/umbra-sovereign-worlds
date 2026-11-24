import unittest
import evolution_research_orchestrator_v39 as m
class RouterTests(unittest.TestCase):
 def test_pin_only_approved_and_never_replace(self):
  tags=[{'name':'qwen3:1.7b','digest':m.QWEN,'size':1359293444},{'name':'gemma3:1b','digest':'a'*64,'size':806067407},{'name':'unapproved:1b','digest':'b'*64,'size':100}]
  pins,available,issues=m.admit(tags,{'qwen3:1.7b':m.QWEN})
  self.assertEqual(set(available),{'qwen3:1.7b','gemma3:1b'})
  self.assertEqual(pins['gemma3:1b'],'a'*64)
  self.assertNotIn('unapproved:1b',pins)
  tags[1]['digest']='c'*64
  new,avail,issues=m.admit(tags,pins)
  self.assertEqual(new['gemma3:1b'],'a'*64)
  self.assertNotIn('gemma3:1b',avail)
  self.assertIn('gemma3:1b',issues)
 def test_new_model_is_priority(self):
  a={'qwen3:1.7b':m.QWEN,'gemma3:1b':'a'*64,'qwen2.5-coder:1.5b':'b'*64}
  self.assertEqual(m.choose(a,{'qwen3:1.7b','gemma3:1b'},100),'qwen2.5-coder:1.5b')
 def test_reject_oversized_and_bad_digest(self):
  p,a,e=m.admit([{'name':'gemma3:1b','digest':'z'*64,'size':806067407},{'name':'qwen2.5-coder:1.5b','digest':'a'*64,'size':9*1024**3}],{})
  self.assertEqual(a,{})
  self.assertEqual(set(e),{'gemma3:1b','qwen2.5-coder:1.5b'})
 def test_unknown_persisted_pin_refused(self):
  with self.assertRaises(ValueError):m.admit([],{'random:tag':'a'*64})
if __name__=='__main__':unittest.main()
