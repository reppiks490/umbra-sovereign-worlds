import hashlib,json,pathlib,tempfile,unittest,sys
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from source_benchmark import PINS,authenticate,load_mmlu,grade_mmlu

class DevelopmentBenchmarkTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=pathlib.Path(self.tmp.name)
  self.raw=b'PAR1fixture-onlyPAR1'
  self.pin={**PINS['mmlu_abstract_algebra_dev'],'size':len(self.raw),'sha':hashlib.sha256(self.raw).hexdigest()}
  self.patcher=patch.dict(PINS,{'mmlu_abstract_algebra_dev':self.pin});self.patcher.start();self.addCleanup(self.patcher.stop)
  self.file=self.root/'intelligence-resources'/'benchmarks'/'cais--mmlu--c30699e8356d'/self.pin['path']
  self.file.parent.mkdir(parents=True);self.file.write_bytes(self.raw)
  self.receipt=self.file.with_name(self.file.name+'.receipt.json')
  self.receipt.write_text(json.dumps(self.pin),encoding='utf8')
 def test_authenticates_pinned_bytes(self):
  r,b=authenticate(self.root,'mmlu_abstract_algebra_dev')
  self.assertEqual(b,self.raw);self.assertEqual(r['sha'],self.pin['sha'])
 def test_rejects_changed_payload(self):
  self.file.write_bytes(self.raw[:-5]+b'XPAR1')
  with self.assertRaises(ValueError):authenticate(self.root,'mmlu_abstract_algebra_dev')
 def test_rejects_receipt_relabeling(self):
  self.receipt.write_text(json.dumps({**self.pin,'split':'training'}),encoding='utf8')
  with self.assertRaises(ValueError):authenticate(self.root,'mmlu_abstract_algebra_dev')
 def test_final_partition_not_addressable(self):
  with self.assertRaises(ValueError):authenticate(self.root,'mmlu_abstract_algebra_test')
 def rows(self):
  return [{'question':'Fixture question '+str(i),'subject':'abstract_algebra','choices':['a','b','c','d'],'answer':i%4} for i in range(5)]
 def decoded(self,rows):
  with patch('source_benchmark.decode_parquet',return_value=rows) as decoder:
   result=load_mmlu(self.root)
   decoder.assert_called_once_with(self.raw)
   return result
 def test_decoded_rows_have_stable_unique_ids_and_no_training_authority(self):
  a=self.decoded(self.rows());b=self.decoded(self.rows())
  self.assertEqual(a,b);self.assertEqual(len({r['case_id'] for r in a}),5)
  self.assertTrue(all(r['training_allowed'] is False and r['split']=='development' for r in a))
 def test_rejects_boolean_labels(self):
  rows=self.rows();rows[0]['answer']=True
  with self.assertRaises(ValueError):self.decoded(rows)
 def test_rejects_duplicate_question(self):
  rows=self.rows();rows[1]['question']=rows[0]['question'].upper()
  with self.assertRaises(ValueError):self.decoded(rows)
 def test_rejects_wrong_subject_or_row_count(self):
  rows=self.rows();rows[0]['subject']='anatomy'
  with self.assertRaises(ValueError):self.decoded(rows)
  with self.assertRaises(ValueError):self.decoded(self.rows()[:4])
 def test_exact_independent_grade(self):
  self.assertEqual(grade_mmlu(' B ',1),'correct')
  self.assertEqual(grade_mmlu('A',1),'incorrect')
  for s in ('A or B','The answer is B','',None,'ABSTAIN'):
   self.assertEqual(grade_mmlu(s,1),'abstain')
  with self.assertRaises(ValueError):grade_mmlu('B',True)
 def test_no_caller_supplied_decoder(self):
  with self.assertRaises(TypeError):load_mmlu(self.root,decoder=lambda _:self.rows())
if __name__=='__main__':unittest.main()
