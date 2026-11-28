import unittest,tempfile,pathlib,sys,hashlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from learning_workspace import ReplayBank,plan_replay
def row(i,domain='math',source='symbolic_verified'):
 p='Question '+str(i)
 return {'prompt':p,'prompt_sha256':hashlib.sha256(p.encode()).hexdigest(),'answer':'yes','options':['yes','no','maybe','unknown'],'domain':domain,'source':source,'level':1}
def corpus(offset=0):
 return {'schema':'umbra.swarm.corpus.v1','model':'qwen3:0.6b','seed':1,'training':[row(i+offset) for i in range(32)],'retention':[row(i+1000) for i in range(8)],'transfer':[row(i+2000) for i in range(8)]}
class WorkspaceTest(unittest.TestCase):
 def test_ingest_dedup_and_cross_cycle_holdout(self):
  with tempfile.TemporaryDirectory() as d:
   with ReplayBank(pathlib.Path(d)) as bank:
    c=corpus();bank.ingest(c);bank.ingest(c)
    self.assertEqual(bank.stats()['examples'],48)
    c=corpus(1000)
    self.assertRaises(ValueError,bank.ingest,c)
    self.assertEqual(bank.stats()['examples'],48)
 def test_cross_family_split_protection(self):
  with tempfile.TemporaryDirectory() as d:
   with ReplayBank(pathlib.Path(d)) as bank:
    bank.ingest(corpus());c=corpus(1000);c['model']='granite4:350m'
    self.assertRaises(ValueError,bank.ingest,c)
 def test_replay_balances_domains_and_avoids_repetition(self):
  rows=[row(i,['math','code','memory'][i%3]) for i in range(12)]
  selected=plan_replay(rows,6,{},0)
  self.assertEqual(len(set(x['prompt_sha256'] for x in selected)),6)
  self.assertEqual(len(set(x['domain'] for x in selected)),3)
  counts={x['prompt_sha256']:1 for x in selected}
  next_rows=plan_replay(rows,6,counts,1)
  self.assertFalse(set(x['prompt_sha256'] for x in selected)&set(x['prompt_sha256'] for x in next_rows))
 def test_training_attempt_receipt_idempotency(self):
  with tempfile.TemporaryDirectory() as d:
   with ReplayBank(pathlib.Path(d)) as bank:
    c=corpus();bank.ingest(c);ids=[c['training'][0]['prompt_sha256']]
    bank.record_attempt('attempt-1',c['model'],ids,False);bank.record_attempt('attempt-1',c['model'],ids,False)
    self.assertEqual(bank.counts(c['model'])[ids[0]],1)
    self.assertRaises(ValueError,bank.record_attempt,'attempt-1',c['model'],ids,True)
    self.assertRaises(ValueError,bank.record_attempt,'attempt-2',c['model'],[c['retention'][0]['prompt_sha256']],False)

 def test_fixed_anchor_survives_corpus_rotation(self):
  with tempfile.TemporaryDirectory() as d:
   with ReplayBank(pathlib.Path(d)) as bank:
    c=corpus();bank.ingest(c);first=bank.anchors(c['model'],'retention')
    newer=corpus(100);newer['retention']=[row(i+3000) for i in range(8)];bank.ingest(newer)
    self.assertEqual(bank.anchors(c['model'],'retention'),first)
    self.assertEqual(len(first),8)
    self.assertRaises(ValueError,bank.anchors,c['model'],'training')
 def test_durable_evaluation_evidence(self):
  with tempfile.TemporaryDirectory() as d:
   with ReplayBank(pathlib.Path(d)) as bank:
    c=corpus();bank.ingest(c);h=c['training'][0]['prompt_sha256']
    r={'before':{'retention':1.,'transfer':2.},'after':{'retention':1.,'transfer':1.8},'adapter_weight_training':True,'accepted':True,'base_sha256':'a'*64,'steps':1}
    bank.record_attempt('evaluated',c['model'],[h],True,r)
    self.assertEqual(bank.stats()['accepted_attempts'],1)
    self.assertRaises(ValueError,bank.record_attempt,'bad',c['model'],[h],True,{**r,'after':{'retention':9.,'transfer':1.}})
    self.assertEqual(bank.stats()['attempts'],1)

 def test_anchor_promotion_and_domain_evaluation(self):
  from learning_workspace import summarize_losses,retention_gate
  rows=[row(1,'math'),row(2,'code'),row(3,'math')]
  s=summarize_losses(rows,[1.,2.,3.],[rows[0]['prompt_sha256']])
  self.assertEqual(s['mean'],2.)
  self.assertEqual(s['anchor_mean'],1.)
  self.assertEqual(s['domains']['math'],{'count':2,'mean':2.})
  self.assertRaises(ValueError,summarize_losses,rows,[1.,float('nan'),3.],[])
  self.assertRaises(ValueError,summarize_losses,rows,[1.,2.,3.],['missing'])
  before={'retention':1.,'transfer':2.}
  after={'retention':1.01,'transfer':1.8}
  self.assertTrue(retention_gate(before,after,before,after))
  self.assertFalse(retention_gate(before,after,before,{'retention':1.1,'transfer':1.8}))
  self.assertFalse(retention_gate(before,after,before,{'retention':float('nan'),'transfer':1.8}))
