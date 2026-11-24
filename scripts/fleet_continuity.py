"""Recover a prior successful synthetic fleet partition without treating hashes as attestation."""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
import hashlib,json,re

def _hour(v):
    if not isinstance(v,str) or not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d',v):raise ValueError('Invalid UTC hour')
    d=datetime.strptime(v,'%Y-%m-%dT%H')
    if d.strftime('%Y-%m-%dT%H')!=v:raise ValueError('Noncanonical UTC hour')
    return d

def hydrate_prior(root,db_path,shard,current_hour,source,mesh):
    root=Path(root); db_path=Path(db_path)
    if type(shard) is not int or not 0<=shard<195 or not re.fullmatch('[a-f0-9]{40}',source):raise ValueError('Invalid partition/source')
    if db_path.exists():raise ValueError('Refusing to replace existing ledger')
    summary=root/'summary.json'
    if not summary.is_file() or summary.stat().st_size>65536:raise ValueError('Invalid group summary')
    meta=json.loads(summary.read_bytes());prior=meta.get('hour')
    if meta.get('source')!=source or meta.get('group')!=shard//13 or meta.get('count')!=13000 or meta.get('production_authority') is not False or meta.get('neural_training') is not False or _hour(prior)>=_hour(current_hour):raise ValueError('Invalid prior run source, time or authority')
    desc=[v for v in meta['shards'] if v.get('shard')==shard]
    if len(desc)!=1 or desc[0].get('count')!=1000:raise ValueError('Missing or duplicated shard')
    p=root/f'shard-{shard}.jsonl'
    if not p.is_file() or p.stat().st_size>8*1024*1024:raise ValueError('Missing or oversized prior shard')
    raw=p.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=desc[0].get('sha256'):raise ValueError('Prior artifact digest mismatch')
    records={};expected={f'E{i:06d}' for i in range(1+shard,195001,195)}
    for line in raw.splitlines():
        if len(line)>8192:raise ValueError('Oversized receipt')
        r=json.loads(line);wid=r.get('workflow');receipt=r.get('receipt_sha256')
        if wid not in expected or wid in records or r.get('hour')!=prior:raise ValueError('Invalid or duplicated prior worker identity')
        wf=mesh.workflow(int(wid[1:]))
        if r.get('domain')!=wf['domain'] or r.get('algorithm')!=mesh.recipe(wf['algorithm_id']):raise ValueError('Prior receipt has forged domain or algorithm')
        if r.get('deployment_authorized') is not False or r.get('real_model_weight_training') is not False or r.get('review_status') not in ('candidate_for_manual_review','rejected_synthetic') or r.get('peer_provenance_schema')!='umbra.evolution.parent_link.v21':raise ValueError('Invalid prior receipt authority')
        if receipt!=mesh.digest({k:v for k,v in r.items() if k!='receipt_sha256'}):raise ValueError('Prior receipt hash mismatch')
        records[wid]=r
    if set(records)!=expected:raise ValueError('Prior partition is incomplete')
    db=mesh.connect(db_path)
    try:
        with db:
            db.executemany('INSERT INTO runs(hour,workflow,domain,receipt,record) VALUES(?,?,?,?,?)',[(prior,w,r['domain'],r['receipt_sha256'],json.dumps(r,sort_keys=True)) for w,r in records.items()])
    finally:db.close()
    return records

def verify_parent(row,records):
    parent=row.get('peer_parent');used=row.get('peer_used')
    if used is False and parent is None:return False
    if used is not True or not isinstance(parent,dict):raise ValueError('Invalid peer-use flag')
    p=records.get(parent.get('parent_workflow'))
    if not p or p['workflow']==row['workflow'] or p['domain']!=row['domain'] or _hour(p['hour'])>=_hour(row['hour']) or p['review_status']!='candidate_for_manual_review':raise ValueError('Unqualified or unbacked parent')
    expected={'parent_workflow':p['workflow'],'parent_hour':p['hour'],'parent_domain':p['domain'],'parent_receipt_sha256':p['receipt_sha256']}
    if parent!=expected:raise ValueError('Parent receipt mismatch')
    return True
