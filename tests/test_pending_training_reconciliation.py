"""Prevent duplicate optimizer attempts after interrupted training reservations."""
import contextlib
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))

from source_curriculum import campaign_eligible, pending_reconciliation
from source_training_schedule import select_candidate
import native_student
import source_assist


class PendingTrainingReconciliationTest(unittest.TestCase):
    def test_interrupted_status_and_reservation_are_never_eligible(self):
        self.assertTrue(campaign_eligible({}))
        self.assertTrue(pending_reconciliation({'status': 'attempting'}))
        self.assertTrue(pending_reconciliation({'pending_attempt': 'attempt-pre-crash'}))
        self.assertFalse(campaign_eligible({'status': 'attempting', 'timestamp': 0, 'curriculum': {}}))
        self.assertFalse(campaign_eligible({'status': 'evaluated', 'pending_attempt': 'attempt-pre-crash'}))

    def test_scheduler_rotates_away_from_pending_reservations(self):
        rows = [
            {'name': 'pending', 'present': True, 'required_ram': 4_500_000_000,
             'state': {'status': 'attempting', 'pending_attempt': 'attempt-pre-crash', 'timestamp': 0}},
            {'name': 'healthy', 'present': True, 'required_ram': 4_500_000_000,
             'state': {'status': 'evaluated', 'timestamp': 5_000}}
        ]
        self.assertEqual(select_candidate(rows, 5_000_000_000, 10_000, campaign=True)['name'], 'healthy')
        self.assertIsNone(select_candidate(rows[:1], 5_000_000_000, 10_000, campaign=True))

    def test_direct_train_rejects_ambiguous_pending_attempt_before_optimizer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / 'root'
            training = pathlib.Path(tmp) / 'training'
            (root / 'experience').mkdir(parents=True)
            training.mkdir()
            name = 'granite4:350m'
            digest = 'a' * 64
            key = hashlib.sha256(name.encode()).hexdigest()[:20]
            folder = root / 'experience' / 'source-lora' / key
            folder.mkdir(parents=True)
            (folder / 'state.json').write_text(json.dumps({
                'base_sha256': digest, 'status': 'attempting',
                'pending_attempt': 'attempt-pre-crash', 'attempts': 1,
                'timestamp': 0, 'curriculum': {}
            }), encoding='utf8')
            with mock.patch.object(native_student, 'available_ram', return_value=9_000_000_000), \
                 mock.patch.object(native_student, 'checkpoint', return_value=(training / 'source', digest, 100)), \
                 mock.patch.object(native_student, 'lock', side_effect=lambda p: contextlib.nullcontext()), \
                 mock.patch.object(native_student.shutil, 'disk_usage', return_value=SimpleNamespace(free=9_000_000_000)), \
                 mock.patch.object(source_assist, 'local_api', return_value={'models': []}), \
                 mock.patch.object(native_student, 'load_corpus', side_effect=AssertionError('duplicate optimizer path')):
                result = native_student.train(root, training, name)
            self.assertEqual(result['status'], 'deferred_pending_reconciliation')
            self.assertEqual(result['pending_attempt'], 'attempt-pre-crash')


if __name__ == '__main__':
    unittest.main()
