"""Read-only lexical template overlap audit; not semantic certification."""
import argparse,collections,hashlib,json,re,unicodedata
from pathlib import Path
def tokens(q):
 return re.findall(r'\w+|[^\w\s]',re.sub(r'\d+(?:[.,]\d+)*',' NUM ',unicodedata.normalize('NFKC',q).casefold()))
def grams(t):
 return set(zip(t,t[1:],t[2:]))
def scan(train,hold):
 index=collections.defaultdict(list); templates=collections.Counter(); sets=[]
 for i,q in enumerate(train):
  t=tokens(q);templates[tuple(t)]+=1;g=grams(t);sets.append(g)
  for x in g:index[x].append(i)
 exact=near=affected=0
 for q in hold:
  t=tokens(q);exact+=templates[tuple(t)];g=grams(t);hits=collections.Counter(i for x in g for i in index.get(x,()))
  n=sum(c/(len(g)+len(sets[i])-c)>=0.65 for i,c in hits.items())
  near+=n;affected+=bool(n or templates[tuple(t)])
 return dict(template_exact_pairs=exact,near_pairs=near,affected_holdout=affected,training=len(train),holdout=len(hold),threshold=0.65)
def run(root):
 p=root/'experience'/'source-knowledge'/'human-corpus'
 audit=json.loads((p/'audit.json').read_text(encoding='utf8'));rows={}
 for key in ('train','validation','test'):
  raw=(p/(key+'.jsonl')).read_bytes()
  if hashlib.sha256(raw).hexdigest()!=audit[key+'_sha256']:raise ValueError('split digest mismatch')
  rows[key]=[json.loads(x)['question'] for x in raw.decode('utf8').split(chr(10)) if x.strip()]
 report={'method':'number-normalized token trigram Jaccard; lexical only, no semantic guarantee','validation':scan(rows['train'],rows['validation']),'test':scan(rows['train']+rows['validation'],rows['test']),'split_digests':{k:audit[k+'_sha256'] for k in rows},'weight_training':False,'production_authority':False}
 # No holdout text, answers or pair identities exported to training.
 out=p/'overlap-audit.json';tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(report,indent=2),encoding='utf8');tmp.replace(out)
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);print(json.dumps(run(p.parse_args().root)))
