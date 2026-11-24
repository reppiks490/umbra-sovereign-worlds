import unittest
import evolution_supervisor_v50 as m
class Tests(unittest.TestCase):
 def test_fleet_windows_preserve_teachers(self):
  phases=[m.phase(h,i) for h in range(24) for i in range(0,60,5)]
  self.assertEqual(phases.count('fleet'),48)
  self.assertEqual(phases.count('teacher'),24)
  self.assertEqual(phases.count('retrieval'),12)
  self.assertEqual(phases.count('benchmark'),4)
 def test_capacity(self):
  self.assertEqual(m.phase(0,55),'benchmark')
  self.assertEqual(m.phase(3,30),'small_teacher')
  self.assertEqual(m.phase(3,20),'fleet')
if __name__=='__main__':unittest.main()
