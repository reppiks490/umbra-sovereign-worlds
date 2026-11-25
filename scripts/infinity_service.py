"""One bounded scheduled invocation; owner-local, no paid services or external code."""
import argparse,json,os,time,subprocess,shutil,sys
from pathlib import Path
from infinity import refresh_catalog,run_cycle,rotate
from acquisition_recovery import recover
from neural_priority import resume_priority
from intelligence_resources import resume as resume_resources
from learning_workspace import refresh as refresh_learning_workspace
from hf_weight_cache import lock
from native_lora_train import available_ram,required_memory
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
def gap_command(root,status):
 return [shutil.which('node') or 'node',str(Path(__file__).resolve().with_name('gap_audit.mjs')),str(root),'probe' if status=='ready' else 'audit']
def run_gap_audit(root,status):
 p=subprocess.run(gap_command(root,status),capture_output=True,text=True,timeout=300,check=True)
 r=json.loads(p.stdout)
 return {k:r.get(k) for k in ('status','probe_status','total_probes','high_confidence_errors','discovered_candidates')}
def bootstrap_plan(training,status,free,last,now,used_bytes=0):
 if (training/'bootstrap.lock').exists():return {'status':'running'}
 if (training/'ready.json').exists():return {'status':'ready_marker'}
 if now-last<(1800 if status=='ready' else 21600):return {'status':'deferred_cooldown'}
 after=status=='ready'
 if free<(3000000000+max(0,4500000000-used_bytes) if after else 51000000000):return {'status':'deferred_storage'}
 return {'status':'eligible','after_queue':after}
def resume_bootstrap(root,training,status):
 training.mkdir(exist_ok=True)
 stamp=training/'service-attempt.json';now=int(time.time())
 try:last=int(json.loads(stamp.read_text(encoding='utf8'))['timestamp'])
 except (OSError,ValueError,KeyError,TypeError):last=0
 from native_training_bootstrap import used
 plan=bootstrap_plan(training,status,shutil.disk_usage(training).free,last,now,used() if status=='ready' else 0)
 if plan['status']!='eligible':return plan
 # The isolated native training venv is not used to create itself.
 python=Path(sys.base_prefix)/'python.exe'
 if not python.is_file():return {'status':'deferred_base_python'}
 stamp.write_text(json.dumps({'timestamp':now}),encoding='utf8')
 args=[str(python),'-u',str(Path(__file__).resolve().with_name('native_training_bootstrap.py'))]
 if plan['after_queue']:args.append('--after-queue')
 with (training/'service-bootstrap.log').open('a',encoding='utf8') as out:
  proc=subprocess.Popen(args,stdout=out,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 return {'status':'started','pid':proc.pid,'after_queue':plan['after_queue']}
def swarm_command(root,training):
 return [shutil.which('node') or 'node',str(Path(__file__).resolve().with_name('swarm_cycle.mjs')),str(root),'init' if (training/'bootstrap.lock').exists() else 'cycle']
def market_command(root,training,status):
 return [shutil.which('node') or 'node',str(Path(__file__).resolve().with_name('market_cycle.mjs')),str(root),'cycle' if status=='ready' and not (training/'bootstrap.lock').exists() else 'audit']
def omni_command(root,training,status):
 return [shutil.which('node') or 'node',str(Path(__file__).resolve().with_name('omni_cycle.mjs')),str(root),'cycle' if status=='ready' and not (training/'bootstrap.lock').exists() else 'audit']
def repository_command(root,training,status):
 ready=False
 if status=='ready' and not (training/'bootstrap.lock').exists() and not (root/'active.lock').exists():
  try:
   marker=json.loads((training/'ready.json').read_text(encoding='utf8'))
   ready=marker.get('runtime_verified') is True and marker.get('native_sources_verified') is True
  except (OSError,ValueError):pass
 return [shutil.which('node') or 'node',str(Path(__file__).resolve().with_name('repository_cycle.mjs')),str(root),'ready' if ready else 'audit']
def curriculum_ready(result):
 expected={'qwen3:0.6b','granite4:350m'}
 for stage in ('megaswarm','market_academy','omni_academy','repository_fabric'):
  if stage+'_error' in result:return False
  if result.get(stage,{}).get('status')!=('indexed' if stage=='repository_fabric' else 'completed'):return False
 for stage in ('market_academy','omni_academy'):
  if {x.get('model') for x in result[stage].get('corpora',[])}!=expected:return False
 rows=result['repository_fabric'].get('repository_learning',{}).get('corpora',[])
 if len(rows)!=2 or {r.get('model') for r in rows}!={'qwen3-0.6b','granite4-350m'}:return False
 return all(type(r.get('training')) is int and 120<=r['training']<=128 and type(r.get('retention')) is int and 28<=r['retention']<=32 and type(r.get('transfer')) is int and 28<=r['transfer']<=32 and type(r.get('repository_examples')) is int and r['repository_examples']>0 for r in rows)
def native_training_plan(root,training,status,free):
 if (training/'bootstrap.lock').exists():return {'status':'deferred_bootstrap'}
 if status!='ready':return {'status':status}
 try:ready=json.loads((training/'ready.json').read_text(encoding='utf8'))
 except (OSError,ValueError):return {'status':'deferred_bootstrap'}
 if ready.get('runtime_verified') is not True or ready.get('native_sources_verified') is not True:return {'status':'deferred_bootstrap'}
 candidates=[m for m in ('granite4:350m','qwen3:0.6b') if free>=required_memory(m)]
 if not candidates:return {'status':'deferred_memory','free_bytes':free}
 now=int(time.time());eligible=[]
 for m in candidates:
  p=root/'megaswarm'/'corpora'/(m.replace(':','-')+'.json')
  stamp=root/'experience'/'llm_adapters'/m.replace(':','-')/'last-attempt.json'
  if not p.is_file():continue
  try:last=int(json.loads(stamp.read_text(encoding='utf8'))['timestamp'])
  except (OSError,ValueError,KeyError,TypeError):last=0
  if now-last>=86400:eligible.append((last,m,p,stamp))
 if not eligible:return {'status':'deferred_cooldown_or_corpus'}
 _,m,p,stamp=min(eligible,key=lambda x:(x[0],x[1]))
 return {'status':'eligible','model':m,'corpus':str(p),'stamp':str(stamp)}
def run_native_training(root,training,status):
 plan=native_training_plan(root,training,status,available_ram())
 if plan['status']!='eligible':return plan
 try:
  with urlopen('http://127.0.0.1:11434/api/ps',timeout=10) as f:
   if json.load(f)['models']:return {'status':'deferred_busy'}
 except Exception:return {'status':'deferred_runtime'}
 py=training/'venv'/'Scripts'/'python.exe'
 if not py.is_file():return {'status':'deferred_runtime'}
 if (root/'active.lock').exists():return {'status':'deferred_acquisition'}
 stamp=Path(plan['stamp']);stamp.parent.mkdir(parents=True,exist_ok=True)
 stamp.write_text(json.dumps({'timestamp':int(time.time())}),encoding='utf8')
 p=subprocess.run([str(py),str(Path(__file__).resolve().with_name('native_lora_train.py')),'--root',str(training),'--workspace',str(root/'experience'),'--model',plan['model'],'--corpus',plan['corpus'],'--steps','4'],capture_output=True,text=True,timeout=1200,check=True)
 return json.loads(p.stdout.splitlines()[-1])
def main(root):
 root=root.resolve();d=root/'infinity';d.mkdir(exist_ok=True)
 try:
  with lock(d/'service.lock'):
   result={'status':queue_ready(root)}
   try:result['download_recovery']=recover(root)
   except Exception as e:result['download_recovery_error']=type(e).__name__
   result['status']=queue_ready(root)
   ready=result['status']
   training=Path.home()/'projects'/'umbra-train-native-20261124'
   try:
    result['neural_priority']=resume_priority(root,training,ready)
    if result['neural_priority']['status'] in ('started','running'):
     ready='deferred_acquisition';result['status']=ready
   except Exception as e:result['neural_priority_error']=type(e).__name__
   try:result['discovered']=len(refresh_catalog(root)['models'])
   except Exception as e:result['discovery_error']=type(e).__name__
   if result['status']=='ready':
    state=run_cycle(root);result.update({'status':state['status'],'cycles':state.get('cycles',0),'champion':state.get('champion')})
    if state['status']=='completed':result['rotated']=rotate(root)
   try:result['intelligence_gap_audit']=run_gap_audit(root,ready if not (training/'bootstrap.lock').exists() else 'deferred_bootstrap')
   except Exception as e:result['gap_audit_error']=type(e).__name__
   try:result['training_bootstrap']=resume_bootstrap(root,training,ready)
   except Exception as e:result['training_bootstrap_error']=type(e).__name__
   try:
    result['intelligence_resources']=resume_resources(root,training,ready)
    if result['intelligence_resources']['status'] in ('started','running'):
     ready='deferred_acquisition';result['status']=ready
   except Exception as e:result['intelligence_resources_error']=type(e).__name__
   try:
    p=subprocess.run(swarm_command(root,training),capture_output=True,text=True,timeout=300,check=True)
    result['megaswarm']=json.loads(p.stdout.splitlines()[-1])
   except Exception as e:result['megaswarm_error']=type(e).__name__
   try:
    p=subprocess.run(market_command(root,training,ready),capture_output=True,text=True,timeout=120,check=True)
    result['market_academy']=json.loads(p.stdout.splitlines()[-1])
   except Exception as e:result['market_academy_error']=type(e).__name__
   try:
    p=subprocess.run(omni_command(root,training,ready),capture_output=True,text=True,timeout=120,check=True)
    result['omni_academy']=json.loads(p.stdout.splitlines()[-1])
   except Exception as e:result['omni_academy_error']=type(e).__name__
   try:
    p=subprocess.run(repository_command(root,training,ready),capture_output=True,text=True,timeout=120,check=True)
    result['repository_fabric']=json.loads(p.stdout.splitlines()[-1])
   except Exception as e:result['repository_fabric_error']=type(e).__name__
   try:result['learning_workspace']=refresh_learning_workspace(root) if curriculum_ready(result) else {'status':'deferred_incomplete_curriculum'}
   except Exception as e:result['learning_workspace_error']=type(e).__name__
   try:result['native_training']=run_native_training(root,training,ready) if result.get('learning_workspace',{}).get('status')=='ready' else {'status':'deferred_incomplete_curriculum_or_replay'}
   except Exception as e:result['native_training_error']=type(e).__name__
   write_status(root,result)
   print(json.dumps(result),flush=True)
 except FileExistsError:print(json.dumps({'status':'service_busy'}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args()
 main(a.root)
