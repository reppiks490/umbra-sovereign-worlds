"""One serialized local scheduler: worker batches, teacher windows and retrieval.
Large-model admission is fail-closed; no application shutdown, paging overrides, or promotion.
"""
import argparse,datetime,json,os,re,time
from pathlib import Path
import evolution_teacher_v40 as teacher
import evolution_research_orchestrator_v39 as orch
import evolution_model_evidence_v24 as ev
SMALL=('granite4:350m','deepseek-r1:1.5b','qwen3:1.7b')
def phase(hour,minute):
    bucket=minute//5
    if bucket==0:return 'teacher'
    if bucket==6:return 'retrieval' if hour%2==0 else 'small_teacher'
    return 'worker'
def compressed_admit(ram,virtual,busy):return not busy and ram>=4700 and virtual>=7500
def select_small(available,used,slot):
    ordered=[n for n in SMALL if n in available]
    return next((n for n in ordered if n not in used),ordered[slot%len(ordered)] if ordered else None)
def run(private,virtual,force=None):
    private=Path(private);key=ev.secret()
    now=datetime.datetime.now(datetime.timezone.utc);slot=int(now.timestamp())//300
    mode=force or phase(now.hour,now.minute)
    report={'schema':'myriad.teacher_supervisor.v41','epoch':int(now.timestamp()),'phase':mode,'production_authority':False,'errors':[]}
    tags,_=teacher.request('/api/tags');available={v.get('name') for v in tags['models']}
    if mode=='worker':return orch.run(private,authorize=True)
    if mode=='retrieval':
        try:
            import evolution_retrieval_review_v42 as rag
            report['retrieval']=rag.run(private,key,slot//24) if 'all-minilm:22m' in available else {'status':'not_installed'}
        except Exception as e:report['errors'].append(type(e).__name__)
    else:
        if mode=='teacher':
            for model in (teacher.TEACHER,teacher.COMPRESSED):
                if model not in available:continue
                try:
                    r=teacher.teacher(private,model,slot,key,virtual)
                    report['large_teacher']={k:v for k,v in r.items() if k not in ('raw','accepted_rows')}
                    if r.get('schema')=='myriad.teacher.v40':break
                    # A deferred full model may admit the separately qualified compressed variant.
                except Exception as e:report['errors'].append(type(e).__name__);break
        # A large-model request, successful or failed, must not lead to an unbounded second inference.
        large=report.get('large_teacher',{})
        if mode=='small_teacher' or (not report['errors'] and large.get('status','').startswith('deferred')):
            # One teacher batch, chosen by missing receipt coverage. No model chosen as a winner without paired evidence.
            used=set()
            folder=private/'teacher-v40'
            for f in sorted(folder.glob('teacher-*.json'))[-256:] if folder.exists() else []:
                v=json.loads(f.read_text())
                if v.get('accepted',0)>0:used.add(v.get('model'))
            model=select_small(available,used,slot)
            if model:
                try:
                    r=teacher.teacher(private,model,slot,key,virtual)
                    report['small_teacher']={k:v for k,v in r.items() if k not in ('raw','accepted_rows')}
                except Exception as e:report['errors'].append(type(e).__name__)
        try:report['student']={k:v for k,v in teacher.train(private,key).items() if k!='weights'}
        except Exception as e:report['errors'].append(type(e).__name__)
    teacher.save(private,'supervisor',report,key)
    orch.atomic(private/'aggregate-teacher-v41.json',report)
    return report
def main():
    p=argparse.ArgumentParser();p.add_argument('--private',required=True);p.add_argument('--free-virtual-mib',type=int,required=True);p.add_argument('--authorize',action='store_true');p.add_argument('--phase',choices=['teacher','small_teacher','retrieval','worker']);a=p.parse_args()
    if not a.authorize:raise PermissionError('explicit research authorization required')
    root=Path(a.private)
    if root.is_symlink() or not root.is_dir():raise ValueError('invalid private directory')
    r=run(root,a.free_virtual_mib,a.phase);print(json.dumps(r,sort_keys=True))
    if r.get('errors') or r.get('execution_issues'):raise SystemExit(2)
if __name__=='__main__':main()
