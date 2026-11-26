"""Owner-local training bootstrap: bounded native public sources and isolated CPU runtime."""
import os,sys,time,subprocess,shutil,json,hashlib,re,urllib.request,urllib.parse,urllib.error,struct,http.client
from pathlib import Path
ROOT=Path.home()/'projects'/'umbra-train-native-20261124'
CAP=4500000000
FLOOR=25000000000
SOURCES=[
 ('Qwen/Qwen3-0.6B','c1899de289a04d12100db370d81485cdf75e47ca','f47f71177f32bcd101b7573ec9171e6a57f4f4d31148d38e382306f42996874b',1503300328),
 ('ibm-granite/granite-4.0-350m','bd8a1497065c0d6ba1ef19af6b0d2b14bacf71c2','21bc1ccaf0eb6a8a503addd93cb7422df71129de0a641a5525e4a665813b6dfc',704786224)]
ALLOW={'model.safetensors','config.json','tokenizer.json','tokenizer_config.json','generation_config.json','vocab.json','merges.txt','special_tokens_map.json','chat_template.jinja','LICENSE','README.md'}
def used():
 total=0
 def onerror(e):
  if not isinstance(e,FileNotFoundError):raise e
 for base,dirs,files in os.walk(ROOT,onerror=onerror,followlinks=False):
  for name in files:
   p=Path(base)/name
   try:
    if not p.is_symlink():total+=p.stat().st_size
   except FileNotFoundError:continue
 return total
def gate(n=0):
 if used()+n>CAP or shutil.disk_usage(ROOT).free-n<FLOOR:raise ValueError('training storage gate')
def log(*a):
 s=' '.join(map(str,a));print(s,flush=True)
 with (ROOT/'bootstrap.log').open('a',encoding='utf8') as f:f.write(time.strftime('%Y-%m-%d %H:%M:%S')+' '+s+'\n')
def get(url):return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'UMBRA-native-training/1.0'}),timeout=60)
def validate_tensor(p):
 with p.open('rb') as f:
  raw=f.read(8);n=struct.unpack('<Q',raw)[0]
  if not 0<n<32000000:raise ValueError('header size')
  h=json.loads(f.read(n))
  rows=[(k,v) for k,v in h.items() if k!='__metadata__']
  if not rows or not any(v['dtype'] in ('F16','BF16','F32','F64') for k,v in rows) or any(v['dtype'] not in ('F16','BF16','F32','F64','I32','I64','BOOL') or re.search('quant|qweight|qzeros|absmax',k,re.I) for k,v in rows):raise ValueError('non-native weights')
def digest(p,alg,prefix=b''):
 h=hashlib.new(alg,prefix)
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def download_verified(url,target,size,expected,algorithm='sha256',prefix=b'',opener=urllib.request.urlopen,attempts=5,gate_fn=None,range_bytes=4*1024**2):
 admit=gate_fn or gate
 if type(size) is not int or size<=0 or algorithm not in ('sha256','sha1') or not re.fullmatch('[a-f0-9]{64}' if algorithm=='sha256' else '[a-f0-9]{40}',expected):raise ValueError('invalid download identity')
 if type(attempts) is not int or not 1<=attempts<=20 or type(range_bytes) is not int or not 1<=range_bytes<=64*1024**2:raise ValueError('invalid transfer budget')
 part=target.with_name(target.name+'.part')
 def correct(p):return p.is_file() and not p.is_symlink() and p.stat().st_size==size and digest(p,algorithm,prefix)==expected
 if target.exists() or target.is_symlink():
  if correct(target):return
  raise ValueError('unexpected target: '+target.name)
 if part.is_symlink() or (part.exists() and not part.is_file()):raise ValueError('invalid partial')
 failures=0
 while True:
  offset=part.stat().st_size if part.exists() else 0
  if offset>size:raise ValueError('oversized partial')
  if offset==size:
   if not correct(part):raise ValueError('partial checksum mismatch')
   if target.exists() or target.is_symlink():raise ValueError('target changed')
   part.rename(target);return
  admit(size-offset)
  end=min(size-1,offset+range_bytes-1)
  ranged=offset>0 or end<size-1
  headers={'User-Agent':'UMBRA-native-training/1.1','Accept-Encoding':'identity'}
  if ranged:headers['Range']='bytes='+str(offset)+'-'+(str(end) if end<size-1 or size>range_bytes else '')
  try:
   with opener(urllib.request.Request(url,headers=headers),timeout=120) as response:
    if ranged:
     if response.status!=206 or response.headers.get('Content-Range')!=f'bytes {offset}-{end}/{size}':raise ValueError('range response mismatch')
    elif response.status!=200:raise ValueError('download status')
    if response.headers.get('Content-Encoding','identity').lower()!='identity':raise ValueError('encoded response')
    count=offset
    with part.open('ab' if offset else 'wb') as out:
     def append(block):
      nonlocal count
      if count+len(block)>end+1:raise ValueError('size mismatch')
      if block:
       admit(len(block));out.write(block);count+=len(block)
     try:
      while True:
       try:chunk=response.read(1024**2)
       except http.client.IncompleteRead as exc:
        append(exc.partial);raise
       if not chunk:break
       append(chunk)
     finally:
      out.flush();os.fsync(out.fileno())
   if count!=end+1:raise OSError('incomplete transfer')
   failures=0
  except (OSError,urllib.error.URLError,http.client.HTTPException) as e:
   failures+=1
   if failures>=attempts:raise
   if ranged and range_bytes>1024**2:range_bytes=max(1024**2,range_bytes//2)
   log('RETRY',target.name,type(e).__name__,'attempt',failures,'offset',part.stat().st_size if part.exists() else 0)
   time.sleep(min(30,2**failures))
TORCH_WHEEL='torch-2.8.0-cp311-cp311-win_amd64.whl'
TORCH_URL='https://files.pythonhosted.org/packages/84/57/2f64161769610cf6b1c5ed782bd8a780e18a3c9d48931319f2887fa9d0b1/'+TORCH_WHEEL
TORCH_SIZE=241366752
TORCH_SHA='8c7ef765e27551b2fbfc0f41bcf270e1292d9bf79f8e0724848b1682be6e80aa'
def fetch_source(repo,rev,sha,size):
 folder=ROOT/'sources'/(repo.replace('/','--')+'--'+rev[:12]);folder.mkdir(parents=True,exist_ok=True)
 with get('https://huggingface.co/api/models/'+repo+'/revision/'+rev+'?blobs=true') as f:m=json.load(f)
 if m.get('id')!=repo or m.get('sha')!=rev or m.get('private') is not False or m.get('gated') not in (False,None) or (m.get('cardData') or {}).get('license')!='apache-2.0':raise ValueError('source metadata')
 rows=[x for x in m['siblings'] if x['rfilename'] in ALLOW]
 w=next(x for x in rows if x['rfilename']=='model.safetensors')
 if w.get('size')!=size or (w.get('lfs') or {}).get('sha256')!=sha:raise ValueError('weight identity')
 receipts=[]
 for x in rows:
  name=x['rfilename'];n=x.get('size');h=(x.get('lfs') or {}).get('sha256');blob=x.get('blobId')
  if type(n) is not int or n<=0 or (name!='model.safetensors' and n>16000000) or not (h or blob):raise ValueError('file metadata')
  target=folder/name;part=folder/(name+'.part')
  def correct(p):return p.is_file() and not p.is_symlink() and p.stat().st_size==n and (digest(p,'sha256')==h if h else digest(p,'sha1',('blob '+str(n)+'\0').encode())==blob)
  if not correct(target):
   log('PULL',repo,name,n)
   download_verified('https://huggingface.co/'+repo+'/resolve/'+rev+'/'+urllib.parse.quote(name),target,n,h or blob,'sha256' if h else 'sha1',b'' if h else ('blob '+str(n)+'\0').encode())
  receipts.append({'name':name,'size':n,'sha256':digest(target,'sha256')})
 validate_tensor(folder/'model.safetensors')
 (folder/'receipt.json').write_text(json.dumps({'repo':repo,'revision':rev,'license':'apache-2.0','weights_sha256':sha,'native_verified':True,'files':receipts},indent=2),encoding='utf8')
 log('VERIFIED_SOURCE',repo,rev,size)
def cmd(args,env):
 gate()
 with (ROOT/'bootstrap.log').open('a',encoding='utf8') as f:
  p=subprocess.Popen(args,stdout=f,stderr=subprocess.STDOUT,env=env)
  try:
   while p.poll() is None:time.sleep(3);gate()
  except Exception:p.terminate();p.wait();raise
  if p.returncode:raise RuntimeError('dependency stage failed: '+str(p.returncode))
def torch_ready(py):
 try:
  r=subprocess.run([str(py),'-c','import torch; assert torch.__version__.split("+")[0]=="2.8.0"; assert torch.version.cuda is None; assert torch.ones(2).sum().item()==2'],capture_output=True,timeout=90)
  return r.returncode==0
 except (OSError,subprocess.TimeoutExpired):return False
def after_queue_ready():
 from acquisition_receipt import queue_status
 return queue_status(Path.home()/'projects'/'umbra-agentic-native-20261124')=='ready'
def main(after_queue=False):
 global FLOOR
 ROOT.mkdir(exist_ok=True)
 if (ROOT/'ready.json').exists():raise ValueError('already ready')
 if after_queue:
  if not after_queue_ready():raise ValueError('initial acquisition not verified')
  from storage_budget import budget
  FLOOR=budget(ROOT.parent/'umbra-agentic-native-20261124').floor
  if shutil.disk_usage(ROOT).free<FLOOR+max(0,CAP-used()):raise ValueError('insufficient post-acquisition headroom')
 elif shutil.disk_usage(ROOT).free<51000000000:raise ValueError('insufficient initial headroom for original queue')
 lock=ROOT/'bootstrap.lock'
 with lock.open('x') as f:f.write(str(os.getpid()))
 try:
  temp=ROOT/'tmp';temp.mkdir(exist_ok=True)
  env={**os.environ,'TMP':str(temp),'TEMP':str(temp),'PIP_NO_CACHE_DIR':'1','PIP_DISABLE_PIP_VERSION_CHECK':'1','HF_HUB_DISABLE_TELEMETRY':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
  venv=ROOT/'venv';py=venv/'Scripts'/'python.exe'
  if not py.exists():cmd([sys.executable,'-m','venv',str(venv)],env)
  if torch_ready(py):log('REUSE_VERIFIED_CPU_TORCH')
  else:
   log('PULL_OFFICIAL_WINDOWS_TORCH',TORCH_SIZE)
   wheel_dir=ROOT/'wheels';wheel_dir.mkdir(exist_ok=True);wheel=wheel_dir/TORCH_WHEEL
   download_verified(TORCH_URL,wheel,TORCH_SIZE,TORCH_SHA)
   log('INSTALL_CPU_TORCH')
   cmd([str(py),'-m','pip','install','--no-cache-dir','--timeout','120','--retries','5','--index-url','https://pypi.org/simple',str(wheel)],env)
   cmd([str(py),'-c','import torch; assert torch.version.cuda is None; assert torch.ones(2).sum().item()==2; print(torch.__version__,torch.version.cuda)'],env)
   if digest(wheel,'sha256')!=TORCH_SHA:raise ValueError('wheel changed')
   wheel.unlink()
  log('INSTALL_TRAINING_STACK')
  for package in ('safetensors==0.6.2','transformers==4.57.3','accelerate==1.12.0','peft==0.18.0'):
   for attempt in range(3):
    try:
     cmd([str(py),'-m','pip','install','--no-cache-dir','--timeout','120','--retries','5','--index-url','https://pypi.org/simple',package],env);break
    except RuntimeError:
     if attempt==2:raise
     log('DEPENDENCY_RETRY',package,attempt+1);time.sleep(30*(attempt+1))
  cmd([str(py),'-c','import torch,transformers,peft,accelerate,safetensors; print(torch.__version__,transformers.__version__,peft.__version__,accelerate.__version__,safetensors.__version__); assert torch.version.cuda is None; assert torch.ones(2).sum().item()==2'],env)
  log('RUNTIME_VERIFIED',used())
  for row in SOURCES:fetch_source(*row)
  (ROOT/'ready.json').write_text(json.dumps({'runtime_verified':True,'native_sources_verified':True,'training_verified':False,'used_bytes':used(),'sources':[x[0] for x in SOURCES]}),encoding='utf8')
  log('BOOTSTRAP_READY',used())
 finally:lock.unlink(missing_ok=True)
if __name__=='__main__':
 if sys.argv[1:] not in ([],['--after-queue']):raise ValueError('invalid bootstrap mode')
 main('--after-queue' in sys.argv)
