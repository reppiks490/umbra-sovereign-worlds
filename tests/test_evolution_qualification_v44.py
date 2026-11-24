import unittest
import evolution_qualification_v44 as m
class Tests(unittest.TestCase):
 def test_preserves_existing_phases_except_four_benchmark_windows(self):
  phases=[m.phase(h,i) for h in range(24) for i in range(0,60,5)]
  self.assertEqual(phases.count('teacher'),24)
  self.assertEqual(phases.count('retrieval'),12)
  self.assertEqual(phases.count('small_teacher'),12)
  self.assertEqual(phases.count('benchmark'),4)
  self.assertEqual(phases.count('worker'),236)
 def test_selects_new_model_before_repeats(self):
  self.assertEqual(m.select({'gemma3:1b','qwen3:1.7b'},{'qwen3:1.7b'}),'gemma3:1b')
  self.assertIsNone(m.select({'gemma3:1b'},{'gemma3:1b'}))
 def test_seed_shared_across_same_week(self):
  self.assertEqual(m.seed_for(604800),m.seed_for(604800+86400))
  self.assertNotEqual(m.seed_for(604800),m.seed_for(1209600))
if __name__=='__main__':unittest.main()
