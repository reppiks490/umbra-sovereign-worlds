"""Model-selected inert numerical tool dispatch with independently computed references."""
import hashlib,hmac,itertools,json,math,random,time,shutil
from pathlib import Path
import evolution_algorithms_v49 as a
import evolution_algorithms_v56 as b
import evolution_algorithms_v60 as c
import evolution_teacher_v40 as teacher
import evolution_model_evidence_v24 as ev
import evolution_fleet_scale_v36 as scale
import evolution_research_orchestrator_v39 as orch
import evolution_native_ollama_v33 as native
from evolution_reliability_v43 import PINS
import evolution_window_claim_v96 as claims
EXPECTED=('dijkstra','max_flow','knapsack','inversions','welford','miller_rabin','quickselect','fft')
QUESTIONS=('Minimum total nonnegative edge cost from vertex 0 to 4.','Maximum units that can move from vertex 0 to 4 subject to directed capacities.','Maximum total value of indivisible items under the weight budget.','Count pairs in a sequence where an earlier number exceeds a later number.','Calculate sample variance using a numerically stable streaming method.','Determine whether the given positive integer is prime.','Find the element at the specified zero-based rank without sorting the full input.','Calculate the complex discrete frequency spectrum of a power-of-two signal.')
def cases(seed):
    if type(seed) is not int or seed<0:raise ValueError('invalid seed')
    r=random.Random(seed);g={i:{} for i in range(5)}
    for i in range(4):
        g[i][i+1]=r.randint(1,9)
        for j in range(i+2,5):
            if r.random()<.6:g[i][j]=r.randint(1,9)
    items=[(r.randint(1,6),r.randint(1,15)) for _ in range(7)]
    x=[r.randint(-20,20) for _ in range(12)];y=[r.randint(-10,10) for _ in range(8)]
    params=(g,g,{'weights':[w for w,v in items],'values':[v for w,v in items],'capacity':12},x,x,r.randint(100,9999),{'values':x,'k':5},y)
    return [{'id':i,'question':q,'input':p} for i,(q,p) in enumerate(zip(QUESTIONS,params))]
def reference(case):
    i=case['id'];x=case['input']
    if i==0:
        paths=[]
        for k in range(4):
            for mid in itertools.permutations(range(1,4),k):
                path=(0,)+mid+(4,)
                if all(v in x[u] for u,v in zip(path,path[1:])):paths.append(sum(x[u][v] for u,v in zip(path,path[1:])))
        return min(paths)
    if i==1:
        return min(sum(w for u in cut for v,w in x[u].items() if v not in cut) for k in range(4) for mid in itertools.combinations(range(1,4),k) for cut in [{0,*mid}])
    if i==2:
        w=x['weights'];v=x['values']
        return max(sum(v[j] for j in range(len(w)) if mask>>j&1) for mask in range(1<<len(w)) if sum(w[j] for j in range(len(w)) if mask>>j&1)<=x['capacity'])
    if i==3:return sum(x[j]>x[k] for j in range(len(x)) for k in range(j+1,len(x)))
    if i==4:
        mu=math.fsum(x)/len(x);return math.fsum((v-mu)**2 for v in x)/(len(x)-1)
    if i==5:return x>=2 and all(x%d for d in range(2,math.isqrt(x)+1))
    if i==6:return sorted(x['values'])[x['k']]
    if i==7:return [[sum(v*math.cos(2*math.pi*k*j/len(x)) for j,v in enumerate(x)),sum(-v*math.sin(2*math.pi*k*j/len(x)) for j,v in enumerate(x))] for k in range(len(x))]
    raise ValueError('unknown task')
def evaluate(case,method):
    if method not in EXPECTED:raise ValueError('unapproved tool')
    i=case['id'];x=case['input']
    if method!=EXPECTED[i]:return {'id':i,'method':method,'executed':False,'qualified':False,'reason':'incompatible algorithm contract'}
    if i==0:v=a.dijkstra(x,0)[4]
    elif i==1:v=b.max_flow(x,0,4)
    elif i==2:v=b.knapsack(x['weights'],x['values'],x['capacity'])
    elif i==3:v=c.inversions(x)
    elif i==4:v=b.welford(x)[1]
    elif i==5:v=c.miller_rabin(x)
    elif i==6:v=a.quickselect(x['values'],x['k'])
    elif i==7:v=[[z.real,z.imag] for z in c.fft(x)]
    else:raise ValueError('unknown tool')
    expected=reference(case)
    if i==7:ok=all(abs(u-w)<1e-8 for row1,row2 in zip(v,expected) for u,w in zip(row1,row2)) and len(v)==len(expected)
    elif i==5:ok=type(v) is bool and v==expected
    else:ok=math.isclose(v,expected,abs_tol=1e-9,rel_tol=1e-9)
    return {'id':i,'method':method,'executed':True,'qualified':ok,'result':v,'reference':expected}
def prompt(cases):
    return 'Select the best numerical method for each question. Return a JSON array of method names in the given order. Available methods: '+', '.join(sorted(EXPECTED))+'. Questions: '+json.dumps([{'id':q['id'],'question':q['question']} for q in cases],separators=(',',':'))
def decode(cases,raw):
    v=json.loads(raw)
    if not isinstance(v,list) or len(v)!=len(cases) or any(not isinstance(x,str) or x not in EXPECTED for x in v):raise ValueError('invalid model plan')
    return v
def verify(record,key):
    if not isinstance(record,dict):raise ValueError('invalid receipt')
    r=dict(record);sig=r.pop('hmac_sha256',None)
    hex64=lambda s:isinstance(s,str) and len(s)==64 and all(c in '0123456789abcdef' for c in s)
    if not hex64(sig) or not hmac.compare_digest(ev.sign(r,key),sig):raise ValueError('invalid authentication')
    base={'schema','seed','model','digest','case_sha256','production_authority','arbitrary_code_execution','status'}
    status=r.get('status')
    if status not in ('completed','failed'):raise ValueError('invalid status')
    extra={'raw','response_sha256','results'} if status=='completed' else {'error_class'}
    if set(r)!=base|extra or r['schema']!='myriad.tool_research.v64' or r['model']!='qwen3:1.7b' or r['digest']!=PINS['qwen3:1.7b'] or r['production_authority'] is not False or r['arbitrary_code_execution'] is not False:raise ValueError('invalid metadata')
    if type(r['seed']) is not int or not 0<=r['seed']<=2**63-1:raise ValueError('invalid seed')
    c_=cases(r['seed'])
    if r['case_sha256']!=hashlib.sha256(ev.canonical(c_)).hexdigest():raise ValueError('case identity')
    if status=='failed':
        e=r['error_class']
        if not isinstance(e,str) or not 1<=len(e)<=80 or not e.isidentifier():raise ValueError('invalid failure')
    else:
        if not hex64(r['response_sha256']) or not isinstance(r['raw'],str) or not 1<=len(r['raw'])<=8192 or not isinstance(r['results'],list):raise ValueError('invalid outcome')
        expected=[evaluate(q,m) for q,m in zip(c_,decode(c_,r['raw']))]
        if ev.canonical(r['results'])!=ev.canonical(expected):raise ValueError('replay mismatch')
    return True

def run(root,virtual):
    if scale.free_mb()<2500 or virtual<6000 or shutil.disk_usage(root).free<6*1024**3:return {'status':'deferred_resource','production_authority':False}
    if teacher.request('/api/ps')[0].get('models'):return {'status':'deferred_resident_model','production_authority':False}
    key=ev.secret();seed=int(time.time())//300;model='qwen3:1.7b';digest=PINS[model]
    if not claims.reserve(root,seed,key,verify):return {'status':'deferred_duplicate_window','production_authority':False}
    c_=cases(seed);r={'schema':'myriad.tool_research.v64','seed':seed,'model':model,'digest':digest,'case_sha256':hashlib.sha256(ev.canonical(c_)).hexdigest(),'production_authority':False,'arbitrary_code_execution':False}
    try:
        native._pin(11434,model,digest,10)
        fmt={'type':'array','items':{'type':'string','enum':list(EXPECTED)},'minItems':8,'maxItems':8}
        body={'model':model,'messages':[{'role':'user','content':prompt(c_)}],'format':fmt,'stream':False,'think':False,'keep_alive':0,'options':{'num_ctx':2048,'num_predict':128,'num_thread':2,'temperature':0}}
        v,raw=teacher.request('/api/chat',body,90)
        if v.get('model')!=model or v.get('done') is not True or v.get('done_reason')!='stop':raise ValueError('incomplete inference')
        native._pin(11434,model,digest,10)
        output=v['message']['content'];results=[evaluate(q,m) for q,m in zip(c_,decode(c_,output))]
        r.update(status='completed',raw=output,response_sha256=hashlib.sha256(raw).hexdigest(),results=results)
    except Exception as e:r.update(status='failed',error_class=type(e).__name__)
    teacher.save(root,'tool-research-v64',r,key);verify(r,key)
    report={'schema':'myriad.tool_research_summary.v64','status':r['status'],'seed':seed,'actual_model_calls':1 if r['status']=='completed' else 0,'tasks':8,'executed':sum(x['executed'] for x in r.get('results',[])),'qualified':sum(x['qualified'] for x in r.get('results',[])),'errors':[r['error_class']] if 'error_class' in r else [],'production_authority':False}
    orch.atomic(root/'aggregate-tool-research-v64.json',report);return report
