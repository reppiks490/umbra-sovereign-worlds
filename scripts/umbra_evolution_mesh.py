#!/usr/bin/env python3
"""Bounded, research-only UMBRA evolution mesh. All scores are SYNTHETIC fixtures.

250k addressable parameterized experiment recipes and 195k logical workflow identities.
A logical identity is not a dedicated GitHub Actions workflow, model, or service.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import random
import sqlite3
from datetime import datetime, timezone

FAMILIES = ('signed-gradient','spsa','coordinate-search','random-direction','mirror-search')
OPTIMIZERS = ('sgd','momentum','rmsprop','adam','trust-region')
ASPECTS = ('resilience','fairness','efficiency','stability','safety','novelty','replicability','sustainability')
DOMAINS = ('ecology','civic','energy','economy','culture','health','governance','research','resilience','integrity','infrastructure','accessibility','education')
ALGORITHM_COUNT = 250_000
WORKFLOW_COUNT = 195_000
SCHEMA = 'umbra.evolution.mesh.v1'


def digest(obj):
    # Stable cross-language evidence canonicalization at published 12-decimal precision.
    # Numeric evidence is represented by its exact formatted decimal string.
    def normalized(value):
        if isinstance(value, bool) or value is None: return value
        if isinstance(value, (int, float)):
            if not math.isfinite(value): raise ValueError('nonfinite evidence')
            return format(value, '.12f')
        if isinstance(value, dict): return {k: normalized(v) for k, v in value.items()}
        if isinstance(value, (tuple, list)): return [normalized(x) for x in value]
        return value
    return hashlib.sha256(json.dumps(normalized(obj), sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def recipe(algorithm_id):
    if not isinstance(algorithm_id, int) or not 1 <= algorithm_id <= ALGORITHM_COUNT:
        raise ValueError('algorithm_id out of range')
    n = algorithm_id - 1
    family = n // 10_000  # five exploration policies x five parameter optimizers
    regime = (n % 10_000) // 100
    objective = n % 100
    return {'id': f'A{algorithm_id:06d}', 'family': FAMILIES[family % 5],
            'optimizer': OPTIMIZERS[family // 5], 'regime': regime,
            'objective': objective, 'synthetic_only': True}


def workflow(workflow_id):
    if not isinstance(workflow_id, int) or not 1 <= workflow_id <= WORKFLOW_COUNT:
        raise ValueError('workflow_id out of range')
    n = workflow_id - 1
    # Multiplication by a number coprime to 250,000 distributes primary recipes.
    algorithm_id = ((n * 73_117) % ALGORITHM_COUNT) + 1
    return {'id': f'E{workflow_id:06d}', 'index': workflow_id,
            'cohort': n % 195, 'domain': DOMAINS[n % len(DOMAINS)],
            'algorithm_id': algorithm_id, 'synthetic_only': True}


def seed_int(*parts):
    return int(hashlib.sha256('|'.join(map(str, parts)).encode()).hexdigest()[:16], 16)


def synthetic_scores(parameters, alg, fold):
    """Deliberately small *toy objective*, NOT the real UMBRA simulation."""
    rng = random.Random(seed_int('fixture-v1', alg['regime'], fold))
    target = [0.21 + 0.58 * rng.random() for _ in ASPECTS]
    return [max(0.0, 1.0 - 2.8 * (x - y)**2) for x, y in zip(parameters, target)]


def utility(parameters, alg, folds):
    # Each objective ID yields a distinct positive 8-aspect weight vector.
    weights = [1 + ((alg['objective'] * (i * 7 + 3) + 11 * i) % 17) for i in range(8)]
    total = float(sum(weights))
    rows = [synthetic_scores(parameters, alg, fold) for fold in folds]
    return sum(sum(w * m for w, m in zip(weights, scores)) / total for scores in rows) / len(rows)


def clamp(x):
    return min(1.0, max(0.0, x))


def explore(params, alg, fold, rng, step):
    family = alg['family']
    eps = .012
    if family == 'signed-gradient':
        gradient = [(utility(params[:i]+[clamp(params[i]+eps)]+params[i+1:], alg, (fold,)) -
                     utility(params[:i]+[clamp(params[i]-eps)]+params[i+1:], alg, (fold,))) / (2*eps)
                    for i in range(8)]
    elif family == 'spsa':
        direction = [rng.choice((-1, 1)) for _ in range(8)]
        plus = [clamp(x + eps*d) for x,d in zip(params,direction)]
        minus = [clamp(x - eps*d) for x,d in zip(params,direction)]
        coef = (utility(plus,alg,(fold,)) - utility(minus,alg,(fold,))) / (2*eps)
        gradient = [coef*d for d in direction]
    elif family == 'coordinate-search':
        gradient = [0.] * 8
        i = step % 8
        a = params.copy(); b = params.copy(); a[i] = clamp(a[i]+eps); b[i] = clamp(b[i]-eps)
        gradient[i] = (utility(a,alg,(fold,))-utility(b,alg,(fold,)))/(2*eps)
    elif family == 'random-direction':
        direction = [rng.gauss(0, 1) for _ in range(8)]
        mag = math.sqrt(sum(x*x for x in direction))
        direction = [x/mag for x in direction]
        a = [clamp(x+eps*d) for x,d in zip(params,direction)]
        b = [clamp(x-eps*d) for x,d in zip(params,direction)]
        coef = (utility(a,alg,(fold,))-utility(b,alg,(fold,)))/(2*eps)
        gradient = [coef*d for d in direction]
    else:  # mirrored perturbation with antithetic reward comparison
        direction = [rng.choice((-1., 1.)) for _ in range(8)]
        a = [clamp(x+eps*d) for x,d in zip(params,direction)]
        b = [clamp(x-eps*d) for x,d in zip(params,direction)]
        if utility(a,alg,(fold,)) >= utility(b,alg,(fold,)):
            gradient = direction
        else:
            gradient = [-d for d in direction]
    return gradient


def train(wf, *, hour, steps, peer=None):
    if not 1 <= steps <= 64:
        raise ValueError('steps must be 1..64')
    alg = recipe(wf['algorithm_id']); rng = random.Random(seed_int(wf['id'], hour, 'trainer'))
    original = [.5] * 8
    params = original.copy()
    if peer is not None:
        # Read-only, bounded peer proposal assimilation; never automatic promotion.
        assert len(peer) == 8 and all(math.isfinite(x) and 0 <= x <= 1 for x in peer)
        params = [clamp(.9*p + .1*q) for p,q in zip(params,peer)]
    moment = [0.] * 8; second = [0.] * 8
    train_folds = tuple(f'train-{i}' for i in range(4))
    heldout_folds = ('heldout-a','heldout-b')
    shift_folds = ('shift-scarcity','shift-perturbation')
    for step in range(steps):
        gradient = explore(params, alg, train_folds[step % 4], rng, step)
        for i,g in enumerate(gradient):
            moment[i] = .9*moment[i] + .1*g
            second[i] = .99*second[i] + .01*g*g
            if alg['optimizer'] == 'sgd': change = .08*g
            elif alg['optimizer'] == 'momentum': change = .11*moment[i]
            elif alg['optimizer'] == 'rmsprop': change = .018*g/(math.sqrt(second[i])+.05)
            elif alg['optimizer'] == 'adam': change = .012*(moment[i]/(1-.9**(step+1)))/(math.sqrt(second[i]/(1-.99**(step+1)))+.02)
            else: change = max(-.018,min(.018,.06*g))
            params[i] = clamp(params[i]+change)
    baselines = {name: utility(original,alg,folds) for name,folds in
                 [('train',train_folds),('holdout',heldout_folds),('stress',shift_folds)]}
    results = {name: utility(params,alg,folds) for name,folds in
               [('train',train_folds),('holdout',heldout_folds),('stress',shift_folds)]}
    deltas = {k: round(results[k]-baselines[k], 9) for k in baselines}
    # Strong acceptance: do not promote based on in-sample gains alone.
    accepted = all(deltas[k] > .0001 for k in ('holdout','stress'))
    proposal = {'schema': SCHEMA, 'workflow': wf['id'], 'hour': hour, 'domain': wf['domain'],
                'algorithm': alg, 'steps': steps, 'parameters': [round(x,8) for x in params],
                'baseline': baselines, 'measured': results, 'delta': deltas,
                'review_status': 'candidate_for_manual_review' if accepted else 'rejected_synthetic',
                'novelty_claim': False, 'deployment_authorized': False,
                'real_model_weight_training': False, 'umbra_engine_run': False,
                'proposal_type': ('experiment','simulation_setting','test','scenario','policy_hypothesis')[wf['index'] % 5]}
    proposal['receipt_sha256'] = digest(proposal)
    return proposal


def connect(path):
    db = sqlite3.connect(str(path), timeout=30)
    db.execute('PRAGMA busy_timeout = 30000')
    db.execute('PRAGMA journal_mode = WAL')
    db.execute('CREATE TABLE IF NOT EXISTS runs(hour TEXT NOT NULL,workflow TEXT NOT NULL,domain TEXT NOT NULL,receipt TEXT NOT NULL,record TEXT NOT NULL,PRIMARY KEY(hour,workflow))')
    db.execute('CREATE INDEX IF NOT EXISTS ix_runs_domain_hour ON runs(domain,hour)')
    return db


def peer_for(db, wf, hour):
    # Only a *previously recorded* and explicitly unpromoted peer record can be used.
    # Strict earlier-hour selection: same-hour worker completion order is not
    # an independent validation signal. Never copy rejected peer candidates.
    rows = db.execute('SELECT record FROM runs WHERE domain=? AND workflow!=? AND hour<? ORDER BY hour DESC, workflow LIMIT 32',
                     (wf['domain'],wf['id'],hour)).fetchall()
    for (raw,) in rows:
        item=json.loads(raw)
        h=item.get('receipt_sha256')
        if not isinstance(h,str) or digest({k:v for k,v in item.items() if k!='receipt_sha256'})!=h:
            raise ValueError('tampered peer evidence')
        if item.get('domain')!=wf['domain'] or item.get('hour','')>=hour:
            raise ValueError('forged peer provenance')
        if item.get('deployment_authorized') or item.get('real_model_weight_training'):
            raise ValueError('untrusted peer authority')
        if item.get('review_status')!='candidate_for_manual_review':continue
        params=item.get('parameters')
        if not isinstance(params,list) or len(params)!=8 or any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1 for v in params):
            raise ValueError('invalid peer weights')
        # Hashes alone are self-attested. Recompute the actual heldout/stress
        # qualification before assimilating any candidate's parameters.
        peer_workflow=item.get('workflow','')
        if not isinstance(peer_workflow,str) or not peer_workflow.startswith('E') or not peer_workflow[1:].isdigit():
            raise ValueError('forged peer identity')
        try:expected_workflow=workflow(int(peer_workflow[1:]))
        except ValueError:raise ValueError('unregistered peer identity') from None
        expected_algorithm=recipe(expected_workflow['algorithm_id'])
        if expected_workflow['domain']!=wf['domain'] or item.get('algorithm')!=expected_algorithm:
            raise ValueError('forged peer method/domain')
        for metric,folds in [('holdout',('heldout-a','heldout-b')),
                             ('stress',('shift-scarcity','shift-perturbation'))]:
            raw=round(utility(params,expected_algorithm,folds)-utility([.5]*8,expected_algorithm,folds),9)
            recorded=item.get('delta',{}).get(metric)
            if not isinstance(recorded,(int,float)) or not math.isfinite(recorded) or abs(raw-recorded)>2e-7 or raw<=.0001:
                raise ValueError('forged peer qualification')
        return params
    return None


def run_batch(args):
    hour = args.hour
    logical_hour = datetime.strptime(hour, '%Y-%m-%dT%H')
    if args.shards < 1 or args.shards > 4096 or not 0 <= args.shard < args.shards:
        raise ValueError('invalid shard configuration')
    if not 1 <= args.limit <= 1000:
        raise ValueError('limit must be 1..1000')
    out = Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    db = connect(args.ledger)
    count=0; accepted=0; duplicates=0
    # Deterministic, complete disjoint partition across shard IDs.
    indexes = range(1+args.shard, WORKFLOW_COUNT+1, args.shards)
    # Rotate starting position each hour to avoid permanent starvation of later IDs.
    # This is partial coverage, NOT an hourly full-fleet execution guarantee.
    hour_number = int(logical_hour.replace(tzinfo=timezone.utc).timestamp() // 3600)
    start_offset = (hour_number * args.limit) % len(indexes)
    with out.open('w', encoding='utf-8') as stream:
        for step_index in range(len(indexes)):
            index = indexes[(start_offset + step_index) % len(indexes)]
            if count >= args.limit: break
            wf = workflow(index)
            if db.execute('SELECT 1 FROM runs WHERE hour=? AND workflow=?',(hour,wf['id'])).fetchone():
                duplicates += 1; continue
            peer = peer_for(db, wf, hour)
            record = train(wf,hour=hour,steps=args.steps,peer=peer)
            record['peer_used'] = peer is not None
            # Peer metadata is in the final receipt, with digest recomputed.
            record.pop('receipt_sha256')
            record['receipt_sha256'] = digest(record)
            try:
                with db:
                    db.execute('INSERT INTO runs(hour,workflow,domain,receipt,record) VALUES(?,?,?,?,?)',
                               (hour,wf['id'],wf['domain'],record['receipt_sha256'],json.dumps(record,sort_keys=True)))
            except sqlite3.IntegrityError:
                duplicates += 1;continue
            stream.write(json.dumps(record,sort_keys=True)+'\n')
            count += 1; accepted += record['review_status']=='candidate_for_manual_review'
    db.close()
    return {'schema':SCHEMA,'hour':hour,'shard':args.shard,'shards':args.shards,
            'processed':count,'duplicate_ids_skipped':duplicates,'synthetic_review_candidates':accepted,
            'eligible_identities':len(indexes),
            'capacity_deferred':max(0,len(indexes)-count-duplicates),
            'autonomous_code_changes':0,'real_model_training_runs':0,'real_world_success_claims':0,
            'per_hour_full_fleet_certified':False}


def validate_space(full=False):
    # Analytically exact space; optional exhaustive enumeration catches collisions.
    assert 5*5*100*100 == ALGORITHM_COUNT
    assert 195*1000 == WORKFLOW_COUNT
    if full:
        observed = set()
        for aid in range(1,ALGORITHM_COUNT+1):
            r=recipe(aid)
            key=(r['family'],r['optimizer'],r['regime'],r['objective'])
            if key in observed: raise AssertionError('duplicate algorithm configuration')
            observed.add(key)
        if len(observed)!=ALGORITHM_COUNT: raise AssertionError('incomplete algorithm space')
        for wid in range(1,WORKFLOW_COUNT+1):
            w=workflow(wid)
            if w['index']!=wid or not 1<=w['algorithm_id']<=ALGORITHM_COUNT:
                raise AssertionError('bad workflow mapping')
    return {'algorithm_specs':ALGORITHM_COUNT,'strategy_recipes':25,'distinct_optimizer_types':5,
            'logical_workflow_identities':WORKFLOW_COUNT,'trained_agents':0,'live_hourly_workers':0,
            'independently_validated_new_algorithms':0,'full_enumeration_checked':full,
            'release_status':'RESEARCH_ONLY_UNQUALIFIED'}


def main():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='command',required=True)
    v=sub.add_parser('validate'); v.add_argument('--full',action='store_true')
    a=sub.add_parser('algorithm');a.add_argument('id',type=int)
    w=sub.add_parser('workflow');w.add_argument('id',type=int)
    t=sub.add_parser('tick')
    t.add_argument('--hour',required=True,help='UTC or agreed logical hour YYYY-MM-DDTHH')
    t.add_argument('--shards',type=int,default=256); t.add_argument('--shard',type=int,default=0)
    t.add_argument('--limit',type=int,default=8);t.add_argument('--steps',type=int,default=8)
    t.add_argument('--ledger',default='evolution-mesh.sqlite3');t.add_argument('--output',default='evolution-evidence.jsonl')
    args=p.parse_args()
    if args.command=='validate': result=validate_space(args.full)
    elif args.command=='algorithm': result=recipe(args.id)
    elif args.command=='workflow': result=workflow(args.id)
    else: result=run_batch(args)
    print(json.dumps(result,sort_keys=True,indent=2))


if __name__=='__main__':
    main()
