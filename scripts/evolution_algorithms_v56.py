"""Sixteen executable reference algorithms, distinct from parameter sweeps."""
import heapq,math,statistics
from collections import deque,Counter
def floyd_warshall(matrix):
    d=[list(r) for r in matrix];n=len(d)
    if any(len(r)!=n for r in d) or any(math.isnan(v) for r in d for v in r):raise ValueError('invalid matrix')
    for k in range(n):
        for i in range(n):
            for j in range(n):d[i][j]=min(d[i][j],d[i][k]+d[k][j])
    if any(d[i][i]<0 for i in range(n)):raise ValueError('negative cycle')
    return d
def kruskal(n,edges):
    if type(n) is not int or n<1:raise ValueError('invalid graph size')
    parent=list(range(n));rank=[0]*n
    def find(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    total=0;chosen=[]
    for a,b,w in sorted(edges,key=lambda e:e[2]):
        if not 0<=a<n or not 0<=b<n or not math.isfinite(w):raise ValueError('invalid edge')
        x,y=find(a),find(b)
        if x==y:continue
        if rank[x]<rank[y]:x,y=y,x
        parent[y]=x
        if rank[x]==rank[y]:rank[x]+=1
        chosen.append((a,b,w));total+=w
    if len(chosen)!=n-1:raise ValueError('disconnected graph')
    return total,chosen
def bfs_path(g,start,end):
    if start not in g or end not in g:raise ValueError('unknown vertex')
    q=deque([start]);prev={start:None}
    while q:
        x=q.popleft()
        if x==end:
            out=[]
            while x is not None:out.append(x);x=prev[x]
            return out[::-1]
        for y in g[x]:
            if y not in g:raise ValueError('unknown vertex')
            if y not in prev:prev[y]=x;q.append(y)
    return None
def max_flow(g,start,end):
    if start not in g or end not in g or start==end:raise ValueError('invalid terminals')
    residual={v:{} for v in g}
    for u,edges in g.items():
        for v,c in edges.items():
            if v not in g or type(c) is not int or c<0:raise ValueError('nonnegative integer capacities required')
            residual[u][v]=residual[u].get(v,0)+c;residual[v].setdefault(u,0)
    total=0
    while True:
        path=bfs_path({u:[v for v,c in edges.items() if c>0] for u,edges in residual.items()},start,end)
        if path is None:return total
        cap=min(residual[u][v] for u,v in zip(path,path[1:]))
        for u,v in zip(path,path[1:]):residual[u][v]-=cap;residual[v][u]+=cap
        total+=cap
def kmp(text,pattern):
    if not pattern:raise ValueError('empty pattern')
    lps=[0]*len(pattern);j=0
    for i in range(1,len(pattern)):
        while j and pattern[i]!=pattern[j]:j=lps[j-1]
        if pattern[i]==pattern[j]:j+=1
        lps[i]=j
    out=[];j=0
    for i,c in enumerate(text):
        while j and c!=pattern[j]:j=lps[j-1]
        if c==pattern[j]:j+=1
        if j==len(pattern):out.append(i-j+1);j=lps[j-1]
    return out
def longest_common_subsequence(a,b):
    p=[0]*(len(b)+1)
    for x in a:
        q=[0]
        for j,y in enumerate(b):q.append(p[j]+1 if x==y else max(q[-1],p[j+1]))
        p=q
    return p[-1]
def knapsack(weights,values,capacity):
    if len(weights)!=len(values) or type(capacity) is not int or not 0<=capacity<=1000000 or any(type(w) is not int or w<=0 for w in weights):raise ValueError('invalid knapsack')
    d=[0]*(capacity+1)
    for w,v in zip(weights,values):
        for c in range(capacity,w-1,-1):d[c]=max(d[c],d[c-w]+v)
    return d[-1]
def huffman_lengths(freq):
    if not freq or any(not math.isfinite(x) or x<=0 for x in freq.values()):raise ValueError('invalid frequencies')
    heap=[(v,i,[k]) for i,(k,v) in enumerate(freq.items())];heapq.heapify(heap);length=dict.fromkeys(freq,0);i=len(heap)
    while len(heap)>1:
        a,_,x=heapq.heappop(heap);b,_,y=heapq.heappop(heap)
        for k in x+y:length[k]+=1
        heapq.heappush(heap,(a+b,i,x+y));i+=1
    return {k:max(1,v) for k,v in length.items()}
def sieve(n):
    if type(n) is not int or not 0<=n<=10000000:raise ValueError('invalid bound')
    a=bytearray(b'\x01')*(n+1)
    if n>=0:a[0]=0
    if n>=1:a[1]=0
    for p in range(2,math.isqrt(n)+1):
        if a[p]:a[p*p:n+1:p]=b'\x00'*((n-p*p)//p+1)
    return [i for i,v in enumerate(a) if v]
def bisection(f,a,b,tol=1e-10):
    if not a<b or not tol>0:raise ValueError('invalid bracket')
    fa,fb=f(a),f(b)
    if not all(math.isfinite(v) for v in (fa,fb)) or fa*fb>0:raise ValueError('root not bracketed')
    if fa==0:return a
    if fb==0:return b
    for _ in range(256):
        c=(a+b)/2;fc=f(c)
        if not math.isfinite(fc):raise ValueError('nonfinite function')
        if fc==0 or b-a<=tol:return c
        if (fa>0)==(fc>0):a,fa=c,fc
        else:b=c
    raise ValueError('not converged')
def simpson(f,a,b,n):
    if type(n) is not int or n<2 or n%2 or n>1000000:raise ValueError('positive even partition required')
    h=(b-a)/n
    return h/3*(f(a)+f(b)+sum((4 if i%2 else 2)*f(a+i*h) for i in range(1,n)))
def welford(values):
    n=0;mu=m2=0.
    for x in values:
        if not math.isfinite(x):raise ValueError('nonfinite sample')
        n+=1;d=x-mu;mu+=d/n;m2+=d*(x-mu)
    if n<2:raise ValueError('insufficient sample')
    return mu,m2/(n-1)
def haar(values):
    x=list(values);n=len(x)
    if not n or n&(n-1) or any(not math.isfinite(v) for v in x):raise ValueError('power of two required')
    details=[];r=math.sqrt(2)
    while len(x)>1:
        details.append([(a-b)/r for a,b in zip(x[::2],x[1::2])])
        x=[(a+b)/r for a,b in zip(x[::2],x[1::2])]
    return x+[v for row in reversed(details) for v in row]
def mann_kendall(values):
    x=list(values)
    if any(not math.isfinite(v) for v in x):raise ValueError('invalid sequence')
    return sum((b>a)-(b<a) for i,a in enumerate(x) for b in x[i+1:])
def theil_sen(x,y):
    if len(x)!=len(y) or len(x)<2:raise ValueError('invalid sample')
    slopes=[(y[j]-y[i])/(x[j]-x[i]) for i in range(len(x)) for j in range(i+1,len(x)) if x[j]!=x[i]]
    if not slopes or any(not math.isfinite(v) for v in slopes):raise ValueError('undefined slope')
    return statistics.median(slopes)
def js_divergence(a,b):
    if len(a)!=len(b) or not a or any(not math.isfinite(v) or v<0 for v in list(a)+list(b)) or not sum(a)>0 or not sum(b)>0:raise ValueError('invalid distribution')
    p=[v/sum(a) for v in a];q=[v/sum(b) for v in b];m=[(x+y)/2 for x,y in zip(p,q)]
    return .5*sum(x*math.log2(x/z) for x,z in zip(p,m) if x)+.5*sum(y*math.log2(y/z) for y,z in zip(q,m) if y)
REGISTRY={f.__name__:f for f in (floyd_warshall,kruskal,bfs_path,max_flow,kmp,longest_common_subsequence,knapsack,huffman_lengths,sieve,bisection,simpson,welford,haar,mann_kendall,theil_sen,js_divergence)}
