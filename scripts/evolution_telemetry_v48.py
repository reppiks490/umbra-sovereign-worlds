"""Public aggregate telemetry contract. No prompts, receipts, paths, credentials or weights."""
import hashlib,json,time
SCHEMA='myriad.public_telemetry.v48'
FIELDS=('legacy_enrolled','legacy_completed','fleet_enrolled','fleet_distinct_completed','fleet_completed_items','fleet_model_calls','fleet_peer_linked','specialist_completed','source_completed','ability_rows','ability_bytes','ability_updates','agent_checkpoints','agent_bytes','teacher_labels','student_updates','algorithm_implementations_added')
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def snapshot(epoch,counts):
    v={'schema':SCHEMA,'observed_epoch':epoch,'counts':dict(counts),'research_only':True,'full_fleet_hourly_verified':False,'semantic_abilities_certified':False}
    v['content_sha256']=hashlib.sha256(canonical(v)).hexdigest()
    validate(v,epoch);return v
def validate(v,now):
    if type(now) is not int or now<0:raise ValueError('invalid reference clock')
    if not isinstance(v,dict) or set(v)!= {'schema','observed_epoch','counts','research_only','full_fleet_hourly_verified','semantic_abilities_certified','content_sha256'}:raise ValueError('unexpected telemetry keys')
    if v['schema']!=SCHEMA or v['research_only'] is not True or v['full_fleet_hourly_verified'] is not False or v['semantic_abilities_certified'] is not False:raise ValueError('invalid scope')
    c=v['counts'];t=v['observed_epoch']
    if not isinstance(c,dict) or type(t) is not int or t<0 or t>now+60 or set(c)!=set(FIELDS) or any(type(n) is not int or not 0<=n<=10**14 for n in c.values()):raise ValueError('invalid telemetry')
    if c['legacy_enrolled']>195000 or c['fleet_enrolled']>195000 or c['fleet_distinct_completed']>c['fleet_enrolled'] or c['fleet_distinct_completed']>c['fleet_completed_items'] or c['fleet_peer_linked']>c['fleet_completed_items'] or c['fleet_model_calls']>c['fleet_completed_items'] or c['ability_rows']>10000000 or c['ability_bytes']!=1000*c['ability_rows']:raise ValueError('inconsistent counters')
    if hashlib.sha256(canonical({k:x for k,x in v.items() if k!='content_sha256'})).hexdigest()!=v['content_sha256']:raise ValueError('content digest')
    age=max(0,now-t)
    return {**v,'age_seconds':age,'freshness':'fresh' if age<=1200 else 'stale','transport':'public GitHub aggregate snapshot; content checksum is not an external attestation'}
