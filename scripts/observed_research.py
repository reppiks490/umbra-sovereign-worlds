"""Bounded chronological statistical research using existing pinned observed datasets."""
import argparse,csv,datetime,hashlib,io,json,math,statistics
from pathlib import Path
from source_knowledge import git
def positive(x):
 v=float(x)
 if not math.isfinite(v) or not 0<v<=1e12:raise ValueError('invalid positive value')
 return v
def parse_airline(raw):
 r=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
 if r.fieldnames!=['Date','Passengers']:raise ValueError('schema')
 out=[];prior=None
 for row in r:
  t=datetime.datetime.strptime(row['Date'],'%Y-%m');month=t.year*12+t.month
  if prior is not None and month!=prior+1:raise ValueError('month order')
  prior=month;out.append(positive(row['Passengers']))
 return out
def parse_market(raw):
 r=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
 if r.fieldnames!=['timestamps','open','close','high','low','volume','amount']:raise ValueError('market schema')
 out=[];prior=None;first=None
 for row in r:
  t=datetime.datetime.strptime(row['timestamps'],'%Y/%m/%d %H:%M')
  if prior is not None and t<=prior:raise ValueError('timestamp order')
  first=first or t;prior=t
  o,c,h,l=[positive(row[k]) for k in ('open','close','high','low')]
  if l>min(o,c) or h<max(o,c) or l>h:raise ValueError('OHLC bounds')
  if any(not math.isfinite(float(row[k])) or float(row[k])<0 for k in ('volume','amount')):raise ValueError('quantity bounds')
  out.append(c)
 if not out:raise ValueError('empty data')
 return out,{'first':first.isoformat(),'last':prior.isoformat(),'timezone':'unspecified in source'}
def evaluate(values,split,lag):
 if not 20<=split<=len(values)-5 or not 1<=lag<=12 or len(values)>200000 or any(not math.isfinite(x) or x<=0 for x in values):raise ValueError('data budget')
 fit_end=int(split*.75)
 if fit_end<lag+3:raise ValueError('insufficient fitting rows')
 # Fit only the earlier observed prices; one-step changes are predicted from prior observed lagged changes.
 def fit(n):
  x=[values[i-1]/values[i-1-lag]-1 for i in range(lag+1,n)]
  y=[values[i]/values[i-1]-1 for i in range(lag+1,n)]
  xm,ym=statistics.mean(x),statistics.mean(y)
  a=sum((u-xm)*(v-ym) for u,v in zip(x,y))/(sum((u-xm)**2 for u in x)+1e-8)
  return (ym-a*xm,a)
 def pred(i,c,coef):
  if c=='persistence':return values[i-1]
  if c=='seasonal':return values[i-lag]
  if c=='drift':return values[i-1]*(1+coef[0])
  return values[i-1]*(1+coef[0]+coef[1]*(values[i-1]/values[i-1-lag]-1))
 def metric(start,end,c,coef):
  errs=[abs(pred(i,c,coef)-values[i]) for i in range(start,end)]
  return statistics.mean(errs)
 candidates=['persistence','seasonal','drift','lagged_return_ols'];coef=fit(fit_end)
 scores={c:metric(fit_end,split,c,coef) for c in candidates}
 selected=min(candidates,key=lambda c:(scores[c],candidates.index(c)))
 final=fit(split)
 test={c:metric(split,len(values),c,final) for c in candidates}
 return {'selected':selected,'selection_mae':scores[selected],'holdout_mae':test[selected],'holdout_persistence_mae':test['persistence'],'holdout_candidates':test,'validation_candidates':scores,'fit_coefficients':list(final),'fit_digest':hashlib.sha256(json.dumps([values[:split],lag,final],separators=(',',':')).encode()).hexdigest(),'observations':len(values),'initial_fit_rows':fit_end,'preholdout_rows':split,'holdout_rows':len(values)-split,'scope':'one-step observed-history forecasts; not trading profitability','neural_weight_training':False,'production_authority':False}
def read_pinned(repo,rev,path,max_bytes):
 ref=rev+':'+path
 if git(repo,'cat-file','-t',ref).strip()!=b'blob' or not 0<int(git(repo,'cat-file','-s',ref))<=max_bytes:raise ValueError('dataset bounds')
 return git(repo,'cat-file','blob',ref)
def run(root):
 base=Path.home()/'projects'/'icarus-ml-research-sources';out=[]
 for name,rid,rev,path,lag in [
 ('aeon-toolkit--aeon','aeon-toolkit/aeon','810325b558c8459c538fd162ef6bae3abacf7d7d','aeon/datasets/data/Airline/Airline.csv',12),
 ('shiyu-coder--Kronos','shiyu-coder/Kronos','67b630e67f6a18c9e9be918d9b4337c960db1e9a','finetune_csv/data/HK_ali_09988_kline_5min_all.csv',1)]:
  try:
   raw=read_pinned(base/name,rev,path,10000000)
   values,span=(parse_airline(raw),{'first':'1949-01','last':'1960-12'}) if lag==12 else parse_market(raw)
   r=evaluate(values,int(len(values)*.8),lag)
   out.append({'status':'completed','repo':rid,'revision':rev,'path':path,'sha256':hashlib.sha256(raw).hexdigest(),'span':span,'rights':'local evaluation only; separate data rights not certified',**r})
  except Exception as e:out.append({'status':'blocked','repo':rid,'reason':type(e).__name__+': '+str(e)[:120]})
 result={'schema':'umbra.observed.research.v1','datasets':out,'production_authority':False}
 p=root/'experience'/'source-knowledge'/'observed-research.json';p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(result,indent=2),encoding='utf8');tmp.replace(p)
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);a=p.parse_args();print(json.dumps(run(a.root)))
