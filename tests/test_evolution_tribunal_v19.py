"""Anti-contamination, forged evidence, cross-domain links and replay tests."""
import copy,json,sqlite3,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import umbra_evolution_mesh as mesh
import evolution_tribunal_v19 as tribunal

class TribunalTests(unittest.TestCase):
    def test_independent_replay_and_receipt_verification(self):
        for i in (1,10,13,100,8888,195000):
            obj=mesh.train(mesh.workflow(i),hour='2026-11-23T19',steps=3)
            review=tribunal.verify_record(obj)
            self.assertTrue(review['replay_passed'])
            self.assertFalse(review['independent_real_world_certification'])

    def test_tampering_fails_even_with_recomputed_hash(self):
        evidence=mesh.train(mesh.workflow(1),hour='2026-11-23T19',steps=3)
        attacks=[('domain','health'),('real_model_weight_training',True),('deployment_authorized',True),
                 ('novelty_claim',True),('review_status','candidate_for_manual_review'),('parameters',[1]*8),
                 ('hour','2026-13-43T19')]
        for key,wrong in attacks:
            obj=copy.deepcopy(evidence);obj[key]=wrong
            obj.pop('receipt_sha256');obj['receipt_sha256']=mesh.digest(obj)
            if wrong==evidence[key]:continue
            with self.assertRaises(ValueError,msg=key):tribunal.verify_record(obj)

    def test_sampled_sqlite_receipt_replay(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'runs.db'
            conn=mesh.connect(path)
            for i in range(1,22):
                p=mesh.train(mesh.workflow(i),hour='2026-11-23T18',steps=3)
                conn.execute('INSERT INTO runs VALUES(?,?,?,?,?)',(p['hour'],p['workflow'],p['domain'],p['receipt_sha256'],json.dumps(p)))
            conn.commit();conn.close()
            out=tribunal.audit(path,sample=13,seed=1)
            self.assertEqual(out['passed'],13)
            self.assertEqual(out['failed'],0)
            self.assertEqual(out['inspected'],13)
            self.assertEqual(tribunal.audit(path,sample=13,seed=1),out)

    def test_cross_domain_only_older_verified_candidates(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'runs.db';db=mesh.connect(path)
            for i in range(1,150):
                o=mesh.train(mesh.workflow(i),hour='2026-11-23T18',steps=8)
                db.execute('INSERT INTO runs VALUES(?,?,?,?,?)',(o['hour'],o['workflow'],o['domain'],o['receipt_sha256'],json.dumps(o)))
            db.commit();db.close()
            report=tribunal.collaboration(path,1,'2026-11-23T19',limit=3)
            self.assertTrue(all(x['domain']!=mesh.workflow(1)['domain'] for x in report['verified_cross_domain_peers']))
            self.assertTrue(all(x['hour']<'2026-11-23T19' for x in report['verified_cross_domain_peers']))
            self.assertEqual(tribunal.collaboration(path,1,'2026-11-23T18')['verified_cross_domain_peers'],[])
            self.assertFalse(report['auto_integrate'])

    def test_contiguous_audit_aggregate_rejects_gaps_and_tampering(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'runs.db';db=mesh.connect(path)
            for i in range(1,22):
                obj=mesh.train(mesh.workflow(i),hour='2026-11-23T18',steps=3)
                db.execute('INSERT INTO runs VALUES(?,?,?,?,?)',(obj['hour'],obj['workflow'],obj['domain'],obj['receipt_sha256'],json.dumps(obj)))
            db.commit();db.close()
            paths=[]
            for a,b in ((1,10),(11,21)):
                x=tribunal.audit(path,row_start=a,row_end=b)
                self.assertEqual(x['passed'],b-a+1)
                f=Path(d)/f'{a}-{b}.json';f.write_text(json.dumps(x));paths.append(f)
            result=tribunal.combine_reports(paths,expected_count=21)
            self.assertEqual(result['independently_verified_receipt_records'],21)
            self.assertEqual(result['quarantined_candidates']+result['rejected_candidates'],21)
            with self.assertRaisesRegex(ValueError,'coverage'):
                tribunal.combine_reports([paths[1]],expected_count=21)
            bad=json.loads(paths[1].read_text());bad['failed']=1;paths[1].write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError,'Tampered'):
                tribunal.combine_reports(paths,expected_count=21)

    def test_bad_schema_lease_or_forward_time_rejected(self):
        for wf in (0,195001):
            with self.assertRaises(ValueError):mesh.workflow(wf)
        with self.assertRaises(ValueError):tribunal.verify_record({})
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'db';mesh.connect(p).close()
            with self.assertRaises(ValueError):tribunal.collaboration(p,1,'not a UTC hour')
            with self.assertRaises(ValueError):tribunal.audit(p,sample=1)

if __name__=='__main__':unittest.main()
