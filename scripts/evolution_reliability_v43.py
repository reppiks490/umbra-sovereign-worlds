"""Evidence-gated transient recovery and paired model qualification."""
from __future__ import annotations
import argparse,datetime,hashlib,hmac,json,math,os,re,sqlite3,time
from pathlib import Path
import evolution_model_queue_v26 as queue
import evolution_model_evidence_v24 as ev
import evolution_research_v37 as research
import evolution_teacher_v40 as teacher
import evolution_fleet_scale_v36 as scale
import evolution_native_ollama_v33 as native
PINS={'qwen3:1.7b':'8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7','gemma3:1b':'97558784bdc9175075a72655bf360b15da17df6b3b9e5182af9f8c0c8e58ba7c','qwen2.5-coder:1.5b':'d7372fd828518a4d38b1eb196c673c31a85f2ed302b3d1e406c4c2d1b64a0668','granite4:350m':'5eee845b49c4b72ef9e385463a1e2ea9f6f937e08b019f3bbecec12bc1927221'}
def next_hour(due,now):
    if type(due) is not int or type(now) is not int or due%3600:raise ValueError('invalid recovery clock')
    return max(due+3600,now//3600*3600)
def recover(path,now,verify_failed,key):
    db=queue.open_db(path);out=[]
    try:
        db.execute('''CREATE TABLE IF NOT EXISTS recovery_v43(worker INTEGER,failed_due INTEGER,retry_due INTEGER,receipt_hmac TEXT,record TEXT,PRIMARY KEY(worker,failed_due))''')
        db.execute('BEGIN IMMEDIATE')
        try:
            rows=db.execute("SELECT worker_id,next_due,failures,last_receipt FROM model_jobs WHERE state='quarantined' AND failure_class='TimeoutError' AND failures BETWEEN 1 AND 2 AND repeating=1").fetchall()
            for worker,due,failures,last in rows:
                sig=verify_failed(worker,due)
                if not isinstance(sig,str) or not re.fullmatch('[a-f0-9]{64}',sig):continue
                new=next_hour(due,now)
                report={'schema':'myriad.quarantine_recovery.v43','worker':worker,'failed_due':due,'retry_due':new,'failed_receipt_hmac':sig,'last_success_hmac':last,'lifetime_failures':failures,'failure_class':'TimeoutError','old_occurrence_recovered':False,'production_authority':False}
                report['hmac_sha256']=ev.sign(report,key)
                db.execute('INSERT INTO recovery_v43 VALUES(?,?,?,?,?)',(worker,due,new,sig,ev.canonical(report).decode()))
                db.execute("UPDATE model_jobs SET state='ready',next_due=?,lease_owner=NULL,lease_until=0,failure_class=NULL WHERE worker_id=? AND state='quarantined'",(new,worker))
                out.append(report)
            db.execute('COMMIT')
        except BaseException:db.execute('ROLLBACK');raise
    finally:db.close()
    return out
def verify_failure(folder,worker,due):
    hour=datetime.datetime.fromtimestamp(due,datetime.timezone.utc).strftime('%Y%m%dT%H')
    p=folder/f'E{worker:06d}_{hour}.private.json'
    if p.is_symlink() or not p.is_file() or p.stat().st_size>131072:return None
    v=json.loads(p.read_text())
    try:r=ev.verify(v)
    except (ValueError,KeyError,TypeError):return None
    if r['completed'] or v['error_class']!='TimeoutError' or v['seed']!=(worker*65537+due//3600)%(2**32):return None
    return v['hmac_sha256']
def benchmark_cases(seed):
    if type(seed) is not int or not 0<=seed<2**32:raise ValueError('invalid seed')
    # Rotated specialties and deterministic evidence permutations, same tasks for all models.
    roles=(0,2,5,9)
    rows=[]
    for j,role in enumerate(roles):
        t=research.task(role+1+(seed%8)*16,seed)
        rows.append({'id':j+1,'specialty':t['specialty'],'scenario':t['scenario'],'facts':t['evidence'],'actions':t['choices'],'decision':t['expected'],'evidence':t['evidence_id']})
    return rows
def grade(cases,raw):
    rows=json.loads(raw,object_pairs_hook=research.unique_pairs)
    if not isinstance(rows,list) or len(rows)!=len(cases):raise ValueError('incomplete paired benchmark')
    keyed={c['id']:c for c in cases};seen=set();results=[]
    for r in rows:
        if not isinstance(r,dict) or set(r)!={'id','decision','evidence'} or type(r['id']) is not int or r['id'] not in keyed or r['id'] in seen or r['decision'] not in ('A','B','C') or r['evidence'] not in ('E1','E2','E3'):raise ValueError('invalid benchmark row')
        seen.add(r['id']);c=keyed[r['id']]
        a=r['decision']==c['decision'];b=r['evidence']==c['evidence']
        results.append({'id':r['id'],'specialty':c['specialty'],'decision_correct':a,'evidence_correct':b,'correct':a and b})
    return {'correct':sum(r['correct'] for r in results),'total':len(cases),'decision_correct':sum(r['decision_correct'] for r in results),'evidence_correct':sum(r['evidence_correct'] for r in results),'rows':results}
def compare(rows):
    if not rows or len({r['case_hash'] for r in rows})!=1 or len({r['total'] for r in rows})!=1 or len({r['model'] for r in rows})!=len(rows):raise ValueError('not paired')
    ranked=sorted(rows,key=lambda r:(-r['correct'],r['model']))
    tied=[r['model'] for r in ranked if r['correct']==ranked[0]['correct']]
    return {'leader':tied[0] if len(tied)==1 else None,'tied_leaders':tied,'models':ranked,'production_authority':False,'automatic_routing_admission':False}
def benchmark(private,model,seed,key):
    if model in PINS:
        digest=PINS[model];native._pin(11434,model,digest,10)
    elif model=='deepseek-r1:1.5b':
        digest=teacher.pin(private,model)
    else:raise ValueError('model not qualified for benchmark')
    if scale.free_mb()<2200:return {'model':model,'status':'deferred_memory'}
    cases=benchmark_cases(seed)
    public=[{k:v for k,v in c.items() if k not in ('decision','evidence')} for c in cases]
    fmt={'type':'array','minItems':len(cases),'maxItems':len(cases),'items':{'type':'object','properties':{'id':{'type':'integer'},'decision':{'type':'string','enum':['A','B','C']},'evidence':{'type':'string','enum':['E1','E2','E3']}},'required':['id','decision','evidence'],'additionalProperties':False}}
    prompt='For each case, select best action and decisive fact. Return JSON array with id, decision and evidence. '+json.dumps(public,separators=(',',':'))
    body={'model':model,'messages':[{'role':'user','content':prompt}],'format':fmt,'think':False,'stream':False,'keep_alive':0,'options':{'num_ctx':2048,'num_predict':256,'num_thread':2,'temperature':0}}
    v,raw=teacher.request('/api/chat',body,100)
    if v.get('model')!=model or v.get('done') is not True:raise ValueError('incomplete benchmark')
    txt=v.get('message',{}).get('content')
    if not isinstance(txt,str) or len(txt)>8192:raise ValueError('invalid output')
    native._pin(11434,model,digest,10)
    result=grade(cases,txt)
    record={'schema':'myriad.paired_benchmark.v43','model':model,'digest':digest,'seed':seed,'case_hash':hashlib.sha256(ev.canonical(cases)).hexdigest(),'raw':txt,'response_sha256':hashlib.sha256(raw).hexdigest(),'production_authority':False,**result}
    teacher.save(private,'paired',record,key)
    return {k:v for k,v in record.items() if k not in ('raw','rows')}
def main():
    p=argparse.ArgumentParser();p.add_argument('--private',required=True);p.add_argument('--authorize',action='store_true');s=p.add_subparsers(dest='cmd',required=True)
    s.add_parser('recover')
    b=s.add_parser('benchmark');b.add_argument('--model',required=True);b.add_argument('--seed',type=int,required=True)
    a=p.parse_args();root=Path(a.private)
    if not a.authorize or root.is_symlink() or not root.is_dir():raise PermissionError('explicit private research authorization required')
    key=ev.secret()
    if a.cmd=='recover':
        rows=recover(root/'local-pilot.sqlite3',int(time.time()),lambda i,d:verify_failure(root/'receipts',i,d),key);result={'recovered':len(rows),'workers':[r['worker'] for r in rows],'historical_missed_occurrences_preserved':True}
    else:result=benchmark(root,a.model,a.seed,key)
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
