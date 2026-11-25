"""One bounded scheduled invocation; owner-local, no paid services or external code."""
import argparse,json,os,time
from pathlib import Path
from infinity import refresh_catalog,run_cycle,rotate
from hf_weight_cache import lock
from urllib.request import urlopen
def write_status(root,result):
 p=root/'infinity'/'service-status.json';tmp=p.with_suffix('.tmp')
 with tmp.open('w',encoding='utf8') as f:json.dump({'timestamp':int(time.time()),**result},f,indent=2);f.flush();os.fsync(f.fileno())
 os.replace(tmp,p)
def queue_ready(root):
 if (root/'active.lock').exists():return 'deferred_acquisition'
 log=root/'acquisition.log'
 if not log.is_file():return 'initial_queue_not_verified'
 with log.open('rb') as f:
  f.seek(max(0,log.stat().st_size-65536));tail=f.read().decode('utf8','replace')
 if not any(' DONE ' in line for line in tail.splitlines()):return 'initial_queue_not_verified'
 try:
  with urlopen('http://127.0.0.1:11434/api/tags',timeout=10) as r:tags=json.load(r)
  if not any(x.get('name')=='qwen3.8:27b-q8_0' for x in tags['models']):return 'q8_not_installed'
 except Exception:return 'ollama_unavailable'
 return 'ready'
def main(root):
 root=root.resolve();d=root/'infinity';d.mkdir(exist_ok=True)
 try:
  with lock(d/'service.lock'):
   result={'status':queue_ready(root)}
   try:result['discovered']=len(refresh_catalog(root)['models'])
   except Exception as e:result['discovery_error']=type(e).__name__
   if result['status']=='ready':
    state=run_cycle(root);result.update({'status':state['status'],'cycles':state.get('cycles',0),'champion':state.get('champion')})
    if state['status']=='completed':result['rotated']=rotate(root)
   write_status(root,result)
   print(json.dumps(result),flush=True)
 except FileExistsError:print(json.dumps({'status':'service_busy'}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args()
 main(a.root)
