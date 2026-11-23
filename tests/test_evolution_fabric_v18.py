"""No external services, no paid model calls, no broker authority."""
import importlib.util, json, os, sqlite3, tempfile, unittest, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def load(mod):
 spec=importlib.util.spec_from_file_location(mod,ROOT/'scripts'/f'{mod}.py')
 obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
import sys
sys.path.insert(0,str(ROOT/'scripts'))
import evolution_scheduler as s
import myriad_bank_fabric as b
import evolution_source_registry as r
import evolution_api as api
import umbra_evolution_mesh as mesh


class FabricTests(unittest.TestCase):
 def test_expanded_banks_exact_geometry(self):
  p=b.plan();self.assertEqual(p['target_agent_bytes'],30_000_000_000)
  self.assertEqual(p['target_ability_bytes'],10_000_000_000)
  self.assertEqual(p['source_agent_bytes'],8_220_000_000)
  self.assertEqual(p['source_ability_bytes'],640_000_000)
  self.assertEqual(p['agent_additional_parameters_per_identity'],1_089_000)
  self.assertEqual(p['ability_additional_parameters_per_identity'],468)
  self.assertFalse(p['expanded_weights_trained'])
 def test_incomplete_bank_must_never_create_extensions(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);a=root/'a';a.mkdir();w=root/'w';w.mkdir();out=root/'out'
   (a/'agent_weights.fp16').write_bytes(b'not original')
   with self.assertRaises((FileNotFoundError,ValueError)):
    b.provision(a,w,out,approve=True)
   self.assertFalse(out.exists())
 def test_source_metadata_licensed_gate(self):
  rows=list(r.entries());ids=[x['source_method_id'] for x in rows]
  self.assertEqual(len(set(ids)),len(ids))
  self.assertGreaterEqual(len(rows),95)
  self.assertTrue(all(x['source_code_copied'] is False and x['license_audit']=='required_before_code_reuse' for x in rows))
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'manifest.json';p.write_text(json.dumps([{'url':'https://github.com/DEAP/deap','title':'NSGA II'}]))
   out=r.ingest(p,Path(d)/'sources.db');self.assertEqual(out['new_quarantined_source_candidates'],1)
   self.assertEqual(r.ingest(p,Path(d)/'sources.db')['new_quarantined_source_candidates'],0)
   p.write_text('[{"url":"file:///etc/passwd","title":"bad"}]')
   with self.assertRaises(ValueError):r.ingest(p,Path(d)/'sources.db')
 def test_identities_single_hour_retries_recovery(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'db';base=1_795_460_000
   init=s.initialize(path,start_at=base)
   self.assertEqual(init['registered_identities'],195_000)
   self.assertFalse(s.initialize(path,start_at=base)['created'])
   now=base+3599
   before=s.status(path,now);self.assertEqual(before['overdue'],195_000)
   out=s.process(path,max_jobs=16,steps=4,owner='worker-A',clock=now)
   self.assertEqual(out['completed_this_invocation'],16)
   self.assertEqual(len(out['receipts']),16)
   self.assertEqual(s.status(path,now)['completed_occurrences'],16)
   # Concurrent claim transactions cannot return the same still-leased identity.
   db=s.open_db(path)
   first=s.claim(db,'owner-B',now)
   second=s.claim(db,'owner-C',now)
   self.assertNotEqual(first,second)
   before_count=db.execute('SELECT COUNT(*) FROM proposals').fetchone()[0]
   with self.assertRaises(ValueError):s.finish(db,'wrong-owner',first[0],first[1],{'workflow':'bogus'},now)
   self.assertEqual(db.execute('SELECT COUNT(*) FROM proposals').fetchone()[0],before_count)
   db.close()
 def test_api_metrics_uses_actual_recorded_runs(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'sqlite3';m=api.overview(p)
   self.assertEqual(m['recorded_research_runs'],0)
   self.assertEqual(m['logical_worker_identities'],195_000)
   self.assertFalse(m['production_writes_authorized'])
   s.initialize(p,start_at=1795460000)
   s.process(p,max_jobs=5,steps=3,owner='test',clock=1795463599)
   self.assertEqual(api.overview(p)['recorded_research_runs'],5)
   w=api.worker_status(p,3600);self.assertEqual(w['id'],'E003600')
   self.assertEqual(w['recorded_runs'],1)


if __name__=='__main__':unittest.main()