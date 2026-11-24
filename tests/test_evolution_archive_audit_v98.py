import hashlib,json,sqlite3,struct,tempfile,unittest,zipfile,warnings
from pathlib import Path
import evolution_archive_audit_v98 as m

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def make(self,*,nonfinite=False,tamper=False,duplicate=False,invalid_manifest=False,malformed=True):
        blocks=[struct.pack('<3H',0x3c00,0x4000,0x4200),struct.pack('<3H',0x4400,0x4500,0x4600 if not nonfinite else 0x7c00)]
        p=self.root/'ledger.sqlite3';c=sqlite3.connect(p)
        c.execute('CREATE TABLE agent_weights(agent INTEGER PRIMARY KEY,status TEXT NOT NULL,steps INTEGER NOT NULL,sha256 TEXT NOT NULL,updated TEXT NOT NULL,baseline_loss REAL,final_loss REAL,heldout_loss REAL,weight_precision TEXT NOT NULL)')
        for i,b in enumerate(blocks,1):c.execute('INSERT INTO agent_weights VALUES(?,?,?,?,?,?,?,?,?)',(i,'trained',5,hashlib.sha256(b).hexdigest(),'fixture',1.0,0.5,0.7,'fp16'))
        c.commit();c.close();zpath=self.root/'pilot.zip'
        manifest=[{'agent':1,'verified':True},{'agent':2,'verified':not invalid_manifest}]
        with zipfile.ZipFile(zpath,'w',compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(m.WEIGHTS,b''.join(blocks) if not tamper else b'\0'*12)
            z.write(p,m.LEDGER);z.writestr(m.VERIFY,json.dumps(manifest));z.writestr(m.RESULTS,'{"example":1}\nnot-json\n' if malformed else '{"example":1}\n')
            if duplicate:
                with warnings.catch_warnings():warnings.simplefilter('ignore');z.writestr(m.RESULTS,'{}\n')
        return zpath
    def test_structural_qualification_does_not_claim_training_replay(self):
        r=m.audit(self.make(),agents=2,parameters=3)
        self.assertTrue(r['structural_verified']);self.assertEqual(r['verified_agents'],2);self.assertEqual(r['recorded_optimizer_steps'],10)
        self.assertEqual(r['result_jsonl_invalid_lines'],1);self.assertFalse(r['optimizer_replay_verified']);self.assertFalse(r['semantic_mastery_certified'])
        self.assertNotIn('sha256',json.dumps(r))
    def test_nonfinite_fp16_rejected(self):
        with self.assertRaises(ValueError):m.audit(self.make(nonfinite=True),agents=2,parameters=3)
    def test_hash_mismatch_rejected(self):
        with self.assertRaises(ValueError):m.audit(self.make(tamper=True),agents=2,parameters=3)
    def test_duplicate_zip_members_rejected(self):
        with self.assertRaises(ValueError):m.audit(self.make(duplicate=True),agents=2,parameters=3)
    def test_manifest_disagreement_rejected(self):
        with self.assertRaises(ValueError):m.audit(self.make(invalid_manifest=True),agents=2,parameters=3)
    def test_wrong_geometry_rejected(self):
        with self.assertRaises(ValueError):m.audit(self.make(),agents=2,parameters=4)
if __name__=='__main__':unittest.main()
