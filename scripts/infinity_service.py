"""One bounded scheduled invocation; owner-local, no paid services or external code."""
import argparse,json,os,time,subprocess,shutil,sys
from pathlib import Path
from infinity import refresh_catalog,run_cycle,rotate
from acquisition_recovery import recover
from neural_priority import resume_priority
from intelligence_resources import resume as resume_resources
from campaign_baselines import benchmark as benchmark_baselines
from chronos_tournament import campaign as chronos_campaign
from learning_workspace import refresh as refresh_learning_workspace
from source_knowledge import refresh as refresh_source_knowledge, learning_policy
from student_council import run as council_cycle
from research_portfolio import run as portfolio_cycle,service_due
from icarus_knowledge import refresh as refresh_icarus
from icarus_code_index import run as refresh_code_index
from capability_frontier import run as refresh_frontier
from source_training_schedule import run as source_training_cycle
from human_corpus import audit as audit_human_corpus
from hf_weight_cache import lock
from native_lora_train import available_ram,required_memory
from urllib.request import urlopen
def write_status(root,result):
 p=root/'infinity'/'service-status.json';tmp=p.with_suffix('.tmp')
 with tmp.open('w',encoding='utf8') as f:json.dump({'timestamp':int(time.time()),**result},f,indent=2);f.flush();os.fsync(f.fileno())
 os.replace(tmp,p)
def queue_ready(root):
 from acquisition_receipt import queue_status
 return queue_status(root)
def gap_command(root,status):
 return [shutil.which('node') or 'node',str(Path(__file__).resolve().with_name('gap_audit.mjs')),str(root),'probe' if status=='ready' else 'audit']
def run_gap_audit(root,status):
 p=subprocess.run(gap_command(root,status),capture_output=True,text=True,timeout=300,check=True)
 r=json.loads(p.stdout)
 return {k:r.get(k) for k in ('status','probe_status','total_probes','high_confidence_errors','discovered_candidates')}
def bootstrap_plan(training,status,free,last,now,used_bytes=0,*,floor=3000000000):
 if (training/'bootstrap.lock').exists():return {'status':'running'}
 if (training/'ready.json').exists():return {'status':'ready_marker'}
 if now-last<(1800 if status=='ready' else 21600):return {'status':'deferred_cooldown'}
 after=status=='ready'
 if free<(floor+max(0,4500000000-used_bytes) if after else 51000000000):return {'status':'deferred_storage'}
 return {'status':'eligible','after_queue':after}
def resume_bootstrap(root,training,status):
 training.mkdir(exist_ok=True)
 if (training/'bootstrap.lock').exists():return {'status':'running'}
 if (training/'ready.json').exists():return {'status':'ready_marker'}
 from storage_budget import budget
 try:floor=budget(root).floor if status=='ready' else 3000000000
 except (OSError,ValueError,TypeError,KeyError):return {'status':'deferred_storage_policy'}
 stamp=training/'service-attempt.json';now=int(time.time())
 try:last=int(json.loads(stamp.read_text(encoding='utf8'))['timestamp'])
 except (OSError,ValueError,KeyError,TypeError):last=0
 from native_training_bootstrap import used
 plan=bootstrap_plan(training,status,shutil.disk_usage(training).free,last,now,used() if status=='ready' else 0,floor=floor)
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
def resource_queue_status(status,bootstrap):
 return 'deferred_bootstrap' if bootstrap.get('status') in ('started','running') else status
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
   try:
    evidence=benchmark_baselines()
    result['campaign_baselines']={'scope':evidence['scope'],'case_sha256':evidence['case_sha256'],'lanes':{k:{'passed':v['passed'],'cases':v['cases']} for k,v in evidence['lanes'].items()},'neural_inference_verified':False}
   except Exception as e:result['campaign_baselines_error']=type(e).__name__
   result['chronos_tournament']={'status':'paused_synthetic_research'}
   try:result['discovered']=len(refresh_catalog(root)['models'])
   except Exception as e:result['discovery_error']=type(e).__name__
   result['infinity_synthetic_qualification']={'status':'paused_source_only'}
   try:result['intelligence_gap_audit']=run_gap_audit(root,'source_only')
   except Exception as e:result['gap_audit_error']=type(e).__name__
   try:result['training_bootstrap']=resume_bootstrap(root,training,ready)
   except Exception as e:result['training_bootstrap_error']=type(e).__name__
   try:
    result['intelligence_resources']=resume_resources(root,training,resource_queue_status(ready,result.get('training_bootstrap',{})))
    if result['intelligence_resources']['status'] in ('started','running'):
     ready='deferred_acquisition';result['status']=ready
   except Exception as e:result['intelligence_resources_error']=type(e).__name__
   result['learning_policy']=learning_policy()
   result['megaswarm']={'status':'paused_synthetic_curriculum'}
   result['market_academy']={'status':'paused_synthetic_curriculum'}
   result['omni_academy']={'status':'paused_synthetic_curriculum'}
   result['repository_fabric']={'status':'preserved_existing_registry'}
   result['learning_workspace']={'status':'preserved_legacy_archive'}
   result['native_training']={'status':'paused_pending_source_corpus'}
   result['campaign_weight_bank']={'status':'paused_owner_directive'}
   try:result['source_knowledge']=refresh_source_knowledge(root)
   except Exception as e:result['source_knowledge_error']=type(e).__name__
   try:result['icarus_knowledge']=refresh_icarus(root)
   except Exception as e:result['icarus_knowledge_error']=type(e).__name__
   try:
    code=root/'experience'/'source-knowledge'/'code-coverage.json'
    if not code.exists() or time.time()-code.stat().st_mtime>=86400:result['icarus_code_index']=refresh_code_index(root)
   except Exception as e:result['icarus_code_index_error']=type(e).__name__
   try:
    bootstrap_busy=(training/'bootstrap.lock').exists() or result.get('training_bootstrap',{}).get('status') in ('started','running')
    if result.get('source_knowledge',{}).get('status')=='ready':
     if bootstrap_busy:
      result['research_portfolio']=portfolio_cycle(root,training,evidence_only=True)
      result['source_assist']={'status':'evidence_only_during_bootstrap'}
     elif service_due(time.time()):
      result['research_portfolio']=portfolio_cycle(root,training)
      result['source_assist']={'status':'research_portfolio_cycle'}
     else:result['source_assist']=council_cycle(root,training)
    else:result['source_assist']={'status':'deferred_source_or_bootstrap'}
   except Exception as e:result['source_assist_error']=type(e).__name__
   try:result['human_corpus']=audit_human_corpus(root)
   except Exception as e:result['human_corpus_error']=type(e).__name__
   try:result['native_training']=source_training_cycle(root,training)
   except Exception as e:result['native_training_error']=type(e).__name__
   try:result['capability_frontier']=refresh_frontier(root)
   except Exception as e:result['capability_frontier_error']=type(e).__name__
   write_status(root,result)
   print(json.dumps(result),flush=True)
 except FileExistsError:print(json.dumps({'status':'service_busy'}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args()
 main(a.root)
