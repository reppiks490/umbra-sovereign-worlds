import hashlib,json,pathlib,tempfile,unittest
from capability_evidence import verified_select
from test_capability_router import registry,policy
A='mcp__GitHub__fetch_file'
class AdmissionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name);self.out=self.root/'output.txt';self.out.write_bytes(b'observed source response')
  self.row={'action':A,'observed_at':100,'status':'verified-read','output':'output.txt','output_sha256':hashlib.sha256(self.out.read_bytes()).hexdigest()}
 def tearDown(self):self.tmp.cleanup()
 def pin(self,rows=None):
  rows=rows if rows is not None else [self.row];entries=[]
  for i,row in enumerate(rows):
   p=self.root/(str(i)+'.json');p.write_text(json.dumps(row),encoding='utf8');entries.append({'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
  m=self.root/'manifest.json';m.write_text(json.dumps({'schema':1,'receipts':entries}),encoding='utf8');return hashlib.sha256(m.read_bytes()).hexdigest()
 def route(self,pin):
  return verified_select(self.root,pin,registry(),policy(),'ICARUS','source-read',101,max_age=50)
 def test_verified_bytes_and_independent_pin(self):
  pin=self.pin();self.assertEqual(self.route(pin)['action'],A)
 def test_manifest_mutation(self):
  pin=self.pin();self.root.joinpath('manifest.json').write_text('{}')
  with self.assertRaises(ValueError):self.route(pin)
 def test_receipt_mutation(self):
  pin=self.pin();self.root.joinpath('0.json').write_text('{}')
  with self.assertRaises(ValueError):self.route(pin)
 def test_output_mutation(self):
  pin=self.pin();self.out.write_bytes(b'changed')
  with self.assertRaises(ValueError):self.route(pin)
 def test_path_escape(self):
  self.row['output']='../outside.txt'
  with self.assertRaises(ValueError):self.route(self.pin())
 def test_failure_revokes_previous_success(self):
  fail={'action':A,'observed_at':101,'status':'failed'}
  self.assertIsNone(self.route(self.pin([self.row,fail])))
 def test_no_independent_pin_no_admission(self):
  self.pin()
  with self.assertRaises(ValueError):self.route('a'*64)
 def test_no_output_for_claimed_success(self):
  del self.row['output']
  with self.assertRaises(ValueError):self.route(self.pin())
