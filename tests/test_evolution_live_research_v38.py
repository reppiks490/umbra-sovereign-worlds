import json,tempfile,unittest,sqlite3
from pathlib import Path
import evolution_live_research_v38 as m
class LiveTests(unittest.TestCase):
 def test_packet_binds_actual_source_and_telemetry(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t); (root/'evolution_model_queue_v26.py').write_text('def claim(db,owner,now):\n    return None\n')
   db=sqlite3.connect(root/'queue.sqlite');db.execute('CREATE TABLE model_runs(hour,workflow,correct,evaluated_requests)');db.execute("INSERT INTO model_runs VALUES('2026-11-24T13','E000001',1,1)");db.commit();db.close()
   p=m.packet(root,root/'queue.sqlite',1,1)
   self.assertEqual(p['telemetry'][0]['distinct_workers'],1);self.assertEqual(p['source']['function'],'claim')
   self.assertIn('return None',p['source']['excerpt'])
   self.assertTrue(m.verify_packet(p))
   p['source']['excerpt']='fabricated'
   with self.assertRaises(ValueError):m.verify_packet(p)
 def test_proposal_requires_real_citation_and_inert_fields(self):
  p={'source':{'lines':[1,2]}}
  good={'finding':'Review lease recovery.','line':2,'experiment':'Replay expired leases.','risk':'Duplicate completion.'}
  self.assertTrue(m.assess(p,json.dumps(good))['valid_structure'])
  good['line']=99
  self.assertFalse(m.assess(p,json.dumps(good))['valid_structure'])
  good['line']=2;good['command']='execute'
  self.assertFalse(m.assess(p,json.dumps(good))['valid_structure'])
 def test_invalid_identity(self):
  with self.assertRaises(ValueError):m.packet(Path('.'),Path('none'),0,1)
if __name__=='__main__':unittest.main()
