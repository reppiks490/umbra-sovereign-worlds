"""Compact teacher labels with independent replay and failure-aware rotation."""
from __future__ import annotations
import argparse,hmac,json,time
from pathlib import Path
import evolution_teacher_v40 as teacher
import evolution_model_evidence_v24 as ev
import evolution_fleet_scale_v36 as scale
import evolution_research_orchestrator_v39 as orch
SMALL=('granite4:350m','deepseek-r1:1.5b','qwen3:1.7b')
def decode(cases,raw):
    values=json.loads(raw)
    if not isinstance(values,list) or len(values)!=len(cases) or any(type(v) is not int or v not in (0,1) for v in values):raise ValueError('invalid compact labels')
    return json.dumps([{'id':c['id'],'label':v} for c,v in zip(cases,values)],separators=(',',':'))
def prompt(cases):
    values=[{'domain':c['domain'],'facts':list(c['facts'].values())} for c in cases]
    return 'Each case has four required facts. Output 1 if all four facts are 1, otherwise 0. Return only the JSON array of integers in input order. '+json.dumps(values,separators=(',',':'))
def choose(models,attempts,slot):
    if not models:return None
    ordered=list(models);n=min(attempts.get(m,0) for m in ordered)
    tied=[m for m in ordered if attempts.get(m,0)==n]
    return tied[slot%len(tied)]
def attempt_counts(private,key):
    counts={}
    folder=private/'teacher-v40'
    for p in list(folder.glob('teacher-*.json'))+list(folder.glob('compact-attempt-*.json')):
        if p.is_symlink() or p.stat().st_size>131072:raise ValueError('invalid attempt receipt')
        r=json.loads(p.read_text());sig=r.pop('hmac_sha256',None)
        if not isinstance(sig,str) or not hmac.compare_digest(ev.sign(r,key),sig):raise ValueError('attempt HMAC')
        if r.get('schema') not in ('myriad.teacher.v40','myriad.compact_attempt.v45'):raise ValueError('attempt scope')
        if r.get('schema')=='myriad.compact_attempt.v45' and r.get('status')!='failed':continue
        m=r.get('model')
        if m in SMALL:counts[m]=counts.get(m,0)+1
    return counts
def teach(private,model,seed,key,virtual):
    digest=teacher.pin(private,model)
    ram=scale.free_mb();busy=bool(teacher.request('/api/ps')[0].get('models'))
    if model==teacher.TEACHER and not teacher.admit_teacher(ram,virtual,busy):
        return {'model':model,'status':'deferred_memory_or_residency','free_ram_mib':ram,'teacher_calls':0}
    if model==teacher.COMPRESSED and (busy or ram<4700 or virtual<7500):
        return {'model':model,'status':'deferred_memory_or_residency','free_ram_mib':ram,'teacher_calls':0}
    if model not in (teacher.TEACHER,teacher.COMPRESSED) and ram<2200:
        return {'model':model,'status':'deferred_memory','teacher_calls':0}
    cases=teacher.cases(seed,0)
    fmt={'type':'array','items':{'type':'integer','enum':[0,1]},'minItems':12,'maxItems':12}
    body={'model':model,'messages':[{'role':'user','content':prompt(cases)}],'format':fmt,'stream':False,'keep_alive':0,'options':{'num_ctx':1024,'num_predict':192,'num_thread':2,'temperature':0}}
    if model!='deepseek-r1:1.5b':body['think']=False
    v,raw=teacher.request('/api/chat',body,150 if model in (teacher.TEACHER,teacher.COMPRESSED) else 75)
    if v.get('model')!=model or v.get('done') is not True or v.get('done_reason')!='stop':raise ValueError('incomplete compact teacher')
    txt=v.get('message',{}).get('content')
    if not isinstance(txt,str) or len(txt)>4096 or teacher.tag(model)!=digest:raise ValueError('invalid teacher response')
    normalized=decode(cases,txt);accepted=teacher.accept(cases,normalized)
    r={'schema':'myriad.teacher.v40','model':model,'model_digest':digest,'seed':seed,'split':0,'response_sha256':teacher.sha(raw),'raw':normalized,'raw_model_output':txt,'encoding':'compact-int-array-v45','cases':len(cases),'accepted':len(accepted),'rejected':len(cases)-len(accepted),'accepted_rows':accepted,'production_authority':False,'model_origin_authenticated':False}
    return teacher.save(private,'teacher',r,key)
def run(private,virtual,mode):
    key=ev.secret();slot=int(time.time())//300
    available={x.get('name') for x in teacher.request('/api/tags')[0]['models']}
    report={'schema':'myriad.compact_supervisor.v45','phase':mode,'epoch':int(time.time()),'errors':[],'production_authority':False}
    model=None
    if mode=='teacher':
        for candidate in (teacher.TEACHER,teacher.COMPRESSED):
            if candidate not in available:continue
            try:
                result=teach(private,candidate,slot,key,virtual)
                report['large_teacher']={k:v for k,v in result.items() if k not in ('raw','raw_model_output','accepted_rows')}
                if result.get('schema')=='myriad.teacher.v40':model=candidate;break
            except Exception as e:
                report['errors'].append(type(e).__name__);teacher.save(private,'compact-attempt',{'schema':'myriad.compact_attempt.v45','model':candidate,'seed':slot,'status':'failed','error_class':type(e).__name__,'production_authority':False},key);model=candidate;break
    if model is None:
        model=choose([m for m in SMALL if m in available],attempt_counts(private,key),slot)
        if model:
            try:
                result=teach(private,model,slot,key,virtual)
                report['small_teacher']={k:v for k,v in result.items() if k not in ('raw','raw_model_output','accepted_rows')}
            except Exception as e:
                report['errors'].append(type(e).__name__)
                teacher.save(private,'compact-attempt',{'schema':'myriad.compact_attempt.v45','model':model,'seed':slot,'status':'failed','error_class':type(e).__name__,'production_authority':False},key)
    try:report['student']={k:v for k,v in teacher.train(private,key).items() if k!='weights'}
    except Exception as e:report['errors'].append(type(e).__name__)
    teacher.save(private,'compact-supervisor',report,key);orch.atomic(private/'aggregate-compact-v45.json',report)
    return report
