"""NEURAL NEXUS: verified native safetensors inventory and bounded BERT embedding."""
import argparse,ctypes,hashlib,json,math,os,re,struct,sys
from pathlib import Path
import numpy as np
HEX=re.compile(r'^[a-f0-9]{64}$')
REPO=re.compile(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$')
LICENSES={'apache-2.0','mit','bsd-2-clause','bsd-3-clause','cc-by-4.0','cc0-1.0','isc'}
SUPPORTED={'sentence-transformers/all-MiniLM-L6-v2':'mean','BAAI/bge-small-en-v1.5':'cls'}
def digest(p,algorithm='sha256',prefix=b''):
 h=hashlib.new(algorithm);h.update(prefix)
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024**2),b''):h.update(chunk)
 return h.hexdigest()
def safe_file(folder,name):
 if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)?',name) or any(x in ('.','..') for x in name.split('/')):raise ValueError('unsafe path')
 p=folder/name
 if p.resolve().parent!=folder.resolve() and p.resolve().parent.parent!=folder.resolve():raise ValueError('path escape')
 if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(folder.resolve()):raise ValueError('missing file')
 return p
def verify_file(folder,f):
 p=safe_file(folder,f['name'])
 n=f['size']
 if type(n) is not int or n<=0 or p.stat().st_size!=n:raise ValueError('size mismatch')
 sha=f.get('sha')
 if sha:
  if not HEX.fullmatch(sha) or digest(p)!=sha:raise ValueError('sha256 mismatch')
 else:
  blob=f.get('blob')
  if not isinstance(blob,str) or not re.fullmatch('[a-f0-9]{40}',blob) or digest(p,'sha1',('blob '+str(n)+'\0').encode())!=blob:raise ValueError('blob mismatch')
 return p
def read_receipt(folder):
 p=safe_file(folder,'receipt.json')
 if p.stat().st_size>256*1024:raise ValueError('receipt budget')
 r=json.loads(p.read_text(encoding='utf8'))
 if not REPO.fullmatch(r.get('repo','')) or not re.fullmatch('[a-f0-9]{40}',r.get('revision','')) or r.get('license') not in LICENSES or r.get('native_verified') is not True or not HEX.fullmatch(r.get('digest','')):raise ValueError('invalid receipt')
 files=r.get('files')
 if not isinstance(files,list) or not 1<=len(files)<=32 or len({f['name'] for f in files})!=len(files):raise ValueError('invalid file list')
 if sum(f['size'] for f in files)!=r.get('total') or r['total']>5*10**9:raise ValueError('bundle budget')
 weights=[f for f in files if f['name']=='model.safetensors']
 if len(weights)!=1 or weights[0].get('sha')!=r['digest']:raise ValueError('missing native weights')
 for f in files:verify_file(folder,f)
 with SafeWeights(safe_file(folder,'model.safetensors')) as w:
  if not w.has_float:raise ValueError('not floating point')
 return r
def inventory(root,repo=None):
 root=Path(root).resolve();out=[];seen=set()
 for bucket in ('neural','tiny'):
  base=root/bucket
  if not base.is_dir() or base.is_symlink() or base.resolve().parent!=root:continue
  for folder in sorted(base.iterdir())[:512]:
   if not folder.is_dir() or folder.is_symlink() or folder.resolve().parent!=base.resolve():continue
   try:
    if repo is not None and json.loads(safe_file(folder,'receipt.json').read_text(encoding='utf8')).get('repo')!=repo:continue
    r=read_receipt(folder)
    if r['digest'] in seen:continue
    seen.add(r['digest']);out.append({'repo':r['repo'],'revision':r['revision'],'digest':r['digest'],'license':r['license'],'task':r.get('task'),'size_bytes':r['total'],'runtime':'numpy-bert' if r['repo'] in SUPPORTED else 'catalog-only','weights_verified':True,'inference_verified':False,'folder':str(folder.relative_to(root))})
   except (OSError,ValueError,KeyError,TypeError,OverflowError):continue
 return out
class SafeWeights:
 def __init__(self,path):
  self.path=Path(path);self.file=None;self.has_float=False
 def __enter__(self):
  self.file=self.path.open('rb')
  try:
   raw=self.file.read(8)
   if len(raw)!=8:raise ValueError('header')
   n=struct.unpack('<Q',raw)[0]
   if not 0<n<=32*1024**2:raise ValueError('header budget')
   h=json.loads(self.file.read(n));self.base=8+n;self.rows={};intervals=[]
   if not isinstance(h,dict) or len(h)>10000:raise ValueError('tensor count')
   sizes={'F32':4,'F64':8,'F16':2,'BF16':2,'I32':4,'I64':8,'BOOL':1}
   for key,row in h.items():
    if key=='__metadata__':continue
    if not isinstance(row,dict) or row.get('dtype') not in sizes or re.search('quant|qweight|qzeros|absmax',key,re.I):raise ValueError('non-native dtype')
    shape=row['shape'];a,b=row['data_offsets'];dt=row['dtype']
    if not isinstance(shape,list) or len(shape)>8 or any(type(v) is not int or v<0 for v in shape) or type(a) is not int or type(b) is not int or not 0<=a<=b<=self.path.stat().st_size-self.base or b-a!=math.prod(shape)*sizes[dt]:raise ValueError('tensor bounds')
    intervals.append((a,b));self.rows[key]=(dt,shape,a,b);self.has_float|=dt in ('F32','F64','F16','BF16')
   intervals.sort()
   if not intervals or any(intervals[i][1]!=intervals[i+1][0] for i in range(len(intervals)-1)) or intervals[0][0]!=0 or intervals[-1][1]!=self.path.stat().st_size-self.base:raise ValueError('tensor layout')
   return self
  except Exception:self.file.close();raise
 def __exit__(self,*args):self.file.close()
 def get(self,key):
  if key not in self.rows and 'bert.'+key in self.rows:key='bert.'+key
  if key not in self.rows:raise ValueError('missing tensor '+key)
  dt,shape,a,b=self.rows[key]
  if dt not in ('F32','F64','F16','BF16') or b-a>256*1024**2:raise ValueError('unsupported tensor')
  self.file.seek(self.base+a);data=self.file.read(b-a)
  if len(data)!=b-a:raise ValueError('short tensor')
  if dt=='BF16':v=(np.frombuffer(data,dtype='<u2').astype(np.uint32)<<16).view(np.float32)
  else:v=np.frombuffer(data,dtype={'F32':'<f4','F64':'<f8','F16':'<f2'}[dt]).astype(np.float32,copy=False)
  v=v.reshape(shape)
  if not np.isfinite(v).all():raise ValueError('nonfinite tensor')
  return v
def norm(x,w,b,eps):return (x-x.mean(axis=-1,keepdims=True))/np.sqrt(x.var(axis=-1,keepdims=True)+eps)*w+b
def bert_forward(w,c,ids,pool):
 h,layers,heads,intermediate=(c[k] for k in ('hidden_size','num_hidden_layers','num_attention_heads','intermediate_size'))
 if any(type(x) is not int for x in (h,layers,heads,intermediate)) or not 1<=h<=768 or not 1<=layers<=12 or not 1<=heads<=16 or h%heads or not 1<=intermediate<=3072 or not 1<=len(ids)<=128 or pool not in ('mean','cls'):raise ValueError('architecture budget')
 if c.get('hidden_act','gelu')!='gelu' or c.get('position_embedding_type','absolute')!='absolute':raise ValueError('unsupported BERT variant')
 eps=float(c.get('layer_norm_eps',1e-12))
 if not 0<eps<=.01:raise ValueError('norm epsilon')
 def ln(x,p):return norm(x,w.get(p+'.weight'),w.get(p+'.bias'),eps)
 def dense(x,p):return x@w.get(p+'.weight').T+w.get(p+'.bias')
 t=len(ids);words=w.get('embeddings.word_embeddings.weight')
 if any(type(i) is not int or not 0<=i<len(words) for i in ids):raise ValueError('token bounds')
 x=ln(words[ids]+w.get('embeddings.position_embeddings.weight')[:t]+w.get('embeddings.token_type_embeddings.weight')[0],'embeddings.LayerNorm')
 for i in range(layers):
  p='encoder.layer.'+str(i)+'.'
  q,k,v=[dense(x,p+'attention.self.'+z).reshape(t,heads,h//heads).transpose(1,0,2) for z in ('query','key','value')]
  att=q@k.transpose(0,2,1)/math.sqrt(h//heads);att-=att.max(axis=-1,keepdims=True);att=np.exp(att);att/=att.sum(axis=-1,keepdims=True)
  context=(att@v).transpose(1,0,2).reshape(t,h)
  y=ln(x+dense(context,p+'attention.output.dense'),p+'attention.output.LayerNorm')
  z=dense(y,p+'intermediate.dense');z=.5*z*(1+np.vectorize(math.erf,otypes=[np.float32])(z/math.sqrt(2)))
  x=ln(y+dense(z,p+'output.dense'),p+'output.LayerNorm')
 out=x.mean(axis=0) if pool=='mean' else x[0]
 mag=np.linalg.norm(out)
 if not np.isfinite(mag) or mag<=0:raise ValueError('invalid embedding')
 return out/mag
def available_ram():
 if os.name=='nt':
  from ctypes import wintypes as wt
  class M(ctypes.Structure):_fields_=[('length',wt.DWORD),('load',wt.DWORD)]+[(x,ctypes.c_ulonglong) for x in ('total','avail','page','pageavail','virtual','virtualavail','extended')]
  m=M();m.length=ctypes.sizeof(m)
  if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):raise ValueError('RAM unavailable')
  return m.avail
 return os.sysconf('SC_AVPHYS_PAGES')*os.sysconf('SC_PAGE_SIZE')
def embed(root,repo,text):
 if repo not in SUPPORTED or not isinstance(text,str) or not 1<=len(text)<=2048:raise ValueError('unsupported embedding')
 candidates=inventory(root,repo)
 if len(candidates)!=1:raise ValueError('verified bundle unavailable')
 r=candidates[0];folder=Path(root).resolve()/r['folder']
 if r['size_bytes']>400*10**6 or available_ram()<r['size_bytes']*4+1024**3:raise ValueError('memory admission denied')
 receipt=read_receipt(folder);files={f['name']:f for f in receipt['files']}
 cfg=json.loads(verify_file(folder,files['config.json']).read_text(encoding='utf8'))
 if cfg.get('model_type')!='bert':raise ValueError('unsupported architecture')
 from tokenizers import Tokenizer
 tokenizer=Tokenizer.from_file(str(verify_file(folder,files['tokenizer.json'])));tokenizer.enable_truncation(max_length=128)
 ids=tokenizer.encode(text).ids
 with SafeWeights(verify_file(folder,files['model.safetensors'])) as w:out=bert_forward(w,cfg,ids,SUPPORTED[repo])
 return {'schema':'umbra.native.embedding.v1','model':repo,'revision':r['revision'],'weight_sha256':r['digest'],'dimensions':len(out),'embedding':out.tolist(),'inference_verified':True,'synthetic':True,'research_qualified':False,'production_authority':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--model');a=p.parse_args()
 if a.model:
  text=sys.stdin.read(2049);print(json.dumps(embed(a.root,a.model,text)))
 else:print(json.dumps({'models':inventory(a.root),'research_qualified':False,'production_authority':False}))
