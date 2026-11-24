import unittest
import evolution_teacher_supervisor_v41 as m
class Tests(unittest.TestCase):
 def test_schedule_keeps_worker_capacity(self):
  phases=[m.phase(8,i) for i in range(0,60,5)]
  self.assertEqual(phases.count('worker'),10)
  self.assertEqual(phases.count('teacher'),1)
  self.assertEqual(phases.count('retrieval'),1)
 def test_alternate_hours(self):
  self.assertEqual(m.phase(9,30),'small_teacher')
  self.assertEqual(m.phase(9,0),'teacher')
 def test_compressed_teacher_gate(self):
  self.assertTrue(m.compressed_admit(4800,8000,False))
  self.assertFalse(m.compressed_admit(4100,8000,False))
  self.assertFalse(m.compressed_admit(4800,8000,True))
 def test_model_choice_prefers_unused(self):
  self.assertEqual(m.select_small({'granite4:350m','deepseek-r1:1.5b','qwen3:1.7b'},{'qwen3:1.7b'},0),'granite4:350m')
  self.assertEqual(m.select_small({'deepseek-r1:1.5b','qwen3:1.7b'},{'granite4:350m','qwen3:1.7b'},0),'deepseek-r1:1.5b')
if __name__=='__main__':unittest.main()
