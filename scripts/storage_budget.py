"""Verified retirement activates bounded incremental allocation; no model mutation."""
from dataclasses import dataclass
import json,re
from pathlib import Path
from acquisition_receipt import TAG,DIGEST,completed_receipt

@dataclass(frozen=True)
class Budget:
 neural_cap:int
 resource_cap:int
 learning_reserve:int
 floor:int
 native_additional:int=0
 specialist_additional:int=0

LEGACY=Budget(42000000000,1500000000,3000000000,3000000000)
# Approximately the owner allocation, with the actual disk admission gate authoritative.
RETIRED=Budget(60000000000,5500000000,5000000000,7800000000,12000000000,6000000000)
NATIVE_DOMAINS=frozenset(('code_training','code_generation','mathematical_reasoning','instruction','edge_reasoning','reasoning','native_reasoning','native_coding'))
def budget(root):
 root=Path(root);p=root/'experience'/'large-model-retirement-20261126.json'
 if not p.exists():return LEGACY
 if p.is_symlink() or not p.is_file() or p.stat().st_size>8192:raise ValueError('retirement receipt path')
 r=json.loads(p.read_text(encoding='utf8'))
 if (r.get('removed')!=TAG or r.get('digest')!=DIGEST or
     any(type(r.get(k)) is not int for k in ('free_before','free_after','reclaimed')) or
     r['free_before']<0 or r['reclaimed']!=r['free_after']-r['free_before'] or
     not 29000000000<=r['reclaimed']<=31000000000 or
     r.get('queue_status')!='ready' or r.get('historical_receipt') is not True or
     r.get('task_trigger_preserved') is not True or
     not re.fullmatch('[a-f0-9]{40}',str(r.get('deployed_revision',''))) or not completed_receipt(root)):
  raise ValueError('unverified retirement receipt')
 return RETIRED
def source_training_storage_admitted(root,free):
 # Preserve the historical 6 GB guard and the verified retirement floor.
 # Reserve 20 MB for the bounded adapter and 5 MB for atomic receipt/state writes.
 if type(free) is not int or free<0:return False
 try:return free>=max(6000000000,budget(root).floor)+25000000
 except (OSError,ValueError,TypeError,KeyError):return False
def expansion_lane(domain):return 'native' if domain in NATIVE_DOMAINS else 'specialist'
def incremental_usage(baseline,current,lanes):
 for values in (baseline,current):
  if any(not isinstance(k,str) or not k or '/' in k or '\\' in k or k in ('.','..') or type(v) is not int or v<0 for k,v in values.items()):raise ValueError('invalid allocation inventory')
 out={'native':0,'specialist':0}
 for name,amount in baseline.items():
  if current.get(name,-1)<amount:raise ValueError('preallocation inventory shrank; reconcile baseline')
 for name,amount in current.items():
  growth=amount-baseline.get(name,0)
  if not growth:continue
  lane=lanes.get(name)
  if lane not in out:raise ValueError('unclassified incremental acquisition')
  out[lane]+=growth
 return out
