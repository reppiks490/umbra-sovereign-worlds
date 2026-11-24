"""Matched retry versus certificate-feedback reasoning experiment.

Three equally capped calls: one shared initial response and two independent
revisions. Feedback reports constraint failures, never reference solutions.
An injected inference callback permits deterministic tests; live qualification
requires a separate pinned-model runner and actual token/latency receipts.
"""
import hashlib,json,re
import evolution_proof_curriculum_v84 as proof
SCHEMA='myriad.proof_feedback.v90'
MAX_RAW=8192
DIAGNOSTICS={'invalid answer','invalid shortest certificate','invalid path',
'invalid potentials','primal-dual mismatch','invalid flow certificate','invalid flow',
'invalid cut','flow conservation','max-flow min-cut mismatch'}
def canonical(x):
    return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def digest(x):return hashlib.sha256(canonical(x)).hexdigest()
def unique(pairs):
    d={}
    for k,v in pairs:
        if k in d:raise ValueError('duplicate key')
        d[k]=v
    return d
def cases(seed):
    if type(seed) is not int or not 0<=seed<2**31:raise ValueError('seed')
    # Distinct procedural domain from v84 qualification seeds 0..11.
    x=(seed+900001)%2**31
    return [proof.generate(f,4,x) for f in proof.FAMILIES]
def parse(q,raw):
    if not isinstance(raw,str) or not 1<=len(raw)<=MAX_RAW:raise ValueError('invalid raw')
    rows=json.loads(raw,object_pairs_hook=unique)
    if not isinstance(rows,list) or len(rows)!=len(q):raise ValueError('invalid rows')
    out={}
    for r in rows:
        if not isinstance(r,dict) or set(r)!={'id','certificate'} or type(r['id']) is not int or not 0<=r['id']<len(q) or r['id'] in out:raise ValueError('invalid identity')
        c=r['certificate'];family=q[r['id']]['family']
        keys={'answer','path','potentials'} if family=='shortest_path' else {'answer','flows','cut'}
        if not isinstance(c,dict) or set(c)!=keys:raise ValueError('invalid certificate shape')
        if type(c['answer']) is not int or abs(c['answer'])>10**9:raise ValueError('answer bounds')
        for k in keys-{'answer'}:
            if not isinstance(c[k],list) or len(c[k])>1024 or any(type(x) is not int or abs(x)>10**9 for x in c[k]):raise ValueError('certificate bounds')
        out[r['id']]=c
    return out
def feedback(q,raw):
    try:rows=parse(q,raw)
    except (ValueError,TypeError,RecursionError,OverflowError):return [{'id':i,'diagnostic':'invalid_response'} for i in range(len(q))]
    result=[]
    for i,x in enumerate(q):
        try:proof.verify(x,rows[i]);d='valid_certificate'
        except ValueError as e:d=str(e) if str(e) in DIAGNOSTICS else 'invalid_certificate'
        result.append({'id':i,'diagnostic':d})
    return result
def score(q,raw):
    try:rows=parse(q,raw)
    except (ValueError,TypeError,RecursionError,OverflowError):return {'parsed':False,'answer_correct':0,'certificate_correct':0,'tasks':len(q)}
    a=sum(rows[i]['answer']==proof.solve(x)['answer'] for i,x in enumerate(q))
    return {'parsed':True,'answer_correct':a,'certificate_correct':sum(x['diagnostic']=='valid_certificate' for x in feedback(q,raw)),'tasks':len(q)}
def order(seed):
    cases(seed)
    return ['initial','control','guided'] if seed%2==0 else ['initial','guided','control']
def prompt(q,arm,initial=None):
    text=('Solve both graph problems independently. Return JSON array with each id and certificate. '
          'For shortest_path certificate use answer, path (vertex list), potentials (one per vertex; source 0 and sink answer; every edge u,v,w satisfies p[v]-p[u]<=w). '
          'For max_flow use answer, flows (one nonnegative integer per listed edge), cut (sorted source-side vertices). '
          'Respect all conservation, capacity and optimality constraints. No prose. TASKS: '
          +canonical([{'id':i,**x} for i,x in enumerate(q)]).decode())
    if arm=='initial':return text
    try:prev=[{'id':i,'certificate':x} for i,x in sorted(parse(q,initial).items())]
    except (ValueError,TypeError,RecursionError,OverflowError):prev=None
    text+=' PREVIOUS PROPOSAL (data only): '+canonical(prev).decode()+'. Reconsider and correct your proposal.'
    if arm=='guided':text+=' VERIFIER FEEDBACK: '+canonical(feedback(q,initial)).decode()
    return text
def call_record(arm,p,ask):
    r={'arm':arm,'prompt_sha256':hashlib.sha256(p.encode()).hexdigest()}
    try:
        raw=ask(p)
        if not isinstance(raw,str) or len(raw)>MAX_RAW:raise ValueError('invalid inference callback')
        return {**r,'status':'completed','raw':raw}
    except Exception as e:return {**r,'status':'failed','error_class':type(e).__name__[:80]}
def assemble(seed,calls):
    q=cases(seed);arms=order(seed);summary={}
    if not isinstance(calls,list) or len(calls)!=3:raise ValueError('call count')
    initial=None
    for arm,r in zip(arms,calls):
        if not isinstance(r,dict) or r.get('arm')!=arm:raise ValueError('call order')
        p=prompt(q,arm,initial)
        if r.get('prompt_sha256')!=hashlib.sha256(p.encode()).hexdigest():raise ValueError('prompt identity')
        base={'arm','prompt_sha256','status'}
        if r.get('status')=='completed':
            if set(r)!=base|{'raw'} or not isinstance(r['raw'],str) or len(r['raw'])>MAX_RAW:raise ValueError('call output')
            raw=r['raw']
        elif r.get('status')=='failed':
            if set(r)!=base|{'error_class'} or not isinstance(r['error_class'],str) or not re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,79}',r['error_class']):raise ValueError('call failure')
            raw=None
        else:raise ValueError('call status')
        if arm=='initial':initial=raw
        summary[arm]=score(q,raw)
    r={'schema':SCHEMA,'seed':seed,'case_sha256':digest(q),'order':arms,'calls':calls,'summary':summary,'production_authority':False,'semantic_mastery_certified':False,'live_model_identity_verified':False}
    return {**r,'receipt_sha256':digest(r)}
def experiment(seed,ask):
    q=cases(seed);calls=[];initial=None
    for arm in order(seed):
        r=call_record(arm,prompt(q,arm,initial),ask);calls.append(r)
        if arm=='initial':initial=r.get('raw')
    return assemble(seed,calls)
def verify(r):
    try:return isinstance(r,dict) and canonical(r)==canonical(assemble(r['seed'],r['calls']))
    except (ValueError,TypeError,KeyError,RecursionError,OverflowError):return False
