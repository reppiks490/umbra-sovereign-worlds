import unittest
import evolution_continuous_v53 as m
class Tests(unittest.TestCase):
 def test_phases_preserve_teacher_and_fleet(self):
  v=[m.phase(h,k) for h in range(24) for k in range(0,60,5)]
  self.assertEqual(v.count('fleet'),48)
  self.assertEqual(v.count('teacher'),24)
  self.assertEqual(v.count('retrieval'),12)
  self.assertEqual(v.count('ability_bank'),24)
  self.assertEqual(v.count('agent_bank'),24)
  self.assertEqual(v.count('benchmark'),4)
 def test_guard(self):
  self.assertFalse(m.admit(2500,10*1024**3,False))
  self.assertFalse(m.admit(4000,4*1024**3,False))
  self.assertFalse(m.admit(4000,10*1024**3,True))
  self.assertTrue(m.admit(4000,10*1024**3,False))
if __name__=='__main__':unittest.main()
