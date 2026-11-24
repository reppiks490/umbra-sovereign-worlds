"""v2.7 model-artifact-bound fresh holdout tests. No private weights required in CI."""
import copy
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import evolution_neural_probe_v27 as probe


class NeuralProbeV27Tests(unittest.TestCase):
    def test_new_holdout_seed_must_not_reuse_training_stream(self):
        with self.assertRaises(ValueError):
            probe.check_seed(1337, 1337)
        with self.assertRaises(ValueError):
            probe.check_seed(1337, 2300)
        self.assertEqual(probe.check_seed(1337, 900000), 900000)

    def test_model_digest_must_match_real_weight_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'candidate.fp16'
            p.write_bytes(b'\x00\x3c\x00\x40')
            expected = hashlib.sha256(p.read_bytes()).hexdigest()
            self.assertEqual(probe.check_file_digest(p, expected, 4), expected)
            with self.assertRaises(ValueError):
                probe.check_file_digest(p, '0'*64, 4)
            p.write_bytes(b'\x01\x3c\x00\x40')
            with self.assertRaises(ValueError):
                probe.check_file_digest(p, expected, 4)

    def test_symlink_is_never_accepted_as_candidate(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'source.fp16';p.write_bytes(b'1234')
            link=Path(d)/'candidate.fp16'
            link.symlink_to(p)
            with self.assertRaises(ValueError):
                probe.check_file_digest(link, hashlib.sha256(b'1234').hexdigest(), 4)

    def test_invalid_evaluation_metric_is_rejected(self):
        with self.assertRaises(ValueError):
            probe.proof_metric(0.5, float('nan'))
        with self.assertRaises(ValueError):
            probe.proof_metric(0.5, -0.1)
        self.assertEqual(probe.proof_metric(1.0, 0.75)['candidate_improved'], True)

    def test_completed_receipt_has_no_claim_of_model_identity(self):
        result=probe.finalize_probe({'source_hash':'abc','agent_evaluations':[]}, 900000)
        self.assertFalse(result['model_identity_authenticated'])
        self.assertFalse(result['production_authority'])
        self.assertFalse(result['trading_alpha_certified'])
        self.assertEqual(result['probe_seed'],900000)
        self.assertTrue(probe.verify_seal(result))

    def test_overstated_authority_rejected_even_with_resealed_digest(self):
        r=probe.finalize_probe({'source_hash':'abc','agent_evaluations':[]},900000)
        r['production_authority']=True
        r['receipt_sha256']=probe.sha(probe.canonical({k:v for k,v in r.items() if k!='receipt_sha256'}))
        with self.assertRaises(ValueError):
            probe.verify_seal(r)

    def test_digest_tampering_and_duplicate_json_keys_rejected(self):
        r=probe.finalize_probe({'source_hash':'abc','agent_evaluations':[]},900000)
        r['source_hash']='def'
        with self.assertRaises(ValueError):
            probe.verify_seal(r)
        with self.assertRaises(ValueError):
            probe.read_strict_json('{"source_hash":"a","source_hash":"b"}')

    def test_metric_mismatch_fails_external_recalculation(self):
        probe.assert_close_recomputed(0.571234,0.571233)
        with self.assertRaises(ValueError):
            probe.assert_close_recomputed(0.571234, 0.574)

    def test_write_is_exclusive_and_does_not_overwrite_receipts(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'report.json'
            r=probe.finalize_probe({'source_hash':'abc','agent_evaluations':[]},900000)
            probe.write_receipt(target,r)
            before=target.read_bytes()
            with self.assertRaises(FileExistsError):
                probe.write_receipt(target,r)
            self.assertEqual(target.read_bytes(),before)


if __name__=='__main__':
    unittest.main()
