"""Failing-first regressions for the native training disk reserve."""
import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))

from training_storage_admission import training_storage_admitted
import native_student
import source_assist
import source_training_schedule


class TrainingStorageAdmissionTest(unittest.TestCase):
    def test_floor_preserved_after_planned_training_growth(self):
        self.assertFalse(training_storage_admitted(8_100_000_000))
        self.assertFalse(training_storage_admitted(8_199_999_999))
        self.assertTrue(training_storage_admitted(8_200_000_000))

    def test_bootstrap_reservation_is_additive(self):
        self.assertFalse(training_storage_admitted(8_200_000_000, outstanding_bootstrap_bytes=1))
        self.assertTrue(training_storage_admitted(9_200_000_000, outstanding_bootstrap_bytes=1_000_000_000))

    def test_reject_invalid_admission_values(self):
        for value in (-1, True, 2.5, None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    training_storage_admitted(value)
        with self.assertRaises(ValueError):
            training_storage_admitted(9_000_000_000, planned_growth_bytes=-1)
        with self.assertRaises(ValueError):
            training_storage_admitted(9_000_000_000, outstanding_bootstrap_bytes=True)

    def test_scheduler_defers_before_runtime_checks_at_8_point_1_gb(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / 'root'
            training = pathlib.Path(tmp) / 'training'
            root.mkdir()
            training.mkdir()
            with mock.patch.object(source_training_schedule, 'local_api', return_value={'models': []}), \
                 mock.patch.object(source_training_schedule.shutil, 'disk_usage', return_value=SimpleNamespace(free=8_100_000_000)):
                result = source_training_schedule.run(root, training)
            self.assertEqual(result['status'], 'deferred_storage')
            self.assertTrue(result['source_only'])

    def test_native_trainer_defers_before_creating_training_bank(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / 'root'
            training = pathlib.Path(tmp) / 'training'
            (root / 'experience').mkdir(parents=True)
            training.mkdir()
            with mock.patch.object(source_assist, 'local_api', return_value={'models': []}), \
                 mock.patch.object(native_student.shutil, 'disk_usage', return_value=SimpleNamespace(free=8_100_000_000)):
                result = native_student.train(root, training, 'granite4:350m')
            self.assertEqual(result['status'], 'deferred_storage')
            self.assertFalse((root / 'experience' / 'source-lora').exists())


if __name__ == '__main__':
    unittest.main()
