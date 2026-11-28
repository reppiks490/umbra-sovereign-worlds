"""Audit original human-authored GSM8K JSONL. Never invoke an optimizer."""
import argparse,hashlib,json,re,unicodedata
from pathlib import Path
REPO='openai/grade-school-math'
REV='3101c7d5072418e28b9008a6636bde82a006892c'
ORIGINAL_ROWS=[
 dict(repo=REPO,revision=REV,category='reasoning',kind='dataset',split=split,path='grade_school_math/data/'+name+'.jsonl',size=size,sha=sha,algorithm='sha256',license='mit',url='https://raw.githubusercontent.com/'+REPO+'/'+REV+'/grade_school_math/data/'+name+'.jsonl')
 for name,split,size,sha in [('train','candidate_training',4166206,'17f347dc51477c50d4efb83959dbb7c56297aba886e5544ee2aaed3024813465'),('test','evaluation',749738,'3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14')]]
def normal(question):
 return ' '.join(unicodedata.normalize('NFKC',question).casefold().split())
def digest(x):
 return hashlib.sha256(x.encode('utf8')).hexdigest()
def validate(row):
 if not isinstance(row,dict) or set(row)!={'question','answer'}:raise ValueError('row schema')
 q,a=row['question'],row['answer']
 if not isinstance(q,str) or not isinstance(a,str) or not 1<=len(q)<=12000 or not 1<=len(a)<=24000 or not normal(q) or not re.search(r'(?:^|\n)####\s+-?[\d,]+(?:\.\d+)?\s*$',a):raise ValueError('invalid human solution')
 return {'question':q,'answer':a,'question_sha256':digest(normal(q)),'record_sha256':digest(json.dumps(row,sort_keys=True,ensure_ascii=False))}
def audit_records(train,test):
 hold={};pool={};overlap=duplicates=0
 for raw in test:
  r=validate(raw);k=r['question_sha256']
  if k in hold and hold[k]['answer']!=r['answer']:raise ValueError('conflicting holdout')
  hold.setdefault(k,r)
 for raw in train:
  r=validate(raw);k=r['question_sha256']
  if k in hold:overlap+=1;continue
  if k in pool:
   if pool[k]['answer']!=r['answer']:raise ValueError('conflicting training record')
   duplicates+=1;continue
  pool[k]=r
 training=[];validation=[]
 for k,r in sorted(pool.items()):
  (validation if int(k[:8],16)%10==0 else training).append(r)
 return {'original_training':len(train),'original_test':len(test),'train_overlap_removed':overlap,'duplicate_training_removed':duplicates,'retained_training_pool':len(pool),'training':len(training),'validation':len(validation),'holdout':len(hold),'deduplication':'NFKC casefold whitespace exact normalized question; not semantic near-duplicate audit','weight_training':False,'production_authority':False},{'train':training,'validation':validation,'test':list(hold.values())}
def read_verified(root,row):
 p=root/'intelligence-resources'/row['category']/(row['repo'].replace('/','--')+'--'+row['revision'][:12])/row['path']
 receipt=p.with_name(p.name+'.receipt.json')
 if not p.is_file() or not receipt.is_file():return None
 if p.is_symlink() or receipt.is_symlink() or json.loads(receipt.read_text(encoding='utf8'))!=row or p.stat().st_size!=row['size']:raise ValueError('corpus receipt mismatch')
 raw=p.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=row['sha']:raise ValueError('corpus source digest mismatch')
 return [json.loads(x) for x in raw.decode('utf8').splitlines() if x.strip()]
def audit(root):
 train,test=[read_verified(root,r) for r in ORIGINAL_ROWS]
 if train is None or test is None:return {'status':'deferred_original_source_download','weight_training':False,'production_authority':False}
 if len(train)!=7473 or len(test)!=1319:raise ValueError('publisher row count mismatch')
 report,rows=audit_records(train,test)
 if not rows['train'] or not rows['validation'] or not rows['test']:raise ValueError('empty split')
 out=root/'experience'/'source-knowledge'/'human-corpus';out.mkdir(parents=True,exist_ok=True)
 for key,records in rows.items():
  raw=''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in records).encode('utf8')
  p=out/(key+'.jsonl');tmp=p.with_suffix('.tmp');tmp.write_bytes(raw);tmp.replace(p)
  report[key+'_sha256']=hashlib.sha256(raw).hexdigest()
 report.update(status='audited',repo=REPO,revision=REV,license='MIT publisher metadata; source review retained',sources=ORIGINAL_ROWS,public_benchmark_contamination='unknown; not proof of novel reasoning',human_authored=True)
 p=out/'audit.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(report,indent=2),encoding='utf8');tmp.replace(p);return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);a=p.parse_args();print(json.dumps(audit(a.root)))
