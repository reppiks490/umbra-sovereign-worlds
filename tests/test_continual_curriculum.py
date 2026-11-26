import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from source_curriculum import plan_cycle,campaign_eligible
from human_corpus import validate
class CampaignTest(unittest.TestCase):
 def corpus(self):
  def rows(prefix,n):
   return [validate({'question':f'{prefix} {i}+2','answer':f'#### {i+2}'}) for i in range(n)]
  return {'train':rows('training',32),'validation':rows('validation',40)}
 def test_resume_and_disjoint(self):
  c=self.corpus();a=plan_cycle(c,{},4,lambda r:r);b=plan_cycle(c,a['next_state'],4,lambda r:r)
  ids=lambda r:{x['record_sha256'] for x,y in r}
  self.assertFalse(ids(a['training'])&ids(b['training']))
  self.assertFalse(ids(a['fresh'])&ids(b['fresh']))
  self.assertEqual(ids(a['retention']),ids(b['retention']))
  self.assertFalse(ids(a['retention'])&ids(a['fresh']))
  self.assertEqual(b['next_state']['completed_steps'],8)
 def test_changed_source_rejected(self):
  c=self.corpus();a=plan_cycle(c,{},4,lambda r:r);c['train'].reverse()
  with self.assertRaises(ValueError):plan_cycle(c,a['next_state'],4,lambda r:r)
 def test_campaign_extends_legacy_cap(self):
  self.assertTrue(campaign_eligible({'attempts':20}))
  self.assertFalse(campaign_eligible({'curriculum':{'train_cursor':20274}}))
 def test_no_holdout_access(self):
  c=self.corpus();c['test']=None
  self.assertEqual(len(plan_cycle(c,{},4,lambda r:r)['training']),4)
if __name__=='__main__':unittest.main()
