"""Paired, evidence-bound council qualification; no weight updates or promotion."""
import argparse, collections, hashlib, json, math, re, time
from pathlib import Path
from decimal import Decimal, InvalidOperation

def canonical(value):
    if not isinstance(value,str) or len(value)>80 or not re.fullmatch(r'-?\d+(?:\.\d+)?',value):
        return None
    try:
        n=Decimal(value)
        if not n.is_finite() or n.copy_abs()>Decimal('1e24'):
            return None
        if not n:return '0'
        exact=format(n,'f')
        return exact.rstrip('0').rstrip('.') if '.' in exact else exact
    except InvalidOperation:
        return None

def evaluate(cases, models, rows):
    """Evaluate complete case/model pairs; missing answers count against accuracy."""
    if not cases or len(models)<3 or len(set(models.values()))!=len(models):
        raise ValueError('independent weight identities required')
    if any(not isinstance(d,str) or not re.fullmatch('[a-f0-9]{64}',d) for d in models.values()):
        raise ValueError('invalid weight digest')
    truths={k:canonical(v) for k,v in cases.items()}
    if None in truths.values():
        raise ValueError('invalid truth')
    expected={(c,m) for c in cases for m in models}
    results={}
    seconds=0.
    for row in rows:
        k=(row['case'],row['model'])
        if k not in expected or k in results or row['digest']!=models[k[1]]:
            raise ValueError('paired identity or duplication')
        duration=row['seconds']
        if type(duration) not in (int,float) or not math.isfinite(duration) or duration<0:
            raise ValueError('invalid inference duration')
        seconds+=duration
        results[k]=canonical(row.get('prediction')) if row['status']=='evaluated' else None
    if set(results)!=expected:
        raise ValueError('incomplete paired evidence')
    def metrics(predictions):
        n=len(truths)
        answered=sum(v is not None for v in predictions.values())
        correct=sum(v==truths[k] for k,v in predictions.items())
        return {'cases':n,'answered':answered,'correct':correct,'accuracy':correct/n,
                'answered_accuracy':correct/answered if answered else None}
    individuals={m:{c:results[c,m] for c in cases} for m in models}
    collective={}
    disagreements=0
    for c in cases:
        votes=collections.Counter(v for m in models if (v:=results[c,m]) is not None)
        disagreements+=len(votes)>1
        winner,count=votes.most_common(1)[0] if votes else (None,0)
        collective[c]=winner if count>len(models)//2 else None
    paired={}
    for m,predictions in individuals.items():
        wins=losses=0
        for c in cases:
            a=collective[c]==truths[c]
            b=predictions[c]==truths[c]
            wins+=a and not b
            losses+=b and not a
        paired[m]={'wins':wins,'losses':losses,'ties':len(cases)-wins-losses}
    return {'ensemble':metrics(collective),'baselines':{m:metrics(p) for m,p in individuals.items()},
            'paired':paired,'disagreement_cases':disagreements,'inference_seconds':seconds,
            'weight_training':False,'production_authority':False,
            'promotion':'not_authorized','scope':'strict majority of all enrolled distinct weight identities'}

DEFAULT_MODELS=('granite4:350m','qwen3:0.6b','gemma3:1b')

def run(root, count=2, offset=None):
    """Fixed panel, bounded validation-only run using existing admission and inference locks."""
    from student_council import roster, load_corpus, lesson, ollama_lesson, answer_value
    from source_assist import local_api
    from native_lora_train import available_ram, atomic
    from hf_weight_cache import lock
    from council_ledger import record, entries, next_offset, summarize
    if not 1<=count<=8 or (offset is not None and (offset<0 or offset+count>715)):
        raise ValueError('bounded validation window')
    bank=root/'experience'/'council-qualification'
    bank.mkdir(parents=True,exist_ok=True)
    with lock(root/'experience'/'model-compute.lock'),lock(bank/'qualification.lock'):
        if local_api('ps').get('models'):
            return {'status':'deferred_busy','production_authority':False}
        available={r['name']:r for r in roster(root) if r['present'] and r['backend']=='ollama'}
        if any(m not in available or available[m]['required_ram']>available_ram() for m in DEFAULT_MODELS):
            return {'status':'deferred_memory_or_model','production_authority':False}
        models={m:available[m]['digest'] for m in DEFAULT_MODELS}
        latest=bank/'latest.json'
        if latest.is_file():
            record(bank,json.loads(latest.read_text(encoding='utf8')))
        prior=entries(bank)
        if any(r['manifest']['models']!=models for r in prior):
            return {'status':'deferred_changed_panel','production_authority':False}
        if offset is None:
            offset=next_offset(bank,models,count)
            if offset is None:
                return {'status':'validation_window_exhausted','production_authority':False}
        used={i for r in prior for i in range(r['manifest']['offset'],r['manifest']['offset']+r['manifest']['count'])}
        if used.intersection(range(offset,offset+count)):
            raise ValueError('validation window already evaluated')
        corpus=load_corpus(root)
        chosen=[lesson(corpus,i) for i in range(offset,offset+count)]
        truths={v['record_sha256']:answer_value(v['answer']) for _,v in chosen}
        if len(truths)!=count:
            raise ValueError('duplicate validation records')
        rows=[]
        for t,v in chosen:
            for name,digest in models.items():
                start=time.monotonic()
                try:
                    result=ollama_lesson(name,digest,t,v)
                except Exception as e:
                    result={'status':'failed','reason':type(e).__name__}
                row={'case':v['record_sha256'],'model':name,'digest':digest,
                     'prediction':result.get('predicted_numeric'),'status':result.get('status','failed'),
                     'seconds':round(time.monotonic()-start,4)}
                rows.append(row)
                print(json.dumps({'progress':len(rows),'total':count*len(models),'model':name,'status':row['status']}),flush=True)
        report=evaluate(truths,models,rows)
        manifest={'models':models,'validation_records':list(truths),'offset':offset,'count':count,
                  'protocol':'fixed-one-human-example-strict-majority-v1'}
        report.update(status='completed',manifest=manifest,
                      manifest_sha256=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest(),
                      model_calls=len(rows),completed_calls=sum(r['status']=='evaluated' for r in rows),
                      data_scope='original GSM8K development validation only; public pretraining overlap unknown',
                      test_partition_used_for_inference=False,rows=rows)
        record(bank,report)
        atomic(bank/'latest.json',report)
        atomic(bank/'aggregate.json',summarize(bank))
        return {k:v for k,v in report.items() if k!='rows'}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--count',type=int,default=2)
    p.add_argument('--offset',type=int,default=None)
    a=p.parse_args()
    print(json.dumps(run(a.root,a.count,a.offset),sort_keys=True))
