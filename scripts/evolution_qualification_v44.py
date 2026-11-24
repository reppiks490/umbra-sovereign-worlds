"""Scheduled, paired model evaluation and evidence-gated transient recovery."""
from __future__ import annotations
import argparse,datetime,hmac,json,time
from pathlib import Path
import evolution_teacher_supervisor_v41 as base
import evolution_teacher_v40 as teacher
import evolution_model_evidence_v24 as ev
import evolution_reliability_v43 as reliability
import evolution_research_orchestrator_v39 as orch
ORDER=('qwen3:1.7b','gemma3:1b','qwen2.5-coder:1.5b','granite4:350m','deepseek-r1:1.5b')
def phase(hour,minute):
    if hour%6==0 and minute//5==11:return 'benchmark'
    return base.phase(hour,minute)
def seed_for(epoch):return 440000+int(epoch)//604800
def select(available,used):return next((x for x in ORDER if x in available and x not in used),None)
def prior(private,key,seed):
    results=[]
    for p in sorted((private/'teacher-v40').glob('paired-*.json'))[-256:]:
        if p.is_symlink() or p.stat().st_size>131072:raise ValueError('invalid paired receipt')
        r=json.loads(p.read_text());sig=r.pop('hmac_sha256',None)
        if not isinstance(sig,str) or not hmac.compare_digest(ev.sign(r,key),sig):raise ValueError('paired receipt signature')
        if r.get('schema')!='myriad.paired_benchmark.v43' or r.get('production_authority') is not False:raise ValueError('paired receipt scope')
        if r['seed']!=seed:continue
        cases=reliability.benchmark_cases(seed)
        expected=reliability.grade(cases,r['raw'])
        if any(r[k]!=v for k,v in expected.items()):raise ValueError('paired score mismatch')
        import hashlib
        if r['case_hash']!=hashlib.sha256(ev.canonical(cases)).hexdigest():raise ValueError('paired task hash')
        if any(v['model']==r['model'] for v in results):raise ValueError('duplicate model in cohort')
        results.append({k:r[k] for k in ('model','case_hash','correct','total','decision_correct','evidence_correct')})
    return results
def run(private,virtual,force=None):
    private=Path(private);key=ev.secret()
    now=datetime.datetime.now(datetime.timezone.utc);epoch=int(now.timestamp());mode=force or phase(now.hour,now.minute)
    recovered=reliability.recover(private/'local-pilot.sqlite3',epoch,lambda i,d:reliability.verify_failure(private/'receipts',i,d),key)
    if mode!='benchmark':
        report=base.run(private,virtual,mode)
        if recovered:report={'schema':'myriad.qualified_run.v44','phase':mode,'recovered':[r['worker'] for r in recovered],'underlying':report,'production_authority':False}
        return report
    seed=seed_for(epoch);rows=prior(private,key,seed)
    tags,_=teacher.request('/api/tags');available={r.get('name') for r in tags['models']}
    model=select(available,{r['model'] for r in rows})
    report={'schema':'myriad.qualification.v44','phase':mode,'seed':seed,'recovered':[r['worker'] for r in recovered],'model':model,'production_authority':False,'errors':[]}
    if model:
        try:report['batch']=reliability.benchmark(private,model,seed,key)
        except Exception as e:report['errors'].append(type(e).__name__)
    rows=prior(private,key,seed)
    report['paired_comparison']=reliability.compare(rows) if rows else None
    report['complete_cohort']=set(ORDER).issubset({r['model'] for r in rows})
    teacher.save(private,'qualification',report,key)
    orch.atomic(private/'aggregate-qualification-v44.json',report)
    return report
def main():
    p=argparse.ArgumentParser();p.add_argument('--private',required=True);p.add_argument('--free-virtual-mib',type=int,required=True);p.add_argument('--authorize',action='store_true');p.add_argument('--phase',choices=['teacher','small_teacher','retrieval','worker','benchmark']);a=p.parse_args()
    root=Path(a.private)
    if not a.authorize or root.is_symlink() or not root.is_dir():raise PermissionError('explicit private research authorization required')
    r=run(root,a.free_virtual_mib,a.phase);print(json.dumps(r,sort_keys=True))
    u=r.get('underlying',r)
    if u.get('errors') or u.get('execution_issues') or any(x.get('errors') for x in u.get('batch',{}).values() if isinstance(x,dict)):raise SystemExit(2)
if __name__=='__main__':main()
