"""Authored, deterministic development questions; NEVER source-only training data.

A large address space is not an executed question count. Each real model call
is reserved before execution and graded against an exact, regenerated label.
"""
import argparse,hashlib,json,math,re,shutil,sqlite3,time
from fractions import Fraction
from pathlib import Path

VERSION='authored-challenge-v1'
SKILLS=('arithmetic','market_accounting','world_state','event_time','code_trace','statistics','resource_planning')
LIMIT=10**9
MAX_DB=256*1024**2
LESSON_TOPICS={
 'arithmetic':'multiplication division parentheses order of operations',
 'market_accounting':'cost quantity price fee arithmetic',
 'world_state':'inventory addition subtraction repeated changes',
 'event_time':'elapsed time sequence intervals',
 'code_trace':'loops accumulators arithmetic and branches',
 'statistics':'mean total rate fraction',
 'resource_planning':'capacity allocation batches integer division'}

def canonical(value):
 return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()

def question(skill,tier,ordinal):
 if skill not in SKILLS or type(tier) is not int or not 0<=tier<=3 or type(ordinal) is not int or not 0<=ordinal<LIMIT:raise ValueError('challenge bounds')
 # Permutation of the index space: no random state, no materialized billions.
 n=(ordinal*104729+817231)%LIMIT
 a,b,c=n//1000000+1,n//1000%1000+1,n%1000+1
 if skill=='arithmetic':
  if tier==0:q=f'Add {a}, {b} and {c}.';v=a+b+c
  elif tier==1:q=f'Evaluate {a} times {b} plus {c}.';v=a*b+c
  elif tier==2:q=f'Evaluate ({a}+{b}) times {c} minus {a}.';v=(a+b)*c-a
  elif ordinal==0:q='Evaluate half of the entire expression (2*17+42*(372*47)).';v=367181
  else:q=f'Evaluate half of the entire expression (2*{a}+{b}*({c}*47)).';v=Fraction(2*a+b*c*47,2)
 elif skill=='market_accounting':
  if tier==0:q=f'In an offline paper simulation, buy {a} units at {b} cents each and pay a total fee of {c} cents. Total cost in cents?';v=a*b+c
  elif tier==1:q=f'Paper simulation: {a} units enter at {b} cents and exit at {b+c} cents. Total fee is {b} cents. Net P&L in cents?';v=a*c-b
  elif tier==2:q=f'Paper simulation: fill {a} units at {b} cents and {c} units at {b+1} cents. Weighted average fill in cents, as exact fraction?';v=Fraction(a*b+c*(b+1),a+c)
  else:q=f'Offline paper ledger: {a} long units gain {b} cents per unit; {c} short units lose {b+1} cents per unit. Pay {a+c} cents in fees. Net cents?';v=a*b-c*(b+1)-a-c
 elif skill=='world_state':
  if tier==0:q=f'A simulated UMBRA inventory starts at {a}, gains {b}, then spends {c}. Signed final inventory?';v=a+b-c
  elif tier==1:q=f'A simulated world has {a} groups of {b} entities; {c} entities leave. Signed remaining count?';v=a*b-c
  elif tier==2:q=f'A simulated world starts with {a} energy. For {b} ticks it gains {c} and spends 1 per tick. Final energy?';v=a+b*(c-1)
  else:q=f'A simulated world starts at {a}; for {b} ticks it first adds {c} then doubles the state, but only on the first three ticks. All later ticks leave it unchanged. Final state?';v=a
  if tier==3:
   for _ in range(min(b,3)):v=2*(v+c)
   # b values above three would be duplicate semantics; make later ticks
   # add one unit instead, so every operand remains relevant.
   q=f'A simulated world starts at {a}; for the first min({b},3) ticks add {c} then double; each remaining tick adds 1. Final state?';v+=max(0,b-3)
 elif skill=='event_time':
  if tier==0:q=f'An event starts at second {a}, lasts {b} seconds, then waits {c} seconds. At what second is it ready?';v=a+b+c
  elif tier==1:q=f'From second {a}, repeat {b} sequential operations lasting {c} seconds each. Final timestamp?';v=a+b*c
  elif tier==2:q=f'Two independent stages start at second {a}; their durations are {b} and {c} seconds. Join waits for both. Join timestamp?';v=a+max(b,c)
  else:q=f'At second {a}, launch {b} sequential tasks lasting {c} seconds each, with a 2-second gap between tasks, not after the last. Final second?';v=a+b*c+2*(b-1)
 elif skill=='code_trace':
  if tier==0:q=f'Trace pseudocode: x={a}; x=x+{b}; x=x-{c}. Final x?';v=a+b-c
  elif tier==1:q=f'Trace pseudocode: x={a}; repeat {b} times: x=x+{c}. Final x?';v=a+b*c
  elif tier==2:q=f'Trace pseudocode: x={a}; repeat {b} times: if iteration number is odd (1-based), add {c}, otherwise subtract 1. Final x?';v=a+((b+1)//2)*c-b//2
  else:q=f'Trace pseudocode: x={a}; for i from 1 through {b}, add {c}*i to x. Final x?';v=a+c*b*(b+1)//2
 elif skill=='statistics':
  if tier==0:q=f'Find the exact arithmetic mean of {a}, {b}, {c}.';v=Fraction(a+b+c,3)
  elif tier==1:q=f'Find the range of observations {a}, {b}, {c}.';v=max(a,b,c)-min(a,b,c)
  elif tier==2:q=f'Group A has {a} observations each equal to {b}; group B has {c} observations each equal to 1. Exact combined mean?';v=Fraction(a*b+c,a+c)
  else:q=f'Find population variance of observations {a}, {b}, {c}, dividing by 3. Exact fraction?';mu=Fraction(a+b+c,3);v=sum((Fraction(x)-mu)**2 for x in (a,b,c))/3
 else:
  if tier==0:q=f'A research queue has {a} tasks, adds {b}, completes {c}. Signed backlog change relative to zero?';v=a+b-c
  elif tier==1:q=f'Allocate {a} workers {b} MiB each plus {c} MiB fixed overhead. Total MiB?';v=a*b+c
  elif tier==2:q=f'A machine has {a+b+c} MiB free, reserves {a} MiB, each worker requires {b} MiB. Maximum whole workers?';v=(b+c)//b
  else:q=f'A queue contains {a} jobs, each uses {b} MiB. Each batch has {b*c} MiB available, all jobs use identical memory and finish before the next batch. Minimum batches?';v=(a+c-1)//c
 body={'version':VERSION,'skill':skill,'tier':tier,'ordinal':ordinal,'question':q,'expected':str(Fraction(v)),
       'source_kind':'authored_generated_evaluation','training_eligible':False,
       'lesson_topic':LESSON_TOPICS[skill],'scope':'generated developmental challenge; not authentic corpus, holdout or training'}
 return {**body,'id':digest(body)}

def prompt(q):
 return 'Solve the following problem without tools. Return exactly one line ANSWER: followed by an integer, decimal or exact fraction. If uncertain return ABSTAIN.\nProblem: '+q['question']

def grade(q,response,done_reason):
 if done_reason=='length':return 'truncated'
 if not isinstance(response,str) or len(response)>24000:return 'format'
 s=response.strip()
 if s=='ABSTAIN':return 'abstain'
 m=re.fullmatch(r'ANSWER: (-?[0-9]{1,24}(?:\.[0-9]{1,24}|/[0-9]{1,24})?)',s)
 if not m:return 'format'
 try:return 'correct' if Fraction(m[1])==Fraction(q['expected']) else 'incorrect'
 except (ValueError,ZeroDivisionError):return 'format'

class Ledger:
 def __init__(self,path):
  self.path=Path(path)
  if self.path.is_symlink():raise ValueError('ledger symlink')
  self.db=sqlite3.connect(self.path,timeout=5)
  self.db.row_factory=sqlite3.Row
  self.db.execute('pragma synchronous=FULL')
  self.db.execute('pragma journal_mode=DELETE')
  self.db.execute('pragma max_page_count='+str(MAX_DB//self.db.execute('pragma page_size').fetchone()[0]))
  self.db.executescript("""CREATE TABLE IF NOT EXISTS attempts(
   attempt INTEGER PRIMARY KEY, model TEXT NOT NULL, digest TEXT NOT NULL,
   skill TEXT NOT NULL, tier INTEGER NOT NULL, ordinal INTEGER NOT NULL,
   question_id TEXT NOT NULL, status TEXT NOT NULL,
   response TEXT, response_hash TEXT, done_reason TEXT, tokens INTEGER,
   seconds REAL, outcome TEXT, error TEXT,
   UNIQUE(model,digest,skill,tier,ordinal));
   CREATE INDEX IF NOT EXISTS attempts_model ON attempts(model,digest,skill,tier,attempt);""")
 def __enter__(self):return self
 def __exit__(self,*args):self.db.close()
 def count(self,model,identity,skill=None):
  sql='select count(*) from attempts where model=? and digest=?'
  args=[model,identity]
  if skill is not None:sql+=' and skill=?';args.append(skill)
  return self.db.execute(sql,args).fetchone()[0]
 def tier(self,model,identity,skill):
  t=self.db.execute('select coalesce(max(tier),0) from attempts where model=? and digest=? and skill=?',(model,identity,skill)).fetchone()[0]
  rows=self.db.execute("select outcome,status from attempts where model=? and digest=? and skill=? and tier=? order by attempt desc limit 8",(model,identity,skill,t)).fetchall()
  # Developmental progression only, never independent mastery certification.
  if t<3 and len(rows)==8 and all(x['status']=='completed' and x['outcome']=='correct' for x in rows):return t+1
  return t
 def reserve(self,model,identity,skill,tier):
  if not isinstance(model,str) or not model or len(model)>200 or not re.fullmatch('[a-f0-9]{64}',identity):raise ValueError('model identity')
  self.db.execute('begin immediate')
  try:
   ordinal=self.db.execute('select coalesce(max(ordinal),-1)+1 from attempts where model=? and digest=? and skill=? and tier=?',(model,identity,skill,tier)).fetchone()[0]
   q=question(skill,tier,ordinal)
   cursor=self.db.execute("insert into attempts(model,digest,skill,tier,ordinal,question_id,status) values (?,?,?,?,?,?,'reserved')",(model,identity,skill,tier,ordinal,q['id']))
   self.db.commit()
   return {'attempt':cursor.lastrowid,'question':q}
  except BaseException:self.db.rollback();raise
 def finish(self,attempt,response,reason,tokens,seconds):
  if type(tokens) is not int or not 0<=tokens<=160 or not isinstance(response,str) or len(response)>24000 or type(seconds) not in (float,int) or not math.isfinite(seconds) or seconds<0 or reason not in ('stop','length'):raise ValueError('invalid inference evidence')
  r=self.db.execute('select * from attempts where attempt=?',(attempt,)).fetchone()
  if not r or r['status']!='reserved':raise ValueError('attempt not reserved')
  q=question(r['skill'],r['tier'],r['ordinal'])
  if q['id']!=r['question_id']:raise ValueError('question identity')
  outcome=grade(q,response,reason)
  with self.db:
   cur=self.db.execute("update attempts set status='completed',response=?,response_hash=?,done_reason=?,tokens=?,seconds=?,outcome=? where attempt=? and status='reserved'",(response,digest(response),reason,tokens,seconds,outcome,attempt))
   if cur.rowcount!=1:raise ValueError('attempt already finalized')
  return outcome
 def fail(self,attempt,error,seconds):
  with self.db:
   self.db.execute("update attempts set status='failed',error=?,seconds=? where attempt=? and status='reserved'",(str(error)[:100],seconds,attempt))
 def audit(self):
  out={'completed_calls':0,'correct':0,'reserved_unknown':0,'failed':0,'errors':[],'models':{},'weight_training':False,'production_authority':False}
  for r in self.db.execute('select * from attempts order by attempt'):
   try:
    q=question(r['skill'],r['tier'],r['ordinal'])
    if q['id']!=r['question_id'] or not re.fullmatch('[a-f0-9]{64}',r['digest']):raise ValueError('identity')
    status=r['status']
    if status=='completed':
     if (not isinstance(r['response'],str) or len(r['response'])>24000 or digest(r['response'])!=r['response_hash'] or
      grade(q,r['response'],r['done_reason'])!=r['outcome'] or r['done_reason'] not in ('stop','length') or
      type(r['tokens']) is not int or not 0<=r['tokens']<=160 or not isinstance(r['seconds'],(int,float)) or not math.isfinite(r['seconds']) or r['seconds']<0):raise ValueError('receipt')
    elif status not in ('reserved','failed'):raise ValueError('status')
    k=r['model']+'@'+r['digest']
    s=out['models'].setdefault(k,{'completed':0,'correct':0,'failed':0,'reserved_unknown':0,'skills':{}})
    if status=='completed':
     out['completed_calls']+=1;out['correct']+=int(r['outcome']=='correct')
     s['completed']+=1;s['correct']+=int(r['outcome']=='correct')
     z=s['skills'].setdefault(r['skill'],{'completed':0,'correct':0,'outcomes':{}})
     z['completed']+=1;z['correct']+=int(r['outcome']=='correct')
     z['outcomes'][r['outcome']]=z['outcomes'].get(r['outcome'],0)+1
    elif status=='reserved':out['reserved_unknown']+=1;s['reserved_unknown']+=1
    else:out['failed']+=1;s['failed']+=1
   except (ValueError,TypeError,KeyError,ZeroDivisionError):
    out['errors'].append(r['attempt'])
  return out

def audit(root):
 p=Path(root)/'experience'/'generated-challenges'/'ledger.sqlite3'
 if not p.is_file():return {'completed_calls':0,'correct':0,'reserved_unknown':0,'failed':0,'errors':[],'models':{},'weight_training':False,'production_authority':False}
 with Ledger(p) as ledger:return ledger.audit()

def run(root,count=2,requested=None,skill=None):
 from student_council import roster
 from source_assist import local_api
 from hf_weight_cache import lock
 from native_lora_train import available_ram
 if type(count) is not int or not 1<=count<=4 or (skill is not None and skill not in SKILLS):raise ValueError('batch budget')
 root=Path(root).resolve();e=root/'experience';bank=e/'generated-challenges'
 if not e.is_dir():raise ValueError('experience root missing')
 if shutil.disk_usage(root).free<6_000_000_000:return {'status':'deferred_storage','production_authority':False}
 bank.mkdir(exist_ok=True)
 p=bank/'ledger.sqlite3'
 if p.exists() and p.stat().st_size>=MAX_DB-1024*1024:return {'status':'deferred_ledger_capacity','production_authority':False}
 try:
  with lock(e/'model-compute.lock'),lock(bank/'research.lock'),Ledger(p) as ledger:
   if (root/'active.lock').exists() or local_api('ps').get('models'):return {'status':'deferred_busy','production_authority':False}
   candidates=[s for s in roster(root) if s['backend']=='ollama' and s['present'] and s['required_ram']<=available_ram() and (requested is None or s['name']==requested)]
   if not candidates:return {'status':'deferred_admission','production_authority':False}
   s=min(candidates,key=lambda s:(ledger.count(s['name'],s['digest']),s['required_ram'],s['name']))
   model,identity=s['name'],s['digest']
   rows=[]
   for _ in range(count):
    if local_api('ps').get('models') or available_ram()<s['required_ram'] or shutil.disk_usage(root).free<6_000_000_000:break
    fresh=next((x for x in local_api('tags')['models'] if x.get('name')==model),{})
    if fresh.get('digest')!=identity:break
    k=skill or min(SKILLS,key=lambda k:(ledger.count(model,identity,k),SKILLS.index(k)))
    tier=ledger.tier(model,identity,k)
    reserved=ledger.reserve(model,identity,k,tier);q=reserved['question'];attempt=reserved['attempt'];started=time.monotonic()
    req={'model':model,'prompt':prompt(q),'stream':False,'keep_alive':0,'options':{'temperature':0,'num_ctx':2048,'num_predict':160,'num_thread':2}}
    if model.startswith('qwen3:') or 'Qwen3-8B' in model:req['think']=False
    try:
     result=local_api('generate',req,180)
     fresh=next((x for x in local_api('tags')['models'] if x.get('name')==model),{})
     if result.get('model')!=model or result.get('done') is not True or fresh.get('digest')!=identity:raise ValueError('model identity')
     outcome=ledger.finish(attempt,result['response'],result['done_reason'],result['eval_count'],round(time.monotonic()-started,4))
     row={'attempt':attempt,'skill':k,'tier':tier,'outcome':outcome,'status':'completed','lesson_topic':q['lesson_topic'] if outcome!='correct' else None}
    except Exception as exc:
     ledger.fail(attempt,type(exc).__name__,round(time.monotonic()-started,4));row={'attempt':attempt,'skill':k,'tier':tier,'status':'failed','error':type(exc).__name__}
    rows.append(row);print(json.dumps({'generated_challenge':row,'model':model}),flush=True)
   n=sum(r['status']=='completed' for r in rows)
   return {'status':'completed' if n==count else 'partial' if rows else 'deferred_admission','model':model,'digest':identity,'model_calls':len(rows),'completed_calls':n,'correct':sum(r.get('outcome')=='correct' for r in rows),'rows':rows,'generated_evaluation':True,'weight_training':False,'production_authority':False}
 except FileExistsError:return {'status':'deferred_busy','production_authority':False}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--count',type=int,default=2);p.add_argument('--model');p.add_argument('--skill',choices=SKILLS);p.add_argument('--audit',action='store_true');a=p.parse_args()
 print(json.dumps(audit(a.root) if a.audit else run(a.root,a.count,a.model,a.skill),ensure_ascii=True))
