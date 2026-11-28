import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from icarus_code_index import extract_symbols,allowed_path
class CodeIndexTest(unittest.TestCase):
 def test_static_only(self):
  s='raise RuntimeError("must never execute")\n\ndef calculate(x):\n    """Calculate a value."""\n    return x+1\n'
  r=extract_symbols(s)
  self.assertEqual(r[0]['symbol'],'calculate')
  self.assertEqual(r[0]['start_line'],3)
  self.assertIn('return x+1',r[0]['text'])
 def test_path_scope(self):
  self.assertTrue(allowed_path('icarus/features/liquidity.py'))
  self.assertFalse(allowed_path('icarus/features/../../secrets.py'))
  self.assertFalse(allowed_path('icarus/features/credentials.py'))
  self.assertFalse(allowed_path('icarus/live_orders.py'))
 def test_sensitive_code_is_not_indexed(self):
  self.assertEqual(extract_symbols('def calculate():\n    api_key = "secret-value"\n    return api_key\n'),[])
