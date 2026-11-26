import pathlib, sys, tempfile, unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from council_ledger import record, summarize, next_offset

class CouncilLedgerTest(unittest.TestCase):
 def setUp(self):
  self.models={'a':'a'*64,'b':'b'*64,'c':'c'*64}
 def trial(self, offset=0, suffix='1'):
  return {'status':'completed','manifest':{'models':self.models,'offset':offset,'count':1,'validation_records':[suffix*64],'protocol':'fixed-one-human-example-strict-majority-v1'},
          'ensemble':{'cases':1,'answered':1,'correct':1},'baselines':{m:{'cases':1,'answered':1,'correct':int(m!='c')} for m in self.models},
          'paired':{m:{'wins':int(m=='c'),'losses':0,'ties':int(m!='c')} for m in self.models},'model_calls':3,'completed_calls':3,
          'inference_seconds':2,'weight_training':False,'production_authority':False,'test_partition_used_for_inference':False}
 def test_preserve_and_deduplicate(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)
   record(p,self.trial()); record(p,self.trial())
   self.assertEqual(summarize(p)['cases'],1)
   self.assertEqual(next_offset(p,self.models),1)
   record(p,self.trial(1,'2'))
   r=summarize(p)
   self.assertEqual(r['cases'],2)
   self.assertEqual(r['ensemble_correct'],2)
   self.assertEqual(r['paired']['c']['wins'],2)
   self.assertEqual(next_offset(p,self.models),2)
   self.assertFalse(r['promotion_authorized'])
 def test_conflicting_replay_and_overlap(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);record(p,self.trial())
   bad=self.trial();bad['inference_seconds']=9
   with self.assertRaises(ValueError):record(p,bad)
   with self.assertRaises(ValueError):record(p,self.trial(1))
 def test_reject_holdout_and_inconsistent_counts(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);bad=self.trial();bad['test_partition_used_for_inference']=True
   with self.assertRaises(ValueError):record(p,bad)
   bad=self.trial();bad['ensemble']['correct']=2
   with self.assertRaises(ValueError):record(p,bad)
 def test_tampering_detected(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);record(p,self.trial());f=next(p.glob('trial-*.json'));f.write_text('{}')
   with self.assertRaises(ValueError):summarize(p)
if __name__=='__main__':unittest.main()
