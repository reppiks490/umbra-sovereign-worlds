"""Pinned local public research documentation; retrieval, not weight training."""
import argparse,hashlib,json,os,re,sqlite3,subprocess,time
from pathlib import Path
CAP=250000000
REPOS={
 'abides-sim--abides':'abides-sim/abides','aeon-toolkit--aeon':'aeon-toolkit/aeon',
 'danijar--dreamerv3':'danijar/dreamerv3','dynamicslab--pysindy':'dynamicslab/pysindy',
 'icaros-usc--pyribs':'icaros-usc/pyribs','KangOxford--jax-lob':'KangOxford/jax-lob',
 'LAMDA-Tabular--TALENT':'LAMDA-Tabular/TALENT','microsoft--qlib':'microsoft/qlib',
 'nicklashansen--tdmpc2':'nicklashansen/tdmpc2','Nixtla--neuralforecast':'Nixtla/neuralforecast',
 'shiyu-coder--Kronos':'shiyu-coder/Kronos','takuseno--d3rlpy':'takuseno/d3rlpy',
 'thuml--Time-Series-Library':'thuml/Time-Series-Library','yuezhihan--ts2vec':'yuezhihan/ts2vec'}
def learning_policy():
 return {'synthetic_training':False,'legacy_llm_optimizer':False,'source_retrieval':True,'source_weight_training':'bounded_native_pilot_enabled','reason':'original human-authored corpus only; verified checkpoints, independent validation and memory admission required'}
def license_id(s):
 t=s.lower()
 normalized=' '.join(t.split())
 if 'permission is hereby granted, free of charge' in normalized and ('mit license' in normalized or all(x in normalized for x in ('associated documentation files','software without restriction','copyright notice and this permission notice','without warranty of any kind'))):return 'MIT'
 if 'apache license' in t and 'version 2.0' in t:return 'Apache-2.0'
 if 'redistribution and use in source and binary forms' in t and 'neither the name' in t:return 'BSD-3-Clause'
 return None
def digest(s):return hashlib.sha256(s.encode('utf8')).hexdigest()
def split_chunks(s):
 out=[];start=0
 while start<len(s):
  end=min(start+1500,len(s))
  if end<len(s):
   br=s.rfind('\n',start+750,end)
   if br>start:end=br+1
  t=s[start:end]
  if t.strip():out.append({'text':t,'start_line':s.count('\n',0,start)+1,'end_line':s.count('\n',0,end-1)+1})
  start=end
 return out
class Knowledge:
 def __init__(self,root):
  root.mkdir(parents=True,exist_ok=True);self.path=root/'sources.sqlite3'
  if self.path.is_symlink() or self.path.exists() and self.path.stat().st_size>CAP:raise ValueError('knowledge budget')
  self.db=sqlite3.connect(self.path,timeout=10)
  self.db.execute('PRAGMA max_page_count='+str(CAP//self.db.execute('PRAGMA page_size').fetchone()[0]))
  self.db.executescript("""CREATE TABLE IF NOT EXISTS sources(id INTEGER PRIMARY KEY,repo TEXT,revision TEXT,path TEXT,license TEXT,sha TEXT,UNIQUE(repo,revision,path));
 CREATE TABLE IF NOT EXISTS chunks(id INTEGER PRIMARY KEY,source_id INTEGER,start_line INTEGER,end_line INTEGER,text TEXT);
 CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(text,content='chunks',content_rowid='id');""")
 def __enter__(self):return self
 def __exit__(self,*a):self.db.close()
 def ingest(self,repo,revision,path,lic,text):
  if not re.fullmatch(r'[\w.-]+/[\w.-]+',repo) or not re.fullmatch('[a-f0-9]{40,64}',revision) or (lic not in ('MIT','Apache-2.0','BSD-3-Clause') and not (lic=='OWNER-LOCAL' and repo.lower().startswith('reppiks490/'))) or not safe_doc(path) or not 0<len(text.encode('utf8'))<=65536 or '\x00' in text:raise ValueError('source identity')
  h=digest(text);old=self.db.execute('SELECT sha FROM sources WHERE repo=? AND revision=? AND path=?',(repo,revision,path)).fetchone()
  if old:
   if old[0]!=h:raise ValueError('immutable source conflict')
   return
  with self.db:
   sid=self.db.execute('INSERT INTO sources(repo,revision,path,license,sha) VALUES(?,?,?,?,?)',(repo,revision,path,lic,h)).lastrowid
   for c in split_chunks(text):
    cid=self.db.execute('INSERT INTO chunks(source_id,start_line,end_line,text) VALUES(?,?,?,?)',(sid,c['start_line'],c['end_line'],c['text'])).lastrowid
    self.db.execute('INSERT INTO search_index(rowid,text) VALUES(?,?)',(cid,c['text']))
 def search(self,q,limit=4):
  if not isinstance(q,str) or len(q)>512 or not 1<=limit<=8:raise ValueError('search scope')
  words=list(dict.fromkeys(re.findall(r'[A-Za-z0-9_]{3,}',q.lower())))[:12]
  if not words:return []
  expr=' OR '.join('"'+w+'"' for w in words)
  rows=self.db.execute("""SELECT s.repo,s.revision,s.path,s.license,s.sha,c.start_line,c.end_line,c.text
 FROM search_index JOIN chunks c ON c.id=search_index.rowid JOIN sources s ON s.id=c.source_id
 WHERE search_index MATCH ? ORDER BY bm25(search_index),c.id LIMIT ?""",(expr,limit))
  return [dict(zip(('repo','revision','path','license','sha256','start_line','end_line','text'),x)) for x in rows]
 def stats(self):
  return {'sources':self.db.execute('SELECT count(*) FROM sources').fetchone()[0],'chunks':self.db.execute('SELECT count(*) FROM chunks').fetchone()[0],'repositories':self.db.execute('SELECT count(DISTINCT repo) FROM sources').fetchone()[0],'db_bytes':self.path.stat().st_size}
def safe_doc(p):
 return isinstance(p,str) and len(p)<240 and re.fullmatch(r'[A-Za-z0-9_./ -]+',p) and not p.startswith('/') and all(x not in ('','.','..') and not x.startswith('.') and not re.search(r'(?i)secret|credential|password|token|cookie|private',x) for x in p.split('/')) and p.lower().endswith(('.md','.rst','.txt'))
def git(repo,*args):
 r=subprocess.run(['git','-C',str(repo),*args],capture_output=True,timeout=15,env={**os.environ,'GIT_NO_REPLACE_OBJECTS':'1','GIT_OPTIONAL_LOCKS':'0','GIT_TERMINAL_PROMPT':'0'})
 if r.returncode:raise ValueError('git unavailable')
 return r.stdout
def read_blob(repo,rev,path):
 ref=rev+':'+path
 if git(repo,'cat-file','-t',ref).strip()!=b'blob' or not 0<int(git(repo,'cat-file','-s',ref))<=65536:raise ValueError('blob bounds')
 return git(repo,'cat-file','blob',ref).decode('utf8')
def refresh(root):
 base=Path.home()/'projects'/'icarus-ml-research-sources'
 workspace=root/'experience'/'source-knowledge'
 rejects=[]
 with Knowledge(workspace) as bank:
  for name,rid in REPOS.items():
   repo=base/name
   try:
    if not (repo/'.git').exists():raise ValueError('source missing')
    rev=git(repo,'rev-parse','HEAD').decode().strip()
    remote=git(repo,'config','--get','remote.origin.url').decode().strip()
    if remote.rstrip('/').removesuffix('.git').lower() not in ('https://github.com/'+rid.lower(),'git@github.com:'+rid.lower()):raise ValueError('unexpected upstream')
    if bank.db.execute('SELECT 1 FROM sources WHERE repo=? AND revision=? LIMIT 1',(rid,rev)).fetchone():continue
    paths=git(repo,'ls-tree','-r','--name-only','-z',rev).decode().split('\x00')
    licenses=[x for x in paths if '/' not in x and x.lower() in ('license','license.md','license.txt','copying')]
    lic=next((l for x in licenses if (l:=license_id(read_blob(repo,rev,x)))),None)
    if not lic:raise ValueError('license unresolved')
    docs=sorted([x for x in paths if safe_doc(x) and (x.lower().startswith(('docs/','doc/','readme')))],key=lambda x:(not x.lower().startswith('readme'),x))[:12]
    for path in docs:
     try:bank.ingest(rid,rev,path,lic,read_blob(repo,rev,path))
     except (UnicodeError,ValueError):continue
   except Exception as e:rejects.append({'repo':rid,'reason':str(e)[:120]})
  return {'status':'ready',**bank.stats(),'rejected':rejects,'scope':'pinned public repository documentation; source assertions not independently proven','weight_training':False,'production_authority':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--query');a=p.parse_args()
 if a.query is None:print(json.dumps(refresh(a.root)))
 else:
  with Knowledge(a.root/'experience'/'source-knowledge') as bank:print(json.dumps(bank.search(a.query),ensure_ascii=True))
