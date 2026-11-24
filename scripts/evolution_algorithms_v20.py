#!/usr/bin/env python3
"""Seven new, independently implemented bounded research optimizers.

Methods use reproducible seeds and an exactly metered objective evaluator.
The methods are familiar public algorithms with original implementations,
not discoveries of new mathematical algorithms. No live market execution or
model-weight updates. The code itself is not a trained model.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import random
from pathlib import Path

from evolution_algorithms_v19 import Evaluator, Result, TASKS, bounded, task, stable_hash

METHODS_V20=(
 'halton-qmc',
 'inverse-bfgs',
 'rank-mu-covariance-es',
 'gaussian-process-ei',
 'artificial-bee-colony',
 'harmony-search',
 'ucb-operator-bandit',
)
REFERENCES={
 'halton-qmc':'https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.qmc.Halton.html',
 'inverse-bfgs':'https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html',
 'rank-mu-covariance-es':'https://github.com/CMA-ES/pycma',
 'gaussian-process-ei':'https://github.com/bayesian-optimization/BayesianOptimization',
 'artificial-bee-colony':'https://github.com/DEAP/deap',
 'harmony-search':'https://github.com/DEAP/deap',
 'ucb-operator-bandit':'https://github.com/facebookresearch/nevergrad',
}
PRIMES=(2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53)

def dot(x,y):return sum(a*b for a,b in zip(x,y))
def ident(d):return [[1.0 if i==j else 0.0 for j in range(d)] for i in range(d)]
def mv(a,x):return [dot(row,x) for row in a]
def halton(n,b):
    f=1.;v=0.
    while n:
        f/=b;v+=f*(n%b);n//=b
    return v

def chol(a):
    n=len(a);L=[[0.]*n for _ in range(n)]
    for i in range(n):
        for j in range(i+1):
            s=a[i][j]-sum(L[i][k]*L[j][k] for k in range(j))
            if i==j:
                if s<=1e-11:raise ValueError('Kernel or covariance not positive definite')
                L[i][j]=math.sqrt(s)
            else:L[i][j]=s/L[j][j]
    return L

def triangular_solve(L,b):
    n=len(b);y=[0.]*n
    for i in range(n):y[i]=(b[i]-sum(L[i][j]*y[j] for j in range(i)))/L[i][i]
    x=[0.]*n
    for i in range(n-1,-1,-1):x[i]=(y[i]-sum(L[j][i]*x[j] for j in range(i+1,n)))/L[i][i]
    return x

def gp_predict(points,scores,x,L,alpha,length=.3):
    def kernel(a,b):return math.exp(-sum((u-v)**2 for u,v in zip(a,b))/(2*length*length))
    k=[kernel(p,x) for p in points]
    mu=dot(k,alpha)
    v=[]
    for i in range(len(k)):v.append((k[i]-sum(L[i][j]*v[j] for j in range(i)))/L[i][i])
    variance=max(1e-12,1.-dot(v,v))
    return mu,math.sqrt(variance)

def optimize_v20(method, fn, *, dimension=6, budget=96, seed=73):
    if method not in METHODS_V20:raise ValueError('Unknown v2.0 independent algorithm')
    if isinstance(dimension,bool) or not isinstance(dimension,int) or not 1<=dimension<=16:
        raise ValueError('Dimension must be 1..16')
    if isinstance(budget,bool) or not isinstance(budget,int) or not 16<=budget<=256:
        raise ValueError('Bounded evaluation budget must be 16..256')
    if isinstance(seed,bool) or not isinstance(seed,int) or not 0<=seed<2**63:
        raise ValueError('Invalid seed')
    rng=random.Random(seed);ev=Evaluator(fn,dimension,budget);d=dimension
    initial=[.5]*d;init=ev.assess(initial)

    if method=='halton-qmc':
        shifts=[rng.random() for _ in range(d)]
        for n in range(1,budget):
            ev.assess([(halton(n,PRIMES[k])+shifts[k])%1. for k in range(d)])

    elif method=='inverse-bfgs':
        # Quasi-Newton method, projected to compact domain. Objective is maximized.
        x=initial;current=init;H=ident(d);eps=.012
        def gradient(p):
            g=[]
            for j in range(d):
                if ev.remaining<2:return None
                left=p.copy();right=p.copy()
                left[j]=max(0,p[j]-eps);right[j]=min(1,p[j]+eps)
                a=ev.assess(left);b=ev.assess(right)
                g.append((b-a)/(right[j]-left[j]))
            return g
        grad=gradient(x)
        while grad is not None and ev.remaining:
            direction=mv(H,grad)
            norm=math.sqrt(dot(direction,direction))
            if norm<1e-8 or not math.isfinite(norm):direction=[rng.gauss(0,1) for _ in range(d)];norm=math.sqrt(dot(direction,direction))
            direction=[v/max(1.,norm) for v in direction]
            best_trial=None
            for step in (.30,.15,.075,.0375):
                if not ev.remaining:break
                candidate=bounded([p+step*v for p,v in zip(x,direction)])
                score=ev.assess(candidate)
                if best_trial is None or score>best_trial[0]:best_trial=(score,candidate)
                if score>current+1e-10:break
            if best_trial is None:break
            f,xnew=best_trial
            if f<=current:
                x=list(ev.best);current=ev.score;H=ident(d)
            else:
                s=[b-a for a,b in zip(x,xnew)];old=grad
                x=xnew;current=f
                if ev.remaining<2*d:break
                grad=gradient(x)
                if grad is None:break
                # Hessian of negative fitness: y=-(new-grad - previous-grad).
                y=[g0-g1 for g0,g1 in zip(old,grad)]
                sy=dot(s,y)
                if sy>1e-9:
                    Hy=mv(H,y);yHy=dot(y,Hy);rho=1/sy
                    H=[[H[i][j]+(1+yHy*rho)*rho*s[i]*s[j]-rho*(s[i]*Hy[j]+Hy[i]*s[j]) for j in range(d)] for i in range(d)]
                else:H=ident(d)
                continue
            if ev.remaining<2*d:break
            grad=gradient(x)
        while ev.remaining:ev.assess(bounded([v+rng.gauss(0,.04) for v in ev.best]))

    elif method=='rank-mu-covariance-es':
        mu=[.5]*d;cov=ident(d);sigma=.23;lam=min(14,max(5,4+int(3*math.log(d+1))))
        lastbest=init
        while ev.remaining:
            try:L=chol(cov)
            except ValueError:cov=ident(d);L=chol(cov)
            population=[]
            for _ in range(min(lam,ev.remaining)):
                z=[rng.gauss(0,1) for _ in range(d)]
                v=[mu[i]+sigma*sum(L[i][j]*z[j] for j in range(i+1)) for i in range(d)]
                candidate=bounded(v);population.append((ev.assess(candidate),candidate))
            population.sort(key=lambda p:p[0],reverse=True)
            elite=population[:max(1,len(population)//2)]
            weights=list(range(len(elite),0,-1));norm=sum(weights);weights=[v/norm for v in weights]
            next_mu=[sum(weight*x[k] for weight,(_,x) in zip(weights,elite)) for k in range(d)]
            # Normalized rank-mu covariance adaptation (not full canonical CMA-ES).
            centered=[[x[k]-mu[k] for k in range(d)] for _,x in elite]
            estimated=[[sum(w*c[i]*c[j] for w,c in zip(weights,centered))/max(sigma*sigma,1e-5) for j in range(d)] for i in range(d)]
            cov=[[.82*cov[i][j]+.18*estimated[i][j]+(.001 if i==j else 0) for j in range(d)] for i in range(d)]
            mu=bounded(next_mu)
            changed=population[0][0]>lastbest
            sigma=min(.45,max(.012,sigma*(1.09 if changed else .96)))
            lastbest=max(lastbest,population[0][0])

    elif method=='gaussian-process-ei':
        # RBF kernel Gaussian Process expected-improvement acquisition on a
        # bounded candidate pool; dimension <=16 and at most 64 GP observations.
        pts=[initial];vals=[init]
        warm=min(6,budget//4)
        for _ in range(warm):
            p=[rng.random() for _ in range(d)];pts.append(p);vals.append(ev.assess(p))
        while ev.remaining:
            # Keep GP linear algebra bounded even with a 256-evaluation budget.
            pts_fit=pts[-64:];vals_fit=vals[-64:];m=len(pts_fit)
            C=[[math.exp(-sum((a-b)**2 for a,b in zip(pi,pj))/(2*.3**2))+(1e-5 if i==j else 0) for j,pj in enumerate(pts_fit)] for i,pi in enumerate(pts_fit)]
            L=chol(C);alpha=triangular_solve(L,vals_fit)
            incumbent=max(vals_fit)
            pool=[[rng.random() for _ in range(d)] for _ in range(48)]
            pool += [bounded([x+rng.gauss(0,.13) for x in ev.best]) for _ in range(24)]
            def acquisition(x):
                avg,sd=gp_predict(pts_fit,vals_fit,x,L,alpha)
                z=(avg-incumbent-.005)/sd
                return (avg-incumbent-.005)*(.5*(1+math.erf(z/math.sqrt(2))))+sd*math.exp(-.5*z*z)/math.sqrt(2*math.pi)
            candidate=max(pool,key=acquisition)
            val=ev.assess(candidate);pts.append(candidate);vals.append(val)

    elif method=='artificial-bee-colony':
        # Employed bees -> probability-weighted onlookers -> exhausted scouts.
        colony=min(12,max(4,budget//5))
        nests=[(initial,init,0)]
        while len(nests)<colony and ev.remaining:
            p=[rng.random() for _ in range(d)];nests.append((p,ev.assess(p),0))
        limit=8+d
        while ev.remaining:
            for i,(p,score,tries) in enumerate(nests):
                if not ev.remaining:break
                k=rng.choice([q for q in range(len(nests)) if q!=i])
                j=rng.randrange(d);q=p.copy();q[j]=p[j]+rng.uniform(-1,1)*(p[j]-nests[k][0][j]);q=bounded(q)
                s=ev.assess(q);nests[i]=(q,s,0) if s>score else (p,score,tries+1)
            for _ in range(min(len(nests),ev.remaining)):
                worst=min(x[1] for x in nests)
                probabilities=[max(.001,s-worst+.001) for _,s,_ in nests]
                i=rng.choices(range(len(nests)),weights=probabilities,k=1)[0]
                p,score,tries=nests[i];k=rng.choice([q for q in range(len(nests)) if q!=i]);j=rng.randrange(d)
                q=p.copy();q[j]=p[j]+rng.uniform(-1,1)*(p[j]-nests[k][0][j]);q=bounded(q)
                s=ev.assess(q);nests[i]=(q,s,0) if s>score else (p,score,tries+1)
            for i,(p,score,tries) in enumerate(nests):
                if tries>=limit and ev.remaining:
                    q=[rng.random() for _ in range(d)];nests[i]=(q,ev.assess(q),0)

    elif method=='harmony-search':
        memory=[(init,initial)]
        while len(memory)<min(12,max(4,budget//4)) and ev.remaining:
            p=[rng.random() for _ in range(d)];memory.append((ev.assess(p),p))
        while ev.remaining:
            child=[]
            for j in range(d):
                if rng.random()<.91:
                    v=rng.choice(memory)[1][j]
                    if rng.random()<.33:v+=rng.uniform(-.09,.09)
                else:v=rng.random()
                child.append(max(0,min(1,v)))
            score=ev.assess(child)
            memory.sort(key=lambda t:t[0])
            if score>memory[0][0]:memory[0]=(score,child)

    elif method=='ucb-operator-bandit':
        # UCB1 dynamically chooses among four genuinely different local moves.
        arms=4;counts=[0]*arms;rewards=[0.]*arms
        current=initial;score=init
        while ev.remaining:
            total=sum(counts)
            arm=(counts.index(0) if 0 in counts else
                 max(range(arms),key=lambda a:rewards[a]/counts[a]+1.2*math.sqrt(math.log(total)/counts[a])))
            t=ev.calls/max(ev.budget,1)
            if arm==0:proposal=[rng.random() for _ in range(d)]
            elif arm==1:proposal=bounded([x+rng.gauss(0,.2*(1-t)+.01) for x in current])
            elif arm==2:
                proposal=current.copy();i=rng.randrange(d);proposal[i]=max(0,min(1,proposal[i]+rng.uniform(-.3,.3)))
            else:proposal=bounded([.5*x+.5*y for x,y in zip(current,ev.best)])
            value=ev.assess(proposal)
            gain=max(0.,value-score)
            counts[arm]+=1;rewards[arm]+=min(1.,gain)
            if value>score or rng.random()<.02:
                current=proposal;score=value

    assert 1<=ev.calls<=budget
    return Result(algorithm=method,best=tuple(round(x,10) for x in ev.best),score=round(ev.score,10),evaluations=ev.calls,
                  budget=budget,seed=seed,history=tuple(ev.trace),schema='umbra.independent.optimizer.v2')


def benchmark(*,budget=48,seeds=3,dimension=6):
    if not 16<=budget<=128 or not 1<=seeds<=20 or not 1<=dimension<=12:raise ValueError('Unsafe benchmark request')
    cases=[]
    for name in METHODS_V20:
        for objective in TASKS:
            for s in range(seeds):
                fn=task(objective,dimension=dimension,seed=9111+s)
                baseline=fn([.5]*dimension)
                r=optimize_v20(name,fn,dimension=dimension,budget=budget,seed=2000+s)
                cases.append({'method':name,'task':objective,'seed':s,'score':r.score,'baseline':baseline,
                              'improvement':round(r.score-baseline,9),'calls':r.evaluations,'claimed_original_invention':False})
    out={'schema':'umbra.independent.optimizer.benchmark.v2','methods':list(METHODS_V20),'case_count':len(cases),
         'budget':budget,'synthetic_only':True,'real_model_training_steps':0,'production_merge_authorized':False,
         'cases':cases}
    out['sha256']=stable_hash(out)
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--budget',type=int,default=48);p.add_argument('--seeds',type=int,default=3)
    p.add_argument('--dimensions',type=int,default=6);p.add_argument('--output')
    a=p.parse_args();r=benchmark(budget=a.budget,seeds=a.seeds,dimension=a.dimensions)
    if a.output:
        f=Path(a.output);f.parent.mkdir(parents=True,exist_ok=True)
        with f.open('x') as stream:json.dump(r,stream,indent=2,sort_keys=True)
    print(json.dumps({k:v for k,v in r.items() if k!='cases'},indent=2))
if __name__=='__main__':main()
