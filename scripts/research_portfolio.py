"""Resource-admitted source-only research portfolio with bounded fair scheduling."""
import argparse,hashlib,json,shutil,subprocess,sys,time
from pathlib import Path
LANES={'collective':3000000000,'authentic_retrieval':2800000000,'neural_routing':4000000000,'instruction_following':2800000000,'receipt_replay':1500000000,'grounded_reasoning':2800000000,'generated_challenges':2800000000,'corrective_curriculum':1500000000}
STUDENTS=('qwen3:0.6b','granite4:350m','gemma3:1b')
QUERIES=('ICARUS causal market replay event clock and execution verification','quality diversity optimization archives and behavior descriptors','time series forecasting chronological validation and persistence baseline')

def choose_lane(state,now,ram,free,busy):
    if busy or free<6000000000 or not isinstance(state,dict):
        return None
    eligible=[k for k,minimum in LANES.items() if ram>=minimum and state.get(k,{}).get('next_due',0)<=now]
    return min(eligible,key=lambda k:(state.get(k,{}).get('last_attempt',0),state.get(k,{}).get('attempts',0),k)) if eligible else None

def record_outcome(state,lane,now,status,summary=None):
    if lane not in LANES or type(now) is not int or now<0 or not isinstance(status,str):
        raise ValueError('portfolio outcome identity')
    out={k:dict(v) for k,v in state.items()}
    p=out.get(lane,{})
    completed=status=='completed'
    cooldown=3600 if completed else 600 if status.startswith('deferred') else 1800
    out[lane]={'attempts':p.get('attempts',0)+1,'completed':p.get('completed',0)+int(completed),
               'last_attempt':now,'next_due':now+cooldown,'status':status}
    if summary is not None:
        out[lane]['summary_sha256']=hashlib.sha256(json.dumps(summary,sort_keys=True,allow_nan=False).encode()).hexdigest()
    return out

def command_for(lane,root,python,completed):
    scripts=Path(__file__).resolve().parent
    model=STUDENTS[completed%len(STUDENTS)]
    if lane=='collective':
        return [str(python),str(scripts/'council_qualification.py'),'--root',str(root),'--count','2']
    if lane=='authentic_retrieval':
        # Each model sees the same window once; advance only after a complete attempt.
        offset=62+2*(completed//len(STUDENTS))
        if offset>713:return None
        return [str(python),str(scripts/'lesson_retrieval.py'),'--root',str(root),'--count','2','--offset',str(offset),'--model',model]
    if lane=='neural_routing':
        return [str(python),str(scripts/'neural_routing.py'),'--root',str(root),'--query',QUERIES[completed%len(QUERIES)],'--student',model]
    if lane=='instruction_following':
        offset=2*(completed//len(STUDENTS))
        if offset>=8:return None
        return [str(python),str(scripts/'ifeval_local.py'),'--root',str(root),'--model',model,'--offset',str(offset),'--count','2']
    if lane=='grounded_reasoning':
        offset=100+2*(completed//len(STUDENTS))
        if offset>713:return None
        return [str(python),str(scripts/'grounded_reasoning.py'),'--root',str(root),'--count','2','--offset',str(offset),'--model',model]
    if lane=='corrective_curriculum':
        return [str(python),str(scripts/'corrective_curriculum.py'),'--root',str(root)]
    if lane=='generated_challenges':
        return [str(python),str(scripts/'generated_challenges.py'),'--root',str(root),'--count','2']
    if lane=='receipt_replay':
        return [str(python),str(scripts/'council_receipt_audit.py'),'--root',str(root)]
    raise ValueError('unknown lane')

def normalize(lane,result):
    if result.get('production_authority') is True or result.get('weight_training') is True:
        raise ValueError('research scope violation')
    status=result.get('status','failed')
    if lane=='corrective_curriculum' and status in ('planned','no_verified_failures'):
        return 'completed'
    if lane=='receipt_replay' and status=='replayed' and result.get('replayed_cases',0)>0:
        return 'completed'
    if status=='already_recorded':
        return 'already_recorded'
    if status=='completed':
        if lane in ('collective','authentic_retrieval','instruction_following','grounded_reasoning','generated_challenges'):
            return 'completed' if result.get('model_calls',0)>0 and result.get('completed_calls')==result.get('model_calls') else 'partial'
        if lane=='neural_routing':
            return 'completed' if len(result.get('specialists',[]))==3 and result.get('candidate_answer',{}).get('status') in ('quote_verified','abstained') else 'partial'
    return str(status) if status!='completed' else 'partial'

def run(root,training,only=None):
    from native_lora_train import available_ram,atomic
    from hf_weight_cache import lock
    from source_assist import local_api
    root=root.resolve()
    d=root/'experience'/'research-portfolio';d.mkdir(parents=True,exist_ok=True)
    python=training/'venv'/'Scripts'/'python.exe'
    if not python.is_file():
        return {'status':'deferred_runtime','production_authority':False}
    if only is not None and only not in LANES:raise ValueError('lane')
    try:
        with lock(d/'portfolio.lock'):
            statefile=d/'state.json'
            state=json.loads(statefile.read_text(encoding='utf8')) if statefile.exists() else {}
            now=int(time.time())
            busy=any(p.exists() for p in (root/'experience'/'model-compute.lock',training/'bootstrap.lock',root/'active.lock')) or bool(local_api('ps').get('models'))
            ram,free=available_ram(),shutil.disk_usage(root).free
            view=state if only is None else {**state,**{k:{'next_due':now+1} for k in LANES if k!=only}}
            lane=choose_lane(view,now,ram,free,busy)
            if lane is None:
                return {'status':'deferred_resources_or_cooldown','ram_bytes':ram,'free_bytes':free,'busy':busy,'production_authority':False}
            prior=state.get(lane,{})
            command=command_for(lane,root,python,prior.get('completed',0))
            if command is None:
                final=record_outcome(state,lane,now,'exhausted_reviewed_window')
                final[lane]['next_due']=now+86400
                atomic(statefile,final)
                return {'status':'exhausted_reviewed_window','lane':lane,'production_authority':False}
            # Reserve before execution. Underlying research commands also own shared
            # compute locks. No lock deletion or process termination to force admission.
            reserved=record_outcome(state,lane,now,'attempting')
            atomic(statefile,reserved)
            print(json.dumps({'phase':'portfolio_dispatch','lane':lane}),flush=True)
            try:
                p=subprocess.run(command,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=1500)
                if p.returncode!=0:result={'status':'failed','exit_code':p.returncode,'reason':'research command failed'}
                else:result=json.loads(p.stdout.splitlines()[-1])
                status=normalize(lane,result)
            except subprocess.TimeoutExpired:
                result={'status':'failed_timeout'};status='failed_timeout'
            except (OSError,ValueError,IndexError,TypeError):
                result={'status':'failed_invalid_result'};status='failed_invalid_result'
            end=int(time.time())
            final=record_outcome(state,lane,now,status,result)
            final[lane]['next_due']=max(final[lane]['next_due'],end+60)
            # An already-recorded run may have completed before a prior state write.
            # Do not silently advance or count it again; preserve explicit recovery.
            if status=='already_recorded':final[lane]['next_due']=end+86400
            atomic(statefile,final)
            receipt={'status':status,'lane':lane,'result':result,'timestamp':end,
                     'scope':'research only; no new production or optimizer authority','production_authority':False}
            atomic(d/'latest.json',receipt)
            return receipt
    except FileExistsError:
        return {'status':'deferred_portfolio_busy','production_authority':False}


def service_due(timestamp):
    return int(timestamp)//1800%2==0

def evidence_snapshot(root):
    """Read-only aggregate; invalid receipts fail closed. Never infer competency from enrollment."""
    from council_ledger import summarize
    e=root/'experience'
    errors=[]
    try:
        collective=summarize(e/'council-qualification')
    except (OSError,ValueError,TypeError,KeyError) as exc:
        collective={'cases':0,'trials':0}
        errors.append('collective:'+type(exc).__name__)
    def load_trials(folder,kind):
        seen=set()
        out={'cases':0,'trials':0,'completed_calls':0}
        if kind=='lesson':out.update(fixed_correct=0,retrieved_correct=0)
        else:out.update(passed_cases=0)
        for p in sorted(folder.glob('trial-*.json')):
            try:
                if p.stat().st_size>2_000_000:raise ValueError('receipt size')
                r=json.loads(p.read_text(encoding='utf8'))
                if r.get('status')!='completed':continue
                if r.get('production_authority') is not False or r.get('weight_training') is not False:raise ValueError('scope')
                m=r['manifest']
                h=hashlib.sha256(json.dumps(m,sort_keys=True).encode()).hexdigest()
                if r['manifest_sha256']!=h or p.name!='trial-'+h+'.json':raise ValueError('identity')
                ids=[x['validation'] for x in m['cases']] if kind=='lesson' else m['keys']
                keys={(m['model'],m['digest'],x) for x in ids}
                n=r['cases']
                if type(n) is not int or not 1<=n<=8 or len(keys)!=n or keys&seen:raise ValueError('case coverage')
                expected=n*(2 if kind=='lesson' else 1)
                if r['completed_calls']!=expected or r['model_calls']!=expected:raise ValueError('call coverage')
                if kind=='lesson':
                    rows=r['rows']
                    if len(rows)!=expected or r.get('test_partition_used_for_inference') is not False:raise ValueError('row coverage')
                    pairs={(v['case'],v['arm']) for v in rows}
                    if pairs!={(i,a) for i in ids for a in ('fixed','retrieved')} or any(v['status']!='evaluated' or type(v['correct']) is not bool for v in rows):raise ValueError('paired records')
                    counts={a:sum(v['correct'] for v in rows if v['arm']==a) for a in ('fixed','retrieved')}
                    if any(r[a+'_correct']!=v for a,v in counts.items()):raise ValueError('paired score')
                    for a,v in counts.items():out[a+'_correct']+=v
                else:
                    rows=r['records']
                    if len(rows)!=n or {v['key'] for v in rows}!=set(ids) or any(v['status']!='evaluated' for v in rows):raise ValueError('instruction records')
                    passed=sum(v['score']['passed'] is True for v in rows)
                    if passed!=r['passed_cases']:raise ValueError('instruction score')
                    out['passed_cases']+=passed
                seen.update(keys);out['cases']+=n;out['trials']+=1;out['completed_calls']+=expected
            except (OSError,ValueError,TypeError,KeyError) as exc:
                errors.append(kind+':'+p.name+':'+type(exc).__name__)
        return out
    routing={}
    try:
        p=e/'neural-routing'/'latest.json'
        if p.is_file():
            r=json.loads(p.read_text(encoding='utf8'))
            if r.get('status')=='completed' and r.get('production_authority') is False:
                routing={'specialists':len({v['weight_sha256'] for v in r['specialists']}),
                         'quote_verified':r.get('candidate_answer',{}).get('status')=='quote_verified',
                         'scope':'latest recorded trial; relevance not established'}
    except (OSError,ValueError,TypeError,KeyError) as exc:errors.append('routing:'+type(exc).__name__)
    from grounded_reasoning import audit as audit_grounded
    try:grounded=audit_grounded(root)
    except (OSError,ValueError,TypeError,KeyError) as exc:
        grounded={'cases':0,'trials':0,'production_authority':False}
        errors.append('grounded:'+type(exc).__name__)
    from generated_challenges import audit as audit_generated
    try:generated=audit_generated(root)
    except (OSError,ValueError,TypeError,KeyError) as exc:
        generated={'completed_calls':0,'production_authority':False}
        errors.append('generated:'+type(exc).__name__)
    return {'generated_challenges':generated,'grounded_reasoning':grounded,'collective':collective,'lesson_retrieval':load_trials(e/'lesson-retrieval','lesson'),
            'instruction_following':load_trials(e/'ifeval-local','instruction'),
            'neural_routing':routing,'errors':errors,
            'scope':'recorded development evidence, not independent general intelligence qualification',
            'production_authority':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--training',required=True,type=Path);p.add_argument('--lane',choices=tuple(LANES));a=p.parse_args();print(json.dumps(run(a.root,a.training,a.lane),ensure_ascii=True))
