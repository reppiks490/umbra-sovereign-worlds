"""Opt-in authenticated lifecycle prototype for isolated, resource-free jobs.
Direct DB access, live runtime and external process ownership are out of scope.
"""
import hashlib,hmac,sqlite3,time
from pathlib import Path
from claim_broker import ClaimBroker,FIELDS
from omega_ledger import canonical,require
REPORT_FIELDS=FIELDS|{'token','receipt_path','receipt_sha256','detail'}
REVIEW_FIELDS=FIELDS|{'worker','receipt_sha256','detail'}
def sign_transition(request,key):
    if not isinstance(request,dict) or not isinstance(key,bytes) or len(key)<32:raise ValueError('signing input')
    return hmac.new(key,b'OMEGA-TRANSITION-v1\x00'+canonical(request).encode('utf8'),hashlib.sha256).hexdigest()
class LifecycleBroker(ClaimBroker):
    def __init__(self,ledger,broker_id,keys,policy,roles):
        if not isinstance(roles,dict) or set(roles)!=set(keys) or any(r not in ('worker','reviewer') for r in roles.values()):raise ValueError('role configuration')
        super().__init__(ledger,broker_id,keys,policy)
        self._roles=dict(roles)
    def claim(self,request,signature,now=None):
        if not isinstance(request,dict) or not isinstance(request.get('principal'),str) or self._roles.get(request['principal'])!='worker':raise ValueError('worker role required')
        return super().claim(request,signature,now)
    def transition(self,request,signature,now=None):
        now=int(time.time()) if now is None else now
        if not isinstance(request,dict) or type(now) is not int:raise ValueError('request')
        r=dict(request);action=r.get('action')
        fields=REPORT_FIELDS if action=='report' else REVIEW_FIELDS if action=='review' else None
        if fields is None or set(r)!=fields or type(r['schema']) is not int or r['schema']!=1:raise ValueError('transition schema')
        principal=require(r['principal'],r'[A-Za-z0-9_.:-]{1,128}')
        require(r['task'],r'[A-Za-z0-9_.:-]{1,128}');require(r['base'],r'[a-f0-9]{40}|[a-f0-9]{64}')
        require(r['nonce'],r'[a-f0-9]{32}');require(r['receipt_sha256'],r'[a-f0-9]{64}');require(signature,r'[a-f0-9]{64}')
        if r['broker']!=self.broker_id or not isinstance(r['lane'],str) or r['lane'] not in self._policy.get(principal,()) or self._roles.get(principal)!=('worker' if action=='report' else 'reviewer'):raise ValueError('transition scope')
        if type(r['issued_at']) is not int or not 0<=now-r['issued_at']<=60:raise ValueError('transition freshness')
        if not isinstance(r['detail'],str) or not 1<=len(r['detail'].strip())<=4000:raise ValueError('detail')
        if not hmac.compare_digest(signature,sign_transition(r,self._keys[principal])):raise ValueError('transition authentication')
        with self.l.tx() as c:
            args=(self.broker_id,principal,r['nonce'])
            if c.execute('SELECT 1 FROM broker_nonces WHERE broker=? AND principal=? AND nonce=?',args).fetchone():raise ValueError('replay')
            task=c.execute('SELECT * FROM tasks WHERE id=? AND lane=? AND base=?',(r['task'],r['lane'],r['base'])).fetchone()
            if not task or task['resource'] or task['handle']:raise ValueError('task outside resource-free lifecycle')
            lease=c.execute('SELECT * FROM broker_leases WHERE broker=? AND task=? AND token=? AND principal=?',(self.broker_id,task['id'],task['token'],task['owner'])).fetchone()
            if not lease:raise ValueError('no authenticated lease')
            if action=='report':
                if task['state']!='leased' or task['owner']!=principal or lease['reported_sha'] is not None or not hmac.compare_digest(require(r['token'],r'[a-f0-9]{32}'),task['token']):raise ValueError('report ownership')
                name=require(r['receipt_path'],r'[A-Za-z0-9_-][A-Za-z0-9_.-]{0,127}\.json')
                root=Path(self.l.path).resolve().parent/'evidence'
                path,sha=self.l.evidence(task,str(root/name))
                if sha!=r['receipt_sha256']:raise ValueError('receipt digest mismatch')
                c.execute("UPDATE tasks SET state='reported',receipt=?,receipt_path=?,reason=? WHERE id=?",(sha,path,r['detail'],task['id']))
                c.execute('UPDATE broker_leases SET reported_sha=? WHERE broker=? AND task=? AND token=?',(sha,self.broker_id,task['id'],task['token']))
                state='reported'
            else:
                if task['state']!='reported' or task['owner']==principal or r['worker']!=task['owner'] or self._roles.get(task['owner'])!='worker' or lease['reported_sha']!=task['receipt'] or task['receipt']!=r['receipt_sha256']:raise ValueError('review binding')
                _,sha=self.l.evidence(task,task['receipt_path'])
                if sha!=task['receipt']:raise ValueError('receipt changed')
                c.execute("UPDATE tasks SET state='qualified',verifier=?,reason=? WHERE id=?",(principal,r['detail'],task['id']))
                state='qualified'
            c.execute('INSERT INTO broker_nonces(broker,principal,nonce,issued_at) VALUES(?,?,?,?)',(*args,r['issued_at']))
            self.l.event(c,task['id'],'broker-'+state,{'principal':principal,'broker':self.broker_id,'receipt':sha,'nonce':r['nonce']})
            return {'id':task['id'],'state':state,'receipt':sha}
