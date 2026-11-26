"""Replay one reviewed owner diagnostic, separate from newly executed inference."""
import hashlib,json,math,re
from pathlib import Path

PROBE='What is half of 2x17+42(372x47)?'
EXPECTED=(2*17+42*372*47)//2
PINNED_SHA256='4e0c112e3a1039592ecfab681018079439c5b57ab67c43c9ae83698eb2df3aa3'
RECEIPT='trial-1795667020051457200.json'
REVIEWED={
 'phi4-mini:latest':('365181','incorrect_intermediate_arithmetic',1),
 'granite3.3:2b':('367231','incorrect_intermediate_arithmetic',1),
 'qwen3:1.7b':('369441','incorrect_intermediate_arithmetic',1),
 'deepseek-r1:1.5b':('8759','missing_operand',3),
 'qwen2.5-coder:1.5b':('10000x + 10000','notation_interpretation',None)}
def classify(model,reason,response):
 if not isinstance(response,str) or not 1<=len(response)<=24000:raise ValueError('response')
 if model=='qwen3:4b' and reason=='length':
  return {'diagnosis':'truncated','lesson_tier':None,'correct':False,'action':'bounded concise explicit-expression retest'}
 if model not in REVIEWED or reason!='stop':raise ValueError('unreviewed result')
 label,diagnosis,tier=REVIEWED[model]
 if not re.search(r'(?<![0-9])'+re.escape(label)+r'(?![0-9])',response[-300:].replace(',','')):
  raise ValueError('reviewed final answer not observed')
 return {'diagnosis':diagnosis,'lesson_tier':tier,'correct':False,
         'action':'explicit notation and interpretation retest' if tier is None else 'source-prerequisite lesson candidates followed by disjoint retest'}

def replay(raw):
 if not isinstance(raw,bytes) or len(raw)>2_000_000 or hashlib.sha256(raw).hexdigest()!=PINNED_SHA256:raise ValueError('original receipt digest')
 v=json.loads(raw.decode('utf-8-sig'))
 if v['prompt']!=PROBE or v['scope']!='unassisted owner arithmetic probe; no hints or answer; no training':raise ValueError('original probe identity')
 results=v['results'];seen=set();evaluated=[];deferred=[]
 for r in results:
  model=r['model']
  if model in seen:raise ValueError('duplicate model')
  seen.add(model)
  if r['status']!='evaluated':
   if r['status'] not in ('deferred_busy','deferred_memory','not_installed'):raise ValueError('unknown status')
   deferred.append({'model':model,'status':r['status']});continue
  if r['backend']!='ollama' or not re.fullmatch('[a-f0-9]{64}',r['digest']) or type(r['tokens']) is not int or not 1<=r['tokens']<=384 or type(r['seconds']) not in (int,float) or not math.isfinite(r['seconds']) or r['seconds']<0:raise ValueError('inference receipt')
  evaluated.append({'model':model,'digest':r['digest'],'tokens':r['tokens'],'seconds':r['seconds'],
   'response_sha256':hashlib.sha256(r['response'].encode()).hexdigest(),**classify(model,r['done_reason'],r['response'])})
 if {r['model'] for r in evaluated}!=set(REVIEWED)|{'qwen3:4b'} or len(deferred)!=10:raise ValueError('coverage')
 return {'status':'reviewed_historical_receipt','source_sha256':PINNED_SHA256,'historical_completed_calls':len(evaluated),
  'historical_correct':0,'new_model_calls':0,'deferred':deferred,'evaluated':evaluated,'expected_whole_expression':EXPECTED,
  'scope':'reviewed historical development probe; ambiguous wording; not independent holdout or new inference',
  'weight_training':False,'production_authority':False}

def read(root):
 p=Path(root)/'experience'/'owner-arithmetic-evaluation'/RECEIPT
 if not p.exists():return {'status':'not_available','historical_completed_calls':0,'new_model_calls':0,'evaluated':[],'deferred':[]}
 if p.is_symlink() or not p.is_file() or p.stat().st_size>2_000_000:raise ValueError('receipt path')
 return replay(p.read_bytes())

def corrective_candidates(corpus,rows):
 from corrective_curriculum import source_index,select_lessons
 indexed=source_index(corpus) if any(r['lesson_tier'] is not None for r in rows) else []
 return [{'model':r['model'],'digest':r['digest'],'diagnosis':r['diagnosis'],'action':r['action'],
          'lessons':select_lessons(corpus,'arithmetic',r['lesson_tier'],index=indexed) if r['lesson_tier'] is not None else [],
          'native_checkpoint_mapping':'unverified; never infer same checkpoint from family name',
          'training_authorized':False,'new_model_calls':0} for r in rows]
