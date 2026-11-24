import unittest
from unittest.mock import patch
import evolution_quality_supervisor_v59 as m
class Tests(unittest.TestCase):
 def test_preserves_all_core_windows(self):
  phases=[m.phase(h,i) for h in range(24) for i in range(0,60,5)]
  self.assertEqual(phases.count('teacher'),24)
  self.assertEqual(phases.count('fleet'),48)
  self.assertEqual(phases.count('distill'),6)
  self.assertEqual(phases.count('evolve_agents'),12)
  self.assertEqual(phases.count('ability_bank'),18)
  self.assertEqual(phases.count('agent_bank'),12)
  self.assertEqual(phases.count('benchmark'),4)
 def test_admission(self):
  self.assertFalse(m.admit(3000,10*1024**3,False))
  self.assertFalse(m.admit(5000,10*1024**3,True))
  self.assertTrue(m.admit(5000,10*1024**3,False))
 def test_manual_reasoning_preserves_schedule(self):
  import evolution_reasoning_runtime_v82 as r
  with patch.object(r,'run',return_value={'status':'completed'}) as call:
   self.assertEqual(m.run('private',9000,'novel_reasoning'),{'status':'completed'})
   call.assert_called_once_with('private',9000)
  self.assertNotIn('novel_reasoning',[m.phase(h,i) for h in range(24) for i in range(0,60,5)])
if __name__=='__main__':unittest.main()
