"""Failure-to-authentic-source planning. No synthetic training or optimizer authority."""
import argparse,collections,json,math,re,sqlite3
from pathlib import Path
from generated_challenges import question,grade,digest,SKILLS
from human_corpus import validate,REPO,REV
from source_curriculum import trace_audit,corpus_identity
from verified_reasoner import calculate,ReasoningError

# These are hypotheses about arithmetic prerequisites, not proven root causes,
# and not full domain-equivalent lessons for trading, code or world simulation.
OPS={
 'arithmetic':(('add',),('mul','add'),('mul','add','sub'),('mul','div','add')),
 'market_accounting':(('mul','add'),('mul','sub'),('mul','add','div'),('mul','sub')),
 'world_state':(('add','sub'),('mul','sub'),('mul','sub'),('add','mul')),
 'event_time':(('add',),('add','mul'),('max','add'),('mul','add','sub')),
 'code_trace':(('add','sub'),('add','mul'),('add','sub','mul'),('mul','div','add')),
 'statistics':(('add','div'),('sub',),('add','mul','div'),('mul','div','sub')),
 'resource_planning':(('add','sub'),('mul','add'),('div',),('div',))}
def read_failures(path,limit=256):
 path=Path(path)
 if type(limit) is not int or not 1<=limit<=1024:raise ValueError('read bound')
 if not path.exists():return []
 if path.is_symlink() or not path.is_file():raise ValueError('ledger path')
 db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=5)
 db.row_factory=sqlite3.Row
 try:
  rows=db.execute("select * from attempts where status='completed' order by attempt desc limit ?",(limit,)).fetchall()
  out=[]
  for r in rows:
   q=question(r['skill'],r['tier'],r['ordinal'])
   response=r['response'];tokens=r['tokens'];seconds=r['seconds'];reason=r['done_reason']
   if (not isinstance(r['model'],str) or not r['model'] or not re.fullmatch('[a-f0-9]{64}',r['digest']) or
       q['id']!=r['question_id'] or not isinstance(response,str) or len(response)>24000 or digest(response)!=r['response_hash'] or
       reason not in ('stop','length') or type(tokens) is not int or not 0<=tokens<=160 or
       type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<0 or
       grade(q,response,reason)!=r['outcome']):raise ValueError('unverified failure receipt')
   if r['outcome']!='correct':
    out.append({k:r[k] for k in ('attempt','model','digest','skill','tier','ordinal','question_id','outcome')})
  return out
 finally:db.close()

def source_index(corpus):
 # Verify identity and split disjointness before using any source record.
 if set(corpus)!= {'train','validation','test'}:raise ValueError('source split schema')
 seen=set()
 for key in ('train','validation','test'):
  local=set()
  for row in corpus[key]:
   if validate({k:row[k] for k in ('question','answer')})!=row:raise ValueError('source record identity')
   q=row['question_sha256']
   if q in seen or q in local:raise ValueError('source split overlap')
   local.add(q)
  seen.update(local)
 results=[]
 for row in corpus['train']:
  if len(row['question'])+len(row['answer'])>2500:continue
  a=trace_audit([row])
  if a['fully_verified_records']!=1 or not a['annotations']:continue
  ops=set()
  try:
   for expr in re.findall(r'<<([^<>\r\n]{1,512})>>',row['answer']):
    lhs=expr.split('=')[0].replace(',','').strip()
    ops.update(n['op'] for n in calculate(lhs)['plan']['nodes'] if n['op']!='literal')
  except (ValueError,ReasoningError):continue
  if ops:results.append((row,ops))
 return results

def select_lessons(corpus,skill,tier,limit=4,index=None):
 if skill not in SKILLS or type(tier) is not int or not 0<=tier<=3 or type(limit) is not int or not 1<=limit<=8:raise ValueError('lesson request')
 required=set(OPS[skill][tier])
 rows=source_index(corpus) if index is None else index
 matches=[(r,ops) for r,ops in rows if required<=ops]
 matches.sort(key=lambda x:(len(x[1]-required),len(x[0]['question'])+len(x[0]['answer']),x[0]['record_sha256']))
 return [{'record_sha256':r['record_sha256'],'question_sha256':r['question_sha256'],
          'source_kind':'verified_original_training','source_repo':REPO,'source_revision':REV,
          'operations':sorted(ops),'scope':'arithmetic prerequisite hypothesis; no domain mastery proof'} for r,ops in matches[:limit]]

def plan(corpus,rows):
 groups=collections.defaultdict(list);seen=set()
 for r in rows:
  q=question(r['skill'],r['tier'],r['ordinal'])
  if q['id']!=r['question_id'] or r['outcome'] not in ('incorrect','abstain','format','truncated') or not re.fullmatch('[a-f0-9]{64}',r['digest']):raise ValueError('failure identity')
  key=(r['model'],r['digest'],r['skill'],r['tier'],r['ordinal'])
  if key in seen:raise ValueError('duplicate failure')
  seen.add(key);groups[(r['model'],r['digest'],r['skill'],r['tier'],r['outcome'])].append(r['question_id'])
 index=source_index(corpus) if groups else []
 clusters=[]
 for (model,identity,skill,tier,outcome),ids in sorted(groups.items(),key=lambda v:(-len(v[1]),v[0])):
  lessons=select_lessons(corpus,skill,tier,index=index) if outcome=='incorrect' else []
  clusters.append({'model':model,'digest':identity,'skill':skill,'tier':tier,'outcome':outcome,
                   'failure_count':len(ids),'diagnostic_question_ids':sorted(ids),
                   'status':'source_prerequisite_candidates' if lessons else 'blocked_no_matching_source' if outcome=='incorrect' else 'diagnose_before_training',
                   'lessons':lessons,'native_checkpoint_mapping':'unverified; no cross-model weight attribution',
                   'training_authorized':False})
 return {'status':'planned' if groups else 'no_verified_failures','clusters':clusters,
         'source_train_identity':corpus_identity(corpus['train']),
         'generated_questions_used_as_training':False,'weight_training':False,'production_authority':False,
         'scope':'bounded recent completed receipt replay and source-prerequisite planning, not causal diagnosis or actual weight training'}

def run(root):
 from student_council import load_corpus
 from native_lora_train import atomic
 bank=root/'experience'/'generated-challenges'
 rows=read_failures(bank/'ledger.sqlite3')
 result=plan(load_corpus(root),rows)
 bank.mkdir(parents=True,exist_ok=True)
 atomic(bank/'corrective-plan.json',result)
 return {'status':result['status'],'clusters':len(result['clusters']),'source_candidate_clusters':sum(x['status']=='source_prerequisite_candidates' for x in result['clusters']),
 'failure_receipts':len(rows),'weight_training':False,'production_authority':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);a=p.parse_args();print(json.dumps(run(a.root)))
