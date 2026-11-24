"""Bounded multi-identity local inference scheduler, preserving v26 evidence.
One shared model, sequential requests, resource-aware admission. No trading.
"""
import argparse,ctypes,functools,json,math,os,re,shutil,time
from pathlib import Path
import evolution_model_queue_v26 as q
import evolution_local_model_v22 as base
import evolution_native_ollama_v33 as native
import evolution_model_evidence_v24 as evidence

def expand(db_path,target,due):
    if type(target) is not int or not 1<=target<=4096 or type(due) is not int or due<0 or due%3600:raise ValueError('Invalid enrollment bounds')
    db=q.open_db(db_path)
    try:
        db.execute('BEGIN IMMEDIATE')
        try:
            before=db.total_changes
            db.executemany("INSERT OR IGNORE INTO model_jobs(worker_id,next_due,repeating,state) VALUES(?,?,1,'ready')",((i,due) for i in range(1,target+1)))
            added=db.total_changes-before
            db.execute('COMMIT')
            return added
        except BaseException:db.execute('ROLLBACK');raise
    finally:db.close()

def batch_limit(cap,latency,seconds,free_mb):
    if free_mb<1536 or seconds<=0 or not math.isfinite(latency) or latency<=0:return 0
    return max(0,min(cap,int(seconds/latency)))

def free_mb():
    if os.name=='nt':
        class Memory(ctypes.Structure):
            _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(k,ctypes.c_ulonglong) for k in ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]
        m=Memory();m.length=ctypes.sizeof(m)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):raise OSError('Memory query failed')
        return m.available//1048576
    with open('/proc/meminfo') as f:
        return int(next(x for x in f if x.startswith('MemAvailable:')).split()[1])//1024

def run(db_path,out,model,digest,port=11434,cap=32,seconds=180,authorize=False):
    if authorize is not True:raise PermissionError('Explicit local research authorization required')
    if type(cap) is not int or not 1<=cap<=128 or type(seconds) is not int or not 20<=seconds<=240:raise ValueError('Invalid execution budget')
    if not re.fullmatch('[a-f0-9]{64}',digest):raise ValueError('Invalid model digest')
    out=Path(out)
    if out.is_symlink() or not out.is_dir():raise ValueError('Existing private receipt directory required')
    if shutil.disk_usage(out).free<5*1024**3:raise RuntimeError('Storage guard')
    if sum(p.stat().st_size for p in out.iterdir() if p.is_file())>1024**3:raise RuntimeError('Evidence quota guard')
    key=evidence.secret();start=time.monotonic();count=0;good=0;errors=[];latency=4.0
    completed=[];original=base.request;original_json=native._json_request
    # Reuse one resident model briefly between calls, never spawn a model per ID.
    def warm_request(port,method,route,body,timeout):
        if method=='POST' and route=='/api/chat':
            body=dict(body);body['keep_alive']='45s'
        return original_json(port,method,route,body,timeout)
    try:
        native._json_request=warm_request
        base.request=functools.partial(native.native_request,digest=digest)
        while count<cap:
            remaining=seconds-(time.monotonic()-start)
            # Existing queue has a 4-job hard cap. Use at most one request if time is short.
            n=batch_limit(min(4,cap-count),max(latency*1.5,1),remaining-30,free_mb())
            if n==0:break
            t=time.monotonic()
            r=q.process(db_path,out,model=model,port=port,max_jobs=n,count=1,max_tokens=32,budget=32,timeout=15,deadline_seconds=30,authorize=True)
            rows=r['completed'];bad=r['quarantined_or_failed'];elapsed=time.monotonic()-t
            if not rows and not bad:break
            count+=len(rows)+len(bad);good+=sum(x['score'] for x in rows);completed.extend(rows);errors.extend(bad)
            latency=max(.25,elapsed/max(1,len(rows)+len(bad)))
            if bad:break
    finally:base.request=original;native._json_request=original_json
    report={'schema':'myriad.local_fleet_scale.v36','completed':len(completed),'correct':good,'attempted':count,'errors':errors,'elapsed_seconds':round(time.monotonic()-start,3),'model':model,'observed_tag_digest':digest,'receipts':[r['receipt_hmac'] for r in completed],'shared_model_runtime':True,'independent_model_weights':False,'production_authority':False,'training_steps':0,'queue':q.status(db_path)}
    report['hmac_sha256']=evidence.sign(report,key)
    name=out/('fleet-v36-'+str(time.time_ns())+'.json')
    with name.open('xb') as f:f.write(evidence.canonical(report)+b'\n');f.flush();os.fsync(f.fileno())
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--db',required=True);sub=p.add_subparsers(dest='cmd',required=True)
    e=sub.add_parser('expand');e.add_argument('--target',type=int,required=True);e.add_argument('--authorize',action='store_true')
    r=sub.add_parser('run');r.add_argument('--private-out',required=True);r.add_argument('--model',required=True);r.add_argument('--digest',required=True);r.add_argument('--cap',type=int,default=32);r.add_argument('--seconds',type=int,default=180);r.add_argument('--authorize',action='store_true')
    a=p.parse_args()
    if not a.authorize:raise PermissionError('Explicit authorization required')
    if a.cmd=='expand':result={'added':expand(a.db,a.target,int(time.time())//3600*3600),'queue':q.status(a.db)}
    else:result=run(a.db,a.private_out,a.model,a.digest,cap=a.cap,seconds=a.seconds,authorize=True)
    print(json.dumps(result,sort_keys=True))
    if result.get('errors'):raise SystemExit(2)
if __name__=='__main__':main()
