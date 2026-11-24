"""Nineteen executable graph, probabilistic, clustering and numerical methods."""
import math
from collections import deque
def bridges(g):
    if any(v not in g or u not in g[v] for u,adj in g.items() for v in adj):raise ValueError('undirected graph required')
    seen={};low={};out=[]
    def visit(u,parent):
        seen[u]=low[u]=len(seen)
        for v in g[u]:
            if v==parent:continue
            if v in seen:low[u]=min(low[u],seen[v])
            else:
                visit(v,u);low[u]=min(low[u],low[v])
                if low[v]>seen[u]:out.append(tuple(sorted((u,v))))
    for u in g:
        if u not in seen:visit(u,None)
    return sorted(out)
def pagerank(g,d=.85,tol=1e-10,steps=1000):
    n=len(g)
    if not n or not 0<d<1 or any(v not in g for adj in g.values() for v in adj):raise ValueError('graph')
    p={u:1/n for u in g}
    for _ in range(steps):
        leak=sum(p[u] for u in g if not g[u]);q={u:(1-d+d*leak)/n for u in g}
        for u,adj in g.items():
            for v in adj:q[v]+=d*p[u]/len(adj)
        if sum(abs(p[u]-q[u]) for u in g)<tol:return q
        p=q
    raise ValueError('not converged')
def components(g):
    if any(v not in g or u not in g[v] for u,adj in g.items() for v in adj):raise ValueError('undirected graph required')
    seen=set();out=[]
    for u in g:
        if u in seen:continue
        q=deque([u]);seen.add(u);c={u}
        while q:
            for v in g[q.popleft()]:
                if v not in seen:seen.add(v);c.add(v);q.append(v)
        out.append(c)
    return out
def longest_palindromic_subsequence(s):
    n=len(s)
    if not n:return 0
    d=[[0]*n for _ in s]
    for i in range(n-1,-1,-1):
        d[i][i]=1
        for j in range(i+1,n):d[i][j]=2+(d[i+1][j-1] if j>i+1 else 0) if s[i]==s[j] else max(d[i+1][j],d[i][j-1])
    return d[0][-1]
def edit_script(a,b):
    n,m=len(a),len(b);d=[[0]*(m+1) for _ in range(n+1)]
    for i in range(n+1):d[i][0]=i
    for j in range(m+1):d[0][j]=j
    for i in range(1,n+1):
        for j in range(1,m+1):d[i][j]=min(d[i-1][j]+1,d[i][j-1]+1,d[i-1][j-1]+(a[i-1]!=b[j-1]))
    i,j=n,m;out=[]
    while i or j:
        if i and j and a[i-1]==b[j-1]:i-=1;j-=1
        elif i and j and d[i][j]==d[i-1][j-1]+1:out.append(('replace',a[i-1],b[j-1]));i-=1;j-=1
        elif i and d[i][j]==d[i-1][j]+1:out.append(('delete',a[i-1]));i-=1
        else:out.append(('insert',b[j-1]));j-=1
    return out[::-1]
def otsu(values):
    x=sorted(values)
    if not x or any(type(v) is not int for v in x):raise ValueError('integer sample')
    total=sum(x);prefix=0;best=-1;threshold=x[0]
    for i,v in enumerate(x[:-1],1):
        prefix+=v
        if v==x[i]:continue
        score=i*(len(x)-i)*(prefix/i-(total-prefix)/(len(x)-i))**2
        if score>best:best=score;threshold=v
    return threshold
def _points(x):
    if not x or not x[0] or any(len(v)!=len(x[0]) or any(not math.isfinite(w) for w in v) for v in x):raise ValueError('invalid points')
def _dist(x,y):return sum((u-v)**2 for u,v in zip(x,y))
def dbscan(x,eps,min_pts):
    _points(x)
    if eps<0 or type(min_pts) is not int or min_pts<1:raise ValueError('invalid parameters')
    labels=[-2]*len(x);cluster=0
    def neighbors(i):return [j for j,v in enumerate(x) if _dist(x[i],v)<=eps*eps]
    for i in range(len(x)):
        if labels[i]!=-2:continue
        ns=neighbors(i)
        if len(ns)<min_pts:labels[i]=-1;continue
        labels[i]=cluster;q=deque(ns);queued=set(ns)
        while q:
            j=q.popleft()
            if labels[j]==-1:labels[j]=cluster
            if labels[j]!=-2:continue
            labels[j]=cluster;near=neighbors(j)
            if len(near)>=min_pts:
                for k in near:
                    if k not in queued:queued.add(k);q.append(k)
        cluster+=1
    return labels
def kmeans(x,centers,steps=100):
    _points(x);_points(centers)
    if len(x[0])!=len(centers[0]):raise ValueError('geometry')
    centers=[list(v) for v in centers]
    for _ in range(steps):
        labels=[min(range(len(centers)),key=lambda j:_dist(v,centers[j])) for v in x]
        out=[]
        for j,c in enumerate(centers):
            rows=[v for v,l in zip(x,labels) if l==j]
            out.append([sum(col)/len(rows) for col in zip(*rows)] if rows else c)
        if out==centers:return centers,labels
        centers=out
    return centers,[min(range(len(centers)),key=lambda j:_dist(v,centers[j])) for v in x]
def entropy(counts):
    if any(not math.isfinite(v) or v<0 for v in counts) or not sum(counts)>0:raise ValueError('distribution')
    s=sum(counts);return -sum(v/s*math.log2(v/s) for v in counts if v)
def mutual_information(table):
    _points(table)
    if any(v<0 for r in table for v in r):raise ValueError('negative count')
    rows=[sum(r) for r in table];cols=[sum(c) for c in zip(*table)];n=sum(rows)
    if n<=0:raise ValueError('empty distribution')
    return sum(v/n*math.log2(v*n/(rows[i]*cols[j])) for i,r in enumerate(table) for j,v in enumerate(r) if v)
def bayes(prior,likelihood):
    if not prior or len(prior)!=len(likelihood) or any(not math.isfinite(v) or not 0<=v<=1 for v in list(prior)+list(likelihood)):raise ValueError('probability')
    v=[p*l for p,l in zip(prior,likelihood)];s=sum(v)
    if s<=0:raise ValueError('impossible evidence')
    return [p/s for p in v]
def _hmm(prior,t,e,obs):
    n=len(prior)
    if not n or not obs or len(t)!=n or len(e)!=n or any(len(r)!=n for r in t) or not e[0] or any(len(r)!=len(e[0]) for r in e) or any(type(o) is not int or not 0<=o<len(e[0]) for o in obs):raise ValueError('hmm geometry')
    if any(not math.isfinite(v) or not 0<=v<=1 for r in [prior]+list(t)+list(e) for v in r):raise ValueError('probability')
def viterbi(prior,t,e,obs):
    _hmm(prior,t,e,obs);n=len(prior);log=lambda x:math.log(x) if x else -math.inf
    p=[log(prior[i])+log(e[i][obs[0]]) for i in range(n)];paths=[[i] for i in range(n)]
    for o in obs[1:]:
        q=[];new=[]
        for j in range(n):
            i=max(range(n),key=lambda i:(round(p[i]+log(t[i][j]),14),-i))
            q.append(p[i]+log(t[i][j])+log(e[j][o]));new.append(paths[i]+[j])
        p=q;paths=new
    return paths[max(range(n),key=lambda i:(round(p[i],14),-i))]
def forward(prior,t,e,obs):
    _hmm(prior,t,e,obs);n=len(prior);p=[prior[i]*e[i][obs[0]] for i in range(n)]
    for o in obs[1:]:p=[sum(p[i]*t[i][j] for i in range(n))*e[j][o] for j in range(n)]
    return sum(p)
def newton(f,df,x,tol=1e-10,steps=100):
    for _ in range(steps):
        y=f(x)
        if abs(y)<tol:return x
        d=df(x)
        if not math.isfinite(d) or d==0:raise ValueError('singular derivative')
        x-=y/d
        if not math.isfinite(x):raise ValueError('nonfinite iterate')
    raise ValueError('not converged')
def trapezoid(f,a,b,n):
    if type(n) is not int or not 1<=n<=1000000:raise ValueError('partition')
    h=(b-a)/n;return h*(.5*(f(a)+f(b))+sum(f(a+i*h) for i in range(1,n)))
def gauss_jordan(a,b):
    n=len(b)
    if not n or len(a)!=n or any(len(r)!=n for r in a):raise ValueError('geometry')
    m=[list(r)+[v] for r,v in zip(a,b)]
    for j in range(n):
        i=max(range(j,n),key=lambda i:abs(m[i][j]))
        if abs(m[i][j])<1e-14:raise ValueError('singular matrix')
        m[i],m[j]=m[j],m[i];p=m[j][j];m[j]=[v/p for v in m[j]]
        for i in range(n):
            if i!=j:
                p=m[i][j];m[i]=[v-p*w for v,w in zip(m[i],m[j])]
    return [r[-1] for r in m]
def poly_eval(coefficients,x):
    y=0
    for c in coefficients:y=y*x+c
    return y
def ema(values,alpha):
    if not 0<alpha<=1:raise ValueError('alpha')
    out=[]
    for v in values:out.append(v if not out else alpha*v+(1-alpha)*out[-1])
    return out
def ljung_box(values,lag):
    a=list(values);n=len(a)
    if type(lag) is not int or not 1<=lag<n:raise ValueError('lag')
    mean=sum(a)/n;b=[v-mean for v in a];den=sum(v*v for v in b)
    if den==0:raise ValueError('constant sequence')
    return n*(n+2)*sum((sum(b[i]*b[i-k] for i in range(k,n))/den)**2/(n-k) for k in range(1,lag+1))
REGISTRY={f.__name__:f for f in (bridges,pagerank,components,longest_palindromic_subsequence,edit_script,otsu,dbscan,kmeans,entropy,mutual_information,bayes,viterbi,forward,newton,trapezoid,gauss_jordan,poly_eval,ema,ljung_box)}
