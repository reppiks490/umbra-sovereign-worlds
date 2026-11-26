"""Opt-in pinned review transition for a cooperative local ledger.

Pins and lock-marker policy must originate from a trusted operator. This does
not authenticate reviewers, prevent direct DB writes, or replace runtime locks.
"""
import hashlib,os,re,stat
from pathlib import Path
from capability_evidence import _read,_json,_digest
from local_process import settlement

def _safe_dir(p):
    st=p.lstat()
    if not stat.S_ISDIR(st.st_mode) or stat.S_ISLNK(st.st_mode) or getattr(st,'st_file_attributes',0)&0x400:raise ValueError('unsafe directory')
    return p
def _pinned(root,name,pin):
    raw=_read(root,name,262144)
    if hashlib.sha256(raw).hexdigest()!=_digest(pin):raise ValueError('trusted digest mismatch')
    result=_json(raw)
    if not isinstance(result,dict) or type(result.get('schema')) is not int or result['schema']!=1:raise ValueError('review schema')
    return result
def _resource_clear(root,policy,resource):
    if not resource:return
    mapping=policy.get('resource_locks')
    names=mapping.get(resource) if isinstance(mapping,dict) else None
    if not isinstance(names,list) or not names or len(names)>32 or any(not isinstance(n,str) or not re.fullmatch('[A-Za-z0-9_-][A-Za-z0-9_.-]{0,127}',n) for n in names):raise ValueError('resource not configured')
    locks=_safe_dir(root/'locks')
    for name in names:
        try:os.lstat(locks/name)
        except FileNotFoundError:continue
        raise ValueError('external lock present')
def accept_pinned(ledger,root,policy_sha256,review_sha256):
    root=_safe_dir(Path(root)).resolve()
    policy=_pinned(root,'policy.json',policy_sha256)
    review=_pinned(root,'review.json',review_sha256)
    task=review.get('task');verifier=review.get('verifier');detail=review.get('detail')
    if not all(isinstance(v,str) and v.strip() for v in (task,verifier,detail)) or review.get('outcome')!='approved':raise ValueError('review disposition')
    with ledger.tx() as c:
        r=c.execute("SELECT * FROM tasks WHERE id=? AND state='reported'",(task,)).fetchone()
        if not r or r['owner']==verifier:raise ValueError('distinct reviewer required')
        allowed=policy.get('reviewers')
        lanes=allowed.get(verifier) if isinstance(allowed,dict) else None
        if not isinstance(lanes,list) or r['lane'] not in lanes:raise ValueError('reviewer not approved for lane')
        if any(review.get(k)!=v for k,v in {'base':r['base'],'worker':r['owner'],'receipt_sha256':r['receipt'],'handle':r['handle']}.items()):raise ValueError('review identity mismatch')
        _,sha=ledger.evidence(r,r['receipt_path'])
        if sha!=r['receipt']:raise ValueError('worker receipt changed')
        process=None
        if r['handle']:
            identity=_json(r['handle'])
            process=settlement(identity)
            if process['state']!='settled':raise ValueError('local process not settled')
        _resource_clear(root,policy,r['resource'])
        c.execute("UPDATE tasks SET state='qualified',verifier=?,handle=NULL,reason=? WHERE id=?",(verifier,detail,task))
        ledger.event(c,task,'pinned-qualified',{'verifier':verifier,'detail':detail,'receipt':sha,'review_sha256':review_sha256,'policy_sha256':policy_sha256,'process':process})
    return {'task':task,'state':'qualified','review_sha256':review_sha256,'policy_sha256':policy_sha256}
