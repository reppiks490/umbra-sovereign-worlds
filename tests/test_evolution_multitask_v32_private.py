"""Optional local-only private-checkpoint adversarial tests, not CI with public code."""
from __future__ import annotations
import copy,json,pathlib,shutil,tempfile,unittest,sys,os
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import evolution_multitask_v32 as m

ARCHIVE=pathlib.Path('/mnt/data/MYRIAD_OMEGA_v2.5_PRIVATE_TRAINED_SYNTHETIC_CANDIDATES.zip')
CAND=pathlib.Path('/mnt/data/myriad_multitask_v32_private')

@unittest.skipUnless(ARCHIVE.is_file() and CAND.is_dir(),'Private research artifacts unavailable')
class PrivateWeightAttacks(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.path=pathlib.Path(self.temp.name)/'candidates'
  shutil.copytree(CAND,self.path)
  self.doc=self.path/'SYNTHETIC_TRANSFER_V32.json'
 def reseal(self,rec):
  rec.pop('receipt_sha256',None)
  rec['receipt_sha256']=m.sha(m.canonical(rec))
  self.doc.write_text(json.dumps(rec,sort_keys=True,indent=2)+'\n')
 def test_valid_saved_cohort(self):
  self.assertEqual(m.verify(ARCHIVE,self.path)['agents'],10)
 def test_resealed_cross_score_is_still_rejected(self):
  r=json.loads(self.doc.read_text());r['rows'][0]['candidate_metrics']['cross']['model_mse']=0.0
  self.reseal(r)
  with self.assertRaises(ValueError):m.verify(ARCHIVE,self.path)
 def test_forged_source_hash_rejected(self):
  r=json.loads(self.doc.read_text());r['rows'][0]['source_sha256']='f'*64
  self.reseal(r)
  with self.assertRaises(ValueError):m.verify(ARCHIVE,self.path)
 def test_model_byte_corruption_rejected(self):
  f=self.path/'AG-00001.synthetic_multitask_v32.fp16';b=bytearray(f.read_bytes());b[100]^=1;f.write_bytes(b)
  with self.assertRaises(ValueError):m.verify(ARCHIVE,self.path)
if __name__=='__main__':unittest.main()
