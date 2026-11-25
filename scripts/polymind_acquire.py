"""Owner-local, bounded public model acquisition. No remote code or pickle."""
import argparse, hashlib, json, os, re, shutil, sys, time, urllib.request, urllib.parse
from pathlib import Path

GIB=1024**3
RESERVE=3*GIB+256*1024**2
MAX_MODEL=180*1024**2
LICENSES={'apache-2.0','mit','bsd-2-clause','bsd-3-clause','cc-by-4.0','cc0-1.0','isc'}
TASKS={'feature-extraction','sentence-similarity','text-classification','token-classification','text-ranking','question-answering','image-classification','object-detection','image-feature-extraction','audio-classification','zero-shot-classification'}
AUTHORS=('Xenova','onnx-community','onnxmodelzoo','Qdrant','sentence-transformers','Supabase','BAAI','ibm-granite','mixedbread-ai','jinaai','optimum-intel-internal-testing')
# Known compact useful families first; discovery adds popularity-ranked candidates.
PRIORITY=('Xenova/all-MiniLM-L12-v2','Xenova/bge-small-en-v1.5','Xenova/gte-small','Xenova/e5-small-v2','Xenova/paraphrase-MiniLM-L6-v2','Xenova/ms-marco-MiniLM-L-6-v2','Xenova/distilbert-base-uncased-finetuned-sst-2-english','Xenova/bert-base-NER','Xenova/distilbert-base-uncased-distilled-squad','Xenova/mobilenet_v2_1.0_224','Xenova/resnet-18','Xenova/vit-base-patch16-224','Xenova/bert-base-multilingual-cased','Xenova/distilbert-base-uncased-mnli')
HEX=re.compile(r'^[a-f0-9]{64}$')
REPO=re.compile(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$')
def count_unique(xs): return len(set(xs))
def admissible(free,size): return size>0 and free-size>=RESERVE
def select_bundle(meta):
    rid=meta.get('id',''); rev=meta.get('sha',''); task=meta.get('pipeline_tag')
    if not REPO.fullmatch(rid) or rid.split('/')[0] not in AUTHORS or not re.fullmatch('[a-f0-9]{40}',rev): return None
    if meta.get('private') or meta.get('gated') or task not in TASKS: return None
    lic=(meta.get('cardData') or {}).get('license')
    if not lic:
        lic=next((x[8:] for x in meta.get('tags',[]) if isinstance(x,str) and x.startswith('license:')),None)
    if not isinstance(lic,str) or lic not in LICENSES: return None
    rows={f.get('rfilename'):f for f in meta.get('siblings',[]) if isinstance(f,dict)}
    if any(isinstance(n,str) and (n.endswith('.onnx_data') or n.endswith('.onnx.data') or n.endswith('.onnx_data_0')) for n in rows): return None
    weights=[]
    for name,f in rows.items():
        if not isinstance(name,str) or not re.fullmatch(r'(?:onnx/)?[A-Za-z0-9_.-]+\.onnx',name): continue
        size=f.get('size'); digest=(f.get('lfs') or {}).get('sha256','')
        if type(size) is not int or not 0<size<=MAX_MODEL or not HEX.fullmatch(digest): continue
        if any(x in name.lower() for x in ('decoder','encoder_model','merged','with_past','vision_model','text_model','external')): continue
        weights.append((size,name,digest))
    if not weights: return None
    _,weight,digest=min(weights)
    text=task in {'feature-extraction','sentence-similarity','text-classification','token-classification','text-ranking','question-answering','zero-shot-classification'}
    if text and 'tokenizer.json' not in rows: return None
    files=[]
    for name in [weight,'tokenizer.json','config.json','tokenizer_config.json','special_tokens_map.json','preprocessor_config.json','processor_config.json','README.md','LICENSE','LICENSE.txt','LICENSE.md']:
        f=rows.get(name)
        if not f: continue
        size=f.get('size')
        if type(size) is not int or not 0<size<=(MAX_MODEL if name==weight else 8*1024**2): 
            if name in (weight,'tokenizer.json'): return None
            continue
        files.append({'name':name,'size':size,'sha256':(f.get('lfs') or {}).get('sha256'),'blobId':f.get('blobId')})
    return {'repo':rid,'revision':rev,'task':task,'license':lic,'weight':weight,'weight_sha256':digest,'files':files,'total_bytes':sum(f['size'] for f in files)}
def request(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'UMBRA-PolyMind/1.0'}),timeout=30)
def get_json(url):
    with request(url) as r:
        data=r.read(16*1024**2+1)
    if len(data)>16*1024**2: raise ValueError('metadata too large')
    return json.loads(data)
def ollama_count():
    try:
        root=Path(os.environ.get('OLLAMA_MODELS') or Path.home()/'.ollama'/'models')/'manifests'
        digests=set()
        for p in root.rglob('*'):
            if not p.is_file(): continue
            try:
                m=json.loads(p.read_text(encoding='utf8'))
                for l in m['layers']:
                    if l.get('mediaType')=='application/vnd.ollama.image.model': digests.add(l['digest'])
            except (OSError,ValueError,KeyError): pass
        tags=get_json('http://127.0.0.1:11434/api/tags')['models']
        if tags and not digests: raise ValueError('missing local manifest evidence')
        return min(len(tags),len(digests))
    except Exception as e: raise RuntimeError('Cannot verify Ollama count') from e
def catalog(root):
    out=[]
    for p in root.glob('*/receipt.json'):
        try:
            d=json.loads(p.read_text(encoding='utf8'))
            weight=p.parent/d['weight']
            if weight.is_file() and HEX.fullmatch(d['weight_sha256']) and weight.stat().st_size==next(f['size'] for f in d['files'] if f['name']==d['weight']): out.append(d)
        except (OSError,ValueError,KeyError,StopIteration): pass
    return out
def download_file(root,bundle,f):
    rel=f['name']; dest=root/rel; dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():
        if dest.stat().st_size==f['size']:
            h=hashlib.sha256()
            with dest.open('rb') as existing:
                for block in iter(lambda:existing.read(1024**2),b''): h.update(block)
            if f.get('sha256') and h.hexdigest()==f['sha256']: return
        dest.unlink()
    url='https://huggingface.co/'+bundle['repo']+'/resolve/'+bundle['revision']+'/'+urllib.parse.quote(rel,safe='/')
    part=dest.with_suffix(dest.suffix+'.part')
    h=hashlib.sha256(); n=0
    # Git blob verification for small non-LFS metadata.
    git=hashlib.sha1(('blob '+str(f['size'])+'\0').encode())
    try:
        with request(url) as r, part.open('wb') as out:
            while True:
                block=r.read(256*1024)
                if not block: break
                n+=len(block)
                if n>f['size'] or shutil.disk_usage(root).free-len(block)<RESERVE: raise ValueError('download budget')
                h.update(block); git.update(block); out.write(block)
        if n!=f['size'] or (f.get('sha256') and h.hexdigest()!=f['sha256']): raise ValueError('size or LFS digest mismatch')
        if not f.get('sha256') and f.get('blobId') and git.hexdigest()!=f['blobId']: raise ValueError('Git blob mismatch')
        part.replace(dest)
    finally:
        if part.exists(): part.unlink()
def acquire(root,target):
    root.mkdir(parents=True,exist_ok=True)
    receipts=catalog(root); seen={d['weight_sha256'] for d in receipts}; repos={d['repo'] for d in receipts}
    existing=ollama_count()
    print('START',existing,'Ollama distinct weights',len(seen),'external',flush=True)
    if existing+len(seen)>=target: return
    candidates=list(PRIORITY)
    for author in AUTHORS:
        if author=='optimum-intel-internal-testing': continue
        try:
            rows=get_json('https://huggingface.co/api/models?'+urllib.parse.urlencode({'author':author,'sort':'downloads','direction':-1,'limit':100,'filter':'onnx'}))
            candidates.extend(x['id'] for x in rows if x.get('pipeline_tag') in TASKS)
        except Exception as e: print('DISCOVERY_SKIP',author,type(e).__name__,flush=True)
    for rid in dict.fromkeys(candidates):
        if existing+len(seen)>=target or shutil.disk_usage(root).free<=RESERVE: break
        if rid in repos or not REPO.fullmatch(rid) or any(s in rid.lower() for s in ('tiny-random','dummy','test-model','random-','tiny_random')): continue
        try:
            m=get_json('https://huggingface.co/api/models/'+rid+'?blobs=true'); b=select_bundle(m)
            if not b or b['weight_sha256'] in seen: continue
            if not admissible(shutil.disk_usage(root).free,b['total_bytes']): continue
            folder=root/(rid.replace('/','--')+'--'+b['revision'][:12])
            folder.mkdir(exist_ok=True)
            print('PULL',rid,b['total_bytes'],flush=True)
            for f in b['files']: download_file(folder,b,f)
            b.update({'schema':'umbra.polymind.bundle.v1','source':'huggingface','runtime':'onnxruntime','inference_verified':False,'research_qualified':False,'production_authority':False})
            tmp=folder/'receipt.tmp'; tmp.write_text(json.dumps(b,indent=2),encoding='utf8'); tmp.replace(folder/'receipt.json')
            seen.add(b['weight_sha256']); repos.add(rid)
            print('VERIFIED',rid,'TOTAL',existing+len(seen),'FREE',shutil.disk_usage(root).free,flush=True)
        except (OSError,ValueError,KeyError,RuntimeError) as e:
            print('SKIP',rid,type(e).__name__,flush=True)
            if shutil.disk_usage(root).free<=RESERVE: break
    print('FINAL',existing+len(seen),'FREE',shutil.disk_usage(root).free,flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--root',required=True,type=Path);p.add_argument('--target',type=int,default=100); p.add_argument('--inventory',action='store_true');a=p.parse_args()
    if not 1<=a.target<=100: p.error('target must be 1-100')
    if a.inventory: print(json.dumps({'ollama':ollama_count(),'external':catalog(a.root)},indent=2))
    else: acquire(a.root,a.target)
