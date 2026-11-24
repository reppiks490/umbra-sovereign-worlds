"""Independently reconstructed task ground truth, receipt audit, compact batched inference."""
import hashlib,hmac,json,re,time,uuid
import evolution_research_v37 as research
import evolution_model_evidence_v24 as ev
import evolution_collective_v54 as collective
import evolution_teacher_v40 as teacher
import evolution_fleet_scale_v36 as scale
def fixture(c,slot):
    if type(c['id']) is not int or not 1<=c['id']<=195000 or c['slot']!=slot:raise ValueError('invalid identity')
    t=research.task((c['id']-1)%4096+1,slot*195000+c['id'])
    expected={'specialty':t['specialty'],'scenario':t['scenario'],'facts':t['evidence'],'choices':t['choices'],'expected':t['expected'],'evidence_id':t['evidence_id']}
    if any(c[k]!=v for k,v in expected.items()):raise ValueError('fixture mismatch')
def check_cases(db,rows,slot,key):
    import evolution_fleet_v46 as f
    expected=f.cases(db,[r['case']['id'] for r in rows],slot)
    for r,c in zip(rows,expected):
        actual=r['case'];fixture(actual,slot)
        if any(actual[k]!=v for k,v in c.items()):raise ValueError('case or state mismatch')
        if 'peer_feedback_available' in actual:
            prior=collective.advice(db,c['id'],slot,key)
            if actual['peer_feedback_available']!=(prior is not None) or actual.get('peer_feedback')!=(prior if collective.use_peer(c['id'],slot) else None):raise ValueError('feedback mismatch')
def decode(cases,raw):
    values=json.loads(raw)
    if not isinstance(values,list) or len(values)!=len(cases) or any(not isinstance(x,str) or not re.fullmatch('[ABC][123]',x) for x in values):raise ValueError('invalid compact response')
    return json.dumps([{'id':c['id'],'decision':v[0],'evidence':'E'+v[1]} for c,v in zip(cases,values)],separators=(',',':'))
def audit(db,key):
    import evolution_fleet_v46 as f
    last={};batches={};n=0;correct=0
    for worker,slot,score,peer,peer_slot,raw,sig in db.execute('SELECT worker,slot,correct,peer_worker,peer_slot,record,hmac FROM receipts ORDER BY slot,worker'):
        r=json.loads(raw)
        if not hmac.compare_digest(ev.sign(r,key),sig) or r.get('schema')!='myriad.fleet_receipt.v46' or r.get('production_authority') is not False:raise ValueError('receipt authentication')
        c=r['case'];fixture(c,slot)
        old=last.get(worker,(None,0,0))
        if c['id']!=worker or (c['prior_hmac'],c['prior_correct'],c['prior_attempts'])!=old:raise ValueError('lineage mismatch')
        grade=f.grade([c],json.dumps([r['answer']]))[0]['correct']
        if grade!=r['correct'] or int(grade)!=score:raise ValueError('score mismatch')
        p=c['peer']
        if p:
            row=db.execute('SELECT correct,hmac FROM receipts WHERE worker=? AND slot=?',(peer,peer_slot)).fetchone()
            if peer!=worker-16 or peer_slot>=slot or p['worker']!=peer or p['slot']!=peer_slot or not row or (bool(row[0]),row[1])!=(p['correct'],p['receipt_hmac']):raise ValueError('peer link mismatch')
        elif peer is not None or peer_slot is not None:raise ValueError('unexpected peer')
        if 'peer_feedback_available' in c:
            a=collective.advice(db,worker,slot,key)
            if c['peer_feedback_available']!=(a is not None) or c.get('peer_feedback')!=(a if collective.use_peer(worker,slot) else None):raise ValueError('feedback replay mismatch')
        last[worker]=(sig,old[1]+score,old[2]+1);n+=1;correct+=score
        b=batches.setdefault(r['batch'],{'items':[],'hash':r['response_sha256'],'slot':slot})
        if b['hash']!=r['response_sha256'] or b['slot']!=slot:raise ValueError('batch binding')
        b['items'].append((c,r['answer'],score))
    seen=set()
    for bid,slot,model,count,wins,response,raw in db.execute('SELECT id,slot,model,n,correct,response_sha,record FROM batches'):
        v=json.loads(raw);sig=v.pop('hmac_sha256')
        if not hmac.compare_digest(ev.sign(v,key),sig) or v.get('production_authority') is not False:raise ValueError('batch HMAC')
        b=batches.get(bid)
        if not b or (slot,count,wins,response)!=(b['slot'],len(b['items']),sum(x[2] for x in b['items']),b['hash']) or (v['batch'],v['slot'],v['model'],v['item_count'],v['correct'],v['response_sha256'],v['inference_requests'])!=(bid,slot,model,count,wins,response,1):raise ValueError('batch counters')
        if 'compact_output' in v:
            by_id={x[0]['id']:x for x in b['items']}
            order=v.get('compact_worker_order',sorted(by_id))
            if len(order)!=len(by_id) or set(order)!=set(by_id):raise ValueError('compact order mismatch')
            ordered=[by_id[i] for i in order];cases=[x[0] for x in ordered]
            if json.loads(decode(cases,v['compact_output']))!=[x[1] for x in ordered]:raise ValueError('compact output replay mismatch')
        seen.add(bid)
    if seen!=set(batches):raise ValueError('orphan batch')
    for worker,receipt,wins,attempts in db.execute('SELECT id,last_hmac,wins,attempts FROM workers WHERE attempts>0'):
        if last.get(worker)!=(receipt,wins,attempts):raise ValueError('worker counters')
    return {'verified_items':n,'verified_batches':len(seen),'distinct_workers':len(last),'correct':correct,'production_authority':False}
def run(db,key,n=8):
    import evolution_fleet_v46 as f
    if scale.free_mb()<2500:return {'status':'deferred_memory',**f.status(db)}
    if teacher.tag(f.MODEL)!=f.DIGEST:raise ValueError('model pin')
    slot=int(time.time())//f.PERIOD;owner=uuid.uuid4().hex;ids=f.claim(db,owner,n,int(time.time()),slot)
    if not ids:return {'status':'no_due_work',**f.status(db)}
    try:
        c=f.cases(db,ids,slot)
        for item in c:
            a=collective.advice(db,item['id'],slot,key);item['peer_feedback_available']=a is not None;item['peer_feedback']=a if collective.use_peer(item['id'],slot) else None
        public=[]
        for i,item in enumerate(c,1):
            p={'n':i,'scenario':item['scenario'],'facts':item['facts'],'choices':item['choices']}
            if item['peer_feedback']:p['prior_example']={k:item['peer_feedback'][k] for k in ('prior_action','prior_evidence')}
            public.append(p)
        fmt={'type':'array','minItems':len(c),'maxItems':len(c),'items':{'type':'string','enum':[a+b for a in 'ABC' for b in '123']}}
        prompt='For every numbered case select the best choice and decisive fact independently. Output exactly one two-character string per case, in order, e.g. A1 means choice A and evidence E1. Prior examples may be wrong for the current case. '+json.dumps(public,separators=(',',':'))
        body={'model':f.MODEL,'messages':[{'role':'user','content':prompt}],'format':fmt,'think':False,'stream':False,'keep_alive':0,'options':{'num_ctx':4096,'num_predict':128,'num_thread':2,'temperature':0}}
        start=time.monotonic();v,raw=teacher.request('/api/chat',body,100)
        if v.get('model')!=f.MODEL or v.get('done') is not True or v.get('done_reason')!='stop' or teacher.tag(f.MODEL)!=f.DIGEST:raise ValueError('incomplete compact batch')
        output=v['message']['content'];rows=f.grade(c,decode(c,output))
        report=f.settle(db,owner,slot,int(time.time()),rows,f.DIGEST,hashlib.sha256(raw).hexdigest(),key,compact_output=output)
        return {'status':'completed','batch':report,'elapsed_seconds':round(time.monotonic()-start,3),**f.status(db)}
    except Exception as e:
        db.execute('UPDATE workers SET lease=?,owner=NULL WHERE owner=?',(int(time.time())+300,owner))
        return {'status':'failed','error_class':type(e).__name__,**f.status(db)}
