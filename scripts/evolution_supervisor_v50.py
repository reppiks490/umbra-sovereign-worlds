"""Bounded unified research runtime; two hourly windows for the full fleet."""
import argparse,datetime,json,time
from pathlib import Path
import evolution_qualification_v44 as previous
import evolution_fleet_v46 as fleet
import evolution_model_evidence_v24 as evidence
import evolution_research_orchestrator_v39 as orch
def phase(hour,minute):
    if minute//5 in (4,10):return 'fleet'
    return previous.phase(hour,minute)
def run(root,virtual,force=None):
    now=datetime.datetime.now(datetime.timezone.utc);mode=force or phase(now.hour,now.minute)
    if mode!='fleet':return previous.run(root,virtual,mode)
    db=fleet.connect(root/'fleet-v46.sqlite3');key=evidence.secret();start=time.monotonic();reports=[]
    try:
        # First coverage before repeated identities. At most two serial requests per window.
        for _ in range(2):
            if time.monotonic()-start>65:break
            r=fleet.run(db,key,4);reports.append(r)
            if r.get('status')!='completed':break
        report={'schema':'myriad.full_fleet_window.v50','epoch':int(time.time()),'phase':mode,'batches':reports,'fleet':fleet.status(db),'elapsed_seconds':round(time.monotonic()-start,3),'production_authority':False,'errors':[r['error_class'] for r in reports if r.get('status')=='failed']}
        report['hmac_sha256']=evidence.sign(report,key);orch.atomic(root/'aggregate-fleet-v50.json',report);return report
    finally:db.close()
def main():
    p=argparse.ArgumentParser();p.add_argument('--private',required=True);p.add_argument('--free-virtual-mib',type=int,required=True);p.add_argument('--authorize',action='store_true');p.add_argument('--phase',choices=['teacher','small_teacher','retrieval','worker','benchmark','fleet']);a=p.parse_args()
    root=Path(a.private)
    if not a.authorize or root.is_symlink() or not root.is_dir():raise PermissionError('explicit private research authorization required')
    r=run(root,a.free_virtual_mib,a.phase);print(json.dumps(r,sort_keys=True))
    u=r.get('underlying',r)
    if u.get('errors') or u.get('execution_issues') or any(x.get('errors') for x in u.get('batch',{}).values() if isinstance(x,dict)):raise SystemExit(2)
if __name__=='__main__':main()
