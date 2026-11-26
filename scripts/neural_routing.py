"""Research-only rank comparison for actual encoder and cross-encoder outputs."""
import argparse,json,math,time,os,gc
from pathlib import Path

def rank_candidates(sources,a,b,c):
    n=len(sources)
    if not n or any(len(v)!=n for v in (a,b,c)):
        raise ValueError('score coverage')
    if any(type(x) not in (int,float) or not math.isfinite(x) for v in (a,b,c) for x in v):
        raise ValueError('nonfinite score')
    if any(abs(x)>1 for v in (a,b) for x in v):
        raise ValueError('cosine bounds')
    def order(v):
        return sorted(range(n),key=lambda i:(-v[i],i))
    cosine=[(x+y)/2 for x,y in zip(a,b)]
    rank=[0.]*n
    for v in (a,b,c):
        for position,i in enumerate(order(v),1):
            rank[i]+=1/(60+position)
    def ranked(v,scale):
        return [{**sources[i],'specialist_scores':{'minilm':a[i],'bge':b[i],'cross_encoder':math.tanh(c[i])},
                 'fused_score':scale(v[i])} for i in order(v)]
    return {'cosine_mean':ranked(cosine,float),'cross_encoder':ranked(c,math.tanh),
            'rank_fusion':ranked(rank,float)}

def select_route(evidence,baseline='cosine_mean'):
    """Research candidate admission only; never controls production."""
    if not isinstance(evidence,dict) or evidence.get('status')!='completed' or evidence.get('independent') is not True or evidence.get('production_authority') is not False:
        return baseline
    route=evidence.get('candidate')
    n,w,l=(evidence.get(k) for k in ('cases','wins','losses'))
    if route not in ('cross_encoder','rank_fusion') or any(type(x) is not int for x in (n,w,l)):
        return baseline
    if not 30<=n<=5000 or min(w,l)<0 or w+l>n or w<=l or (w-l)/n<.05:
        return baseline
    from council_ledger import paired_sign_p
    # Conservative two-candidate adjustment; external evidence still requires source audit.
    return route if paired_sign_p(w,l)<=.025 else baseline

def cross_scores(root,query,sources):
    from retrieval_qualification import checkpoint,CROSS
    from agentic_native import read_receipt,verify_file
    os.environ['HF_HUB_OFFLINE']='1'
    os.environ['TRANSFORMERS_OFFLINE']='1'
    import torch
    from transformers import AutoModelForSequenceClassification,AutoTokenizer
    torch.set_num_threads(2)
    folder,identity=checkpoint(root,CROSS)
    receipt=read_receipt(folder)
    for f in receipt['files']:
        verify_file(folder,f)
    tok=AutoTokenizer.from_pretrained(str(folder),local_files_only=True,trust_remote_code=False)
    model,info=AutoModelForSequenceClassification.from_pretrained(str(folder),local_files_only=True,trust_remote_code=False,use_safetensors=True,output_loading_info=True)
    if info['missing_keys'] or info['mismatched_keys']:
        raise ValueError('classifier weight mismatch')
    model.eval()
    x=tok([query]*len(sources),[s['text'] for s in sources],padding=True,truncation=True,max_length=128,return_tensors='pt')
    with torch.inference_mode():
        v=model(**x).logits
    if tuple(v.shape)!=(len(sources),1):
        raise ValueError('classifier shape')
    result={'model':CROSS,'revision':identity['revision'],'weight_sha256':identity['digest'],'scores':v[:,0].tolist()}
    del model,v,x
    gc.collect()
    return result

def run(root,query,student='qwen3:0.6b'):
    from specialist_feed import score,MODELS
    from source_assist import retrieve_sources,assist,local_api
    from native_lora_train import atomic
    from hf_weight_cache import lock
    if not 1<=len(query)<=300:
        raise ValueError('query budget')
    out=root/'experience'/'neural-routing'
    out.mkdir(parents=True,exist_ok=True)
    with lock(root/'experience'/'model-compute.lock'),lock(out/'research.lock'):
        if local_api('ps').get('models'):
            return {'status':'deferred_busy','production_authority':False}
        sources=retrieve_sources(root,query)
        if len(sources)<2:
            return {'status':'deferred_insufficient_sources','production_authority':False}
        started=time.monotonic()
        with lock(root/'cache-use.lock'):
            a,b=[score(root,m,query,sources) for m in MODELS]
            c=cross_scores(root,query,sources)
        rankings=rank_candidates(sources,a['scores'],b['scores'],c['scores'])
        print(json.dumps({'phase':'three_specialists_completed','sources':len(sources)}),flush=True)
        # Explicit fixed research arm, not automatic promotion.
        answer=assist(root,query,student,ranked_sources=rankings['cross_encoder'])
        report={'status':'completed','query':query,'student':student,
                'specialists':[a,b,c],'routes':{k:[{f:s.get(f) for f in ('repo','revision','path','sha256','start_line','end_line','symbol','specialist_scores','fused_score')} for s in v] for k,v in rankings.items()},
                'candidate_answer':answer,'elapsed_seconds':time.monotonic()-started,
                'scope':'single live source-assistance trial; quotation fidelity only, relevance and improvement not established',
                'production_authority':False,'weight_training':False,'selected_production_route':None}
        atomic(out/'latest.json',report)
        return report

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--query',required=True)
    p.add_argument('--student',default='qwen3:0.6b')
    a=p.parse_args()
    print(json.dumps(run(a.root,a.query,a.student),ensure_ascii=True))
