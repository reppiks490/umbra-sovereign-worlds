"""Unified bounded multi-model local research scheduler; raw outputs remain private."""
from __future__ import annotations
import argparse,json,os,re,shutil,time,uuid
from pathlib import Path
import evolution_fleet_scale_v36 as scale
import evolution_model_queue_v26 as queue
import evolution_model_evidence_v24 as evidence
import evolution_native_ollama_v33 as native
import evolution_research_v37 as specialist
import evolution_live_research_v38 as source
QWEN='8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7'
GEMMA='97558784bdc9175075a72655bf360b15da17df6b3b9e5182af9f8c0c8e58ba7c'
APPROVED=('qwen3:1.7b','gemma3:1b','qwen2.5-coder:1.5b')
SCHEMA='myriad.local_research_orchestrator.v39'
def admit(tags,previous):
    if not isinstance(previous,dict) or any(k not in APPROVED or not isinstance(v,str) or not re.fullmatch('[a-f0-9]{64}',v) for k,v in previous.items()):raise ValueError('invalid persisted model pins')
    if previous.get('qwen3:1.7b',QWEN)!=QWEN:raise ValueError('primary pin changed')
    pins=dict(previous);available={};issues={}
    if not isinstance(tags,list):raise ValueError('invalid local tag registry')
    for name in APPROVED:
        matches=[x for x in tags if isinstance(x,dict) and x.get('name')==name]
        if not matches:
            if name in pins:issues[name]='not_installed'
            continue
        if len(matches)!=1:issues[name]='ambiguous_tag';continue
        x=matches[0];digest=x.get('digest');size=x.get('size')
        if not isinstance(digest,str) or not re.fullmatch('[a-f0-9]{64}',digest) or type(size) is not int or not 0<size<=2*1024**3:issues[name]='invalid_digest_or_size';continue
        if name=='qwen3:1.7b' and digest!=QWEN:issues[name]='primary_pin_mismatch';continue
        if name in pins and pins[name]!=digest:issues[name]='changed_digest';continue
        pins[name]=digest;available[name]=digest
    return pins,available,issues
def choose(available,used,slot):
    ordered=[n for n in APPROVED if n in available]
    if not ordered:return None
    return next((n for n in ordered if n not in used),ordered[slot%len(ordered)])
def atomic(path,value):
    p=Path(path);tmp=p.with_name(p.name+'.'+uuid.uuid4().hex+'.tmp')
    with tmp.open('xb') as f:f.write(evidence.canonical(value)+b'\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,p)
def read_pins(path):
    if not path.exists():return {'qwen3:1.7b':QWEN,'gemma3:1b':GEMMA}
    if path.is_symlink() or path.stat().st_size>4096:raise ValueError('invalid registry file')
    return json.loads(path.read_text())
def run(private,authorize=False):
    if authorize is not True:raise PermissionError('explicit research authorization required')
    private=Path(private)
    if private.is_symlink() or not private.is_dir() or shutil.disk_usage(private).free<5*1024**3:raise ValueError('private storage guard')
    key=evidence.secret();start=time.monotonic();issues={};outputs={}
    pin_path=private/'research-model-pins-v39.json'
    tags,_=native._json_request(11434,'GET','/api/tags',None,10)
    pins,available,model_issues=admit(tags.get('models'),read_pins(pin_path));atomic(pin_path,pins)
    paths={'arithmetic':private/'local-pilot.sqlite3','specialist':private/'research-v37.sqlite3','source':private/'source-research-v38.sqlite3'}
    for p in paths.values():
        if p.is_symlink() or not p.is_file() or p.stat().st_size>512*1024**2:raise ValueError('private ledger guard')
    sp=specialist.connect(paths['specialist']);so=specialist.connect(paths['source'])
    try:
        used={r[0] for r in sp.execute('SELECT DISTINCT model FROM receipts WHERE error IS NULL')}|{r[0] for r in so.execute('SELECT DISTINCT model FROM receipts WHERE error IS NULL')}
        model=choose(available,used,int(time.time())//300)
        def elapsed():return time.monotonic()-start
        if 'qwen3:1.7b' in available and queue.status(paths['arithmetic'])['overdue_ready'] and scale.free_mb()>=1536:
            try:
                r=scale.run(paths['arithmetic'],private/'receipts','qwen3:1.7b',QWEN,cap=24,seconds=70,authorize=True)
                outputs['arithmetic']={k:r[k] for k in ('attempted','completed','correct','elapsed_seconds','errors')}
            except Exception as exc:issues['arithmetic']=type(exc).__name__
        if model and elapsed()<105 and specialist.status(sp)['due'] and scale.free_mb()>=1536:
            try:
                r=specialist.run(sp,model,available[model],6,100,key)
                outputs['specialist']={k:r[k] for k in ('model','attempted','completed','passed','valid_structured','errors','elapsed_seconds')}
            except Exception as exc:issues['specialist']=type(exc).__name__
        remaining=int(245-elapsed())
        if model and remaining>=80 and source.status(so)['due'] and scale.free_mb()>=1536:
            try:
                r=source.run(so,Path(__file__).resolve().parent,paths['arithmetic'],model,available[model],2,min(115,remaining-5),key)
                outputs['source']={k:r[k] for k in ('model','completed','valid_citations','errors','elapsed_seconds')}
            except Exception as exc:issues['source']=type(exc).__name__
        report={'schema':SCHEMA,'utc_epoch':int(time.time()),'elapsed_seconds':round(elapsed(),3),'selected_research_model':model,'available_models':sorted(available),'model_issues':model_issues,'execution_issues':issues,'batch':outputs,'arithmetic':queue.status(paths['arithmetic']),'specialist':specialist.status(sp),'source':source.status(so),'production_authority':False,'independent_model_weights_per_worker':False,'proposals_executed':0,'external_telemetry_published':False}
        report['hmac_sha256']=evidence.sign(report,key)
        atomic(private/'aggregate-research-v39.json',report)
        return report
    finally:sp.close();so.close()
def main():
    p=argparse.ArgumentParser();p.add_argument('--private',required=True);p.add_argument('--authorize',action='store_true');a=p.parse_args()
    r=run(a.private,a.authorize);print(json.dumps(r,sort_keys=True))
    if r['execution_issues'] or any(v.get('errors') for v in r['batch'].values()):raise SystemExit(2)
if __name__=='__main__':main()
