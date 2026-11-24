"""Paired prompt experiment. No automatic admission or answer leakage."""
import hashlib,hmac,json,time
import evolution_research_v37 as research
import evolution_fleet_integrity_v55 as integrity
import evolution_teacher_v40 as teacher
import evolution_model_evidence_v24 as ev
import evolution_native_ollama_v33 as native
import evolution_fleet_scale_v36 as scale
import evolution_research_orchestrator_v39 as orch
from evolution_reliability_v43 import PINS
MODEL='qwen3:1.7b'
def cases(seed):
    start=1+(seed%4)*4
    return [research.task(i,seed) for i in range(start,start+4)]
def prompt(cases,protocol):
    if protocol=='compact':
        return 'For each numbered case select the best choice and decisive fact independently. Output exactly one two-character string per case, in order, e.g. A1 means choice A and evidence E1. '+json.dumps([{'n':i+1,'scenario':c['scenario'],'facts':c['evidence'],'choices':c['choices']} for i,c in enumerate(cases)],separators=(',',':'))
    if protocol!='explicit':raise ValueError('unknown protocol')
    lines=['Assess each case separately. First identify the safest scientifically warranted action. Then identify the one fact that makes that action necessary, rather than a fact that is merely true. Return an array of objects containing n, action (A/B/C), fact (E1/E2/E3). Use the printed labels, never the list position.']
    for i,c in enumerate(cases,1):
        lines.extend([f'CASE {i}: '+c['scenario'],'FACTS:']+[k+': '+v for k,v in c['evidence'].items()]+['ACTIONS:']+[k+': '+v for k,v in c['choices'].items()])
    return '\n'.join(lines)
def score(cases,raw,protocol):
    rows=json.loads(raw,object_pairs_hook=research.unique_pairs)
    if not isinstance(rows,list) or len(rows)!=len(cases):raise ValueError('incomplete response')
    if protocol=='compact':
        rows=[{'n':i+1,'action':v['decision'],'fact':v['evidence']} for i,v in enumerate(json.loads(integrity.decode([{'id':i+1} for i in range(len(cases))],raw)))]
    elif protocol!='explicit':raise ValueError('unknown protocol')
    seen=set();result=[]
    for r in rows:
        if not isinstance(r,dict) or set(r)!={'n','action','fact'} or type(r['n']) is not int or not 1<=r['n']<=len(cases) or r['n'] in seen or r['action'] not in ('A','B','C') or r['fact'] not in ('E1','E2','E3'):raise ValueError('invalid answer')
        seen.add(r['n']);c=cases[r['n']-1];a=r['action']==c['expected'];b=r['fact']==c['evidence_id']
        result.append({'n':r['n'],'decision_correct':a,'evidence_correct':b,'joint_correct':a and b})
    return {'total':len(cases),'decision_correct':sum(r['decision_correct'] for r in result),'evidence_correct':sum(r['evidence_correct'] for r in result),'joint_correct':sum(r['joint_correct'] for r in result),'rows':sorted(result,key=lambda r:r['n'])}
def compare(a,b):
    if a['protocol']!='compact' or b['protocol']!='explicit' or a['case_sha256']!=b['case_sha256'] or a['total']!=b['total']:raise ValueError('unpaired comparison')
    return {'total':a['total'],'compact_correct':a['joint_correct'],'explicit_correct':b['joint_correct'],'joint_delta':b['joint_correct']-a['joint_correct'],'compact_seconds':a['seconds'],'explicit_seconds':b['seconds'],'routing_authorized':False}
def infer(c,protocol):
    digest=PINS[MODEL];native._pin(11434,MODEL,digest,10)
    item={'type':'string','enum':[a+b for a in 'ABC' for b in '123']} if protocol=='compact' else {'type':'object','properties':{'n':{'type':'integer','minimum':1,'maximum':len(c)},'action':{'type':'string','enum':list('ABC')},'fact':{'type':'string','enum':['E1','E2','E3']}},'required':['n','action','fact'],'additionalProperties':False}
    fmt={'type':'array','items':item,'minItems':len(c),'maxItems':len(c)}
    start=time.monotonic();v,raw=teacher.request('/api/chat',{'model':MODEL,'messages':[{'role':'user','content':prompt(c,protocol)}],'format':fmt,'think':False,'stream':False,'keep_alive':0,'options':{'num_ctx':3072,'num_predict':192,'num_thread':2,'temperature':0}},65)
    if v.get('model')!=MODEL or v.get('done') is not True or v.get('done_reason')!='stop':raise ValueError('incomplete response')
    native._pin(11434,MODEL,digest,10)
    output=v['message']['content'];return {'protocol':protocol,'case_sha256':hashlib.sha256(ev.canonical(c)).hexdigest(),'raw':output,'response_sha256':hashlib.sha256(raw).hexdigest(),'seconds':round(time.monotonic()-start,3),**score(c,output,protocol)}
def verify(record,key):
    r=dict(record);sig=r.pop('hmac_sha256',None)
    if not isinstance(sig,str) or not hmac.compare_digest(ev.sign(r,key),sig) or r['schema']!='myriad.research_protocol.v67' or r['production_authority'] is not False or r['digest']!=PINS[MODEL]:raise ValueError('receipt authentication')
    c=cases(r['seed'])
    for v in r['results']:
        if v['case_sha256']!=hashlib.sha256(ev.canonical(c)).hexdigest() or any(v[k]!=x for k,x in score(c,v['raw'],v['protocol']).items()):raise ValueError('score replay')
    if r['status']=='completed' and r['comparison']!=compare(*sorted(r['results'],key=lambda v:v['protocol'])):raise ValueError('comparison replay')
    return True
def run(root,virtual):
    if scale.free_mb()<2500 or virtual<6000 or teacher.request('/api/ps')[0].get('models'):return {'status':'deferred_resource_guard','production_authority':False}
    key=ev.secret();seed=int(time.time())//300;c=cases(seed)
    r={'schema':'myriad.research_protocol.v67','seed':seed,'model':MODEL,'digest':PINS[MODEL],'results':[],'production_authority':False,'errors':[]}
    order=('compact','explicit') if seed%2==0 else ('explicit','compact')
    for protocol in order:
        try:r['results'].append(infer(c,protocol))
        except Exception as e:r['errors'].append({'protocol':protocol,'error_class':type(e).__name__})
    r['status']='completed' if len(r['results'])==2 else 'failed'
    if r['status']=='completed':r['comparison']=compare(*sorted(r['results'],key=lambda v:v['protocol']))
    teacher.save(root,'protocol-v67',r,key);verify(r,key)
    out={k:v for k,v in r.items() if k not in ('results','hmac_sha256')}
    orch.atomic(root/'aggregate-protocol-v67.json',out);return out
