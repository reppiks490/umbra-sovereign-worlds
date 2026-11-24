#!/usr/bin/env python3
"""Create cryptographically checkable candidate research proposals from 12 methods.

The proposals are intentionally backward compatible with UMBRA v5's existing
read-only simulation bridge. The optimizer trains on a private synthetic
objective and simulator evaluation is performed separately by Node. There is
no model-weight training, live trading, or repository modification here.
"""
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path
import evolution_algorithms_v19 as algorithms
import umbra_evolution_mesh as mesh


def proposal(workflow_id: int, *, hour='2026-11-23T19', budget=96, seed=0):
    wf=mesh.workflow(workflow_id)
    alg=mesh.recipe(wf['algorithm_id'])
    method=algorithms.METHODS[(workflow_id-1) % len(algorithms.METHODS)]
    # Keep training labels separated from a frozen holdout and shifted stress set.
    training=('train-0','train-1','train-2','train-3')
    holdout=('heldout-a','heldout-b')
    stress=('shift-scarcity','shift-perturbation')
    fn=lambda x: mesh.utility(x,alg,training)
    result=algorithms.optimize(method,fn,dimension=8,budget=budget,seed=algorithms_seed(wf['id'],hour,seed))
    before=[.5]*8
    after=list(result.best)
    baseline={k:mesh.utility(before,alg,folds) for k,folds in [('train',training),('holdout',holdout),('stress',stress)]}
    measured={k:mesh.utility(after,alg,folds) for k,folds in [('train',training),('holdout',holdout),('stress',stress)]}
    deltas={k:round(measured[k]-baseline[k],9) for k in baseline}
    accepted=all(deltas[k]>.0001 for k in ('holdout','stress'))
    receipt={
        'schema':mesh.SCHEMA,'workflow':wf['id'],'hour':hour,'domain':wf['domain'],
        'algorithm':alg,'steps':result.evaluations,'parameters':[round(x,8) for x in after],
        'baseline':baseline,'measured':measured,'delta':deltas,
        'review_status':'candidate_for_manual_review' if accepted else 'rejected_synthetic',
        'novelty_claim':False,'deployment_authorized':False,'real_model_weight_training':False,
        'umbra_engine_run':False,'proposal_type':'independently_implemented_optimizer_candidate',
        'optimizer_evidence_v19':{'method':method,'source_reference':algorithms.REFERENCE[method],
            'evaluations':result.evaluations,'budget':budget,'recovered_large_weight_banks':False,
            'source_code_copied':False,'trained_on_real_umbra_engine':False,
            'heldout_outcomes_disclosed':True,'training_protocol':'synthetic_fixture_only',
            'algorithm_receipt':algorithms.stable_hash(result.__dict__)}
    }
    receipt['receipt_sha256']=mesh.digest(receipt)
    return receipt


def algorithms_seed(*parts):
    return int(hashlib.sha256('|'.join(map(str,parts)).encode()).hexdigest()[:15],16)


def batch(*,start=1,count=12,budget=96,hour='2026-11-23T19'):
    if not 1<=start<=mesh.WORKFLOW_COUNT or not 1<=count<=500 or start+count-1>mesh.WORKFLOW_COUNT:
        raise ValueError('Invalid bounded workflow range')
    if not 8<=budget<=1000:raise ValueError('Unapproved optimizer budget')
    return [proposal(i,hour=hour,budget=budget) for i in range(start,start+count)]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--start',type=int,default=1)
    p.add_argument('--count',type=int,default=12)
    p.add_argument('--budget',type=int,default=96)
    p.add_argument('--hour',default='2026-11-23T19')
    p.add_argument('--output',required=True)
    a=p.parse_args()
    dest=Path(a.output)
    if dest.exists():raise FileExistsError('Refuse to overwrite existing research evidence')
    result=batch(start=a.start,count=a.count,budget=a.budget,hour=a.hour)
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('x') as fp:
        for item in result:fp.write(json.dumps(item,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'proposals':len(result),'real_model_training':0,
                      'algorithms':len({x['optimizer_evidence_v19']['method'] for x in result}),
                      'candidates_for_review':sum(x['review_status']=='candidate_for_manual_review' for x in result),
                      'evidence_file':str(dest)}))

if __name__=='__main__':main()
