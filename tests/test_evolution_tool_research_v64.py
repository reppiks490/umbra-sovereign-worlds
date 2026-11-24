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

class ReceiptTests(unittest.TestCase):
 def receipt(self,completed=True):
  seed=3;c=m.cases(seed)
  r={'schema':'myriad.tool_research.v64','seed':seed,'model':'qwen3:1.7b','digest':m.PINS['qwen3:1.7b'],'case_sha256':m.hashlib.sha256(m.ev.canonical(c)).hexdigest(),'production_authority':False,'arbitrary_code_execution':False}
  if completed:r.update(status='completed',raw=json.dumps(list(m.EXPECTED)),response_sha256='a'*64,results=[m.evaluate(q,k) for q,k in zip(c,m.EXPECTED)])
  else:r.update(status='failed',error_class='ValueError')
  return r
 def signed(self,r):
  return {**r,'hmac_sha256':m.ev.sign(r,b'x'*32)}
 def test_valid_old_receipts(self):
  for b in (True,False):self.assertTrue(m.verify(self.signed(self.receipt(b)),b'x'*32))
 def test_signed_invalid_metadata(self):
  for status in (True,False):
   r=self.receipt(status)
   for k,v in [('status','unknown'),('model','unapproved'),('digest','wrong'),('seed',True),('case_sha256','bad'),('arbitrary_code_execution',True),('extra',1)]:
    with self.subTest(status=status,k=k),self.assertRaises(ValueError):m.verify(self.signed({**r,k:v}),b'x'*32)
 def test_bad_completed_fields(self):
  r=self.receipt()
  for k,v in [('response_sha256','invalid'),('raw',123),('results',[])]:
   with self.subTest(k=k),self.assertRaises(ValueError):m.verify(self.signed({**r,k:v}),b'x'*32)
  r['results'][0]['executed']=1
  with self.assertRaises(ValueError):m.verify(self.signed(r),b'x'*32)
 def test_failure_fields(self):
  r=self.receipt(False)
  for p in ({**r,'error_class':'bad error'},{**r,'raw':'[]'},{k:v for k,v in r.items() if k!='error_class'}):
   with self.assertRaises(ValueError):m.verify(self.signed(p),b'x'*32)

if __name__=='__main__':unittest.main()
