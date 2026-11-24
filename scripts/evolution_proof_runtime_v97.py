"""Bounded live proof-feedback capture, distinct from synthetic qualification.

Only the existing protected scheduler may invoke run. Local pin checks and
self-reported token counts are not independent model-origin attestation.
"""
import hashlib,hmac,json,math,re,shutil,time
from pathlib import Path

MODEL='qwen3:1.7b'
CAP=256
CTX=3072
PERIOD=14400
ARMS=('initial','control','guided')
STAGES=('admission','pin_before','request','envelope','pin_after','message')
SCHEMA='myriad.proof_runtime.v97'


def sha(x):return hashlib.sha256(x).hexdigest()
def digest(x):return isinstance(x,str) and bool(re.fullmatch('[a-f0-9]{64}',x))
def integer(x,lo,hi):return type(x) is int and lo<=x<=hi

def body(prompt):
    arr={'type':'array','items':{'type':'integer'},'minItems':1,'maxItems':32}
    def cert(keys):
        return {'type':'object','properties':{'answer':{'type':'integer'},**{k:arr for k in keys}},'required':['answer',*keys],'additionalProperties':False}
    item={'type':'object','properties':{'id':{'type':'integer','enum':[0,1]},'certificate':{'oneOf':[cert(['path','potentials']),cert(['flows','cut'])]}},'required':['id','certificate'],'additionalProperties':False}
    return {'model':MODEL,'messages':[{'role':'user','content':prompt}],'format':{'type':'array','items':item,'minItems':2,'maxItems':2},'stream':False,'think':False,'keep_alive':0,'options':{'num_ctx':CTX,'num_predict':CAP,'num_thread':2,'temperature':0}}

def failure(arm,prompt,stage,error,started,seconds):
    c={'arm':arm,'prompt_sha256':sha(prompt.encode()),'status':'failed','error_class':error}
    return c,{'arm':arm,'stage':stage,'request_started':started,'pin_verified':False,'seconds':seconds}

def capture(arm,prompt,model_digest,pin,request):
    if arm not in ARMS or not isinstance(prompt,str) or not 1<=len(prompt)<=32768 or not digest(model_digest):raise ValueError('capture configuration')
    stage='pin_before';started=False;start=time.monotonic()
    try:
        pin(11434,MODEL,model_digest,10)
        stage='request';started=True
        v,raw=request('/api/chat',body(prompt),45)
        stage='envelope'
        if not isinstance(v,dict) or v.get('model')!=MODEL or v.get('done') is not True or v.get('done_reason')!='stop' or not isinstance(raw,bytes) or not 1<=len(raw)<=4*1024**2:raise ValueError('incomplete response')
        if not integer(v.get('prompt_eval_count'),1,CTX) or not integer(v.get('eval_count'),1,CAP):raise ValueError('token evidence')
        stage='pin_after';pin(11434,MODEL,model_digest,10)
        stage='message';output=v['message']['content']
        if not isinstance(output,str) or not 1<=len(output)<=8192:raise ValueError('output bounds')
        return {'arm':arm,'prompt_sha256':sha(prompt.encode()),'status':'completed','raw':output},{'arm':arm,'request_started':True,'pin_verified':True,'seconds':round(time.monotonic()-start,3),'response_sha256':sha(raw),'prompt_tokens':v['prompt_eval_count'],'completion_tokens':v['eval_count']}
    except Exception as e:return failure(arm,prompt,stage,type(e).__name__,started,round(time.monotonic()-start,3))

def validate_capture(call,meta):
    if not isinstance(call,dict) or not isinstance(meta,dict) or call.get('arm') not in ARMS or call.get('arm')!=meta.get('arm') or not digest(call.get('prompt_sha256')):raise ValueError('capture identity')
    common={'arm','request_started','pin_verified','seconds'}
    s=meta.get('seconds')
    if type(s) not in (int,float) or not math.isfinite(s) or s<0 or type(meta.get('request_started')) is not bool:raise ValueError('capture timing')
    if call.get('status')=='completed':
        if set(meta)!=common|{'response_sha256','prompt_tokens','completion_tokens'} or set(call)!={'arm','prompt_sha256','status','raw'} or meta['request_started'] is not True or meta['pin_verified'] is not True or not digest(meta['response_sha256']) or not integer(meta['prompt_tokens'],1,CTX) or not integer(meta['completion_tokens'],1,CAP) or not isinstance(call['raw'],str) or not 1<=len(call['raw'])<=8192:raise ValueError('capture completion')
    elif call.get('status')=='failed':
        if set(meta)!=common|{'stage'} or set(call)!={'arm','prompt_sha256','status','error_class'} or meta['pin_verified'] is not False or meta['stage'] not in STAGES or meta['request_started']!=(meta['stage'] not in ('admission','pin_before')) or not isinstance(call['error_class'],str) or not re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,79}',call['error_class']):raise ValueError('capture failure')
    else:raise ValueError('capture status')
    return True

def experiment(seed,model_digest,pin,request,admit):
    import evolution_proof_feedback_v90 as bench
    if not digest(model_digest):raise ValueError('model digest')
    q=bench.cases(seed);calls=[];captures=[];initial=None;start=time.monotonic()
    for arm in bench.order(seed):
        p=bench.prompt(q,arm,initial)
        try:allowed=time.monotonic()-start<=120 and admit()
        except Exception as e:c,m=failure(arm,p,'admission',type(e).__name__,False,0)
        else:
            if not allowed:c,m=failure(arm,p,'admission','ResourceDeferred',False,0)
            else:c,m=capture(arm,p,model_digest,pin,request)
        calls.append(c);captures.append(m)
        if arm=='initial':initial=c.get('raw')
    return {'schema':SCHEMA,'model':MODEL,'digest':model_digest,'seed':seed,'status':'completed' if all(c['status']=='completed' for c in calls) else 'failed','feedback_receipt':bench.assemble(seed,calls),'captures':captures,'requested_completion_budget':3*CAP,'origin_authenticated':False,'production_authority':False,'semantic_mastery_certified':False}

def validate(r,model_digest):
    import evolution_proof_feedback_v90 as bench
    required={'schema','model','digest','seed','status','feedback_receipt','captures','requested_completion_budget','origin_authenticated','production_authority','semantic_mastery_certified'}
    if not isinstance(r,dict) or set(r)!=required or r['schema']!=SCHEMA or r['model']!=MODEL or not digest(model_digest) or r['digest']!=model_digest or not integer(r['seed'],0,2**31-1) or type(r['requested_completion_budget']) is not int or r['requested_completion_budget']!=3*CAP or any(r[x] is not False for x in ('origin_authenticated','production_authority','semantic_mastery_certified')):raise ValueError('proof receipt identity')
    x=r['feedback_receipt']
    if not bench.verify(x) or x['seed']!=r['seed']:raise ValueError('proof replay')
    if not isinstance(r['captures'],list) or len(r['captures'])!=3:raise ValueError('capture coverage')
    for c,m in zip(x['calls'],r['captures']):validate_capture(c,m)
    if r['status']!=('completed' if all(c['status']=='completed' for c in x['calls']) else 'failed'):raise ValueError('receipt status')
    return True

def verify(record,key,model_digest):
    import evolution_model_evidence_v24 as ev
    if not isinstance(record,dict):raise ValueError('receipt')
    r=dict(record);sig=r.pop('hmac_sha256',None)
    if not digest(sig) or not hmac.compare_digest(sig,ev.sign(r,key)):raise ValueError('authentication')
    return validate(r,model_digest)

def aggregate(r):
    c=r['captures'];scores=r['feedback_receipt']['summary']
    good=[x for x in c if x['pin_verified']]
    return {'schema':'myriad.proof_runtime_summary.v97','seed':r['seed'],'status':r['status'],'request_attempts':sum(x['request_started'] for x in c),'verified_completions':len(good),'reported_prompt_tokens':sum(x['prompt_tokens'] for x in good),'reported_completion_tokens':sum(x['completion_tokens'] for x in good),'requested_completion_budget':3*CAP,'scores':scores,'errors':[{'arm':x['arm'],'stage':m['stage'],'error_class':x['error_class']} for x,m in zip(r['feedback_receipt']['calls'],c) if x['status']=='failed'],'production_authority':False,'origin_authenticated':False,'semantic_mastery_certified':False}

def run(root,virtual):
    import evolution_fleet_scale_v36 as scale
    import evolution_teacher_v40 as teacher
    import evolution_model_evidence_v24 as ev
    import evolution_native_ollama_v33 as native
    import evolution_research_orchestrator_v39 as orch
    import evolution_window_claim_v96 as claims
    from evolution_reliability_v43 import PINS
    root=Path(root)
    def admit():return scale.free_mb()>=2500 and virtual>=6000 and shutil.disk_usage(root).free>=6*1024**3 and not teacher.request('/api/ps')[0].get('models')
    if not admit():return {'status':'deferred_resource_guard','production_authority':False}
    seed=int(time.time())//PERIOD;key=ev.secret();d=PINS[MODEL]
    if not claims.reserve(root,seed,key,lambda r,k:verify(r,k,d),family='proof'):return {'status':'already_attempted','production_authority':False}
    r=experiment(seed,d,native._pin,teacher.request,admit);validate(r,d)
    teacher.save(root,'proof-feedback-v97',r,key);verify(r,key,d)
    report=aggregate(r);orch.atomic(root/'aggregate-proof-feedback-v97.json',report);return report
