"""Fair source-grounded council; one admitted student per cycle, no synthetic training."""
import argparse,hashlib,json,math,re,shutil,subprocess,time
from decimal import Decimal,InvalidOperation
from pathlib import Path
from native_lora_train import available_ram,atomic
from source_assist import local_api,MODELS as OLLAMA
from hf_weight_cache import lock
from human_corpus import audit_records,read_verified,ORIGINAL_ROWS
NATIVE=('HuggingFaceTB/SmolLM2-360M-Instruct','HuggingFaceTB/SmolLM2-1.7B-Instruct','Qwen/Qwen2.5-Coder-0.5B-Instruct','Qwen/Qwen2.5-Coder-1.5B-Instruct','HuggingFaceTB/SmolLM2-135M-Instruct','Qwen/Qwen2.5-Math-1.5B-Instruct','Qwen/Qwen2.5-1.5B-Instruct')
QUERIES=('ICARUS architecture market data indicators','time series forecasting methods','ICARUS backtesting signal execution risk','quantitative investment research','quality diversity archive','sparse identification nonlinear dynamics','reinforcement learning offline datasets')
def load_json(p):
 try:return json.loads(p.read_text(encoding='utf8'))
 except (OSError,ValueError):return {}
def answer_value(s):
 if not isinstance(s,str) or len(s)>24000 or s.count('####')!=1:return None
 m=re.search(r'(?:^|\n)####[ \t]+(-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)[ \t]*$',s.strip())
 if not m:return None
 try:
  v=Decimal(m[1].replace(',',''))
  if not v.is_finite() or abs(v)>Decimal('1e24'):return None
  return format(v.normalize(),'f') if v else '0'
 except InvalidOperation:return None
def grade_answer(given,truth):
 a,b=answer_value(given),answer_value(truth)
 return a is not None and b is not None and a==b
def load_corpus(root):
 train,test=[read_verified(root,r) for r in ORIGINAL_ROWS]
 if train is None or test is None or len(train)!=7473 or len(test)!=1319:raise ValueError('original corpus incomplete')
 report,rows=audit_records(train,test)
 return rows
def choose_student(rows,state,ram):
 eligible=[r for r in rows if r['present'] and r['required_ram']<=ram]
 return min(eligible,key=lambda r:(state.get(r['name'],{}).get('last_attempt',0),r['required_ram'],r['name'])) if eligible else None
def roster(root):
 try:tags={x['name']:x for x in local_api('tags')['models']}
 except Exception:tags={}
 out=[]
 for name in OLLAMA:
  m=tags.get(name,{})
  valid=type(m.get('size')) is int and m['size']>0 and re.fullmatch('[a-f0-9]{64}',str(m.get('digest','')))
  out.append({'name':name,'backend':'ollama','present':bool(valid),'digest':m.get('digest'),'required_ram':m['size']+1600000000 if valid else 10**12,'weight_training':'requires matching verified native checkpoint; no GGUF mutation'})
 receipts={}
 for p in (root/'neural').glob('*/receipt.json'):
  r=load_json(p)
  if r.get('repo') in NATIVE and r.get('native_verified') is True:receipts.setdefault(r['repo'],[]).append((r,p))
 for name in NATIVE:
  candidates=receipts.get(name,[]);valid=len(candidates)==1
  r,p=candidates[0] if valid else ({},None)
  valid=valid and type(r.get('total')) is int and 0<r['total']<4_000_000_000 and re.fullmatch('[a-f0-9]{64}',str(r.get('digest','')))
  out.append({'name':name,'backend':'native','present':bool(valid),'digest':r.get('digest'),'required_ram':2*r['total']+3000000000 if valid else 10**12,'weight_training':'separate audited LoRA required'})
 return out
def lesson(rows,attempt):
 # Train examples are original human solutions; validation answer is never in the prompt.
 training=rows['train'];validation=rows['validation']
 t=training[(attempt*37)%len(training)];v=validation[(attempt*19)%len(validation)]
 if t['question_sha256']==v['question_sha256']:raise ValueError('split overlap')
 return t,v
def lesson_prompt(t,v):
 return 'Study this human-written worked example:\nQuestion: '+t['question']+'\nSolution: '+t['answer']+'\n\nNow solve a DIFFERENT problem. Show your reasoning briefly and finish on a new line with #### followed by only the final numeric answer.\nQuestion: '+v['question']+'\nSolution:'
def ollama_lesson(name,digest,t,v):
 if local_api('ps').get('models'):return {'status':'deferred_busy'}
 m=next((x for x in local_api('tags')['models'] if x.get('name')==name),{})
 if m.get('digest')!=digest or available_ram()<m.get('size',10**12)+1600000000:return {'status':'deferred_identity_or_memory'}
 prompt=lesson_prompt(t,v)
 request={'model':name,'prompt':prompt,'stream':False,'keep_alive':0,'options':{'temperature':0,'num_ctx':2048,'num_predict':320,'num_thread':2}}
 if name.startswith('qwen3:') or 'Qwen3-8B' in name:request['think']=False
 r=local_api('generate',request,180)
 fresh=next((x for x in local_api('tags')['models'] if x.get('name')==name),{})
 if r.get('model')!=name or r.get('done') is not True or fresh.get('digest')!=digest:return {'status':'invalid_response'}
 response=r.get('response','')
 return {'status':'evaluated','correct':grade_answer(response,v['answer']),'response':response[:12000],'lesson_record':t['record_sha256'],'validation_record':v['record_sha256'],'expected_numeric':answer_value(v['answer']),'predicted_numeric':answer_value(response),'scope':'one-shot human example, rotating validation; no weight update'}
def compact_feed(r):
 return {k:r.get(k) for k in ('status','query','model','specialists','errors','ranked_sources','answer','weight_training')}
def run(root,training,requested=None):
 bank=root/'experience'/'student-council';bank.mkdir(parents=True,exist_ok=True)
 with lock(root/'experience'/'model-compute.lock'),lock(bank/'council.lock'):
  state=load_json(bank/'state.json');students=state.get('students',{})
  rows=roster(root);ram=available_ram()
  if requested:rows=[r for r in rows if r['name']==requested]
  student=choose_student(rows,students,ram)
  if not student:return {'status':'deferred_memory_or_availability','free_ram':ram,'roster':rows,'weight_training':False}
  if (training/'bootstrap.lock').exists() or local_api('ps').get('models'):return {'status':'deferred_busy','weight_training':False}
  name=student['name'];digest=student['digest'];s=students.get(name,{})
  if s.get('digest')!=digest:s={'digest':digest,'attempts':0,'evaluated':0,'correct':0,'verified_feeds':0}
  attempt=s['attempts'];query=QUERIES[attempt%len(QUERIES)]
  s['attempts']+=1;s['last_attempt']=int(time.time());students[name]=s
  atomic(bank/'state.json',{'students':students,'roster':roster(root)})
  try:
   corpus=load_corpus(root);t,v=lesson(corpus,attempt)
   if student['backend']=='ollama':
    from specialist_feed import run as feed
    try:f=compact_feed(feed(root,query,name))
    except Exception as e:f={'status':'failed','reason':type(e).__name__}
    try:m=ollama_lesson(name,digest,t,v)
    except Exception as e:m={'status':'failed','reason':type(e).__name__}
   else:
    py=training/'venv'/'Scripts'/'python.exe'
    if not py.is_file():raise ValueError('native runtime missing')
    q=subprocess.run([str(py),str(Path(__file__).with_name('native_student.py')),'--root',str(root),'--model',name,'--attempt',str(attempt),'--query',query],capture_output=True,text=True,timeout=600,check=True)
    result=json.loads(q.stdout.splitlines()[-1]);f=result['feed'];m=result['lesson']
  except Exception as e:f={'status':'failed','reason':type(e).__name__};m={'status':'not_evaluated'}
  if f.get('status')=='feed_verified':s['verified_feeds']+=1
  if m.get('status')=='evaluated':s['evaluated']+=1;s['correct']+=int(m.get('correct') is True)
  result={'status':'evaluated' if m.get('status')=='evaluated' else f.get('status','deferred'),'student':student,'feed':f,'lesson':m,'cumulative':s,'weight_training':False,'production_authority':False}
  # Bound storage: last attempt per model plus counters, and latest aggregate.
  key=hashlib.sha256(name.encode()).hexdigest()[:20];atomic(bank/(key+'.json'),result);atomic(bank/'latest.json',result);atomic(bank/'state.json',{'students':students,'roster':roster(root)})
  return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--training',type=Path,required=True);p.add_argument('--model');a=p.parse_args()
 print(json.dumps(run(a.root,a.training,a.model),ensure_ascii=True))
