"""Owner-authorized ICARUS local repository retrieval, bounded and read-only."""
import argparse,json,re
from pathlib import Path
from source_knowledge import Knowledge,git,read_blob,safe_doc
NAMES=('Icarus','Icarus-engine','icarus-owner-actions','icarus-csv-evidence-lab','icarus-causal-router','daedalus-research-os','aion-parallax-research','divine-providence','multi-level-csv','csv-data-multi-chart-type','all-of-the-build-as-they-are-as-of-2-13am-9-26-2026','builds','new','ideas-reality','big-contracts-tracker','Reconstructing-MBP-10-data-from-MBO-data','orderbook','torq-cme')
ALLOWED={('reppiks490/'+n).lower() for n in NAMES}
def allowed_document(path):
 return bool(safe_doc(path) and (path.lower().startswith('readme') or (path.lower().startswith(('docs/','doc/')) and re.search(r'(?i)architecture|design|research|method|algorithm|indicator|backtest|overview|model|protocol|specification',path))) and not re.search(r'(?i)credential|secret|token|password|private|deploy|config|account|broker|key|handoff|environment|incident|auth|receipt|log|backup',path))
def screen_document(text):
 return not re.search(r'(?im)-----BEGIN [^-]*PRIVATE KEY-----|(?:api[_ -]?key|access[_ -]?token|client[_ -]?secret|password|authorization)\s*[:=]\s*\S+|(?:sk-[a-zA-Z0-9_-]{12,}|gh[pousr]_[a-zA-Z0-9]{16,}|github_pat_[a-zA-Z0-9_]{16,}|AKIA[A-Z0-9]{16})|https?://[^/\s:@]+:[^/\s@]+@',text)
def select_local(rows):
 out={}
 for r in rows:
  name=str(r.get('repo','')).lower()
  if name not in ALLOWED or r.get('kind')!='git' or not isinstance(r.get('path'),str):continue
  out.setdefault(name,[]).append(r)
 return out
def verified_remote_doc(m):
 import base64,hashlib
 p=m.get('path');n=m.get('size')
 if m.get('type')!='file' or m.get('encoding')!='base64' or not allowed_document(p) or type(n) is not int or not 0<n<=65536:raise ValueError('remote document bounds')
 raw=base64.b64decode(''.join(m['content'].split()),validate=True)
 if len(raw)!=n or hashlib.sha1(b'blob '+str(n).encode()+b'\0'+raw).hexdigest()!=m.get('sha'):raise ValueError('remote blob identity')
 t=raw.decode('utf8')
 if not screen_document(t):raise ValueError('remote document screening')
 return p,t
def github_get(path):
 import urllib.request
 with urllib.request.urlopen(urllib.request.Request('https://api.github.com/'+path,headers={'User-Agent':'UMBRA-source-index','Accept':'application/vnd.github+json'}),timeout=15) as f:
  b=f.read(524289)
  if len(b)>524288:raise ValueError('response bounds')
  return json.loads(b)
def remote_readme(rid):
 import urllib.parse
 if rid.lower() not in ALLOWED:raise ValueError('repository scope')
 m=github_get('repos/'+rid)
 if str(m.get('full_name','')).lower()!=rid.lower() or m.get('private') is not False:raise ValueError('public repository identity')
 branch=m.get('default_branch')
 if not isinstance(branch,str) or not branch:raise ValueError('branch unavailable')
 c=github_get('repos/'+rid+'/commits/'+urllib.parse.quote(branch,safe=''))
 rev=c.get('sha')
 if not isinstance(rev,str) or not re.fullmatch('[a-f0-9]{40}',rev):raise ValueError('commit identity')
 p,t=verified_remote_doc(github_get('repos/'+rid+'/readme?ref='+rev))
 return rev,p,t
def ingest_connector_rows(bank,rows):
 import base64
 accepted=[];rejected=[]
 for r in rows:
  try:
   rid=r['repo'];rev=r['revision']
   if rid.lower() not in ALLOWED or rid.lower()=='reppiks490/builds' or not re.fullmatch('[a-f0-9]{40}',rev):raise ValueError('repository scope')
   raw=base64.b64decode(''.join(r['content'].split()),validate=True)
   p,t=verified_remote_doc({'type':'file','encoding':'base64','path':r['path'],'size':len(raw),'content':r['content'],'sha':r['sha']})
   bank.ingest(rid,rev,p,'OWNER-LOCAL',t)
   accepted.append({'repo':rid,'revision':rev,'documents':1,'origin':'authenticated_connector_pinned_blob'})
  except (ValueError,KeyError,TypeError,UnicodeError) as e:rejected.append({'repo':r.get('repo'),'reason':type(e).__name__})
 return {'accepted':accepted,'rejected':rejected}
def refresh(root,remote_budget=2):
 rows=json.loads((root/'local-source-inventory.json').read_text(encoding='utf8'))['repositories']
 found=select_local(rows);done=[];failed=[]
 import time
 prior_path=root/'experience'/'source-knowledge'/'icarus-remote-attempts.json'
 try:attempts=json.loads(prior_path.read_text(encoding='utf8'))
 except (OSError,ValueError):attempts={}
 now=int(time.time())

 with Knowledge(root/'experience'/'source-knowledge') as bank:
  for name in NAMES:
   rid='reppiks490/'+name;k=rid.lower()
   if k=='reppiks490/builds':failed.append({'repo':rid,'reason':'excluded: no ICARUS documentation identified; unreviewed security-themed projects'});continue
   options=found.get(k,[])
   if not options:
    old=bank.db.execute('SELECT revision,count(*) FROM sources WHERE repo=? AND license=? GROUP BY revision ORDER BY revision LIMIT 1',(rid,'OWNER-LOCAL')).fetchone()
    if old:
     done.append({'repo':rid,'revision':old[0],'documents':old[1],'origin':'pinned_remote_or_previous_local'});continue
    if remote_budget>0 and now-attempts.get(k,0)>=86400:
     remote_budget-=1;attempts[k]=now
     try:
      rev,p,t=remote_readme(rid);bank.ingest(rid,rev,p,'OWNER-LOCAL',t)
      done.append({'repo':rid,'revision':rev,'documents':1,'origin':'pinned_public_github'});continue
     except Exception as e:failed.append({'repo':rid,'reason':'remote '+type(e).__name__});continue
    failed.append({'repo':rid,'reason':'no local Git checkout; remote retry pending'});continue
   # Prefer named root checkout, not backups or historical worktrees.
   options.sort(key=lambda x:(Path(x['path']).name.lower()!=name.lower(),len(x['path']),x['path']))
   indexed=False
   for row in options:
    try:
     repo=Path(row['path']).resolve()
     if not repo.is_relative_to(Path.home().resolve()) or not repo.exists():continue
     remote=git(repo,'config','--get','remote.origin.url').decode().strip().rstrip('/').removesuffix('.git').lower()
     if remote not in ('https://github.com/'+k,'git@github.com:'+k):continue
     rev=git(repo,'rev-parse','HEAD').decode().strip()
     if not re.fullmatch('[a-f0-9]{40}',rev):continue
     paths=git(repo,'ls-tree','-r','--name-only','-z',rev).decode().split('\x00')
     docs=sorted((p for p in paths if allowed_document(p)),key=lambda p:(not p.lower().startswith('readme'),p))[:8]
     count=0
     for p in docs:
      try:
       t=read_blob(repo,rev,p)
       if not screen_document(t):continue
       bank.ingest(rid,rev,p,'OWNER-LOCAL',t);count+=1
      except (UnicodeError,ValueError):continue
     if count:
      done.append({'repo':rid,'revision':rev,'documents':count});indexed=True;break
    except Exception:continue
   if not indexed:failed.append({'repo':rid,'reason':'no admitted documents in verified local checkout'})
  result={'status':'indexed','target_repositories':len(NAMES),'indexed':done,'unavailable':failed,'combined_index':bank.stats(),'scope':'screened local owner-authorized documentation only; no source weight training or code execution'}
 tmp=prior_path.with_suffix('.tmp');tmp.write_text(json.dumps(attempts),encoding='utf8');tmp.replace(prior_path)
 p=root/'experience'/'source-knowledge'/'icarus-coverage.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(result,indent=2),encoding='utf8');tmp.replace(p)
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--remote-budget',type=int,choices=range(9),default=2);a=p.parse_args();print(json.dumps(refresh(a.root,a.remote_budget)))
