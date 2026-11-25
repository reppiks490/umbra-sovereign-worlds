"""Conservative owner-local acquisition recovery, called by the existing service."""
import csv,ctypes,json,os,re,shutil,subprocess,sys,time
from pathlib import Path
from urllib.request import urlopen
TAG='qwen3.8:27b-q8_0'
BLOB='sha256-2bb22714289826d7b9e0ba376c3ce47d08bce39abe598745857c44d88c09bdbf'
TOTAL=29047084384
RESERVE=25000000000
def remaining_bytes(blobs,blob=BLOB,total=TOTAL):
 try:
  paths=list(blobs.glob(blob+'-partial-*'))
  if not paths or len(paths)>128:return None
  rows=[json.loads(p.read_text(encoding='utf8')) for p in paths if p.is_file() and not p.is_symlink()]
  if len(rows)!=len(paths):return None
  end=0;completed=0
  for i,r in enumerate(sorted(rows,key=lambda r:r['Offset'])):
   n,offset,size,done=[r[k] for k in ('N','Offset','Size','Completed')]
   if any(type(x) is not int for x in (n,offset,size,done)) or n!=i or offset!=end or size<=0 or not 0<=done<=size:return None
   end+=size;completed+=done
  return total-completed if end==total else None
 except (OSError,ValueError,TypeError,KeyError):return None
def plan_recovery(installed,pull_alive,queue_locked,queue_done,free,remaining):
 if installed:
  if queue_locked:return {'status':'queue_running'}
  if queue_done:return {'status':'complete'}
  return {'status':'resume_queue' if free>=RESERVE else 'deferred_queue_storage'}
 if pull_alive:return {'status':'pull_running'}
 if remaining is None:return {'status':'deferred_partial_identity'}
 return {'status':'resume_q8' if free>=RESERVE+remaining else 'deferred_storage'}
def pid_alive(pid):
 if type(pid) is not int or pid<=0:return False
 if os.name!='nt':return True
 k=ctypes.WinDLL('kernel32',use_last_error=True)
 k.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong];k.OpenProcess.restype=ctypes.c_void_p
 k.GetExitCodeProcess.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_ulong)]
 k.CloseHandle.argtypes=[ctypes.c_void_p]
 h=k.OpenProcess(0x1000,False,pid)
 if not h:return ctypes.get_last_error()!=87
 try:
  code=ctypes.c_ulong()
  return not k.GetExitCodeProcess(h,ctypes.byref(code)) or code.value==259
 finally:k.CloseHandle(h)
def ollama_idle_pull():
 # More than one Ollama CLI/server process is ambiguous. Never start a competing pull.
 p=subprocess.run(['tasklist','/FI','IMAGENAME eq ollama.exe','/FO','CSV','/NH'],capture_output=True,text=True,timeout=10,check=True)
 return sum(1 for r in csv.reader(p.stdout.splitlines()) if r and r[0].lower()=='ollama.exe')<=1
def recover(root):
 root=Path(root);p=root/'download-recovery.json'
 try:state=json.loads(p.read_text(encoding='utf8'))
 except (OSError,ValueError):state={}
 try:
  with urlopen('http://127.0.0.1:11434/api/tags',timeout=10) as f:
   installed=any(x.get('name')==TAG for x in json.load(f)['models'])
 except Exception:return {'status':'deferred_ollama_unavailable'}
 log=root/'acquisition.log';done=False
 if log.exists():
  with log.open('rb') as f:
   f.seek(max(0,log.stat().st_size-65536));tail=f.read().decode('utf8','replace')
  # The most recent terminal status is authoritative, not an older DONE line.
  terminal=[x for x in tail.splitlines() if ' DONE ' in x or ' STOP_' in x or ' WAIT_Q8 ' in x]
  done=bool(terminal and ' DONE ' in terminal[-1])
 blobs=Path.home()/'.ollama'/'models'/'blobs'
 remaining=0 if installed else remaining_bytes(blobs)
 plan=plan_recovery(installed,pid_alive(state.get('pull_pid')), (root/'active.lock').exists(),done,shutil.disk_usage(root).free,remaining)
 if plan['status'] not in ('resume_q8','resume_queue'):return plan
 if time.time()-state.get('last_attempt',0)<900:return {'status':'deferred_retry_cooldown'}
 if plan['status']=='resume_q8':
  if not ollama_idle_pull():return {'status':'deferred_other_ollama_process'}
  args=['ollama','pull',TAG];key='pull_pid'
 else:
  script=Path.home()/'projects'/'umbra-polymind-acquisition-pinned'/'agentic_acquire_20261124.py'
  py=Path(sys.base_prefix)/'python.exe'
  if not script.is_file() or not py.is_file():return {'status':'deferred_queue_runtime'}
  args=[str(py),'-u',str(script)];key='queue_pid'
  if pid_alive(state.get(key)):return {'status':'queue_starting'}
 state['last_attempt']=int(time.time())
 with (root/'download-recovery.log').open('a',encoding='utf8') as out:
  out.write('\n'+time.strftime('%Y-%m-%d %H:%M:%S')+' '+plan['status']+'\n');out.flush()
  proc=subprocess.Popen(args,stdout=out,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 state[key]=proc.pid
 temp=p.with_suffix('.tmp');temp.write_text(json.dumps(state),encoding='utf8');os.replace(temp,p)
 return {'status':plan['status']+'_started','pid':proc.pid,'remaining_bytes':remaining}
