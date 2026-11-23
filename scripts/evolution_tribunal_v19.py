#!/usr/bin/env python3
"""Independent read-only auditor and source-traced research collaboration tribunal.

Checks evidence receipts AND replays synthetic held-out/stress scores. Creates
quarantined collaboration hypotheses from already verified records, never direct
code changes, neural weight promotions, or independent claims of market success.
The independent evaluation shares a synthetic objective definition: it is a
reproducible consistency audit, NOT independently collected scientific evidence.
"""
from __future__ import annotations
import argparse, hashlib, json, math, random, re, sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path
import umbra_evolution_mesh as mesh

REQUIRED={'schema','workflow','hour','domain','algorithm','parameters','steps','baseline','measured','delta',
          'review_status','deployment_authorized','real_model_weight_training','umbra_engine_run',
          'proposal_type','receipt_sha256'}
METRICS={'train':('train-0','train-1','train-2','train-3'),
         'holdout':('heldout-a','heldout-b'),
         'stress':('shift-scarcity','shift-perturbation')}


def verify_record(obj):
    """Fail-closed schema, agent identity, authority and numerical replay audit."""
    if not isinstance(obj,dict) or not REQUIRED.issubset(obj):raise ValueError('Missing evidence keys')
    if obj['schema']!=mesh.SCHEMA:raise ValueError('Unqualified evidence schema')
    if not isinstance(obj['workflow'],str) or not re.fullmatch(r'E\d{6}',obj['workflow']):
        raise ValueError('Noncanonical workflow ID')
    wid=int(obj['workflow'][1:]);wf=mesh.workflow(wid)
    if obj['workflow']!=wf['id'] or obj['domain']!=wf['domain']:
        raise ValueError('Mismatched workflow ownership')
    if obj['algorithm']!=mesh.recipe(wf['algorithm_id']):
        raise ValueError('False algorithm identity')
    try:datetime.strptime(obj['hour'],'%Y-%m-%dT%H')
    except (ValueError,TypeError) as e:raise ValueError('Unqualified logical time') from e
    if type(obj['steps']) is not int or not 1<=obj['steps']<=1000:
        raise ValueError('Unqualified training step count')
    if obj['deployment_authorized'] is not False or obj['real_model_weight_training'] is not False or obj['umbra_engine_run'] is not False:
        raise ValueError('Authority escalation / misreported external work')
    if obj.get('novelty_claim',False) is not False:raise ValueError('Unsupported novelty claim')
    if obj['review_status'] not in ('candidate_for_manual_review','rejected_synthetic'):
        raise ValueError('Invalid review status')
    params=obj['parameters']
    if not isinstance(params,list) or len(params)!=8 or any(type(x) not in (int,float) or not math.isfinite(x) or x<0 or x>1 for x in params):
        raise ValueError('Nonfinite or out-of-range parameters')
    sha=obj['receipt_sha256']
    if not isinstance(sha,str) or not re.fullmatch(r'[0-9a-f]{64}',sha):raise ValueError('Invalid receipt hash')
    unsigned={k:v for k,v in obj.items() if k!='receipt_sha256'}
    if mesh.digest(unsigned)!=sha:raise ValueError('Corrupted receipt signature')
    baseline=[.5]*8;errors=[];replayed={}
    for key,folds in METRICS.items():
        raw0=mesh.utility(baseline,obj['algorithm'],folds)
        raw1=mesh.utility(params,obj['algorithm'],folds)
        for field,value in [('baseline',raw0),('measured',raw1),('delta',round(raw1-raw0,9))]:
            got=obj[field].get(key) if isinstance(obj[field],dict) else None
            if type(got) not in (int,float) or not math.isfinite(got) or abs(got-value)>2e-7:
                errors.append(f'{key}/{field}')
        replayed[key]=round(raw1-raw0,9)
    if errors:raise ValueError('Independent synthetic replay mismatch '+','.join(errors))
    would_pass=all(replayed[k]>.0001 for k in ('holdout','stress'))
    if would_pass!=(obj['review_status']=='candidate_for_manual_review'):
        raise ValueError('Forged review decision')
    return {'workflow':obj['workflow'],'hour':obj['hour'],'domain':obj['domain'],
            'source_receipt_sha256':sha,'replay_passed':True,
            'heldout_delta':replayed['holdout'],'stress_delta':replayed['stress'],
            'review_state':'quarantined' if would_pass else 'rejected',
            'evidence_class':'synthetic_replay_only','independent_real_world_certification':False}


def audit(path,*,sample=1024,seed=20261123,row_start=None,row_end=None):
    if not 1<=sample<=195000:raise ValueError('Unsupported audit sample')
    if (row_start is None)!=(row_end is None):raise ValueError('Both range endpoints are required')
    if row_start is not None and not 1<=row_start<=row_end<=195000:raise ValueError('Invalid audit row span')
    p=Path(path)
    with sqlite3.connect(f'file:{p}?mode=ro',uri=True) as db:
        n,maximum=db.execute('SELECT COUNT(*), MAX(rowid) FROM runs').fetchone()
        if row_start is None and n < sample:raise ValueError('Not enough actual stored results')
        if row_start is not None and row_end>maximum:raise ValueError('Requested rows not present')
        # Fully exhaustive mode uses the existing database index in bounded chunks.
        chosen=(range(row_start,row_end+1) if row_start is not None else
                range(1,maximum+1) if sample==n else
                sorted(random.Random(seed).sample(range(1,maximum+1),sample)))
        tally=Counter();valid=[];bad=[]
        for i in range(0,len(chosen),600):
            batch=chosen[i:i+600]
            slots=','.join('?' for _ in batch)
            rows=db.execute(f'SELECT rowid,hour,workflow,domain,receipt,record FROM runs WHERE rowid IN ({slots})',tuple(batch)).fetchall()
            if len(rows)!=len(batch):raise ValueError('Missing numbered research evidence')
            for rowid,hour,wid,domain,receipt,record in rows:
                try:
                    obj=json.loads(record)
                    if (obj.get('hour'),obj.get('workflow'),obj.get('domain'),obj.get('receipt_sha256'))!=(hour,wid,domain,receipt):
                        raise ValueError('Ledger metadata/receipt mismatch')
                    reviewed=verify_record(obj)
                    valid.append((rowid,reviewed['source_receipt_sha256']))
                    tally[reviewed['review_state']]+=1
                    tally[domain]+=1
                except (ValueError,KeyError,TypeError,json.JSONDecodeError) as e:
                    bad.append({'rowid':rowid,'kind':type(e).__name__,'reason':str(e)[:120]})
    out={'schema':'umbra.evolution.independent_tribunal.v1',
         'requested':len(chosen),'inspected':len(valid)+len(bad),'passed':len(valid),'failed':len(bad),
         'selection':('contiguous_range' if row_start is not None else 'all' if sample==n else 'deterministic_random_sample'),
         'range_start':row_start,'range_end':row_end,
         'quarantined_candidates':tally['quarantined'],'rejected_candidates':tally['rejected'],
         'domains_covered':len(set(tally).intersection(mesh.DOMAINS)),
         'negative_findings':bad[:25],'seed':seed,
         'source_replay':'deterministic_synthetic_no_external_oracle',
         'verified_receipt_set_sha256':hashlib.sha256(json.dumps(sorted(valid),separators=(',',':')).encode()).hexdigest(),
         'production_merges':0,'full_neural_bank_training_certified':False}
    out['report_sha256']=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return out


def combine_reports(paths,expected_count=195000):
    """Combine disjoint fully verified ranges; never turn sampled reports into full coverage."""
    docs=[]
    for p in paths:
        obj=json.loads(Path(p).read_text())
        digest=obj.get('report_sha256')
        clean={k:v for k,v in obj.items() if k!='report_sha256'}
        if digest!=hashlib.sha256(json.dumps(clean,sort_keys=True,separators=(',',':')).encode()).hexdigest():
            raise ValueError('Tampered tribunal segment')
        if obj.get('selection')!='contiguous_range' or obj['failed']!=0 or obj['passed']!=obj['requested']:
            raise ValueError('Unqualified or sampled tribunal segment')
        docs.append(obj)
    docs.sort(key=lambda d:d['range_start'])
    end=0
    for obj in docs:
        if obj['range_start']!=end+1 or obj['requested']!=obj['range_end']-obj['range_start']+1:
            raise ValueError('Missing or overlapping coverage')
        end=obj['range_end']
    if end!=expected_count:raise ValueError('Incomplete 195k evidence scan')
    out={'schema':'umbra.evolution.tribunal.aggregate.v1',
         'independently_verified_receipt_records':sum(x['passed'] for x in docs),
         'covered_rowids':[1,end], 'segments':len(docs),
         'quarantined_candidates':sum(x['quarantined_candidates'] for x in docs),
         'rejected_candidates':sum(x['rejected_candidates'] for x in docs),
         'synthetic_only':True,'actual_neural_gradient_training':0,'production_integrations':0,
         'subreport_hashes':[x['report_sha256'] for x in docs]}
    out['report_sha256']=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return out

def find_collaborators(db,requester,logical_hour,*,limit=3):
    """Only prior-hour, distinct-domain verified peers can contribute evidence."""
    if not 1<=limit<=10:raise ValueError('Unsupported cross-domain fanout')
    requester=mesh.workflow(requester)
    if not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d',logical_hour):raise ValueError('Invalid target hour')
    available=[]
    for domain in mesh.DOMAINS:
        if domain==requester['domain']:continue
        # Inspect a bounded recent candidate window. The newest peer may have
        # failed the heldout gate; do not mistake that for an empty domain.
        rows=db.execute('SELECT record FROM runs WHERE domain=? AND hour<? ORDER BY hour DESC, workflow LIMIT 16',
                        (domain,logical_hour)).fetchall()
        for (raw,) in rows:
            obj=json.loads(raw);review=verify_record(obj)  # Tampering fails closed.
            if review['review_state']!='quarantined':continue
            # Pure evidence link only, no applying another domain's parameters.
            available.append({'source_workflow':obj['workflow'],'domain':domain,
                              'parent_receipt_sha256':obj['receipt_sha256'],
                              'hour':obj['hour'],'evidence':review['evidence_class'],
                              'cross_domain_only':True})
            break
    available.sort(key=lambda x:(x['domain'],x['source_workflow']))
    return available[:limit]


def collaboration(db_path,requester_id,logical_hour,*,limit=3):
    with sqlite3.connect(f'file:{Path(db_path)}?mode=ro',uri=True) as db:
        peers=find_collaborators(db,requester_id,logical_hour,limit=limit)
    obj={'schema':'umbra.evolution.collaboration.v1','requester':mesh.workflow(requester_id)['id'],
         'hour':logical_hour,'verified_cross_domain_peers':peers,
         'proposal':'cross-domain synthetic evidence comparison',
         'auto_integrate':False,'learning_weight_updates':0,
         'peer_support_is_not_independent_real_world_validation':True}
    obj['receipt_sha256']=hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return obj


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('audit');a.add_argument('--ledger',required=True);a.add_argument('--sample',type=int,default=1024)
    a.add_argument('--seed',type=int,default=20261123);a.add_argument('--start-rowid',type=int);a.add_argument('--end-rowid',type=int);a.add_argument('--output')
    g=sub.add_parser('aggregate');g.add_argument('--reports',nargs='+',required=True);g.add_argument('--output')
    c=sub.add_parser('collaborate');c.add_argument('--ledger',required=True);c.add_argument('--id',type=int,required=True)
    c.add_argument('--hour',required=True);c.add_argument('--limit',type=int,default=3);c.add_argument('--output')
    args=p.parse_args()
    data=(audit(args.ledger,sample=args.sample,seed=args.seed,row_start=args.start_rowid,row_end=args.end_rowid) if args.command=='audit'
          else combine_reports(args.reports) if args.command=='aggregate'
          else collaboration(args.ledger,args.id,args.hour,limit=args.limit))
    if args.output:
        dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('x') as stream:json.dump(data,stream,sort_keys=True,indent=2)
    print(json.dumps(data,sort_keys=True,indent=2))

if __name__=='__main__':main()
