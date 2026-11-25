"""Owner-local EXASOVEREIGN resource acquisition; immutable data, no execution."""
import argparse,json,os,re,shutil,sys,time,urllib.parse,urllib.request
from pathlib import Path,PurePosixPath
from native_training_bootstrap import download_verified,used as training_used
from neural_priority import size,write,ROOT,CAP as NEURAL_CAP
BUDGETS=dict(science=2000000000,finance=2000000000,reasoning=2000000000,graphs=1000000000,symbolic=500000000,algorithms=500000000,experience=1000000000,simulation=1000000000,causal=500000000,benchmarks=1000000000,synthetic=500000000,cognition=500000000,reinforcement=500000000,semantic=1500000000,evolution=500000000)
CAP=sum(BUDGETS.values())
FLOOR=3000000000
LICENSES={'apache-2.0','mit','bsd-2-clause','bsd-3-clause','cc-by-4.0','cc0-1.0','isc','odc-by','odc-pddl','unlicense'}
DATASETS=[
 ('allenai/ai2_arc','science'),('allenai/openbookqa','science'),('allenai/sciq','science'),('allenai/qasper','science'),('allenai/physqa','science'),
 ('FinGPT/fingpt-sentiment-train','finance'),('FinGPT/fingpt-finred','finance'),('FinGPT/fingpt-fiqa_qa','finance'),('zeroshot/twitter-financial-news-sentiment','finance'),('FinGPT/fingpt-headline','finance'),
 ('openai/gsm8k','reasoning'),('google/boolq','reasoning'),('allenai/strategyqa','reasoning'),('openai/gsm-hard','reasoning'),('openai/prm800k','reasoning'),
 ('cais/mmlu','benchmarks'),('HuggingFaceH4/MATH-500','benchmarks'),('TIGER-Lab/MMLU-Pro','benchmarks'),('openai/humaneval','benchmarks'),('google/IFEval','benchmarks'),
 ('wikimedia/structured-wikipedia','semantic'),('rag-datasets/rag-mini-wikipedia','semantic'),('sentence-transformers/natural-questions','semantic'),('microsoft/ms_marco','semantic'),
 ('HuggingFaceTB/smoltalk','synthetic'),('allenai/tulu-3-sft-mixture','synthetic'),('openai/grade-school-math','reasoning')]
PACKAGES=[
 ('networkx','3.4.2','graphs'),('rdflib','7.1.4','graphs'),('sympy','1.14.0','symbolic'),('mpmath','1.3.0','symbolic'),
 ('scipy','1.15.3','algorithms'),('scikit-learn','1.6.1','algorithms'),('simpy','4.1.1','simulation'),('gymnasium','1.1.1','reinforcement'),
 ('dowhy','0.12','causal'),('causal-learn','0.1.4.0','causal'),('hypothesis','6.130.0','synthetic'),
 ('jsonschema','4.23.0','cognition'),('pydantic','2.11.4','cognition'),('rank-bm25','0.2.2','semantic'),('rapidfuzz','3.13.0','semantic'),
 ('duckdb','1.2.2','experience'),('pyarrow','19.0.1','experience'),('optuna','4.3.0','evolution'),('deap','1.4.2','evolution'),
 ('pymoo','0.6.1.3','evolution'),('statsmodels','0.14.4','finance'),('arch','7.2.0','finance')]
def admit(used,category_used,additional,free,training_remaining,learning_remaining,category_cap):
 return (0<additional and used+additional<=CAP and category_used+additional<=category_cap and free-additional>=FLOOR+max(0,training_remaining)+max(0,learning_remaining))
def neural_complete(status):
 return status.get('status')=='pass_finished' and status.get('cap_bytes',0)>=NEURAL_CAP and not any(x.get('status')=='retry_needed' for x in status.get('results',[]))
def get(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'UMBRA-intelligence-resource/1.0'}),timeout=25) as f:
  return json.load(f)
def safe_path(s):
 return isinstance(s,str) and len(s)<240 and not re.search(r'[:\\\x00-\x1f]',s) and not s.startswith('/') and all(x not in ('','.','..') for x in s.split('/'))
def dataset_rows(repo,category,m):
 if m.get('id')!=repo or m.get('private') is not False or m.get('gated') not in (False,None) or not re.fullmatch('[a-f0-9]{40}',str(m.get('sha',''))):return []
 lic=(m.get('cardData') or {}).get('license')
 if not isinstance(lic,str) or lic.lower() not in LICENSES:return []
 rows=[]
 for f in m.get('siblings',[]):
  p=f.get('rfilename');n=f.get('size');h=(f.get('lfs') or {}).get('sha256')
  if not safe_path(p) or PurePosixPath(p).suffix.lower() not in ('.parquet','.jsonl','.csv','.json') or type(n) is not int or not 0<n<=500000000 or not re.fullmatch('[a-f0-9]{64}',str(h)):continue
  if p.lower().endswith(('dataset_infos.json','config.json')):continue
  split='evaluation' if re.search(r'(^|[/_-])(test|validation|dev|eval)([/_.-]|$)',p.lower()) or category=='benchmarks' else 'candidate_training'
  rows.append(dict(repo=repo,category=category,revision=m['sha'],license=lic,path=p,size=n,sha=h,split=split,url='https://huggingface.co/datasets/'+repo+'/resolve/'+m['sha']+'/'+urllib.parse.quote(p,safe='/'),kind='dataset'))
 return rows
def package_row(name,version,category,m):
 i=m.get('info') or {};lic=(i.get('license_expression') or i.get('license') or '').strip().lower()
 if i.get('version')!=version or i.get('name','').lower().replace('_','-')!=name.lower().replace('_','-'):return None
 mapping={'mit license':'mit','bsd license':'bsd-3-clause','apache software license':'apache-2.0','apache 2.0':'apache-2.0'}
 lic=mapping.get(lic,lic)
 if lic not in LICENSES:return None
 rows=[]
 for f in m.get('urls',[]):
  p=f.get('filename','');n=f.get('size');h=(f.get('digests') or {}).get('sha256');url=f.get('url','')
  if not safe_path(p) or '/' in p or not p.endswith('.whl') or f.get('yanked') or type(n) is not int or not 0<n<=200000000 or not re.fullmatch('[a-f0-9]{64}',str(h)) or not url.startswith('https://files.pythonhosted.org/'):continue
  if not ('-none-any.whl' in p or ('win_amd64.whl' in p and ('cp311-' in p or 'abi3-' in p))):continue
  rows.append(dict(repo=name,category=category,revision=version,license=lic,path=p,size=n,sha=h,split='tool_artifact',url=url,kind='wheel'))
 return min(rows,key=lambda x:x['size']) if rows else None
def plan():
 rows=[];rejected=[]
 for repo,cat in DATASETS:
  try:
   found=dataset_rows(repo,cat,get('https://huggingface.co/api/datasets/'+repo+'?blobs=true'))
   if not found:raise ValueError('license, pinned data format or digest unavailable')
   rows+=found;print('DATASET_ELIGIBLE',repo,len(found),sum(x['size'] for x in found),flush=True)
  except Exception as e:rejected.append({'repo':repo,'reason':type(e).__name__})
 for name,v,cat in PACKAGES:
  try:
   row=package_row(name,v,cat,get('https://pypi.org/pypi/'+name+'/'+v+'/json'))
   if not row:raise ValueError('license or compatible hashed wheel unavailable')
   rows.append(row);print('PACKAGE_ELIGIBLE',name,row['size'],flush=True)
  except Exception as e:rejected.append({'repo':name,'reason':type(e).__name__})
 return {'schema':'umbra.intelligence.resources.v1','cap_bytes':CAP,'budgets':BUDGETS,'rows':rows,'rejected':rejected}
def load(p):
 try:return json.loads(p.read_text(encoding='utf8'))
 except (OSError,ValueError):return {}
def run(plan_only=False):
 root=ROOT/'intelligence-resources';root.mkdir(exist_ok=True)
 manifest=root/'plan.json';m=load(manifest)
 if not m:
  m=plan();write(manifest,m)
 print('PLAN_READY',len(m['rows']),sum(x['size'] for x in m['rows']),flush=True)
 if plan_only:return
 training=ROOT.parent/'umbra-train-native-20261124'
 status=load(ROOT/'neural-priority-status.json')
 if not neural_complete(status) or (ROOT/'active.lock').exists() or (training/'bootstrap.lock').exists():
  print('DEFERRED_NEURAL_OR_TRAINING',flush=True);return
 lock=ROOT/'active.lock'
 with lock.open('x') as f:f.write(str(os.getpid()))
 results=[]
 try:
  if (training/'bootstrap.lock').exists():return
  for row in sorted(m['rows'],key=lambda x:(x['kind']!='wheel',x['split']!='evaluation',x['size'],x['repo'],x['path'])):
   cat=row['category'];bucket=root/cat;folder=bucket/(row['repo'].replace('/','--')+'--'+row['revision'][:12]);target=folder/row['path']
   if not safe_path(row['path']) or cat not in BUDGETS:raise ValueError('unsafe manifest')
   receipt=target.with_name(target.name+'.receipt.json')
   if receipt.exists() and target.is_file() and load(receipt)==row and target.stat().st_size==row['size']:continue
   part=target.with_name(target.name+'.part')
   need=max(1,row['size']-(part.stat().st_size if part.exists() else 0))+4096
   reserve_training=max(0,4500000000-training_used());reserve_learning=3000000000
   if not admit(size(root),size(bucket),need,shutil.disk_usage(ROOT).free,reserve_training,reserve_learning,BUDGETS[cat]):
    results.append({'repo':row['repo'],'path':row['path'],'status':'deferred_storage'});continue
   target.parent.mkdir(parents=True,exist_ok=True)
   def gate(n=0):
    if not admit(size(root),size(bucket),max(1,n),shutil.disk_usage(ROOT).free,reserve_training,reserve_learning,BUDGETS[cat]):raise ValueError('resource disk gate')
   try:
    print('PULL',row['repo'],row['path'],row['size'],flush=True)
    download_verified(row['url'],target,row['size'],row['sha'],attempts=2,gate_fn=gate)
    write(receipt,row);results.append({'repo':row['repo'],'path':row['path'],'status':'verified'});print('VERIFIED',row['repo'],row['path'],flush=True)
   except Exception as e:
    results.append({'repo':row['repo'],'path':row['path'],'status':'retry_needed','reason':type(e).__name__});print('RETRY',row['repo'],type(e).__name__,flush=True)
  write(root/'status.json',{'status':'pass_finished','timestamp':int(time.time()),'results':results,'used_bytes':size(root)})
 finally:lock.unlink(missing_ok=True)
def resume(root,training,queue_status):
 import subprocess
 from acquisition_recovery import pid_alive
 d=root/'intelligence-resources';d.mkdir(exist_ok=True)
 s=load(d/'status.json');a=load(d/'attempt.json');now=int(time.time())
 if pid_alive(a.get('pid')):return {'status':'running'}
 if queue_status!='ready' or not neural_complete(load(root/'neural-priority-status.json')) or (training/'bootstrap.lock').exists():return {'status':'deferred_neural_or_training'}
 if s.get('status')=='pass_finished' and not any(x.get('status') in ('deferred_storage','retry_needed') for x in s.get('results',[])):return {'status':'complete'}
 if now-max(a.get('timestamp',0),s.get('timestamp',0))<1800:return {'status':'cooldown'}
 py=Path(sys.base_prefix)/'python.exe'
 if not py.is_file():return {'status':'deferred_runtime'}
 with (d/'acquisition.log').open('a',encoding='utf8') as out:
  proc=subprocess.Popen([str(py),'-u',str(Path(__file__).resolve())],stdout=out,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 write(d/'attempt.json',{'pid':proc.pid,'timestamp':now});return {'status':'started','pid':proc.pid}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--plan',action='store_true');run(p.parse_args().plan)
