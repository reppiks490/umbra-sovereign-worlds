import hashlib,json,sqlite3,tempfile,unittest,sys
from pathlib import Path
from contextlib import closing
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import fleet_continuity as c
class Mesh:
    @staticmethod
    def digest(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True).encode()).hexdigest()
    @staticmethod
    def workflow(i):return {'id':f'E{i:06d}','domain':'test','algorithm_id':i}
    @staticmethod
    def recipe(i):return {'id':f'A{i:06d}'}
    @staticmethod
    def connect(path):
        db=sqlite3.connect(path)
        db.execute('CREATE TABLE IF NOT EXISTS runs(hour TEXT,workflow TEXT,domain TEXT,receipt TEXT,record TEXT,PRIMARY KEY(hour,workflow))')
        return db
class Tests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name);self.db=self.root/'db.sqlite';self.source='a'*40
        self.hour='2026-11-24T02';self.current='2026-11-24T14';self.rows=[]
        for i in range(1,195001,195):
            row={'workflow':f'E{i:06d}','domain':'test','hour':self.hour,'algorithm':Mesh.recipe(i),'deployment_authorized':False,'real_model_weight_training':False,'review_status':'candidate_for_manual_review','peer_used':False,'peer_parent':None,'peer_provenance_schema':'umbra.evolution.parent_link.v21'}
            row['receipt_sha256']=Mesh.digest(row);self.rows.append(row)
        self.write()
    def write(self):
        p=self.root/'shard-0.jsonl';p.write_text(''.join(json.dumps(r)+'\n' for r in self.rows))
        s={'group':0,'hour':self.hour,'source':self.source,'count':13000,'shards':[{'shard':0,'count':1000,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}],'production_authority':False,'neural_training':False}
        (self.root/'summary.json').write_text(json.dumps(s))
    def load(self):return c.hydrate_prior(self.root,self.db,0,self.current,self.source,Mesh)
    def test_exact_prior_coverage(self):
        m=self.load();self.assertEqual(len(m),1000);self.assertEqual(m['E000001']['hour'],self.hour)
        with closing(sqlite3.connect(self.db)) as db:self.assertEqual(db.execute('SELECT count(*) FROM runs').fetchone()[0],1000)
    def test_tamper_even_after_outer_hash_resealed(self):
        self.rows[0]['domain']='forged';self.write()
        with self.assertRaises(ValueError):self.load()
        self.assertFalse(self.db.exists())
    def test_same_hour_rejected(self):
        self.current=self.hour
        with self.assertRaises(ValueError):self.load()
    def test_duplicate_resealed_receipt_rejected(self):
        self.rows[1]=self.rows[0].copy();self.write()
        with self.assertRaises(ValueError):self.load()
    def test_parent_binding(self):
        m=self.load();p=m['E000001'];row={'workflow':'E000196','domain':'test','hour':self.current,'peer_used':True,'peer_parent':{'parent_workflow':p['workflow'],'parent_hour':p['hour'],'parent_domain':p['domain'],'parent_receipt_sha256':p['receipt_sha256']}}
        self.assertTrue(c.verify_parent(row,m))
        row['peer_parent']['parent_receipt_sha256']='0'*64
        with self.assertRaises(ValueError):c.verify_parent(row,m)
    def test_unbacked_parent_rejected(self):
        with self.assertRaises(ValueError):c.verify_parent({'workflow':'E000001','domain':'test','hour':self.current,'peer_used':True,'peer_parent':{}},{})
if __name__=='__main__':unittest.main()
