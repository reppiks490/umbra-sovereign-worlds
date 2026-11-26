"""Owner-local OMEGA durable coordination. No execution, trading or deployment authority."""
import sqlite3,json,math,uuid,contextlib,re,time,argparse,hashlib
from pathlib import Path
LANES=('OMEGA','ICARUS','EXASOVEREIGN','MYRIAD','UMBRA')
WEIGHTS=(.30,.25,.20,.15,.10)
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def require(v,pattern):
 if not isinstance(v,str) or not re.fullmatch(pattern,v):raise ValueError('invalid identity')
 return v
class Ledger:
 def __init__(self,path):
  self.path=str(path)
  with self.tx() as c:
   c.execute("""CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY,lane TEXT NOT NULL,base TEXT NOT NULL,objective TEXT NOT NULL,priority TEXT NOT NULL,score REAL NOT NULL,resource TEXT NOT NULL,deps TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'ready',owner TEXT,token TEXT,leased_at INTEGER,handle TEXT,receipt TEXT,receipt_path TEXT,verifier TEXT,reason TEXT,retry_condition TEXT)""")
   c.execute("""CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY,task TEXT NOT NULL,event TEXT NOT NULL,detail TEXT NOT NULL,at INTEGER NOT NULL)""")
 @contextlib.contextmanager
 def tx(self):
  c=sqlite3.connect(self.path,timeout=15,isolation_level=None);c.row_factory=sqlite3.Row
  try:
   c.execute('PRAGMA busy_timeout=15000');c.execute('BEGIN IMMEDIATE')
   yield c
   c.execute('COMMIT')
  except BaseException:
   if c.in_transaction:c.execute('ROLLBACK')
   raise
  finally:c.close()
 def event(self,c,k,event,detail):
  c.execute('INSERT INTO events(task,event,detail,at) VALUES(?,?,?,?)',(k,event,canonical(detail),int(time.time())))
 def add(self,k,lane,base,objective,priority,resource,deps):
  require(k,r'[A-Za-z0-9_.:-]{1,128}');require(base,r'[a-f0-9]{40}|[a-f0-9]{64}')
  if lane not in LANES or not isinstance(objective,str) or not 1<=len(objective)<=4000:raise ValueError('task scope')
  if not isinstance(resource,str) or len(resource)>128:raise ValueError('resource')
  if len(priority)!=6 or any(type(x) not in (int,float) or not math.isfinite(x) or not 0<=x<=1 for x in priority):raise ValueError('priority')
  if not isinstance(deps,list) or len(set(deps))!=len(deps) or k in deps:raise ValueError('dependencies')
  p=canonical(priority);ds=canonical(sorted(deps));score=sum(x*y for x,y in zip(priority,WEIGHTS))-priority[5]
  identity=(lane,base,objective,p,resource,ds)
  with self.tx() as c:
   old=c.execute('SELECT * FROM tasks WHERE id=?',(k,)).fetchone()
   if old:
    if tuple(old[x] for x in ('lane','base','objective','priority','resource','deps'))!=identity:raise ValueError('task identity conflict')
    return k
   if any(c.execute('SELECT 1 FROM tasks WHERE id=?',(d,)).fetchone() is None for d in deps):raise ValueError('unknown dependency')
   c.execute('INSERT INTO tasks(id,lane,base,objective,priority,score,resource,deps) VALUES(?,?,?,?,?,?,?,?)',(k,lane,base,objective,p,score,resource,ds))
   self.event(c,k,'added',{'base':base,'lane':lane})
  return k
 def claim(self,lane,owner,now=None):
  if lane not in LANES or not isinstance(owner,str) or not 1<=len(owner)<=128:raise ValueError('claim identity')
  now=int(time.time()) if now is None else int(now)
  with self.tx() as c:
   rows=c.execute("SELECT * FROM tasks WHERE lane=? AND state='ready' ORDER BY score DESC,id ASC",(lane,)).fetchall()
   for r in rows:
    if any(c.execute('SELECT state FROM tasks WHERE id=?',(d,)).fetchone()[0]!='qualified' for d in json.loads(r['deps'])):continue
    if r['resource'] and c.execute("SELECT 1 FROM tasks WHERE resource=? AND state IN ('leased','reported')",(r['resource'],)).fetchone():continue
    token=uuid.uuid4().hex
    c.execute("UPDATE tasks SET state='leased',owner=?,token=?,leased_at=?,reason=NULL,retry_condition=NULL WHERE id=?",(owner,token,now,r['id']))
    self.event(c,r['id'],'claimed',{'owner':owner,'token':token})
    return dict(c.execute('SELECT * FROM tasks WHERE id=?',(r['id'],)).fetchone())
  return None
 def owned(self,c,k,token):
  r=c.execute("SELECT * FROM tasks WHERE id=? AND state='leased' AND token=?",(k,token)).fetchone()
  if not r:raise ValueError('stale or invalid ownership')
  return r
 def handle(self,k,token,handle):
  if not isinstance(handle,str) or not 1<=len(handle)<=512:raise ValueError('handle')
  with self.tx() as c:
   r=self.owned(c,k,token)
   if r['handle'] and r['handle']!=handle:raise ValueError('active handle already recorded')
   c.execute('UPDATE tasks SET handle=? WHERE id=?',(handle,k));self.event(c,k,'handle',{'handle':handle})
 def evidence(self,r,receipt):
  root=Path(self.path).resolve().parent/'evidence'
  p=Path(receipt)
  if not root.is_dir() or root.is_symlink() or not p.is_absolute() or not p.is_file() or p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):raise ValueError('receipt outside evidence root')
  p=p.resolve()
  if p.stat().st_size>262144:raise ValueError('receipt size')
  raw=p.read_bytes()
  try:j=json.loads(raw)
  except (ValueError,UnicodeError) as e:raise ValueError('receipt syntax') from e
  if not isinstance(j,dict) or any(j.get(k)!=v for k,v in {'task':r['id'],'base':r['base'],'token':r['token'],'outcome':'passed','handle':r['handle']}.items()):raise ValueError('receipt identity')
  items=j.get('artifacts')
  if not isinstance(items,list) or not 1<=len(items)<=16:raise ValueError('artifact scope')
  seen=set()
  for item in items:
   if not isinstance(item,dict):raise ValueError('artifact record')
   name=item.get('path')
   if not isinstance(name,str) or not name or Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('artifact path')
   target=p.parent/name
   if target.is_symlink() or not target.is_file() or not target.resolve().is_relative_to(p.parent):raise ValueError('artifact outside receipt directory')
   target=target.resolve()
   if target==p or target in seen or target.stat().st_size>64*1024**2:raise ValueError('artifact identity or size')
   seen.add(target)
   expected=require(item.get('sha256'),r'[a-f0-9]{64}')
   h=hashlib.sha256()
   with target.open('rb') as fd:
    for b in iter(lambda:fd.read(1048576),b''):h.update(b)
   if h.hexdigest()!=expected:raise ValueError('artifact digest mismatch')
  return str(p),hashlib.sha256(raw).hexdigest()
 def finish(self,k,token,receipt,detail):
  if not isinstance(detail,str) or not detail.strip():raise ValueError('receipt detail')
  with self.tx() as c:
   r=self.owned(c,k,token);path,sha=self.evidence(r,receipt)
   c.execute("UPDATE tasks SET state='reported',receipt=?,receipt_path=?,reason=? WHERE id=?",(sha,path,detail,k));self.event(c,k,'reported',{'receipt':sha,'detail':detail})
 def accept(self,k,verifier,detail,settled=None):
  if not all(isinstance(v,str) and v.strip() for v in (verifier,detail)):raise ValueError('review evidence')
  with self.tx() as c:
   r=c.execute("SELECT * FROM tasks WHERE id=? AND state='reported'",(k,)).fetchone()
   if not r or r['owner']==verifier:raise ValueError('distinct reviewer required')
   if r['handle'] and (not isinstance(settled,str) or not settled.strip()):raise ValueError('handle settlement observation required')
   _,sha=self.evidence(r,r['receipt_path'])
   if sha!=r['receipt']:raise ValueError('receipt changed')
   c.execute("UPDATE tasks SET state='qualified',verifier=?,handle=NULL,reason=? WHERE id=?",(verifier,detail,k));self.event(c,k,'qualified',{'verifier':verifier,'detail':detail,'settled':settled,'receipt':sha})
 def block(self,k,token,reason,condition):
  if not all(isinstance(v,str) and v.strip() for v in (reason,condition)):raise ValueError('block condition')
  with self.tx() as c:
   r=self.owned(c,k,token)
   if r['handle']:raise ValueError('active handle must be resolved before release')
   c.execute("UPDATE tasks SET state='blocked',reason=?,retry_condition=? WHERE id=?",(reason,condition,k));self.event(c,k,'blocked',{'reason':reason,'condition':condition})
 def retry(self,k,evidence):
  if not isinstance(evidence,str) or not evidence.strip():raise ValueError('retry evidence')
  with self.tx() as c:
   r=c.execute("SELECT * FROM tasks WHERE id=? AND state='blocked' AND handle IS NULL",(k,)).fetchone()
   if not r:raise ValueError('not safely blocked')
   c.execute("UPDATE tasks SET state='ready',owner=NULL,token=NULL,leased_at=NULL WHERE id=?",(k,));self.event(c,k,'retry',{'evidence':evidence})
 def snapshot(self):
  with self.tx() as c:return [dict(r) for r in c.execute('SELECT * FROM tasks ORDER BY id')]
 def history(self):
  with self.tx() as c:return [dict(r) for r in c.execute('SELECT * FROM events ORDER BY seq')]
def main():
 p=argparse.ArgumentParser();p.add_argument('--db',required=True);sub=p.add_subparsers(dest='action',required=True)
 sub.add_parser('status');sub.add_parser('history')
 x=sub.add_parser('claim');x.add_argument('lane',choices=LANES);x.add_argument('owner')
 x=sub.add_parser('handle');x.add_argument('id');x.add_argument('token');x.add_argument('handle')
 x=sub.add_parser('finish');x.add_argument('id');x.add_argument('token');x.add_argument('receipt');x.add_argument('detail')
 x=sub.add_parser('accept');x.add_argument('id');x.add_argument('verifier');x.add_argument('detail');x.add_argument('--settled')
 x=sub.add_parser('block');x.add_argument('id');x.add_argument('token');x.add_argument('reason');x.add_argument('condition')
 x=sub.add_parser('retry');x.add_argument('id');x.add_argument('evidence')
 a=p.parse_args();l=Ledger(a.db)
 if a.action=='status':v=l.snapshot()
 elif a.action=='history':v=l.history()
 elif a.action=='claim':v=l.claim(a.lane,a.owner)
 elif a.action=='handle':v=l.handle(a.id,a.token,a.handle)
 elif a.action=='finish':v=l.finish(a.id,a.token,a.receipt,a.detail)
 elif a.action=='accept':v=l.accept(a.id,a.verifier,a.detail,a.settled)
 elif a.action=='block':v=l.block(a.id,a.token,a.reason,a.condition)
 elif a.action=='retry':v=l.retry(a.id,a.evidence)
 print(canonical(v))
if __name__=='__main__':main()
