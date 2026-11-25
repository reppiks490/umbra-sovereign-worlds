import unittest,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from repository_runtime import validate_input,allowed_path,run_algorithm
class Test(unittest.TestCase):
 def test_numeric_budgets(self):
  self.assertEqual(validate_input('forecast_metrics',{'actual':[1,2],'predicted':[1,4]})['actual'],[1,2])
  for x in [{'actual':[1],'predicted':[1,2]},{'actual':[True],'predicted':[1]},{'actual':[float('nan')],'predicted':[1]}]:
   self.assertRaises(ValueError,validate_input,'forecast_metrics',x)
  self.assertRaises(ValueError,validate_input,'unknown',{})
 def test_safe_source_paths(self):
  for p in ['README.md','docs/intro.md','src/metrics.py']:self.assertTrue(allowed_path(p))
  for p in ['../README.md','.env','src/token.py','secrets/config.py','a\\b.py','a/../b.py','test.pem','credentials.json']:self.assertFalse(allowed_path(p))
 def test_pinned_actual_local_algorithms(self):
  # Live test is separately executed via CLI against owner inventory.
  self.assertRaises(ValueError,run_algorithm,{},'forecast_metrics',{'actual':[1],'predicted':[2]})
if __name__=='__main__':unittest.main()

class ExpansionTest(unittest.TestCase):
 def test_extended_capability_input_validation(self):
  self.assertEqual(validate_input('forecast_crosscheck',{'actual':[1,2],'predicted':[1,3]})['actual'],[1,2])
  self.assertRaises(ValueError,validate_input,'forecast_crosscheck',{'actual':[0],'predicted':[1]})
  self.assertEqual(validate_input('sparse_regularization',{'coefficients':[-2,0,2],'weight':.5})['weight'],.5)
  self.assertRaises(ValueError,validate_input,'sparse_regularization',{'coefficients':[1],'weight':-1})

class SourceBrowsingTest(unittest.TestCase):
 def test_archive_and_extracted_source_listing(self):
  import tempfile,zipfile,hashlib
  from repository_runtime import list_source,source_receipt
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)
   archive=root/'source.zip'
   with zipfile.ZipFile(archive,'w') as z:
    z.writestr('src/algorithm.py','def f(): return 2')
    z.writestr('credentials.txt','not readable')
    z.writestr('../escape.py','not readable')
   readme=root/'README.md';readme.write_bytes(b'Example source')
   registry={'repositories':[{'id':'archive','kind':'archive_candidate','path':str(archive),'head':None},{'id':'source','kind':'source_candidate','path':str(root),'readme':'README.md','readme_sha256':hashlib.sha256(readme.read_bytes()).hexdigest(),'head':None}]}
   self.assertEqual(list_source(registry,'archive')['files'],['src/algorithm.py'])
   self.assertEqual(source_receipt(registry,'archive','src/algorithm.py')['text'],'def f(): return 2')
   self.assertEqual(list_source(registry,'source')['files'],['README.md'])
   self.assertRaises(ValueError,source_receipt,registry,'archive','../escape.py')
   self.assertRaises(ValueError,list_source,registry,'missing')
