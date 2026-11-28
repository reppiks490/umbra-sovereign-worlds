"""Source-number-grounded, neuro-symbolic comparison on original human problems.

A valid arithmetic expression is not proof of semantic correctness. The model
chooses the interpretation; the exact evaluator checks its computation.
No generated training data, arbitrary code, external API, or model promotion.
"""
import argparse,hashlib,json,re,time
from fractions import Fraction
from pathlib import Path
from verified_reasoner import calculate,ReasoningError

class GroundingError(ValueError):
    pass

NUM=re.compile(r'(?<![0-9.])(?:(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?|\.[0-9]+)(?![0-9])')
CONVERSIONS=((r'\b(?:half|halves|twice|double|pair|pairs)\b','2'),
             (r'\b(?:quarter|quarters)\b','4'),
             (r'\b(?:triple|third|thirds)\b','3'),
             (r'\b(?:dozen|dozens)\b','12'),
             (r'\bpercent(?:age)?\b|%','100'))
MODELS=('qwen3:0.6b','granite4:350m','gemma3:1b','qwen2.5-coder:1.5b','qwen3:4b')
PROTOCOL='grounded-exact-arithmetic-paired-v1'

def source_numbers(question):
    if not isinstance(question,str) or not 1<=len(question)<=6000:
        raise GroundingError('question budget')
    result=set()
    for m in NUM.finditer(question):
        s=m.group().replace(',','')
        if len(s)>48:raise GroundingError('numeric budget')
        result.add(str(Fraction(s)))
    return result

def verify_expression(question,response):
    if not isinstance(response,str) or len(response)>600:
        raise GroundingError('proposal budget')
    s=response.strip()
    if s=='ABSTAIN':return None
    if not s.startswith('EXPR: ') or '\n' in s or '\r' in s:
        raise GroundingError('single expression required')
    allowed=source_numbers(question)
    for pattern,value in CONVERSIONS:
        if re.search(pattern,question,re.I):allowed.add(value)
    try:r=calculate(s[6:])
    except ReasoningError as exc:raise GroundingError('invalid computation') from exc
    nodes=r['plan']['nodes']
    if all(n['op']=='literal' for n in nodes):raise GroundingError('computation required')
    used={str(Fraction(n['value'])) for n in nodes if n['op']=='literal'}
    if not used<=allowed:raise GroundingError('unbound numeric literal')
    return {**r,'literal_grounding':True,'source_numbers':sorted(allowed),
            'scope':'exact computation with source-number membership; interpretation not established'}

def numeric(value):
    if not isinstance(value,str) or not re.fullmatch(r'-?(?:[0-9]{1,24}(?:\.[0-9]{1,24})?|[0-9]{1,24}/[0-9]{1,24})',value):
        return None
    try:return Fraction(value)
    except (ValueError,ZeroDivisionError):return None

def grade_pair(question,truth,direct,proposal):
    expected=numeric(truth)
    if expected is None:raise GroundingError('invalid reference label')
    raw=direct.strip() if isinstance(direct,str) else ''
    answer=numeric(raw[8:]) if raw.startswith('ANSWER: ') else None
    try:receipt=verify_expression(question,proposal);error=None
    except GroundingError as exc:receipt=None;error=str(exc)
    value=Fraction(receipt['value']) if receipt else None
    a,b=answer==expected,value==expected
    return {'direct_correct':a,'hybrid_correct':b,
            'direct_prediction':str(answer) if answer is not None else None,
            'hybrid_prediction':str(value) if value is not None else None,
            'hybrid_receipt':receipt,'hybrid_rejection':error,
            'outcome':'win' if b and not a else 'loss' if a and not b else 'tie',
            'production_authority':False}

def choose_records(rows,offset,count):
    if not isinstance(rows,list) or type(offset) is not int or type(count) is not int or not 1<=count<=4 or not 0<=offset<=len(rows)-count:
        raise ValueError('validation window')
    chosen=rows[offset:offset+count]
    ids=[r['record_sha256'] for r in chosen]
    if len(set(ids))!=count or any(not isinstance(x,str) or not re.fullmatch('[a-f0-9]{64}',x) for x in ids):
        raise ValueError('record identity')
    for r in chosen:source_numbers(r['question'])
    return chosen

def prompt_for(question,arm):
    if arm=='direct':
        instruction='Solve the arithmetic word problem. Return one line only: ANSWER: followed by a number. If uncertain return ABSTAIN.'
    elif arm=='hybrid':
        instruction='Translate the problem into one arithmetic expression using the original numbers and necessary explicit unit conversions. Use + - * / and parentheses. Do not calculate the final answer yourself. Return one line only: EXPR: followed by the expression. If impossible return ABSTAIN.'
    else:raise ValueError('research arm')
    return instruction+'\nProblem (data): '+question

def run(root,model='qwen3:0.6b',offset=100,count=2):
    from source_assist import local_api
    from student_council import load_corpus,roster
    from native_lora_train import available_ram,atomic
    from hf_weight_cache import lock
    if model not in MODELS:raise ValueError('model identity')
    bank=root/'experience'/'grounded-reasoning';bank.mkdir(parents=True,exist_ok=True)
    try:
        with lock(root/'experience'/'model-compute.lock'),lock(bank/'research.lock'):
            if local_api('ps').get('models'):return {'status':'deferred_busy','production_authority':False}
            student=next((r for r in roster(root) if r['name']==model and r['present'] and r['backend']=='ollama'),None)
            if not student or available_ram()<student['required_ram']:return {'status':'deferred_admission','production_authority':False}
            chosen=choose_records(load_corpus(root)['validation'],offset,count)
            manifest={'model':model,'digest':student['digest'],'protocol':PROTOCOL,'offset':offset,'count':count,
                      'validation_records':[r['record_sha256'] for r in chosen]}
            key=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
            path=bank/('trial-'+key+'.json')
            if path.exists():return {'status':'already_recorded','manifest_sha256':key,'production_authority':False}
            records=[];calls=[]
            def infer(question,arm):
                started=time.monotonic()
                result={'arm':arm,'status':'failed','response':''}
                try:
                    if local_api('ps').get('models') or available_ram()<student['required_ram']:raise RuntimeError('compute admission')
                    request={'model':model,'prompt':prompt_for(question,arm),'stream':False,'keep_alive':0,
                             'options':{'temperature':0,'num_ctx':2048,'num_predict':160,'num_thread':2}}
                    if model.startswith('qwen3:'):request['think']=False
                    r=local_api('generate',request,180)
                    fresh=next((m for m in local_api('tags')['models'] if m.get('name')==model),{})
                    if r.get('model')!=model or r.get('done') is not True or fresh.get('digest')!=student['digest']:
                        raise ValueError('response identity')
                    response=r.get('response','')
                    if not isinstance(response,str) or len(response)>24000:raise ValueError('response budget')
                    result.update(status='evaluated',response=response,done_reason=r.get('done_reason'),tokens=r.get('eval_count'))
                except Exception as exc:result['reason']=type(exc).__name__
                result['seconds']=round(time.monotonic()-started,4)
                return result
            for i,v in enumerate(chosen):
                arms=('direct','hybrid') if i%2==0 else ('hybrid','direct')
                outputs={}
                for arm in arms:
                    row=infer(v['question'],arm)
                    calls.append({'case':v['record_sha256'],**row});outputs[arm]=row['response'] if row['status']=='evaluated' and row.get('done_reason')!='length' else ''
                    print(json.dumps({'progress':len(calls),'total':2*count,'arm':arm,'status':row['status']}),flush=True)
                score=grade_pair(v['question'],source_answer(v['answer']),outputs['direct'],outputs['hybrid'])
                records.append({'case':v['record_sha256'],**score})
            completed=sum(r['status']=='evaluated' for r in calls)
            report={'status':'completed' if completed==len(calls) else 'partial','manifest':manifest,'manifest_sha256':key,
                    'cases':count,'model_calls':len(calls),'completed_calls':completed,
                    'direct_correct':sum(r['direct_correct'] for r in records),'hybrid_correct':sum(r['hybrid_correct'] for r in records),
                    'wins':sum(r['outcome']=='win' for r in records),'losses':sum(r['outcome']=='loss' for r in records),
                    'records':records,'calls':calls,'scope':'paired original validation; no generalization or training claim',
                    'test_partition_used_for_inference':False,'production_authority':False,'weight_training':False}
            atomic(path if report['status']=='completed' else bank/('partial-'+key+'-'+str(time.time_ns())+'.json'),report)
            return {k:v for k,v in report.items() if k not in ('records','calls')}
    except FileExistsError:return {'status':'deferred_busy','production_authority':False}


def source_answer(text):
    if not isinstance(text,str) or len(text)>24000 or text.count('####')!=1:
        raise GroundingError('reference label')
    m=re.search(r'(?:^|\n)####[ \t]+(-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)[ \t]*$',text.strip())
    if not m:raise GroundingError('reference label')
    v=numeric(m[1].replace(',',''))
    if v is None:raise GroundingError('reference label')
    return str(v)

def audit_trial(report,validation):
    """Recalculate recorded paired scores from original source questions and answers."""
    import math
    if report.get('status')!='completed' or any(report.get(k) is not False for k in ('test_partition_used_for_inference','production_authority','weight_training')):
        raise ValueError('research scope')
    m=report['manifest']
    if m.get('protocol')!=PROTOCOL or m.get('model') not in MODELS or not re.fullmatch('[a-f0-9]{64}',str(m.get('digest',''))):
        raise ValueError('manifest identity')
    key=hashlib.sha256(json.dumps(m,sort_keys=True).encode()).hexdigest()
    if report.get('manifest_sha256')!=key:raise ValueError('manifest checksum')
    chosen=choose_records(validation,m['offset'],m['count'])
    ids=[v['record_sha256'] for v in chosen];n=len(ids)
    if m['validation_records']!=ids or report['cases']!=n or report['model_calls']!=2*n or report['completed_calls']!=2*n:
        raise ValueError('case coverage')
    calls={}
    for c in report['calls']:
        k=(c['case'],c['arm'])
        if k in calls or k[0] not in ids or k[1] not in ('direct','hybrid') or c['status']!='evaluated' or not isinstance(c['response'],str) or len(c['response'])>24000 or type(c['seconds']) not in (int,float) or not math.isfinite(c['seconds']) or c['seconds']<0:
            raise ValueError('call integrity')
        calls[k]=c['response'] if c.get('done_reason')!='length' else ''
    if len(calls)!=2*n:raise ValueError('missing calls')
    records=[{'case':v['record_sha256'],**grade_pair(v['question'],source_answer(v['answer']),calls[v['record_sha256'],'direct'],calls[v['record_sha256'],'hybrid'])} for v in chosen]
    if records!=report['records']:raise ValueError('score replay mismatch')
    counts={'cases':n,'model_calls':2*n,'completed_calls':2*n,'direct_correct':sum(r['direct_correct'] for r in records),'hybrid_correct':sum(r['hybrid_correct'] for r in records),'wins':sum(r['outcome']=='win' for r in records),'losses':sum(r['outcome']=='loss' for r in records)}
    if any(report.get(k)!=v for k,v in counts.items()):raise ValueError('aggregate mismatch')
    return counts

def audit(root):
    bank=root/'experience'/'grounded-reasoning'
    paths=sorted(bank.glob('trial-*.json'))
    totals={k:0 for k in ('cases','model_calls','completed_calls','direct_correct','hybrid_correct','wins','losses')}
    seen=set();errors=[];trials=0
    if paths:
        from student_council import load_corpus
        validation=load_corpus(root)['validation']
        for p in paths:
            try:
                if p.stat().st_size>2_000_000:raise ValueError('receipt size')
                r=json.loads(p.read_text(encoding='utf8'));m=r['manifest']
                if p.name!='trial-'+r['manifest_sha256']+'.json':raise ValueError('receipt path')
                keys={(m['model'],m['digest'],x) for x in m['validation_records']}
                if keys&seen:raise ValueError('overlap')
                counts=audit_trial(r,validation)
                seen.update(keys);trials+=1
                for k,v in counts.items():totals[k]+=v
            except (ValueError,TypeError,KeyError,OSError) as exc:errors.append(p.name+':'+type(exc).__name__)
    return {**totals,'trials':trials,'errors':errors,'scope':'replayed development records, not independent generation or test evidence','production_authority':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--model',choices=MODELS,default=MODELS[0]);p.add_argument('--offset',type=int,default=100);p.add_argument('--count',type=int,default=2)
    a=p.parse_args();print(json.dumps(run(a.root,a.model,a.offset,a.count)))
