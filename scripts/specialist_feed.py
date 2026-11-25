"""Evidence-bearing specialist outputs for the local small LLMs."""
import argparse,json,math,time
from pathlib import Path
from source_knowledge import Knowledge
from native_lora_train import available_ram
MODELS=('sentence-transformers/all-MiniLM-L6-v2','BAAI/bge-small-en-v1.5')
def fuse_rankings(sources,results):
 if not sources or not results:raise ValueError('empty ranking')
 names=[r['model'] for r in results]
 if len(names)!=len(set(names)):raise ValueError('duplicate specialist')
 for r in results:
  if len(r['scores'])!=len(sources) or any(type(x) not in (float,int) or not math.isfinite(x) or not -1<=x<=1 for x in r['scores']):raise ValueError('invalid score vector')
 out=[]
 for i,s in enumerate(sources):
  scores={r['model']:r['scores'][i] for r in results}
  out.append({**s,'specialist_scores':scores,'fused_score':round(sum(scores.values())/len(scores),12)})
 return sorted(out,key=lambda x:-x['fused_score'])
def score(root,repo,query,sources):
 from agentic_native import inventory,read_receipt,verify_file,SafeWeights,bert_forward,SUPPORTED
 from tokenizers import Tokenizer
 import numpy as np
 candidates=inventory(root,repo)
 if len(candidates)!=1:raise ValueError('verified weight identity')
 r=candidates[0];folder=root/r['folder']
 if available_ram()<r['size_bytes']*4+1600000000:raise ValueError('memory admission')
 receipt=read_receipt(folder);files={f['name']:f for f in receipt['files']}
 cfg=json.loads(verify_file(folder,files['config.json']).read_text(encoding='utf8'))
 if cfg.get('model_type')!='bert':raise ValueError('architecture')
 tok=Tokenizer.from_file(str(verify_file(folder,files['tokenizer.json'])));tok.enable_truncation(max_length=96)
 with SafeWeights(verify_file(folder,files['model.safetensors'])) as w:
  q=bert_forward(w,cfg,tok.encode(query).ids,SUPPORTED[repo])
  scores=[float(np.clip(q@bert_forward(w,cfg,tok.encode(s['text']).ids,SUPPORTED[repo]),-1,1)) for s in sources]
 return {'model':repo,'revision':r['revision'],'weight_sha256':r['digest'],'scores':scores,'inference':'native_numpy_bert','scope':'cosine ranking of 96-token input; not calibrated probability'}
def catalog(root):
 rows=[]
 for bucket in ('neural','tiny'):
  for p in sorted((root/bucket).glob('*/receipt.json')):
   try:
    r=json.loads(p.read_text(encoding='utf8'))
    if r.get('native_verified') is True:rows.append({k:r.get(k) for k in ('repo','revision','digest','task','total','license','native_verified','inference_verified','training_verified')})
   except (OSError,ValueError):continue
 return rows
def run(root,query,model):
 from source_assist import assist
 from hf_weight_cache import lock
 outdir=root/'experience'/'source-knowledge';outdir.mkdir(parents=True,exist_ok=True)
 with Knowledge(outdir) as db:sources=db.search(query,3)
 if not sources:return {'status':'no_sources'}
 with lock(root/'cache-use.lock'):
  results=[];errors=[]
  for repo in MODELS:
   try:results.append(score(root,repo,query,sources))
   except Exception as e:errors.append({'model':repo,'reason':type(e).__name__+': '+str(e)[:100]})
 if not results:return {'status':'deferred_specialists','errors':errors}
 ranked=fuse_rankings(sources,results)
 try:answer=assist(root,query,model,ranked_sources=ranked)
 except Exception as e:answer={'status':'failed','reason':type(e).__name__}
 result={'status':'feed_verified' if answer.get('status')=='quote_verified' else 'ranked_sources_only','query':query,'model':model,'specialists':results,'errors':errors,'ranked_sources':[{k:s.get(k) for k in ('repo','revision','path','sha256','start_line','end_line','specialist_scores','fused_score')} for s in ranked],'answer':answer,'catalog':catalog(root),'weight_training':False,'production_authority':False}
 p=outdir/'latest-specialist-feed.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(result,indent=2),encoding='utf8');tmp.replace(p)
 if result['status']=='feed_verified':
  target=outdir/('latest-specialist-feed-'+model.replace(':','-')+'.json')
  temp=target.with_suffix('.tmp');temp.write_text(json.dumps(result,indent=2),encoding='utf8');temp.replace(target)
 return {**result,'catalog':{'receipt_count':len(result['catalog']),'scope':'metadata only, not all inference-qualified'}}
def cycle(root):
 from source_assist import MODELS as LLMS
 queries=('time series forecasting methods','quantitative investment research','quality diversity archive','sparse identification nonlinear dynamics')
 tick=int(time.time())//1800
 return run(root,queries[tick%len(queries)],LLMS[tick%len(LLMS)])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--query',required=True);p.add_argument('--model',default='qwen3:0.6b');a=p.parse_args();print(json.dumps(run(a.root,a.query,a.model)))
