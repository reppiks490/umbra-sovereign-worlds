import unittest
import evolution_quality_supervisor_v59 as m
class ResourceTests(unittest.TestCase):
 def test_distill_low_ram_but_enough_virtual_memory(self):
  self.assertTrue(m.admit_window('distill',2600,10000,10*1024**3,False))
 def test_heavier_training_not_relaxed(self):
  self.assertFalse(m.admit_window('evolve_agents',2600,10000,10*1024**3,False))
 def test_memory_disk_and_residency_guards(self):
  for args in [(2200,10000,10*1024**3,False),(3000,4000,10*1024**3,False),(3000,10000,1024**3,False),(3000,10000,10*1024**3,True)]:
   self.assertFalse(m.admit_window('distill',*args))
 def test_unknown_mode(self):
  with self.assertRaises(ValueError):m.admit_window('unknown',5000,10000,10*1024**3,False)
if __name__=='__main__':unittest.main()
