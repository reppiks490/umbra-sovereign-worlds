import sys, pathlib, unittest, tempfile
from unittest.mock import patch
from contextlib import nullcontext
from types import SimpleNamespace
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import storage_budget as storage
import native_student as student
import source_training_schedule as schedule

class SourceTrainingDiskGate(unittest.TestCase):
    def test_scheduler_respects_retirement_floor(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d); training=root/'training'; training.mkdir()
            with patch.object(storage,'budget',return_value=storage.RETIRED), patch.object(schedule,'local_api',return_value={'models':[]}), patch.object(schedule.shutil,'disk_usage',return_value=SimpleNamespace(free=7_000_000_000)):
                self.assertEqual(schedule.run(root,training)['status'],'deferred_storage')

    def test_optimizer_rejects_before_loading_checkpoint(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d); training=root/'training'; training.mkdir()
            (root/'experience').mkdir()
            with patch.object(storage,'budget',return_value=storage.RETIRED), patch('source_assist.local_api',return_value={'models':[]}), patch.object(student.shutil,'disk_usage',return_value=SimpleNamespace(free=7_000_000_000)), patch.object(student,'checkpoint',side_effect=AssertionError('checkpoint must not be loaded below storage floor')):
                self.assertEqual(student.train(root,training,'granite4:350m')['status'],'deferred_storage')

    def test_optimizer_rechecks_after_lock_acquisition(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d); training=root/'training';training.mkdir()
            (root/'experience').mkdir()
            with patch.object(storage,'budget',return_value=storage.RETIRED), patch('source_assist.local_api',return_value={'models':[]}), patch.object(student.shutil,'disk_usage',side_effect=[SimpleNamespace(free=9_000_000_000),SimpleNamespace(free=7_000_000_000)]), patch.object(student,'checkpoint',return_value=(root,'a'*64,1000)), patch.object(student,'available_ram',return_value=10_000_000_000), patch.object(student,'lock',side_effect=lambda path:nullcontext()), patch.object(student,'campaign_eligible',return_value=True), patch.object(student,'load_corpus',side_effect=AssertionError('corpus must not be loaded below storage floor')):
                self.assertEqual(student.train(root,training,'granite4:350m')['status'],'deferred_storage')

    def test_shared_gate_preserves_legacy_floor_and_reserves_output(self):
        with patch.object(storage,'budget',return_value=storage.LEGACY):
            self.assertFalse(storage.source_training_storage_admitted(pathlib.Path('.'),5_999_999_999))
            self.assertFalse(storage.source_training_storage_admitted(pathlib.Path('.'),6_024_999_999))
            self.assertTrue(storage.source_training_storage_admitted(pathlib.Path('.'),6_025_000_000))
        with patch.object(storage,'budget',return_value=storage.RETIRED):
            self.assertFalse(storage.source_training_storage_admitted(pathlib.Path('.'),7_824_999_999))
            self.assertTrue(storage.source_training_storage_admitted(pathlib.Path('.'),7_825_000_000))
            self.assertFalse(storage.source_training_storage_admitted(pathlib.Path('.'),True))

    def test_invalid_retirement_evidence_fails_closed(self):
        with patch.object(storage,'budget',side_effect=ValueError('bad receipt')):
            self.assertFalse(storage.source_training_storage_admitted(pathlib.Path('.'),100_000_000_000))
