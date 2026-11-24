"""Collect an allowlisted, non-sensitive snapshot and publish to a dedicated branch."""
import argparse,base64,json,os,sqlite3,subprocess,time
from pathlib import Path
from contextlib import closing
import evolution_telemetry_v48 as contract
import evolution_bank_v47 as bank
import evolution_fresh_training_v35 as neural
import evolution_teacher_v40 as teacher
import evolution_model_evidence_v24 as ev
import hmac
import evolution_algorithms_v49 as methods
import evolution_agent_bank_v51 as agents
REPO='reppiks490/umbra-sovereign-worlds';BRANCH='telemetry/myriad-live';DEST='telemetry/live.json'
def query(path,sql):
    with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=10)) as c:return c.execute(sql).fetchone()
def collect(root,key):
    legacy=root/'local-pilot.sqlite3';fleet=root/'fleet-v46.sqlite3'
    n=query(legacy,'SELECT count(*) FROM model_jobs')[0];runs=query(legacy,'SELECT count(*) FROM model_runs')[0]
    en=query(fleet,'SELECT count(*) FROM workers')[0];items,dist,peer=query(fleet,'SELECT count(*),count(distinct worker),count(peer_worker) FROM receipts')
    calls=query(fleet,'SELECT count(*) FROM batches')[0]
    ab=bank.status(root/'ability-v47')
    labels={};updates=0
    for p in (root/'teacher-v40').glob('teacher-*.json'):
        v=json.loads(p.read_text());sig=v.pop('hmac_sha256')
        if not hmac.compare_digest(ev.sign(v,key),sig):raise ValueError('teacher receipt HMAC')
        for r in teacher.accept(teacher.cases(v['seed'],0),v['raw']):labels[r['id']]=r
    for p in (root/'teacher-v40').glob('student-*.json'):
        v=json.loads(p.read_text());sig=v.pop('hmac_sha256')
        if not hmac.compare_digest(ev.sign(v,key),sig):raise ValueError('student receipt HMAC')
        updates=max(updates,v['gradient_updates'])
    checkpoints=0
    for p in (root/'fresh-v34').glob('NEW-*'):
        v=neural.latest(root/'fresh-v34',int(p.name[4:]))
        if v:checkpoints+=v['generation']
    new_agents=agents.status(root/'agent-v51')
    counts={'legacy_enrolled':n,'legacy_completed':runs,'fleet_enrolled':en,'fleet_distinct_completed':dist,'fleet_completed_items':items,'fleet_model_calls':calls,'fleet_peer_linked':peer,'specialist_completed':query(root/'research-v37.sqlite3','SELECT count(*) FROM receipts WHERE error IS NULL')[0],'source_completed':query(root/'source-research-v38.sqlite3','SELECT count(*) FROM receipts WHERE error IS NULL')[0],'ability_rows':ab['trained_rows'],'ability_bytes':ab['trained_bytes'],'ability_updates':ab['row_updates'],'agent_checkpoints':checkpoints+new_agents['trained_agents'],'agent_bytes':checkpoints*neural.WIDTH+new_agents['trained_bytes'],'teacher_labels':len(labels),'student_updates':updates,'algorithm_implementations_added':len(methods.REGISTRY)}
    return contract.snapshot(int(time.time()),counts)
def gh(*args,input=None):
    p=subprocess.run(['gh','api',*args],input=input,text=True,capture_output=True,timeout=35)
    if p.returncode!=0:raise RuntimeError('GitHub aggregate publication failed')
    return json.loads(p.stdout)
def publish(v):
    # Branch is already created by repository owner. Only this one fixed path is writable.
    endpoint=f'repos/{REPO}/contents/{DEST}'
    current=gh(endpoint+'?ref='+BRANCH)
    payload={'message':'Refresh aggregate MYRIAD research telemetry','branch':BRANCH,'sha':current['sha'],'content':base64.b64encode(contract.canonical(v)+b'\n').decode()}
    return gh('--method','PUT',endpoint,'--input','-',input=json.dumps(payload))['commit']['sha']
def main():
    p=argparse.ArgumentParser();p.add_argument('--private',required=True);p.add_argument('--authorize-public-aggregate',action='store_true');p.add_argument('--publish',action='store_true');a=p.parse_args()
    root=Path(a.private)
    if not a.authorize_public_aggregate or root.is_symlink() or not root.is_dir():raise PermissionError('explicit aggregate publication required')
    v=collect(root,ev.secret())
    print(json.dumps(v,sort_keys=True))
    if a.publish:print(json.dumps({'published_commit':publish(v)}))
if __name__=='__main__':main()
