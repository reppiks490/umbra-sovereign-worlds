"""Observed source retrieval comparison, reference parity, and bounded neural composition."""
import argparse,json,math,os,time,statistics,hashlib
from pathlib import Path
from source_knowledge import Knowledge
from native_lora_train import available_ram
from hf_weight_cache import lock
ENCODERS={'sentence-transformers/all-MiniLM-L6-v2':'mean','BAAI/bge-small-en-v1.5':'cls'}
CROSS='cross-encoder/ms-marco-MiniLM-L6-v2'
# Reviewer-specified repository-identification probes; authentic document text, not training.
PROBES=(('time series classification clustering and anomaly detection','aeon-toolkit/aeon'),('sparse identification of nonlinear dynamical systems','dynamicslab/pysindy'),('quality diversity optimization archives','icaros-usc/pyribs'),('offline reinforcement learning algorithms','takuseno/d3rlpy'),('quantitative investment research platform','microsoft/qlib'),('agent based interactive discrete event market simulation','abides-sim/abides'),('world model reinforcement learning','danijar/dreamerv3'),('neural forecasting time series library','Nixtla/neuralforecast'))
def rank_metrics(order,relevant):
 if len(set(order))!=len(order) or not relevant:raise ValueError('ranking identity')
 first=next((i+1 for i,x in enumerate(order) if x in relevant),None)
 return {'reciprocal_rank':1/first if first else 0,'hit_at_1':first==1,'hit_at_3':first is not None and first<=3}
def compare_vectors(a,b):
 if not a or len(a)!=len(b) or not all(math.isfinite(x) for x in list(a)+list(b)):raise ValueError('vector bounds')
 denom=math.sqrt(sum(x*x for x in a)*sum(x*x for x in b))
 if not denom:raise ValueError('zero norm')
 cosine=sum(x*y for x,y in zip(a,b))/denom;error=max(abs(x-y) for x,y in zip(a,b))
 return {'cosine':cosine,'max_abs_error':error,'passed':cosine>=.9999 and error<=.002}
def order_scores(v):
 if not v or not all(math.isfinite(x) for x in v):raise ValueError('score bounds')
 return sorted(range(len(v)),key=lambda i:(-v[i],i))
def rank_fusion(scores):
 if not scores or len({len(v) for v in scores.values()})!=1:raise ValueError('score coverage')
 n=len(next(iter(scores.values())));total=[0.]*n
 for values in scores.values():
  for i,k in enumerate(order_scores(values),1):total[k]+=1/(60+i)
 return order_scores(total)
def documents(root):
 with Knowledge(root/'experience'/'source-knowledge') as db:
  rows=db.db.execute("""SELECT s.repo,s.revision,s.path,s.sha,c.text FROM sources s JOIN chunks c ON c.source_id=s.id WHERE lower(s.path) LIKE 'readme%' AND c.id=(SELECT min(id) FROM chunks WHERE source_id=s.id) ORDER BY s.repo,s.revision,s.path""").fetchall()
 chosen={}
 for repo,rev,path,sha,t in rows:
  if repo in {r for _,r in PROBES} and repo not in chosen:chosen[repo]={'repo':repo,'revision':rev,'path':path,'sha256':sha,'text':t}
 if len(chosen)!=len(PROBES):raise ValueError('missing reviewed source')
 return [chosen[k] for k in sorted(chosen)]
def checkpoint(root,repo):
 from agentic_native import inventory,read_receipt
 matches=inventory(root,repo)
 if len(matches)!=1:raise ValueError('checkpoint identity')
 r=matches[0];p=root/r['folder'];read_receipt(p)
 if available_ram()<r['size_bytes']*4+1600000000:raise ValueError('memory admission')
 return p,r
def run(root):
 import gc,re
 from source_assist import local_api
 if available_ram()<3000000000 or local_api('ps').get('models'):return {'status':'deferred_memory_or_busy'}
 docs=documents(root);queries=[q for q,r in PROBES];repos=[d['repo'] for d in docs]
 scores={};parity={};identities={};errors={};elapsed={}
 from agentic_native import SafeWeights,bert_forward,configure_tokenizer
 from tokenizers import Tokenizer
 os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
 with lock(root/'experience'/'model-compute.lock'),lock(root/'cache-use.lock'):
  import torch
  from transformers import AutoModel,AutoModelForSequenceClassification,AutoTokenizer
  torch.set_num_threads(2)
  for repo,pool in ENCODERS.items():
   started=time.monotonic()
   try:
    p,r=checkpoint(root,repo);tok=AutoTokenizer.from_pretrained(str(p),local_files_only=True,trust_remote_code=False)
    model,info=AutoModel.from_pretrained(str(p),local_files_only=True,trust_remote_code=False,use_safetensors=True,output_loading_info=True)
    if any('pooler' not in k for k in info['missing_keys']) or info['mismatched_keys']:raise ValueError('missing reference weights')
    model.eval()
    strings=queries+[d['text'] for d in docs]
    def reference(s):
     x=tok(s,return_tensors='pt',max_length=96,truncation=True)
     with torch.inference_mode():y=model(**x).last_hidden_state
     v=y.mean(dim=1)[0] if pool=='mean' else y[0,0]
     return torch.nn.functional.normalize(v,dim=0).tolist()
    vectors=[reference(s) for s in strings]
    cfg=json.loads((p/'config.json').read_text(encoding='utf8'));native=configure_tokenizer(Tokenizer.from_file(str(p/'tokenizer.json')),96)
    with SafeWeights(p/'model.safetensors') as w:
     comparisons=[compare_vectors(bert_forward(w,cfg,native.encode(s).ids,pool).tolist(),vectors[i]) for i,s in enumerate(strings[:2])]
    parity[repo]={'cases':comparisons,'passed':all(x['passed'] for x in comparisons)}
    scores[repo]=[[sum(a*b for a,b in zip(v,w)) for w in vectors[len(queries):]] for v in vectors[:len(queries)]]
    identities[repo]={'revision':r['revision'],'digest':r['digest']};del model,vectors;gc.collect()
   except Exception as e:errors[repo]=type(e).__name__+': '+str(e)[:160]
   elapsed[repo]=time.monotonic()-started
  started=time.monotonic()
  try:
   p,r=checkpoint(root,CROSS);tok=AutoTokenizer.from_pretrained(str(p),local_files_only=True,trust_remote_code=False)
   model,info=AutoModelForSequenceClassification.from_pretrained(str(p),local_files_only=True,trust_remote_code=False,use_safetensors=True,output_loading_info=True)
   if info['missing_keys'] or info['mismatched_keys']:raise ValueError('missing classifier weights')
   model.eval();out=[]
   for q in queries:
    x=tok([q]*len(docs),[d['text'] for d in docs],padding=True,truncation=True,max_length=128,return_tensors='pt')
    with torch.inference_mode():v=model(**x).logits
    if tuple(v.shape)!=(len(docs),1):raise ValueError('classifier shape')
    out.append(v[:,0].tolist())
   scores[CROSS]=out;identities[CROSS]={'revision':r['revision'],'digest':r['digest']};del model;gc.collect()
  except Exception as e:errors[CROSS]=type(e).__name__+': '+str(e)[:160]
  elapsed[CROSS]=time.monotonic()-started
 words=lambda s:set(re.findall('[a-z0-9]{3,}',s.lower()))
 scores['lexical_overlap']=[[len(words(q)&words(d['text'])) for d in docs] for q in queries]
 from itertools import combinations
 variants={};names=list(scores)
 for n in range(1,len(names)+1):
  for group in combinations(names,n):
   results=[]
   for i,(q,repo) in enumerate(PROBES):
    ranking=rank_fusion({k:scores[k][i] for k in group}) if len(group)>1 else order_scores(scores[group[0]][i])
    ordered=[repos[k] for k in ranking];results.append({'query':q,'expected_repo':repo,'ranking':ordered,**rank_metrics(ordered,{repo})})
   variants[' + '.join(group)]={'mrr':statistics.mean(r['reciprocal_rank'] for r in results),'hit_at_1':sum(r['hit_at_1'] for r in results),'hit_at_3':sum(r['hit_at_3'] for r in results),'cases':results}
 report={'status':'completed','scope':'eight reviewer-authored repository identification probes, real pinned README first passages; exploratory, not independent general retrieval benchmark','parity':parity,'identities':identities,'errors':errors,'elapsed_seconds':elapsed,'variants':variants,'documents':[{k:v for k,v in d.items() if k!='text'} for d in docs],'probe_count':len(PROBES),'weight_training':False,'production_authority':False}
 out=root/'experience'/'source-knowledge'/'retrieval-qualification.json';tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(report,indent=2),encoding='utf8');tmp.replace(out)
 return {**report,'variants':{k:{x:y for x,y in v.items() if x!='cases'} for k,v in variants.items()}}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();print(json.dumps(run(a.root)))
