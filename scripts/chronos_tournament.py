"""Synthetic walk-forward strategy tournaments. No broker or live trading interface."""
import argparse,dataclasses,hashlib,json,math,random,statistics
from pathlib import Path
@dataclasses.dataclass(frozen=True)
class Config:
 mode:str
 lookback:int
 threshold:float
def validate(prices,c,start,end,bps):
 if not isinstance(prices,list) or not 3<=len(prices)<=8192 or any(type(x) not in (float,int) or not math.isfinite(x) or not 0<x<=1e12 for x in prices):raise ValueError('prices')
 if c.mode not in ('trend','reversion','flat') or type(c.lookback) is not int or not 2<=c.lookback<=128 or not 0<=c.threshold<=.1:raise ValueError('configuration')
 if type(start) is not int or type(end) is not int or not c.lookback<=start<end<=len(prices) or type(bps) not in (int,float) or not 0<=bps<=200:raise ValueError('range or costs')
def simulate(prices,c,start,end,bps):
 validate(prices,c,start,end,bps)
 equity=gross=peak=1.;drawdown=cost=0.;pos=0;positions=[];trades=[];net_steps=[]
 fee=bps/10000
 # A close at i-1 is observable; change position only at close i.
 # The new position earns close-i to close-(i+1), never the prior move.
 for i in range(start,end):
  before=equity
  r=prices[i]/prices[i-1]-1
  factor=1+pos*r
  if factor<=0:raise ValueError('insolvency under unit position')
  equity*=factor;gross*=factor
  delta=prices[i-1]/prices[i-c.lookback]-1
  signal=0 if c.mode=='flat' or abs(delta)<=c.threshold else (1 if delta>0 else -1)*(1 if c.mode=='trend' else -1)
  if i==end-1:signal=0
  turnover=abs(signal-pos)
  if turnover:
   charge=equity*turnover*fee;equity-=charge;cost+=charge
   trades.append({'signal_index':i-1,'fill_index':i,'old':pos,'new':signal,'cost':charge})
  pos=signal;positions.append(pos);peak=max(peak,equity);drawdown=max(drawdown,1-equity/peak)
  net_steps.append(equity/before-1)
 return {'net_return':equity-1,'gross_return':gross-1,'cost':cost,'max_drawdown':drawdown,'turnovers':len(trades),'trades':trades,'positions':positions,'mean_step':statistics.mean(net_steps)}
def synthetic(seed,regime,n):
 if regime not in ('trend','reversal','noise','shock') or type(n) is not int or not 64<=n<=8192:raise ValueError('synthetic config')
 rng=random.Random(seed);a=[100.]
 for i in range(1,n):
  drift={'trend':.001,'reversal':.0015 if (i//30)%2==0 else -.0015,'noise':0,'shock':.0003}[regime]
  if regime=='shock' and i in (n//3,3*n//4):drift=-.08
  a.append(a[-1]*math.exp(drift+rng.gauss(0,.004)))
 return a
def compact(r):return {k:v for k,v in r.items() if k not in ('trades','positions')}
def score(r):return r['net_return']-1.5*r['max_drawdown']
def tournament(prices,split,bps=10):
 if type(split) is not int or not 80<=split<=len(prices)-16:raise ValueError('split')
 configs=[Config('flat',2,0)]+[Config(m,w,t) for m in ('trend','reversion') for w in (2,4,8,16,32) for t in (0,.002,.005)]
 # Three chronological pre-holdout validation slices; flat starts and liquidations.
 edges=[32,32+(split-32)//3,32+2*(split-32)//3,split]
 scored=[]
 for c in configs:
  folds=[simulate(prices,c,a,b,bps) for a,b in zip(edges,edges[1:])]
  scored.append((statistics.mean(score(x) for x in folds),c))
 best,c=max(scored,key=lambda z:(z[0],z[1].mode=='flat',-z[1].lookback,-z[1].threshold))
 hold=simulate(prices,c,split,len(prices),bps)
 return {'selected':dataclasses.asdict(c),'selection_score':best,'candidate_count':len(configs),'validation_folds':3,'split':split,'holdout':compact(hold),'flat_holdout':compact(simulate(prices,Config('flat',2,0),split,len(prices),bps)),'cost_stress':[{'bps':v,**compact(simulate(prices,c,split,len(prices),v))} for v in (bps,min(200,bps*2),min(200,bps*4))],'synthetic_only':True,'production_authority':False}
def campaign(seed):
 rows=[]
 for j,r in enumerate(('trend','reversal','noise','shock')):
  for k in range(4):
   data=synthetic(seed+100*j+k,r,256)
   rows.append({'regime':r,'seed':seed+100*j+k,**tournament(data,192,10)})
 return {'schema':'umbra.chronos.tournament.v1','seed':seed,'scope':'synthetic close-to-close fills; not empirical or live','episodes':len(rows),'candidates_per_episode':31,'holdout_positive':sum(x['holdout']['net_return']>0 for x in rows),'holdout_negative':sum(x['holdout']['net_return']<0 for x in rows),'holdout_flat':sum(x['holdout']['net_return']==0 for x in rows),'mean_holdout_net':statistics.mean(x['holdout']['net_return'] for x in rows),'rows':rows,'synthetic_only':True,'production_authority':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--seed',type=int,required=True);p.add_argument('--output',type=Path);a=p.parse_args();r=campaign(a.seed)
 if a.output:
  a.output.parent.mkdir(parents=True,exist_ok=True);tmp=a.output.with_suffix('.tmp');tmp.write_text(json.dumps(r,indent=2),encoding='utf8');tmp.replace(a.output)
 print(json.dumps({k:v for k,v in r.items() if k!='rows'}))
