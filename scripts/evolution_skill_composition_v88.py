"""Bounded declarative skill composition over approved public read capabilities.

External text is data only: never an executable instruction, URL or argument
to another provider. Ordered acyclic plans undergo full validation before I/O.
Receipts are structurally replayable, not independent provider attestation.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
import evolution_capability_fabric_v86 as fabric

SCHEMA='myriad.skill_composition.v88'
MAX_NODES=16
MAX_READS=5

def digest(x):
    return hashlib.sha256(fabric.canonical(x)).hexdigest()

def valid_id(x):
    return isinstance(x,str) and re.fullmatch('[a-z][a-z0-9_]{0,31}',x) is not None

def valid_sha(x):
    return isinstance(x,str) and re.fullmatch('[a-f0-9]{64}',x) is not None

def dependencies(n):
    if n['op']=='read':return []
    if n['op']=='count':return [n['input']]
    return n['inputs']

def validate(plan):
    if not isinstance(plan,dict) or set(plan)!={'nodes','output'} or not isinstance(plan['nodes'],list) or not 1<=len(plan['nodes'])<=MAX_NODES or not valid_id(plan['output']):
        raise ValueError('invalid plan')
    kinds={};providers=set();by_id={}
    for n in plan['nodes']:
        if not isinstance(n,dict) or not valid_id(n.get('id')) or n['id'] in kinds:
            raise ValueError('node identity')
        i=n['id'];op=n.get('op')
        if op=='read':
            if set(n)!={'id','op','tool','args'} or not isinstance(n['tool'],str):raise ValueError('read node')
            fabric.validate(n['tool'],n['args'])
            provider=fabric.SPECS[n['tool']][0]
            if provider in providers or len(providers)>=MAX_READS:raise ValueError('provider budget per skill')
            providers.add(provider)
            kinds[i]='quote' if n['tool'] in fabric.SYMBOLS else 'discovery'
        elif op=='count':
            if set(n)!={'id','op','input'} or not valid_id(n['input']) or kinds.get(n['input'])!='discovery':raise ValueError('count expects preceding discovery')
            kinds[i]='integer'
        elif op=='join':
            if set(n)!={'id','op','inputs'} or not isinstance(n['inputs'],list) or not 1<=len(n['inputs'])<=MAX_NODES or any(not valid_id(x) or x not in kinds or kinds[x]=='bundle' for x in n['inputs']) or len(set(n['inputs']))!=len(n['inputs']):
                raise ValueError('invalid join')
            kinds[i]='bundle'
        else:raise ValueError('unsupported operation')
        by_id[i]=n
    if plan['output'] not in kinds:raise ValueError('missing output')
    required=set();stack=[plan['output']]
    while stack:
        i=stack.pop()
        if i not in required:required.add(i);stack.extend(dependencies(by_id[i]))
    if required!=set(kinds):raise ValueError('dead nodes')
    if len(fabric.canonical(plan))>16384:raise ValueError('plan size')
    return kinds

def evidence(n,r):
    fields={'tool','provider','observed_at','response_sha256','data','production_authority','execution_authorized','cache_hit'}
    if not isinstance(r,dict) or set(r)!=fields or r['tool']!=n['tool'] or r['provider']!=fabric.SPECS[n['tool']][0] or type(r['observed_at']) is not int or r['observed_at']<0 or not valid_sha(r['response_sha256']) or r['production_authority'] is not False or r['execution_authorized'] is not False or type(r['cache_hit']) is not bool:
        raise ValueError('invalid evidence envelope')
    if n['tool'] in fabric.SYMBOLS:
        row=r['data'];keys={'symbol','price','quote_currency'}|({'source_time_ms'} if n['tool']=='bybit.spot' else set())
        if not isinstance(row,dict) or set(row)!=keys or row['symbol']!=n['args']['symbol']:raise ValueError('quote identity')
        expected='USDT' if n['tool']=='bybit.spot' else n['args']['symbol'].split('-')[1]
        if row['quote_currency']!=expected:raise ValueError('quote currency')
        fabric.price(row['price'])
        if 'source_time_ms' in row and (type(row['source_time_ms']) is not int or row['source_time_ms']<0):raise ValueError('quote time')
    else:
        rows=r['data'];keys={'id','url','license'} if n['tool']=='github.search' else {'doi','title'} if n['tool']=='crossref.search' else {'id','revision','license'}
        if not isinstance(rows,list) or len(rows)>n['args']['limit'] or any(not isinstance(row,dict) or set(row)!=keys for row in rows):raise ValueError('invalid discovery data')
    if len(fabric.canonical(r))>fabric.MAX_BYTES:raise ValueError('evidence size')
    return r

def calculate(n,states):
    if n['op']=='count':return len(states[n['input']]['value']['data'])
    return {i:states[i]['value'] for i in n['inputs']}

def error_name(e):
    s=type(e).__name__
    return s if re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,79}',s) else 'Error'

def execute(plan,local):
    validate(plan)
    # Freeze caller-owned input before any provider request.
    plan=json.loads(fabric.canonical(plan))
    states={};reads=0
    for n in plan['nodes']:
        i=n['id']
        if any(states[d]['status']!='completed' for d in dependencies(n)):
            states[i]={'status':'blocked'};continue
        try:
            if n['op']=='read':
                reads+=1
                value=evidence(n,local.invoke(n['tool'],n['args']))
            else:value=calculate(n,states)
            states[i]={'status':'completed','value':value}
        except Exception as e:
            states[i]={'status':'failed','error_class':error_name(e)}
    final=states[plan['output']]
    r={'schema':SCHEMA,'plan_sha256':digest(plan),'nodes':states,'reads':reads,
       'status':'completed' if final['status']=='completed' else 'failed',
       'output':final.get('value'),'production_authority':False,'semantic_mastery_certified':False}
    r['receipt_sha256']=digest(r)
    return r

def verify(receipt,plan):
    try:
        validate(plan)
        if not isinstance(receipt,dict):return False
        r=dict(receipt);sig=r.pop('receipt_sha256',None)
        if not valid_sha(sig) or sig!=digest(r) or set(r)!={'schema','plan_sha256','nodes','reads','status','output','production_authority','semantic_mastery_certified'} or r['schema']!=SCHEMA or r['plan_sha256']!=digest(plan) or r['production_authority'] is not False or r['semantic_mastery_certified'] is not False:return False
        states=r['nodes']
        if not isinstance(states,dict) or set(states)!={n['id'] for n in plan['nodes']}:return False
        reads=0
        for n in plan['nodes']:
            s=states[n['id']];blocked=any(states[d]['status']!='completed' for d in dependencies(n))
            if blocked:
                if s!={'status':'blocked'}:return False
                continue
            if n['op']=='read':reads+=1
            if not isinstance(s,dict):return False
            if s.get('status')=='failed':
                if n['op']!='read' or set(s)!={'status','error_class'} or not isinstance(s['error_class'],str) or not re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,79}',s['error_class']):return False
            elif s.get('status')=='completed':
                if set(s)!={'status','value'}:return False
                if n['op']=='read':evidence(n,s['value'])
                elif fabric.canonical(s['value'])!=fabric.canonical(calculate(n,states)):return False
            else:return False
        final=states[plan['output']]
        return type(r['reads']) is int and r['reads']==reads and r['status']==('completed' if final['status']=='completed' else 'failed') and fabric.canonical(r['output'])==fabric.canonical(final.get('value'))
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError):return False

def discovery_plan(query,limit=2):
    nodes=[]
    for i,t in [('papers','crossref.search'),('repositories','github.search'),('models','hf.models')]:
        nodes.append({'id':i,'op':'read','tool':t,'args':{'query':query,'limit':limit}})
        nodes.append({'id':i+'_count','op':'count','input':i})
    nodes.append({'id':'bundle','op':'join','inputs':[n['id'] for n in nodes]})
    plan={'nodes':nodes,'output':'bundle'}
    validate(plan);return plan

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--query',required=True);p.add_argument('--authorize-public-read',action='store_true');a=p.parse_args()
    if not a.authorize_public_read:raise PermissionError('public read authorization required')
    plan=discovery_plan(a.query);r=execute(plan,fabric.Fabric(Path(a.root)))
    if not verify(r,plan):raise ValueError('receipt replay failure')
    print(json.dumps(r,sort_keys=True))
if __name__=='__main__':main()
