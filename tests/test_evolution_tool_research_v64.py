import unittest,json
import evolution_tool_research_v64 as m
class Tests(unittest.TestCase):
 def test_independent_reference_matches_all_methods(self):
  for seed in range(12):
   for i,c in enumerate(m.cases(seed)):
    self.assertTrue(m.evaluate(c,m.EXPECTED[i])['qualified'])
 def test_wrong_method_and_unknown_rejected(self):
  c=m.cases(1)[0]
  self.assertFalse(m.evaluate(c,'fft')['qualified'])
  with self.assertRaises(ValueError):m.evaluate(c,'exec')
 def test_prompt_has_no_key_and_strict_order(self):
  c=m.cases(1)
  self.assertNotIn('expected',m.prompt(c))
  self.assertEqual(m.decode(c,json.dumps(list(m.EXPECTED))),list(m.EXPECTED))
  with self.assertRaises(ValueError):m.decode(c,'["fft"]')
 def test_different_data(self):
  self.assertNotEqual(m.cases(1),m.cases(2))
if __name__=='__main__':unittest.main()
