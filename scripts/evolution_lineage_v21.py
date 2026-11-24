#!/usr/bin/env python3
"""Independent read-only verification of prior-hour peer learning lineage.

No code promotions and no cryptographic identity attestation: hashes demonstrate
consistency, not who authored the evidence. Historical v1.8/v1.9 peer-used
records without parent receipts are explicitly classified as legacy/unproven.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path
import umbra_evolution_mesh as mesh
from evolution_tribunal_v19 import verify_record

SCHEMA='umbra.evolution.parent_link.v21'
RESULT_SCHEMA='umbra.evolution.lineage.tribunal.v21'
PARENT_FIELDS={'parent_workflow','parent_hour','parent_receipt_sha256','parent_domain'}


def validate_child(db, obj, *, max_depth=1):
    if not isinstance(obj,dict):raise ValueError('Invalid child evidence type')
    reviewed=verify_record(obj)
    if obj.get('peer_provenance_schema')!=SCHEMA:
        if obj.get('peer_used'):
            return {'status':'legacy_unproven','child':obj.get('workflow'),'parent':None}
        return {'status':'legacy_no_peer','child':obj.get('workflow'),'parent':None}
    parent=obj.get('peer_parent')
    if obj.get('peer_used') is not bool(parent):raise ValueError('Child peer-use flag contradicts parent metadata')
    if parent is None:
        # Explicitly recorded absence of peer assistance must be consistent with
        # the exact deterministic training algorithm, not just the booleans.
        identity=mesh.workflow(int(obj['workflow'][1:]))
        replay=mesh.train(identity,hour=obj['hour'],steps=obj['steps'],peer=None)
        if obj['parameters']!=replay['parameters']:
            raise ValueError('No-peer child does not match deterministic training replay')
        return {'status':'no_prior_parent','child':obj['workflow'],'parent':None}
    if not isinstance(parent,dict) or set(parent)!=PARENT_FIELDS:
        raise ValueError('Malformed parent link')
    ref=parent.get('parent_receipt_sha256')
    if not isinstance(ref,str) or not re.fullmatch(r'[0-9a-f]{64}',ref):
        raise ValueError('Parent digest malformed')
    prior_hour=parent.get('parent_hour')
    if not isinstance(prior_hour,str) or not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d',prior_hour) or prior_hour>=obj['hour']:
        raise ValueError('Future or same-hour parent evidence')
    domain=parent.get('parent_domain')
    if domain!=obj['domain']:raise ValueError('Parameters may not cross domain boundary')
    source=parent.get('parent_workflow')
    if source==obj['workflow'] or not isinstance(source,str) or not re.fullmatch(r'E\d{6}',source):
        raise ValueError('Self-link or malformed parent workflow')
    row=db.execute('SELECT domain,receipt,record FROM runs WHERE hour=? AND workflow=?',(prior_hour,source)).fetchone()
    if not row:raise ValueError('Missing parent evidence')
    row_domain,stored_digest,encoded=row
    if (row_domain,stored_digest)!=(domain,ref):raise ValueError('Parent hash or domain mismatch')
    original=json.loads(encoded)
    if original.get('receipt_sha256')!=ref or original.get('domain')!=domain:
        raise ValueError('Tampered parent record')
    assessed=verify_record(original)
    if assessed['review_state']!='quarantined':raise ValueError('Unqualified parent claim')
    if original.get('deployment_authorized') or original.get('real_model_weight_training'):
        raise ValueError('Unauthorized parent evidence')
    expected=mesh.workflow(int(source[1:]))
    if expected['domain']!=domain:raise ValueError('Parent workflow/domain mismatch')
    # Re-run the actual deterministic synthetic trainer with the exact
    # referenced parent input: a valid hash and a valid review flag alone do
    # not establish that a child actually used that parent's parameters.
    child_workflow=mesh.workflow(int(obj['workflow'][1:]))
    expected=mesh.train(child_workflow,hour=obj['hour'],steps=obj['steps'],peer=original['parameters'])
    if obj['parameters']!=expected['parameters'] or obj.get('algorithm')!=expected['algorithm']:
        raise ValueError('Claimed peer influence fails deterministic re-execution')
    return {'status':'verified_prior_hour','child':obj['workflow'],'parent':source,'source_receipt_sha256':ref,
            'source_hour':prior_hour,'source_domain':domain}


def audit(db_path,*,limit=5000,start_row=1):
    if not 1<=limit<=200000 or start_row<1:raise ValueError('Unbounded audit')
    db_path=Path(db_path).resolve()
    if not db_path.is_file():raise FileNotFoundError('Ledger database missing')
    with sqlite3.connect(f'file:{db_path}?mode=ro',uri=True) as db:
        db.execute('PRAGMA query_only=ON')
        rows=db.execute('SELECT rowid,hour,workflow,domain,receipt,record FROM runs WHERE rowid>=? ORDER BY rowid LIMIT ?',
                        (start_row,limit)).fetchall()
        counts={'verified_prior_hour':0,'no_prior_parent':0,'legacy_unproven':0,'legacy_no_peer':0,'failed':0}
        inspected=[];failures=[]
        for rid,hour,wf,domain,receipt,raw in rows:
            try:
                obj=json.loads(raw)
                if (obj.get('hour'),obj.get('workflow'),obj.get('domain'),obj.get('receipt_sha256'))!=(hour,wf,domain,receipt):
                    raise ValueError('Child ledger metadata mismatch')
                result=validate_child(db,obj)
                counts[result['status']]+=1
                inspected.append([rid,result['status'],receipt,result.get('source_receipt_sha256')])
            except (ValueError,KeyError,TypeError,json.JSONDecodeError) as e:
                counts['failed']+=1;failures.append({'rowid':rid,'failure':type(e).__name__,'cause':str(e)[:120]})
                inspected.append([rid,'failed',receipt,None])
    summary={'schema':RESULT_SCHEMA,'inspected':len(rows),'start_row':start_row,'last_row':rows[-1][0] if rows else None,
             'categories':counts,'all_records_cryptographically_authenticated':False,'historical_peer_provenance_reconstructed':False,
             'new_production_integrations':0,'market_edge_certified':False,'failures':failures[:30],
             'evidence_set_sha256':hashlib.sha256(json.dumps(inspected,separators=(',',':')).encode()).hexdigest()}
    summary['report_sha256']=hashlib.sha256(json.dumps(summary,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ledger',required=True);p.add_argument('--limit',type=int,default=5000)
    p.add_argument('--start-row',type=int,default=1);p.add_argument('--output')
    a=p.parse_args();v=audit(a.ledger,limit=a.limit,start_row=a.start_row)
    if a.output:
        dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('x') as h:json.dump(v,h,sort_keys=True,indent=2)
    print(json.dumps(v,sort_keys=True,indent=2))
if __name__=='__main__':main()
