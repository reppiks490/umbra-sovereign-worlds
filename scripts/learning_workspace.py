"""Owner-local durable replay bank. No model loading or external calls."""
import hashlib,json,os,sqlite3,shutil,time,math
from pathlib import Path
CAP=1000000000
FLOOR=3000000000
MODELS=('qwen3:0.6b','granite4:350m')
SPLITS=('training','retention','transfer')
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def plan_replay(rows,n,counts,cycle):
 if type(n) is not int or not 1<=n<=128 or type(cycle) is not int or cycle<0:raise ValueError('replay budget')
 unique={}
 for r in rows:
  h=r['prompt_sha256']
  if h not in unique:unique[h]=r
 groups={}
 for r in unique.values():groups.setdefault(r['domain'],[]).append(r)
 for domain in groups:
  groups[domain].sort(key=lambda r:(counts.get(r['prompt_sha256'],0),digest([cycle,r['prompt_sha256']])))
 picked=[];usage={}
 while groups and len(picked)<n:
  # Exposure first; domain balance second. Tie-breaking changes per cycle.
  domain=min(groups,key=lambda d:(counts.get(groups[d][0]['prompt_sha256'],0),usage.get(d,0),digest([cycle,d])))
  picked.append(groups[domain].pop(0));usage[domain]=usage.get(domain,0)+1
  if not groups[domain]:del groups[domain]
 return picked
def summarize_losses(rows,losses,anchor_ids):
 if len(rows)!=len(losses) or not rows or any(type(x) not in (int,float) or not math.isfinite(x) or x<0 for x in losses):raise ValueError('evaluation losses')
 ids=[r['prompt_sha256'] for r in rows]
 if len(set(ids))!=len(ids) or not anchor_ids or not set(anchor_ids)<=set(ids):raise ValueError('anchor identity')
 domains={};anchor=[]
 for r,x in zip(rows,losses):
  domains.setdefault(r['domain'],[]).append(x)
  if r['prompt_sha256'] in anchor_ids:anchor.append(x)
 return {'mean':sum(losses)/len(losses),'anchor_mean':sum(anchor)/len(anchor),'domains':{k:{'count':len(v),'mean':sum(v)/len(v)} for k,v in domains.items()}}
def retention_gate(before,after,anchor_before,anchor_after):
 from native_lora_train import promotion_gate
 return promotion_gate(before,after) and all(math.isfinite(anchor_before[k]) and math.isfinite(anchor_after[k]) and 0<=anchor_after[k]<=anchor_before[k]+.02 for k in ('retention','transfer'))
class ReplayBank:
 def __init__(self,root):
  self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
  self.path=self.root/'replay.sqlite3'
  if self.path.is_symlink() or self.path.exists() and self.path.stat().st_size>CAP:raise ValueError('bank size or path')
  self.db=sqlite3.connect(self.path,timeout=10)
  self.db.execute('PRAGMA foreign_keys=ON')
  self.db.execute('PRAGMA journal_mode=DELETE')
  self.db.execute('PRAGMA synchronous=FULL')
  self.db.execute('PRAGMA max_page_count='+str(CAP//self.db.execute('PRAGMA page_size').fetchone()[0]))
  self.db.executescript("""
  CREATE TABLE IF NOT EXISTS questions(hash TEXT PRIMARY KEY,split TEXT NOT NULL,truth TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS examples(model TEXT NOT NULL,hash TEXT NOT NULL REFERENCES questions(hash),domain TEXT NOT NULL,payload TEXT NOT NULL,first_seen INTEGER NOT NULL,PRIMARY KEY(model,hash));
  CREATE TABLE IF NOT EXISTS snapshots(model TEXT NOT NULL,digest TEXT NOT NULL,created INTEGER NOT NULL,PRIMARY KEY(model,digest));
  CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY,model TEXT NOT NULL,identity TEXT NOT NULL,accepted INTEGER NOT NULL,created INTEGER NOT NULL);
  CREATE TABLE IF NOT EXISTS exposures(model TEXT NOT NULL,hash TEXT NOT NULL,visits INTEGER NOT NULL,PRIMARY KEY(model,hash),FOREIGN KEY(model,hash) REFERENCES examples(model,hash));
  CREATE TABLE IF NOT EXISTS anchors(model TEXT NOT NULL,split TEXT NOT NULL,ordinal INTEGER NOT NULL,hash TEXT NOT NULL,PRIMARY KEY(model,split,ordinal),FOREIGN KEY(model,hash) REFERENCES examples(model,hash));
  CREATE TABLE IF NOT EXISTS evaluations(id TEXT PRIMARY KEY REFERENCES attempts(id),payload TEXT NOT NULL);
  CREATE INDEX IF NOT EXISTS examples_domain ON examples(model,domain);
  """)
 def __enter__(self):return self
 def __exit__(self,*args):self.db.close()
 def ingest(self,c):
  from native_lora_train import validate_corpus
  validate_corpus(c,c.get('model'))
  model=c['model'];now=int(time.time());sid=digest(c)
  if shutil.disk_usage(self.root).free<FLOOR:raise ValueError('workspace disk reserve')
  with self.db:
   for split in SPLITS:
    for r in c[split]:
     h=r['prompt_sha256'];truth=digest([r['answer'],sorted(r['options'])])
     if not isinstance(r.get('domain'),str) or not 1<=len(r['domain'])<=100:raise ValueError('domain')
     payload=json.dumps(r,ensure_ascii=False,sort_keys=True,allow_nan=False)
     if len(payload.encode())>16384:raise ValueError('example budget')
     old=self.db.execute('SELECT split,truth FROM questions WHERE hash=?',(h,)).fetchone()
     if old and old!=(split,truth):raise ValueError('cross-cycle split or truth conflict')
     self.db.execute('INSERT OR IGNORE INTO questions VALUES(?,?,?)',(h,split,truth))
     self.db.execute('INSERT OR IGNORE INTO examples VALUES(?,?,?,?,?)',(model,h,r['domain'],payload,now))
   for split in ('retention','transfer'):
    if not self.db.execute('SELECT 1 FROM anchors WHERE model=? AND split=?',(model,split)).fetchone():
     rows=sorted(c[split],key=lambda r:r['prompt_sha256'])[:8]
     for i,r in enumerate(rows):self.db.execute('INSERT INTO anchors VALUES(?,?,?,?)',(model,split,i,r['prompt_sha256']))
   self.db.execute('INSERT OR IGNORE INTO snapshots VALUES(?,?,?)',(model,sid,now))
  return sid
 def counts(self,model):
  if model not in MODELS:raise ValueError('model')
  return dict(self.db.execute('SELECT hash,visits FROM exposures WHERE model=?',(model,)))
 def candidates(self,model,limit=512):
  if model not in MODELS or type(limit) is not int or not 1<=limit<=512:raise ValueError('candidate budget')
  rows=self.db.execute("""SELECT e.payload FROM examples e JOIN questions q ON q.hash=e.hash LEFT JOIN exposures x ON x.model=e.model AND x.hash=e.hash WHERE e.model=? AND q.split='training' ORDER BY COALESCE(x.visits,0),e.first_seen DESC,e.hash LIMIT ?""",(model,limit))
  return [json.loads(x[0]) for x in rows]
 def anchors(self,model,split):
  if model not in MODELS or split not in ('retention','transfer'):raise ValueError('anchor scope')
  return [json.loads(r[0]) for r in self.db.execute('SELECT e.payload FROM anchors a JOIN examples e ON a.model=e.model AND a.hash=e.hash WHERE a.model=? AND a.split=? ORDER BY a.ordinal',(model,split))]
 def record_attempt(self,aid,model,ids,accepted,evaluation=None):
  if model not in MODELS or not isinstance(aid,str) or not 1<=len(aid)<=128 or type(accepted) is not bool or not isinstance(ids,list) or not 1<=len(ids)<=128 or len(set(ids))!=len(ids):raise ValueError('attempt identity')
  if evaluation is not None:
   from native_lora_train import promotion_gate
   if not isinstance(evaluation,dict) or evaluation.get('adapter_weight_training') is not True or evaluation.get('accepted') is not accepted or (accepted and not promotion_gate(evaluation['before'],evaluation['after'])) or len(json.dumps(evaluation,allow_nan=False))>65536:raise ValueError('evaluation evidence')
  if accepted and evaluation and 'anchor_before' in evaluation and not retention_gate(evaluation['before'],evaluation['after'],evaluation['anchor_before'],evaluation['anchor_after']):raise ValueError('anchor regression')
  identity=digest([model,ids,accepted,evaluation])
  with self.db:
   old=self.db.execute('SELECT identity FROM attempts WHERE id=?',(aid,)).fetchone()
   if old:
    if old[0]!=identity:raise ValueError('attempt conflict')
    return
   for h in ids:
    if not self.db.execute("SELECT 1 FROM examples e JOIN questions q ON q.hash=e.hash WHERE e.model=? AND e.hash=? AND q.split='training'",(model,h)).fetchone():raise ValueError('unverified replay')
   self.db.execute('INSERT INTO attempts VALUES(?,?,?,?,?)',(aid,model,identity,int(accepted),int(time.time())))
   if evaluation is not None:self.db.execute('INSERT INTO evaluations VALUES(?,?)',(aid,json.dumps(evaluation,sort_keys=True,allow_nan=False)))
   for h in ids:self.db.execute('INSERT INTO exposures VALUES(?,?,1) ON CONFLICT(model,hash) DO UPDATE SET visits=visits+1',(model,h))
 def stats(self):
  scalar=lambda sql:self.db.execute(sql).fetchone()[0]
  return {'examples':scalar('SELECT COUNT(*) FROM examples'),'unique_prompts':scalar('SELECT COUNT(*) FROM questions'),'snapshots':scalar('SELECT COUNT(*) FROM snapshots'),'attempts':scalar('SELECT COUNT(*) FROM attempts'),'accepted_attempts':scalar('SELECT COUNT(*) FROM attempts WHERE accepted=1'),'evaluations':scalar('SELECT COUNT(*) FROM evaluations'),'anchor_examples':scalar('SELECT COUNT(*) FROM anchors'),'exposures':scalar('SELECT COALESCE(SUM(visits),0) FROM exposures'),'splits':dict(self.db.execute('SELECT split,COUNT(*) FROM questions GROUP BY split')),'models':dict(self.db.execute('SELECT model,COUNT(*) FROM examples GROUP BY model')),'domains':scalar('SELECT COUNT(DISTINCT domain) FROM examples'),'db_bytes':self.path.stat().st_size,'cap_bytes':CAP}
def refresh(root):
 root=Path(root);workspace=root/'experience'/'learning-workspace'
 with ReplayBank(workspace) as bank:
  for model in MODELS:
   p=root/'megaswarm'/'corpora'/(model.replace(':','-')+'.json')
   if not p.is_file() or p.is_symlink() or p.stat().st_size>2000000:raise ValueError('missing or invalid corpus')
   bank.ingest(json.loads(p.read_text(encoding='utf8')))
  stats=bank.stats()
 return {'status':'ready','scope':'validated curriculum archive; no weight update',**stats}
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args()
 print(json.dumps(refresh(a.root)),flush=True)
