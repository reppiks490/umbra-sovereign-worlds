"""Native loopback Ollama adapter for v26; research-only, no training or promotion."""
from __future__ import annotations
import argparse, functools, hashlib, http.client, json, os, re, time, uuid
from pathlib import Path

MAX_BYTES=65536

def _json_request(port, method, route, body, timeout):
    if (method,route) not in {('GET','/api/tags'),('POST','/api/chat')}:
        raise ValueError('Unsupported loopback route')
    conn=http.client.HTTPConnection('127.0.0.1',port,timeout=timeout)
    try:
        data=None if body is None else json.dumps(body,allow_nan=False).encode()
        conn.request(method,route,body=data,headers={'Content-Type':'application/json'})
        res=conn.getresponse()
        if res.status!=200:raise ValueError('Native endpoint HTTP error')
        raw=res.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:raise ValueError('Native response too large')
        result=json.loads(raw)
        if not isinstance(result,dict):raise ValueError('Native response is not an object')
        return result,raw
    finally:conn.close()

def _pin(port,model,digest,timeout):
    tags,_=_json_request(port,'GET','/api/tags',None,timeout)
    entries=tags.get('models')
    if not isinstance(entries,list):raise ValueError('Invalid model registry')
    matches=[x for x in entries if isinstance(x,dict) and x.get('name')==model]
    if len(matches)!=1 or matches[0].get('digest')!=digest:
        raise ValueError('Local model tag digest mismatch')

def native_request(port,model,prompt,token,max_tokens,timeout,*,digest):
    if type(port) is not int or not 1<=port<=65535:raise ValueError('Invalid port')
    if not isinstance(model,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}',model):raise ValueError('Invalid model')
    if not isinstance(digest,str) or not re.fullmatch('[a-f0-9]{64}',digest):raise ValueError('Invalid digest')
    if not isinstance(prompt,str) or not 1<=len(prompt)<=512:raise ValueError('Invalid prompt')
    if type(max_tokens) is not int or not 1<=max_tokens<=64:raise ValueError('Invalid token cap')
    if type(timeout) not in (int,float) or not 0<timeout<=30:raise ValueError('Invalid timeout')
    end=time.monotonic()+timeout
    def left():
        remaining=end-time.monotonic()
        if remaining<=0:raise TimeoutError('Native request deadline exceeded')
        return remaining
    _pin(port,model,digest,left())
    body={'model':model,'messages':[{'role':'system','content':'Return only the integer. No explanation.'},{'role':'user','content':prompt}], 'format':{'type':'integer'},'think':False,'stream':False,'keep_alive':0,'options':{'num_predict':max_tokens,'num_ctx':1024,'num_thread':2,'temperature':0}}
    reply,raw=_json_request(port,'POST','/api/chat',body,left())
    if reply.get('model')!=model or reply.get('done') is not True or reply.get('done_reason')!='stop':raise ValueError('Incomplete or mismatched generation')
    used=reply.get('eval_count')
    if type(used) is not int or not 0<=used<=max_tokens:raise ValueError('Reported completion cap violation')
    msg=reply.get('message')
    content=msg.get('content') if isinstance(msg,dict) else None
    if not isinstance(content,str) or len(content)>128 or not re.fullmatch(r'-?(?:0|[1-9][0-9]*)',content.strip()):raise ValueError('Expected one JSON integer')
    _pin(port,model,digest,left())
    left()
    return content,used,hashlib.sha256(raw).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',required=True);p.add_argument('--private-out',required=True)
    p.add_argument('--model',required=True);p.add_argument('--digest',required=True)
    p.add_argument('--port',type=int,default=11434);p.add_argument('--max-jobs',type=int,default=4)
    p.add_argument('--authorize-local-model',action='store_true');a=p.parse_args()
    if not a.authorize_local_model:raise PermissionError('Explicit local authorization required')
    if not 1<=a.port<=65535 or not re.fullmatch('[a-f0-9]{64}',a.digest):raise ValueError('Invalid endpoint pin')
    import evolution_model_queue_v26 as queue
    import evolution_local_model_v22 as base
    import evolution_model_evidence_v24 as evidence
    key=evidence.secret()
    _pin(a.port,a.model,a.digest,10)
    original=base.request
    try:
        base.request=functools.partial(native_request,digest=a.digest)
        result=queue.process(a.db,a.private_out,model=a.model,port=a.port,max_jobs=a.max_jobs,count=1,max_tokens=32,budget=32,timeout=30,deadline_seconds=60,authorize=True)
    finally:base.request=original
    report={'schema':'myriad.native_ollama_pilot.v33','model':a.model,'observed_local_tag_digest':a.digest,'model_origin_authenticated':False,'raw_native_response_hashes_in_private_receipts':True,'training_steps':0,'production_authority':False,'auto_promote':False,'queue_result':result}
    report['hmac_sha256']=evidence.sign(report,key)
    path=Path(a.private_out)/('native-batch-'+uuid.uuid4().hex+'.json')
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:
        f.write(evidence.canonical(report)+b'\n');f.flush();os.fsync(f.fileno())
    print(json.dumps(report,sort_keys=True))
    if result['quarantined_or_failed']:raise SystemExit(2)

if __name__=='__main__':main()
