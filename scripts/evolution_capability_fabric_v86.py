"""Independent read-only public capability fabric. No remote code execution.

Only fixed public endpoints, explicit public search inputs, bounded requests,
persistent per-provider admission and fresh normalized cached observations.
No credentials, trading operations, arbitrary URLs, or automatic installation.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import re
import sqlite3
import stat
import time
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation
from pathlib import Path

MAX_BYTES=1048576
SPECS={
    'github.search':('github','https://api.github.com/search/repositories',3600,30,10),
    'hf.models':('hf','https://huggingface.co/api/models',3600,60,10),
    'hf.spaces':('hf','https://huggingface.co/api/spaces',3600,60,10),
    'hf.datasets':('hf','https://huggingface.co/api/datasets',3600,60,10),
    'crossref.search':('crossref','https://api.crossref.org/works',3600,60,10),
    'coinbase.spot':('coinbase','https://api.coinbase.com/v2/prices',60,120,10),
    'bybit.spot':('bybit','https://api.bybit.com/v5/market/tickers',60,120,10),
}
SYMBOLS={'coinbase.spot':('BTC-USD','ETH-USD','SOL-USD'),
         'bybit.spot':('BTCUSDT','ETHUSDT','SOLUSDT')}

class BudgetError(RuntimeError):pass

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise ValueError('redirect refused')

def canonical(x):
    return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def unique(pairs):
    result={}
    for k,v in pairs:
        if k in result:raise ValueError('duplicate response field')
        result[k]=v
    return result

def reject_constant(value):raise ValueError('nonfinite JSON')

def decode(raw):
    if not isinstance(raw,bytes) or not 1<=len(raw)<=MAX_BYTES:raise ValueError('response size')
    return json.loads(raw,object_pairs_hook=unique,parse_constant=reject_constant)

def validate(name,args):
    if name not in SPECS or not isinstance(args,dict):raise ValueError('unknown capability')
    if name in SYMBOLS:
        if set(args)!={'symbol'} or not isinstance(args['symbol'],str) or args['symbol'] not in SYMBOLS[name]:raise ValueError('unsupported spot symbol')
    else:
        if set(args)!={'query','limit'} or not isinstance(args['query'],str) or not 1<=len(args['query'])<=160 or not args['query'].strip() or any(ord(c)<32 or ord(c)==127 for c in args['query']) or type(args['limit']) is not int or not 1<=args['limit']<=20:
            raise ValueError('public query bounds')

def list_tools():
    result=[]
    for name,(provider,url,ttl,daily,gap) in SPECS.items():
        props={'symbol':{'type':'string','enum':list(SYMBOLS[name])}} if name in SYMBOLS else {'query':{'type':'string','minLength':1,'maxLength':160},'limit':{'type':'integer','minimum':1,'maximum':20}}
        result.append({'name':name,'provider':provider,'input_schema':{'type':'object','properties':props,'required':list(props),'additionalProperties':False},'read_only':True,'execution_authorized':False,'cache_seconds':ttl,'daily_request_budget':daily})
    return result

def request_url(name,args):
    validate(name,args);base=SPECS[name][1]
    if name=='coinbase.spot':return base+'/'+args['symbol']+'/spot'
    if name=='bybit.spot':params={'category':'spot','symbol':args['symbol']}
    elif name=='github.search':params={'q':args['query'],'per_page':args['limit']}
    elif name=='crossref.search':params={'query':args['query'],'rows':args['limit'],'select':'DOI,title'}
    else:params={'search':args['query'],'limit':args['limit']}
    return base+'?'+urllib.parse.urlencode(params)

def fetch(url):
    opener=urllib.request.build_opener(NoRedirect())
    request=urllib.request.Request(url,headers={'User-Agent':'UMBRA-research-capability/1.0','Accept':'application/json'},method='GET')
    with opener.open(request,timeout=12) as response:
        if response.status!=200 or response.headers.get_content_type()!='application/json':raise ValueError('unexpected HTTP response')
        if response.headers.get('Content-Encoding','identity').lower()!='identity':raise ValueError('unsupported response encoding')
        raw=response.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES:raise ValueError('response exceeds budget')
    return raw

def text(value,limit):
    if not isinstance(value,str) or not 1<=len(value)<=limit or any(ord(c)<32 for c in value):raise ValueError('invalid metadata')
    return value

def price(value):
    if not isinstance(value,str) or not re.fullmatch(r'[0-9]{1,20}(?:\.[0-9]{1,24})?',value):raise ValueError('price format')
    try:d=Decimal(value)
    except InvalidOperation:raise ValueError('invalid decimal')
    if not d.is_finite() or d<=0:raise ValueError('invalid price')
    return value

def normalize(name,args,data):
    validate(name,args)
    if name=='coinbase.spot':
        base,quote=args['symbol'].split('-')
        row=data.get('data') if isinstance(data,dict) else None
        if not isinstance(row,dict) or row.get('base')!=base or row.get('currency')!=quote:raise ValueError('quote identity mismatch')
        return {'symbol':args['symbol'],'price':price(row.get('amount')),'quote_currency':quote}
    if name=='bybit.spot':
        if not isinstance(data,dict) or type(data.get('retCode')) is not int or data['retCode']!=0 or not isinstance(data.get('result'),dict):raise ValueError('provider error')
        result=data['result'];rows=result.get('list');ms=data.get('time')
        if result.get('category')!='spot' or not isinstance(rows,list) or len(rows)!=1 or not isinstance(rows[0],dict) or rows[0].get('symbol')!=args['symbol'] or type(ms) is not int or not 0<=ms<=2**63-1:raise ValueError('quote identity mismatch')
        return {'symbol':args['symbol'],'price':price(rows[0].get('lastPrice')),'quote_currency':'USDT','source_time_ms':ms}
    if name=='github.search':
        rows=data.get('items') if isinstance(data,dict) else None
    elif name=='crossref.search':
        rows=data.get('message',{}).get('items') if isinstance(data,dict) and isinstance(data.get('message'),dict) else None
    else:rows=data
    if not isinstance(rows,list) or len(rows)>args['limit']:raise ValueError('invalid discovery response')
    out=[]
    for row in rows:
        if not isinstance(row,dict):raise ValueError('invalid metadata row')
        if name=='github.search':
            if row.get('private') is not False:continue
            ident=text(row.get('full_name'),200)
            if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',ident):raise ValueError('repository identity')
            lic=row.get('license')
            out.append({'id':ident,'url':'https://github.com/'+ident,'license':text(lic['spdx_id'],80) if isinstance(lic,dict) and lic.get('spdx_id') else None})
        elif name=='crossref.search':
            titles=row.get('title')
            if not isinstance(titles,list) or not titles or not isinstance(titles[0],str):continue
            doi=text(row.get('DOI'),300)
            out.append({'doi':doi,'title':text(titles[0].replace('\n',' ').replace('\r',' ')[:500],500)})
        else:
            if row.get('private') is True:continue
            ident=text(row.get('id'),200)
            rev=row.get('sha')
            if rev is not None and (not isinstance(rev,str) or not re.fullmatch('[0-9a-f]{40}',rev)):raise ValueError('invalid revision')
            tags=row.get('tags',[])
            licenses=[s[8:] for s in tags if isinstance(s,str) and s.startswith('license:')] if isinstance(tags,list) else []
            out.append({'id':ident,'revision':rev,'license':text(licenses[0],100) if len(licenses)==1 else None})
    return out

def safe_path(p):
    if p.exists() or p.is_symlink():
        s=p.lstat()
        if p.is_symlink() or getattr(s,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',1024):raise ValueError('unsafe path')

class Fabric:
    def __init__(self,root,transport=fetch,clock=lambda:int(time.time())):
        root=Path(root);safe_path(root)
        if not root.is_dir():raise ValueError('existing data directory required')
        self.path=root/'capability-v86.sqlite3';safe_path(self.path)
        self.transport=transport;self.clock=clock
        with self.connect() as c:
            c.execute('CREATE TABLE IF NOT EXISTS cache(k TEXT PRIMARY KEY, observed INTEGER NOT NULL, expires INTEGER NOT NULL, payload BLOB NOT NULL, payload_sha TEXT NOT NULL)')
            c.execute('CREATE TABLE IF NOT EXISTS budget(provider TEXT PRIMARY KEY, day INTEGER NOT NULL, count INTEGER NOT NULL, last INTEGER NOT NULL)')
    @contextmanager
    def connect(self):
        safe_path(self.path)
        c=sqlite3.connect(self.path,timeout=5)
        try:
            with c:yield c
        finally:c.close()
    def now(self):
        v=self.clock()
        if type(v) is not int or not 0<=v<=2**63-86401:raise ValueError('invalid clock')
        return v
    def invoke(self,name,args):
        url=request_url(name,args);provider,_,ttl,limit,gap=SPECS[name]
        key=hashlib.sha256(canonical([name,args])).hexdigest()
        now=self.now()
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            cached=c.execute('SELECT observed,expires,payload,payload_sha FROM cache WHERE k=?',(key,)).fetchone()
            if cached and cached[0]<=now<cached[1]:
                observed,expires,payload,digest=cached
                if hashlib.sha256(payload).hexdigest()!=digest:raise ValueError('cache corruption')
                record=decode(payload)
                if record.get('tool')!=name or record.get('observed_at')!=observed:raise ValueError('cache identity mismatch')
                return {**record,'cache_hit':True}
            last=c.execute('SELECT day,count,last FROM budget WHERE provider=?',(provider,)).fetchone()
            day=now//86400
            count=last[1] if last and last[0]==day else 0
            if last and (now<last[2] or now-last[2]<gap) or count>=limit:raise BudgetError('provider request budget')
            c.execute('INSERT OR REPLACE INTO budget VALUES(?,?,?,?)',(provider,day,count+1,now))
        raw=self.transport(url)
        decoded=decode(raw)
        payload=normalize(name,args,decoded)
        observed=self.now()
        if observed<now:raise ValueError('clock moved backward')
        record={'tool':name,'provider':provider,'observed_at':observed,'response_sha256':hashlib.sha256(raw).hexdigest(),'data':payload,'production_authority':False,'execution_authorized':False}
        encoded=canonical(record)
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            c.execute('DELETE FROM cache WHERE expires<=?',(observed,))
            c.execute('INSERT OR REPLACE INTO cache VALUES(?,?,?,?,?)',(key,observed,observed+ttl,encoded,hashlib.sha256(encoded).hexdigest()))
            c.execute('DELETE FROM cache WHERE k IN (SELECT k FROM cache ORDER BY observed DESC,k LIMIT -1 OFFSET 2000)')
        return {**record,'cache_hit':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--list',action='store_true');p.add_argument('--root');p.add_argument('--tool',choices=SPECS);p.add_argument('--args');p.add_argument('--authorize-public-read',action='store_true');a=p.parse_args()
    if a.list:
        print(json.dumps(list_tools(),sort_keys=True));return
    if not a.authorize_public_read or not a.root or not a.tool or not a.args:raise PermissionError('explicit public read authorization required')
    result=Fabric(Path(a.root)).invoke(a.tool,json.loads(a.args,object_pairs_hook=unique))
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
