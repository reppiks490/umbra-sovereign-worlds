import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from icarus_knowledge import allowed_document,screen_document,select_local
class IcarusKnowledgeTest(unittest.TestCase):
 def test_document_scope(self):
  self.assertTrue(allowed_document('docs/architecture.md'))
  self.assertTrue(allowed_document('README.md'))
  for x in ('docs/credentials.md','docs/private/account.md','docs/deployment.md','docs/config.md','docs/secrets.md','src/trade.py','docs/../README.md'):
   self.assertFalse(allowed_document(x))
 def test_sensitive_material_excluded(self):
  self.assertTrue(screen_document('An architecture for forecasting and research.'))
  self.assertFalse(screen_document('API_KEY = "not-for-the-index"'))
  self.assertFalse(screen_document('-----BEGIN PRIVATE KEY-----'))
 def test_owner_scope(self):
  rows=[{'repo':'reppiks490/Icarus','kind':'git','path':'A'},{'repo':'reppiks490/Icarus','kind':'git','path':'B'},{'repo':'other/Icarus','kind':'git','path':'C'},{'repo':'reppiks490/cash-flow-','kind':'git','path':'D'}]
  self.assertEqual(len(select_local(rows)),1)

 def test_remote_blob_integrity(self):
  import hashlib,base64
  from icarus_knowledge import verified_remote_doc
  b=b'# ICARUS research architecture\n';h=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
  m={'type':'file','path':'README.md','encoding':'base64','content':base64.b64encode(b).decode(),'size':len(b),'sha':h}
  self.assertEqual(verified_remote_doc(m),('README.md',b.decode()))
  with self.assertRaises(ValueError):verified_remote_doc({**m,'sha':'0'*40})
  with self.assertRaises(ValueError):verified_remote_doc({**m,'path':'docs/credentials.md'})

 def test_connector_pinned_import(self):
  import tempfile,base64,hashlib
  from icarus_knowledge import ingest_connector_rows
  from source_knowledge import Knowledge
  b=b'# Forecast architecture and research';h=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
  row={'repo':'reppiks490/orderbook','revision':'a'*40,'path':'README.md','sha':h,'content':base64.b64encode(b).decode()}
  with tempfile.TemporaryDirectory() as tmp:
   with Knowledge(pathlib.Path(tmp)) as k:
    r=ingest_connector_rows(k,[row,{**row,'repo':'unrelated/repo'},{**row,'sha':'0'*40}]);self.assertEqual(len(r['accepted']),1);self.assertEqual(len(r['rejected']),2);self.assertEqual(k.stats()['sources'],1)
