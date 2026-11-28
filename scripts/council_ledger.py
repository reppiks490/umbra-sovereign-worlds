"""Immutable local council experiment receipts and nonoverlapping paired aggregates.

Digests detect accidental corruption, not malicious replacement of a receipt.
No training, automatic model selection, or promotion authority.
"""
import hashlib, json, math, os, re, tempfile
from pathlib import Path

def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf8')

def sha(value):
    return hashlib.sha256(encoded(value)).hexdigest()

def natural(x):
    return type(x) is int and x>=0

def validate(r):
    if not isinstance(r,dict) or r.get('status')!='completed':
        raise ValueError('completed trial required')
    if any(r.get(k) is not False for k in ('weight_training','production_authority','test_partition_used_for_inference')):
        raise ValueError('research-only development evidence required')
    m=r.get('manifest',{})
    models=m.get('models',{})
    ids=m.get('validation_records',[])
    n=m.get('count')
    start=m.get('offset')
    if not natural(n) or not 1<=n<=8 or not natural(start) or start+n>715:
        raise ValueError('validation window')
    if not isinstance(models,dict) or len(models)<3 or any(not isinstance(v,str) or not re.fullmatch('[a-f0-9]{64}',v) for v in models.values()) or len(set(models.values()))!=len(models):
        raise ValueError('model identity')
    if not isinstance(ids,list) or len(ids)!=n or any(not isinstance(v,str) or not re.fullmatch('[a-f0-9]{64}',v) for v in ids) or len(set(ids))!=n:
        raise ValueError('case identity')
    if m.get('protocol')!='fixed-one-human-example-strict-majority-v1':
        raise ValueError('protocol')
    if 'manifest_sha256' in r and r['manifest_sha256']!=hashlib.sha256(json.dumps(m,sort_keys=True).encode()).hexdigest():
        raise ValueError('manifest checksum')
    def counts(v):
        if not isinstance(v,dict) or v.get('cases')!=n or not all(natural(v.get(k)) for k in ('cases','answered','correct')) or not 0<=v['correct']<=v['answered']<=n:
            raise ValueError('metric counts')
        return v
    e=counts(r.get('ensemble'))
    baselines=r.get('baselines',{})
    paired=r.get('paired',{})
    if set(baselines)!=set(models) or set(paired)!=set(models):
        raise ValueError('baseline panel')
    for name in models:
        b=counts(baselines[name]);p=paired[name]
        if not all(natural(p.get(k)) for k in ('wins','losses','ties')) or sum(p[k] for k in ('wins','losses','ties'))!=n or p['wins']-p['losses']!=e['correct']-b['correct'] or p['wins']>min(e['correct'],n-b['correct']) or p['losses']>min(b['correct'],n-e['correct']):
            raise ValueError('inconsistent paired comparison')
    calls=r.get('model_calls');completed=r.get('completed_calls');seconds=r.get('inference_seconds')
    if not natural(calls) or calls!=n*len(models) or not natural(completed) or not 0<=completed<=calls or type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<0:
        raise ValueError('execution accounting')
    if sum(b['answered'] for b in baselines.values())>completed:
        raise ValueError('answers exceed completed calls')
    if 'rows' in r:
        rows=r['rows'];keys=set()
        if not isinstance(rows,list) or len(rows)!=calls:
            raise ValueError('row coverage')
        for row in rows:
            key=(row.get('case'),row.get('model'))
            if key in keys or key[0] not in ids or key[1] not in models or row.get('digest')!=models[key[1]]:
                raise ValueError('row identity')
            keys.add(key)
        if sum(row.get('status')=='evaluated' for row in rows)!=completed:
            raise ValueError('row completion')
    return m

def entries(bank):
    results=[]
    seen=set();used=set();panel=None
    for p in sorted(bank.glob('trial-*.json')):
        try:
            env=json.loads(p.read_text(encoding='utf8'))
            r=env['report'];m=validate(r)
            if env['sha256']!=sha(r) or p.name!='trial-'+sha(m)+'.json':
                raise ValueError('receipt integrity')
        except (KeyError,TypeError,OSError,ValueError) as exc:
            raise ValueError('invalid receipt '+p.name) from exc
        identity=(m['models'],m['protocol'])
        if panel is not None and identity!=panel:
            raise ValueError('mixed model panels')
        panel=identity
        offsets=set(range(m['offset'],m['offset']+m['count']))
        ids=set(m['validation_records'])
        if offsets&used or ids&seen:
            raise ValueError('overlapping validation evidence')
        used.update(offsets);seen.update(ids);results.append(r)
    return results

def record(bank,report):
    """Caller holds the qualification lock; replay identical evidence only."""
    m=validate(report)
    bank.mkdir(parents=True,exist_ok=True)
    existing=entries(bank)
    path=bank/('trial-'+sha(m)+'.json')
    if path.exists():
        if json.loads(path.read_text(encoding='utf8'))['sha256']!=sha(report):
            raise ValueError('conflicting replay')
        return path
    for prior in existing:
        old=prior['manifest']
        if old['models']!=m['models'] or old['protocol']!=m['protocol']:
            raise ValueError('mixed model panels')
        if set(old['validation_records'])&set(m['validation_records']) or set(range(old['offset'],old['offset']+old['count']))&set(range(m['offset'],m['offset']+m['count'])):
            raise ValueError('overlapping validation evidence')
    data=encoded({'sha256':sha(report),'report':report})
    # A hard link publishes the completed temporary file without replacing any receipt.
    with tempfile.NamedTemporaryFile(dir=bank,prefix='pending-',delete=False) as f:
        temp=Path(f.name)
        f.write(data);f.flush();os.fsync(f.fileno())
    try:
        os.link(temp,path)
    finally:
        temp.unlink()
    return path

def next_offset(bank,models,count=1):
    if not natural(count) or not 1<=count<=8:
        raise ValueError('window size')
    used=set()
    for r in entries(bank):
        m=r['manifest']
        if m['models']!=models:
            raise ValueError('model panel changed; separate research ledger required')
        used.update(range(m['offset'],m['offset']+m['count']))
    return next((i for i in range(716-count) if all(j not in used for j in range(i,i+count))),None)

def paired_sign_p(wins,losses):
    n=wins+losses
    if not n:
        return 1.0
    return min(1.,2*sum(math.comb(n,i) for i in range(min(wins,losses)+1))/(2**n))

def summarize(bank):
    trials=entries(bank)
    n=sum(r['ensemble']['cases'] for r in trials)
    names=trials[0]['manifest']['models'] if trials else {}
    paired={m:{k:sum(r['paired'][m][k] for r in trials) for k in ('wins','losses','ties')} for m in names}
    for p in paired.values():
        p['exploratory_two_sided_sign_p']=paired_sign_p(p['wins'],p['losses'])
    correct=sum(r['ensemble']['correct'] for r in trials)
    answered=sum(r['ensemble']['answered'] for r in trials)
    return {'trials':len(trials),'cases':n,'ensemble_correct':correct,'ensemble_answered':answered,
            'ensemble_accuracy':correct/n if n else None,'ensemble_answered_accuracy':correct/answered if answered else None,
            'baseline_correct':{m:sum(r['baselines'][m]['correct'] for r in trials) for m in names},
            'paired':paired,'model_calls':sum(r['model_calls'] for r in trials),
            'completed_calls':sum(r['completed_calls'] for r in trials),
            'inference_seconds':sum(r['inference_seconds'] for r in trials),
            'promotion_authorized':False,
            'scope':'nonoverlapping development cases; exploratory unadjusted comparisons; not independent test evidence'}
