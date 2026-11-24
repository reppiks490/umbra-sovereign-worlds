"""Structural audit of recovered private FP16 pilot archives, not training replay.

Never extract archive paths, execute source, or expose individual weights/hashes.
Ledger losses and steps are historical claims, not independent learning evidence.
"""
import argparse,array,hashlib,json,math,sqlite3,stat,sys,tempfile,zipfile
from pathlib import Path

PREFIX='MYRIAD-OMEGA-v0.8/training/'
WEIGHTS=PREFIX+'agentbank_pilot100/agent_weights.fp16'
LEDGER=PREFIX+'agentbank_pilot100/weight_ledger.sqlite3'
VERIFY=PREFIX+'AGENT_PILOT_100_VERIFICATION.json'
RESULTS=PREFIX+'AGENT_PILOT_100_RESULTS.jsonl'
COLUMNS=('agent','status','steps','sha256','updated','baseline_loss','final_loss','heldout_loss','weight_precision')
MAX_METADATA=8*1024**2


def integer(x,a,b):return type(x) is int and a<=x<=b

def unique(pairs):
    d={}
    for k,v in pairs:
        if k in d:raise ValueError('duplicate JSON field')
        d[k]=v
    return d

def constant(x):raise ValueError('nonfinite JSON constant')

def decode(raw):return json.loads(raw,object_pairs_hook=unique,parse_constant=constant)

def read_metadata(z,name):
    with z.open(name) as f:b=f.read(MAX_METADATA+1)
    if len(b)>MAX_METADATA or len(b)!=z.getinfo(name).file_size:raise ValueError('metadata bounds')
    return b

def ledger_rows(raw,agents):
    with tempfile.TemporaryDirectory(prefix='myriad-pilot-audit-') as tmp:
        p=Path(tmp)/'ledger.sqlite3';p.write_bytes(raw)
        c=sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True)
        try:
            c.execute('PRAGMA trusted_schema=OFF');c.execute('PRAGMA query_only=ON')
            if c.execute('PRAGMA quick_check').fetchall()!=[('ok',)]:raise ValueError('ledger integrity')
            if c.execute("SELECT name,type FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()!=[('agent_weights','table')]:raise ValueError('ledger schema')
            if tuple(x[1] for x in c.execute('PRAGMA table_info(agent_weights)'))!=COLUMNS:raise ValueError('ledger columns')
            rows=c.execute('SELECT '+','.join(COLUMNS)+' FROM agent_weights ORDER BY agent LIMIT ?', (agents+1,)).fetchall()
        finally:c.close()
    if len(rows)!=agents:raise ValueError('ledger geometry')
    return rows

def audit(path,*,agents=100,parameters=411000):
    if not integer(agents,1,100) or not integer(parameters,1,411000):raise ValueError('pilot geometry bounds')
    p=Path(path);s=p.lstat()
    if not stat.S_ISREG(s.st_mode) or getattr(s,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',1024):raise ValueError('unsafe archive path')
    block_bytes=parameters*2;size=agents*block_bytes
    with zipfile.ZipFile(p) as z:
        members=z.infolist()
        if len(members)!=4 or {x.filename for x in members}!={WEIGHTS,LEDGER,VERIFY,RESULTS}:raise ValueError('archive layout')
        for x in members:
            mode=(x.external_attr>>16)&0xffff
            if x.is_dir() or stat.S_ISLNK(mode) or x.flag_bits&1:raise ValueError('unsafe member')
            if x.filename==WEIGHTS:
                if x.file_size!=size:raise ValueError('weight geometry')
            elif not 1<=x.file_size<=MAX_METADATA:raise ValueError('metadata geometry')
        rows=ledger_rows(read_metadata(z,LEDGER),agents)
        manifest=decode(read_metadata(z,VERIFY))
        if not isinstance(manifest,list) or len(manifest)!=agents or any(not isinstance(x,dict) or set(x)!={'agent','verified'} or not integer(x['agent'],1,agents) or x['verified'] is not True for x in manifest) or {x['agent'] for x in manifest}!=set(range(1,agents+1)):raise ValueError('verification manifest mismatch')
        distinct=set();steps=0;final_better=0;heldout_better=0
        with z.open(WEIGHTS) as f:
            for i,row in enumerate(rows,1):
                agent,status,n,digest,updated,baseline,final,heldout,precision=row
                if type(agent) is not int or agent!=i or status!='trained' or precision!='fp16' or not integer(n,1,10**9) or not isinstance(updated,str) or not updated:raise ValueError('invalid ledger row')
                if any(type(x) not in (int,float) or not math.isfinite(x) or x<0 for x in (baseline,final,heldout)):raise ValueError('invalid reported loss')
                b=f.read(block_bytes)
                if len(b)!=block_bytes:raise ValueError('truncated weight block')
                actual=hashlib.sha256(b).hexdigest()
                if digest!=actual or actual in distinct:raise ValueError('weight identity or duplicate')
                distinct.add(actual);v=array.array('H');v.frombytes(b)
                if sys.byteorder!='little':v.byteswap()
                if any((x&0x7c00)==0x7c00 for x in v):raise ValueError('nonfinite FP16 block')
                steps+=n;final_better+=final<baseline;heldout_better+=heldout<baseline
            if f.read(1):raise ValueError('trailing weight bytes')
        valid=invalid=0
        for line in read_metadata(z,RESULTS).splitlines():
            if not line.strip():continue
            try:
                if not isinstance(decode(line),dict):raise ValueError('not a JSON object')
                valid+=1
            except (ValueError,UnicodeError,RecursionError):invalid+=1
    return {'schema':'myriad.historical_pilot_audit.v98','structural_verified':True,'verified_agents':agents,'parameters_per_agent':parameters,'verified_weight_bytes':size,'distinct_finite_blocks':len(distinct),'recorded_optimizer_steps':steps,'reported_final_loss_improved':final_better,'reported_heldout_loss_improved':heldout_better,'result_jsonl_valid_lines':valid,'result_jsonl_invalid_lines':invalid,'optimizer_replay_verified':False,'full_historical_bank_verified':False,'semantic_mastery_certified':False,'production_authority':False}

def main():
    a=argparse.ArgumentParser();a.add_argument('archive');a.add_argument('--authorize-local-audit',action='store_true');args=a.parse_args()
    if not args.authorize_local_audit:raise PermissionError('local archive audit authorization required')
    print(json.dumps(audit(args.archive),sort_keys=True,allow_nan=False))
if __name__=='__main__':main()
