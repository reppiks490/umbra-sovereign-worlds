"""Authenticated cross-worker feedback with deterministic control cohort."""
import hmac,json
import evolution_model_evidence_v24 as ev
def use_peer(worker,slot):return (worker+slot)%2==0
def advice(db,worker,slot,key):
    p=worker-16
    if p<1:return None
    row=db.execute('SELECT slot,correct,record,hmac FROM receipts WHERE worker=? AND slot<? ORDER BY slot DESC LIMIT 1',(p,slot)).fetchone()
    if not row:return None
    prev,correct,raw,sig=row
    r=json.loads(raw)
    if not hmac.compare_digest(ev.sign(r,key),sig) or r.get('schema')!='myriad.fleet_receipt.v46' or r.get('production_authority') is not False:raise ValueError('invalid peer receipt')
    c=r['case'];a=r['answer']
    if c['id']!=p or c['slot']!=prev or a['id']!=p or bool(correct)!=r['correct'] or r['correct']!=(a['decision']==c['expected'] and a['evidence']==c['evidence_id']):raise ValueError('peer score mismatch')
    if not correct:return None
    return {'worker':p,'slot':prev,'receipt_hmac':sig,'prior_action':c['choices'][a['decision']],'prior_evidence':c['facts'][a['evidence']],'scope':'previous correct synthetic task, not current answer or independently verified new research'}
def summarize(db):
    counts={}
    for raw,correct in db.execute('SELECT record,correct FROM receipts'):
        r=json.loads(raw);c=r['case']
        if c.get('peer_feedback_available') is not True:continue
        group='feedback' if c.get('peer_feedback') else 'control'
        n,w=counts.get(group,(0,0));counts[group]=(n+1,w+int(correct))
    return {'cohorts':{k:{'items':n,'correct':w} for k,(n,w) in counts.items()},'causal_benefit_certified':False}
