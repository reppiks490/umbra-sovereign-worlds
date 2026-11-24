#!/usr/bin/env python3
"""UMBRA daily fleet: fail-closed manual workflow coverage and batch receipt audit.

A synthetic scenario case executing inside a grouped runner is NOT the same as
triggering its individual workflow_dispatch YAML. No broker, paid or deploy calls.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

FILENAME = re.compile(r'umbra-u(?P<number>\d{3,4})-[a-z0-9-]+\.yml\Z')
HEX64 = re.compile(r'[0-9a-f]{64}\Z')


def verify_manual_workflows(root: Path, expected_base: int = 300, expected_advanced: int = 5000) -> dict:
    root=Path(root)
    directory=root/'.github'/'workflows'
    if not directory.is_dir():raise ValueError('Workflow directory missing')
    ids=set()
    for path in directory.glob('umbra-u*.yml'):
        if path.is_symlink() or not path.is_file():raise ValueError(f'Untrusted workflow path: {path}')
        match=FILENAME.fullmatch(path.name)
        if not match:raise ValueError(f'Invalid numbered workflow filename: {path.name}')
        number=int(match.group('number'))
        if number in ids:raise ValueError(f'Duplicate workflow identity: {number}')
        ids.add(number)
        code=f'U{number:03d}' if number<=300 else f'U{number:04d}'
        src=path.read_text(encoding='utf-8')
        if 'workflow_dispatch:' not in src or re.search(r'^\s*schedule\s*:',src,re.M):
            raise ValueError(f'Unsafe or nonmanual trigger: {path}')
        expected_executable='umbra_lab.mjs' if number<=300 else 'umbra_advanced_lab.mjs'
        if expected_executable not in src or f'--id {code}' not in src:
            raise ValueError(f'Workflow command does not match identity: {path}')
    allowed=set(range(1,expected_base+1))|set(range(301,301+expected_advanced))
    if ids!=allowed:raise ValueError(f'Workflow coverage mismatch: missing={len(allowed-ids)}, extra={len(ids-allowed)}')
    return {'schema':'umbra.daily.coverage.v1','count':len(ids),'base':expected_base,'advanced':expected_advanced,
            'individual_workflows_triggered':False,'cases_executed_by_batch':True,'production_authority':False}


def _safe_json(path):
    def unique(pairs):
        o={}
        for k,v in pairs:
            if k in o:raise ValueError(f'Duplicate JSON key: {k}')
            o[k]=v
        return o
    if path.is_symlink() or not path.is_file() or path.stat().st_size>200_000:
        raise ValueError('Evidence file missing, link or too large')
    return json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=unique)


def _int(x,n):
    if type(x) is not int or x!=n:raise ValueError(f'Invalid {n}: got {x}')


def verify_evidence(directory:Path,base_count:int=300,advanced_count:int=5000,shards:int=10)->dict:
    root=Path(directory)
    if not (1<=shards<=100) or advanced_count%shards:raise ValueError('Invalid workload geometry')
    items=set(p.name for p in root.iterdir())
    expected={'base.json'} | {f'shard-{i}.json' for i in range(shards)}
    if items!=expected:raise ValueError(f'Evidence shard coverage mismatch: {items^expected}')
    base=_safe_json(root/'base.json')
    if base.get('schema')!='umbra.synthetic.catalog.audit.v1' or type(base.get('failed')) is not int or base['failed']!=0:
        raise ValueError('Base audit failed')
    for k in ('passed','total'):_int(base.get(k),base_count)
    digest_list=[]
    for i in range(shards):
        r=_safe_json(root/f'shard-{i}.json')
        if r.get('schema')!='umbra.synthetic.advanced-shard.v1':raise ValueError('Unexpected shard schema')
        for key,value in [('shard',i),('totalShards',shards),('passed',advanced_count//shards),('expected',advanced_count//shards),('failed',0)]:_int(r.get(key),value)
        if r.get('failures')!=[] or not isinstance(r.get('aggregateDigest'),str) or not HEX64.fullmatch(r['aggregateDigest']):
            raise ValueError('Unverifiable shard evidence')
        digest_list.append(r['aggregateDigest'])
    return {'schema':'umbra.daily.audit.v1','total_passed':base_count+advanced_count,
            'base_passed':base_count,'advanced_passed':advanced_count,'shards':shards,
            'shard_digests':digest_list,'independent_external_validation':False,'individual_actions_run_count':0,
            'authority':'synthetic read-only only'}


def validate_schedule(path:Path)->dict:
    s=Path(path).read_text(encoding='utf-8')
    crons=re.findall(r"^\s*- cron:\s*['\"]([^'\"]+)['\"]\s*$",s,re.M)
    if crons!=['23 3,15 * * *'] or 'workflow_dispatch:' not in s or 'max-parallel: 2' not in s or 'contents: read' not in s:
        raise ValueError('Daily fleet schedule or safety budget is not as specified')
    return {'valid':True,'daily_windows_utc':["03:23","15:23"],'expected_cases_per_window':5300,
            'scheduled_case_executions_per_day':10600,'individual_actions_dispatched':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['catalog','evidence','schedule'])
    p.add_argument('--root',default='.')
    p.add_argument('--evidence-dir',default='fleet-evidence')
    args=p.parse_args()
    if args.command=='catalog': result=verify_manual_workflows(Path(args.root))
    elif args.command=='evidence':result=verify_evidence(Path(args.evidence_dir))
    else:result=validate_schedule(Path(args.root)/'.github'/'workflows'/'umbra-daily-scenario-fleet.yml')
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
