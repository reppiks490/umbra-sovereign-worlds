"""Pinned local scientific-skill documents: provenance and lexical retrieval.

The catalog is a data store, not an executable skill runner or proof of mastery.
No Git checkout, remote request, external asset fetching or source execution.
"""
import argparse
from contextlib import closing
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import subprocess
import tempfile

SOURCE = 'K-Dense-AI/scientific-agent-skills'
COMMIT = 'c21d13b3cc2894680229ba9959a53281acb9200e'
LICENSE_BLOB = 'eb246475fd5a66b9bb56176f3a718984632dd98d'
SCHEMA = 'myriad.skill_catalog.v93'
MAX_DOC = 65536
MAX_DOCS = 512
MAX_TOTAL = 16 * 1024**2
PATH = re.compile(r'skills/([A-Za-z0-9][A-Za-z0-9_-]{0,79})/SKILL\.md')
HEX40 = re.compile(r'[a-f0-9]{40}')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def blob_hash(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def safe(p):
    st = p.lstat()
    return not p.is_symlink() and not bool(getattr(st,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',1024))


def require_dir(p):
    p=Path(p)
    if not p.is_dir() or not safe(p):raise ValueError('unsafe directory')
    return p


def validate_entry(e):
    if not isinstance(e,dict) or set(e)!={'path','blob','text'}:raise ValueError('invalid entry')
    path=e['path'];blob=e['blob'];body=e['text']
    if not isinstance(path,str) or not PATH.fullmatch(path) or not isinstance(blob,str) or not HEX40.fullmatch(blob) or not isinstance(body,str) or '\0' in body:raise ValueError('invalid identity')
    raw=body.encode('utf-8')
    if not 1<=len(raw)<=MAX_DOC or blob_hash(raw)!=blob:raise ValueError('blob identity or size')
    return path,blob,sha(raw),PATH.fullmatch(path).group(1),body,len(raw)


def license_digest(text):
    if not isinstance(text,str) or not 1<=len(text.encode())<=MAX_DOC or '\0' in text:raise ValueError('invalid license text')
    return sha(text.strip().encode())


def metadata(source,commit,license_text,count,total):
    if not isinstance(source,str) or not re.fullmatch(r'[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)?',source) or not isinstance(commit,str) or not HEX40.fullmatch(commit):raise ValueError('invalid provenance')
    digest=license_digest(license_text)
    if source==SOURCE and (commit!=COMMIT or blob_hash(license_text.encode())!=LICENSE_BLOB):raise ValueError('pinned source or license mismatch')
    if type(count) is not int or not 1<=count<=MAX_DOCS or type(total) is not int or not count<=total<=MAX_TOTAL:raise ValueError('catalog bounds')
    return {'schema':SCHEMA,'source':source,'commit':commit,'license_sha256':digest,'license_text':license_text,'documents':count,'bytes':total}


def build(root,entries,license_text,*,source=SOURCE,commit=COMMIT):
    root=require_dir(root)
    if not isinstance(entries,list) or not 1<=len(entries)<=MAX_DOCS:raise ValueError('entry count')
    rows=[validate_entry(e) for e in entries]
    if len({r[0] for r in rows})!=len(rows):raise ValueError('duplicate path')
    total=sum(r[5] for r in rows)
    meta=metadata(source,commit,license_text,len(rows),total)
    dest=root/f'skill-catalog-v93-{commit}.sqlite3'
    if dest.exists() or dest.is_symlink():raise FileExistsError('catalog already exists')
    fd,tmp=tempfile.mkstemp(prefix='.catalog-v93-',suffix='.sqlite3',dir=root);os.close(fd);tmp=Path(tmp)
    try:
        with closing(sqlite3.connect(tmp)) as c:
            with c:
                c.execute('CREATE TABLE metadata (value TEXT NOT NULL)')
                c.execute('INSERT INTO metadata VALUES (?)',(json.dumps(meta,sort_keys=True),))
                c.execute("CREATE VIRTUAL TABLE skills USING fts5(path UNINDEXED, blob UNINDEXED, digest UNINDEXED, slug, body, tokenize='unicode61')")
                c.executemany('INSERT INTO skills(path,blob,digest,slug,body) VALUES (?,?,?,?,?)',[r[:5] for r in sorted(rows)])
                c.execute("INSERT INTO skills(skills) VALUES ('integrity-check')")
        audit(tmp)
        # Hard-link installation fails if another writer already created dest.
        os.link(tmp,dest)
    finally:
        tmp.unlink(missing_ok=True)
    return dest


def read_only(p):
    p=Path(p)
    if not p.is_file() or not safe(p) or p.stat().st_size>128*1024**2:raise ValueError('unsafe catalog')
    c=sqlite3.connect(p.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
    try:
        c.execute('PRAGMA query_only=ON');c.execute('PRAGMA trusted_schema=OFF')
    except Exception:
        c.close();raise
    return c


def read_meta(c):
    rows=c.execute('SELECT value FROM metadata LIMIT 2').fetchall()
    if len(rows)!=1:raise ValueError('metadata count')
    m=json.loads(rows[0][0]);expected=metadata(m['source'],m['commit'],m['license_text'],m['documents'],m['bytes'])
    if m!=expected:raise ValueError('metadata replay')
    return m


def audit(p):
    with closing(read_only(p)) as c:
        m=read_meta(c)
        if c.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]:raise ValueError('database integrity')
        count=0;total=0;seen=set()
        for path,blob,digest,slug,body in c.execute('SELECT path,blob,digest,slug,body FROM skills'):
            count+=1
            if count>MAX_DOCS:raise ValueError('document budget')
            row=validate_entry({'path':path,'blob':blob,'text':body})
            if path in seen or row[2]!=digest or row[3]!=slug:raise ValueError('provenance replay')
            seen.add(path);total+=row[5]
            if total>MAX_TOTAL:raise ValueError('byte budget')
        if count!=m['documents'] or total!=m['bytes']:raise ValueError('catalog count mismatch')
    return {k:v for k,v in m.items() if k!='license_text'}|{'production_authority':False,'semantic_mastery_certified':False,'data_only':True}


def search(p,query,limit=5):
    if not isinstance(query,str) or not 1<=len(query)<=160 or any(ord(x)<32 for x in query) or type(limit) is not int or not 1<=limit<=20:raise ValueError('invalid search')
    terms=re.findall('[A-Za-z0-9]{2,40}',query)
    if not 1<=len(terms)<=12:raise ValueError('query token budget')
    q=' AND '.join('"'+x+'"' for x in terms)
    with closing(read_only(p)) as c:
        m=read_meta(c)
        # Source text is never evaluated or passed to an external service.
        rows=c.execute("SELECT path,blob,digest,slug,snippet(skills,4,'[',']',' ... ',24),body FROM skills WHERE skills MATCH ? ORDER BY bm25(skills,0,0,0,8,1),path LIMIT ?",(q,limit)).fetchall()
        result=[]
        for path,blob,digest,slug,snippet,body in rows:
            v=validate_entry({'path':path,'blob':blob,'text':body})
            if digest!=v[2] or slug!=v[3]:raise ValueError('search row provenance')
            result.append({'source':m['source'],'commit':m['commit'],'path':path,'blob':blob,'sha256':digest,'slug':slug,'snippet':snippet[:2000],'data_only':True,'execution_authorized':False})
    return result


def git(repo,*args,input=None):
    env=dict(os.environ,GIT_NO_REPLACE_OBJECTS='1',GIT_TERMINAL_PROMPT='0')
    return subprocess.run(['git','--no-replace-objects','-C',str(repo),*args],input=input,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=60,env=env).stdout


def read_pinned(repo):
    repo=require_dir(repo)
    if git(repo,'rev-parse','HEAD').strip().decode()!=COMMIT:raise ValueError('pinned HEAD mismatch')
    license_text=git(repo,'show',COMMIT+':LICENSE.md').decode('utf-8')
    if blob_hash(license_text.encode())!=LICENSE_BLOB:raise ValueError('pinned license mismatch')
    tree=git(repo,'ls-tree','-r','-l','-z',COMMIT,'--','skills')
    if len(tree)>8*1024**2:raise ValueError('tree size')
    selected=[];total=0
    for entry in tree.split(b'\0'):
        if not entry:continue
        head,path=entry.split(b'\t',1);path=path.decode('utf-8')
        if not path.endswith('/SKILL.md'):continue
        fields=head.decode('ascii').split()
        if len(fields)!=4 or fields[0] not in ('100644','100755') or fields[1]!='blob' or not HEX40.fullmatch(fields[2]) or not PATH.fullmatch(path):raise ValueError('unsupported skill tree entry')
        size=int(fields[3]);total+=size
        if not 1<=size<=MAX_DOC or len(selected)>=MAX_DOCS or total>MAX_TOTAL:raise ValueError('source corpus bounds')
        selected.append((path,fields[2],size))
    if not selected:raise ValueError('no skill documents')
    batch=git(repo,'cat-file','--batch',input=('\n'.join(x[1] for x in selected)+'\n').encode())
    stream=io.BytesIO(batch);rows=[]
    for path,blob,size in selected:
        h=stream.readline(256).decode('ascii').strip().split()
        if h!=[blob,'blob',str(size)]:raise ValueError('batch object identity')
        raw=stream.read(size)
        if len(raw)!=size or stream.read(1)!=b'\n' or blob_hash(raw)!=blob:raise ValueError('batch object integrity')
        rows.append({'path':path,'blob':blob,'text':raw.decode('utf-8')})
    if stream.read(1):raise ValueError('unexpected batch data')
    return rows,license_text


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='mode',required=True)
    b=sub.add_parser('build');b.add_argument('--root',required=True);b.add_argument('--repo',required=True);b.add_argument('--authorize-local-import',action='store_true')
    a=sub.add_parser('audit');a.add_argument('--catalog',required=True)
    s=sub.add_parser('search');s.add_argument('--catalog',required=True);s.add_argument('--query',required=True);s.add_argument('--limit',type=int,default=5)
    x=p.parse_args()
    if x.mode=='build':
        if not x.authorize_local_import:raise PermissionError('local import authorization required')
        rows,license_text=read_pinned(Path(x.repo));result=audit(build(Path(x.root),rows,license_text))
    elif x.mode=='audit':result=audit(Path(x.catalog))
    else:result=search(Path(x.catalog),x.query,x.limit)
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
