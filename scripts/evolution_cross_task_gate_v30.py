#!/usr/bin/env python3
"""MYRIAD v3.0 immutable, baseline-aware cross-task admission tribunal.

Requires *real* FP16 source/candidate replay for authoritative evaluation.
A research pass never authorizes a model promotion, UMBRA main merge or trade.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re
from pathlib import Path
import evolution_transfer_ood_v28 as ood

SCHEMA='myriad.synthetic_cross_task_admission.v30'
REQUIRED_WIN_COUNT=6  # majority across each of 11 subjects, each family, each seed
FAMILIES=ood.FAMILIES
SEEDS=ood.PREREGISTERED_SEEDS
IDENTITIES={('agent',i) for i in range(1,11)}|{('ability_bank',10000)}
DIGEST=re.compile(r'[0-9a-f]{64}\Z')


def sha(data):return hashlib.sha256(data).hexdigest()
def canonical(data):return json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def seal(data):
    p={k:v for k,v in data.items() if k!='receipt_sha256'}
    p['receipt_sha256']=sha(canonical(p))
    return p

def verify_seal(data):
    if not isinstance(data,dict) or data.get('schema')!=SCHEMA:raise ValueError('Wrong admission report schema')
    p=dict(data);digest=p.pop('receipt_sha256',None)
    if type(digest) is not str or digest!=sha(canonical(p)):
        raise ValueError('Invalid admission receipt checksum')
    for k in ('production_authority','automatic_promotion','market_alpha_certified'):
        if data.get(k) is not False:raise ValueError('Report cannot assert production authority')
    if data.get('production_release_gates_verified')!=0 or data.get('status') not in ('BLOCKED_TRANSFER_EVIDENCE','RESEARCH_REVIEW_ELIGIBLE'):
        raise ValueError('Unsafe release status')
    return True

def assert_digest(value,label):
    if type(value) is not str or not DIGEST.fullmatch(value):raise ValueError(f'Invalid {label}')

def validate_sample(d):
    if not ood.verify_seal(d):raise ValueError('Source receipt integrity invalid')
    if d.get('source_import_status')!='imported_unverified':raise ValueError('Unattested source must not claim verified training')
    if d.get('candidate_agent_count')!=10 or d.get('candidate_adapter_count')!=10000:
        raise ValueError('Partial model cohort')
    if d.get('unseen_target_families')!=3 or d.get('precommitted_seeds')!=list(SEEDS):
        raise ValueError('Changed experimental plan')
    if d.get('selection_rule')!='all 3 families; 10 agents and full ability adapter bank; zero baseline included':
        raise ValueError('Changed comparison selection rule')
    for k in ('source_archive_sha256','v25_training_receipt_sha256'):
        assert_digest(d.get(k),k)
    rows=d['rows']
    if len(rows)!=33:raise ValueError('Exactly 33 independent comparison records per seed required')
    summary={}
    for family in FAMILIES:
        group=[x for x in rows if x.get('family')==family]
        if len(group)!=11 or {(x.get('subject'),x.get('identity')) for x in group}!=IDENTITIES:
            raise ValueError('Missing/duplicate/wrong identity in family')
        if any(type(x.get('identity')) is not int for x in group):
            raise ValueError('Non-integer model identity')
        for x in group:
            for key in ('inputs_sha256','target_sha256'):
                assert_digest(x.get(key),key)
        metrics={
            'comparisons':len(group),'beats_source':sum(x['beats_source'] for x in group),
            'beats_zero':sum(x['beats_zero'] for x in group),
            'wins_both':sum(x['beats_source'] and x['beats_zero'] for x in group)
        }
        if d.get('summary',{}).get(family)!=metrics:
            raise ValueError('Submitted aggregate mismatches per-model evidence')
        summary[family]=metrics
    if set(d.get('summary',{}))!=set(FAMILIES):raise ValueError('Extra or omitted target family')
    return summary

def assess(receipts):
    if not isinstance(receipts,(list,tuple)) or len(receipts)!=len(SEEDS):
        raise ValueError('Both preregistered seeds required')
    seen={}
    for d in receipts:
        if not isinstance(d,dict) or type(d.get('seed')) is not int or d.get('seed') not in SEEDS or d['seed'] in seen:
            raise ValueError('Receipt seed not preregistered or duplicated')
        groups=validate_sample(d)
        seen[d['seed']]=(d,groups)
    if set(seen)!=set(SEEDS):raise ValueError('All preregistered seeds must be present')
    identities={(d['source_archive_sha256'],d['v25_training_receipt_sha256']) for d,_ in seen.values()}
    if len(identities)!=1:raise ValueError('Inconsistent preserved source or trained candidate lineage')
    wins=sum(m['wins_both'] for _,groups in seen.values() for m in groups.values())
    needs={str(seed):{fam:groups[fam]['wins_both'] for fam in FAMILIES} for seed,(d,groups) in sorted(seen.items())}
    permitted=all(x>=REQUIRED_WIN_COUNT for by_family in needs.values() for x in by_family.values())
    return {'schema':SCHEMA,'status':'RESEARCH_REVIEW_ELIGIBLE' if permitted else 'BLOCKED_TRANSFER_EVIDENCE',
            'threshold_wins_both_per_family_per_seed':REQUIRED_WIN_COUNT,
            'per_seed_family_wins_both':needs,
            'wins_both':wins,'comparison_count':len(SEEDS)*len(FAMILIES)*len(IDENTITIES),
            'provenance':{'source_archive_sha256':next(iter(identities))[0],
                'training_receipt_sha256':next(iter(identities))[1],
                'original_training_origin_authenticated':False},
            'private_source_receipt_shas':{str(seed):seen[seed][0]['receipt_sha256'] for seed in SEEDS},
            'independently_replayed_from_saved_FP16':False,
            'production_release_gates_verified':0,'production_authority':False,
            'automatic_promotion':False,'market_alpha_certified':False,
            'scope':'fixed new synthetic target families only; passing this gate would permit further review, never deployment'}

def run(archive,candidates,receipts,out,*,authorize=False):
    if authorize is not True:raise PermissionError('Explicit independent FP16 admission audit authorization required')
    dest=Path(out)
    if dest.exists():raise FileExistsError('No overwrite of prior admission evidence')
    if not isinstance(receipts,(tuple,list)) or len(receipts)!=2:raise ValueError('Two private source receipts required')
    paths=[Path(x) for x in receipts]
    if any(not p.is_file() or p.is_symlink() for p in paths):raise ValueError('Missing/symlinked private source receipts')
    data=[ood.prior.read_strict_json(p.read_text()) for p in paths]
    result=assess(data) # inexpensive structural validation before neural execution
    for p,d in zip(paths,data):
        independently=ood.verify(archive,candidates,p) # restore actual saved source+candidate weights and recompute
        if independently.get('independent_replay') is not True or independently.get('comparisons')!=33 or independently.get('seed')!=d['seed']:
            raise ValueError('Independent FP16 replay did not validate complete declared cohort')
    result['independently_replayed_from_saved_FP16']=True
    result=seal(result)
    verify_seal(result)
    with os.fdopen(os.open(dest,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:
        f.write(canonical(result)+b'\n');f.flush();os.fsync(f.fileno())
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    s=p.add_subparsers(dest='cmd',required=True)
    r=s.add_parser('audit');r.add_argument('--archive',required=True);r.add_argument('--candidates',required=True)
    r.add_argument('--receipt',action='append',required=True);r.add_argument('--out',required=True);r.add_argument('--authorize',action='store_true')
    v=s.add_parser('verify');v.add_argument('--receipt',required=True)
    a=vars(p.parse_args());op=a.pop('cmd')
    result=run(a['archive'],a['candidates'],a['receipt'],a['out'],authorize=a['authorize']) if op=='audit' else verify_seal(ood.prior.read_strict_json(Path(a['receipt']).read_text()))
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__':main()
