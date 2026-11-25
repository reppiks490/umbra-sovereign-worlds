"""Read-only, owner-scoped Python symbol index. Never import or execute indexed code."""
import argparse,ast,hashlib,json,re,sqlite3
from pathlib import Path
from source_knowledge import git
from icarus_knowledge import select_local,screen_document
REPOS=('reppiks490/icarus','reppiks490/icarus-engine','reppiks490/icarus-causal-router')
CAP=100000000
def allowed_path(p):
 return bool(isinstance(p,str) and re.fullmatch(r'(?:icarus/features/[A-Za-z0-9_]+|icarus/(?:indicators|risk|signal|backtest)|icarus_engine/backtest|causal_router/(?:engine|learning)|tests/test_(?:indicators|risk|signal|backtest)|tests_engine/test_backtest_(?:validation|window))\.py',p) and not re.search(r'(?i)secret|credential|token|password|private|broker|auth|live|config',p))
def extract_symbols(s):
 if not isinstance(s,str) or len(s.encode('utf8'))>131072 or not screen_document(s):return []
 tree=ast.parse(s);out=[]
 for node in tree.body:
  if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):continue
  code=ast.get_source_segment(s,node)
  if not code or len(code)>12000 or not screen_document(code):continue
  out.append({'symbol':node.name,'kind':type(node).__name__,'start_line':node.lineno,'end_line':node.end_lineno,'text':code,'sha256':hashlib.sha256(code.encode('utf8')).hexdigest()})
 return out
def connect(root):
 p=root/'experience'/'source-knowledge'/'code-symbols.sqlite3';p.parent.mkdir(parents=True,exist_ok=True)
 if p.is_symlink() or p.exists() and p.stat().st_size>CAP:raise ValueError('code database budget')
 db=sqlite3.connect(p,timeout=15)
 db.execute('PRAGMA max_page_count='+str(CAP//db.execute('PRAGMA page_size').fetchone()[0]))
 db.executescript("""CREATE TABLE IF NOT EXISTS symbols(repo TEXT,revision TEXT,path TEXT,blob_sha256 TEXT,symbol TEXT,kind TEXT,start_line INTEGER,end_line INTEGER,sha256 TEXT,text TEXT,UNIQUE(repo,revision,path,symbol,start_line));
 CREATE VIRTUAL TABLE IF NOT EXISTS symbol_search USING fts5(symbol,text,content='symbols',content_rowid='rowid');""")
 return db
def search(root,q,limit=3):
 if not isinstance(q,str) or len(q)>300 or not 1<=limit<=8:raise ValueError('query budget')
 words=list(dict.fromkeys(re.findall('[A-Za-z0-9_]{3,}',q.lower())))[:12]
 if not words:return []
 with connect(root) as db:
  rows=db.execute("""SELECT repo,revision,path,symbols.symbol,start_line,end_line,sha256,blob_sha256,substr(symbols.text,1,1800) FROM symbol_search JOIN symbols ON symbols.rowid=symbol_search.rowid WHERE symbol_search MATCH ? ORDER BY bm25(symbol_search),symbols.rowid LIMIT ?""",(' OR '.join('"'+w+'"' for w in words),limit)).fetchall()
 return [dict(zip(('repo','revision','path','symbol','start_line','end_line','sha256','blob_sha256','text'),r)) for r in rows]
def run(root):
 local=select_local(json.loads((root/'local-source-inventory.json').read_text(encoding='utf8'))['repositories']);errors=[]
 with connect(root) as db:
  for rid in REPOS:
   options=local.get(rid,[])
   if not options:errors.append({'repo':rid,'reason':'checkout unavailable'});continue
   options=sorted(options,key=lambda r:(Path(r['path']).name.lower()!=rid.split('/')[-1],len(r['path']),r['path']))
   try:
    p=Path(options[0]['path']).resolve()
    if not p.is_relative_to(Path.home().resolve()):raise ValueError('owner scope')
    remote=git(p,'config','--get','remote.origin.url').decode().strip().rstrip('/').removesuffix('.git').lower()
    if remote not in ('https://github.com/'+rid,'git@github.com:'+rid):raise ValueError('remote identity')
    rev=git(p,'rev-parse','HEAD').decode().strip()
    if not re.fullmatch('[a-f0-9]{40}',rev):raise ValueError('revision')
    paths=[x for x in git(p,'ls-tree','-r','--name-only','-z',rev).decode().split('\x00') if allowed_path(x)]
    for path in paths[:24]:
     try:
      ref=rev+':'+path
      if git(p,'cat-file','-t',ref).strip()!=b'blob' or not 0<int(git(p,'cat-file','-s',ref))<=131072:continue
      raw=git(p,'cat-file','blob',ref);h=hashlib.sha256(raw).hexdigest()
      for s in extract_symbols(raw.decode('utf8')):
       values=(rid,rev,path,h,s['symbol'],s['kind'],s['start_line'],s['end_line'],s['sha256'],s['text'])
       cur=db.execute('INSERT OR IGNORE INTO symbols VALUES(?,?,?,?,?,?,?,?,?,?)',values)
       if cur.rowcount:db.execute('INSERT INTO symbol_search(rowid,symbol,text) VALUES(?,?,?)',(cur.lastrowid,s['symbol'],s['text']))
      db.commit()
     except (ValueError,SyntaxError,UnicodeError) as e:errors.append({'repo':rid,'path':path,'reason':type(e).__name__})
   except Exception as e:errors.append({'repo':rid,'reason':type(e).__name__})
  result={'status':'indexed','symbols':db.execute('select count(*) from symbols').fetchone()[0],'files':db.execute('select count(*) from (select distinct repo,revision,path from symbols)').fetchone()[0],'repositories':db.execute('select count(distinct repo) from symbols').fetchone()[0],'integrity':db.execute('pragma integrity_check').fetchone()[0],'errors':errors,'scope':'static selected Python symbol text, not execution or proof of strategy correctness','production_authority':False}
 result['retrieval_probe']=[{k:v for k,v in x.items() if k!='text'} for x in search(root,'liquidity orderflow risk',3)]
 p=root/'experience'/'source-knowledge'/'code-coverage.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(result,indent=2),encoding='utf8');tmp.replace(p)
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--query');a=p.parse_args();print(json.dumps(search(a.root,a.query) if a.query else run(a.root)))
