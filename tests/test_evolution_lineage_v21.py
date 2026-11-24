"""No same-hour leakage, forged parent, invalid review or absent lineage."""
import argparse,json,sqlite3,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import umbra_evolution_mesh as mesh
import evolution_scheduler as sched
from evolution_lineage_v21 import validate_child, audit,SCHEMA

class LineageTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.path=Path(self.temp.name)/'evidence.sqlite3'
  self.db=sched.open_db(self.path)
  self.addCleanup(self.db.close)
  parent=mesh.train(mesh.workflow(14),hour='2026-11-23T18',steps=8)
  assert parent['review_status']=='candidate_for_manual_review'
  self.parent=parent
  self.db.execute('INSERT INTO runs VALUES(?,?,?,?,?)',(parent['hour'],parent['workflow'],parent['domain'],parent['receipt_sha256'],json.dumps(parent)))
  child=mesh.train(mesh.workflow(1),hour='2026-11-23T19',steps=4,peer=parent['parameters'])
  child['peer_used']=True;child['peer_provenance_schema']=SCHEMA
  child['peer_parent']={'parent_workflow':parent['workflow'],'parent_hour':parent['hour'],'parent_receipt_sha256':parent['receipt_sha256'],'parent_domain':parent['domain']}
  child.pop('receipt_sha256');child['receipt_sha256']=mesh.digest(child)
  self.child=child

 def test_real_previous_hour_parent_verified(self):
  v=validate_child(self.db,self.child)
  self.assertEqual(v['status'],'verified_prior_hour')
  self.assertEqual(v['source_receipt_sha256'],self.parent['receipt_sha256'])
  self.db.execute('INSERT INTO runs VALUES(?,?,?,?,?)',(self.child['hour'],self.child['workflow'],self.child['domain'],self.child['receipt_sha256'],json.dumps(self.child)))
  result=audit(self.path,limit=2)
  self.assertEqual(result['inspected'],2)
  self.assertEqual(result['categories']['verified_prior_hour'],1)
  self.assertEqual(result['categories']['failed'],0)

 def test_real_mesh_run_emits_provenance_for_prior_hour_candidate(self):
  self.db.close()
  output=Path(self.temp.name)/'jobs.jsonl'
  args=argparse.Namespace(hour='2026-11-23T19',shards=1,shard=0,limit=14,
                          steps=4,ledger=str(self.path),output=str(output))
  result=mesh.run_batch(args)
  self.assertEqual(result['processed'],14)
  records=[json.loads(line) for line in output.read_text().splitlines()]
  self.assertTrue(all(r['peer_provenance_schema']==SCHEMA for r in records))
  self.assertTrue(any(r['peer_used'] for r in records))
  for record in records:
   with sqlite3.connect(self.path) as db:
    reviewed=validate_child(db,record)
    self.assertEqual(reviewed['status'],'verified_prior_hour' if record['peer_used'] else 'no_prior_parent')

 def test_same_hour_parent_rejected_even_if_child_rehashed(self):
  altered=json.loads(json.dumps(self.child))
  altered['peer_parent']['parent_hour']=self.child['hour']
  altered.pop('receipt_sha256');altered['receipt_sha256']=mesh.digest(altered)
  with self.assertRaisesRegex(ValueError,'same-hour'):validate_child(self.db,altered)

 def test_parent_digest_forgery_rejected(self):
  altered=json.loads(json.dumps(self.child));altered['peer_parent']['parent_receipt_sha256']='0'*64
  altered.pop('receipt_sha256');altered['receipt_sha256']=mesh.digest(altered)
  with self.assertRaisesRegex(ValueError,'Parent hash'):validate_child(self.db,altered)

 def test_missing_parent_rejected(self):
  self.db.execute('DELETE FROM runs')
  with self.assertRaisesRegex(ValueError,'Missing parent'):validate_child(self.db,self.child)

 def test_legacy_peer_evidence_is_not_backfilled(self):
  legacy=mesh.train(mesh.workflow(1),hour='2026-11-23T19',steps=4)
  legacy['peer_used']=True;legacy.pop('receipt_sha256');legacy['receipt_sha256']=mesh.digest(legacy)
  self.assertEqual(validate_child(self.db,legacy)['status'],'legacy_unproven')

 def test_no_peer_is_verifiably_distinct(self):
  p=mesh.train(mesh.workflow(1),hour='2026-11-23T19',steps=3)
  p['peer_used']=False;p['peer_provenance_schema']=SCHEMA;p['peer_parent']=None
  p.pop('receipt_sha256');p['receipt_sha256']=mesh.digest(p)
  self.assertEqual(validate_child(self.db,p)['status'],'no_prior_parent')

if __name__=='__main__':unittest.main()
