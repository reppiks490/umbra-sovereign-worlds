import json,tempfile,unittest,hashlib
from pathlib import Path
import evolution_retrieval_review_v42 as m
class Tests(unittest.TestCase):
 def test_source_digest_and_line_binding(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);f=p/'evolution_model_queue_v26.py';f.write_text('def claim():\n    return None\n')
   hit={'file':f.name,'function':'claim','source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'similarity':.8}
   packet=m.packet(p,hit,'lease ownership')
   self.assertEqual(packet['source']['lines'],[1,2])
   self.assertTrue(m.assess(packet,json.dumps({'finding':'Claim returns none.','line':2,'experiment':'Call claim once.','risk':'No lease returned.'}))['valid_structure'])
   f.write_text('def claim():\n    return 2\n')
   with self.assertRaises(ValueError):m.packet(p,hit,'lease ownership')
 def test_path_outside_allowlist_rejected(self):
  with self.assertRaises(ValueError):m.packet(Path('.'),{'file':'../secret','function':'x','source_sha256':'a'*64},'lease')
 def test_rotation(self):
  self.assertEqual(len({m.query(i) for i in range(6)}),6)
  self.assertEqual(m.query(0),m.query(6))
if __name__=='__main__':unittest.main()
