"""Bounded local repository operations. Only explicitly reviewed functions can execute."""
import ast, hashlib, json, math, os, re, subprocess, sys, zipfile
from pathlib import Path, PurePosixPath
from typing import Optional, Union
from functools import wraps
import __future__
SPECS={
 'forecast_metrics':('Nixtla/neuralforecast','24dd828c12d966ba5d41566d91735c996e488db7','neuralforecast/losses/numpy.py',['_metric_protections','mae','mse','rmse','quantile_loss']),
 'simulation_latency':('abides-sim/abides','c4bf157678928934417aba6073eb0651aeaf6d15','util/util.py',['meters_to_light_ns','sigmoid']),
 'timeseries_windows':('yuezhihan/ts2vec','b0088e14a99706c05451316dc6db8d3da9351163','utils.py',['pad_nan_to_target','split_with_nan']),
 'forecast_crosscheck':('thuml/Time-Series-Library','4e938a1767106324dd753b2a44832bf870a0252e','utils/metrics.py',['MAE','MSE','RMSE','MAPE','MSPE','metric']),
 'sparse_regularization':('dynamicslab/pysindy','c4421fcec275c8f4cc5c1e93bebb961b212067ae','pysindy/utils/base.py',['_validate_prox_and_reg_inputs','_prox_l1','_prox_l2','_regularization_l1','_regularization_l2'])}
SOURCE_HASHES={'forecast_metrics':'6151fd16e8d1ee200cb24d87f1bbd21f74a1f715aa6edee5368e49f25317bc5e','simulation_latency':'85e0824d8a90a7510b4322b96d263b7bd884df382ea447984ce3370142a23a42','timeseries_windows':'85ca67e8e84cad09933d2f3ba60de3bc18bafda78706bd5c4c4a509f577dea90','forecast_crosscheck':'0a565c3f64d7cd29d9a87dee0c22d48f4a6a329476f893458cc18a35fa46a5df','sparse_regularization':'be5fad3f6cd5b62f06dd51bc94d027f4b86f5228f8ef3097a0b5f7b77a7e59e5'}
ROOT=Path.home()/'projects'/'umbra-agentic-native-20261124'
def allowed_path(s):
 if not isinstance(s,str) or len(s)>240 or not re.fullmatch(r'[A-Za-z0-9_./ -]+',s):return False
 p=PurePosixPath(s)
 if p.is_absolute() or any(x in ('','.','..') or x.startswith('.') or re.search(r'(?i)secret|credential|token|password|private|keyring|cookie|\.pem|\.key',x) for x in s.split('/')):return False
 return p.suffix.lower() in ('.md','.rst','.txt','.py','.js','.mjs','.ts','.rs','.go','.cpp','.c','.h') and p.name.lower() not in ('requirements.txt',)
def vector(v,lo=-1e9,hi=1e9):
 if not isinstance(v,list) or not 1<=len(v)<=512 or any(type(x) not in (float,int) or not math.isfinite(x) or not lo<=x<=hi for x in v):raise ValueError('numeric input budget')
 return v
def validate_input(name,a):
 if not isinstance(a,dict):raise ValueError('invalid input')
 if name in ('forecast_metrics','forecast_crosscheck'):
  if set(a)!={'actual','predicted'} or len(vector(a['actual']))!=len(vector(a['predicted'])):raise ValueError('forecast shape')
  if name=='forecast_crosscheck' and any(abs(x)<1e-9 for x in a['actual']):raise ValueError('percentage denominator')
 elif name=='simulation_latency':
  if set(a)!={'meters','signal','beta'}:raise ValueError('latency input')
  vector(a['meters'],0,1e8);vector([a['signal']],-100,100);vector([a['beta']],0,100)
 elif name=='timeseries_windows':
  if set(a)!={'values','sections'}:raise ValueError('window input')
  v=vector(a['values'])
  if type(a['sections']) is not int or not 1<=a['sections']<=min(32,len(v)):raise ValueError('sections')
 elif name=='sparse_regularization':
  if set(a)!={'coefficients','weight'}:raise ValueError('regularization input')
  vector(a['coefficients']);vector([a['weight']],0,1000)
 else:raise ValueError('unknown capability')
 return a
def command(repo,args):
 p=repo['path']
 if p.startswith('wsl://Ubuntu/'):
  cmd=['wsl','-d','Ubuntu','--','git','-C',p[len('wsl://Ubuntu'):],*args]
 else:cmd=['git','-C',p,*args]
 env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GIT_OPTIONAL_LOCKS':'0','GIT_NO_REPLACE_OBJECTS':'1'}
 r=subprocess.run(cmd,capture_output=True,timeout=15,env=env)
 if r.returncode:raise ValueError('local git unavailable')
 return r.stdout
def git_source(repo,path,cap=65536):
 if repo.get('kind')!='git' or not re.fullmatch('[a-f0-9]{40,64}',repo.get('head','')) or not allowed_path(path):raise ValueError('source identity')
 ref=repo['head']+':'+path
 if command(repo,['cat-file','-t',ref]).strip()!=b'blob':raise ValueError('not a file')
 size=int(command(repo,['cat-file','-s',ref]))
 if not 0<size<=cap:raise ValueError('source size')
 data=command(repo,['cat-file','blob',ref])
 if len(data)!=size:raise ValueError('source changed')
 return data
def list_source(registry,rid):
 rows=[r for r in registry['repositories'] if r['id']==rid]
 if len(rows)!=1:raise ValueError('source selection')
 r=rows[0];files=[];truncated=False
 if r['kind']=='git':
  # Enumerate tracked paths, not working-tree files or dependency contents.
  if not re.fullmatch('[a-f0-9]{40,64}',r['head']):raise ValueError('invalid revision')
  data=command(r,['ls-tree','-r','--name-only','-z',r['head']])
  if len(data)>16*1024**2:raise ValueError('tree budget')
  files=[x for x in data.decode('utf8','replace').split('\0') if allowed_path(x)]
 elif r['kind']=='archive_candidate':
  if not r['path'].lower().endswith('.zip'):raise ValueError('archive format')
  with zipfile.ZipFile(r['path']) as z:
   files=[x.filename for x in z.infolist() if not x.is_dir() and 0<x.file_size<=65536 and not x.flag_bits&1 and allowed_path(x.filename)]
 elif r['kind']=='source_candidate':
  if r['readme_sha256'] and not r['path'].startswith('wsl://') and allowed_path(r['readme']):
   source_receipt(registry,rid,r['readme']);files=[r['readme']]
 else:raise ValueError('source kind')
 files=sorted(set(files),key=lambda x:(not PurePosixPath(x).name.lower().startswith('readme'),x))
 return {'repo_id':rid,'revision':r['head'],'files':files[:128],'eligible_paths':len(files),'truncated':len(files)>128,'trust':'untrusted_source_data','production_authority':False}
def source_receipt(registry,rid,path):
 rows=[r for r in registry['repositories'] if r['id']==rid]
 if len(rows)!=1 or not allowed_path(path):raise ValueError('source selection')
 r=rows[0]
 if r['kind']=='git':data=git_source(r,path)
 elif r['kind']=='archive_candidate':
  if not str(r['path']).lower().endswith('.zip'):raise ValueError('archive format')
  with zipfile.ZipFile(r['path']) as z:
   i=z.getinfo(path)
   if i.is_dir() or not 0<i.file_size<=65536 or i.flag_bits&1:raise ValueError('archive member')
   with z.open(i) as f:data=f.read(65537)
 elif r['kind']=='source_candidate':
  # Only the inventoried README for unpinned trees; never arbitrary working-tree files.
  if path!=r['readme'] or not r['readme_sha256'] or r['path'].startswith('wsl://'):raise ValueError('unpinned source restriction')
  p=Path(r['path'])/path
  if p.is_symlink() or not p.is_file() or p.stat().st_size>65536:raise ValueError('source path')
  data=p.read_bytes()
  if hashlib.sha256(data).hexdigest()!=r['readme_sha256']:raise ValueError('source digest changed')
 else:raise ValueError('source kind')
 if not 0<len(data)<=65536 or b'\0' in data:raise ValueError('source size or binary')
 return {'repo_id':rid,'revision':r['head'],'path':path,'sha256':hashlib.sha256(data).hexdigest(),'text':data.decode('utf8'),'trust':'untrusted_source_data','production_authority':False}
def run_algorithm(registry,name,a):
 a=validate_input(name,a)
 upstream,rev,file,funcs=SPECS[name]
 matches=[r for r in registry.get('repositories',[]) if r.get('repo','') and r['repo'].lower()==upstream.lower() and r.get('head')==rev and r.get('kind')=='git']
 if not matches:raise ValueError('pinned repository missing')
 repo=matches[0];data=git_source(repo,file)
 if hashlib.sha256(data).hexdigest()!=SOURCE_HASHES[name]:raise ValueError('reviewed source digest mismatch')
 # Execute only the reviewed definitions from the immutable commit. No module top-level code.
 tree=ast.parse(data.decode('utf8'));nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in funcs]
 if sorted(n.name for n in nodes)!=sorted(funcs) or any(n.decorator_list and not (name=='sparse_regularization' and len(n.decorator_list)==1 and isinstance(n.decorator_list[0],ast.Name) and n.decorator_list[0].id=='_validate_prox_and_reg_inputs') for n in nodes):raise ValueError('reviewed definitions missing')
 import numpy as np
 scope={'np':np,'Optional':Optional,'Union':Union,'wraps':wraps}
 exec(compile(ast.Module(body=nodes,type_ignores=[]),file,'exec',flags=__future__.annotations.compiler_flag),scope)
 if name=='forecast_metrics':
  y=np.array(a['actual'],dtype=float);p=np.array(a['predicted'],dtype=float)
  out={k:float(scope[k](y,p)) for k in ('mae','mse','rmse','quantile_loss')}
  diff=[x-y for x,y in zip(a['actual'],a['predicted'])]
  expected={'mae':sum(map(abs,diff))/len(diff),'mse':sum(x*x for x in diff)/len(diff)}
  expected['rmse']=math.sqrt(expected['mse']);expected['quantile_loss']=expected['mae']/2
  if not all(math.isclose(out[k],v,rel_tol=1e-10,abs_tol=1e-10) for k,v in expected.items()):raise ValueError('independent numeric disagreement')
 elif name=='simulation_latency':
  out={'light_nanoseconds':scope['meters_to_light_ns'](np.array(a['meters'],dtype=float)).tolist(),'sigmoid':float(scope['sigmoid'](a['signal'],a['beta']))}
  z=a['signal']*a['beta'];expected=1/(1+math.exp(-z)) if z>=0 else math.exp(z)/(1+math.exp(z))
  if out['light_nanoseconds']!=[int(x/(299792458e-9)) for x in a['meters']] or not math.isclose(out['sigmoid'],expected,abs_tol=1e-12):raise ValueError('simulation verification')
 elif name=='forecast_crosscheck':
  y=np.array(a['actual'],dtype=float);p=np.array(a['predicted'],dtype=float)
  out=dict(zip(('mae','mse','rmse','mape','mspe'),map(float,scope['metric'](p,y))))
  diff=[x-z for x,z in zip(a['actual'],a['predicted'])]
  mse=sum(x*x for x in diff)/len(diff)
  expected={'mae':sum(map(abs,diff))/len(diff),'mse':mse,'rmse':math.sqrt(mse),'mape':sum(abs(x/y) for x,y in zip(diff,a['actual']))/len(diff),'mspe':sum((x/y)**2 for x,y in zip(diff,a['actual']))/len(diff)}
  if not all(math.isclose(out[k],v,rel_tol=1e-10,abs_tol=1e-10) for k,v in expected.items()):raise ValueError('forecast crosscheck disagreement')
 elif name=='sparse_regularization':
  x=np.array(a['coefficients'],dtype=float);w=a['weight']
  out={'l1_prox':scope['_prox_l1'](x,w).tolist(),'l2_prox':scope['_prox_l2'](x,w).tolist(),'l1_penalty':float(scope['_regularization_l1'](x,w)),'l2_penalty':float(scope['_regularization_l2'](x,w))}
  expected=[math.copysign(max(abs(v)-w,0),v) for v in a['coefficients']]
  if not all(math.isclose(u,v,rel_tol=1e-10,abs_tol=1e-10) for u,v in zip(out['l1_prox'],expected)) or not all(math.isclose(u,v/(1+2*w),rel_tol=1e-10,abs_tol=1e-10) for u,v in zip(out['l2_prox'],a['coefficients'])) or not math.isclose(out['l1_penalty'],w*sum(map(abs,a['coefficients'])),rel_tol=1e-10,abs_tol=1e-10) or not math.isclose(out['l2_penalty'],w*sum(v*v for v in a['coefficients']),rel_tol=1e-10,abs_tol=1e-10):raise ValueError('regularization disagreement')
 else:
  parts=scope['split_with_nan'](np.array(a['values'],dtype=float),a['sections'])
  out={'windows':[[None if np.isnan(x) else float(x) for x in v] for v in parts]}
  if [x for row in out['windows'] for x in row if x is not None]!=a['values'] or len(out['windows'])!=a['sections'] or len({len(x) for x in out['windows']})!=1:raise ValueError('window verification')
 return {'schema':'umbra.repository.execution.v1','capability':name,'repository':upstream,'revision':rev,'source_sha256':hashlib.sha256(data).hexdigest(),'functions':funcs,'arguments':a,'result':out,'independently_checked':True,'production_authority':False}
FIXTURES={'forecast_metrics':{'actual':[1,3,5],'predicted':[2,3,2]},'simulation_latency':{'meters':[0,1,300],'signal':2,'beta':1},'timeseries_windows':{'values':[1,2,3,4,5],'sections':2},'forecast_crosscheck':{'actual':[1,3,5],'predicted':[2,3,2]},'sparse_regularization':{'coefficients':[-2,0,3],'weight':.5}}
def main():
 raw=sys.stdin.buffer.read(65537)
 if len(raw)>65536:raise ValueError('request budget')
 q=json.loads(raw)
 p=ROOT/'repository-fabric'/'registry.json'
 if p.stat().st_size>32*1024**2:raise ValueError('registry budget')
 registry=json.loads(p.read_text(encoding='utf8'))
 if q.get('operation')=='qualify' and set(q)=={'operation'}:
  results=[]
  for name,a in FIXTURES.items():
   try:results.append({'status':'operational','receipt':run_algorithm(registry,name,a)})
   except Exception as e:results.append({'status':'blocked','capability':name,'reason':type(e).__name__})
  print(json.dumps({'results':results},allow_nan=False));return
 if q.get('operation')=='source_list' and set(q)=={'operation','repo_id'}:r=list_source(registry,q['repo_id'])
 elif q.get('operation')=='source' and set(q)=={'operation','repo_id','path'}:r=source_receipt(registry,q['repo_id'],q['path'])
 elif q.get('operation')=='execute' and set(q)=={'operation','capability','arguments'}:r=run_algorithm(registry,q['capability'],q['arguments'])
 else:raise ValueError('invalid operation')
 print(json.dumps(r,allow_nan=False))
if __name__=='__main__':main()
