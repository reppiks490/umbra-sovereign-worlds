import unittest,sys,pathlib,tempfile,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from acquisition_recovery import plan_recovery,remaining_bytes
from native_training_bootstrap import torch_ready
class RecoveryTest(unittest.TestCase):
 def test_resume_preserves_reserve_and_active_pull(self):
  self.assertEqual(plan_recovery(False,True,False,False,33000000000,4284562036)['status'],'pull_running')
  self.assertEqual(plan_recovery(False,False,False,False,33000000000,4284562036)['status'],'resume_q8')
  self.assertEqual(plan_recovery(False,False,False,False,27000000000,4284562036)['status'],'deferred_storage')
  self.assertEqual(plan_recovery(False,False,False,False,33000000000,None)['status'],'deferred_partial_identity')
 def test_queue_restarts_only_after_q8_and_not_after_completion(self):
  self.assertEqual(plan_recovery(True,False,False,False,28000000000,0)['status'],'resume_queue')
  self.assertEqual(plan_recovery(True,False,True,False,28000000000,0)['status'],'queue_running')
  self.assertEqual(plan_recovery(True,False,False,True,28000000000,0)['status'],'complete')
  self.assertEqual(plan_recovery(True,False,False,False,24000000000,0)['status'],'deferred_queue_storage')
 def test_validate_partial_segments(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)
   for n in range(2):
    (p/('sha256-x-partial-'+str(n))).write_text(json.dumps({'N':n,'Offset':n*10,'Size':10,'Completed':5}))
   self.assertEqual(remaining_bytes(p,'sha256-x',20),10)
   (p/'sha256-x-partial-1').write_text(json.dumps({'N':1,'Offset':9,'Size':10,'Completed':5}))
   self.assertIsNone(remaining_bytes(p,'sha256-x',20))
 def test_already_installed_cpu_torch_is_reused(self):
  from unittest.mock import patch
  with patch('native_training_bootstrap.subprocess.run') as run:
   run.return_value.returncode=0
   self.assertTrue(torch_ready(pathlib.Path('python.exe')))
   run.return_value.returncode=1
   self.assertFalse(torch_ready(pathlib.Path('python.exe')))
