"""Evidence-based capability gaps. Discovery counts are not proof of competence."""
import argparse,json,time
from pathlib import Path
ROUTES={
 'repository_discovery':('coverage','Pin and screen each relevant repository; classify absent and excluded sources.'),
 'repository_code_index':('open','Index reviewed source functions with symbol and test provenance.'),
 'document_retrieval':('established','Verify source identity and passage integrity.'),
 'neural_catalog':('coverage','Inventory receipts; independently qualify each distinct architecture.'),
 'embedding_retrieval':('partial','Compare native encoder outputs with reference runtime and retrieval benchmark.'),
 'reranking':('open','Qualify cross-encoder adapters on labeled relevance data.'),
 'logical_entailment':('open','Test entailment and contradiction models on independent labeled records.'),
 'forecasting':('partial','Compare specialist forecasts with observed chronological baselines.'),
 'financial_sentiment':('open','Validate against licensed human-labeled financial text.'),
 'vision_segmentation':('open','Execute SAM on reviewed image inputs with reference masks.'),
 'vision_detection':('open','Evaluate DETR and OWL-ViT against annotated examples.'),
 'document_vision':('open','Verify chart and table extraction against labeled documents.'),
 'speech_recognition':('open','Qualify Whisper on licensed audio-transcript pairs.'),
 'multilingual':('open','Evaluate multilingual retrieval on human-labeled pairs.'),
 'dataset_discovery':('coverage','Review source rights, authorship, schema and independently held-out splits.'),
 'human_curriculum':('established','Preserve original solutions and separate training and test files.'),
 'semantic_deduplication':('open','Audit near-duplicate cross-split contamination.'),
 'student_enrollment':('coverage','Track identity, backend, admission and independent evidence per student.'),
 'student_specialist_feed':('partial','Record successful model-specific specialist use.'),
 'source_grounded_optimizer':('partial','Require verified checkpoint, actual gradients, independent validation.'),
 'adapter_promotion':('open','Require improvement, retention, hash verification and independent evaluation.'),
 'adapter_inference':('open','Qualify retained candidate versus base on unseen tasks.'),
 'model_composition':('open','Test single specialist versus fused route with identical task budget.'),
 'tool_routing':('open','Benchmark adaptive routing against single model and fixed routing.'),
 'cross_model_consensus':('open','Preserve disagreement; compare with independently verified outcomes.'),
 'causal_research':('partial','Validate observed-data assumptions and independent counterexamples.'),
 'historical_market_research':('partial','Confirm dataset rights, point-in-time data, costs and out-of-sample evaluation.'),
 'scientific_discovery':('open','Require reproducible hypothesis, experiment and independent verification.'),
 'memory_retention':('open','Measure forgetting across domains after adapter training.'),
 'resource_recovery':('partial','Verify interrupted transfer and scheduler recovery without duplicate workers.'),
 'migration':('open','Prepare checksummed inventory and verify actual destination hardware.'),
}
def classify_route(installed,connected,executed,evaluated):
 a=[installed,connected,executed,evaluated]
 if any(type(x) is not bool for x in a) or any(a[i] and not a[i-1] for i in range(1,4)):raise ValueError('evidence order')
 return ('missing','installed_only','connected','executed','evaluated')[sum(a)]
def make_frontier(s):
 counts={k:int(s.get(k,0)) for k in ('native_bundles','students','source_repos','human_records','student_feeds','optimizer_steps','accepted_adapters','icarus_repos','resource_files')}
 counts['student_specialist_pairs']=counts['native_bundles']*counts['students']
 counts['student_repository_pairs']=counts['source_repos']*counts['students']
 counts['student_specialist_repository_routes']=counts['student_specialist_pairs']*counts['source_repos']
 gaps=[{'route':k,'status':v[0],'next_evidence':v[1]} for k,v in ROUTES.items()]
 # A declared route is a review item, not a unique trained capability.
 return {'schema':'umbra.capability.frontier.v1','counts':counts,'gaps':gaps,'exhausted':False,'scope':'bounded known discovery dimensions; combinations are candidate addresses, not trained or verified routes','production_authority':False}
def load(p):
 try:return json.loads(p.read_text(encoding='utf8'))
 except (OSError,ValueError):return {}
def run(root):
 from student_council import roster
 from source_knowledge import Knowledge
 e=root/'experience';k=e/'source-knowledge';coverage=load(k/'icarus-coverage.json');human=load(k/'human-corpus'/'audit.json')
 council=load(e/'student-council'/'state.json')
 feeds={name for name,s in council.get('students',{}).items() if s.get('verified_feeds',0)>0}
 for p in k.glob('latest-specialist-feed-*.json'):
  r=load(p)
  if r.get('status')=='feed_verified' and isinstance(r.get('model'),str):feeds.add(r['model'])
 results=[load(p) for p in (e/'source-lora').rglob('last-result.json')]
 with Knowledge(k) as db:stats=db.stats()
 r=make_frontier({'native_bundles':len(list((root/'neural').glob('*/receipt.json'))),'students':sum(x['present'] for x in roster(root)),'source_repos':stats['repositories'],'human_records':human.get('original_training',0)+human.get('original_test',0),'student_feeds':len(feeds),'optimizer_steps':sum(x.get('optimizer_steps',0) for x in results),'accepted_adapters':sum(bool(x.get('retained_candidate')) for x in results),'icarus_repos':len(coverage.get('indexed',[])),'resource_files':len(list((root/'intelligence-resources').rglob('*.receipt.json')))})
 code=load(k/'code-coverage.json');retrieval=load(k/'retrieval-qualification.json')
 r['evidence']={'code_index':{x:code.get(x) for x in ('symbols','files','repositories','integrity')},'retrieval_probe_count':retrieval.get('probe_count',0),'retrieval_variants':len(retrieval.get('variants',{})),'reference_parity':retrieval.get('parity',{})}
 for g in r['gaps']:
  if g['route']=='repository_code_index' and code.get('integrity')=='ok' and code.get('symbols',0)>0:g['status']='partial';g['next_evidence']='Expand selected static symbol index and evaluate code-grounded answers.'
  if g['route']=='model_composition' and len(retrieval.get('variants',{}))>1:g['status']='partial';g['next_evidence']='Compare exploratory combinations on independent labeled data, then test downstream answers.'
  if g['route']=='reranking' and 'cross-encoder/ms-marco-MiniLM-L6-v2' in retrieval.get('identities',{}):g['status']='partial';g['next_evidence']='Evaluate cross-encoder on a larger independent relevance benchmark and connect bounded inference to students.'
 r['timestamp']=int(time.time());r['training_scope']='latest completed receipt per model, not cumulative optimizer lifetime';r['verified_feed_models']=sorted(feeds);r['repository_coverage']=coverage.get('unavailable',[])
 p=root/'infinity'/'capability-frontier.json';p.parent.mkdir(exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(r,indent=2),encoding='utf8');tmp.replace(p)
 return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);a=p.parse_args();print(json.dumps(run(a.root)))
