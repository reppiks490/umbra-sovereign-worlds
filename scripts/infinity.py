"""UMBRA INFINITY: bounded autonomous public-weight discovery and qualification."""
import argparse,hashlib,json,math,os,re,shutil,time,urllib.parse
from pathlib import Path
from agentic_native import SUPPORTED,LICENSES,REPO,HEX,read_receipt,SafeWeights,embed,available_ram
from hf_weight_cache import Cache,MIN_FREE,lock,request,metadata
DISCOVERY_TASKS=('feature-extraction','sentence-similarity','text-classification','time-series-forecasting','image-classification','automatic-speech-recognition','text-generation','text2text-generation','question-answering','token-classification','text-ranking','object-detection','image-feature-extraction','audio-classification')
CAP=10**9
MAX_MODEL=400*10**6
FILES=('model.safetensors','config.json','tokenizer.json','tokenizer_config.json','special_tokens_map.json','vocab.txt','modules.json','1_Pooling/config.json','README.md','LICENSE','LICENSE.txt')
CASES=[
 ('A city has insufficient drinking water.','A town faces a shortage of clean water.','A computer renders a picture.'),
 ('The crops failed after prolonged drought.','A lack of rainfall destroyed the harvest.','A musician tunes a violin.'),
 ('The software test detects a regression.','An automated check finds a new defect.','The sea level rises after a storm.'),
 ('The hospital treats an infectious disease.','Doctors care for patients with an infection.','A mountain trail is closed.'),
 ('A solar panel generates electricity.','Sunlight is converted into electrical power.','A person reads a mystery novel.'),
 ('The forest shelters many animal species.','A woodland provides habitat for wildlife.','A train arrives at the station.')
]
def empty_state():return {'schema':'umbra.infinity.v1','profiles':{},'catalog':[],'status':'new','cycles':0}
def load_state(root):
 p=root/'infinity'/'state.json'
 if not p.exists():return empty_state()
 if p.is_symlink() or p.stat().st_size>8*1024**2:raise ValueError('state budget')
 s=json.loads(p.read_text(encoding='utf8'))
 if s.get('schema')!='umbra.infinity.v1' or not isinstance(s.get('profiles'),dict) or len(s['profiles'])>512:raise ValueError('invalid state')
 return s
def save_state(root,s):
 d=root/'infinity';d.mkdir(exist_ok=True);p=d/'state.json';tmp=d/('state.'+str(os.getpid())+'.tmp')
 with tmp.open('x',encoding='utf8') as f:json.dump(s,f,indent=2);f.flush();os.fsync(f.fileno())
 os.replace(tmp,p)
def discover_candidates():
 rows=[]
 for repo in SUPPORTED:
  try:
   with request('https://huggingface.co/api/models/'+repo+'?blobs=true') as r:m=json.loads(r.read(8*1024**2))
   rev=m.get('sha','');w=next(x for x in m['siblings'] if x['rfilename']=='model.safetensors')
   digest=w['lfs']['sha256'];lic=(m.get('cardData') or {}).get('license')
   if m.get('id')!=repo or m.get('private') is not False or m.get('gated') not in (False,None) or lic not in LICENSES or not re.fullmatch('[a-f0-9]{40}',rev) or not HEX.fullmatch(digest) or not 0<w['size']<=MAX_MODEL:continue
   rows.append({'repo':repo,'revision':rev,'digest':digest,'size_bytes':w['size'],'license':lic,'task':'retrieval','runtime':'numpy-bert'})
  except Exception:continue
 return rows
def scan_catalog():
 rows=[]
 for task in DISCOVERY_TASKS:
  try:
   url='https://huggingface.co/api/models?'+urllib.parse.urlencode({'pipeline_tag':task,'filter':'safetensors','sort':'downloads','direction':-1,'limit':30})
   with request(url) as r:data=json.loads(r.read(4*1024**2))
   for x in data:
    rid=x.get('id','')
    if REPO.fullmatch(rid) and not x.get('private') and not x.get('gated') and not re.search('quant|gguf|gptq|awq|int4|int8|random|dummy',rid,re.I):
     rows.append({'repo':rid,'task':task,'status':'discovered_unverified','downloads':x.get('downloads',0)})
  except Exception:continue
 return list({x['repo']:x for x in rows}.values())
def refresh_catalog(root):
 d=root/'infinity';d.mkdir(exist_ok=True);p=d/'discovery.json'
 with lock(d/'discovery.lock'):
  if p.exists():
   prior=json.loads(p.read_text(encoding='utf8'))
   if prior.get('discovery_version')==2 and int(time.time())-prior.get('updated',0)<86400:return prior
  result={'updated':int(time.time()),'models':scan_catalog(),'status':'discovery_only','discovery_version':2}
  if not result['models'] and p.exists():return prior
  tmp=d/('discovery.'+str(os.getpid())+'.tmp')
  with tmp.open('x',encoding='utf8') as f:json.dump(result,f);f.flush();os.fsync(f.fileno())
  os.replace(tmp,p)
  return result
def select_candidates(rows,state,now):
 return sorted([x for x in rows if x.get('runtime')=='numpy-bert' and state['profiles'].get(x['digest'],{}).get('status')!='qualified' and state['profiles'].get(x['digest'],{}).get('retry_after',0)<=now],key=lambda x:(state['profiles'].get(x['digest'],{}).get('attempts',0),x['repo']))
def score_embeddings(cases):
 correct=0; margins=[]
 for q,docs,label in cases:
  if not q or len(docs)<2 or label not in range(len(docs)) or any(len(v)!=len(q) for v in docs) or not all(math.isfinite(x) for v in [q,*docs] for x in v):raise ValueError('invalid vectors')
  scores=[sum(a*b for a,b in zip(q,v)) for v in docs];rank=sorted(range(len(scores)),key=lambda i:(-scores[i],i))
  correct+=rank[0]==label;margins.append(scores[label]-max(x for i,x in enumerate(scores) if i!=label))
 if not margins:raise ValueError('empty evaluation')
 return {'accuracy':correct/len(margins),'mean_margin':sum(margins)/len(margins),'cases':len(margins)}
def cache_root(root):
 p=root/'infinity'/'cache';p.mkdir(parents=True,exist_ok=True);(p/'neural').mkdir(exist_ok=True);return p
def find_local(root,row):
 for base in (root,cache_root(root)):
  for bucket in ('neural','tiny'):
   p=base/bucket/(row['repo'].replace('/','--')+'--'+row['revision'][:12])
   if p.is_dir():
    try:
     r=read_receipt(p)
     if r['digest']==row['digest']:return base
    except Exception:pass
 return None
def fetch_bundle(root,row):
 base=cache_root(root);folder=base/'neural'/(row['repo'].replace('/','--')+'--'+row['revision'][:12])
 c=Cache(base)
 if folder.exists():
  c.ensure(row['digest']);return base
 m=metadata(row['repo'],row['revision']);r={'repo':row['repo'],'revision':row['revision'],'license':row['license'],'task':'feature-extraction','digest':row['digest'],'native_verified':True,'inference_verified':False,'training_verified':False,'files':[]}
 table={x['rfilename']:x for x in m['siblings']}
 for name in FILES:
  f=table.get(name)
  if f is None:continue
  size=f.get('size');sha=(f.get('lfs') or {}).get('sha256');blob=f.get('blobId')
  if type(size) is not int or size<1 or size>(MAX_MODEL if name=='model.safetensors' else 16*10**6) or not (sha or blob):raise ValueError('file metadata')
  r['files'].append({'name':name,'size':size,'sha':sha,'blob':blob})
 r['total']=sum(f['size'] for f in r['files'])
 w=next(f for f in r['files'] if f['name']=='model.safetensors');c.remote_check(r,w)
 if not {'config.json','tokenizer.json','model.safetensors'}<=set(f['name'] for f in r['files']):raise ValueError('incomplete runtime bundle')
 if r['total']>MAX_MODEL:raise ValueError('bundle cap')
 used=sum(p.stat().st_size for p in base.rglob('*') if p.is_file())
 if used+r['total']>CAP or shutil.disk_usage(base).free-r['total']<MIN_FREE:raise ValueError('cache or free-space cap')
 folder.mkdir()
 try:
  for f in r['files']:
   p=folder/f['name'];p.parent.mkdir(exist_ok=True,parents=True);n=0;h=hashlib.sha256();g=hashlib.sha1(('blob '+str(f['size'])+'\0').encode())
   with request('https://huggingface.co/'+r['repo']+'/resolve/'+r['revision']+'/'+urllib.parse.quote(f['name'],safe='/')) as src,p.open('xb') as out:
    while True:
     b=src.read(1024**2)
     if not b:break
     n+=len(b)
     if n>f['size'] or shutil.disk_usage(base).free-len(b)<MIN_FREE:raise ValueError('storage gate')
     h.update(b);g.update(b);out.write(b)
   if n!=f['size'] or (h.hexdigest()!=f['sha'] if f['sha'] else g.hexdigest()!=f['blob']):raise ValueError('file integrity')
  (folder/'receipt.json').write_text(json.dumps(r),encoding='utf8');read_receipt(folder)
 except Exception:
  shutil.rmtree(folder);raise
 return base
def auto_embed(root,text):
 state=load_state(root);champion=state.get('champion')
 if not champion:raise ValueError('no benchmark-qualified model')
 row=next((x for x in state.get('candidates',[]) if x['digest']==champion['digest']),None)
 if row is None:raise ValueError('champion revision not available in current registry')
 if (root/'active.lock').exists():raise ValueError('acquisition active')
 base=find_local(root,row)
 if base is None:
  # Restore only a previously registered exact weight; no substitute revision.
  for candidate in (root,cache_root(root)):
   if any(x['digest']==row['digest'] and x['status']=='remote' for x in Cache(candidate).list()):
    Cache(candidate).ensure(row['digest']);base=candidate;break
 if base is None:raise ValueError('champion unavailable')
 with lock(base/'cache-use.lock'):
  out=embed(base,row['repo'],text)
 if out['weight_sha256']!=row['digest'] or out['revision']!=row['revision']:raise ValueError('identity mismatch')
 return out
def qualify_model(root,row):
 if available_ram()<row['size_bytes']*4+1024**3:raise ValueError('memory admission')
 base=find_local(root,row) or fetch_bundle(root,row)
 results=[];start=time.monotonic()
 with lock(base/'cache-use.lock'):
  for query,pos,neg in CASES:
   vectors=[embed(base,row['repo'],s) for s in (query,pos,neg)]
   if any(v['weight_sha256']!=row['digest'] or v['revision']!=row['revision'] for v in vectors):raise ValueError('inference identity')
   results.append((vectors[0]['embedding'],[vectors[1]['embedding'],vectors[2]['embedding']],0))
 score=score_embeddings(results)
 return {'status':'qualified' if score['accuracy']>=5/6 and score['mean_margin']>0 else 'rejected','score':score['accuracy'],'mean_margin':score['mean_margin'],'cases':score['cases'],'elapsed_seconds':round(time.monotonic()-start,3),'scope':'six synthetic retrieval probes','source':str(base.relative_to(root)) if base!=root else 'initial_pool'}
def run_cycle(root,discover=discover_candidates,qualify=qualify_model):
 root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True)
 if (root/'active.lock').exists():return {'status':'deferred_acquisition'}
 try:
  with lock(root/'active.lock'):
   state=load_state(root);now=int(time.time());rows=discover()
   state['cycles']+=1;state['status']='completed';state['candidates']=rows
   for row in select_candidates(rows,state,now)[:1]:
    prior=state['profiles'].get(row['digest'],{})
    try:result=qualify(root,row)
    except Exception as e:result={'status':'deferred','reason':type(e).__name__+': '+str(e)[:120]}
    result.update({'repo':row['repo'],'revision':row.get('revision'),'digest':row['digest'],'attempts':prior.get('attempts',0)+1,'updated':now,'retry_after':now+86400})
    state['profiles'][row['digest']]=result
   state['champion']=max((p for p in state['profiles'].values() if p['status']=='qualified'),key=lambda p:(p['score'],p.get('mean_margin',0)),default=None)
   save_state(root,state);return state
 except FileExistsError:return {'status':'deferred_lock'}
def rotate(root):
 """Only remove originals from the separate INFINITY cache, never initial pool."""
 state=load_state(root);base=cache_root(root);champion=state.get('champion') or {};out=[]
 for row in Cache(base).list():
  profile=state['profiles'].get(row['digest'],{})
  if row['status']=='local' and profile.get('status') in ('qualified','rejected') and row['digest']!=champion.get('digest'):
   try:out.append(Cache(base).evict(row['digest']))
   except (ValueError,OSError):continue
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('action',choices=['scan','cycle','status','embed','gaps']);a=p.parse_args();root=a.root.resolve()
 if a.action=='scan':print(json.dumps(refresh_catalog(root)))
 elif a.action=='embed':
  import sys
  print(json.dumps(auto_embed(root,sys.stdin.read(2049))))
 elif a.action=='status':print(json.dumps(load_state(root)))
 elif a.action=='gaps':
  f=root/'infinity'/'gaps'/'report.json'
  if not f.exists():print(json.dumps({'status':'unmeasured','production_authority':False}))
  elif f.is_symlink() or f.stat().st_size>8*1024**2:raise ValueError('audit report budget')
  else:print(f.read_text(encoding='utf8'))
 else:
  result=run_cycle(root)
  if result['status']=='completed':
   result['rotated']=rotate(root)
  print(json.dumps(result))
