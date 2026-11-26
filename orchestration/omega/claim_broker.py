"""Isolated authenticated claim prototype; never deploy with direct DB access.
Keys must be provisioned out of band and protected by an owner-controlled process.
Resource-bearing jobs are intentionally refused pending runtime lock integration.
"""
import hashlib,hmac,json,re,time,uuid
from omega_ledger import canonical,LANES,require

FIELDS={'schema','broker','principal','action','lane','task','base','issued_at','nonce'}
def sign_request(request,key):
    if not isinstance(key,bytes) or len(key)<32:raise ValueError('invalid signing key')
    if not isinstance(request,dict):raise ValueError('request')
    return hmac.new(key,b'OMEGA-CLAIM-v1\x00'+canonical(request).encode('utf8'),hashlib.sha256).hexdigest()

class ClaimBroker:
    def __init__(self,ledger,broker_id,keys,policy):
        self.l=ledger
        self.broker_id=require(broker_id,r'[A-Za-z0-9_.:-]{1,128}')
        if not isinstance(keys,dict) or not keys or not isinstance(policy,dict) or set(keys)!=set(policy):raise ValueError('principal configuration')
        for principal,key in keys.items():
            require(principal,r'[A-Za-z0-9_.:-]{1,128}')
            if not isinstance(key,bytes) or len(key)<32:raise ValueError('invalid key')
            lanes=policy[principal]
            if not isinstance(lanes,list) or not lanes or any(lane not in LANES for lane in lanes):raise ValueError('principal policy')
        if len(set(keys.values()))!=len(keys):raise ValueError('shared principal key')
        self._keys=dict(keys)
        self._policy={k:frozenset(v) for k,v in policy.items()}
        with self.l.tx() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS broker_nonces(broker TEXT NOT NULL,principal TEXT NOT NULL,nonce TEXT NOT NULL,issued_at INTEGER NOT NULL,PRIMARY KEY(broker,principal,nonce))""")
    def claim(self,request,signature,now=None):
        now=int(time.time()) if now is None else now
        if type(now) is not int or not isinstance(request,dict) or set(request)!=FIELDS or type(request['schema']) is not int or request['schema']!=1:raise ValueError('request schema')
        r=dict(request)
        principal=require(r['principal'],r'[A-Za-z0-9_.:-]{1,128}')
        require(r['task'],r'[A-Za-z0-9_.:-]{1,128}')
        require(r['base'],r'[a-f0-9]{40}|[a-f0-9]{64}')
        require(r['nonce'],r'[a-f0-9]{32}')
        require(signature,r'[a-f0-9]{64}')
        if r['broker']!=self.broker_id or r['action']!='claim' or not isinstance(r['lane'],str) or r['lane'] not in self._policy.get(principal,()):raise ValueError('request scope')
        if type(r['issued_at']) is not int or not 0<=now-r['issued_at']<=60:raise ValueError('request freshness')
        if not hmac.compare_digest(signature,sign_request(r,self._keys[principal])):raise ValueError('request authentication')
        with self.l.tx() as c:
            args=(self.broker_id,principal,r['nonce'])
            if c.execute('SELECT 1 FROM broker_nonces WHERE broker=? AND principal=? AND nonce=?',args).fetchone():raise ValueError('replay')
            task=c.execute("SELECT * FROM tasks WHERE id=? AND lane=? AND base=? AND state='ready'",(r['task'],r['lane'],r['base'])).fetchone()
            if not task:raise ValueError('task not available at exact identity')
            if task['resource']:raise ValueError('external resource admission not integrated')
            for dep in json.loads(task['deps']):
                row=c.execute('SELECT state FROM tasks WHERE id=?',(dep,)).fetchone()
                if not row or row[0]!='qualified':raise ValueError('dependency pending')
            token=uuid.uuid4().hex
            c.execute('INSERT INTO broker_nonces(broker,principal,nonce,issued_at) VALUES(?,?,?,?)',(*args,r['issued_at']))
            c.execute("UPDATE tasks SET state='leased',owner=?,token=?,leased_at=?,reason=NULL,retry_condition=NULL WHERE id=?",(principal,token,now,r['task']))
            self.l.event(c,r['task'],'broker-claimed',{'broker':self.broker_id,'principal':principal,'nonce':r['nonce'],'base':r['base']})
            return dict(c.execute('SELECT * FROM tasks WHERE id=?',(r['task'],)).fetchone())
