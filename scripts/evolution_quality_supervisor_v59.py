"""Resource-bounded training quality windows, keeping all existing core workloads."""
import argparse,datetime,json,shutil,subprocess,time
from pathlib import Path
import evolution_continuous_v53 as base
import evolution_fleet_scale_v36 as scale
import evolution_teacher_v40 as teacher
import evolution_model_evidence_v24 as ev
import evolution_research_orchestrator_v39 as orch
def phase(hour,minute):
    mode=base.phase(hour,minute)
    if mode=='worker' and hour%4==0 and minute//5==1:return 'tool_research'
    if mode=='worker' and hour%4==2 and minute//5==1:return 'protocol_research'
    if mode=='ability_bank' and hour%4==0:return 'distill'
    if mode=='agent_bank' and hour%2==1:return 'evolve_agents'
    return mode
def admit(free_mb,free_disk,busy):return free_mb>=3500 and free_disk>=6*1024**3 and not busy
def admit_window(mode,free_mb,virtual,free_disk,busy):
    if mode not in ('distill','evolve_agents'):raise ValueError('unknown training window')
    threshold=2400 if mode=='distill' else 3500
    return free_mb>=threshold and virtual>=6000 and free_disk>=6*1024**3 and not busy
def run(root,virtual,force=None):
    now=datetime.datetime.now(datetime.timezone.utc);mode=force or phase(now.hour,now.minute)
    if mode=='proof_feedback':
        import evolution_proof_runtime_v97 as proof_runtime
        return proof_runtime.run(root,virtual)
    if mode=='receipt_audit':
        import evolution_receipt_audit_v91 as receipt_audit
        return receipt_audit.run(root)
    if mode=='novel_reasoning':
        import evolution_reasoning_runtime_v82 as reasoning
        return reasoning.run(root,virtual)
    if mode=='protocol_research':
        import evolution_research_protocol_v67 as protocol
        return protocol.run(root,virtual)
    if mode=='tool_research':
        import evolution_tool_research_v64 as tool_research
        return tool_research.run(root,virtual)
    if mode=='benchmark':
        import evolution_model_tournament_v62 as tournament
        return tournament.run(root,virtual)
    if mode not in ('distill','evolve_agents'):return base.run(root,virtual,mode)
    key=ev.secret();report={'schema':'myriad.quality_window.v59','phase':mode,'epoch':int(time.time()),'production_authority':False,'errors':[]}
    busy=bool(teacher.request('/api/ps')[0].get('models'))
    if not admit_window(mode,scale.free_mb(),virtual,shutil.disk_usage(root).free,busy):
        report['status']='deferred_resource_guard'
    else:
        here=Path(__file__).resolve().parent;exe=here/'.training-venv'/'Scripts'/'python.exe'
        if not exe.is_file():raise ValueError('training runtime missing')
        if mode=='distill':
            cmd=[str(exe),str(here/'evolution_distill_v63.py'),'--root',str(root/'distill-v63'),'--authorize','--rows','32','--samples','1024']
        else:
            cmd=[str(exe),str(here/'evolution_task_adapter_v61.py'),'--source',str(root/'agent-v51'),'--root',str(root/'task-adapters-v61'),'--authorize','--agents','16','--steps','256']
        try:
            p=subprocess.run(cmd,capture_output=True,text=True,timeout=195)
            if p.returncode:raise RuntimeError('bounded training failed')
            report['training']=json.loads(p.stdout.strip().splitlines()[-1]);report['status']='completed'
        except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as e:
            report['status']='failed';report['errors'].append(type(e).__name__)
    report['hmac_sha256']=ev.sign(report,key);orch.atomic(root/f'aggregate-{mode}-v59.json',report);return report
def main():
    p=argparse.ArgumentParser();p.add_argument('--private',required=True);p.add_argument('--free-virtual-mib',type=int,required=True);p.add_argument('--authorize',action='store_true');p.add_argument('--phase',choices=['teacher','small_teacher','retrieval','worker','benchmark','fleet','ability_bank','agent_bank','distill','evolve_agents','tool_research','protocol_research','novel_reasoning','receipt_audit','proof_feedback']);a=p.parse_args()
    root=Path(a.private)
    if not a.authorize or root.is_symlink() or not root.is_dir():raise PermissionError('explicit private research authorization required')
    r=run(root,a.free_virtual_mib,a.phase);print(json.dumps(r,sort_keys=True));u=r.get('underlying',r)
    if u.get('errors') or u.get('execution_issues') or any(x.get('errors') for x in u.get('batch',{}).values() if isinstance(x,dict)):raise SystemExit(2)
if __name__=='__main__':main()
