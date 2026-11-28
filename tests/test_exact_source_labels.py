import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from source_curriculum import trace_audit
from council_qualification import canonical
class ExactSourceLabels(unittest.TestCase):
 def test_source_decimal_annotations(self):
  r=trace_audit([{'answer':'<<1/10=.1>> <<-1/2=-.5>> <<1/2=.50>>'}])
  self.assertEqual(r['verified'],3)
  self.assertEqual(r['unsupported'],0)
  self.assertEqual(r['mismatch'],0)
 def test_bad_label_not_silently_corrected(self):
  r=trace_audit([{'answer':'<<1/10=.2>> <<1/2=..5>>'}])
  self.assertEqual(r['mismatch'],1)
  self.assertEqual(r['unsupported'],1)
 def test_canonical_precision(self):
  a='0.123456789012345678901234567890123456789'
  b='0.123456789012345678901234567890123456788'
  self.assertEqual(canonical(a),a)
  self.assertNotEqual(canonical(a),canonical(b))
  self.assertEqual(canonical('-0.000'),'0')
  self.assertEqual(canonical('12.34000'),'12.34')
if __name__=='__main__':unittest.main()
