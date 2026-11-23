#!/usr/bin/env python3
"""Durable 195,000-identity evolution queue with idempotent leases & peer exchange.

Research proposals only. No claims of 195K hourly completion without measured
capacity. Intended for a single persistent host; GitHub Actions CI is not one.
"""
from __future__ import annotations
import argparse, json, os, sqlite3, sys, time
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0,str(Path(__file__).resolve().parent))
import umbra_evolution_mesh as mesh

SCHEMA='umbra.evolution.scheduler.v1'
HOUR=3600


def open_db(path):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(str(p),timeout=30,isolation_level=None)
    db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA busy_timeout=30000')
    db.execute('''CREATE TABLE IF NOT EXISTS worker_state (
        id INTEGER PRIMARY KEY CHECK(id BETWEEN 1 AND 195000),
        next_due INTEGER NOT NULL, lease_until INTEGER NOT NULL DEFAULT 0,
        lease_owner TEXT, attempts INTEGER NOT NULL DEFAULT 0,
        completed INTEGER NOT NULL DEFAULT 0, failures INTEGER NOT NULL DEFAULT 0,
        last_receipt TEXT)''')
    db.execute('CREATE INDEX IF NOT EXISTS ix_worker_due ON worker_state(next_due,lease_until)')
    db.execute('''CREATE TABLE IF NOT EXISTS runs(
        hour TEXT NOT NULL, workflow TEXT NOT NULL, domain TEXT NOT NULL,
        receipt TEXT NOT NULL, record TEXT NOT NULL,
        PRIMARY KEY(hour,workflow))''')
    db.execute('CREATE INDEX IF NOT EXISTS ix_runs_domain_hour ON runs(domain,hour)')
    db.execute('''CREATE TABLE IF NOT EXISTS proposals(
        workflow TEXT NOT NULL, hour TEXT NOT NULL, kind TEXT NOT NULL,
        record_hash TEXT NOT NULL, review_state TEXT NOT NULL CHECK(review_state IN ('quarantined','rejected')),
        PRIMARY KEY(workflow,hour))''')
    return db


def initialize(db_path,start_at=None):
    if start_at is None:start_at=int(time.time())
    if start_at<0:raise ValueError('Invalid start time')
    db=open_db(db_path)
    total=db.execute('SELECT COUNT(*) FROM worker_state').fetchone()[0]
    if total not in (0,mesh.WORKFLOW_COUNT):raise RuntimeError('Partial registry; do not silently reinitialize')
    if total==0:
        # Spread 195k individual identities over the next hour, not a stampede.
        db.execute('BEGIN IMMEDIATE')
        try:
            for start in range(1,mesh.WORKFLOW_COUNT+1,5000):
                rows=[(wid,start_at+(wid*37)%HOUR) for wid in range(start,min(start+5000,mesh.WORKFLOW_COUNT+1))]
                db.executemany('INSERT INTO worker_state(id,next_due) VALUES (?,?)',rows)
            db.execute('COMMIT')
        except Exception:
            db.execute('ROLLBACK');raise
    current=db.execute('SELECT COUNT(*) FROM worker_state').fetchone()[0];db.close()
    return {'schema':SCHEMA,'registered_identities':current,'created':total==0,
            'hourly_capacity_verified':False,'agent_models_running':0,'automatic_promotions':0}


def claim(db,owner,now,lease_seconds=120):
    if not owner or len(owner)>70 or lease_seconds<30 or lease_seconds>3600:raise ValueError('Invalid worker lease')
    db.execute('BEGIN IMMEDIATE')
    try:
        row=db.execute('SELECT id,next_due FROM worker_state WHERE next_due<=? AND lease_until<=? ORDER BY next_due,id LIMIT 1',(now,now)).fetchone()
        if row is None:db.execute('COMMIT');return None
        idx,due=row
        db.execute('UPDATE worker_state SET lease_owner=?,lease_until=?,attempts=attempts+1 WHERE id=?',(owner,now+lease_seconds,idx))
        db.execute('COMMIT');return idx,due
    except Exception:db.execute('ROLLBACK');raise


def finish(db,owner,idx,due,record,now):
    if mesh.workflow(idx)['id']!=record['workflow']:raise ValueError('Worker identity mismatch')
    expected=record['receipt_sha256'];c=record.copy();c.pop('receipt_sha256')
    if mesh.digest(c)!=expected:raise ValueError('Corrupted learning record')
    logical_hour=datetime.fromtimestamp(due,tz=timezone.utc).strftime('%Y-%m-%dT%H')
    # Retries use deterministic due hour, independent of wall-clock completion.
    if record['hour']!=logical_hour:raise ValueError('Receipt/lease hour mismatch')
    db.execute('BEGIN IMMEDIATE')
    try:
        state=db.execute('SELECT lease_owner,next_due,lease_until FROM worker_state WHERE id=?',(idx,)).fetchone()
        if not state or state[0]!=owner or state[1]!=due or state[2]<now:raise ValueError('Expired or stolen worker lease')
        db.execute('INSERT OR IGNORE INTO runs(hour,workflow,domain,receipt,record) VALUES(?,?,?,?,?)',
                   (logical_hour,record['workflow'],record['domain'],expected,json.dumps(record,sort_keys=True)))
        db.execute('INSERT OR IGNORE INTO proposals(workflow,hour,kind,record_hash,review_state) VALUES(?,?,?,?,?)',
                   (record['workflow'],logical_hour,record['proposal_type'],expected,'quarantined' if record['review_status']=='candidate_for_manual_review' else 'rejected'))
        # Next scheduled occurrence exactly one hour after previous due; if overdue,
        # do not drop identities. Backlog remains observable and will drain only if capacity allows.
        db.execute('UPDATE worker_state SET completed=completed+1,last_receipt=?,next_due=?,lease_until=0,lease_owner=NULL WHERE id=?',
                   (expected,due+HOUR,idx))
        db.execute('COMMIT')
    except Exception:db.execute('ROLLBACK');raise


def process(db_path,*,max_jobs=12,steps=3,owner='local-worker',clock=None):
    if not 1<=max_jobs<=10000 or not 1<=steps<=64:raise ValueError('Unsupported run budget')
    now=int(time.time()) if clock is None else int(clock)
    db=open_db(db_path);completed=0;errors=[];last=[]
    try:
        for _ in range(max_jobs):
            item=claim(db,owner,now)
            if not item:break
            idx,due=item;wf=mesh.workflow(idx)
            h=datetime.fromtimestamp(due,tz=timezone.utc).strftime('%Y-%m-%dT%H')
            try:
                peer=mesh.peer_for(db,wf,h)
                record=mesh.train(wf,hour=h,steps=steps,peer=peer)
                record['peer_used']=peer is not None
                record.pop('receipt_sha256');record['receipt_sha256']=mesh.digest(record)
                finish(db,owner,idx,due,record,now)
                completed+=1;last.append({'worker':wf['id'],'receipt':record['receipt_sha256']})
            except Exception as exc:
                # Failed leases become retryable only after lease timeout, never
                # promoted or falsely recorded as successful.
                db.execute('UPDATE worker_state SET failures=failures+1 WHERE id=? AND lease_owner=?',(idx,owner))
                errors.append({'worker':wf['id'],'error':type(exc).__name__})
    finally:db.close()
    return {'schema':SCHEMA,'completed_this_invocation':completed,'failures':errors,'receipts':last,
            'actual_neural_gradient_training':0,'automated_code_integrations':0,'reviewable_proposal_evidence':completed,
            'full_195000_hourly_certified':False}


def status(db_path,now=None):
    if now is None:now=int(time.time())
    db=open_db(db_path)
    try:
        r=db.execute('SELECT COUNT(*),SUM(CASE WHEN next_due<=? THEN 1 ELSE 0 END),SUM(completed),SUM(failures),MIN(next_due) FROM worker_state',(now,)).fetchone()
        p=db.execute('SELECT COUNT(*),SUM(CASE WHEN review_state=\'quarantined\' THEN 1 ELSE 0 END) FROM proposals').fetchone()
        return {'schema':SCHEMA,'registered_workers':r[0],'overdue':r[1] or 0,'completed_occurrences':r[2] or 0,'failures':r[3] or 0,'next_due_utc':r[4],
                'evidence_proposals':p[0],'quarantined_proposals':p[1] or 0,'automated_production_integrations':0}
    finally:db.close()


def main():
    p=argparse.ArgumentParser();p.add_argument('--db',default='evolution-mesh.sqlite3');s=p.add_subparsers(dest='cmd',required=True)
    x=s.add_parser('init');x.add_argument('--start-at',type=int)
    x=s.add_parser('run');x.add_argument('--max-jobs',type=int,default=12);x.add_argument('--steps',type=int,default=3);x.add_argument('--owner',default=f'worker-pid-{os.getpid()}')
    s.add_parser('status');a=p.parse_args()
    if a.cmd=='init':v=initialize(a.db,a.start_at)
    elif a.cmd=='run':v=process(a.db,max_jobs=a.max_jobs,steps=a.steps,owner=a.owner)
    else:v=status(a.db)
    print(json.dumps(v,indent=2))
if __name__=='__main__':main()
