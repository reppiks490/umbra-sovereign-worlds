"""Bounded CPU LoRA pilot on verified native checkpoints; never overwrite originals."""
import argparse,ctypes,hashlib,json,math,os,re,shutil,time
from pathlib import Path
from native_training_bootstrap import SOURCES
from learning_workspace import ReplayBank,plan_replay,summarize_losses,retention_gate
MODELS={'qwen3:0.6b':SOURCES[0],'granite4:350m':SOURCES[1]}
def required_memory(model):
 if model not in MODELS:raise ValueError('unsupported model')
 return 7500000000 if model=='qwen3:0.6b' else 4500000000
def validate_corpus(x,model):
 if x.get('schema')!='umbra.swarm.corpus.v1' or x.get('model')!=model or model not in MODELS:raise ValueError('corpus identity')
 seen=set()
 for key,lo,hi in [('training',32,128),('retention',8,32),('transfer',8,32)]:
  rows=x.get(key)
  if not isinstance(rows,list) or not lo<=len(rows)<=hi:raise ValueError('corpus bounds')
  for r in rows:
   p=r.get('prompt');a=r.get('answer');opts=r.get('options')
   if not isinstance(p,str) or not 1<=len(p)<=512 or not isinstance(a,str) or not isinstance(opts,list) or len(opts)!=4 or not all(isinstance(o,str) and 1<=len(o)<=256 for o in opts) or len(set(opts))!=4 or a not in opts:raise ValueError('corpus example')
   h=hashlib.sha256(p.encode()).hexdigest()
   if h!=r.get('prompt_sha256') or h in seen:raise ValueError('duplicate or corrupted prompt')
   seen.add(h)
   if r.get('source')=='teacher' and (r.get('teacher')==model or not re.fullmatch('[a-f0-9]{64}',r.get('teacher_digest','')) or not re.fullmatch('[a-f0-9]{64}',r.get('lesson_evidence',''))):raise ValueError('teacher provenance')
 return x
def promotion_gate(before,after):
 return all(math.isfinite(x) and x>=0 for x in [before['retention'],before['transfer'],after['retention'],after['transfer']]) and after['retention']<=before['retention']+.02 and after['transfer']<before['transfer']-.01
def adaptive_budget(last,rank):
 if rank not in (4,8,16):raise ValueError('unsupported incumbent rank')
 try:
  ok=last['status']=='evaluated' and last['accepted'] is True and last['adapter_weight_training'] is True and last['rank']==rank and last['steps'] in (4,8,16) and promotion_gate(last['before'],last['after'])
 except (TypeError,KeyError,ValueError):ok=False
 return {'steps':min(16,last['steps']*2) if ok else 4,'rank':min(16,rank*2) if ok else rank}
def growth_slices(old,new,kind):
 if len(old)!=2 or len(new)!=2:raise ValueError('rank tensor dimensions')
 if kind=='lora_A' and old[1]==new[1] and 0<old[0]<=new[0]:return (slice(0,old[0]),slice(None))
 if kind=='lora_B' and old[0]==new[0] and 0<old[1]<=new[1]:return (slice(None),slice(0,old[1]))
 raise ValueError('invalid rank growth')
def available_ram():
 if os.name=='nt':
  from ctypes import wintypes
  class M(ctypes.Structure):_fields_=[('length',wintypes.DWORD),('load',wintypes.DWORD)]+[(k,ctypes.c_ulonglong) for k in ('total','avail','page','pageavail','virtual','virtualavail','extended')]
  m=M();m.length=ctypes.sizeof(m)
  if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):raise ValueError('memory unavailable')
  return m.avail
 return os.sysconf('SC_AVPHYS_PAGES')*os.sysconf('SC_PAGE_SIZE')
def filehash(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def read_json(p,limit=2*1024**2):
 if p.is_symlink() or not p.is_file() or p.stat().st_size>limit:raise ValueError('invalid JSON file')
 return json.loads(p.read_text(encoding='utf8'))
def verified_source(root,model):
 repo,rev,sha,size=MODELS[model];p=root/'sources'/(repo.replace('/','--')+'--'+rev[:12]);r=read_json(p/'receipt.json')
 if r.get('repo')!=repo or r.get('revision')!=rev or r.get('weights_sha256')!=sha or r.get('native_verified') is not True:raise ValueError('source identity')
 files=r.get('files')
 if not isinstance(files,list) or len(files)>20 or len({x['name'] for x in files})!=len(files):raise ValueError('source inventory')
 for x in files:
  name=x['name'];f=p/name
  if not re.fullmatch('[A-Za-z0-9_.-]+',name) or name in ('.','..') or f.is_symlink() or not f.is_file() or f.stat().st_size!=x['size'] or filehash(f)!=x['sha256']:raise ValueError('source corruption')
 w=p/'model.safetensors'
 if w.stat().st_size!=size or filehash(w)!=sha:raise ValueError('source weight mismatch')
 return p
def atomic(p,x):
 t=p.with_name(p.name+'.'+str(os.getpid())+'.tmp')
 with t.open('x',encoding='utf8') as f:json.dump(x,f,indent=2);f.flush();os.fsync(f.fileno())
 os.replace(t,p)
def run(root,workspace,model,corpus,steps=4):
 if type(steps) is not int or not 1<=steps<=16:raise ValueError('step budget')
 if not (root/'ready.json').is_file():return {'status':'deferred_bootstrap'}
 if available_ram()<required_memory(model):return {'status':'deferred_memory','required_bytes':required_memory(model),'free_bytes':available_ram()}
 if shutil.disk_usage(workspace).free<8000000000:return {'status':'deferred_storage'}
 data=validate_corpus(read_json(corpus),model);source=verified_source(root,model)
 bank=workspace/'llm_adapters'/model.replace(':','-');bank.mkdir(parents=True,exist_ok=True)
 if sum(p.stat().st_size for p in (workspace/'llm_adapters').rglob('*') if p.is_file())>500000000:return {'status':'deferred_adapter_budget'}
 lock=bank/'train.lock'
 try:
  with lock.open('x') as f:f.write(str(os.getpid()))
 except FileExistsError:return {'status':'deferred_lock'}
 try:
  import torch
  from transformers import AutoModelForCausalLM,AutoTokenizer
  from peft import LoraConfig,get_peft_model,PeftModel,get_peft_model_state_dict,set_peft_model_state_dict
  from safetensors.torch import load_file
  torch.set_num_threads(1);torch.manual_seed(int(data.get('seed',1)))
  tok=AutoTokenizer.from_pretrained(str(source),local_files_only=True,trust_remote_code=False)
  base=AutoModelForCausalLM.from_pretrained(str(source),local_files_only=True,trust_remote_code=False,use_safetensors=True,torch_dtype=torch.float32)
  base.config.use_cache=False
  active=bank/'active.json';prior=None;rank=4;old_rank=4
  if active.exists():
   prior=read_json(active)
   name=prior.get('name','')
   if not re.fullmatch('adapter-[a-f0-9]{16}',name) or prior.get('base_sha256')!=MODELS[model][2]:raise ValueError('incumbent identity')
   folder=bank/name
   for k in ('adapter_model.safetensors','adapter_config.json'):
    if (folder/k).is_symlink() or filehash(folder/k)!=prior['files'][k]:raise ValueError('incumbent corruption')
   config=read_json(folder/'adapter_config.json');old_rank=config.get('r')
   if old_rank not in (4,8,16) or config.get('lora_alpha')!=2*old_rank or config.get('use_rslora') or config.get('rank_pattern') or config.get('alpha_pattern') or set(config.get('target_modules',[]))!={'q_proj','v_proj'}:raise ValueError('unsupported incumbent adapter')
   last=read_json(bank/'last-result.json') if (bank/'last-result.json').exists() else None
   if last and (last.get('model')!=model or last.get('base_sha256')!=MODELS[model][2] or last.get('accepted_adapter')!=name):last=None
   budget=adaptive_budget(last,old_rank);rank=budget['rank'];steps=budget['steps']
   if rank==old_rank:net=PeftModel.from_pretrained(base,str(folder),is_trainable=True,local_files_only=True)
   else:
    net=get_peft_model(base,LoraConfig(r=rank,lora_alpha=2*rank,lora_dropout=0.0,target_modules=['q_proj','v_proj'],task_type='CAUSAL_LM'))
    prior_weights=load_file(str(folder/'adapter_model.safetensors'),device='cpu');fresh=get_peft_model_state_dict(net)
    if set(fresh)!=set(prior_weights):raise ValueError('rank growth state identity')
    expanded={}
    for key,old in prior_weights.items():
     kind='lora_A' if '.lora_A.' in key else 'lora_B' if '.lora_B.' in key else None
     if kind is None or not torch.isfinite(old).all():raise ValueError('unsupported rank growth tensor')
     target=fresh[key].detach().clone()
     if kind=='lora_B':target.zero_()
     target[growth_slices(tuple(old.shape),tuple(target.shape),kind)].copy_(old.to(target.dtype))
     expanded[key]=target
    set_peft_model_state_dict(net,expanded)
    actual=get_peft_model_state_dict(net)
    if any(not torch.equal(actual[k],v) for k,v in expanded.items()):raise ValueError('rank growth load mismatch')
  else:
   net=get_peft_model(base,LoraConfig(r=rank,lora_alpha=2*rank,lora_dropout=0.0,target_modules=['q_proj','v_proj'],task_type='CAUSAL_LM'))
  params=[p for p in net.parameters() if p.requires_grad]
  if not params or sum(p.numel() for p in params)>20000000:raise ValueError('adapter budget')
  def batch(row):
   prefix='Question: '+row['prompt']+'\nOptions: '+ ' | '.join(row['options'])+'\nAnswer:'
   a=tok.encode(prefix,add_special_tokens=False);b=tok.encode(' '+row['answer'],add_special_tokens=False)
   if not a or not b or len(a+b)>256:raise ValueError('sequence budget')
   return {'input_ids':torch.tensor([a+b]),'labels':torch.tensor([[-100]*len(a)+b]),'attention_mask':torch.ones((1,len(a+b)),dtype=torch.long)}
  begin=time.monotonic()
  def guard():
   if time.monotonic()-begin>900 or available_ram()<1000000000:raise ValueError('training runtime budget')
  def evaluate(rows,anchor_ids):
   net.eval();out=[]
   with torch.no_grad():
    for r in rows:guard();out.append(float(net(**batch(r)).loss))
   if not all(math.isfinite(x) for x in out):raise ValueError('nonfinite evaluation')
   return summarize_losses(rows,out,anchor_ids)
  with ReplayBank(workspace/'learning-workspace') as ledger:
   snapshot=ledger.ingest(data)
   counts=ledger.counts(model)
   pool=ledger.candidates(model)
   # Preserve fixed anchors separately from rotating holdouts.
   anchors={k:ledger.anchors(model,k) for k in ('retention','transfer')}
  if any(len(v)!=8 for v in anchors.values()):raise ValueError('missing immutable anchors')
  selected=plan_replay(pool,steps,counts,sum(counts.values()))
  if len(selected)!=steps:raise ValueError('replay supply')
  evaluation_sets={k:anchors[k]+[r for r in data[k] if r['prompt_sha256'] not in {a['prompt_sha256'] for a in anchors[k]}][:24] for k in ('retention','transfer')}
  anchor_ids={k:[r['prompt_sha256'] for r in anchors[k]] for k in anchors}
  before_detail={k:evaluate(evaluation_sets[k],anchor_ids[k]) for k in anchors}
  before={k:v['mean'] for k,v in before_detail.items()}
  anchor_before={k:v['anchor_mean'] for k,v in before_detail.items()}
  opt=torch.optim.AdamW(params,lr=1e-4);losses=[]
  teach=[r for r in selected if r['source']=='teacher']
  net.train()
  for r in selected:
   guard()
   opt.zero_grad();loss=net(**batch(r)).loss
   if not torch.isfinite(loss):raise ValueError('nonfinite loss')
   loss.backward();torch.nn.utils.clip_grad_norm_(params,1.0);opt.step();losses.append(float(loss.detach()))
  after_detail={k:evaluate(evaluation_sets[k],anchor_ids[k]) for k in anchors}
  after={k:v['mean'] for k,v in after_detail.items()}
  anchor_after={k:v['anchor_mean'] for k,v in after_detail.items()}
  accepted=retention_gate(before,after,anchor_before,anchor_after)
  result={'status':'evaluated','model':model,'base_sha256':MODELS[model][2],'before':before,'after':after,'steps':steps,'rank':rank,'previous_rank':old_rank,'losses':losses,'trainable_parameters':sum(p.numel() for p in params),'accepted':accepted,'teacher_examples':len(teach),'scope':'synthetic answer-only NLL pilot; not general reasoning qualification','external_base_weights_modified':False,'adapter_weight_training':True,'production_authority':False}
  result.update({'domain_evaluation_before':before_detail,'domain_evaluation_after':after_detail,'anchor_before':anchor_before,'anchor_after':anchor_after,'replay_snapshot':snapshot,'replay_prompts':[r['prompt_sha256'] for r in selected],'replay_domains':sorted({r['domain'] for r in selected}),'evaluation_set_sha256':{k:hashlib.sha256(json.dumps([r['prompt_sha256'] for r in v]).encode()).hexdigest() for k,v in evaluation_sets.items()}})
  attempt_id='train-'+hashlib.sha256((snapshot+model+str(time.time_ns())).encode()).hexdigest()
  result['attempt_id']=attempt_id
  if accepted:
   name='adapter-'+hashlib.sha256((filehash(corpus)+str(time.time_ns())).encode()).hexdigest()[:16];stage=bank/(name+'.stage');stage.mkdir()
   net.save_pretrained(str(stage),safe_serialization=True)
   files={k:filehash(stage/k) for k in ('adapter_model.safetensors','adapter_config.json')}
   if sum(p.stat().st_size for p in stage.rglob('*') if p.is_file())>50000000:raise ValueError('adapter size')
   result['accepted_adapter']=name
   atomic(stage/'receipt.json',result);stage.rename(bank/name)
  with ReplayBank(workspace/'learning-workspace') as ledger:ledger.record_attempt(attempt_id,model,result['replay_prompts'],accepted,result)
  if accepted:atomic(active,{'name':name,'base_sha256':MODELS[model][2],'files':files,'corpus_sha256':filehash(corpus)})
  atomic(bank/'last-result.json',result);return result
 finally:lock.unlink(missing_ok=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--workspace',type=Path,required=True);p.add_argument('--model',choices=list(MODELS),required=True);p.add_argument('--corpus',type=Path,required=True);p.add_argument('--steps',type=int,default=4);a=p.parse_args()
 print(json.dumps(run(a.root.resolve(),a.workspace.resolve(),a.model,a.corpus.resolve(),a.steps)),flush=True)
