import sys,pathlib,tempfile,unittest
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import infinity_service as service
import native_training_bootstrap as bootstrap
import storage_budget as storage
import test_hf_weight_cache as cache_fixture

class BootstrapPolicyTest(unittest.TestCase):
 def test_scheduler_enforces_retired_floor_plus_install_reserve(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);training=root/'training'
   with patch.object(storage,'budget',return_value=storage.RETIRED),patch.object(bootstrap,'used',return_value=4_000_000_000),patch.object(service.shutil,'disk_usage',return_value=SimpleNamespace(free=8_000_000_000)),patch.object(service.subprocess,'Popen',side_effect=AssertionError('must not start')):
    self.assertEqual(service.resume_bootstrap(root,training,'ready')['status'],'deferred_storage')
 def test_bootstrap_rejects_below_retired_floor_before_writing_lock(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)
   with patch.object(bootstrap,'ROOT',root),patch.object(bootstrap,'FLOOR',25_000_000_000),patch.object(bootstrap,'after_queue_ready',return_value=True),patch.object(bootstrap,'used',return_value=4_000_000_000),patch.object(bootstrap.shutil,'disk_usage',return_value=SimpleNamespace(free=8_000_000_000)),patch.object(storage,'budget',return_value=storage.RETIRED),patch.object(bootstrap,'cmd',side_effect=AssertionError('must not install')):
    with self.assertRaisesRegex(ValueError,'headroom'):bootstrap.main(True)
    self.assertFalse((root/'bootstrap.lock').exists())
 def test_invalid_budget_fails_closed_before_spawn(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);training=root/'training'
   with patch.object(storage,'budget',side_effect=ValueError('bad retirement receipt')),patch.object(bootstrap,'used',return_value=4_000_000_000),patch.object(service.shutil,'disk_usage',return_value=SimpleNamespace(free=20_000_000_000)),patch.object(service.subprocess,'Popen',side_effect=AssertionError('must not start')):
    self.assertEqual(service.resume_bootstrap(root,training,'ready')['status'],'deferred_storage_policy')
 def test_active_bootstrap_remains_running_even_if_policy_unreadable(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);training=root/'training';training.mkdir();(training/'bootstrap.lock').write_text('active')
   with patch.object(storage,'budget',side_effect=ValueError('bad receipt')):
    self.assertEqual(service.resume_bootstrap(root,training,'ready')['status'],'running')

class CachePolicyTest(unittest.TestCase):
 setUp=cache_fixture.Test.setUp
 tearDown=cache_fixture.Test.tearDown
 def test_restore_respects_retired_floor(self):
  self.cache.evict(self.sha)
  self.cache.free=lambda:7_000_000_000
  with patch.object(storage,'budget',return_value=storage.RETIRED):
   with self.assertRaisesRegex(ValueError,'storage reserve'):self.cache.ensure(self.sha)
  self.assertFalse(self.weight.exists())
  self.assertEqual(self.cache.list()[0]['status'],'remote')
