import sys,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from source_assist import validate_quote
class SourceAssistTest(unittest.TestCase):
 def test_exact_quote_only(self):
  sources=[{'text':'The method uses a held-out test set.','repo':'a/b','revision':'a'*40,'path':'README.md','start_line':1,'end_line':1}]
  self.assertTrue(validate_quote({'source':1,'quote':'uses a held-out test set'},sources)['verified_quote'])
  for bad in [{'source':2,'quote':'uses a held-out test set'},{'source':1,'quote':'guaranteed accuracy'},{'source':True,'quote':'uses a held-out test set'}]:
   self.assertFalse(validate_quote(bad,sources)['verified_quote'])
