"""All 195000 addressable workers, bounded local multi-item inference and evidence-linked memory.
One model call may answer several independent task records; never counts as several LLM calls.
"""
import argparse,hashlib,hmac,json,math,os,re,sqlite3,time,uuid,shutil
from pathlib import Path
import evolution_research_v37 as research
import evolution_model_evidence_v24 as ev
import evolution_teacher_v40 as teacher
import evolution_fleet_scale_v36 as scale
import evolution_collective_v54 as collective
TOTAL=195000;PERIOD=3600
MODEL='qwen3:1.7b';DIGEST='8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7'
def connect(path):
    db=sqlite3.connect(path,timeout=15,isolation_level=None);db.execute('PRAGMA journal_mode=WAL')
    db.execute('CREATE TABLE IF NOT EXISTS workers(id INTEGER PRIMARY KEY, next_slot INTEGER NOT NULL DEFAULT 0, owner TEXT, lease INTEGER NOT NULL DEFAULT 0, last_hmac TEXT, wins INTEGER NOT NULL DEFAULT 0, attempts INTEGER NOT NULL DEFAULT 0)')
    db.execute('CREATE INDEX IF NOT EXISTS fleet_due ON workers(next_slot,id)')
    db.execute('CREATE TABLE IF NOT EXISTS receipts(worker INTEGER,slot INTEGER,correct INTEGER NOT NULL,peer_worker INTEGER,peer_slot INTEGER,record TEXT NOT NULL,hmac TEXT NOT NULL,PRIMARY KEY(worker,slot))')
    db.execute('CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY,slot INTEGER,model TEXT,n INTEGER,correct INTEGER,response_sha TEXT,record TEXT)')
    return db
def enroll(db,n):
    if type(n) is not int or not 1<=n<=TOTAL:raise ValueError('invalid fleet size')
    db.execute('BEGIN IMMEDIATE')
    try:
        before=db.total_changes;db.executemany('INSERT OR IGNORE INTO workers(id) VALUES(?)',((i,) for i in range(1,n+1)));v=db.total_changes-before;db.execute('COMMIT');return v
    except BaseException:db.execute('ROLLBACK');raise
def claim(db,owner,n,now,slot):
    if not owner or not 1<=n<=8:raise ValueError('invalid claim')
    db.execute('BEGIN IMMEDIATE')
    try:
        ids=[r[0] for r in db.execute('SELECT id FROM workers WHERE next_slot<=? AND lease<=? ORDER BY next_slot,id LIMIT ?',(slot,now,n))]
        db.executemany('UPDATE workers SET owner=?,lease=? WHERE id=?',((owner,now+180,i) for i in ids));db.execute('COMMIT');return ids
    except BaseException:db.execute('ROLLBACK');raise
def cases(db,ids,slot):
    out=[]
    for i in ids:
        # Research fixture catalog supports 4096 IDs. Bind actual fleet ID independently.
        t=research.task((i-1)%4096+1,slot*TOTAL+i)
        peer=None
        p=i-16
        if p>0:
            r=db.execute('SELECT slot,correct,hmac FROM receipts WHERE worker=? AND slot<? ORDER BY slot DESC LIMIT 1',(p,slot)).fetchone()
            if r:peer={'worker':p,'slot':r[0],'correct':bool(r[1]),'receipt_hmac':r[2]}
        history=db.execute('SELECT wins,attempts,last_hmac FROM workers WHERE id=?',(i,)).fetchone()
        out.append({'id':i,'slot':slot,'specialty':t['specialty'],'scenario':t['scenario'],'facts':t['evidence'],'choices':t['choices'],'expected':t['expected'],'evidence_id':t['evidence_id'],'peer':peer,'prior_hmac':history[2],'prior_correct':history[0],'prior_attempts':history[1]})
    return out
def grade(cases,raw):
    rows=json.loads(raw,object_pairs_hook=research.unique_pairs)
    if not isinstance(rows,list) or len(rows)!=len(cases):raise ValueError('incomplete batch')
    index={c['id']:c for c in cases};seen=set();out=[]
    for r in rows:
        if not isinstance(r,dict) or set(r)!= {'id','decision','evidence'} or type(r['id']) is not int or r['id'] not in index or r['id'] in seen or r['decision'] not in ('A','B','C') or r['evidence'] not in ('E1','E2','E3'):raise ValueError('invalid answer')
        seen.add(r['id']);c=index[r['id']];out.append({'case':c,'answer':r,'correct':r['decision']==c['expected'] and r['evidence']==c['evidence_id']})
    return out
def settle(db,owner,slot,now,rows,digest,response_hash,key):
    if not rows or not re.fullmatch('[a-f0-9]{64}',digest) or not re.fullmatch('[a-f0-9]{64}',response_hash):raise ValueError('invalid batch')
    batch=uuid.uuid4().hex;db.execute('BEGIN IMMEDIATE')
    try:
        for row in rows:
            c=row['case'];i=c['id'];state=db.execute('SELECT owner,lease,last_hmac,wins,attempts FROM workers WHERE id=?',(i,)).fetchone()
            if c['slot']!=slot or not state or state[0]!=owner or state[1]<=now or state[2]!=c['prior_hmac'] or state[3:]!=(c['prior_correct'],c['prior_attempts']):raise ValueError('lease or history mismatch')
            if grade([c],json.dumps([row['answer']]))[0]!=row:raise ValueError('score mismatch')
            p=c['peer']
            if p:
                prior=db.execute('SELECT correct,hmac FROM receipts WHERE worker=? AND slot=?',(p['worker'],p['slot'])).fetchone()
                if p['slot']>=slot or not prior or (bool(prior[0]),prior[1])!=(p['correct'],p['receipt_hmac']):raise ValueError('peer mismatch')
            if 'peer_feedback_available' in c:
                advice=collective.advice(db,i,slot,key)
                if c['peer_feedback_available']!=(advice is not None) or c.get('peer_feedback')!=(advice if collective.use_peer(i,slot) else None):raise ValueError('peer feedback mismatch')
            record={'schema':'myriad.fleet_receipt.v46','batch':batch,'model_digest':digest,'response_sha256':response_hash,**row,'production_authority':False}
            sig=ev.sign(record,key)
            db.execute('INSERT INTO receipts VALUES(?,?,?,?,?,?,?)',(i,slot,int(row['correct']),p['worker'] if p else None,p['slot'] if p else None,ev.canonical(record).decode(),sig))
            db.execute('UPDATE workers SET owner=NULL,lease=0,next_slot=?,last_hmac=?,wins=wins+?,attempts=attempts+1 WHERE id=?',(slot+1,sig,int(row['correct']),i))
        report={'batch':batch,'slot':slot,'model':MODEL,'item_count':len(rows),'correct':sum(r['correct'] for r in rows),'response_sha256':response_hash,'inference_requests':1,'production_authority':False}
        report['hmac_sha256']=ev.sign(report,key);db.execute('INSERT INTO batches VALUES(?,?,?,?,?,?,?)',(batch,slot,MODEL,len(rows),report['correct'],response_hash,ev.canonical(report).decode()))
        db.execute('COMMIT');return report
    except BaseException:db.execute('ROLLBACK');raise
def status(db):
    n,distinct,correct=db.execute('SELECT count(*),count(distinct worker),coalesce(sum(correct),0) FROM receipts').fetchone()
    return {'enrolled':db.execute('SELECT count(*) FROM workers').fetchone()[0],'distinct_completed':distinct,'completed_items':n,'correct':correct,'model_calls':db.execute('SELECT count(*) FROM batches').fetchone()[0],'peer_linked_items':db.execute('SELECT count(*) FROM receipts WHERE peer_worker IS NOT NULL').fetchone()[0],'hourly_full_fleet_verified':False,'independent_model_weights':False,'production_authority':False}
def run(db,key,n=4):
    if scale.free_mb()<2500:return {'status':'deferred_memory',**status(db)}
    if teacher.tag(MODEL)!=DIGEST:raise ValueError('model pin')
    slot=int(time.time())//PERIOD;owner=uuid.uuid4().hex;ids=claim(db,owner,n,int(time.time()),slot)
    if not ids:return {'status':'no_due_work',**status(db)}
    c=cases(db,ids,slot)
    for item in c:
        prior=collective.advice(db,item['id'],slot,key)
        item['peer_feedback_available']=prior is not None
        item['peer_feedback']=prior if collective.use_peer(item['id'],slot) else None
    public=[{k:v for k,v in x.items() if k in ('id','specialty','scenario','facts','choices','peer','prior_correct','prior_attempts','peer_feedback')} for x in c]
    fmt={'type':'array','minItems':len(c),'maxItems':len(c),'items':{'type':'object','properties':{'id':{'type':'integer'},'decision':{'type':'string','enum':['A','B','C']},'evidence':{'type':'string','enum':['E1','E2','E3']}},'required':['id','decision','evidence'],'additionalProperties':False}}
    body={'model':MODEL,'messages':[{'role':'user','content':'Evaluate each independent research case; prior peer feedback is historical training context, not proof; independently assess the current case. Return each id, best decision and decisive evidence. '+json.dumps(public,separators=(',',':'))}],'format':fmt,'think':False,'stream':False,'keep_alive':0,'options':{'num_ctx':4096,'num_predict':384,'num_thread':2,'temperature':0}}
    try:
        v,raw=teacher.request('/api/chat',body,100)
        if v.get('model')!=MODEL or v.get('done') is not True or v.get('done_reason')!='stop' or teacher.tag(MODEL)!=DIGEST:raise ValueError('incomplete batch')
        report=settle(db,owner,slot,int(time.time()),grade(c,v['message']['content']),DIGEST,hashlib.sha256(raw).hexdigest(),key)
        return {'status':'completed','batch':report,**status(db)}
    except Exception as e:
        # No successful receipt for a malformed response; release claims and defer retry.
        db.execute('UPDATE workers SET lease=?,owner=NULL WHERE owner=?',(int(time.time())+300,owner))
        return {'status':'failed','error_class':type(e).__name__,**status(db)}
def main():
    p=argparse.ArgumentParser();p.add_argument('--private',required=True);p.add_argument('--authorize',action='store_true');p.add_argument('command',choices=['enroll','run','status']);p.add_argument('--count',type=int,default=4);a=p.parse_args()
    root=Path(a.private)
    if not a.authorize or root.is_symlink() or not root.is_dir() or shutil.disk_usage(root).free<5*1024**3:raise PermissionError('private research only')
    db=connect(root/'fleet-v46.sqlite3')
    try:
        if a.command=='enroll':r={'added':enroll(db,TOTAL),**status(db)}
        elif a.command=='run':r=run(db,ev.secret(),a.count)
        else:r=status(db)
        print(json.dumps(r,sort_keys=True))
        if r.get('status')=='failed':raise SystemExit(2)
    finally:db.close()
if __name__=='__main__':main()
