"""Native-weight expansion. No model execution, remote code or additional quantization."""
import argparse,json,hashlib,os,shutil,sys,time,urllib.parse
from pathlib import Path
from urllib.request import urlopen
from native_training_bootstrap import download_verified,used as training_used
CAP=42000000000
RESOURCE_CAP=1500000000
LEARNING_CAP=3000000000
BUNDLE_CAP=4000000000
FLOOR=3000000000
TRAINING_CAP=4500000000
ROOT=Path.home()/'projects'/'umbra-agentic-native-20261124'
# Complementary tasks, not claims of measured capability or universal superiority.
CANDIDATES=[
 ('openai/whisper-base','speech',10),('google/siglip2-base-patch16-224','multimodal_retrieval',10),
 ('microsoft/table-transformer-structure-recognition','document_tables',10),
 ('microsoft/table-transformer-detection','document_tables',8),
 ('Qwen/Qwen2.5-Coder-0.5B-Instruct','code_training',9),
 ('microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext','scientific_text',8),
 ('depth-anything/Depth-Anything-V2-Small-hf','spatial_vision',8),
 ('facebook/dinov2-small','visual_features',9),('google/siglip-base-patch16-224','multimodal_retrieval',8),
 ('facebook/bart-large-mnli','contradiction',6),('dslim/bert-base-NER','entity_extraction',9),
 ('google/flan-t5-small','instruction',6),('HuggingFaceTB/SmolLM2-360M-Instruct','instruction',7),
 ('amazon/chronos-bolt-small','forecasting',5),('sentence-transformers/all-MiniLM-L6-v2','retrieval',5),
 ('microsoft/trocr-base-printed','ocr',10),('microsoft/trocr-small-printed','ocr',8),
 ('microsoft/layoutlmv3-base','document_layout',10),('google/deplot','chart_to_table',10),
 ('google/tapas-base-finetuned-wtq','table_question_answering',10),
 ('naver-clova-ix/donut-base-finetuned-docvqa','document_question_answering',9),
 ('allenai/specter2_base','scientific_retrieval',9),('Salesforce/codet5p-220m','code_representation',9),
 ('microsoft/graphcodebert-base','code_representation',8),
 ('Qwen/Qwen2.5-Coder-1.5B-Instruct','code_generation',10),
 ('HuggingFaceTB/SmolVLM-500M-Instruct','visual_question_answering',10),
 ('HuggingFaceTB/SmolVLM-256M-Instruct','visual_question_answering',8),
 ('Salesforce/blip-image-captioning-base','image_captioning',9),
 ('facebook/sam-vit-base','image_segmentation',9),
 ('google/owlvit-base-patch32','open_vocabulary_detection',9),
 ('facebook/detr-resnet-50','object_detection',8),
 ('nvidia/segformer-b0-finetuned-ade-512-512','semantic_segmentation',8),
 ('google/long-t5-local-base','long_context_text',9),
 ('google/flan-t5-large','instruction',8),
 ('BAAI/bge-m3','multilingual_retrieval',9),
 ('facebook/wav2vec2-base-960h','speech',6),
 ('MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli','contradiction',8),
 ('sentence-transformers/LaBSE','multilingual_retrieval',8),
 ('google/vit-base-patch16-224','visual_features',6),
 ('Qwen/Qwen2.5-Math-1.5B-Instruct','mathematical_reasoning',10),
 ('Qwen/Qwen2.5-1.5B-Instruct','instruction',7),
 ('ProsusAI/finbert','financial_sentiment',10),
 ('yiyanghkust/finbert-tone','financial_sentiment',8),
 ('BAAI/bge-base-en-v1.5','retrieval',9),
 ('BAAI/bge-reranker-base','evidence_reranking',10),
 ('intfloat/e5-base-v2','retrieval',8),
 ('intfloat/multilingual-e5-small','multilingual_retrieval',8),
 ('cross-encoder/ms-marco-MiniLM-L12-v2','evidence_reranking',9),
 ('cross-encoder/nli-deberta-v3-base','contradiction',8),
 ('google-bert/bert-base-uncased','text_representation',6),
 ('google-bert/bert-base-multilingual-cased','multilingual_retrieval',7),
 ('openai/whisper-small','speech',9),
 ('openai/whisper-tiny','speech',5),
 ('facebook/wav2vec2-large-960h-lv60-self','speech',7),
 ('facebook/bart-large-cnn','summarization',8),
 ('google/pegasus-xsum','summarization',8),
 ('google/t5-v1_1-large','text_generation',7),
 ('microsoft/resnet-50','visual_features',7),
 ('facebook/convnext-tiny-224','visual_features',7),
 ('microsoft/swin-tiny-patch4-window7-224','visual_features',7),
 ('google/vit-base-patch32-224-in21k','visual_features',6),
 ('microsoft/deberta-v3-base','logical_representation',8),
 ('google/mobilebert-uncased','text_representation',6),
 ('google/electra-base-discriminator','text_representation',7),
 ('microsoft/MiniLM-L12-H384-uncased','text_representation',7),
 ('google/mt5-small','multilingual_generation',8),
 ('HuggingFaceTB/SmolLM2-135M-Instruct','edge_reasoning',6),
 ('ibm-granite/granite-embedding-125m-english','retrieval',8),
 ('ibm-granite/granite-embedding-30m-english','retrieval',7)]
EXTRA_FILES={'tokenizer.model','added_tokens.json','processor_config.json','feature_extractor_config.json','normalizer.json','chat_template.jinja'}
def protected_remaining(training_bytes,resource_bytes):
 return max(0,TRAINING_CAP-training_bytes)+max(0,RESOURCE_CAP-resource_bytes)+LEARNING_CAP
def can_admit(used_bytes,additional,free,remaining_training):
 return 0<additional and used_bytes+additional<=CAP and free-additional>=FLOOR+max(0,remaining_training)
def rank_candidates(rows,seen,domains):
 return sorted([r for r in rows if r['digest'] not in seen],key=lambda r:(r['domain'] in domains,-r['value'],r['total'],r['repo']))
def size(root):
 total=0
 for p in root.rglob('*'):
  try:
   if p.is_file() and not p.is_symlink():total+=p.stat().st_size
  except FileNotFoundError:pass
 return total
def write(p,x):
 tmp=p.with_name(p.name+'.tmp');tmp.write_text(json.dumps(x,indent=2),encoding='utf8');os.replace(tmp,p)
def pending_candidates(candidates,rows,rejected):
 known={r['repo'] for r in rows+rejected}
 return [r for r in candidates if r[0] not in known]
def inspect_candidates(old,candidates=None):
 rows=[];rejected=[]
 for rid,domain,value in (CANDIDATES if candidates is None else candidates):
  try:
   m=old.api('https://huggingface.co/api/models/'+rid+'?blobs=true')
   b=old.pick(m,BUNDLE_CAP)
   if not b or b['repo']!=rid or not any(x['name']=='config.json' for x in b['files']):raise ValueError('metadata, license or native single-file format')
   for f in m.get('siblings',[]):
    name=f['rfilename'];n=f.get('size');h=(f.get('lfs') or {}).get('sha256');blob=f.get('blobId')
    if name in EXTRA_FILES and type(n) is int and 0<n<=16000000 and (h or blob):
     b['files'].append({'name':name,'size':n,'sha':h,'blob':blob});b['total']+=n
   if b['total']>BUNDLE_CAP:raise ValueError('bundle cap')
   rows.append({**b,'domain':domain,'value':value});print('METADATA_ELIGIBLE',rid,b['total'],flush=True)
  except Exception as e:rejected.append({'repo':rid,'reason':type(e).__name__})
 return rows,rejected
def inventory(root):
 seen=set();domains=set();repos=set()
 for f in root.glob('*/*/receipt.json'):
  try:
   r=json.loads(f.read_text(encoding='utf8'))
   if r.get('native_verified') is not True:continue
   seen.add(r['digest']);repos.add(r['repo'])
   domains.update(d for name,d,v in CANDIDATES if name==r['repo'])
  except (ValueError,KeyError,OSError):continue
 return seen,domains,repos
def original_done(root):
 from acquisition_receipt import queue_status
 return queue_status(root)=='ready'
def run(plan_only=False,wait_bootstrap=False,wait_existing=False):
 sys.path.insert(0,str(ROOT.parent/'umbra-polymind-acquisition-pinned'))
 import agentic_acquire_20261124 as old
 ROOT.mkdir(exist_ok=True)
 bucket=ROOT/'neural';bucket.mkdir(exist_ok=True)
 manifest=ROOT/'neural-priority-plan.json';status=ROOT/'neural-priority-status.json'
 seen,domains,repos=inventory(ROOT)
 if manifest.exists():
  m=json.loads(manifest.read_text(encoding='utf8'));rows=m['candidates'];rejected=m['rejected']
  pending=pending_candidates(CANDIDATES,rows,rejected)
  if pending:
   more,failed=inspect_candidates(old,pending);rows+=more;rejected+=failed
  if pending or m.get('cap_bytes')!=CAP:write(manifest,{**m,'cap_bytes':CAP,'candidates':rows,'rejected':rejected})
 else:
  rows,rejected=inspect_candidates(old)
  write(manifest,{'schema':'umbra.neural.priority.v1','cap_bytes':CAP,'learning_workspace_bytes':3000000000,'candidates':rows,'rejected':rejected})
 if plan_only:
  print(json.dumps({'status':'planned','cap_bytes':CAP,'eligible':[(r['repo'],r['domain'],r['total']) for r in rank_candidates(rows,seen,domains) if r['repo'] not in repos],'rejected':rejected}),flush=True);return
 bootstrap=ROOT.parent/'umbra-train-native-20261124'/'bootstrap.lock'
 if wait_bootstrap and bootstrap.exists():
  print('QUEUED_BEHIND_TRAINING_BOOTSTRAP',flush=True)
  deadline=time.monotonic()+21600
  while bootstrap.exists() and time.monotonic()<deadline:time.sleep(20)
 if wait_existing:
  print('QUEUED_BEHIND_ACTIVE_ACQUISITION',flush=True)
  deadline=time.monotonic()+21600
  while ((ROOT/'active.lock').exists() or bootstrap.exists()) and time.monotonic()<deadline:time.sleep(20)
 if not original_done(ROOT) or bootstrap.exists():print('deferred_existing_acquisition',flush=True);return
 lock=ROOT/'active.lock'
 with lock.open('x') as f:f.write(str(os.getpid()))
 results=[]
 try:
  for r in rank_candidates(rows,seen,domains):
   if r['repo'] in repos or r['digest'] in seen:continue
   folder=bucket/(r['repo'].replace('/','--')+'--'+r['revision'][:12])
   # Only resume folders created by this expansion; never overwrite an original queue folder.
   marker=folder/'priority-bundle.json'
   if folder.exists() and not marker.exists():continue
   if marker.exists() and json.loads(marker.read_text(encoding='utf8'))!=r:continue
   existing=size(folder) if folder.exists() else 0
   need=max(1,r['total']-existing)+65536
   remaining_training=protected_remaining(training_used(),size(ROOT/'intelligence-resources'))
   if not can_admit(size(bucket),need,shutil.disk_usage(ROOT).free,remaining_training):
    results.append({'repo':r['repo'],'status':'deferred_storage'});continue
   print('PULL',r['repo'],r['total'],flush=True)
   folder.mkdir(exist_ok=True);write(marker,r)
   def gate(n=0):
    if size(bucket)+n>CAP or shutil.disk_usage(ROOT).free-n<FLOOR+remaining_training:raise ValueError('priority storage gate')
   try:
    for f in r['files']:
     name=f['name'];target=folder/name;target.parent.mkdir(exist_ok=True,parents=True)
     algorithm='sha256' if f['sha'] else 'sha1';expected=f['sha'] or f['blob']
     prefix=b'' if f['sha'] else ('blob '+str(f['size'])+'\0').encode()
     url='https://huggingface.co/'+r['repo']+'/resolve/'+r['revision']+'/'+urllib.parse.quote(name,safe='/')
     download_verified(url,target,f['size'],expected,algorithm,prefix,gate_fn=gate)
    if not old.native(folder/'model.safetensors'):raise ValueError('native tensor validation')
    write(folder/'receipt.json',{**r,'native_verified':True,'inference_verified':False,'training_verified':False})
    seen.add(r['digest']);repos.add(r['repo']);domains.add(r['domain']);results.append({'repo':r['repo'],'status':'verified'});print('VERIFIED',r['repo'],flush=True)
   except Exception as e:results.append({'repo':r['repo'],'status':'retry_needed','reason':type(e).__name__});print('RETRY_NEEDED',r['repo'],type(e).__name__,flush=True);break
  write(status,{'status':'pass_finished','timestamp':int(time.time()),'cap_bytes':CAP,'used_bytes':size(bucket),'results':results})
 finally:lock.unlink(missing_ok=True)
def priority_plan(queue_status,bootstrap_running,priority_running,last,now,status):
 if queue_status!='ready':return 'deferred_original'
 if bootstrap_running:return 'deferred_bootstrap'
 if priority_running:return 'running'
 if type(status.get('cap_bytes')) is int and status['cap_bytes']<CAP and status.get('status')=='pass_finished':return 'eligible'
 if status.get('status')=='pass_finished' and not any(r.get('status') in ('deferred_storage','retry_needed') for r in status.get('results',[])):return 'complete'
 delay=21600 if status.get('status')=='pass_finished' and any(r.get('status')=='deferred_storage' for r in status.get('results',[])) else 1800
 if now-max(last,status.get('timestamp',0))<delay:return 'cooldown'
 return 'eligible'
def resume_priority(root,training,queue_status,queue_behind_bootstrap=False,queue_behind_active=False):
 import subprocess
 from acquisition_recovery import pid_alive
 stamp=root/'neural-priority-attempt.json'
 def read(p):
  try:return json.loads(p.read_text(encoding='utf8'))
  except (OSError,ValueError):return {}
 a=read(stamp);status=read(root/'neural-priority-status.json');now=int(time.time())
 decision=priority_plan('ready' if queue_behind_active and queue_status=='deferred_acquisition' else queue_status,(training/'bootstrap.lock').exists() and not queue_behind_bootstrap,pid_alive(a.get('pid')),a.get('timestamp',0),now,status)
 if decision!='eligible':return {'status':decision}
 if shutil.disk_usage(root).free<=FLOOR+protected_remaining(training_used(),size(root/'intelligence-resources')):return {'status':'deferred_storage'}
 py=Path(sys.base_prefix)/'python.exe'
 if not py.is_file():return {'status':'deferred_runtime'}
 with (root/'neural-priority.log').open('a',encoding='utf8') as out:
  proc=subprocess.Popen([str(py),'-u',str(Path(__file__).resolve())]+(['--wait-bootstrap'] if queue_behind_bootstrap else [])+(['--wait-existing'] if queue_behind_active else []),stdout=out,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 write(stamp,{'pid':proc.pid,'timestamp':now});return {'status':'started','pid':proc.pid,'cap_bytes':CAP}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--plan',action='store_true');p.add_argument('--wait-bootstrap',action='store_true');p.add_argument('--wait-existing',action='store_true');a=p.parse_args();run(a.plan,a.wait_bootstrap,a.wait_existing)
