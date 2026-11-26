import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from source_curriculum import window,gate,trace_audit,corpus_identity
from human_corpus import validate
class CurriculumTest(unittest.TestCase):
 def rows(self,n=12):
  return [validate({'question':f'Calculate {i}+2.','answer':f'Original solution <<{i}+2={i+2}>>.\n#### {i+2}'}) for i in range(n)]
 def test_resumable_full_coverage(self):
  rows=self.rows();cursor=0;seen=[]
  for _ in range(4):
   chosen,cursor=window(rows,cursor,3,lambda r:r)
   seen.extend(r['record_sha256'] for r,x in chosen)
  self.assertEqual(cursor,12);self.assertEqual(len(set(seen)),12)
  chosen,cursor=window(rows,cursor,3,lambda r:r)
  self.assertEqual(cursor,15);self.assertEqual([r['record_sha256'] for r,x in chosen],seen[:3])
 def test_skipped_records_advance_cursor(self):
  rows=self.rows();chosen,cursor=window(rows,0,3,lambda r:None if r==rows[0] else r)
  self.assertEqual(cursor,4);self.assertEqual(len(chosen),3)
 def test_no_duplicate_within_window(self):
  with self.assertRaises(ValueError):window(self.rows(2),0,3,lambda r:r)
 def test_insufficient_eligible(self):
  with self.assertRaises(ValueError):window(self.rows(),0,3,lambda r:None)
 def test_fixed_retention_and_fresh_gate(self):
  self.assertTrue(gate([1.]*8,[.99]*8,[1.]*8,[.97]*8))
  self.assertFalse(gate([1.]*8,[1.11]*8,[1.]*8,[.97]*8))
  self.assertFalse(gate([1.]*8,[.99]*8,[1.]*8,[1.]*8))
  self.assertFalse(gate([1.]*8,[.99]*8,[1.]*8,[float('nan')]*8))
 def test_trace_audit(self):
  good=self.rows(1)[0];bad=validate({'question':'Calculate 2+2.','answer':'Original solution <<2+2=5>>.\n#### 5'})
  unsupported=validate({'question':'Compute power.','answer':'<<2^3=8>>\n#### 8'})
  r=trace_audit([good,bad,unsupported])
  self.assertEqual(r['records'],3);self.assertEqual(r['verified'],1);self.assertEqual(r['mismatch'],1);self.assertEqual(r['unsupported'],1)
 def test_corpus_identity_detects_order_change(self):
  rows=self.rows();self.assertNotEqual(corpus_identity(rows),corpus_identity(rows[::-1]))
if __name__=='__main__':unittest.main()
