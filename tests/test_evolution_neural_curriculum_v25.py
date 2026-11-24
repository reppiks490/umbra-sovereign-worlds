"""CPU-only metadata and safety tests; separate real autograd evidence is private."""
import sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import evolution_neural_curriculum_v25 as v

class CurriculumTests(unittest.TestCase):
 def test_bank_plan_tracks_real_portable_geometry(self):
  p=v.plan()
  self.assertEqual(p['agents'],10)
  self.assertEqual(p['ability_adapters'],10_000)
  self.assertEqual(p['parameters_per_agent'],411_000)
  self.assertEqual(p['ability_parameters_per_adapter'],32)
  self.assertFalse(p['production_authority'])
  self.assertFalse(p['trained_large_banks'])
 def test_reject_invalid_budget_before_training(self):
  with tempfile.TemporaryDirectory() as d:
   src=Path(d)/'does-not-exist.zip';out=Path(d)/'out'
   for n,steps in [(0,1),(11,1),(1,0),(1,33)]:
    with self.subTest(n=n,steps=steps):
     with self.assertRaises(ValueError):v.train(src,out,n,steps,1337,authorize=True)
     self.assertFalse(out.exists())
 def test_reject_reusing_output_directory(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'out';out.mkdir();(out/'unrelated.txt').write_text('keep')
   with self.assertRaises(FileExistsError):v.train(Path(d)/'missing.zip',out,1,1,1337,authorize=True)
   self.assertEqual((out/'unrelated.txt').read_text(),'keep')
 def test_reject_missing_archive_without_creating_output(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'out'
   with self.assertRaises((FileNotFoundError,ValueError)):
    v.train(Path(d)/'missing.zip',out,1,1,1337,authorize=True)
   self.assertFalse(out.exists())
 def test_no_run_without_explicit_selection(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(PermissionError):
    v.train(Path(d)/'missing.zip',Path(d)/'out',1,1,1337,authorize=False)

if __name__=='__main__':unittest.main()
