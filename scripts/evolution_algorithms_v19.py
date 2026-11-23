#!/usr/bin/env python3
"""Twelve independently implemented, bounded black-box optimization algorithms.

Research-only mathematical algorithms, independently written from public methods;
no third-party source code is vendored. This module never runs a market order,
imports secrets, updates model weights, or modifies a repository. Named methods
are distinct algorithms, not parameter variations counted as new inventions.
"""
from __future__ import annotations
import argparse
from collections import deque
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import random
from statistics import mean, median

METHODS = (
    'uniform-random', 'latin-hypercube', 'coordinate-pattern',
    'simulated-annealing', 'differential-evolution', 'particle-swarm',
    'genetic-algorithm', 'cross-entropy', 'evolution-strategy',
    'nelder-mead', 'spsa-ascent', 'tabu-neighborhood',
)
REFERENCE = {
    'uniform-random': 'https://docs.scipy.org/doc/scipy/reference/optimize.html',
    'latin-hypercube': 'https://docs.scipy.org/doc/scipy/reference/stats.qmc.html',
    'coordinate-pattern': 'https://docs.scipy.org/doc/scipy/reference/optimize.html',
    'simulated-annealing': 'https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.dual_annealing.html',
    'differential-evolution': 'https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html',
    'particle-swarm': 'https://github.com/DEAP/deap',
    'genetic-algorithm': 'https://github.com/DEAP/deap',
    'cross-entropy': 'https://github.com/facebookresearch/nevergrad',
    'evolution-strategy': 'https://github.com/DEAP/deap',
    'nelder-mead': 'https://docs.scipy.org/doc/scipy/reference/optimize.html',
    'spsa-ascent': 'https://docs.scipy.org/doc/scipy/reference/optimize.html',
    'tabu-neighborhood': 'https://github.com/facebookresearch/nevergrad',
}
TASKS=('shifted-sphere','rotated-quadratic','rastrigin','rosenbrock','huber-robust')


def bounded(x):
    return [max(0., min(1., float(v))) for v in x]


def stable_hash(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class Result:
    algorithm: str
    best: tuple[float, ...]
    score: float
    evaluations: int
    budget: int
    seed: int
    history: tuple[tuple[int, float], ...]
    schema: str='umbra.independent.optimizer.v1'
    real_model_weights_changed: bool=False
    live_trades: int=0
    original_invention_claim: bool=False


class Evaluator:
    """Only permitted way to invoke the function: bounded input, exact budget."""
    def __init__(self, fn, dimension, budget):
        if not callable(fn) or isinstance(dimension,bool) or not 1<=dimension<=64:
            raise ValueError('Unsupported black-box objective or dimension')
        if isinstance(budget,bool) or not 8<=budget<=100_000:
            raise ValueError('Budget must be 8..100000 objective evaluations')
        self.fn=fn;self.dim=dimension;self.budget=budget
        self.calls=0;self.best=tuple([0.5]*dimension);self.score=-math.inf;self.trace=[]

    @property
    def remaining(self):return self.budget-self.calls

    def assess(self, x):
        if not self.remaining:raise RuntimeError('Evaluation budget exhausted')
        if len(x)!=self.dim or not all(isinstance(v,(float,int)) and math.isfinite(v) for v in x):
            raise ValueError('Non-finite or malformed candidate')
        x=tuple(bounded(x))
        value=float(self.fn(x))
        if not math.isfinite(value):raise ValueError('Non-finite objective value')
        self.calls+=1
        if value>self.score:
            self.score=value;self.best=x
        if self.calls==1 or self.calls%max(1,self.budget//8)==0 or self.calls==self.budget:
            self.trace.append((self.calls,round(self.score,9)))
        return value


def random_candidate(rng,dim):return [rng.random() for _ in range(dim)]


def optimize(algorithm, fn, *, dimension=6, budget=128, seed=73):
    if algorithm not in METHODS:raise ValueError('Unknown independently implemented method')
    if isinstance(seed,bool) or not 0<=seed<2**63:raise ValueError('Invalid deterministic seed')
    rng=random.Random(seed); ev=Evaluator(fn,dimension,budget)
    dim=dimension
    ev.assess([.5]*dim)
    if algorithm=='uniform-random':
        while ev.remaining:ev.assess(random_candidate(rng,dim))

    elif algorithm=='latin-hypercube':
        n=ev.remaining
        grids=[rng.sample(list(range(n)),n) for _ in range(dim)]
        for i in range(n):
            ev.assess([(grids[k][i]+rng.random())/n for k in range(dim)])

    elif algorithm=='coordinate-pattern':
        point=[.5]*dim;delta=.24
        while ev.remaining:
            improved=False
            for j in range(dim):
                for sign in (1,-1):
                    if not ev.remaining:break
                    p=point.copy();p[j]+=sign*delta;p=bounded(p)
                    val=ev.assess(p)
                    if val>=ev.score and tuple(p)==ev.best:point=p;improved=True
                if not ev.remaining:break
            if not improved:delta*=.55
            if delta<.003:delta=.19;point=random_candidate(rng,dim)

    elif algorithm=='simulated-annealing':
        point=[.5]*dim;value=ev.score
        while ev.remaining:
            t=ev.calls/max(ev.budget,1)
            temp=max(0.002,0.25*(1-t)**1.8)
            trial=bounded([x+rng.gauss(0,0.28*(1-t)+.015) for x in point])
            score=ev.assess(trial)
            if score>value or rng.random()<math.exp(max(-100.,(score-value)/temp)):
                point,value=trial,score

    elif algorithm=='differential-evolution':
        population=[([.5]*dim,ev.score)]
        while len(population)<min(12,ev.budget//3) and ev.remaining:
            x=random_candidate(rng,dim);population.append((x,ev.assess(x)))
        i=0
        while ev.remaining:
            if len(population)<4:break
            ids=list(range(len(population)));ids.remove(i)
            a,b,c=rng.sample(ids,3)
            j0=rng.randrange(dim)
            trial=bounded([(population[a][0][j]+.68*(population[b][0][j]-population[c][0][j])
                            if rng.random()<.78 or j==j0 else population[i][0][j]) for j in range(dim)])
            score=ev.assess(trial)
            if score>=population[i][1]:population[i]=(trial,score)
            i=(i+1)%len(population)

    elif algorithm=='particle-swarm':
        particles=[]
        for i in range(min(12,max(3,ev.budget//3))):
            if not ev.remaining:break
            p=[.5]*dim if i==0 else random_candidate(rng,dim)
            score=ev.score if i==0 else ev.assess(p)
            particles.append([p,[rng.uniform(-.06,.06) for _ in range(dim)],p.copy(),score])
        while ev.remaining:
            for item in particles:
                if not ev.remaining:break
                p,v,pbest,score=item
                for j in range(dim):
                    v[j]=max(-.2,min(.2,.6*v[j]+1.4*rng.random()*(pbest[j]-p[j])+1.4*rng.random()*(ev.best[j]-p[j])))
                nxt=bounded([x+y for x,y in zip(p,v)])
                val=ev.assess(nxt)
                item[0]=nxt
                if val>score:item[2]=nxt.copy();item[3]=val

    elif algorithm=='genetic-algorithm':
        pop=[([.5]*dim,ev.score)]
        while len(pop)<min(12,max(4,ev.budget//3)) and ev.remaining:
            x=random_candidate(rng,dim);pop.append((x,ev.assess(x)))
        while ev.remaining:
            pool=sorted(pop,key=lambda x:x[1],reverse=True)
            def tournament():return max(rng.sample(pool,min(3,len(pool))),key=lambda x:x[1])[0]
            mom,dad=tournament(),tournament()
            alpha=rng.random();child=[alpha*x+(1-alpha)*y+rng.gauss(0,.08) if rng.random()<.75 else x for x,y in zip(mom,dad)]
            child=bounded(child);score=ev.assess(child)
            pop=sorted(pop+[(child,score)],key=lambda x:x[1],reverse=True)[:len(pop)]

    elif algorithm=='cross-entropy':
        mu=[.5]*dim;sd=[.30]*dim
        while ev.remaining:
            batch=[]
            for _ in range(min(12,ev.remaining)):
                candidate=bounded([rng.gauss(m,s) for m,s in zip(mu,sd)])
                batch.append((ev.assess(candidate),candidate))
            elites=sorted(batch,reverse=True)[:max(1,len(batch)//4)]
            mu=[.65*mu[k]+.35*sum(x[k] for _,x in elites)/len(elites) for k in range(dim)]
            if len(elites)>1:
                sd=[max(.015,min(.4,.7*sd[k]+.3*math.sqrt(sum((x[k]-mu[k])**2 for _,x in elites)/len(elites)))) for k in range(dim)]
            else:sd=[max(.015,s*.85) for s in sd]

    elif algorithm=='evolution-strategy':
        parent=[.5]*dim;value=ev.score;sigma=.19
        while ev.remaining:
            mutations=[]
            for _ in range(min(7,ev.remaining)):
                x=bounded([p+rng.gauss(0,sigma) for p in parent]);mutations.append((ev.assess(x),x))
            best=max(mutations,key=lambda v:v[0]);success=best[0]>value
            if success:parent=best[1];value=best[0]
            sigma=max(.007,min(.5,sigma*(1.1 if success else .85)))

    elif algorithm=='nelder-mead':
        simplex=[([.5]*dim,ev.score)]
        for i in range(dim):
            if not ev.remaining:break
            p=[.5]*dim;p[i]=.68;simplex.append((p,ev.assess(p)))
        while ev.remaining and len(simplex)==dim+1:
            simplex.sort(key=lambda x:x[1],reverse=True)
            centroid=[sum(x[0][j] for x in simplex[:-1])/dim for j in range(dim)]
            worst=simplex[-1][0]
            reflected=bounded([2*c-w for c,w in zip(centroid,worst)])
            fs=ev.assess(reflected)
            if simplex[0][1]>=fs>simplex[-2][1]:simplex[-1]=(reflected,fs);continue
            if fs>simplex[0][1] and ev.remaining:
                expanded=bounded([3*c-2*w for c,w in zip(centroid,worst)])
                es=ev.assess(expanded)
                simplex[-1]=(expanded,es) if es>fs else (reflected,fs)
            elif ev.remaining:
                contracted=bounded([.5*(c+w) for c,w in zip(centroid,worst)])
                cs=ev.assess(contracted)
                if cs>simplex[-1][1]:simplex[-1]=(contracted,cs)
                else:
                    pivot=simplex[0][0]
                    rest=[]
                    for p,_ in simplex[1:]:
                        if not ev.remaining:break
                        x=bounded([.5*(a+b) for a,b in zip(pivot,p)]);rest.append((x,ev.assess(x)))
                    simplex=[simplex[0]]+rest+simplex[len(rest)+1:]
            else:simplex[-1]=(reflected,fs)

    elif algorithm=='spsa-ascent':
        p=[.5]*dim;m=[0.]*dim;iteration=0
        while ev.remaining>=2:
            iteration+=1
            ck=.13/iteration**.101
            delta=[rng.choice((-1,1)) for _ in range(dim)]
            plus=bounded([x+ck*d for x,d in zip(p,delta)]);minus=bounded([x-ck*d for x,d in zip(p,delta)])
            sp=ev.assess(plus);sm=ev.assess(minus)
            lr=.11/iteration**.60
            for j,d in enumerate(delta):m[j]=.65*m[j]+.35*((sp-sm)/(2*ck*d))
            p=bounded([x+lr*g for x,g in zip(p,m)])
        if ev.remaining:ev.assess(p)

    elif algorithm=='tabu-neighborhood':
        p=[.5]*dim;tabu=deque(maxlen=31);size=.22;step=0
        def key(v):return tuple(round(x,3) for x in v)
        tabu.append(key(p))
        while ev.remaining:
            step+=1
            options=[]
            for j in range(dim):
                for sign in (-1,1):
                    if not ev.remaining:break
                    x=p.copy();x[j]=max(0,min(1,x[j]+sign*size))
                    if key(x) in tabu:continue
                    score=ev.assess(x);options.append((score,x))
                if not ev.remaining:break
            if options:
                p=max(options,key=lambda x:x[0])[1];tabu.append(key(p))
            else:
                size=max(.02,size*.55)
                p=random_candidate(rng,dim);tabu.clear();tabu.append(key(p))
            if step%12==0:size=max(.02,size*.8)

    if ev.calls<1:raise AssertionError('No evaluations')
    return Result(algorithm=algorithm,best=tuple(round(x,10) for x in ev.best),
                  score=round(ev.score,10),evaluations=ev.calls,budget=budget,seed=seed,
                  history=tuple(ev.trace))


def task(name,dimension=6,seed=123,structure="independent"):
    """Deterministic synthetic benchmark; nonstationarity is controlled by task seed."""
    if name not in TASKS:raise ValueError('Unknown synthetic benchmark')
    if structure not in ('independent','shared'):raise ValueError('Unknown synthetic target correlation')
    rng=random.Random(seed)
    if structure=='shared':
        # Bounded seed-specific measurement noise around shared latent parameters.
        # This is an intentionally easier transfer task, not real general intelligence.
        base=random.Random(int(hashlib.sha256(f'{name}|{dimension}|shared-v1'.encode()).hexdigest()[:15],16))
        target=[max(.1,min(.9,.17+.66*base.random()+rng.gauss(0,.018))) for _ in range(dimension)]
    else:target=[.1+.8*rng.random() for _ in range(dimension)]
    if name=='shifted-sphere':
        def fn(x):return -sum((v-t)**2 for v,t in zip(x,target))
    elif name=='rotated-quadratic':
        def fn(x):
            d=[v-t for v,t in zip(x,target)]
            return -sum((1+j)*((d[j]+.5*d[(j+1)%dimension])**2) for j in range(dimension))
    elif name=='rastrigin':
        def fn(x):return -sum(10+z*z-10*math.cos(2*math.pi*z) for v,t in zip(x,target) for z in ((v-t)*5.,))
    elif name=='rosenbrock':
        def fn(x):
            y=[1+2*(v-t) for v,t in zip(x,target)]
            return -sum(100*(b-a*a)**2+(1-a)**2 for a,b in zip(y,y[1:]))
    else: # robust Huber objective, useful for outlier sensitivity
        def fn(x):
            residual=[(v-t)*(2+j) for j,(v,t) in enumerate(zip(x,target))]
            return -sum((.5*z*z if abs(z)<.25 else .25*(abs(z)-.125)) for z in residual)
    return fn


def suite(*,budget=96,seeds=3,dimensions=5):
    if not 16<=budget<=10_000 or not 1<=seeds<=100 or not 1<=dimensions<=32:
        raise ValueError('Unsafe study dimensions')
    cases=[]
    for name in METHODS:
        for task_name in TASKS:
            for s in range(seeds):
                fn=task(task_name,dimensions,seed=100+s)
                baseline=fn([.5]*dimensions)
                heldout_fn=task(task_name,dimensions,seed=50_000+s)
                heldout_base=heldout_fn([.5]*dimensions)
                run=optimize(name,fn,dimension=dimensions,budget=budget,seed=1000+s)
                heldout_score=heldout_fn(run.best)
                cases.append({'algorithm':name,'task':task_name,'seed':s,'evaluations':run.evaluations,
                              'best_score':run.score,'baseline_center':baseline,
                              'gain_vs_baseline':round(run.score-baseline,9),
                              'heldout_score':round(heldout_score,9),
                              'heldout_gain_vs_center':round(heldout_score-heldout_base,9),
                              'best':run.best,'deterministic_receipt':stable_hash(asdict(run))})
    aggregated={method:{'trials':len([c for c in cases if c['algorithm']==method]),
                         'median_train_gain':round(median(c['gain_vs_baseline'] for c in cases if c['algorithm']==method),9),
                         'median_heldout_gain':round(median(c['heldout_gain_vs_center'] for c in cases if c['algorithm']==method),9),
                         'tasks':len(TASKS)} for method in METHODS}
    report={'schema':'umbra.evolution.independent_methods.v1','case_count':len(cases),
            'implemented_distinct_methods':len(METHODS),'task_count':len(TASKS),
            'seeds_per_task':seeds,'budget_per_case':budget,
            'results':cases,'summary':aggregated,
            'real_model_weight_updates':0,'production_changes':0,
            'data_domain':'synthetic_test_functions_only'}
    report['sha256']=stable_hash(report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--budget',type=int,default=96)
    p.add_argument('--seeds',type=int,default=3)
    p.add_argument('--dimensions',type=int,default=5)
    p.add_argument('--output')
    a=p.parse_args()
    report=suite(budget=a.budget,seeds=a.seeds,dimensions=a.dimensions)
    if a.output:
        dest=Path(a.output)
        if dest.exists():raise FileExistsError('Research receipt already exists; never silently overwrite')
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'schema':report['schema'],'case_count':report['case_count'],
                      'methods':report['implemented_distinct_methods'],'sha256':report['sha256'],
                      'output':a.output},indent=2))

if __name__=='__main__':main()
