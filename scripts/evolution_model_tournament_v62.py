"""Paired, independently scored model tournament across all sixteen specialist families."""
import argparse,hashlib,hmac,json,re,time
from pathlib import Path
import evolution_research_v37 as research
import evolution_model_evidence_v24 as ev
import evolution_teacher_v40 as teacher
import evolution_fleet_scale_v36 as scale
import evolution_native_ollama_v33 as native
import evolution_reliability_v43 as reliability
import evolution_fleet_integrity_v55 as integrity
import evolution_research_orchestrator_v39 as orch
MODELS=('qwen3:1.7b','gemma3:1b','granite4:350m','qwen2.5-coder:1.5b','deepseek-r1:1.5b',teacher.COMPRESSED,teacher.TEACHER)
def cases(cohort,partition):
    if type(cohort) is not int or cohort<0 or partition not in (0,1):raise ValueError('invalid cohort')
    return [{'id':i,**research.task(i,cohort)} for i in range(1+8*partition,9+8*partition)]
def grade(c,raw):
    rows=json.loads(integrity.decode(c,raw));result=[]
    for t,r in zip(c,rows):
        a=r['decision']==t['expected'];b=r['evidence']==t['evidence_id']
        result.append({'id':t['id'],'decision_correct':a,'evidence_correct':b,'joint_correct':a and b})
    return {'total':len(c),'decision_correct':sum(r['decision_correct'] for r in result),'evidence_correct':sum(r['evidence_correct'] for r in result),'joint_correct':sum(r['joint_correct'] for r in result),'rows':result}
def compare(rows):
    if len({r['cohort'] for r in rows})>1:raise ValueError('mixed cohorts')
    groups=[]
    for p in (0,1):
        a=[r for r in rows if r['partition']==p]
        if not a:continue
        if len({r['case_sha256'] for r in a})!=1 or len({r['total'] for r in a})!=1 or len({r['model'] for r in a})!=len(a):raise ValueError('unpaired comparison')
        a.sort(key=lambda r:(-r['joint_correct'],r['seconds'],r['model']))
        ties=[r['model'] for r in a if r['joint_correct']==a[0]['joint_correct']]
        groups.append({'partition':p,'leader':ties[0] if len(ties)==1 else None,'ties':ties,'models':a})
    return {'partitions':groups,'routing_authorized':False,'production_authority':False}
def choose(models,completed,attempts):
    candidates=[(m,p) for m in models for p in (0,1) if (m,p) not in completed]
    return min(candidates,key=lambda x:attempts.get(x,0)) if candidates else None
def read_prior(root,key,cohort):
    rows=[];attempts={}
    for f in sorted((root/'teacher-v40').glob('tournament-v62-*.json')):
        r=json.loads(f.read_text());sig=r.pop('hmac_sha256',None)
        if not isinstance(sig,str) or not hmac.compare_digest(ev.sign(r,key),sig) or r.get('schema')!='myriad.tournament.v62' or r.get('production_authority') is not False:raise ValueError('invalid tournament receipt')
        if r['cohort']!=cohort:continue
        pair=(r['model'],r['partition']);attempts[pair]=attempts.get(pair,0)+1
        if r['status']!='completed':continue
        c=cases(cohort,r['partition']);g=grade(c,r['raw'])
        if r['case_sha256']!=hashlib.sha256(ev.canonical(c)).hexdigest() or any(r[k]!=v for k,v in g.items()):raise ValueError('tournament replay')
        rows.append({k:r[k] for k in ('model','cohort','partition','case_sha256','joint_correct','decision_correct','evidence_correct','total','seconds')})
    return rows,attempts
def run(root,virtual):
    key=ev.secret();cohort=int(time.time())//604800;rows,attempts=read_prior(root,key,cohort)
    tags,_=teacher.request('/api/tags');available={x.get('name') for x in tags['models']}
    ram=scale.free_mb();busy=bool(teacher.request('/api/ps')[0].get('models'))
    eligible=[m for m in MODELS if m in available and (teacher.admit_teacher(ram,virtual,busy) if m==teacher.TEACHER else (ram>=5000 and virtual>=7500 and not busy) if m==teacher.COMPRESSED else ram>=2500)]
    choice=choose(eligible,{(r['model'],r['partition']) for r in rows},attempts)
    report={'schema':'myriad.tournament_summary.v62','cohort':cohort,'production_authority':False,'errors':[]}
    if not choice:
        report['status']='no_eligible_pending_model';report['comparison']=compare(rows);return report
    model,p=choice;c=cases(cohort,p)
    rec={'schema':'myriad.tournament.v62','cohort':cohort,'partition':p,'model':model,'case_sha256':hashlib.sha256(ev.canonical(c)).hexdigest(),'production_authority':False}
    start=time.monotonic()
    try:
        digest=reliability.PINS.get(model) or teacher.pin(root,model)
        native._pin(11434,model,digest,10)
        public=[{'n':i+1,'question':t['scenario'],'facts':t['evidence'],'choices':t['choices']} for i,t in enumerate(c)]
        fmt={'type':'array','minItems':8,'maxItems':8,'items':{'type':'string','enum':[a+b for a in 'ABC' for b in '123']}}
        prompt='For each numbered question choose the best action AND the single most decisive fact. Return exactly eight strings in order. A1 means action A, fact E1. '+json.dumps(public,separators=(',',':'))
        body={'model':model,'messages':[{'role':'user','content':prompt}],'format':fmt,'stream':False,'keep_alive':0,'options':{'num_ctx':3072,'num_predict':192,'num_thread':2,'temperature':0}}
        if model!='deepseek-r1:1.5b':body['think']=False
        v,raw=teacher.request('/api/chat',body,140 if model in (teacher.TEACHER,teacher.COMPRESSED) else 90)
        if v.get('model')!=model or v.get('done') is not True or v.get('done_reason')!='stop':raise ValueError('incomplete result')
        native._pin(11434,model,digest,10)
        output=v['message']['content'];rec.update(status='completed',digest=digest,raw=output,response_sha256=hashlib.sha256(raw).hexdigest(),**grade(c,output))
    except Exception as e:rec.update(status='failed',error_class=type(e).__name__);report['errors'].append(type(e).__name__)
    rec['seconds']=round(time.monotonic()-start,3)
    teacher.save(root,'tournament-v62',rec,key)
    rows,_=read_prior(root,key,cohort);report.update(status=rec['status'],batch={k:v for k,v in rec.items() if k not in ('raw','rows')},comparison=compare(rows));orch.atomic(root/'aggregate-tournament-v62.json',report);return report
