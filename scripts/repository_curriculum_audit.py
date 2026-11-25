"""Low-resource audit of the complete curriculum, under the service's existing lock."""
import json,subprocess,sys
from pathlib import Path
from hf_weight_cache import lock
from native_lora_train import validate_corpus
root=Path.home()/'projects'/'umbra-agentic-native-20261124'
scripts=Path(__file__).resolve().parent
with lock(root/'infinity'/'service.lock'):
 for name,mode in [('swarm_cycle','init'),('market_cycle','audit'),('omni_cycle','audit'),('repository_cycle','audit')]:
  r=subprocess.run(['node',str(scripts/(name+'.mjs')),str(root),mode],capture_output=True,text=True,timeout=120,check=True)
  v=json.loads(r.stdout.splitlines()[-1])
  if v.get('status') not in ('completed','indexed'):raise RuntimeError(name+' not completed')
  print(name,json.dumps(v.get('repository_learning') or v.get('corpora') or {k:v[k] for k in ('status','agents') if k in v}),flush=True)
 for f in (root/'megaswarm'/'corpora').glob('*.json'):
  v=json.loads(f.read_text(encoding='utf8'));validate_corpus(v,v['model'])
  assert v.get('repository_examples',0)>0 and v.get('market_examples',0)>0 and v.get('omni_added',0)>0
  print('VALIDATED',f.name,{k:len(v[k]) for k in ('training','retention','transfer')},flush=True)
