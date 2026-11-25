import unittest,sys,pathlib,tempfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from intelligence_resources import BUDGETS,admit,neural_complete,dataset_rows
class ResourcesTest(unittest.TestCase):
 def test_budget_and_protection(self):
  self.assertEqual(sum(BUDGETS.values()),15000000000)
  self.assertTrue(admit(0,0,1000000000,12000000000,2000000000,3000000000,2000000000))
  self.assertFalse(admit(0,0,1000000000,8999999999,2000000000,3000000000,2000000000))
  self.assertFalse(admit(14900000000,0,200000000,30000000000,0,0,2000000000))
  self.assertFalse(admit(0,1900000000,200000000,30000000000,0,0,2000000000))
 def test_neural_first(self):
  self.assertFalse(neural_complete({'cap_bytes':15000000000,'status':'pass_finished','results':[]}))
  self.assertFalse(neural_complete({'cap_bytes':28000000000,'status':'pass_finished','results':[{'status':'retry_needed'}]}))
  self.assertTrue(neural_complete({'cap_bytes':28000000000,'status':'pass_finished','results':[{'status':'deferred_storage'}]}))
 def test_dataset_metadata_requires_license_pinned_hash_safe_path(self):
  m={'id':'openai/gsm8k','sha':'a'*40,'private':False,'gated':False,'cardData':{'license':'mit'},'siblings':[{'rfilename':'main/train.parquet','size':100,'lfs':{'sha256':'b'*64}},{'rfilename':'../evil.parquet','size':100,'lfs':{'sha256':'b'*64}},{'rfilename':'data/script.py','size':100,'lfs':{'sha256':'b'*64}},{'rfilename':'main/test.parquet','size':101,'lfs':{'sha256':'c'*64}}]}
  r=dataset_rows('openai/gsm8k','reasoning',m)
  self.assertEqual([x['path'] for x in r],['main/train.parquet','main/test.parquet'])
  self.assertEqual(dataset_rows('openai/gsm8k','reasoning',{**m,'gated':True}),[])
  self.assertEqual(dataset_rows('openai/gsm8k','reasoning',{**m,'cardData':{}}),[])

 def test_real_metadata_single_license_list_and_git_blob(self):
  m={'id':'openai/gsm8k','sha':'a'*40,'private':False,'gated':False,'cardData':{'license':['mit']},'siblings':[{'rfilename':'main/train.parquet','size':100,'lfs':{'sha256':'b'*64}},{'rfilename':'test.jsonl','size':100,'blobId':'c'*40}]}
  r=dataset_rows('openai/gsm8k','reasoning',m)
  self.assertEqual(len(r),2)
  self.assertEqual(r[1]['algorithm'],'sha1')
  self.assertEqual(r[1]['sha'],'c'*40)
  self.assertEqual(r[1]['split'],'evaluation')
  self.assertEqual(dataset_rows('openai/gsm8k','reasoning',{**m,'cardData':{'license':['mit','unknown']}}),[])
 def test_metadata_refresh_preserves_pins_and_deduplicates(self):
  from intelligence_resources import merge_plan
  old={'rows':[{'repo':'a','path':'train','revision':'old'}],'rejected':[{'repo':'b','reason':'ValueError'}]}
  new={'rows':[{'repo':'a','path':'train','revision':'new'},{'repo':'b','path':'test','revision':'pin'}],'rejected':[]}
  result=merge_plan(old,new)
  self.assertEqual(result['rows'],old['rows']+[new['rows'][1]])
  self.assertEqual(result['rejected'],[])
 def test_resources_defer_after_bootstrap_launch(self):
  from infinity_service import resource_queue_status
  self.assertEqual(resource_queue_status('ready',{'status':'started'}),'deferred_bootstrap')
  self.assertEqual(resource_queue_status('ready',{'status':'running'}),'deferred_bootstrap')
  self.assertEqual(resource_queue_status('ready',{'status':'ready_marker'}),'ready')

 def test_balanced_order_prevents_large_corpus_monopoly(self):
  from intelligence_resources import balanced_order
  rows=[{'repo':'a','category':'science','kind':'dataset','split':'candidate_training','size':i,'path':str(i)} for i in (1,2,3)]
  rows.append({'repo':'b','category':'science','kind':'dataset','split':'candidate_training','size':100,'path':'x'})
  self.assertEqual([r['repo'] for r in balanced_order(rows)],['a','b','a','a'])

 def test_preview_reports_budget_fit_without_claiming_downloads(self):
  from intelligence_resources import preview
  rows=[{'repo':'a','category':'science','kind':'dataset','split':'candidate_training','size':900000000,'path':str(i)} for i in range(3)]
  result=preview(rows)
  self.assertEqual(result['science']['eligible_bytes'],2700000000)
  self.assertEqual(result['science']['admitted_bytes'],1800000000)
  self.assertEqual(result['science']['admitted_files'],2)
  self.assertEqual(result['symbolic']['admitted_bytes'],0)

 def test_source_only_acquisition_preserves_review_boundary(self):
  from intelligence_resources import source_disposition,source_order
  from human_corpus import ORIGINAL_ROWS
  human=ORIGINAL_ROWS[0]
  synthetic={**human,'repo':'HuggingFaceTB/cosmopedia'}
  duplicate={**human,'path':'socratic/train-00000-of-00001.parquet'}
  benchmark={**human,'repo':'cais/mmlu','split':'evaluation'}
  wheel={**human,'repo':'symengine','kind':'wheel','split':'tool_artifact'}
  self.assertEqual(source_disposition(human),'human_authored_corpus')
  self.assertEqual(source_disposition(benchmark),'evaluation_only')
  self.assertEqual(source_disposition(synthetic),'deferred_source_review')
  self.assertEqual(source_disposition(duplicate),'deferred_source_review')
  self.assertEqual(list(source_order([wheel,synthetic,duplicate,benchmark,human])),[human,wheel,benchmark])
