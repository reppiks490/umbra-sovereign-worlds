"""Bounded deterministic numerical tools; no inference, no trades, no remote code."""
import argparse,hashlib,heapq,json,math,statistics,time
from fractions import Fraction
from pathlib import Path
LANES=('forecast','stratified_effect','rational','shortest_path','knapsack','bayes')
def number(x):
 if type(x) not in (int,float) or not math.isfinite(x) or abs(x)>1e12:raise ValueError('finite bounded number required')
 return x
def integer(x,low,high):
 if type(x) is not int or not low<=x<=high:raise ValueError('bounded integer required')
 return x
def sequence(x,lo,hi):
 if not isinstance(x,list) or not lo<=len(x)<=hi:raise ValueError('bounded sequence required')
 return x
def label(x):
 if not isinstance(x,str) or not 0<len(x)<=80:raise ValueError('invalid label')
 return x
def execute(lane,p):
 if not isinstance(p,dict):raise ValueError('object required')
 if lane=='forecast':
  a=[number(x) for x in sequence(p['train'],2,4096)];h=integer(p['horizon'],1,256);d=(a[-1]-a[0])/(len(a)-1)
  return {'prediction':[a[-1]+d*i for i in range(1,h+1)],'persistence':[a[-1]]*h,'method':'endpoint_drift'}
 if lane=='stratified_effect':
  groups={};allarms=[[],[]]
  for g,t,y in sequence(p['rows'],2,4096):
   g=label(g);t=integer(t,0,1);y=number(y)
   groups.setdefault(g,[[],[]])[t].append(y);allarms[t].append(y)
  if any(not a or not b for a,b in groups.values()):raise ValueError('positivity violation')
  n=sum(len(a)+len(b) for a,b in groups.values())
  return {'estimate':sum((len(a)+len(b))*(statistics.mean(b)-statistics.mean(a)) for a,b in groups.values())/n,'naive':statistics.mean(allarms[1])-statistics.mean(allarms[0]),'assumptions':'observed strata sufficient; no empirical causal identification claimed'}
 if lane=='rational':
  total=Fraction(0)
  for a,b in sequence(p['terms'],1,128):total+=Fraction(integer(a,-1000000,1000000),integer(b,1,1000000))
  return {'value':str(total)}
 if lane=='shortest_path':
  source=label(p['source']);target=label(p['target']);adj={}
  for a,b,w in sequence(p['edges'],1,4096):
   a=label(a);b=label(b);w=number(w)
   if w<0:raise ValueError('negative edge')
   adj.setdefault(a,[]).append((b,w))
  q=[(0,source)];dist={source:0}
  while q:
   cost,v=heapq.heappop(q)
   if cost!=dist[v]:continue
   if v==target:return {'cost':cost}
   for u,w in adj.get(v,[]):
    if cost+w<dist.get(u,math.inf):dist[u]=cost+w;heapq.heappush(q,(cost+w,u))
  return {'cost':None}
 if lane=='knapsack':
  c=integer(p['capacity'],0,4096);dp=[0]*(c+1)
  for w,v in sequence(p['items'],1,128):
   w=integer(w,1,4096);v=integer(v,0,1000000)
   for j in range(c,w-1,-1):dp[j]=max(dp[j],dp[j-w]+v)
  return {'value':dp[c]}
 if lane=='bayes':
  a,b,c=(number(p[k]) for k in ('prior','sensitivity','false_positive'))
  if any(not 0<=x<=1 for x in (a,b,c)) or a*b+(1-a)*c==0:raise ValueError('invalid evidence probability')
  return {'posterior':a*b/(a*b+(1-a)*c)}
 raise ValueError('unknown lane')
CASES={
 'forecast':[({'train':[2,4,6,8],'horizon':2},'prediction',[10,12]),({'train':[5,5],'horizon':1},'prediction',[5]),({'train':[10,7,4],'horizon':2},'prediction',[1,-2])],
 'stratified_effect':[({'rows':[['a',0,1],['a',1,3],['b',0,5],['b',1,7]]},'estimate',2),({'rows':[['a',0,1],['a',1,1]]},'estimate',0),({'rows':[['a',0,4],['a',1,1],['b',0,12],['b',1,9]]},'estimate',-3)],
 'rational':[({'terms':[[1,2],[1,3]]},'value','5/6'),({'terms':[[1,3],[-1,3]]},'value','0'),({'terms':[[5,2],[1,2]]},'value','3')],
 'shortest_path':[({'edges':[['a','b',9],['a','c',1],['c','b',3]],'source':'a','target':'b'},'cost',4),({'edges':[['a','b',1]],'source':'b','target':'a'},'cost',None),({'edges':[['a','b',0]],'source':'a','target':'b'},'cost',0)],
 'knapsack':[({'items':[[2,3],[3,4],[4,5]],'capacity':5},'value',7),({'items':[[1,6],[2,10],[3,12]],'capacity':5},'value',22),({'items':[[2,9]],'capacity':1},'value',0)],
 'bayes':[({'prior':.1,'sensitivity':.9,'false_positive':.1},'posterior',.5),({'prior':.4,'sensitivity':.5,'false_positive':.5},'posterior',.4),({'prior':.5,'sensitivity':1,'false_positive':0},'posterior',1)]}
def benchmark():
 start=time.monotonic();lanes={}
 for lane,cases in CASES.items():
  passed=0;results=[]
  for data,key,expected in cases:
   actual=execute(lane,data)[key]
   ok=math.isclose(actual,expected,rel_tol=1e-10,abs_tol=1e-10) if type(actual) in (int,float) and type(expected) in (int,float) else actual==expected
   passed+=ok;results.append({'actual':actual,'expected':expected,'passed':ok})
  lanes[lane]={'cases':len(cases),'passed':passed,'results':results}
 return {'schema':'umbra.campaign.baselines.v1','scope':'deterministic synthetic reference cases only','lanes':lanes,'case_sha256':hashlib.sha256(json.dumps(CASES,sort_keys=True).encode()).hexdigest(),'elapsed_seconds':time.monotonic()-start,'neural_inference_verified':False,'training_verified':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path);a=p.parse_args();r=benchmark()
 if a.output:
  a.output.parent.mkdir(parents=True,exist_ok=True);tmp=a.output.with_suffix('.tmp');tmp.write_text(json.dumps(r,indent=2),encoding='utf8');tmp.replace(a.output)
 print(json.dumps(r))
 if any(v['passed']!=v['cases'] for v in r['lanes'].values()):raise SystemExit(1)
