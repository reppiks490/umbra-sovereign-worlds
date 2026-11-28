"""Historical acquisition completion, independent of continued model residency.

No model removal, network download, or claims of model quality. Evidence is
local Ollama tag identity, manifest metadata, blob lengths, and original DONE
log. This is not a full rehash of the 30 GB weights.
"""
import argparse,hashlib,json,os,re
from pathlib import Path
from urllib.request import urlopen

TAG='qwen3.8:27b-q8_0'
DIGEST='8f5fb6b71ea00052cbe8545738c55ce61112c4e571cb60ca4dad00b131766039'
SIZE=29978242050
RECEIPT='initial-acquisition-receipt.json'
SCOPE='historical acquisition metadata; not model capability or training evidence'
LAYERS={
 'application/vnd.ollama.image.model':{'digest':'sha256:2bb22714289826d7b9e0ba376c3ce47d08bce39abe598745857c44d88c09bdbf','size':29047084384},
 'application/vnd.ollama.image.projector':{'digest':'sha256:ac3714bfdddeca31351f2752bf1a63f266f4df87c0b68c895e44945ca704448e','size':931146016}}
def expected_tag():return {'name':TAG,'digest':DIGEST,'size':SIZE}
def expected_layers():return {k:dict(v) for k,v in LAYERS.items()}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def terminal_done(root):
 p=Path(root)/'acquisition.log'
 if not p.is_file() or p.is_symlink():return None
 with p.open('rb') as f:
  offset=max(0,p.stat().st_size-65536);f.seek(offset)
  if offset:f.readline()
  tail=f.read(65536).decode('utf8','replace')
 terminal=[x for x in tail.splitlines() if ' DONE ' in x or ' STOP_' in x or ' WAIT_Q8 ' in x]
 if terminal and re.fullmatch(r'\d{4}-\d\d-\d\d \d\d:\d\d:\d\d DONE [0-9]{1,20}',terminal[-1]):
  return terminal[-1]
 return None
def installed(tags):
 return isinstance(tags,list) and any(isinstance(x,dict) and all(x.get(k)==v for k,v in expected_tag().items()) for x in tags)
def local_tags():
 with urlopen('http://127.0.0.1:11434/api/tags',timeout=10) as f:
  raw=f.read(1048577)
  if len(raw)>1048576:raise ValueError('tag response limit')
  return json.loads(raw)['models']
def inspect_installed_manifest(models):
 models=Path(models)
 p=models/'manifests'/'registry.ollama.ai'/'library'/'qwen3.8'/'27b-q8_0'
 if p.is_symlink() or not p.is_file() or p.stat().st_size>65536:raise ValueError('manifest missing')
 raw=p.read_bytes();manifest=json.loads(raw)
 layers={}
 for row in manifest['layers']:
  key=row.get('mediaType')
  if key not in LAYERS:continue
  if key in layers or {k:row.get(k) for k in ('digest','size')}!=LAYERS[key]:raise ValueError('manifest layer identity')
  blob=models/'blobs'/row['digest'].replace(':','-')
  if blob.is_symlink() or not blob.is_file() or blob.stat().st_size!=row['size']:raise ValueError('blob size')
  layers[key]=dict(LAYERS[key])
 if layers!=LAYERS:raise ValueError('manifest layer coverage')
 return {'manifest_sha256':sha(raw),'layers':layers}
def completed_receipt(root):
 try:
  root=Path(root);p=root/RECEIPT;done=terminal_done(root)
  if not done or not p.is_file() or p.is_symlink() or p.stat().st_size>8192:return False
  r=json.loads(p.read_text(encoding='utf8'))
  return (set(r)=={'version','tag','terminal_sha256','manifest_sha256','layers','scope'} and type(r['version']) is int and r['version']==1 and
   r['tag']==expected_tag() and r['layers']==LAYERS and r['terminal_sha256']==sha(done.encode()) and
   isinstance(r['manifest_sha256'],str) and re.fullmatch('[a-f0-9]{64}',r['manifest_sha256']) is not None and r['scope']==SCOPE)
 except (OSError,ValueError,KeyError,TypeError):return False
def record_completion(root,tags,models):
 root=Path(root);done=terminal_done(root)
 if not done or (root/'active.lock').exists() or not installed(tags):raise ValueError('original acquisition not verified')
 p=root/RECEIPT
 if p.exists():
  if completed_receipt(root):return json.loads(p.read_text(encoding='utf8'))
  raise ValueError('existing invalid acquisition receipt')
 evidence=inspect_installed_manifest(models)
 result={'version':1,'tag':expected_tag(),'terminal_sha256':sha(done.encode()),**evidence,'scope':SCOPE}
 if terminal_done(root)!=done or (root/'active.lock').exists():raise ValueError('acquisition changed')
 with p.open('x',encoding='utf8') as f:json.dump(result,f,sort_keys=True);f.flush();os.fsync(f.fileno())
 return result
def queue_status(root,fetch_tags=local_tags):
 root=Path(root)
 if (root/'active.lock').exists():return 'deferred_acquisition'
 try:
  if not terminal_done(root):return 'initial_queue_not_verified'
  tags=fetch_tags()
  if not isinstance(tags,list):return 'ollama_unavailable'
  return 'ready' if installed(tags) or completed_receipt(root) else 'q8_not_installed'
 except (OSError,ValueError,KeyError,TypeError):return 'ollama_unavailable'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--record',action='store_true');a=p.parse_args()
 if a.record:
  models=Path(os.environ.get('OLLAMA_MODELS') or Path.home()/'.ollama'/'models')
  print(json.dumps(record_completion(a.root,local_tags(),models)))
 else:print(json.dumps({'status':queue_status(a.root),'historical_receipt':completed_receipt(a.root),'model_removal_performed':False}))
