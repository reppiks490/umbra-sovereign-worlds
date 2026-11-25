"""Select only source-grounded native training candidates within physical budgets."""
import hashlib,json,shutil,subprocess,time
from pathlib import Path
from native_lora_train import available_ram,MODELS,required_memory
from student_council import roster,load_json
from source_assist import local_api
def select_candidate(rows,ram,now):
 eligible=[r for r in rows if r['present'] and r['required_ram']<=ram and r['state'].get('attempts',0)<20 and now-r['state'].get('timestamp',0)>=3600]
 return min(eligible,key=lambda r:(r['state'].get('timestamp',0),r['required_ram'],r['name'])) if eligible else None
def run(root,training):
 if (training/'bootstrap.lock').exists() or (root/'experience'/'model-compute.lock').exists() or (root/'experience'/'student-council'/'council.lock').exists() or local_api('ps').get('models'):return {'status':'deferred_busy','source_only':True}
 if shutil.disk_usage(root).free<6000000000:return {'status':'deferred_storage','source_only':True}
 py=training/'venv'/'Scripts'/'python.exe'
 if not py.is_file():return {'status':'deferred_runtime','source_only':True}
 if not (root/'experience'/'source-knowledge'/'human-corpus'/'audit.json').is_file():return {'status':'deferred_corpus','source_only':True}
 rows=[{**r,'required_ram':max(4500000000,r['required_ram'])} for r in roster(root) if r['backend']=='native']
 for name,(repo,rev,sha,n) in MODELS.items():
  p=training/'sources'/(repo.replace('/','--')+'--'+rev[:12])/'receipt.json'
  rows.append({'name':name,'digest':sha,'present':p.is_file(),'required_ram':max(required_memory(name),2*n+3000000000)})
 for r in rows:
  key=hashlib.sha256(r['name'].encode()).hexdigest()[:20]
  s=load_json(root/'experience'/'source-lora'/key/'state.json')
  r['state']=s if s.get('base_sha256')==r['digest'] else {}
 ram=available_ram();pick=select_candidate(rows,ram,int(time.time()))
 if not pick:return {'status':'deferred_memory_or_checkpoint_or_cooldown','free_ram':ram,'candidates':rows,'source_only':True}
 p=subprocess.run([str(py),'-u',str(Path(__file__).with_name('native_student.py')),'--root',str(root),'--training',str(training),'--model',pick['name'],'--train'],capture_output=True,text=True,timeout=900)
 if p.returncode:return {'status':'training_failed','model':pick['name'],'reason':p.stderr[-1500:],'source_only':True}
 return json.loads(p.stdout.splitlines()[-1])
