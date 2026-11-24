#!/usr/bin/env python3
"""Private, independently scored receipts for bounded opt-in loopback model evaluation.

Only deterministic toy arithmetic is allowed. The upstream server is untrusted:
its model identity and token usage are self-reported. This never trains weights,
trades, authorizes merges, or persists bearer tokens.
"""
from __future__ import annotations
import argparse
import hashlib
import hmac
import json
import os
import re
import time
from pathlib import Path

import evolution_local_model_v22 as base

SCHEMA = 'myriad.private_model_evidence.v24'
MAX_RAW_CHARS = 4096


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode('utf-8')


def secret():
    value = os.environ.get('MYRIAD_EVIDENCE_HMAC_KEY', '')
    if not isinstance(value, str) or not 32 <= len(value) <= 256 or not value.isascii() or any(ord(c) < 33 or ord(c) > 126 for c in value):
        raise PermissionError('Set a separate 32–256 character private MYRIAD_EVIDENCE_HMAC_KEY')
    return value.encode('ascii')


def sign(value, key):
    return hmac.new(key, canonical(value), hashlib.sha256).hexdigest()


def integer(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError('Invalid '+name)
    return value


def config(port,model,seed,count,max_tokens,budget,timeout,deadline_seconds):
    base.config(port,model,seed,count,max_tokens,budget,timeout)
    if type(deadline_seconds) not in (float,int) or not 0 < deadline_seconds <= 60:
        raise ValueError('Total deadline must be between 0 and 60 seconds')


def run(port,model,seed,count,max_tokens,budget,timeout,deadline_seconds,out,*,authorize=False):
    config(port,model,seed,count,max_tokens,budget,timeout,deadline_seconds)
    if authorize is not True:
        raise PermissionError('Explicit --authorize required for local inference')
    bearer = os.environ.get('MYRIAD_LOCAL_MODEL_TOKEN','')
    if not isinstance(bearer,str) or not re.fullmatch(r'[A-Za-z0-9._~+/-]{1,512}={0,2}',bearer):
        raise PermissionError('Local bearer-token environment variable required')
    key = secret()
    target = Path(out)
    fd = os.open(target, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
    rows=[];status='incomplete'; error_class=None
    start=time.monotonic()
    try:
        for ix,(prompt,answer) in enumerate(base.tasks(seed,count),1):
            remaining=deadline_seconds-(time.monotonic()-start)
            if remaining <= 0:
                raise TimeoutError('Total inference deadline exceeded before call')
            # This is a bounded per-operation socket timeout, not a strict
            # total process kill. The hard deadline is checked between calls.
            content,used,response_hash=base.request(port,model,prompt,bearer,max_tokens,min(float(timeout),remaining))
            if not isinstance(content,str) or len(content)>MAX_RAW_CHARS:
                raise ValueError('Private raw-output length limit exceeded')
            integer(used,0,max_tokens,'reported model token usage')
            if not isinstance(response_hash,str) or not re.fullmatch('[0-9a-f]{64}',response_hash):
                raise ValueError('Invalid response-byte digest')
            rows.append({'task':ix,'prompt_sha256':sha(prompt.encode()),'expected_answer':answer,
                         'content':content,'completion_sha256':sha(content.encode()),
                         'response_sha256':response_hash,'reported_completion_tokens':used,
                         'exact_match':content.strip()==answer})
            if time.monotonic()-start > deadline_seconds:
                raise TimeoutError('Model request exceeded total elapsed deadline')
        status='completed'
    except BaseException as exc:
        error_class=type(exc).__name__
        raise
    finally:
        payload={'schema':SCHEMA,'status':status,'error_class':error_class,
                 'model':model,'seed':seed,'planned_requests':count,
                 'max_tokens_per_request':max_tokens,'requested_completion_budget':budget,
                 'deadline_seconds':deadline_seconds,'completed_requests':len(rows),
                 'reported_completion_tokens':sum(r['reported_completion_tokens'] for r in rows),
                 'correct':sum(r['exact_match'] for r in rows), 'rows':rows,
                 'endpoint_identity_authenticated':False,'trained_parameters':0,
                 'production_authority':False,'auto_promote':False,
                 'data_scope':'deterministic toy arithmetic; private raw outputs'}
        payload['hmac_sha256']=sign(payload,key)
        with os.fdopen(fd,'wb') as f:
            f.write(canonical(payload)+b'\n');f.flush();os.fsync(f.fileno())
    return payload


def verify(report):
    if not isinstance(report,dict):raise ValueError('Expected JSON object')
    key=secret()
    copy=dict(report)
    provided=copy.pop('hmac_sha256',None)
    if not isinstance(provided,str) or not hmac.compare_digest(sign(copy,key),provided):
        raise ValueError('Private evidence authentication mismatch')
    if copy.get('schema')!=SCHEMA or copy.get('production_authority') is not False or copy.get('auto_promote') is not False or copy.get('trained_parameters')!=0 or copy.get('endpoint_identity_authenticated') is not False:
        raise ValueError('Invalid evidence scope/authority')
    count=integer(copy['planned_requests'],1,8,'planned count')
    cap=integer(copy['max_tokens_per_request'],1,64,'per-request cap')
    budget=integer(copy['requested_completion_budget'],1,8*64,'budget')
    seed=integer(copy['seed'],0,2**32-1,'seed')
    if count*cap>budget:raise ValueError('Invalid requested cap')
    rows=copy['rows']
    if not isinstance(rows,list) or len(rows)>count or copy['completed_requests']!=len(rows):
        raise ValueError('Invalid evidence coverage')
    if copy['status'] not in ('completed','incomplete') or (copy['status']=='completed')!=(len(rows)==count):
        raise ValueError('Incomplete or overstated coverage')
    expected=base.tasks(seed,count)
    total_correct=0;total_tokens=0
    for ix,row in enumerate(rows,1):
        if not isinstance(row,dict):raise ValueError('Malformed evidence row')
        prompt,answer=expected[ix-1]
        if row.get('task')!=ix or row.get('prompt_sha256')!=sha(prompt.encode()) or row.get('expected_answer')!=answer:
            raise ValueError('Task provenance mismatch')
        content=row.get('content')
        if not isinstance(content,str) or len(content)>MAX_RAW_CHARS or row.get('completion_sha256')!=sha(content.encode()):
            raise ValueError('Completion evidence mismatch')
        if not isinstance(row.get('response_sha256'),str) or not re.fullmatch(r'[0-9a-f]{64}',row['response_sha256']):
            raise ValueError('Response hash format mismatch')
        tokens=integer(row.get('reported_completion_tokens'),0,cap,'reported completion tokens')
        passed=content.strip()==answer
        if row.get('exact_match') is not passed:
            raise ValueError('Stored score does not match replayed private output')
        total_correct+=passed;total_tokens+=tokens
    if copy['correct']!=total_correct or copy['reported_completion_tokens']!=total_tokens:
        raise ValueError('Summary does not match replay')
    return {'hmac_valid':True,'score_replayed':True,'completed':copy['status']=='completed',
            'correct':total_correct,'completed_requests':len(rows),
            'model_identity_authenticated':False,'independent_neural_output_reproduction':False,
            'production_authority':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    s=p.add_subparsers(dest='action',required=True)
    r=s.add_parser('run')
    r.add_argument('--port',type=int,required=True)
    r.add_argument('--model',required=True)
    r.add_argument('--seed',type=int,default=17)
    r.add_argument('--count',type=int,default=4)
    r.add_argument('--max-tokens',type=int,default=16)
    r.add_argument('--budget',type=int,default=64)
    r.add_argument('--timeout',type=int,default=10)
    r.add_argument('--deadline-seconds',type=float,default=30)
    r.add_argument('--out',required=True)
    r.add_argument('--authorize',action='store_true')
    q=s.add_parser('verify');q.add_argument('receipt')
    args=vars(p.parse_args());action=args.pop('action')
    response=run(**{k.replace('-','_'):v for k,v in args.items()}) if action=='run' else verify(json.loads(Path(args['receipt']).read_text()))
    print(json.dumps(response,sort_keys=True))

if __name__=='__main__':main()
