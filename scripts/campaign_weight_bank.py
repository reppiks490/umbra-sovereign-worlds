"""Bounded independent synthetic neural training inside the existing learning budget."""
import argparse,json,os,shutil,sys,time
from pathlib import Path
from urllib.request import urlopen
from native_lora_train import available_ram
from neural_priority import size
from hf_weight_cache import lock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'mcp'))
import myriad_agent_bank_v51 as bank
MAX_AGENTS=100
MAX_BATCH=4
STEPS=32
LEARNING_CAP=3000000000
RAM_MIN=3000000000
FREE_MIN=6000000000
PER_AGENT=bank.WIDTH+65536
def admission(count,workspace_bytes,free,ram,busy,bootstrap):
 if busy or bootstrap or ram<RAM_MIN or free<FREE_MIN or not 0<=count<=MAX_AGENTS or workspace_bytes<0:return 0
 return max(0,min(MAX_BATCH,MAX_AGENTS-count,(LEARNING_CAP-workspace_bytes)//PER_AGENT,(free-FREE_MIN)//PER_AGENT))
def ollama_busy():
 try:
  with urlopen('http://127.0.0.1:11434/api/ps',timeout=5) as r:return bool(json.load(r)['models'])
 except Exception:return True
def run(root,training):
 workspace=root/'experience';workspace.mkdir(exist_ok=True)
 target=workspace/'campaign-agent-bank';target.mkdir(exist_ok=True)
 if target.is_symlink() or workspace.is_symlink():raise ValueError('invalid training path')
 with lock(workspace/'campaign-agent-bank.lock'):
  before=bank.status(target);n=before['trained_agents']
  allowed=admission(n,size(workspace),shutil.disk_usage(workspace).free,available_ram(),ollama_busy(),(training/'bootstrap.lock').exists())
  if not allowed:return {'status':'deferred_admission',**before,'campaign_cap_agents':MAX_AGENTS}
  trained=[]
  for i in range(n+1,n+allowed+1):
   if not admission(i-1,size(workspace),shutil.disk_usage(workspace).free,available_ram(),ollama_busy(),(training/'bootstrap.lock').exists()):break
   q=bank.train(target,i,STEPS);bank.verify(target/f'{i:05d}',True)
   trained.append({'agent':i,'steps':q['steps'],'before':q['before'],'after':q['after'],'review_eligible_synthetic':q['review_eligible_synthetic']})
  result={'status':'completed' if trained else 'deferred_admission',**bank.status(target),'campaign_cap_agents':MAX_AGENTS,'trained_this_cycle':len(trained),'batch':trained,'scope':'independent synthetic regression networks; not LLM fine-tuning','production_authority':False}
  out=workspace/'campaign-agent-bank-status.json';tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(result,indent=2),encoding='utf8');os.replace(tmp,out);return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--training',required=True,type=Path);a=p.parse_args()
 try:print(json.dumps(run(a.root,a.training)))
 except FileExistsError:print(json.dumps({'status':'busy','production_authority':False}))
