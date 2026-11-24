"""Bounded teacher supervision, real local retrieval, and independently checked student training."""
from __future__ import annotations
import argparse,ast,hashlib,hmac,http.client,json,math,os,random,re,shutil,time
from pathlib import Path
import evolution_fleet_scale_v36 as scale
import evolution_model_evidence_v24 as ev
import evolution_native_ollama_v33 as native
import evolution_research_orchestrator_v39 as orch
TEACHER='qwen3:8b'
TEACHER_DIGEST='500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41'
COMPRESSED='hf.co/bartowski/Qwen_Qwen3-8B-GGUF:IQ2_M'
APPROVED={TEACHER:6*1024**3,COMPRESSED:3300*1024**2,'qwen3:1.7b':2*1024**3,'granite4:350m':2*1024**3,'deepseek-r1:1.5b':2*1024**3,'all-minilm:22m':128*1024**2}
RULES=(('checkpoint admission',('hash verified','holdout passed','baseline beaten','no leakage')),('lease settlement',('owner matches','lease unexpired','unique occurrence','receipt verified')),('market replay',('real fills','costs modeled','latency modeled','chronological split')),('deployment admission',('tests passed','source pinned','authority granted','rollback available')))
FILES=('evolution_model_queue_v26.py','evolution_fleet_scale_v36.py','evolution_research_v37.py','evolution_live_research_v38.py','evolution_fresh_training_v35.py')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def admit_teacher(free_mb,free_virtual_mb,busy):
    return not busy and free_mb>=6200 and free_virtual_mb>=7500
def cases(seed,split):
    rng=random.Random(seed*1009+split*99991);out=[]
    for role,(name,flags) in enumerate(RULES):
        for i in range(3):
            values=[1]*4 if i==0 else [int(rng.random()>.45) for _ in range(4)]
            if i and all(values):values[rng.randrange(4)]=0
            features=[int(j==role) for j in range(4)]+values
            out.append({'id':f'{seed}-{split}-{role}-{i}','domain':name,'facts':dict(zip(flags,values)),'features':features,'label':int(all(values))})
    rng.shuffle(out);return out
def accept(rows,raw):
    from evolution_research_v37 import unique_pairs
    d=json.loads(raw,object_pairs_hook=unique_pairs)
    if not isinstance(d,list) or len(d)!=len(rows):raise ValueError('incomplete teacher batch')
    known={c['id']:c for c in rows};seen=set();out=[]
    for r in d:
        if not isinstance(r,dict) or set(r)!= {'id','label'} or r['id'] not in known or r['id'] in seen or type(r['label']) is not int or r['label'] not in (0,1):raise ValueError('invalid teacher row')
        seen.add(r['id']);c=known[r['id']]
        if r['label']==c['label']:out.append(c)
    return out
def request(route,body=None,timeout=25):
    if route not in ('/api/tags','/api/ps','/api/embed','/api/chat'):raise ValueError('invalid local route')
    conn=http.client.HTTPConnection('127.0.0.1',11434,timeout=timeout)
    try:
        conn.request('POST' if body is not None else 'GET',route,body=None if body is None else json.dumps(body,allow_nan=False),headers={'Content-Type':'application/json'})
        response=conn.getresponse();raw=response.read(4*1024**2+1)
        if response.status!=200 or len(raw)>4*1024**2:raise ValueError('local inference failed')
        d=json.loads(raw)
        if not isinstance(d,dict):raise ValueError('malformed local response')
        return d,raw
    finally:conn.close()
def tag(model):
    if model not in APPROVED:raise ValueError('unapproved model')
    tags,_=request('/api/tags')
    matches=[x for x in tags['models'] if x.get('name')==model]
    if len(matches)!=1:raise ValueError('model not available')
    t=matches[0];digest=t.get('digest');size=t.get('size')
    if not isinstance(digest,str) or not re.fullmatch('[a-f0-9]{64}',digest) or type(size) is not int or not 0<size<=APPROVED[model]:raise ValueError('invalid local model')
    if model==TEACHER and digest!=TEACHER_DIGEST:raise ValueError('8B teacher digest changed')
    return digest
def pin(private,model):
    path=private/'teacher-model-pins-v40.json';pins=json.loads(path.read_text()) if path.exists() else {}
    if not isinstance(pins,dict) or any(k not in APPROVED or not isinstance(v,str) or not re.fullmatch('[a-f0-9]{64}',v) for k,v in pins.items()):raise ValueError('invalid teacher registry')
    d=tag(model)
    if model in pins and pins[model]!=d:raise ValueError('changed model digest')
    pins[model]=d;orch.atomic(path,pins);return d
def save(private,prefix,record,key):
    record['hmac_sha256']=ev.sign(record,key);folder=private/'teacher-v40';folder.mkdir(exist_ok=True)
    if folder.is_symlink() or sum(x.stat().st_size for x in folder.iterdir() if x.is_file())>128*1024**2:raise ValueError('teacher evidence quota')
    p=folder/(prefix+'-'+str(time.time_ns())+'.json')
    with p.open('xb') as f:f.write(ev.canonical(record)+b'\n');f.flush();os.fsync(f.fileno())
    return record
def teacher(private,model,seed,key,free_virtual_mb):
    digest=pin(private,model);ram=scale.free_mb();busy=bool(request('/api/ps')[0].get('models'))
    if model==TEACHER and not admit_teacher(ram,free_virtual_mb,busy):
        return {'model':model,'status':'deferred_memory_or_residency','free_ram_mib':ram,'other_model_resident':busy,'teacher_calls':0}
    if model==COMPRESSED and (busy or ram<4700 or free_virtual_mb<7500):
        return {'model':model,'status':'deferred_memory_or_residency','free_ram_mib':ram,'other_model_resident':busy,'teacher_calls':0}
    if model not in (TEACHER,COMPRESSED) and ram<2200:return {'model':model,'status':'deferred_memory','teacher_calls':0}
    rows=cases(seed,0);public=[{k:c[k] for k in ('id','domain','facts')} for c in rows]
    prompt='For each case, label 1 only if all four required facts equal 1; otherwise 0. Return all ids and labels, no prose. '+json.dumps(public,separators=(',',':'))
    fmt={'type':'array','items':{'type':'object','properties':{'id':{'type':'string'},'label':{'type':'integer','enum':[0,1]}},'required':['id','label'],'additionalProperties':False},'minItems':len(rows),'maxItems':len(rows)}
    body={'model':model,'messages':[{'role':'user','content':prompt}],'format':fmt,'think':False,'stream':False,'keep_alive':0,'options':{'num_ctx':1536 if model==COMPRESSED else 2048,'num_predict':384,'num_thread':2,'temperature':0}}
    v,raw=request('/api/chat',body,150 if model in (TEACHER,COMPRESSED) else 70)
    if v.get('model')!=model or v.get('done') is not True or v.get('done_reason')!='stop':raise ValueError('incomplete teacher')
    txt=v.get('message',{}).get('content')
    if not isinstance(txt,str) or len(txt)>8192 or tag(model)!=digest:raise ValueError('teacher response or pin mismatch')
    accepted=accept(rows,txt)
    return save(private,'teacher',{'schema':'myriad.teacher.v40','model':model,'model_digest':digest,'seed':seed,'split':0,'response_sha256':sha(raw),'raw':txt,'cases':len(rows),'accepted':len(accepted),'rejected':len(rows)-len(accepted),'accepted_rows':accepted,'production_authority':False,'model_origin_authenticated':False},key)
def train(private,key):
    folder=private/'teacher-v40';data={};teachers=set();seen_seeds=set()
    for f in sorted(folder.glob('teacher-*.json'))[-256:] if folder.exists() else []:
        if f.is_symlink() or f.stat().st_size>128*1024:raise ValueError('invalid teacher receipt')
        v=json.loads(f.read_text());sig=v.pop('hmac_sha256',None)
        if not isinstance(sig,str) or not hmac.compare_digest(ev.sign(v,key),sig) or v.get('schema')!='myriad.teacher.v40' or v.get('production_authority') is not False:raise ValueError('teacher receipt authentication')
        rows=accept(cases(v['seed'],0),v['raw'])
        if rows!=v['accepted_rows']:raise ValueError('teacher labels changed')
        for row in rows:data[row['id']]=row
        if rows:teachers.add(v['model']);seen_seeds.add(v['seed'])
    if len(data)<24 or len({v['label'] for v in data.values()})!=2:return {'status':'insufficient_verified_labels','accepted_unique':len(data)}
    w=[0.0]*9
    def predict(x):
        z=max(-40,min(40,sum(a*b for a,b in zip(w,x+[1]))));return 1/(1+math.exp(-z))
    rows=list(data.values())
    for _ in range(160):
        for r in rows:
            x=r['features']+[1];err=predict(r['features'])-r['label']
            for j in range(9):w[j]-=.025*err*x[j]
    held=[r for seed in range(990001,990033) for r in cases(seed,1) if seed not in seen_seeds]
    correct=sum(int(predict(r['features'])>=.5)==r['label'] for r in held)
    baseline=sum(r['label']==0 for r in held)
    result={'schema':'myriad.teacher_student.v40','teacher_models':sorted(teachers),'accepted_unique':len(data),'gradient_updates':160*len(rows),'trainable_parameters':9,'heldout_cases':len(held),'heldout_correct':correct,'all_reject_baseline':baseline,'weights':w,'scope':'small synthetic binary admission classifier; not LLM fine tuning','production_authority':False,'auto_promote':False}
    return save(private,'student',result,key)
def documents(root):
    docs=[]
    for name in FILES:
        p=Path(root)/name
        if not p.exists():continue
        if p.is_symlink() or p.stat().st_size>256*1024:raise ValueError('invalid source')
        raw=p.read_bytes();src=raw.decode('utf-8-sig');lines=src.splitlines()
        for n in ast.parse(src).body:
            if isinstance(n,ast.FunctionDef):
                text='\n'.join(lines[n.lineno-1:min(n.end_lineno,n.lineno+10)])[:850]
                docs.append({'file':name,'function':n.name,'sha256':sha(raw),'text':text})
    return docs[:96]
def cosine(a,b):
    if not a or len(a)!=len(b) or not all(math.isfinite(x) for x in a+b):raise ValueError('invalid vectors')
    den=math.sqrt(sum(x*x for x in a)*sum(x*x for x in b))
    if not den:raise ValueError('zero vector')
    return sum(x*y for x,y in zip(a,b))/den
def retrieve(private,key):
    model='all-minilm:22m';digest=pin(private,model)
    if scale.free_mb()<1500:return {'status':'deferred_memory'}
    docs=documents(Path(__file__).resolve().parent)
    if not docs:raise ValueError('no source corpus')
    query='fenced worker lease ownership and expiration, duplicate settlement'
    inputs=[query]+[d['file']+' '+d['function']+' '+d['text'] for d in docs]
    embeddings=[]
    for i in range(0,len(inputs),16):
        v,_=request('/api/embed',{'model':model,'input':inputs[i:i+16],'truncate':True,'keep_alive':0},45)
        if v.get('model')!=model or not isinstance(v.get('embeddings'),list) or len(v['embeddings'])!=len(inputs[i:i+16]):raise ValueError('embedding coverage')
        embeddings.extend(v['embeddings'])
    if tag(model)!=digest:raise ValueError('embedding model changed')
    ranked=sorted([(cosine(embeddings[0],v),i) for i,v in enumerate(embeddings[1:])],reverse=True)[:5]
    result={'schema':'myriad.retrieval.v40','model':model,'model_digest':digest,'documents':len(docs),'embedding_dimensions':len(embeddings[0]),'query':query,'top':[{'file':docs[i]['file'],'function':docs[i]['function'],'source_sha256':docs[i]['sha256'],'similarity':score} for score,i in ranked],'production_authority':False,'retrieval_quality_certified':False}
    return save(private,'retrieval',result,key)
def main():
    p=argparse.ArgumentParser();p.add_argument('--private',required=True);p.add_argument('--authorize',action='store_true');s=p.add_subparsers(dest='cmd',required=True)
    t=s.add_parser('teach');t.add_argument('--model',required=True,choices=[TEACHER,COMPRESSED,'qwen3:1.7b','granite4:350m','deepseek-r1:1.5b']);t.add_argument('--seed',type=int,required=True);t.add_argument('--free-virtual-mib',type=int,default=0)
    s.add_parser('retrieve');s.add_parser('train');a=p.parse_args();root=Path(a.private)
    if not a.authorize or root.is_symlink() or not root.is_dir() or shutil.disk_usage(root).free<5*1024**3:raise PermissionError('private authorized research only')
    key=ev.secret()
    if a.cmd=='teach':r=teacher(root,a.model,a.seed,key,a.free_virtual_mib)
    elif a.cmd=='retrieve':r=retrieve(root,key)
    else:r=train(root,key)
    print(json.dumps({k:v for k,v in r.items() if k not in ('raw','accepted_rows','weights')},sort_keys=True))
if __name__=='__main__':main()
