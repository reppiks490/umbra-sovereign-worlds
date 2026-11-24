"""32 independent executable reference algorithms; no parameter-variant inflation."""
import cmath,heapq,math,random,statistics
from collections import deque
from bisect import bisect_right
def scc(g):
    order=[];seen=set()
    def dfs(u):
        seen.add(u)
        for v in g[u]:
            if v not in g:raise ValueError('unknown vertex')
            if v not in seen:dfs(v)
        order.append(u)
    for u in g:
        if u not in seen:dfs(u)
    rev={u:[] for u in g}
    for u in g:
        for v in g[u]:rev[v].append(u)
    seen.clear();out=[]
    def visit(u,c):
        seen.add(u);c.add(u)
        for v in rev[u]:
            if v not in seen:visit(v,c)
    for u in reversed(order):
        if u not in seen:
            c=set();visit(u,c);out.append(c)
    return list(reversed(out))
def astar(g,start,end,h):
    if start not in g or end not in g:raise ValueError('unknown vertex')
    if any(v not in g or not math.isfinite(w) or w<0 for edges in g.values() for v,w in edges.items()):raise ValueError('invalid edges')
    dist={start:0};prev={};q=[(h(start),0,0,start)];counter=0
    while q:
        _,cost,_,u=heapq.heappop(q)
        if cost!=dist[u]:continue
        if u==end:
            path=[u]
            while u!=start:u=prev[u];path.append(u)
            return cost,path[::-1]
        for v,w in g[u].items():
            n=cost+w
            if n<dist.get(v,math.inf):
                dist[v]=n;prev[v]=u;counter+=1;heapq.heappush(q,(n+h(v),n,counter,v))
    return math.inf,[]
def hopcroft_karp(g):
    left={};right={};dist={}
    def bfs():
        q=deque();found=False
        for u in g:
            dist[u]=0 if u not in left else math.inf
            if u not in left:q.append(u)
        while q:
            u=q.popleft()
            for v in g[u]:
                if v not in right:found=True
                elif dist[right[v]]==math.inf:dist[right[v]]=dist[u]+1;q.append(right[v])
        return found
    def dfs(u):
        for v in g[u]:
            if v not in right or (dist[right[v]]==dist[u]+1 and dfs(right[v])):
                left[u]=v;right[v]=u;return True
        dist[u]=math.inf;return False
    while bfs():
        for u in g:
            if u not in left:dfs(u)
    return left
def hungarian(m):
    n=len(m)
    if not n or any(len(r)!=n or any(not math.isfinite(x) for x in r) for r in m):raise ValueError('square finite cost matrix required')
    u=[0]*(n+1);v=[0]*(n+1);p=[0]*(n+1);way=[0]*(n+1)
    for i in range(1,n+1):
        p[0]=i;j0=0;minv=[math.inf]*(n+1);used=[False]*(n+1)
        while True:
            used[j0]=True;i0=p[j0];delta=math.inf;j1=0
            for j in range(1,n+1):
                if used[j]:continue
                cur=m[i0-1][j-1]-u[i0]-v[j]
                if cur<minv[j]:minv[j]=cur;way[j]=j0
                if minv[j]<delta:delta=minv[j];j1=j
            for j in range(n+1):
                if used[j]:u[p[j]]+=delta;v[j]-=delta
                else:minv[j]-=delta
            j0=j1
            if p[j0]==0:break
        while j0:
            j1=way[j0];p[j0]=p[j1];j0=j1
    assignment=[0]*n
    for j in range(1,n+1):assignment[p[j]-1]=j-1
    return sum(m[i][j] for i,j in enumerate(assignment)),assignment
def weighted_intervals(intervals):
    a=sorted(intervals,key=lambda x:x[1]);ends=[v[1] for v in a];dp=[0];take=[]
    for i,(s,e,w) in enumerate(a):
        if e<s:raise ValueError('reversed interval')
        j=bisect_right(ends,s,0,i);take.append(j);dp.append(max(dp[-1],dp[j]+w))
    out=[];i=len(a)
    while i:
        j=take[i-1]
        if dp[i]>dp[i-1]:out.append(a[i-1]);i=j
        else:i-=1
    return dp[-1],out[::-1]
def stable_matching(proposers,receivers):
    n=len(proposers)
    if len(receivers)!=n or any(sorted(r)!=list(range(n)) for r in list(proposers)+list(receivers)):raise ValueError('complete preferences required')
    ranks=[{p:i for i,p in enumerate(r)} for r in receivers];next_=[0]*n;held={};q=deque(range(n))
    while q:
        p=q.popleft();r=proposers[p][next_[p]];next_[p]+=1
        old=held.get(r)
        if old is None or ranks[r][p]<ranks[r][old]:
            held[r]=p
            if old is not None:q.append(old)
        else:q.append(p)
    out=[None]*n
    for r,p in held.items():out[p]=r
    return out
def aho_corasick(text,patterns):
    go=[{}];fail=[0];out=[[]]
    for p in patterns:
        if not p:raise ValueError('empty pattern')
        s=0
        for c in p:
            if c not in go[s]:go[s][c]=len(go);go.append({});fail.append(0);out.append([])
            s=go[s][c]
        out[s].append(p)
    q=deque(go[0].values())
    while q:
        r=q.popleft()
        for c,s in go[r].items():
            q.append(s);f=fail[r]
            while f and c not in go[f]:f=fail[f]
            fail[s]=go[f].get(c,0);out[s].extend(out[fail[s]])
    s=0;matches=[]
    for i,c in enumerate(text):
        while s and c not in go[s]:s=fail[s]
        s=go[s].get(c,0)
        matches.extend((i-len(p)+1,p) for p in out[s])
    return sorted(matches,key=lambda x:(x[0],len(x[1]),x[1]))
def dtw(a,b):
    p=[0]+[math.inf]*len(b)
    for x in a:
        r=[math.inf]
        for j,y in enumerate(b):r.append(abs(x-y)+min(r[-1],p[j],p[j+1]))
        p=r
    return p[-1]
def inversions(a):
    def rec(x):
        if len(x)<2:return x,0
        k=len(x)//2;l,c=rec(x[:k]);r,d=rec(x[k:]);i=j=0;out=[];n=c+d
        while i<len(l) and j<len(r):
            if l[i]<=r[j]:out.append(l[i]);i+=1
            else:out.append(r[j]);j+=1;n+=len(l)-i
        return out+l[i:]+r[j:],n
    return rec(list(a))[1]
def radix_sort(a):
    a=list(a)
    if any(type(v) is not int or v<0 for v in a):raise ValueError('nonnegative integers required')
    p=1
    while p<=max(a,default=0):
        buckets=[[] for _ in range(10)]
        for v in a:buckets[v//p%10].append(v)
        a=[v for b in buckets for v in b];p*=10
    return a
def counting_sort(a):
    a=list(a)
    if not a:return []
    if any(type(v) is not int for v in a) or max(a)-min(a)>1000000:raise ValueError('bounded integer range required')
    lo=min(a);counts=[0]*(max(a)-lo+1)
    for v in a:counts[v-lo]+=1
    return [i+lo for i,n in enumerate(counts) for _ in range(n)]
def manacher(s):
    a=[None]
    for c in s:a.extend((c,None))
    p=[0]*len(a);center=right=0;best=(0,0)
    for i in range(len(a)):
        if i<right:p[i]=min(right-i,p[2*center-i])
        while i-p[i]-1>=0 and i+p[i]+1<len(a) and a[i-p[i]-1]==a[i+p[i]+1]:p[i]+=1
        if i+p[i]>right:center,right=i,i+p[i]
        start=(i-p[i])//2
        if p[i]>best[1]:best=(start,p[i])
    return best
def z_search(text,pattern):
    if not pattern:raise ValueError('empty pattern')
    s=list(pattern)+[object()]+list(text);z=[0]*len(s);l=r=0
    for i in range(1,len(s)):
        if i<=r:z[i]=min(r-i+1,z[i-l])
        while i+z[i]<len(s) and s[z[i]]==s[i+z[i]]:z[i]+=1
        if i+z[i]-1>r:l,r=i,i+z[i]-1
    return [i-len(pattern)-1 for i in range(len(pattern)+1,len(s)) if z[i]>=len(pattern)]
def logsumexp(values):
    a=list(values)
    if not a:return -math.inf
    m=max(a)
    if math.isinf(m):return m
    return m+math.log(sum(math.exp(x-m) for x in a))
def kahan(values):
    s=c=0.
    for x in values:
        y=x-c;t=s+y;c=(t-s)-y;s=t
    return s
def cholesky(a):
    n=len(a)
    if not n or any(len(r)!=n for r in a) or any(not math.isfinite(a[i][j]) or abs(a[i][j]-a[j][i])>1e-12 for i in range(n) for j in range(n)):raise ValueError('symmetric finite matrix required')
    l=[[0.]*n for _ in range(n)]
    for i in range(n):
        for j in range(i+1):
            v=a[i][j]-sum(l[i][k]*l[j][k] for k in range(j))
            if i==j:
                if v<=0:raise ValueError('not positive definite')
                l[i][j]=math.sqrt(v)
            else:l[i][j]=v/l[j][j]
    return l
def conjugate_gradient(a,b,tol=1e-10):
    n=len(b)
    if not n or len(a)!=n or any(len(r)!=n for r in a):raise ValueError('invalid geometry')
    x=[0.]*n;r=list(b);p=list(r);rr=sum(v*v for v in r)
    for _ in range(max(1,n*4)):
        if rr<=tol*tol:return x
        ap=[sum(v*w for v,w in zip(row,p)) for row in a];den=sum(v*w for v,w in zip(p,ap))
        if den<=0:raise ValueError('not positive definite')
        alpha=rr/den;x=[v+alpha*w for v,w in zip(x,p)];r=[v-alpha*w for v,w in zip(r,ap)]
        new=sum(v*v for v in r);p=[v+new/rr*w for v,w in zip(r,p)];rr=new
    if rr>tol*tol:raise ValueError('not converged')
    return x
def fft(values):
    a=list(values);n=len(a)
    if not n or n&(n-1):raise ValueError('power of two required')
    if n==1:return [complex(a[0])]
    e=fft(a[::2]);o=fft(a[1::2]);w=[cmath.exp(-2j*math.pi*k/n)*o[k] for k in range(n//2)]
    return [v+t for v,t in zip(e,w)]+[v-t for v,t in zip(e,w)]
def goertzel(values,k):
    a=list(values);n=len(a)
    if not n or type(k) is not int or not 0<=k<n:raise ValueError('invalid bin')
    c=2*math.cos(2*math.pi*k/n);s1=s2=0.
    for x in a:s1,s2=x+c*s1-s2,s1
    return s1*s1+s2*s2-c*s1*s2
def pava(values):
    blocks=[]
    for x in values:
        blocks.append([float(x),1])
        while len(blocks)>1 and blocks[-2][0]/blocks[-2][1]>blocks[-1][0]/blocks[-1][1]:
            b=blocks.pop();blocks[-1][0]+=b[0];blocks[-1][1]+=b[1]
    return [s/n for s,n in blocks for _ in range(n)]
def huber_location(values,delta):
    a=list(values)
    if not a or delta<=0:raise ValueError('invalid sample')
    lo=min(a);hi=max(a)
    for _ in range(100):
        mid=(lo+hi)/2;g=sum(max(-delta,min(delta,x-mid)) for x in a)
        if g>0:lo=mid
        else:hi=mid
    return (lo+hi)/2
def hampel(values,radius,threshold=3):
    a=list(values)
    if radius<1 or threshold<=0:raise ValueError('invalid window')
    out=[]
    for i,x in enumerate(a):
        w=a[max(0,i-radius):i+radius+1];m=statistics.median(w);mad=statistics.median(abs(y-m) for y in w)
        out.append(m if abs(x-m)>threshold*1.4826*mad else x)
    return out
def page_hinkley(values,delta,threshold):
    if delta<0 or threshold<=0:raise ValueError('invalid parameters')
    mu=total=low=0.;n=0;out=[]
    for i,x in enumerate(values):
        n+=1;mu+=(x-mu)/n;total+=x-mu-delta;low=min(low,total)
        if total-low>threshold:out.append(i);mu=total=low=0.;n=0
    return out
def ewma_variance(values,alpha):
    if not 0<alpha<=1:raise ValueError('invalid alpha')
    a=list(values)
    if not a:raise ValueError('empty')
    v=a[0]**2
    for x in a[1:]:v=(1-alpha)*v+alpha*x*x
    return v
def roc_auc(labels,scores):
    if len(labels)!=len(scores) or any(x not in (0,1) for x in labels):raise ValueError('invalid binary labels')
    p=[x for x,y in zip(scores,labels) if y];n=[x for x,y in zip(scores,labels) if not y]
    if not p or not n:raise ValueError('both classes required')
    return sum((x>y)+.5*(x==y) for x in p for y in n)/(len(p)*len(n))
def kaplan_meier(records):
    a=list(records)
    if any(t<0 or e not in (0,1) for t,e in a):raise ValueError('invalid observation')
    risk=len(a);s=1.;out=[]
    for t in sorted({t for t,e in a}):
        group=[e for u,e in a if u==t];deaths=sum(group)
        if deaths:s*= (risk-deaths)/risk;out.append((t,s))
        risk-=len(group)
    return out
def bh(p,alpha):
    if not 0<alpha<1 or any(not 0<=x<=1 for x in p):raise ValueError('invalid probability')
    a=sorted(enumerate(p),key=lambda x:x[1]);k=0
    for i,(_,v) in enumerate(a,1):
        if v<=alpha*i/len(a):k=i
    return sorted(i for i,_ in a[:k])
def wilson(wins,n,z=1.959963984540054):
    if type(n) is not int or n<1 or not 0<=wins<=n or z<=0:raise ValueError('invalid sample')
    p=wins/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;r=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return max(0,c-r),min(1,c+r)
def reservoir(values,k,seed):
    if type(k) is not int or k<0:raise ValueError('invalid capacity')
    rng=random.Random(seed);out=[]
    for i,v in enumerate(values):
        if i<k:out.append(v)
        else:
            j=rng.randrange(i+1)
            if j<k:out[j]=v
    return out
def bootstrap_mean(values,n,seed):
    a=list(values)
    if not a or not 1<=n<=100000:raise ValueError('invalid bootstrap')
    r=random.Random(seed);v=sorted(statistics.mean(r.choices(a,k=len(a))) for _ in range(n))
    return v[int(.025*(n-1))],v[int(.975*(n-1))]
def permutation_difference(a,b,n,seed):
    if not a or not b or not 1<=n<=100000:raise ValueError('invalid sample')
    obs=abs(statistics.mean(a)-statistics.mean(b));pool=list(a)+list(b);r=random.Random(seed);count=1
    for _ in range(n):
        r.shuffle(pool);count+=abs(statistics.mean(pool[:len(a)])-statistics.mean(pool[len(a):]))>=obs
    return count/(n+1)
def miller_rabin(n):
    if type(n) is not int or not 0<=n<2**64:raise ValueError('unsigned 64 bit integer required')
    if n<2:return False
    for p in (2,3,5,7,11,13,17,19,23,29,31,37):
        if n%p==0:return n==p
    d=n-1;s=0
    while d%2==0:d//=2;s+=1
    for a in (2,325,9375,28178,450775,9780504,1795265022):
        if a%n==0:continue
        x=pow(a,d,n)
        if x in (1,n-1):continue
        for _ in range(s-1):
            x=x*x%n
            if x==n-1:break
        else:return False
    return True
def extended_gcd(a,b):
    r,s=a,b;x,y=1,0;u,v=0,1
    while s:
        q=r//s;r,s=s,r-q*s;x,y=y,x-q*y;u,v=v,u-q*v
    return (r,x,u) if r>=0 else (-r,-x,-u)
def modular_power(a,e,m):
    if type(e) is not int or e<0 or m<=0:raise ValueError('invalid exponent/modulus')
    a%=m;r=1%m
    while e:
        if e&1:r=r*a%m
        a=a*a%m;e>>=1
    return r
REGISTRY={f.__name__:f for f in (scc,astar,hopcroft_karp,hungarian,weighted_intervals,stable_matching,aho_corasick,dtw,inversions,radix_sort,counting_sort,manacher,z_search,logsumexp,kahan,cholesky,conjugate_gradient,fft,goertzel,pava,huber_location,hampel,page_hinkley,ewma_variance,roc_auc,kaplan_meier,bh,wilson,reservoir,bootstrap_mean,permutation_difference,miller_rabin,extended_gcd,modular_power)}
