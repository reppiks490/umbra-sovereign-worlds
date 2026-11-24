"""Certificate-checked length generalization for directed graph reasoning.
Independent procedural tasks inspired by length extrapolation benchmarks.
No external dataset, model inference, or automatic routing.
"""
import collections
import heapq
import random

FAMILIES=('shortest_path','max_flow')
SIZES=(4,8,16,32)
SCHEMA='myriad.proof_curriculum.v84'


def integer(x,lo,hi):
    return type(x) is int and lo<=x<=hi


def validate(q):
    if not isinstance(q,dict) or set(q)!={'family','n','source','sink','edges'} or q['family'] not in FAMILIES or not integer(q['n'],2,32):raise ValueError('invalid task')
    n=q['n'];s=q['source'];t=q['sink'];edges=q['edges']
    if not integer(s,0,n-1) or not integer(t,0,n-1) or s==t or not isinstance(edges,list) or not 1<=len(edges)<=n*(n-1):raise ValueError('invalid graph geometry')
    g={}
    for edge in edges:
        if not isinstance(edge,list) or len(edge)!=3:raise ValueError('invalid edge')
        u,v,w=edge
        if not integer(u,0,n-1) or not integer(v,0,n-1) or u==v or not integer(w,1,1000000) or (u,v) in g:raise ValueError('invalid or duplicate edge')
        g[u,v]=w
    return n,s,t,g


def generate(family,n,seed):
    if family not in FAMILIES or type(n) is not int or n not in SIZES or not integer(seed,0,2**31-1):raise ValueError('invalid generation bounds')
    rng=random.Random(8400000000+seed*256+n*2+FAMILIES.index(family))
    g={(u,u+1):rng.randint(1,20) for u in range(n-1)}
    for u in range(n):
        for v in range(n):
            if u!=v and (u,v) not in g and rng.random()<min(.5,4/n):g[u,v]=rng.randint(1,20)
    edges=[[u,v,w] for (u,v),w in sorted(g.items())]
    return {'family':family,'n':n,'source':0,'sink':n-1,'edges':edges}


def transform(q,seed,factor):
    n,s,t,g=validate(q)
    if not integer(seed,0,2**31-1) or not integer(factor,1,1000) or any(w*factor>1000000 for w in g.values()):raise ValueError('invalid transform')
    perm=list(range(n));random.Random(8410000000+seed).shuffle(perm)
    edges=sorted([perm[u],perm[v],w*factor] for (u,v),w in g.items())
    return {'family':q['family'],'n':n,'source':perm[s],'sink':perm[t],'edges':edges}


def verify(q,c):
    """Verify optimality certificates without executing either reference solver."""
    n,s,t,g=validate(q)
    if not isinstance(c,dict) or not integer(c.get('answer'),0,n*n*1000000):raise ValueError('invalid answer')
    answer=c['answer']
    if q['family']=='shortest_path':
        if set(c)!={'answer','path','potentials'}:raise ValueError('invalid shortest certificate')
        path=c['path'];p=c['potentials']
        if not isinstance(path,list) or not 2<=len(path)<=n or any(not integer(u,0,n-1) for u in path) or len(set(path))!=len(path) or path[0]!=s or path[-1]!=t:raise ValueError('invalid path')
        if not isinstance(p,list) or len(p)!=n or any(not integer(x,-n*1000000,n*1000000) for x in p) or p[s]!=0 or p[t]!=answer:raise ValueError('invalid potentials')
        route=list(zip(path,path[1:]))
        if any(e not in g for e in route) or sum(g[e] for e in route)!=answer or any(p[v]-p[u]>w for (u,v),w in g.items()):raise ValueError('primal-dual mismatch')
    else:
        if set(c)!={'answer','flows','cut'}:raise ValueError('invalid flow certificate')
        flows=c['flows'];cut=c['cut']
        if not isinstance(flows,list) or len(flows)!=len(q['edges']) or any(not integer(f,0,w) for f,(_,_,w) in zip(flows,q['edges'])):raise ValueError('invalid flow')
        if not isinstance(cut,list) or not 1<=len(cut)<n or any(not integer(u,0,n-1) for u in cut) or cut!=sorted(set(cut)) or s not in cut or t in cut:raise ValueError('invalid cut')
        balance=[0]*n
        for f,(u,v,w) in zip(flows,q['edges']):balance[u]-=f;balance[v]+=f
        if any(balance[u]!=(-answer if u==s else answer if u==t else 0) for u in range(n)):raise ValueError('flow conservation')
        cut=set(cut)
        if sum(w for (u,v),w in g.items() if u in cut and v not in cut)!=answer:raise ValueError('max-flow min-cut mismatch')
    return True


def shortest(n,s,t,g):
    adj=[[] for _ in range(n)]
    for (u,v),w in g.items():adj[u].append((v,w))
    dist=[None]*n;dist[s]=0;parent={};queue=[(0,s)]
    while queue:
        d,u=heapq.heappop(queue)
        if d!=dist[u]:continue
        for v,w in adj[u]:
            k=d+w
            if dist[v] is None or k<dist[v]:dist[v]=k;parent[v]=u;heapq.heappush(queue,(k,v))
    if dist[t] is None:raise ValueError('unreachable target')
    path=[t]
    while path[-1]!=s:path.append(parent[path[-1]])
    high=max(d for d in dist if d is not None)
    return {'answer':dist[t],'path':list(reversed(path)),'potentials':[high if d is None else d for d in dist]}


def flow(n,s,t,g,edges):
    cap=[[0]*n for _ in range(n)]
    for (u,v),w in g.items():cap[u][v]=w
    residual=[row[:] for row in cap];value=0
    while True:
        parents={s:s};queue=collections.deque([s])
        while queue and t not in parents:
            u=queue.popleft()
            for v,w in enumerate(residual[u]):
                if w>0 and v not in parents:parents[v]=u;queue.append(v)
        if t not in parents:break
        path=[];v=t
        while v!=s:u=parents[v];path.append((u,v));v=u
        inc=min(residual[u][v] for u,v in path);value+=inc
        for u,v in path:residual[u][v]-=inc;residual[v][u]+=inc
    return {'answer':value,'flows':[max(0,cap[u][v]-residual[u][v]) for u,v,_ in edges],'cut':sorted(parents)}


def solve(q):
    n,s,t,g=validate(q)
    c=shortest(n,s,t,g) if q['family']=='shortest_path' else flow(n,s,t,g,q['edges'])
    verify(q,c)
    return c


def qualify():
    by_size={}
    for n in SIZES:
        rows=0
        for family in FAMILIES:
            for seed in range(12):
                q=generate(family,n,seed);a=solve(q);v=transform(q,seed+100,3);b=solve(v)
                if b['answer']!=3*a['answer']:raise ValueError('metamorphic qualification failure')
                rows+=2
        by_size[str(n)]=rows
    return {'schema':SCHEMA,'certificate_cases':sum(by_size.values()),'by_size':by_size,'production_authority':False,'semantic_mastery_certified':False,'actual_model_calls':0}
