"""Pinned development-only benchmark admission. No benchmark weight training."""
import hashlib,io,json,re
from pathlib import Path

PINS={
 'mmlu_abstract_algebra_dev':{
  'repo':'cais/mmlu','revision':'c30699e8356da336a370243923dbaf21066bb9fe',
  'path':'abstract_algebra/dev-00000-of-00001.parquet','size':3452,
  'sha':'e778f60903669e953c49f0d3c8deffa1738a81fe344e0bf1791e450a5e8b9d6c',
  'algorithm':'sha256','split':'evaluation','license':'mit','kind':'dataset'},
 'mbpp_sanitized_validation':{
  'repo':'google-research-datasets/mbpp','revision':'4bb6404fdc6cacfda99d4ac4205087b89d32030c',
  'path':'sanitized/validation-00000-of-00001.parquet','size':13987,
  'sha':'27e065fcab3c863959933328a7fdbf404e1bcb5464b1be6fe0dcd9530e420204',
  'algorithm':'sha256','split':'evaluation','license':'cc-by-4.0','kind':'dataset'},
}

def authenticate(root,key):
    if key not in PINS:raise ValueError('unreviewed development shard')
    pin=PINS[key];base=Path(root).resolve()
    folder=pin['repo'].replace('/','--')+'--'+pin['revision'][:12]
    parts=('intelligence-resources','benchmarks',folder,*pin['path'].split('/'))
    p=base
    for part in parts:
        p=p/part
        if p.is_symlink() or not p.resolve().is_relative_to(base):raise ValueError('source path')
    receipt=p.with_name(p.name+'.receipt.json')
    if receipt.is_symlink() or not receipt.is_file() or receipt.stat().st_size>16384:raise ValueError('receipt path')
    meta=json.loads(receipt.read_text(encoding='utf8'))
    if not isinstance(meta,dict) or any(meta.get(k)!=v for k,v in pin.items()):raise ValueError('publisher receipt identity')
    if not p.is_file() or p.stat().st_size!=pin['size']:raise ValueError('source size')
    with p.open('rb') as f:raw=f.read(pin['size']+1)
    if len(raw)!=pin['size'] or hashlib.sha256(raw).hexdigest()!=pin['sha']:raise ValueError('publisher payload hash')
    if not raw.startswith(b'PAR1') or not raw.endswith(b'PAR1'):raise ValueError('parquet framing')
    return dict(pin),raw

def decode_parquet(raw):
    try:import pyarrow.parquet as pq
    except ImportError as exc:raise RuntimeError('reviewed offline parquet decoder unavailable') from exc
    return pq.read_table(io.BytesIO(raw)).to_pylist()

def load_mmlu(root):
    pin,raw=authenticate(root,'mmlu_abstract_algebra_dev')
    rows=decode_parquet(raw)
    if not isinstance(rows,list) or len(rows)!=5:raise ValueError('development row count')
    out=[];seen=set()
    for i,r in enumerate(rows):
        if not isinstance(r,dict) or r.get('subject')!='abstract_algebra':raise ValueError('subject identity')
        q=r.get('question');c=r.get('choices');a=r.get('answer')
        if not isinstance(q,str) or not q.strip() or len(q)>16000 or not isinstance(c,list) or len(c)!=4 or any(not isinstance(x,str) or not x.strip() or len(x)>16000 for x in c):raise ValueError('question schema')
        if type(a) is not int or not 0<=a<4:raise ValueError('answer label')
        norm=lambda s:' '.join(s.casefold().split())
        if len({norm(x) for x in c})!=4 or norm(q) in seen:raise ValueError('ambiguous or repeated question')
        seen.add(norm(q))
        ident=hashlib.sha256(json.dumps([pin['sha'],i,q,c,a],ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        out.append({'case_id':ident,'question':q,'choices':c,'answer':a,'subject':r['subject'],
                    'source_revision':pin['revision'],'source_sha256':pin['sha'],'split':'development',
                    'training_allowed':False,'qualification':False})
    return out

def grade_mmlu(response,answer):
    if type(answer) is not int or not 0<=answer<4:raise ValueError('answer label')
    if not isinstance(response,str) or not re.fullmatch('[A-D]',response.strip()):return 'abstain'
    return 'correct' if ord(response.strip())-ord('A')==answer else 'incorrect'

def audit(root):
    out=[]
    for key in PINS:
        pin,raw=authenticate(root,key)
        out.append({'key':key,'repo':pin['repo'],'revision':pin['revision'],'sha256':pin['sha'],'bytes':len(raw),
                    'payload_verified':True,'records_decoded':False,'training_allowed':False})
    return out
