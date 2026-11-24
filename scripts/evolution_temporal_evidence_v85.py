"""Research-only bitemporal evidence admission and purged chronological splits.

Times are explicit integer UTC epoch seconds. Event time is when an observation
occurred, available time is when that exact revision was demonstrably accessible.
No inference of availability, provider integration, trading, or execution.
"""
import math
import re

MAX_ROWS=100000
MAX_TIME=2**63-1
FIELDS={'source','series','entity','event_time','available_time','revision','value','source_sha256'}
LABEL_FIELDS={'id','decision_time','label_end','label_available'}


def integer(v,lo=0,hi=MAX_TIME):
    return type(v) is int and lo<=v<=hi


def text_id(v):
    return isinstance(v,str) and 1<=len(v)<=128 and re.fullmatch(r'[A-Za-z0-9_.:/-]+',v) is not None


def finite(v):
    return type(v) in (int,float) and -1e300<=v<=1e300 and math.isfinite(v)


def collection(rows):
    if not isinstance(rows,list) or len(rows)>MAX_ROWS:raise ValueError('row budget')


def record_key(r):
    return (r['source'],r['series'],r['entity'],r['event_time'])


def validate(rows):
    collection(rows);groups={}
    for r in rows:
        if not isinstance(r,dict) or set(r)!=FIELDS or any(not text_id(r[k]) for k in ('source','series','entity')) or not integer(r['event_time']) or not integer(r['available_time'],r['event_time']) or not integer(r['revision'],0,2**31-1) or not finite(r['value']) or not isinstance(r['source_sha256'],str) or re.fullmatch('[0-9a-f]{64}',r['source_sha256']) is None:
            raise ValueError('invalid temporal record')
        versions=groups.setdefault(record_key(r),{});rev=r['revision']
        if rev in versions and versions[rev]!=r:raise ValueError('conflicting revision')
        versions[rev]=dict(r)
    for versions in groups.values():
        times=[versions[i]['available_time'] for i in sorted(versions)]
        if any(a>=b for a,b in zip(times,times[1:])):raise ValueError('nonmonotonic revision availability')
    return groups


def snapshot(rows,as_of):
    """Return each event's latest revision actually available at as_of."""
    if not integer(as_of):raise ValueError('invalid cutoff')
    groups=validate(rows);out=[]
    for key,versions in sorted(groups.items()):
        eligible=[r for r in versions.values() if r['available_time']<=as_of]
        if eligible:out.append(max(eligible,key=lambda r:r['revision']))
    return out


def latest(rows,as_of,max_age):
    """Select latest known observation per source/series/entity; no forward fill past age."""
    if not integer(max_age):raise ValueError('invalid staleness limit')
    result={}
    for r in snapshot(rows,as_of):
        if as_of-r['event_time']>max_age:continue
        key=record_key(r)[:3]
        if key not in result or r['event_time']>result[key]['event_time']:result[key]=r
    return [result[k] for k in sorted(result)]


def purged_split(rows,test_start,test_end,embargo,evaluation_as_of):
    """Train labels must mature strictly before the embargo boundary.

    Test membership is [test_start,test_end); labels must be available by the
    explicit evaluation cutoff. Rows after test_end are not evaluated.
    """
    collection(rows)
    if not integer(test_start,1) or not integer(test_end,test_start+1) or not integer(embargo,0,test_start) or not integer(evaluation_as_of,test_end):raise ValueError('invalid split bounds')
    cutoff=test_start-embargo;seen=set();valid=[]
    for r in rows:
        if not isinstance(r,dict) or set(r)!=LABEL_FIELDS or not text_id(r['id']) or r['id'] in seen or not integer(r['decision_time']) or not integer(r['label_end'],r['decision_time']) or not integer(r['label_available'],r['label_end']):raise ValueError('invalid label row')
        seen.add(r['id']);valid.append(r)
    out={'train':[],'test':[],'purged_train':[],'unmatured_test':[],'outside':[]}
    for r in sorted(valid,key=lambda x:(x['decision_time'],x['id'])):
        when=r['decision_time']
        if when<test_start:
            part='train' if when<cutoff and r['label_available']<cutoff else 'purged_train'
        elif when<test_end:part='test' if r['label_available']<=evaluation_as_of else 'unmatured_test'
        else:part='outside'
        out[part].append(r['id'])
    return out
