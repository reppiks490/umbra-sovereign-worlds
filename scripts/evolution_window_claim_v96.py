"""Fail-closed at-most-once admission for tool-research windows.

Historical receipts are authenticated before reservation. Crash markers consume
windows permanently; they are not evidence of completed inference.
"""
import json,os,stat
from pathlib import Path

CLAIMS='tool-research-claims-v96'
MAX_HISTORY=4096
MAX_RECEIPT=65536

def _safe(path,directory):
    s=path.lstat()
    if stat.S_ISLNK(s.st_mode) or getattr(s,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',1024):raise ValueError('unsafe reparse path')
    if directory and not stat.S_ISDIR(s.st_mode):raise ValueError('expected directory')
    if not directory and not stat.S_ISREG(s.st_mode):raise ValueError('expected regular file')

def _unique(pairs):
    out={}
    for k,v in pairs:
        if k in out:raise ValueError('duplicate JSON field')
        out[k]=v
    return out

def reserve(root,seed,key,verify):
    if type(seed) is not int or not 0<=seed<2**63:raise ValueError('invalid window seed')
    root=Path(root);_safe(root,True)
    hist=root/'teacher-v40';seen=False
    if hist.exists() or hist.is_symlink():
        _safe(hist,True)
        for i,p in enumerate(hist.glob('tool-research-v64-*.json'),1):
            if i>MAX_HISTORY:raise ValueError('receipt scan limit')
            _safe(p,False)
            with p.open('rb') as f:raw=f.read(MAX_RECEIPT+1)
            if len(raw)>MAX_RECEIPT:raise ValueError('receipt size limit')
            r=json.loads(raw,object_pairs_hook=_unique)
            if not isinstance(r,dict) or verify(r,key) is not True or type(r.get('seed')) is not int or not 0<=r['seed']<2**63 or r.get('status') not in ('completed','failed'):raise ValueError('invalid receipt')
            seen|=r['seed']==seed
    if seen:return False
    folder=root/CLAIMS;folder.mkdir(exist_ok=True);_safe(folder,True)
    for i,p in enumerate(folder.glob('*.claim'),1):
        if i>MAX_HISTORY:raise ValueError('claim scan limit')
        _safe(p,False)
    # Exclusive creation serializes contenders. A partial or empty marker
    # remains consumed after interruption: never automatically retry a window.
    path=folder/f'{seed}.claim'
    try:
        with path.open('xb') as f:
            f.write(f'{seed}\n'.encode('ascii'));f.flush();os.fsync(f.fileno())
    except FileExistsError:return False
    return True
