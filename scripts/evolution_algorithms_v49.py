"""Twelve separate, executable algorithm implementations. No recipe multiplication."""
from bisect import bisect_left,insort
from collections import deque
import heapq,math
def mergesort(seq):
    a=list(seq)
    if len(a)<2:return a
    mid=len(a)//2;l=mergesort(a[:mid]);r=mergesort(a[mid:]);i=j=0;out=[]
    while i<len(l) and j<len(r):
        if l[i]<=r[j]:out.append(l[i]);i+=1
        else:out.append(r[j]);j+=1
    return out+l[i:]+r[j:]
def quickselect(seq,k):
    a=list(seq)
    if type(k) is not int or not 0<=k<len(a):raise ValueError('invalid rank')
    while True:
        p=a[len(a)//2];lo=[v for v in a if v<p];hi=[v for v in a if v>p];eq=len(a)-len(lo)-len(hi)
        if k<len(lo):a=lo
        elif k<len(lo)+eq:return p
        else:k-=len(lo)+eq;a=hi
def _graph(g,s):
    if s not in g or any(v not in g or not math.isfinite(w) for edges in g.values() for v,w in edges.items()):raise ValueError('invalid graph')
def dijkstra(g,s):
    _graph(g,s)
    if any(w<0 for edges in g.values() for w in edges.values()):raise ValueError('negative weight')
    d={v:math.inf for v in g};d[s]=0;counter=0;q=[(0,counter,s)]
    while q:
        cost,_,u=heapq.heappop(q)
        if cost!=d[u]:continue
        for v,w in g[u].items():
            c=cost+w
            if c<d[v]:d[v]=c;counter+=1;heapq.heappush(q,(c,counter,v))
    return d
def bellman_ford(g,s):
    _graph(g,s);d={v:math.inf for v in g};d[s]=0
    edges=[(u,v,w) for u,e in g.items() for v,w in e.items()]
    for _ in range(len(g)-1):
        changed=False
        for u,v,w in edges:
            if d[u]+w<d[v]:d[v]=d[u]+w;changed=True
        if not changed:break
    if any(d[u]+w<d[v] for u,v,w in edges):raise ValueError('reachable negative cycle')
    return d
def topological(g):
    degrees=dict.fromkeys(g,0)
    for edges in g.values():
        for v in edges:
            if v not in degrees:raise ValueError('unknown vertex')
            degrees[v]+=1
    q=deque(v for v,n in degrees.items() if n==0);out=[]
    while q:
        u=q.popleft();out.append(u)
        for v in g[u]:
            degrees[v]-=1
            if degrees[v]==0:q.append(v)
    if len(out)!=len(g):raise ValueError('cycle')
    return out
def kalman(values,q,r):
    a=list(values)
    if not a or q<0 or r<=0 or not all(math.isfinite(v) for v in a+[q,r]):raise ValueError('invalid filter input')
    x=a[0];p=r;out=[]
    for z in a:
        p+=q;k=p/(p+r);x+=k*(z-x);p*=1-k;out.append(x)
    return out
def cusum(values,mean,threshold,drift=0):
    if threshold<=0 or drift<0 or not all(math.isfinite(v) for v in (mean,threshold,drift)):raise ValueError('invalid detection parameters')
    pos=neg=0.;out=[]
    for i,z in enumerate(values):
        if not math.isfinite(z):raise ValueError('nonfinite signal')
        delta=z-mean;pos=max(0.,pos+delta-drift);neg=min(0.,neg+delta+drift)
        if pos>=threshold or -neg>=threshold:out.append(i);pos=neg=0.
    return out
def autocorr(values,lag):
    a=list(values)
    if type(lag) is not int or not 0<=lag<len(a) or not all(math.isfinite(v) for v in a):raise ValueError('invalid lag or series')
    mu=sum(a)/len(a);b=[v-mu for v in a];den=sum(v*v for v in b)
    if den==0:raise ValueError('constant series')
    return sum(b[i]*b[i-lag] for i in range(lag,len(b)))/den
def levenshtein(a,b):
    prev=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        row=[i]
        for j,y in enumerate(b,1):row.append(min(row[-1]+1,prev[j]+1,prev[j-1]+(x!=y)))
        prev=row
    return prev[-1]
def lis(seq):
    tails=[]
    for x in seq:
        i=bisect_left(tails,x)
        if i==len(tails):tails.append(x)
        else:tails[i]=x
    return len(tails)
def rolling_median(values,k):
    a=list(values)
    if type(k) is not int or not 1<=k<=len(a):raise ValueError('invalid window')
    w=sorted(a[:k]);out=[]
    for i in range(k,len(a)+1):
        out.append(w[k//2] if k%2 else (w[k//2-1]+w[k//2])/2)
        if i<len(a):w.pop(bisect_left(w,a[i-k]));insort(w,a[i])
    return out
def max_drawdown(values):
    peak=None;worst=0.
    for v in values:
        if not math.isfinite(v) or v<=0:raise ValueError('invalid positive equity')
        peak=v if peak is None else max(peak,v);worst=max(worst,(peak-v)/peak)
    if peak is None:raise ValueError('empty equity')
    return worst
REGISTRY={f.__name__:f for f in (mergesort,quickselect,dijkstra,bellman_ford,topological,kalman,cusum,autocorr,levenshtein,lis,rolling_median,max_drawdown)}
