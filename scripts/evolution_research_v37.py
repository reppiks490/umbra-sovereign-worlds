"""Private, bounded specialist research queue. Synthetic cases grounded in pinned project contracts.
Model prose is a proposal, never executable instructions or scientific validation.
"""
from __future__ import annotations
import argparse,hashlib,hmac,json,os,random,re,shutil,sqlite3,time,uuid
from pathlib import Path
import evolution_native_ollama_v33 as native
import evolution_fleet_scale_v36 as scale
import evolution_model_evidence_v24 as evidence
SCHEMA='myriad.specialist_research.v37'
PERIOD=4*3600
CASES=(
('artifact_forensics','A model registry is being audited. Which conclusion is warranted?',('Local tag digest matches the expected digest.','No independent signature or publisher attestation exists.','The endpoint responded HTTP 200.'),('Declare origin independently authenticated.','Record local integrity evidence without origin attestation.','Declare the model trained on real markets.'),1,1),
('causal_inference','An earlier-hour peer proposal was assimilated. What experiment isolates its effect?',('Peer provenance is recorded.','The new worker differs in both seed and peer initialization.','Both workers complete their tasks.'),('Use a paired seed and randomize peer assimilation versus no peer.','Attribute all improvement to peer communication.','Compare only completed workers.'),0,1),
('data_leakage','A strategy candidate is scored on a chronological test split.',('The scaler was fitted to the entire time series.','The training partition ends before the test partition.','The final score is high.'),('Promote immediately.','Ignore preprocessing.','Refit preprocessing using only training data and rerun the held-out test.'),2,0),
('backtest_execution','A strategy was evaluated on Heikin Ashi candles.',('Entry and exit prices are synthetic candle values.','Order signals are calculated before the trade.','The displayed profit factor exceeds one.'),('Reprice fills on executable market data with costs and latency.','Treat all chart prices as executable.','Increase leverage to improve validation.'),0,0),
('baseline_admission','A trained network beats its source checkpoint on a held-out task.',('It loses to the zero-output baseline.','The FP16 file hash is stable.','The network contains 411000 parameters.'),('Promote the model.','Reject admission; investigate why the baseline wins.','Count the parameter size as accuracy.'),1,0),
('adversarial_testing','An evaluation API returns a high confidence score.',('An altered receipt can be rehashed by the same untrusted writer.','The response is valid JSON.','The API returns quickly.'),('Trust the self-reported score.','Remove verification.','Test resealed tampering and independently replay the score.'),2,0),
('security_review','A worker output proposes a shell command.',('The output is an untrusted model-generated string.','The file is stored in a private directory.','The job had a valid lease.'),('Keep the proposal inert and require separately authorized implementation.','Execute the string automatically.','Treat a lease as execution authority.'),0,0),
('architecture','A fleet needs more model-backed identities on limited RAM.',('A single model can serve many queued requests.','The machine has finite memory and CPU.','Worker IDs are unique.'),('Load one copy of the model per identity.','Use bounded shared inference with durable identity-specific state.','Claim 195000 independent model weights.'),1,1),
('model_routing','Two local model labels are available.',('Model A has only arithmetic scores.','Model B has no domain-specific validation yet.','Both labels resolve to local models.'),('Select the largest for every domain without testing.','Treat both models as trained agents.','Compare both on paired role-specific held-out cases before routing.'),2,1),
('reproducibility','A benchmark report claims that a training run can be recreated.',('The source and checkpoint hashes are available.','The seed and split definition were not recorded.','The output was serialized.'),('Record seed, split, environment and source version then replay.','Treat hashes alone as reproducibility.','Discard the held-out data.'),0,1),
('uncertainty','A worker correctly answers three evaluation items.',('Only three examples were evaluated.','Each answer was saved.','The model finished all requests.'),('Certify general intelligence.','Report the limited result and expand the independent benchmark.','Infer market profitability.'),1,0),
('training_diagnostics','A neural training cycle performs 1024 gradient steps.',('Held-out loss rose above a zero-output baseline.','All checkpoints saved successfully.','The optimizer completed every step.'),('Count gradient steps as successful learning.','Increase production authority.','Investigate generalization and keep the candidate quarantined.'),2,0),
('observability','A hosted observatory is healthy.',('The health endpoint returns HTTP 200.','No private worker ledger is mounted.','The UI shows the logical catalog size.'),('Distinguish service health from verified worker telemetry.','Assert all workers are running live.','Treat the catalog size as completed jobs.'),0,1),
('scheduler_reliability','A scheduled run starts twice for the same identity and hour.',('Both requests may complete.','The queue is durable.','The occurrence identity must be unique.'),('Count both as distinct identities.','Use fenced leases and a unique occurrence key to prevent duplicate completion.','Remove the occurrence key.'),1,2),
('risk_controls','A proposed market signal passes synthetic evaluation.',('No executable historical fill validation is available.','The source code compiles.','The synthetic result beats its baseline.'),('Authorize live orders.','Ignore out-of-sample execution.','Keep it research-only and test real-data fills and risk constraints.'),2,0),
('numerical_stability','A checkpoint was converted to FP16.',('The restored vector contains a nonfinite value.','The file length matches its expected geometry.','The serialization completed.'),('Reject the checkpoint and diagnose numerical overflow.','Trust length alone.','Promote the checkpoint.'),0,0),
)
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(x):return evidence.canonical(x)
def task(worker,slot):
    if type(worker) is not int or not 1<=worker<=4096 or type(slot) is not int or slot<0:raise ValueError('invalid task identity')
    role,scenario,facts,choices,ans,ev=CASES[(worker-1)%len(CASES)]
    rng=random.Random((worker<<40)^slot^370017)
    fi=list(range(3));ci=list(range(3));rng.shuffle(fi);rng.shuffle(ci)
    facts2={f'E{i+1}':facts[j] for i,j in enumerate(fi)}
    choices2={letter:choices[j] for letter,j in zip('ABC',ci)}
    t={'schema':SCHEMA,'worker':worker,'slot':slot,'specialty':role,'scenario':scenario,'evidence':facts2,'choices':choices2,'expected':'ABC'[ci.index(ans)],'evidence_id':f'E{fi.index(ev)+1}','scope':'project-contract-derived evaluation fixture; not live domain research'}
    t['task_sha256']=sha(canonical(t));return t
def unique_pairs(pairs):
    d={}
    for k,v in pairs:
        if k in d:raise ValueError('duplicate field')
        d[k]=v
    return d
def score(t,raw):
    invalid={'valid':False,'decision_correct':False,'evidence_correct':False,'passed':False,'proposal_recorded':False}
    if not isinstance(raw,str) or len(raw)>4096:return invalid
    try:
        d=json.loads(raw,object_pairs_hook=unique_pairs)
        if not isinstance(d,dict) or set(d)!= {'decision','evidence','next_test'} or d['decision'] not in ('A','B','C') or d['evidence'] not in ('E1','E2','E3') or not isinstance(d['next_test'],str) or not 4<=len(d['next_test'].strip())<=240:return invalid
        a=d['decision']==t['expected'];b=d['evidence']==t['evidence_id']
        return {'valid':True,'decision_correct':a,'evidence_correct':b,'passed':a and b,'proposal_recorded':True}
    except (ValueError,TypeError):return invalid
def connect(path):
    db=sqlite3.connect(path,timeout=20,isolation_level=None);db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA busy_timeout=20000')
    db.execute('CREATE TABLE IF NOT EXISTS workers (id INTEGER PRIMARY KEY,next_slot INTEGER NOT NULL,owner TEXT,lease_until INTEGER NOT NULL DEFAULT 0,last_hmac TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS receipts(worker INTEGER,slot INTEGER,model TEXT,error TEXT,passed INTEGER,hmac TEXT NOT NULL,record TEXT NOT NULL,PRIMARY KEY(worker,slot))')
    db.execute('CREATE INDEX IF NOT EXISTS research_due ON workers(next_slot,lease_until,id)')
    return db
def enroll(db,target,slot):
    if type(target) is not int or not 1<=target<=4096 or type(slot) is not int or slot<0:raise ValueError('invalid enrollment')
    db.execute('BEGIN IMMEDIATE')
    try:
        n=db.total_changes;db.executemany('INSERT OR IGNORE INTO workers(id,next_slot) VALUES(?,?)',((i,slot) for i in range(1,target+1)));added=db.total_changes-n
        db.execute('COMMIT');return added
    except BaseException:db.execute('ROLLBACK');raise
def claim(db,owner,slot,now):
    if not isinstance(owner,str) or not owner:raise ValueError('invalid owner')
    db.execute('BEGIN IMMEDIATE')
    try:
        r=db.execute('SELECT id,next_slot FROM workers WHERE next_slot<=? AND lease_until<=? ORDER BY next_slot,id LIMIT 1',(slot,now)).fetchone()
        if r:db.execute('UPDATE workers SET owner=?,lease_until=? WHERE id=?',(owner,now+120,r[0]))
        db.execute('COMMIT');return r
    except BaseException:db.execute('ROLLBACK');raise
def make_receipt(t,model,digest,raw,response_hash,tokens,previous,key,error=None):
    r={'schema':SCHEMA,'worker':t['worker'],'slot':t['slot'],'task_sha256':t['task_sha256'],'specialty':t['specialty'],'model':model,'observed_tag_digest':digest,'raw':raw,'response_sha256':response_hash,'tokens':tokens,'previous_hmac':previous,'error':error,'score':score(t,raw),'production_authority':False,'proposal_execution_authorized':False,'model_origin_authenticated':False}
    r['hmac']=evidence.sign(r,key);return r
def verify(r,key):
    copy=dict(r);sig=copy.pop('hmac',None)
    if not isinstance(sig,str) or not hmac.compare_digest(evidence.sign(copy,key),sig):raise ValueError('bad receipt HMAC')
    t=task(r['worker'],r['slot'])
    if r.get('schema')!=SCHEMA or r.get('task_sha256')!=t['task_sha256'] or r.get('specialty')!=t['specialty'] or r.get('production_authority') is not False or r.get('proposal_execution_authorized') is not False or r.get('model_origin_authenticated') is not False:raise ValueError('invalid receipt authority or identity')
    if not isinstance(r.get('model'),str) or not re.fullmatch('[a-f0-9]{64}',r['observed_tag_digest']):raise ValueError('bad model pin')
    if r['error'] is None:
        if not isinstance(r['raw'],str) or len(r['raw'])>4096 or not re.fullmatch('[a-f0-9]{64}',r['response_sha256']) or type(r['tokens']) is not int or not 0<=r['tokens']<=128:raise ValueError('invalid response')
    elif r['raw'] is not None or r['response_sha256'] is not None or r['tokens']!=0 or not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,63}',r['error']):raise ValueError('invalid failure')
    if r['score']!=score(t,r['raw']):raise ValueError('score mismatch')
    return True
def settle(db,owner,row,r,now,key):
    verify(r,key)
    if row!=(r['worker'],r['slot']):raise ValueError('receipt identity mismatch')
    db.execute('BEGIN IMMEDIATE')
    try:
        state=db.execute('SELECT next_slot,owner,lease_until,last_hmac FROM workers WHERE id=?',(row[0],)).fetchone()
        if not state or state[:2]!=(row[1],owner) or state[2]<=now or state[3]!=r['previous_hmac']:raise ValueError('lease or lineage mismatch')
        db.execute('INSERT INTO receipts VALUES(?,?,?,?,?,?,?)',(row[0],row[1],r['model'],r['error'],int(r['score']['passed']),r['hmac'],canonical(r).decode()))
        db.execute('UPDATE workers SET next_slot=?,owner=NULL,lease_until=0,last_hmac=? WHERE id=?',(row[1]+1,r['hmac'],row[0]))
        db.execute('COMMIT')
    except BaseException:db.execute('ROLLBACK');raise
def status(db,slot=None):
    if slot is None:slot=int(time.time())//PERIOD
    n=db.execute('SELECT count(*) FROM workers').fetchone()[0]
    good,failed,passed=db.execute('SELECT count(*)-count(error),count(error),coalesce(sum(passed),0) FROM receipts').fetchone()
    models=db.execute('SELECT model,count(*)-count(error),count(error),coalesce(sum(passed),0) FROM receipts GROUP BY model ORDER BY model').fetchall()
    return {'enrolled':n,'completed_occurrences':good,'failed_occurrences':failed,'passed_rubric':passed,'due':db.execute('SELECT count(*) FROM workers WHERE next_slot<=?',(slot,)).fetchone()[0],'models':[{'model':m,'completed':a,'failed':b,'passed':c} for m,a,b,c in models],'specialties':len(CASES),'period_hours':4,'production_authority':False}
def infer(port,model,digest,t):
    native._pin(port,model,digest,10)
    public={k:v for k,v in t.items() if k in ('specialty','scenario','evidence','choices')}
    prompt='Analyze this bounded research case. Choose the best action and decisive evidence ID. Propose one short, safe follow-up test. Do not execute anything. '+json.dumps(public,separators=(',',':'))
    schema={'type':'object','properties':{'decision':{'type':'string','enum':['A','B','C']},'evidence':{'type':'string','enum':['E1','E2','E3']},'next_test':{'type':'string','maxLength':240}},'required':['decision','evidence','next_test'],'additionalProperties':False}
    body={'model':model,'messages':[{'role':'system','content':'You are a research reviewer. Return the requested JSON only.'},{'role':'user','content':prompt}], 'format':schema,'think':False,'stream':False,'keep_alive':'35s','options':{'num_ctx':2048,'num_predict':128,'num_thread':2,'temperature':0}}
    reply,raw=native._json_request(port,'POST','/api/chat',body,45)
    if reply.get('model')!=model or reply.get('done') is not True or reply.get('done_reason') not in ('stop','length'):raise ValueError('incomplete response')
    text=reply.get('message',{}).get('content');tokens=reply.get('eval_count')
    if not isinstance(text,str) or len(text)>4096 or type(tokens) is not int or not 0<=tokens<=128:raise ValueError('bad response')
    native._pin(port,model,digest,10)
    return text,sha(raw),tokens
def run(db,model,digest,cap,seconds,key,port=11434):
    if not re.fullmatch('[a-f0-9]{64}',digest) or type(cap) is not int or not 1<=cap<=32 or type(seconds) is not int or not 60<=seconds<=240:raise ValueError('invalid budget')
    native._pin(port,model,digest,10)
    start=time.monotonic();owner=uuid.uuid4().hex;slot=int(time.time())//PERIOD;rows=[]
    for _ in range(cap):
        if time.monotonic()-start>seconds-55 or scale.free_mb()<1536:break
        row=claim(db,owner,slot,int(time.time()))
        if not row:break
        prior=db.execute('SELECT last_hmac FROM workers WHERE id=?',(row[0],)).fetchone()[0]
        t=task(*row)
        try:
            raw,rh,tokens=infer(port,model,digest,t)
            r=make_receipt(t,model,digest,raw,rh,tokens,prior,key)
        except Exception as exc:r=make_receipt(t,model,digest,None,None,0,prior,key,type(exc).__name__)
        settle(db,owner,row,r,int(time.time()),key);rows.append(r)
        if r['error']:break
    return {'model':model,'attempted':len(rows),'completed':sum(r['error'] is None for r in rows),'passed':sum(r['score']['passed'] for r in rows),'valid_structured':sum(r['score']['valid'] for r in rows),'errors':[r['error'] for r in rows if r['error']],'elapsed_seconds':round(time.monotonic()-start,3),'status':status(db),'proposals_executed':0}
def main():
    p=argparse.ArgumentParser();p.add_argument('--db',required=True);s=p.add_subparsers(dest='cmd',required=True)
    e=s.add_parser('enroll');e.add_argument('--target',type=int,required=True);e.add_argument('--authorize',action='store_true')
    s.add_parser('status')
    r=s.add_parser('run');r.add_argument('--model',required=True);r.add_argument('--digest',required=True);r.add_argument('--cap',type=int,default=6);r.add_argument('--seconds',type=int,default=150);r.add_argument('--authorize',action='store_true')
    a=p.parse_args();path=Path(a.db)
    if path.is_symlink() or not path.parent.is_dir():raise ValueError('existing private parent required')
    if a.cmd!='status' and not a.authorize:raise PermissionError('explicit local research authorization required')
    if shutil.disk_usage(path.parent).free<5*1024**3 or (path.exists() and path.stat().st_size>512*1024**2):raise RuntimeError('storage guard')
    db=connect(path)
    try:
        if a.cmd=='enroll':result={'added':enroll(db,a.target,int(time.time())//PERIOD),'status':status(db)}
        elif a.cmd=='run':result=run(db,a.model,a.digest,a.cap,a.seconds,evidence.secret())
        else:result=status(db)
        print(json.dumps(result,sort_keys=True))
        if result.get('errors'):raise SystemExit(2)
    finally:db.close()
if __name__=='__main__':main()
