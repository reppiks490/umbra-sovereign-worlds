"""Read-only, aggregate-only audit of locally authenticated research receipts."""
import json,stat,time
from pathlib import Path
import evolution_tool_research_v64 as tool
import evolution_reasoning_runtime_v82 as reasoning
import evolution_research_v37 as research
import evolution_model_evidence_v24 as ev
import evolution_research_orchestrator_v39 as orch

LIMIT=4096
MAX_BYTES=65536
FAMILIES={'tool':('tool-research-v64-',tool.verify),'reasoning':('reasoning-v82-',reasoning.verify)}
def safe(p):
    s=p.lstat()
    return not p.is_symlink() and not bool(getattr(s,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',1024))

def audit(root,key):
    root=Path(root)
    if not root.is_dir() or not safe(root):raise ValueError('unsafe root')
    h=root/'teacher-v40'
    if h.exists() or h.is_symlink():
        if not h.is_dir() or not safe(h):raise ValueError('unsafe evidence directory')
    out={}
    for family,(prefix,verify) in FAMILIES.items():
        row={k:0 for k in ('observed','verified','rejected','completed_outcome','failed_outcome','duplicate_seed_records','qualified_tasks')}
        seen={}
        for p in h.glob(prefix+'*.json'):
            row['observed']+=1
            if row['observed']>LIMIT:raise ValueError('receipt budget exceeded')
            try:
                if not p.is_file() or not safe(p):raise ValueError('unsafe receipt')
                with p.open('rb') as f:raw=f.read(MAX_BYTES+1)
                if not 1<=len(raw)<=MAX_BYTES:raise ValueError('receipt size')
                r=json.loads(raw,object_pairs_hook=research.unique_pairs)
                if verify(r,key) is not True:raise ValueError('receipt verification')
                seed=r['seed']
                if seed in seen:
                    row['duplicate_seed_records']+=1
                    seen[seed]=None
                else:
                    seen[seed]=(sum(x['qualified'] for x in r['results']) if family=='tool' else r['scores']['joint_correct']) if r['status']=='completed' else 0
                row['verified']+=1
                row['completed_outcome' if r['status']=='completed' else 'failed_outcome']+=1
            except (ValueError,TypeError,KeyError,OSError,OverflowError,RecursionError):
                row['rejected']+=1
        row['qualified_tasks']=sum(v for v in seen.values() if v is not None)
        row['distinct_verified_seeds']=len(seen);out[family]=row
    status='issues_detected' if any(x['rejected'] or x['duplicate_seed_records'] for x in out.values()) else 'qualified' if any(x['observed'] for x in out.values()) else 'no_evidence'
    return {'schema':'myriad.receipt_audit.v91','status':status,'families':out,'actual_model_calls':0,'production_authority':False,'semantic_mastery_certified':False}

def run(root):
    report=audit(root,ev.secret());report['observed_epoch']=int(time.time())
    orch.atomic(root/'aggregate-receipt-audit-v91.json',report)
    return report
