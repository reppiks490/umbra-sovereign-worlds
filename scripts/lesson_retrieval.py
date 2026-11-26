"""Leakage-screened retrieval of original human-authored worked examples."""
import argparse,collections,hashlib,json,math,re,time
from pathlib import Path
from human_corpus import normal,digest,validate
def tokens(text):
 return re.findall(r'[a-z]+|#',re.sub(r'\d+(?:[.,]\d+)*','#',normal(text)))
def grams(t):
 return set(zip(t,t[1:],t[2:]))
def template_similarity(a,b):
 x,y=tokens(a),tokens(b)
 if x==y:return 1.
 g,h=grams(x),grams(y)
 return len(g&h)/len(g|h) if g and h else 0.
class LessonIndex:
 def __init__(self,rows):
  self.rows={};self.tf={};self.df=collections.Counter();self.lengths={}
  for row in rows:
   r=validate({k:row[k] for k in ('question','answer')})
   if r!=row or r['question_sha256'] in self.rows:raise ValueError('source identity or duplicate')
   k=r['question_sha256'];self.rows[k]=r
   t=tokens(r['question']);self.tf[k]=collections.Counter(t);self.df.update(set(t));self.lengths[k]=len(t)
  if not self.rows:raise ValueError('empty source index')
  self.avg=max(1,sum(self.lengths.values())/len(self.rows))
 def select(self,question,question_sha256):
  if digest(normal(question))!=question_sha256:raise ValueError('query identity')
  q=set(tokens(question));n=len(self.rows);best=None
  for k in sorted(self.rows):
   if k==question_sha256:continue
   r=self.rows[k]
   if len(r['question'])+len(r['answer'])>2500:continue
   score=0.
   for w in sorted(q&self.tf[k].keys()):
    f=self.tf[k][w];idf=math.log1p((n-self.df[w]+.5)/(self.df[w]+.5))
    score+=idf*f*2.2/(f+1.2*(.25+.75*self.lengths[k]/self.avg))
   if score<=0 or (best is not None and score<=best['score']):continue
   sim=template_similarity(question,r['question'])
   if sim>=.65:continue
   best={'record':r,'score':score,'template_similarity':sim}
  return best
def run(root,count=2,offset=60,model='qwen3:0.6b'):
 from student_council import roster,load_corpus,lesson,ollama_lesson
 from source_assist import local_api
 from native_lora_train import available_ram,atomic
 from hf_weight_cache import lock
 if not 1<=count<=4 or not 0<=offset<=715-count:raise ValueError('validation window')
 bank=root/'experience'/'lesson-retrieval';bank.mkdir(parents=True,exist_ok=True)
 with lock(root/'experience'/'model-compute.lock'),lock(bank/'research.lock'):
  if local_api('ps').get('models'):return {'status':'deferred_busy'}
  s=next((r for r in roster(root) if r['name']==model and r['backend']=='ollama' and r['present']),None)
  if s is None or available_ram()<s['required_ram']:return {'status':'deferred_admission'}
  corpus=load_corpus(root);index=LessonIndex(corpus['train'])
  cases=[]
  for i in range(offset,offset+count):
   fixed,v=lesson(corpus,i)
   found=index.select(v['question'],v['question_sha256'])
   if found is None:raise ValueError('no admissible retrieved example')
   if template_similarity(v['question'],fixed['question'])>=.65 or len(fixed['question'])+len(fixed['answer'])>2500 or fixed['record_sha256']==found['record']['record_sha256']:
    fixed=next((t for t in corpus['train'] if t['record_sha256']!=found['record']['record_sha256'] and len(t['question'])+len(t['answer'])<=2500 and template_similarity(t['question'],v['question'])<.65),None)
    if fixed is None:raise ValueError('no admissible baseline')
   cases.append((fixed,found,v))
  manifest={'model':model,'digest':s['digest'],'protocol':'bm25-masked-number-lexical-v1','offset':offset,'count':count,'cases':[{'validation':v['record_sha256'],'fixed':t['record_sha256'],'retrieved':f['record']['record_sha256']} for t,f,v in cases]}
  key=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
  path=bank/('trial-'+key+'.json')
  if path.exists():return {'status':'already_recorded','manifest_sha256':key}
  rows=[]
  for i,(fixed,found,v) in enumerate(cases):
   arms=[('fixed',fixed),('retrieved',found['record'])]
   if i%2:arms.reverse()
   for arm,t in arms:
    start=time.monotonic()
    try:r=ollama_lesson(model,s['digest'],t,v)
    except Exception as e:r={'status':'failed','reason':type(e).__name__}
    rows.append({'case':v['record_sha256'],'arm':arm,'lesson':t['record_sha256'],'status':r.get('status'),'correct':r.get('status')=='evaluated' and r.get('correct') is True,'prediction':r.get('predicted_numeric'),'seconds':time.monotonic()-start,'template_similarity':template_similarity(t['question'],v['question'])})
    print(json.dumps({'progress':len(rows),'total':2*count,'arm':arm,'status':r.get('status')}),flush=True)
  paired={v['record_sha256']:{r['arm']:r['correct'] for r in rows if r['case']==v['record_sha256']} for _,_,v in cases}
  wins=sum(x['retrieved'] and not x['fixed'] for x in paired.values())
  losses=sum(x['fixed'] and not x['retrieved'] for x in paired.values())
  result={'status':'completed','manifest':manifest,'manifest_sha256':key,'rows':rows,'cases':count,'source_rows':len(index.rows),'fixed_correct':sum(x['fixed'] for x in paired.values()),'retrieved_correct':sum(x['retrieved'] for x in paired.values()),'wins':wins,'losses':losses,'ties':count-wins-losses,'completed_calls':sum(r['status']=='evaluated' for r in rows),'model_calls':len(rows),'scope':'development validation only; lexical screen not semantic contamination proof; no model promotion','weight_training':False,'production_authority':False,'test_partition_used_for_inference':False}
  atomic(path,result)
  return {k:v for k,v in result.items() if k!='rows'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--count',type=int,default=2);p.add_argument('--offset',type=int,default=60);p.add_argument('--model',default='qwen3:0.6b');a=p.parse_args();print(json.dumps(run(a.root,a.count,a.offset,a.model)))
