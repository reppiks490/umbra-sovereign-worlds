#!/usr/bin/env python3
"""Opt-in bounded model-backed evaluation queue across 195,000 logical IDs.

This is a *durable identity scheduler*, not 195,000 concurrent neural models.
No jobs are enrolled, executed or repeated without the operator's explicit
commands. Actual inference is limited to a local authenticated model endpoint;
all outputs remain private and unpromoted research evidence.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sqlite3
import time
import uuid
from datetime import datetime,timezone
from pathlib import Path

SCHEMA='myriad.model_worker_queue.v26'
WORKER_COUNT=195_000
MAX_ENROLL=128
MAX_CALLS=4
HOUR=3600


def _integer(value,low,high,label):
    if type(value) is not int or not low<=value<=high:
        raise ValueError('Invalid '+label)
    return value


def open_db(path):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(str(path),timeout=20,isolation_level=None)
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA busy_timeout=20000')
    db.execute('''CREATE TABLE IF NOT EXISTS model_jobs (
        worker_id INTEGER PRIMARY KEY CHECK (worker_id BETWEEN 1 AND 195000),
        next_due INTEGER NOT NULL,
        repeating INTEGER NOT NULL CHECK(repeating IN (0,1)),
        state TEXT NOT NULL CHECK(state IN ('ready','leased','completed','quarantined')),
        lease_owner TEXT, lease_until INTEGER NOT NULL DEFAULT 0,
        attempts INTEGER NOT NULL DEFAULT 0, completed_count INTEGER NOT NULL DEFAULT 0,
        failures INTEGER NOT NULL DEFAULT 0, last_receipt TEXT, failure_class TEXT
        )''')
    db.execute('CREATE INDEX IF NOT EXISTS idx_model_due ON model_jobs(state,next_due,lease_until)')
    db.execute('''CREATE TABLE IF NOT EXISTS model_runs (
        hour TEXT NOT NULL, workflow TEXT NOT NULL,
        evidence_hmac TEXT NOT NULL, evidence_path TEXT NOT NULL,
        model_label TEXT NOT NULL, evaluated_requests INTEGER NOT NULL,
        correct INTEGER NOT NULL, previous_hmac TEXT,
        PRIMARY KEY (hour,workflow)
        )''')
    return db


def enroll(db_path,start,count,due,repeat=False):
    _integer(start,1,WORKER_COUNT,'start identity')
    _integer(count,1,MAX_ENROLL,'enrollment count')
    _integer(due,0,2**40,'UTC due timestamp')
    if start+count-1>WORKER_COUNT or type(repeat) is not bool:
        raise ValueError('Enrollment address range or repeat flag invalid')
    db=open_db(db_path)
    try:
        db.execute('BEGIN IMMEDIATE')
        try:
            values=[(i,due,int(repeat),'ready') for i in range(start,start+count)]
            db.executemany('INSERT INTO model_jobs(worker_id,next_due,repeating,state) VALUES (?,?,?,?)',values)
            db.execute('COMMIT')
        except sqlite3.IntegrityError as exc:
            db.execute('ROLLBACK')
            raise ValueError('Identity already enrolled or invalid') from exc
        except Exception:
            db.execute('ROLLBACK')
            raise
    finally:
        db.close()
    return {'schema':SCHEMA,'enrolled':count,'first':f'E{start:06d}',
            'last':f'E{start+count-1:06d}','repeats_hourly':repeat,
            'live_calls_started':0,'automatic_promotions':0}


def claim(db,owner,now,lease_seconds=120):
    if not isinstance(owner,str) or not 1<=len(owner)<=100:
        raise ValueError('Invalid lease identity')
    _integer(now,0,2**40,'clock')
    _integer(lease_seconds,30,3600,'lease time')
    db.execute('BEGIN IMMEDIATE')
    try:
        row=db.execute('''SELECT worker_id,next_due FROM model_jobs
           WHERE next_due<=? AND (state='ready' OR (state='leased' AND lease_until<=?))
           ORDER BY next_due,worker_id LIMIT 1''',(now,now)).fetchone()
        if row is None:
            db.execute('COMMIT')
            return None
        idx,due=row
        db.execute('''UPDATE model_jobs SET state='leased',lease_owner=?,lease_until=?,
            attempts=attempts+1 WHERE worker_id=?''',(owner,now+lease_seconds,idx))
        db.execute('COMMIT')
        return idx,due
    except Exception:
        db.execute('ROLLBACK')
        raise


def _validate_owned(db,owner,idx,due,now):
    row=db.execute('SELECT lease_owner,next_due,lease_until,state,repeating,last_receipt FROM model_jobs WHERE worker_id=?',(idx,)).fetchone()
    if not row or row[0]!=owner or row[1]!=due or row[2]<=now or row[3]!='leased':
        raise ValueError('Stale, expired, unowned or already completed lease')
    return row


def complete(db,owner,idx,due,private_evidence,now):
    """Only a valid private HMAC receipt can complete a model-backed occurrence."""
    db.execute('BEGIN IMMEDIATE')
    try:
        state=_validate_owned(db,owner,idx,due,now)
        expected_hour=datetime.fromtimestamp(due,timezone.utc).strftime('%Y%m%dT%H')
        expected_name=f'E{idx:06d}_{expected_hour}.private.json'
        target=Path(private_evidence)
        if target.name!=expected_name:
            raise ValueError('Private evidence path is not scoped to the claimed occurrence')
        import evolution_model_evidence_v24 as evidence
        if not target.is_file() or target.is_symlink() or target.stat().st_size>131_072:
            raise ValueError('Expected bounded regular private-evidence file')
        report=json.loads(target.read_text())
        verification=evidence.verify(report)
        if verification['completed'] is not True or verification['score_replayed'] is not True or verification['production_authority'] is not False:
            raise ValueError('Model evidence failed replay or completion')
        expected_seed=(idx*65537+(due//HOUR))%(2**32)
        if type(report.get('seed')) is not int or report['seed']!=expected_seed:
            raise ValueError('Model evaluation seed does not bind to claimed workflow and hour')
        if type(report.get('correct')) is not int or type(report.get('completed_requests')) is not int:
            raise ValueError('Malformed model score')
        hour=datetime.fromtimestamp(due,timezone.utc).strftime('%Y-%m-%dT%H')
        wf=f'E{idx:06d}'
        db.execute('''INSERT INTO model_runs(hour,workflow,evidence_hmac,evidence_path,
          model_label,evaluated_requests,correct,previous_hmac)
          VALUES (?,?,?,?,?,?,?,?)''',(hour,wf,report['hmac_sha256'],str(target.resolve()),
           report['model'],report['completed_requests'],report['correct'],state[5]))
        new_state='ready' if state[4]==1 else 'completed'
        new_due=due+HOUR if state[4]==1 else due
        db.execute('''UPDATE model_jobs SET completed_count=completed_count+1,
          last_receipt=?,state=?,next_due=?,lease_owner=NULL,lease_until=0,
          failure_class=NULL WHERE worker_id=?''',(report['hmac_sha256'],new_state,new_due,idx))
        db.execute('COMMIT')
        return {'workflow':wf,'hour':hour,'score':report['correct'],
                'requests':report['completed_requests'],'receipt_hmac':report['hmac_sha256'],
                'next_hour_scheduled':state[4]==1,'model_identity_authenticated':False}
    except Exception:
        db.execute('ROLLBACK')
        raise


def quarantine(db,owner,idx,due,now,failure_class):
    if not isinstance(failure_class,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}',failure_class):
        raise ValueError('Failure category must not contain secret-bearing messages')
    db.execute('BEGIN IMMEDIATE')
    try:
        _validate_owned(db,owner,idx,due,now)
        db.execute('''UPDATE model_jobs SET state='quarantined',lease_owner=NULL,
            lease_until=0,failures=failures+1,failure_class=? WHERE worker_id=?''',
            (failure_class,idx))
        db.execute('COMMIT')
    except Exception:
        db.execute('ROLLBACK')
        raise


def status(db_path,now=None):
    if now is None:now=int(time.time())
    _integer(now,0,2**40,'clock')
    db=open_db(db_path)
    try:
        items=dict(db.execute('SELECT state,COUNT(*) FROM model_jobs GROUP BY state').fetchall())
        total=sum(items.values())
        return {'schema':SCHEMA,'addressable_logical_identities':WORKER_COUNT,
                'enrolled_model_workers':total,
                'ready':items.get('ready',0),'leased':items.get('leased',0),
                'completed':items.get('completed',0),'quarantined':items.get('quarantined',0),
                'overdue_ready':db.execute("SELECT COUNT(*) FROM model_jobs WHERE state='ready' AND next_due<=?",(now,)).fetchone()[0],
                'completed_occurrences':db.execute('SELECT COUNT(*) FROM model_runs').fetchone()[0],
                'active_neural_processes_claimed':0,'fleet_hourly_model_sla_verified':False,
                'production_authority':False,'automatic_merge':False}
    finally:db.close()


def process(db_path,out_dir,*,model,port,max_jobs=1,count=2,max_tokens=16,
            budget=32,timeout=10,deadline_seconds=30,clock=None,authorize=False):
    _integer(max_jobs,1,MAX_CALLS,'bounded job count')
    _integer(count,1,4,'questions per job')
    _integer(max_tokens,1,64,'requested token limit')
    _integer(budget,1,512,'per-job budget')
    if budget<count*max_tokens:raise ValueError('Requested per-job completion budget too low')
    if authorize is not True:raise PermissionError('Explicit --authorize-local-model required')
    import evolution_model_evidence_v24 as evidence
    # Validate model and credentials before claiming or quarantining a job.
    evidence.config(port,model,1,count,max_tokens,budget,timeout,deadline_seconds)
    evidence.secret()
    if not re.fullmatch(r'[A-Za-z0-9._~+/-]{1,512}={0,2}',os.environ.get('MYRIAD_LOCAL_MODEL_TOKEN','')):
        raise PermissionError('Local endpoint bearer credential required')
    out_dir=Path(out_dir)
    out_dir.mkdir(parents=True,exist_ok=True)
    due_time=int(time.time()) if clock is None else int(clock)
    owner=f'model-fence-{uuid.uuid4().hex}'
    db=open_db(db_path)
    completed=[];failed=[]
    try:
        for _ in range(max_jobs):
            claimed=claim(db,owner,due_time)
            if claimed is None:break
            idx,due=claimed
            hour=datetime.fromtimestamp(due,timezone.utc).strftime('%Y%m%dT%H')
            name=f'E{idx:06d}_{hour}.private.json'
            path=out_dir/name
            seed=(idx*65537+(due//3600))%(2**32)
            try:
                evidence.run(port,model,seed,count,max_tokens,budget,timeout,deadline_seconds,path,authorize=True)
                completed.append(complete(db,owner,idx,due,path,due_time))
            except Exception as exc:
                try:quarantine(db,owner,idx,due,due_time,type(exc).__name__)
                except ValueError:
                    # Expired/stolen lease must never be converted to an accepted result.
                    pass
                failed.append({'worker':f'E{idx:06d}','error_class':type(exc).__name__})
    finally:db.close()
    return {'schema':SCHEMA,'model_evaluation_occurrences':len(completed),
            'completed':completed,'quarantined_or_failed':failed,
            'requested_max_jobs':max_jobs,'full_195000_model_hourly_sla':False,
            'automatic_model_promotions':0,'live_trading_authorized':False}


def hour_timestamp(text):
    if not isinstance(text,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}',text):
        raise ValueError('Due hour must use YYYY-MM-DDTHH UTC')
    dt=datetime.strptime(text,'%Y-%m-%dT%H').replace(tzinfo=timezone.utc)
    if dt.strftime('%Y-%m-%dT%H')!=text:raise ValueError('Noncanonical due hour')
    return int(dt.timestamp())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sp=p.add_subparsers(dest='cmd',required=True)
    e=sp.add_parser('enroll');e.add_argument('--db',required=True);e.add_argument('--start',type=int,required=True)
    e.add_argument('--count',type=int,required=True);e.add_argument('--due-hour',required=True);e.add_argument('--repeat-hourly',action='store_true')
    s=sp.add_parser('status');s.add_argument('--db',required=True)
    r=sp.add_parser('run');r.add_argument('--db',required=True);r.add_argument('--private-out',required=True)
    r.add_argument('--port',type=int,required=True);r.add_argument('--model',required=True)
    r.add_argument('--max-jobs',type=int,default=1);r.add_argument('--count',type=int,default=2)
    r.add_argument('--max-tokens',type=int,default=16);r.add_argument('--budget',type=int,default=32)
    r.add_argument('--timeout',type=int,default=10);r.add_argument('--deadline-seconds',type=float,default=30)
    r.add_argument('--authorize-local-model',action='store_true')
    args=p.parse_args()
    if args.cmd=='enroll':result=enroll(args.db,args.start,args.count,hour_timestamp(args.due_hour),args.repeat_hourly)
    elif args.cmd=='status':result=status(args.db)
    else:result=process(args.db,args.private_out,model=args.model,port=args.port,max_jobs=args.max_jobs,
        count=args.count,max_tokens=args.max_tokens,budget=args.budget,timeout=args.timeout,
        deadline_seconds=args.deadline_seconds,authorize=args.authorize_local_model)
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=='__main__':main()
