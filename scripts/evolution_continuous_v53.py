"""Bounded serialized model, bank and teacher orchestration."""
import argparse,datetime,json,os,shutil,subprocess,time
from pathlib import Path
import evolution_supervisor_v50 as base
import evolution_fleet_scale_v36 as scale
import evolution_teacher_v40 as teacher
import evolution_model_evidence_v24 as ev
import evolution_research_orchestrator_v39 as orch
def phase(hour,minute):
    if minute//5==2:return 'ability_bank'
    if minute//5==8:return 'agent_bank'
    return base.phase(hour,minute)
def admit(free_mb,free_disk,busy):return free_mb>=3500 and free_disk>=6*1024**3 and not busy
def run(root,virtual,force=None):
    now=datetime.datetime.now(datetime.timezone.utc);mode=force or phase(now.hour,now.minute)
    if mode not in ('ability_bank','agent_bank'):return base.run(root,virtual,mode)
    key=ev.secret();report={'schema':'myriad.continuous_bank.v53','phase':mode,'epoch':int(time.time()),'production_authority':False,'errors':[]}
    busy=bool(teacher.request('/api/ps')[0].get('models'))
    if not admit(scale.free_mb(),shutil.disk_usage(root).free,busy):
        report['status']='deferred_resource_guard'
    else:
        script_root=Path(__file__).resolve().parent
        exe=script_root/'.training-venv'/'Scripts'/'python.exe'
        if not exe.is_file():raise ValueError('training runtime missing')
        if mode=='ability_bank':
            cmd=[str(exe),str(script_root/'evolution_bank_v47.py'),'--root',str(root/'ability-v47'),'--authorize','--shards','8','--steps','24','train']
        else:
            cmd=[str(exe),str(script_root/'evolution_agent_bank_v51.py'),'--root',str(root/'agent-v51'),'--authorize','--agents','16','--steps','32','train']
        try:
            p=subprocess.run(cmd,capture_output=True,text=True,timeout=195)
            if p.returncode!=0:raise RuntimeError('bounded training failed')
            report['training']=json.loads(p.stdout.strip().splitlines()[-1]);report['status']='completed'
        except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as e:
            report['status']='failed';report['errors'].append(type(e).__name__)
    report['hmac_sha256']=ev.sign(report,key);orch.atomic(root/f'aggregate-{mode}-v53.json',report);return report
def main():
    p=argparse.ArgumentParser();p.add_argument('--private',required=True);p.add_argument('--free-virtual-mib',type=int,required=True);p.add_argument('--authorize',action='store_true');p.add_argument('--phase',choices=['teacher','small_teacher','retrieval','worker','benchmark','fleet','ability_bank','agent_bank']);a=p.parse_args()
    root=Path(a.private)
    if not a.authorize or root.is_symlink() or not root.is_dir():raise PermissionError('explicit private research authorization required')
    r=run(root,a.free_virtual_mib,a.phase);print(json.dumps(r,sort_keys=True))
    u=r.get('underlying',r)
    if u.get('errors') or u.get('execution_issues') or any(x.get('errors') for x in u.get('batch',{}).values() if isinstance(x,dict)):raise SystemExit(2)
if __name__=='__main__':main()
