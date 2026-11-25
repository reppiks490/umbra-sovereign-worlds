import sys,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from source_assist import validate_quote
class SourceAssistTest(unittest.TestCase):
 def test_exact_quote_only(self):
  sources=[{'text':'The method uses a held-out test set.','repo':'a/b','revision':'a'*40,'path':'README.md','start_line':1,'end_line':1}]
  self.assertTrue(validate_quote({'source':1,'quote':'uses a held-out test set'},sources)['verified_quote'])
  for bad in [{'source':2,'quote':'uses a held-out test set'},{'source':1,'quote':'guaranteed accuracy'},{'source':True,'quote':'uses a held-out test set'}]:
   self.assertFalse(validate_quote(bad,sources)['verified_quote'])

 def test_ranked_sources_only_reorder_retrieved_evidence(self):
  from source_assist import apply_ranked
  a={'repo':'a/b','text':'original first','sha256':'a'*64}
  b={'repo':'a/b','text':'original second','sha256':'b'*64}
  ranked=[{**b,'specialist_scores':{'encoder':.8},'fused_score':.8},{**a,'specialist_scores':{'encoder':.2},'fused_score':.2}]
  self.assertEqual([r['text'] for r in apply_ranked([a,b],ranked)],['original second','original first'])
  with self.assertRaises(ValueError):apply_ranked([a,b],[{**ranked[0],'text':'changed'},ranked[1]])
  with self.assertRaises(ValueError):apply_ranked([a,b],[ranked[0],ranked[0]])

 def test_source_mix_preserves_provenance_and_budget(self):
  from source_assist import merge_sources
  docs=[{'text':'document','sha256':'a'*64},{'text':'second','sha256':'b'*64},{'text':'third','sha256':'c'*64}]
  code=[{'text':'def foo(): return 1','sha256':'d'*64,'symbol':'foo','blob_sha256':'e'*64}]
  self.assertEqual(merge_sources('general research',docs,code),docs)
  mixed=merge_sources('ICARUS risk implementation',docs,code)
  self.assertEqual(len(mixed),3)
  self.assertEqual(mixed[2],code[0])
  self.assertEqual(merge_sources('ICARUS risk',docs,[]),docs)
