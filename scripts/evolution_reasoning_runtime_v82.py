"""Pinned local numerical reasoning with private authenticated replay and bounded admission."""
import hashlib,hmac,json,math,os,shutil,time
import evolution_novel_reasoning_v81 as bench
import evolution_research_v37 as research
import evolution_teacher_v40 as teacher
import evolution_native_ollama_v33 as native
import evolution_model_evidence_v24 as ev
import evolution_fleet_scale_v36 as scale
import evolution_research_orchestrator_v39 as orch
from evolution_reliability_v43 import PINS
MODEL='qwen3:1.7b'
SCHEMA='myriad.generated_reasoning.v82'
STAGES=('pin_before','request','envelope','pin_after','message','score')
PERIOD=14400
def sha(x):return hashlib.sha256(x).hexdigest()
def digest(x):return isinstance(x,str) and len(x)==64 and all(c in '0123456789abcdef' for c in x)
def metadata(seed):
    c=bench.cases(seed)
    return {'schema':SCHEMA,'seed':seed,'model':MODEL,'digest':PINS[MODEL],'case_sha256':sha(ev.canonical(c)),'production_authority':False,'semantic_mastery_certified':False}
def completed(seed,raw,response_sha256,seconds):
    r={**metadata(seed),'status':'completed','raw':raw,'response_sha256':response_sha256,'seconds':seconds,'scores':bench.score(bench.cases(seed),raw)}
    validate(r);return r
def failed(seed,stage,error):
    r={**metadata(seed),'status':'failed','failure_stage':stage,'error_class':error}
    validate(r);return r
def validate(r):
    if not isinstance(r,dict) or r.get('status') not in ('completed','failed') or type(r.get('seed')) is not int:raise ValueError('invalid receipt')
    meta=metadata(r['seed']);extra={'status','raw','response_sha256','seconds','scores'} if r['status']=='completed' else {'status','failure_stage','error_class'}
    if set(r)!=set(meta)|extra or any(ev.canonical(r[k])!=ev.canonical(v) for k,v in meta.items()):raise ValueError('invalid metadata')
    if r['status']=='failed':
        if r['failure_stage'] not in STAGES or not isinstance(r['error_class'],str) or not r['error_class'].isidentifier():raise ValueError('invalid failure')
    else:
        if not digest(r['response_sha256']) or type(r['seconds']) not in (int,float) or not math.isfinite(r['seconds']) or r['seconds']<0:raise ValueError('invalid outcome')
        if ev.canonical(r['scores'])!=ev.canonical(bench.score(bench.cases(r['seed']),r['raw'])):raise ValueError('score replay')
    return True
def seal(r,key):
    x=dict(r);x.pop('hmac_sha256',None);x['hmac_sha256']=ev.sign(x,key);return x
def verify(record,key):
    if not isinstance(record,dict):raise ValueError('invalid record')
    r=dict(record);sig=r.pop('hmac_sha256',None)
    if not digest(sig) or not hmac.compare_digest(sig,ev.sign(r,key)):raise ValueError('authentication')
    return validate(r)
def reserve(root,seed):
    bench.cases(seed)
    if root.is_symlink() or not root.is_dir():raise ValueError('private root')
    p=root/'reasoning-claims-v82'
    if p.is_symlink():raise ValueError('claim root')
    p.mkdir(exist_ok=True)
    marker=p/f'{seed}.claim'
    if marker.is_symlink():raise ValueError('claim symlink')
    try:
        with marker.open('xb') as f:
            f.write(ev.canonical({'schema':'myriad.reasoning_claim.v82','seed':seed,'production_authority':False})+b'\n');f.flush();os.fsync(f.fileno())
    except FileExistsError:return False
    return True
def infer(seed):
    c=bench.cases(seed);stage='pin_before'
    try:
        native._pin(11434,MODEL,PINS[MODEL],10)
        item={'type':'object','properties':{k:{'type':'integer'} for k in ('id','answer','witness')},'required':['id','answer','witness'],'additionalProperties':False}
        fmt={'type':'array','items':item,'minItems':len(c),'maxItems':len(c)}
        stage='request';start=time.monotonic()
        v,raw=teacher.request('/api/chat',{'model':MODEL,'messages':[{'role':'user','content':bench.prompt(c)}],'format':fmt,'think':False,'stream':False,'keep_alive':0,'options':{'num_ctx':3072,'num_predict':256,'num_thread':2,'temperature':0}},65)
        stage='envelope'
        if not isinstance(v,dict) or v.get('model')!=MODEL or v.get('done') is not True or v.get('done_reason')!='stop':raise ValueError('incomplete inference')
        stage='pin_after';native._pin(11434,MODEL,PINS[MODEL],10)
        stage='message';output=v['message']['content']
        if not isinstance(output,str) or len(output)>8192:raise ValueError('invalid output')
        stage='score';return completed(seed,output,sha(raw),round(time.monotonic()-start,3))
    except Exception as e:return failed(seed,stage,type(e).__name__)
def aggregate(r):
    scores=r.get('scores',{});return {'schema':'myriad.generated_reasoning_summary.v82','status':r['status'],'seed':r['seed'],'attempted_tasks':4,'completed_tasks':scores.get('total',0),'answer_correct':scores.get('answer_correct',0),'witness_correct':scores.get('witness_correct',0),'joint_correct':scores.get('joint_correct',0),'errors':[{'stage':r['failure_stage'],'error_class':r['error_class']}] if r['status']=='failed' else [],'production_authority':False,'semantic_mastery_certified':False}
def run(root,virtual):
    if root.is_symlink() or not root.is_dir():raise ValueError('invalid root')
    if scale.free_mb()<2500 or virtual<6000 or shutil.disk_usage(root).free<6*1024**3 or teacher.request('/api/ps')[0].get('models'):
        return {'status':'deferred_resource_guard','production_authority':False}
    seed=int(time.time())//PERIOD;key=ev.secret();history=root/'teacher-v40'
    if history.is_symlink():raise ValueError('history symlink')
    for i,p in enumerate(history.glob('reasoning-v82-*.json'),1):
        if i>4096 or p.is_symlink() or not p.is_file() or p.stat().st_size>65536:raise ValueError('invalid history')
        r=json.loads(p.read_bytes(),object_pairs_hook=research.unique_pairs);verify(r,key)
        if r['seed']==seed:return {'status':'already_attempted','production_authority':False}
    if not reserve(root,seed):return {'status':'already_attempted','production_authority':False}
    r=infer(seed);teacher.save(root,'reasoning-v82',r,key);verify(r,key)
    report=aggregate(r);orch.atomic(root/'aggregate-reasoning-v82.json',report);return report
