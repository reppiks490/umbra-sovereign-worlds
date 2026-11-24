import argparse
import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / 'scripts' / 'umbra_evolution_mesh.py'
spec = importlib.util.spec_from_file_location('umbra_evolution_mesh', SRC)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class EvolutionMeshTests(unittest.TestCase):
    def test_exact_catalog_and_boundaries(self):
        result = m.validate_space(full=True)
        self.assertEqual(result['algorithm_specs'], 250_000)
        self.assertEqual(result['logical_workflow_identities'], 195_000)
        self.assertEqual(m.recipe(250_000)['id'], 'A250000')
        self.assertEqual(m.workflow(195_000)['id'], 'E195000')
        for invalid in (0,-1,250_001):
            with self.assertRaises(ValueError): m.recipe(invalid)
        for invalid in (0,-1,195_001):
            with self.assertRaises(ValueError): m.workflow(invalid)

    def test_distinct_25_operators_and_determinism(self):
        seen = set()
        for i in range(25):
            alg = m.recipe(1 + i*10_000)
            seen.add((alg['family'],alg['optimizer']))
            wf = {'id': f'E{i+1:06d}', 'index': i+1, 'domain': 'ecology', 'algorithm_id': 1+i*10_000}
            a=m.train(wf,hour='2026-11-23T19',steps=4)
            b=m.train(wf,hour='2026-11-23T19',steps=4)
            self.assertEqual(a,b)
            receipt=a.pop('receipt_sha256');self.assertEqual(receipt,m.digest(a))
            self.assertFalse(a['deployment_authorized'])
            self.assertFalse(a['real_model_weight_training'])
            self.assertEqual(len(a['parameters']),8)
        self.assertEqual(len(seen),25)

    def test_shard_partition_exactly_once(self):
        for n in (1,2,3,7,256):
            sizes = [len(range(1+k,m.WORKFLOW_COUNT+1,n)) for k in range(n)]
            self.assertEqual(sum(sizes),m.WORKFLOW_COUNT)
            self.assertLessEqual(max(sizes)-min(sizes),1)

    def test_persistent_receipts_and_peer_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/'db.sqlite3';output=Path(tmp)/'out.jsonl'
            args=argparse.Namespace(hour='2026-11-23T19',shards=1,shard=0,limit=14,steps=4,ledger=str(db),output=str(output))
            a=m.run_batch(args)
            self.assertEqual(a['processed'],14)
            lines=[json.loads(x) for x in output.read_text().splitlines()]
            self.assertEqual(len(lines),14)
            self.assertFalse(lines[13]['peer_used'])  # same-hour records cannot be treated as prior evidence
            self.assertFalse(lines[0]['peer_used'])
            self.assertEqual(len({x['workflow'] for x in lines}),14)
            self.assertEqual(sqlite3.connect(db).execute('SELECT COUNT(*) FROM runs').fetchone()[0],14)
            # A genuine previously evaluated candidate can participate next hour.
            prev=m.train(m.workflow(14),hour='2026-11-23T18',steps=8)
            self.assertEqual(prev['review_status'],'candidate_for_manual_review')
            with m.connect(db) as handle:
                handle.execute('INSERT INTO runs VALUES(?,?,?,?,?)',
                               (prev['hour'],prev['workflow'],prev['domain'],prev['receipt_sha256'],json.dumps(prev)))
                self.assertEqual(m.peer_for(handle,m.workflow(1),'2026-11-23T19'),prev['parameters'])
            b=m.run_batch(args)
            self.assertEqual(b['processed'],14)
            self.assertEqual(b['duplicate_ids_skipped'],14)
            self.assertEqual(sqlite3.connect(db).execute('SELECT COUNT(*) FROM runs').fetchone()[0],29)

    def test_bad_peer_receipt_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=m.connect(Path(tmp)/'x.sqlite3');wf=m.workflow(14)
            fraud={'parameters':[0.5]*8,'receipt_sha256':'forged'}
            db.execute('INSERT INTO runs(hour,workflow,domain,receipt,record) VALUES(?,?,?,?,?)',
                       ('2026-11-23T18','E000001',wf['domain'],'forged',json.dumps(fraud)))
            db.commit()
            with self.assertRaisesRegex(ValueError,'tampered'): m.peer_for(db,wf,'2026-11-23T19')
            db.close()

    def test_invalid_batch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            kwargs=dict(hour='2026-11-23T19',shards=2,shard=3,limit=1,steps=8,ledger=str(Path(tmp)/'db'),output=str(Path(tmp)/'out'))
            with self.assertRaises(ValueError):m.run_batch(argparse.Namespace(**kwargs))
            kwargs['shard']=1;kwargs['hour']='not-an-hour'
            with self.assertRaises(ValueError):m.run_batch(argparse.Namespace(**kwargs))
            with self.assertRaises(ValueError):m.train(m.workflow(1),hour='2026-11-23T19',steps=65)


if __name__=='__main__':
    unittest.main()
