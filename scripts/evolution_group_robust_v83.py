"""Bounded Group-DRO-inspired optimizer and paired synthetic shift experiment.

Independent implementation of exponential group reweighting, not a reproduction
of Sagawa et al. (ICLR 2020) or a trained production model. No dependencies.
"""
import argparse
import json
import math
import random

SCHEMA = 'myriad.group_robust.v83'
ARMS = ('pooled', 'balanced', 'dro')
SIZES = (256, 64, 32, 16)
TEST_SIZE = 128
ETA = .2
LR = .025
L2 = .02


def number(x):
    return type(x) in (int, float) and math.isfinite(x)


def valid_logs(logs):
    if not isinstance(logs, (list, tuple)) or not 2 <= len(logs) <= 128 or any(not number(x) or not -1e12 <= x <= 0 for x in logs) or max(logs) != 0:
        raise ValueError('invalid normalized log group weights')


def probabilities(logs):
    valid_logs(logs)
    vals = [math.exp(x) for x in logs]
    total = math.fsum(vals)
    return [x/total for x in vals]


def update_log_weights(logs, losses, eta):
    valid_logs(logs)
    if not isinstance(losses, (list, tuple)) or len(losses) != len(logs) or any(not number(x) or not 0 <= x <= 1e6 for x in losses) or not number(eta) or not 0 < eta <= 1:
        raise ValueError('invalid group update')
    shifted = [a + eta*b for a,b in zip(logs,losses)]
    peak = max(shifted)
    out = [x-peak for x in shifted]
    valid_logs(out)
    return out


def group_data(seed, group, split, n):
    if type(seed) is not int or not 0 <= seed < 2**31 or type(group) is not int or not 0 <= group < 4 or split not in ('train','test') or type(n) is not int or not 1 <= n <= 4096:
        raise ValueError('invalid dataset bounds')
    rng = random.Random(8300000000 + seed*16 + group*2 + (split=='test'))
    # The target is generated from a latent cause. Feature 0 is a noisy causal
    # proxy; feature 1 is an environment-dependent, spurious correlate.
    # Test distributions differ from their matching training environments.
    corrs = (1.4, .8, -.8, -1.4) if split=='train' else (1.0, .2, -1.0, -1.8)
    rows=[]
    for _ in range(n):
        z=rng.gauss(0,1)
        y=z+rng.gauss(0,.12)
        a=z+rng.gauss(0,.55)
        b=corrs[group]*z+rng.gauss(0,.25)
        rows.append((a,b,y))
    return rows


def moments(rows):
    n=len(rows)
    return tuple(math.fsum(v)/n for v in zip(*((a*a,a*b,b*b,a*y,b*y,y*y) for a,b,y in rows)))


def mse(w,m):
    a,b=w;aa,ab,bb,ay,by,yy=m
    return max(0.,a*a*aa+2*a*b*ab+b*b*bb-2*a*ay-2*b*by+yy)


def gradient(w,m):
    a,b=w;aa,ab,bb,ay,by,_=m
    return (2*(a*aa+b*ab-ay),2*(a*ab+b*bb-by))


def experiment(seed, steps=160):
    if type(steps) is not int or not 1<=steps<=2048:raise ValueError('step budget')
    train=[moments(group_data(seed,g,'train',n)) for g,n in enumerate(SIZES)]
    test=[moments(group_data(seed,g,'test',TEST_SIZE)) for g in range(4)]
    init=random.Random(8400000000+seed)
    start=[init.uniform(-.1,.1),init.uniform(-.1,.1)]
    arms={}
    for arm in ARMS:
        w=start[:];logs=[0.]*4
        for _ in range(steps):
            if arm=='dro':
                logs=update_log_weights(logs,[mse(w,m) for m in train],ETA)
                q=probabilities(logs)
            elif arm=='balanced':q=[.25]*4
            else:q=[n/sum(SIZES) for n in SIZES]
            grads=[gradient(w,m) for m in train]
            w=[w[j]-LR*(math.fsum(q[k]*grads[k][j] for k in range(4))+2*L2*w[j]) for j in range(2)]
            if any(not number(x) for x in w):raise ValueError('nonfinite training state')
        scores=[mse(w,m) for m in test]
        arms[arm]={'steps':steps,'test_group_mse':scores,'worst_mse':max(scores),'mean_mse':math.fsum(scores)/4,'final_group_weights':q,'coefficients':w}
    return {'schema':SCHEMA,'seed':seed,'arms':arms,'production_authority':False,'semantic_mastery_certified':False}


def summarize(results):
    if not isinstance(results,list) or not 1<=len(results)<=128:raise ValueError('result bounds')
    seen=set();s={'seeds':len(results),'worst_vs_balanced':{'wins':0,'ties':0,'losses':0},'worst_vs_pooled':{'wins':0,'ties':0,'losses':0},'mean_worst_mse':{},'mean_group_mse':{},'production_authority':False,'semantic_mastery_certified':False}
    for r in results:
        if not isinstance(r,dict) or r.get('schema')!=SCHEMA or type(r.get('seed')) is not int or r['seed'] in seen or set(r.get('arms',{}))!=set(ARMS) or r.get('production_authority') is not False or r.get('semantic_mastery_certified') is not False:raise ValueError('invalid or duplicate result')
        seen.add(r['seed'])
        for arm in ARMS:
            a=r['arms'][arm];v=a['test_group_mse']
            if not isinstance(v,list) or len(v)!=4 or any(not number(x) or x<0 for x in v) or a['worst_mse']!=max(v) or a['mean_mse']!=math.fsum(v)/4:raise ValueError('invalid loss summary')
        for k in ('balanced','pooled'):
            a=r['arms']['dro']['worst_mse'];b=r['arms'][k]['worst_mse']
            s['worst_vs_'+k]['wins' if a<b else 'losses' if a>b else 'ties']+=1
    for arm in ARMS:
        s['mean_worst_mse'][arm]=math.fsum(r['arms'][arm]['worst_mse'] for r in results)/len(results)
        s['mean_group_mse'][arm]=math.fsum(r['arms'][arm]['mean_mse'] for r in results)/len(results)
    return s


def main():
    p=argparse.ArgumentParser();p.add_argument('--authorize',action='store_true');a=p.parse_args()
    if not a.authorize:raise PermissionError('explicit research authorization required')
    # Fixed, pre-result cohort: 12 independent seeds, 160 steps for each arm.
    rows=[experiment(seed) for seed in range(12)]
    print(json.dumps({'summary':summarize(rows),'results':rows},sort_keys=True,allow_nan=False))
if __name__=='__main__':main()
