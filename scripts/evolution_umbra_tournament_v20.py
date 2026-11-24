#!/usr/bin/env python3
"""Qualify seven new optimizer variants through the existing independent UMBRA v5 bridge.

The objective inside this module remains an explicitly synthetic fixture. The
actual UMBRA worldlines are evaluated ONLY after proposals are sealed, by the
separate JS simulator. No auto-promotion, Icarus integration or live trading.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

import evolution_algorithms_v20 as v20
import umbra_evolution_mesh as mesh


def seed_for(*parts):
    return int(hashlib.sha256('|'.join(map(str,parts)).encode()).hexdigest()[:15],16)


def proposal(workflow_id, *, hour='2026-11-23T20', budget=48):
    wf=mesh.workflow(workflow_id)
    alg=mesh.recipe(wf['algorithm_id'])
    method=v20.METHODS_V20[(workflow_id-1)%len(v20.METHODS_V20)]
    before=[.5]*8
    folds={'train':('train-0','train-1','train-2','train-3'),
           'holdout':('heldout-a','heldout-b'),
           'stress':('shift-scarcity','shift-perturbation')}
    fn=lambda x:mesh.utility(x,alg,folds['train'])
    result=v20.optimize_v20(method,fn,dimension=8,budget=budget,seed=seed_for(wf['id'],hour,'v20'))
    after=list(result.best)
    baseline={k:mesh.utility(before,alg,f) for k,f in folds.items()}
    measured={k:mesh.utility(after,alg,f) for k,f in folds.items()}
    deltas={k:round(measured[k]-baseline[k],9) for k in folds}
    selected=all(deltas[k]>.0001 for k in ('holdout','stress'))
    receipt={'schema':mesh.SCHEMA,'workflow':wf['id'],'hour':hour,'domain':wf['domain'],
             'algorithm':alg,'steps':result.evaluations,
             'parameters':[round(x,8) for x in after],
             'baseline':baseline,'measured':measured,'delta':deltas,
             'review_status':'candidate_for_manual_review' if selected else 'rejected_synthetic',
             'novelty_claim':False,'deployment_authorized':False,'real_model_weight_training':False,
             'umbra_engine_run':False,'proposal_type':'v20_sealed_independent_optimizer_candidate',
             'optimizer_evidence_v20':{'method':method,'source_reference':v20.REFERENCES[method],
                 'budget':budget,'evaluations':result.evaluations,
                 'optimizer_receipt_sha256':v20.stable_hash(result.__dict__),
                 'training_is_synthetic_fixture_only':True,
                 'real_umbra_engine_training':False,'source_code_copied':False,
                 'real_world_performance_certified':False,'cross_repo_merge_authorized':False}}
    receipt['receipt_sha256']=mesh.digest(receipt)
    return receipt


def batch(*,start=1,count=7,budget=48,hour='2026-11-23T20'):
    if not 1<=start<=mesh.WORKFLOW_COUNT or not 1<=count<=32 or start+count-1>mesh.WORKFLOW_COUNT:
        raise ValueError('Unbounded or invalid worker request')
    if not 16<=budget<=128:raise ValueError('Invalid objective-evaluation budget')
    return [proposal(i,hour=hour,budget=budget) for i in range(start,start+count)]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--start',type=int,default=1);p.add_argument('--count',type=int,default=7)
    p.add_argument('--budget',type=int,default=48)
    p.add_argument('--hour',default='2026-11-23T20');p.add_argument('--output',required=True)
    a=p.parse_args();cases=batch(start=a.start,count=a.count,budget=a.budget,hour=a.hour)
    target=Path(a.output);target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('x') as f:
        for case in cases:f.write(json.dumps(case,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'proposals':len(cases),'distinct_methods':len(set(x['optimizer_evidence_v20']['method'] for x in cases)),
                      'quarantined':sum(x['review_status']=='candidate_for_manual_review' for x in cases),
                      'production_integrations':0,'actual_neural_training':0,'output':str(target)}))

if __name__=='__main__':main()
