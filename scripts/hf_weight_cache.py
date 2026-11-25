"""Owner-local Hugging Face-backed cache. Only exact public original weights are evictable."""
import argparse,contextlib,hashlib,json,os,re,shutil,urllib.request,urllib.parse
from pathlib import Path
from agentic_native import read_receipt,digest,SafeWeights,LICENSES,REPO,HEX
MIN_FREE=8*10**9 # 5 GB Windows + 3 GB learning workspace
MAX_WEIGHT=5*10**9
WEIGHT='model.safetensors'
def request(url):
 return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'UMBRA-weight-cache/1.0'}),timeout=45)
def metadata(repo,rev):
 with request('https://huggingface.co/api/models/'+repo+'/revision/'+rev+'?blobs=true') as r:
  raw=r.read(16*1024**2+1)
 if len(raw)>16*1024**2:raise ValueError('metadata budget')
 return json.loads(raw)
def stream(repo,rev):
 return request('https://huggingface.co/'+repo+'/resolve/'+rev+'/'+WEIGHT)
def receipt(folder):
 p=folder/'receipt.json'
 if p.is_symlink() or not p.is_file() or p.stat().st_size>256*1024:raise ValueError('receipt missing')
 r=json.loads(p.read_text(encoding='utf8'))
 if not REPO.fullmatch(r.get('repo','')) or not re.fullmatch('[a-f0-9]{40}',r.get('revision','')) or r.get('license') not in LICENSES or r.get('native_verified') is not True or not HEX.fullmatch(r.get('digest','')):raise ValueError('receipt invalid')
 if folder.name!=r['repo'].replace('/','--')+'--'+r['revision'][:12]:raise ValueError('folder identity mismatch')
 files=r.get('files')
 if not isinstance(files,list) or not 1<=len(files)<=32:raise ValueError('invalid receipt files')
 weights=[x for x in files if x.get('name')==WEIGHT]
 if len(weights)!=1:raise ValueError('missing original weight')
 w=weights[0]
 if w.get('sha')!=r['digest'] or type(w.get('size')) is not int or not 0<w['size']<=MAX_WEIGHT:raise ValueError('weight metadata')
 return r,w
@contextlib.contextmanager
def lock(path):
 with path.open('x',encoding='utf8') as f:f.write(str(os.getpid()))
 try:yield
 finally:path.unlink()
class Cache:
 def __init__(self,root,metadata=metadata,stream=stream,free=None):
  self.root=Path(root).resolve();self.metadata=metadata;self.stream=stream;self.free=free or (lambda:shutil.disk_usage(self.root).free)
 def folders(self):
  for bucket in ('neural','tiny'):
   base=self.root/bucket
   if not base.is_dir() or base.is_symlink() or base.resolve().parent!=self.root:continue
   for folder in sorted(base.iterdir())[:512]:
    if folder.is_dir() and not folder.is_symlink() and folder.resolve().parent==base.resolve():
     try:r,w=receipt(folder)
     except (OSError,ValueError,TypeError,KeyError):continue
     yield folder,r,w
 def find(self,sha):
  if not isinstance(sha,str) or not HEX.fullmatch(sha):raise ValueError('invalid digest')
  matches=[x for x in self.folders() if x[1]['digest']==sha]
  if len(matches)!=1:raise ValueError('weight identity missing or ambiguous')
  return matches[0]
 def marker(self,folder,r,w):
  p=folder/'offloaded.json'
  if not p.exists():return False
  if p.is_symlink() or p.stat().st_size>4096:raise ValueError('invalid marker')
  return json.loads(p.read_text(encoding='utf8'))==self.marker_value(r,w)
 def marker_value(self,r,w):
  return {'schema':'umbra.hf-cache.v1','repo':r['repo'],'revision':r['revision'],'digest':r['digest'],'size':w['size'],'source':'huggingface-public'}
 def remote_check(self,r,w):
  m=self.metadata(r['repo'],r['revision'])
  lic=(m.get('cardData') or {}).get('license') or next((t[8:] for t in m.get('tags',[]) if isinstance(t,str) and t.startswith('license:')),None)
  rows=[x for x in m.get('siblings',[]) if x.get('rfilename')==WEIGHT]
  if m.get('id')!=r['repo'] or m.get('sha')!=r['revision'] or m.get('private') is not False or m.get('gated') not in (False,None) or lic!=r['license'] or len(rows)!=1 or rows[0].get('size')!=w['size'] or (rows[0].get('lfs') or {}).get('sha256')!=r['digest']:raise ValueError('public pinned source not verified')
 def list(self):
  out=[]
  for folder,r,w in self.folders():
   p=folder/WEIGHT;status='missing'
   try:
    if p.exists():status='local' if not p.is_symlink() and p.stat().st_size==w['size'] and digest(p)==r['digest'] else 'modified'
    elif self.marker(folder,r,w):status='remote'
   except (OSError,ValueError):status='unknown'
   out.append({'repo':r['repo'],'revision':r['revision'],'digest':r['digest'],'size_bytes':w['size'],'task':r.get('task'),'license':r['license'],'status':status,'source':'https://huggingface.co/'+r['repo']+'/tree/'+r['revision']})
  return out
 def evict(self,sha):
  with lock(self.root/'active.lock'),lock(self.root/'cache-use.lock'):
   folder,r,w=self.find(sha);p=folder/WEIGHT
   if p.is_symlink() or not p.is_file():raise ValueError('local original unavailable')
   read_receipt(folder);self.remote_check(r,w)
   marker=folder/'offloaded.json'
   if marker.exists():
    if not self.marker(folder,r,w):raise ValueError('marker mismatch')
   else:
    with marker.open('x',encoding='utf8') as f:json.dump(self.marker_value(r,w),f);f.flush();os.fsync(f.fileno())
   if digest(p)!=sha:raise ValueError('weight changed')
   p.unlink()
   return {'status':'remote','digest':sha,'released_logical_bytes':w['size']}
 def ensure(self,sha):
  with lock(self.root/'active.lock'),lock(self.root/'cache-use.lock'):
   folder,r,w=self.find(sha);p=folder/WEIGHT
   if p.exists():
    read_receipt(folder);return {'status':'local','digest':sha,'downloaded_bytes':0}
   if not self.marker(folder,r,w):raise ValueError('not a registered offload')
   self.remote_check(r,w)
   if self.free()-w['size']<MIN_FREE:raise ValueError('storage reserve')
   temp=folder/(WEIGHT+'.restore-part');n=0;h=hashlib.sha256()
   if temp.exists() or temp.is_symlink():raise ValueError('prior staging file requires owner review')
   try:
    with self.stream(r['repo'],r['revision']) as src,temp.open('xb') as out:
     while True:
      block=src.read(1024**2)
      if not block:break
      n+=len(block)
      if n>w['size'] or self.free()-len(block)<MIN_FREE:raise ValueError('storage reserve or size mismatch')
      h.update(block);out.write(block)
     out.flush();os.fsync(out.fileno())
    if n!=w['size'] or h.hexdigest()!=sha:raise ValueError('restore integrity')
    with SafeWeights(temp) as weights:
     if not weights.has_float:raise ValueError('not native weights')
    if p.exists():raise ValueError('destination changed')
    temp.rename(p)
    read_receipt(folder)
    return {'status':'local','digest':sha,'downloaded_bytes':n}
   finally:
    if temp.exists():temp.unlink()
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',required=True,type=Path);a.add_argument('action',choices=['list','evict','ensure']);a.add_argument('digest',nargs='?');q=a.parse_args()
 c=Cache(q.root)
 if q.action=='list':print(json.dumps({'models':c.list()}))
 elif not q.digest:a.error('exact SHA-256 required')
 else:print(json.dumps(getattr(c,q.action)(q.digest)))
