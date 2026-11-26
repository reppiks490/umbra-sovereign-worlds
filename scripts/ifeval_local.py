"""Pinned IFEval strict local subset, not an official IFEval score or training set."""
import argparse,hashlib,json,re,time
from pathlib import Path

REVISION='966cd89545d6b6acfd7638bc708b98261ca58e84'
BLOB='7c875005c09550bc3fd94c7f42867f78490bc554'
SUPPORTED={'punctuation:no_comma','change_case:english_lowercase','change_case:english_capital','startend:quotation','detectable_format:json_format','detectable_format:title'}
# Reviewed benign original prompts, fixed before inference. Other benchmark prompts
# remain unevaluated by this bounded research pilot.
KEYS=(1001,1075,1087,1187,1322,1593,1645,1667)
MODELS=('qwen3:0.6b','granite4:350m','gemma3:1b')

def check(instruction,kwargs,response):
    if instruction not in SUPPORTED or kwargs!={}:
        return None
    if not isinstance(response,str) or not response.strip() or len(response)>30000:
        return False
    s=response.strip()
    if instruction=='punctuation:no_comma':
        return ',' not in s
    if instruction=='change_case:english_lowercase':
        return bool(re.search('[a-z]',s)) and s.islower()
    if instruction=='change_case:english_capital':
        return bool(re.search('[A-Z]',s)) and s.isupper()
    if instruction=='startend:quotation':
        return len(s)>2 and s.startswith('"') and s.endswith('"')
    if instruction=='detectable_format:title':
        return any(x.strip() for x in re.findall(r'<<([^<>\n]+)>>',s))
    if instruction=='detectable_format:json_format':
        try:
            def invalid(x):
                raise ValueError('nonfinite JSON')
            def unique(items):
                d={}
                for k,v in items:
                    if k in d:raise ValueError('duplicate key')
                    d[k]=v
                return d
            value=json.loads(s,parse_constant=invalid,object_pairs_hook=unique)
            return isinstance(value,(dict,list))
        except (ValueError,RecursionError):
            return False
    return None

def score(row,response):
    ids=row.get('instruction_id_list')
    kw=row.get('kwargs')
    if not isinstance(ids,list) or not isinstance(kw,list) or not ids or len(ids)!=len(kw) or len(ids)>20:
        raise ValueError('instruction coverage')
    details=[{'instruction':i,'passed':check(i,k,response)} for i,k in zip(ids,kw)]
    supported=all(d['passed'] is not None for d in details)
    return {'status':'scored' if supported else 'unsupported',
            'passed':supported and all(d['passed'] for d in details),
            'constraints':details}

def load(root):
    p=root/'intelligence-resources'/'benchmarks'/('google--IFEval--'+REVISION[:12])/'ifeval_input_data.jsonl'
    meta=json.loads(p.with_name(p.name+'.receipt.json').read_text(encoding='utf8'))
    expected={'repo':'google/IFEval','revision':REVISION,'path':p.name,'size':207111,'sha':BLOB,'algorithm':'sha1','split':'evaluation','license':'apache-2.0','kind':'dataset'}
    if any(meta.get(k)!=v for k,v in expected.items()) or p.is_symlink() or p.stat().st_size!=expected['size']:
        raise ValueError('publisher receipt mismatch')
    raw=p.read_bytes()
    if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=BLOB:
        raise ValueError('publisher blob mismatch')
    rows={}
    for line in raw.decode('utf8').splitlines():
        if not line.strip():continue
        r=json.loads(line)
        if type(r.get('key')) is not int or r['key'] in rows or not isinstance(r.get('prompt'),str) or not 1<=len(r['prompt'])<=16000:
            raise ValueError('benchmark record identity')
        rows[r['key']]=r
    if len(rows)!=541 or any(k not in rows for k in KEYS):
        raise ValueError('benchmark coverage')
    return rows

def run(root,model=MODELS[0],offset=0,count=2):
    from source_assist import local_api
    from student_council import roster
    from native_lora_train import available_ram,atomic
    from hf_weight_cache import lock
    if model not in MODELS or not 1<=count<=2 or not 0<=offset<=len(KEYS)-count:
        raise ValueError('bounded reviewed evaluation window')
    rows=load(root)
    selected=[rows[k] for k in KEYS[offset:offset+count]]
    if any(score(r,'probe')['status']=='unsupported' for r in selected):
        raise ValueError('unsupported reviewed case')
    bank=root/'experience'/'ifeval-local'
    bank.mkdir(parents=True,exist_ok=True)
    with lock(root/'experience'/'model-compute.lock'),lock(bank/'research.lock'):
        if local_api('ps').get('models'):
            return {'status':'deferred_busy','production_authority':False}
        s=next((r for r in roster(root) if r['name']==model and r['present'] and r['backend']=='ollama'),None)
        if not s or available_ram()<s['required_ram']:
            return {'status':'deferred_admission','production_authority':False}
        manifest={'revision':REVISION,'blob':BLOB,'model':model,'digest':s['digest'],'keys':[r['key'] for r in selected],'protocol':'strict-local-reviewed-v1'}
        key=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
        path=bank/('trial-'+key+'.json')
        if path.exists():
            return {'status':'already_recorded','manifest_sha256':key,'production_authority':False}
        records=[]
        for r in selected:
            start=time.monotonic()
            try:
                if local_api('ps').get('models'):raise ValueError('model runtime busy')
                request={'model':model,'prompt':r['prompt'],'stream':False,'keep_alive':0,'options':{'temperature':0,'num_ctx':2048,'num_predict':320,'num_thread':2}}
                if model.startswith('qwen3:'):request['think']=False
                response=local_api('generate',request,180)
                tags=local_api('tags')['models']
                verified=any(x.get('name')==model and x.get('digest')==s['digest'] for x in tags)
                if response.get('model')!=model or response.get('done') is not True or not verified:
                    raise ValueError('response identity')
                answer=response.get('response','')
                result=score(r,answer)
                record={'key':r['key'],'status':'evaluated','score':result,'response_sha256':hashlib.sha256(answer.encode()).hexdigest(),'eval_count':response.get('eval_count')}
            except Exception as exc:
                record={'key':r['key'],'status':'failed','reason':type(exc).__name__}
            record['seconds']=time.monotonic()-start
            records.append(record)
            print(json.dumps({'progress':len(records),'total':count,'status':record['status']}),flush=True)
        completed=sum(r['status']=='evaluated' for r in records)
        report={'status':'completed' if completed==count else 'partial','manifest':manifest,'manifest_sha256':key,
                'cases':count,'completed_calls':completed,'model_calls':count,
                'passed_cases':sum(r.get('score',{}).get('passed') is True for r in records),
                'constraint_passes':sum(x['passed'] is True for r in records for x in r.get('score',{}).get('constraints',[])),
                'records':records,'dataset_cases':len(rows),'reviewed_subset_cases':len(KEYS),
                'scope':'strict local formatting checks only; not official IFEval, content quality or novelty evidence',
                'weight_training':False,'production_authority':False}
        atomic(path,report)
        return {k:v for k,v in report.items() if k!='records'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--model',choices=MODELS,default=MODELS[0]);p.add_argument('--offset',type=int,default=0);p.add_argument('--count',type=int,default=2);a=p.parse_args();print(json.dumps(run(a.root,a.model,a.offset,a.count)))
