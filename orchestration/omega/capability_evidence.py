"""Pinned local evidence admission for the advisory router.

The manifest digest must come from a separately trusted operator or verifier.
No authentication, dispatch, review identity, or write authority is granted.
"""
import hashlib,json,re
from pathlib import Path
from capability_router import select

def _sha(raw):return hashlib.sha256(raw).hexdigest()
def _digest(v):
    if not isinstance(v,str) or not re.fullmatch('[a-f0-9]{64}',v):raise ValueError('digest')
    return v
def _read(root,name,limit):
    if not isinstance(name,str) or not name or '\\' in name or ':' in name:raise ValueError('path')
    parts=name.split('/')
    if any(x in ('','.','..') for x in parts):raise ValueError('path')
    p=root
    for part in parts:
        p=p/part
        if p.is_symlink() or getattr(p,'is_junction',lambda:False)():raise ValueError('linked path')
    if not p.is_file() or not p.resolve().is_relative_to(root):raise ValueError('missing or escaped evidence')
    with p.open('rb') as f:raw=f.read(limit+1)
    if len(raw)>limit:raise ValueError('evidence size')
    return raw
def _json(raw):
    def pairs(rows):
        d={}
        for k,v in rows:
            if k in d:raise ValueError('duplicate json key')
            d[k]=v
        return d
    try:return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite json')))
    except (TypeError,UnicodeError,ValueError) as exc:raise ValueError('invalid evidence json') from exc

def verified_select(root,manifest_sha256,registry,policy,lane,intent,now,max_age=3600):
    pin=_digest(manifest_sha256)
    root=Path(root)
    if not root.is_dir() or root.is_symlink() or getattr(root,'is_junction',lambda:False)():raise ValueError('evidence root')
    root=root.resolve()
    raw=_read(root,'manifest.json',262144)
    if _sha(raw)!=pin:raise ValueError('manifest digest mismatch')
    m=_json(raw)
    if not isinstance(m,dict) or type(m.get('schema')) is not int or m['schema']!=1 or not isinstance(m.get('receipts'),list) or len(m['receipts'])>256:raise ValueError('manifest schema')
    rows=[];seen=set();total=0
    for entry in m['receipts']:
        if not isinstance(entry,dict):raise ValueError('receipt entry')
        path=entry.get('path')
        if not isinstance(path,str) or path in seen or path=='manifest.json':raise ValueError('receipt path')
        seen.add(path)
        raw=_read(root,path,262144)
        sha=_digest(entry.get('sha256'))
        if _sha(raw)!=sha:raise ValueError('receipt digest mismatch')
        r=_json(raw)
        if not isinstance(r,dict) or not isinstance(r.get('action'),str) or type(r.get('observed_at')) not in (float,int) or r.get('status') not in ('verified-read','failed'):raise ValueError('receipt schema')
        if r['status']=='verified-read':
            expected=_digest(r.get('output_sha256'))
            output=_read(root,r.get('output'),8*1024**2)
            total+=len(output)
            if total>64*1024**2:raise ValueError('aggregate output limit')
            if _sha(output)!=expected:raise ValueError('output digest mismatch')
        rows.append({'action':r['action'],'observed_at':r['observed_at'],'status':r['status'],'receipt_sha256':sha})
    return select(registry,policy,rows,lane,intent,now,max_age)
