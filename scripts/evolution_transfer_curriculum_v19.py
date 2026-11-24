#!/usr/bin/env python3
"""Tripartite optimizer transfer evaluation: train, correlated holdout, hard shift.

All tasks are synthetic mathematical functions. Never extrapolate to market data,
real capabilities, autonomous LLMs, or trained neural weights.
"""
import argparse,hashlib,json
from pathlib import Path
from statistics import median
import evolution_algorithms_v19 as lab


def run(*,budgets=(64,128,256),seeds=10,dimension=6):
    if not 1<=seeds<=100 or not 1<=dimension<=20:raise ValueError('Unsupported curriculum size')
    if not budgets or any(b<16 or b>10000 for b in budgets):raise ValueError('Budget bound')
    trials=[]
    for budget in budgets:
        for method in lab.METHODS:
            for name in lab.TASKS:
                for i in range(seeds):
                    train=lab.task(name,dimension,seed=1000+i,structure='shared')
                    correlated=lab.task(name,dimension,seed=7000+i,structure='shared')
                    shifted=lab.task(name,dimension,seed=8000+i,structure='independent')
                    result=lab.optimize(method,train,dimension=dimension,budget=budget,seed=42+i)
                    center=tuple([.5]*dimension)
                    delta=lambda fn:round(fn(result.best)-fn(center),8)
                    trials.append({'method':method,'task':name,'budget':budget,'seed':i,
                                   'evaluations':result.evaluations,'train_delta':delta(train),
                                   'correlated_holdout_delta':delta(correlated),
                                   'unrelated_shift_delta':delta(shifted),
                                   'receipt':lab.stable_hash(result.__dict__)})
    summary={}
    for method in lab.METHODS:
        own=[x for x in trials if x['method']==method]
        summary[method]={k:round(median(x[k] for x in own),8) for k in ('train_delta','correlated_holdout_delta','unrelated_shift_delta')}
    out={'schema':'umbra.evolution.transfer.curriculum.v19',
         'total_trials':len(trials),'source_algorithms':len(lab.METHODS),
         'correlated_target_protocol':'shared synthetic latent target + gaussian seed noise',
         'unrelated_shift_protocol':'independently sampled synthetic target, deliberately harder',
         'train_holdout_seed_separation':True,
         'results':trials,'method_medians':summary,
         'real_model_weight_updates':0,'real_world_validation':False,'production_integrations':0}
    out['sha256']=lab.stable_hash(out)
    return out


def main():
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=10)
    p.add_argument('--budgets',type=int,nargs='+',default=[64,128,256]);p.add_argument('--output',required=True)
    a=p.parse_args();out=run(budgets=a.budgets,seeds=a.seeds)
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(out,f,indent=2,sort_keys=True)
    print(json.dumps({'total_trials':out['total_trials'],'sha256':out['sha256'],
      'correlated_holdout_positive_methods':sum(x['correlated_holdout_delta']>0 for x in out['method_medians'].values()),
      'shifted_holdout_positive_methods':sum(x['unrelated_shift_delta']>0 for x in out['method_medians'].values())}))

if __name__=='__main__':main()
