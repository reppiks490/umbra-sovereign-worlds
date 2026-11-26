"""Read-only OMEGA capability recommendations. No dispatch or permission authority."""
import re, math
from collections import defaultdict

def validate_registry(registry):
    if not isinstance(registry,dict):raise ValueError('registry')
    out={}
    for row in registry['connectorNamespaces']:
        name=row['name']
        if not isinstance(name,str) or not name:raise ValueError('namespace')
        for action in row['actions']:
            if not isinstance(action,str) or not action.startswith('mcp__'+name+'__') or action in out:raise ValueError('action identity')
            out[action]=name
    lanes=defaultdict(set)
    for row in registry['routing']:
        lanes[row['lane']].update(row['connectors'])
    return out,lanes

def select(registry,policy,evidence,lane,intent,now,max_age=3600):
    """Recommend a fresh, explicitly allowed read only; receipt identity is not authentication."""
    if type(now) not in (int,float) or not math.isfinite(now) or type(max_age) not in (int,float) or not math.isfinite(max_age) or max_age<=0:raise ValueError('clock')
    actions,lanes=validate_registry(registry)
    observed=defaultdict(list)
    for e in evidence:
        if not isinstance(e,dict) or not isinstance(e.get('action'),str):continue
        observed[e['action']].append(e)
    candidates=[]
    for a,p in policy.items():
        if a not in actions or actions[a] not in lanes.get(lane,set()):continue
        if p.get('lane')!=lane or p.get('intent')!=intent or p.get('effect')!='read':continue
        rank=p.get('rank')
        if type(rank) not in (int,float) or not math.isfinite(rank):continue
        rows=observed.get(a,[])
        if not rows or any(type(e.get('observed_at')) not in (int,float) or not math.isfinite(e['observed_at']) or e['observed_at']>now for e in rows):continue
        latest=max(e['observed_at'] for e in rows)
        if now-latest>max_age:continue
        newest=[e for e in rows if e['observed_at']==latest]
        if any(e!=newest[0] for e in newest):continue
        e=newest[0]
        sha=e.get('receipt_sha256')
        if e.get('status')!='verified-read' or not isinstance(sha,str) or not re.fullmatch('[a-f0-9]{64}',sha):continue
        candidates.append({'action':a,'namespace':actions[a],'lane':lane,'intent':intent,'rank':rank,'receipt_sha256':sha,'observed_at':latest,'authority':'recommendation-only'})
    return sorted(candidates,key=lambda c:(-c['rank'],c['action']))[0] if candidates else None
