"""Offline, exact-revision forward-pass qualification. No training or production promotion."""
import argparse,hashlib,json,math,os,re,struct,time
from pathlib import Path
from agentic_native import REPO,HEX,LICENSES,read_receipt,available_ram
from hf_weight_cache import lock
from source_assist import local_api

ENCODERS={'bert','roberta','albert','modernbert','xlm-roberta','deberta-v2'}
CAUSAL={'llama','qwen2','qwen3','granite','gemma','gemma2','gemma3_text'}
VISION={'vit','resnet','swin'}
TASKS={'feature-extraction','sentence-similarity'}
CLASSIFICATION={'text-classification','zero-shot-classification','text-ranking'}
def route(receipt,config):
    if not isinstance(config,dict) or config.get('auto_map'):return None
    kind=config.get('model_type');task=receipt.get('task')
    names={x.get('name') for x in receipt.get('files',[]) if isinstance(x,dict)}
    if not {'model.safetensors','config.json'}<=names:return None
    if kind in VISION and task=='image-classification':return 'vision'
    if kind in VISION|{'dinov2'} and task=='image-feature-extraction':return 'vision_features'
    if task=='automatic-speech-recognition':
        return {'whisper':'whisper','wav2vec2':'ctc'}.get(kind)
    if 'tokenizer.json' not in names and not (kind=='bert' and 'vocab.txt' in names):return None
    if kind in ENCODERS and task=='fill-mask':return 'masked'
    if kind in ENCODERS and task=='token-classification':return 'token_classification'
    if kind in {'t5','longt5','bart'}:
        if task in {'text2text-generation','summarization','translation'}:return 'seq2seq'
        if task is None and set(config.get('architectures') or []) & {'T5ForConditionalGeneration','LongT5ForConditionalGeneration','BartForConditionalGeneration'}:return 'seq2seq'
        if kind=='bart' and task in CLASSIFICATION:return 'classification'
    if kind in ENCODERS and task in TASKS:return 'encoder'
    if kind in ENCODERS and task in CLASSIFICATION:return 'classification'
    if kind in CAUSAL and task=='text-generation':return 'causal'
    return None

def read_json(path,limit=262144):
    if path.is_symlink() or not path.is_file() or path.stat().st_size>limit:raise ValueError('metadata path or size')
    return json.loads(path.read_text(encoding='utf8'))

def catalog(root):
    root=Path(root).resolve();rows=[]
    for bucket in ('neural','tiny'):
        base=root/bucket
        if not base.is_dir() or base.is_symlink() or base.resolve().parent!=root:continue
        for folder in sorted(base.iterdir())[:512]:
            if not folder.is_dir() or folder.is_symlink() or folder.resolve().parent!=base.resolve():continue
            try:
                r=read_json(folder/'receipt.json')
                repo=r['repo'];rev=r['revision'];sha=r['digest'];total=r['total']
                if not REPO.fullmatch(repo) or not re.fullmatch('[a-f0-9]{40}',rev) or not HEX.fullmatch(sha) or type(total) is not int or not 0<total<=5*10**9 or r['native_verified'] is not True:raise ValueError('identity')
                if folder.name!=repo.replace('/','--')+'--'+rev[:12]:raise ValueError('folder identity')
                cfg=read_json(folder/'config.json')
                lane=route(r,cfg)
                rows.append({'repo':repo,'revision':rev,'digest':sha,'total':total,'folder':str(folder.relative_to(root)),'task':r.get('task'),'model_type':cfg.get('model_type'),'route':lane,'status':'candidate' if lane else 'unsupported','inference_verified':False,'weights_verified_this_run':False,'required_ram':max(3000000000,4*total+2000000000)})
            except (OSError,ValueError,TypeError,KeyError,AttributeError):
                rows.append({'folder':str(folder.relative_to(root)),'status':'invalid_metadata','inference_verified':False})
    return rows

def output_evidence(values,shape):
    if not isinstance(shape,list) or not shape or len(shape)>4 or any(type(n) is not int or n<1 for n in shape):raise ValueError('shape')
    if not 2<=len(values)<=262144 or math.prod(shape)!=len(values):raise ValueError('output size')
    if any(type(v) not in (float,int) or not math.isfinite(v) for v in values) or min(values)==max(values):raise ValueError('nonfinite or degenerate output')
    packed=struct.pack('<'+'f'*len(values),*values)
    return {'shape':shape,'elements':len(values),'output_sha256':hashlib.sha256(packed).hexdigest(),'minimum':min(values),'maximum':max(values)}

def forward(folder,receipt,lane):
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
    # Only receipt-listed files may influence model/tokenizer loading.
    allowed={x['name'] for x in receipt['files']}|{'receipt.json'}
    if any(p.is_symlink() or (p.is_file() and p.relative_to(folder).as_posix() not in allowed) for p in folder.rglob('*')):raise ValueError('unverified bundle member')
    cfg=read_json(folder/'config.json')
    if route(receipt,cfg)!=lane:raise ValueError('architecture changed')
    import torch
    import transformers as tf
    torch.set_num_threads(1)
    loaders={'encoder':tf.AutoModel,'classification':tf.AutoModelForSequenceClassification,'causal':tf.AutoModelForCausalLM,'vision':tf.AutoModelForImageClassification,'vision_features':tf.AutoModel,'seq2seq':tf.AutoModelForSeq2SeqLM,'whisper':tf.WhisperForConditionalGeneration,'ctc':tf.AutoModelForCTC,'masked':tf.AutoModelForMaskedLM,'token_classification':tf.AutoModelForTokenClassification}
    model,info=loaders[lane].from_pretrained(str(folder),local_files_only=True,trust_remote_code=False,use_safetensors=True,torch_dtype=torch.float32,output_loading_info=True,low_cpu_mem_usage=True)
    if any(info.get(k) for k in ('missing_keys','unexpected_keys','mismatched_keys','error_msgs')):raise ValueError('inexact model load')
    model.eval()
    if lane in ('vision','vision_features'):
        side=cfg.get('image_size',224);channels=cfg.get('num_channels',3)
        if type(side) is not int or not 32<=side<=512 or channels!=3:raise ValueError('image shape budget')
        args={'pixel_values':torch.linspace(-1,1,3*side*side).reshape(1,3,side,side)}
    elif lane=='whisper':
        bins=cfg.get('num_mel_bins',80);positions=cfg.get('max_source_positions',1500)
        if type(bins) is not int or not 1<=bins<=128 or type(positions) is not int or not 1<=positions<=1500:raise ValueError('mel shape budget')
        args={'input_features':torch.linspace(-1,1,bins*2*positions).reshape(1,bins,2*positions)}
    elif lane=='ctc':
        t=torch.arange(16000,dtype=torch.float32)/16000
        args={'input_values':(0.1*torch.sin(2*math.pi*440*t)).reshape(1,-1)}
    else:
        tok=tf.AutoTokenizer.from_pretrained(str(folder),local_files_only=True,trust_remote_code=False)
        prompt='Chronological validation separates observations from future evidence.'
        if lane=='masked':
            if not tok.mask_token or type(tok.mask_token_id) is not int:raise ValueError('mask token identity')
            prompt='Chronological validation separates '+tok.mask_token+' from future evidence.'
        args=tok(prompt,return_tensors='pt',truncation=True,max_length=32)
        if lane=='masked':
            positions=(args['input_ids'][0]==tok.mask_token_id).nonzero(as_tuple=True)[0]
            if positions.numel()!=1:raise ValueError('expected exactly one mask')
            mask_position=int(positions.item())
        if lane in ('causal','seq2seq') or cfg.get('model_type')=='bart':args.pop('token_type_ids',None)
        if not 1<=args['input_ids'].shape[1]<=32:raise ValueError('token budget')
    if lane in ('seq2seq','whisper'):
        token=model.config.decoder_start_token_id
        if type(token) is not int or not 0<=token<model.config.vocab_size:raise ValueError('decoder start identity')
        args['decoder_input_ids']=torch.tensor([[token]],dtype=torch.long)
    with torch.inference_mode():
        result=model(**args)
        tensor=result.last_hidden_state if lane in ('encoder','vision_features') else result.logits
        if lane=='vision_features':tensor=tensor[:,0,:]
        if lane=='masked':tensor=tensor[:,mask_position,:]
        if lane in ('encoder','causal','seq2seq','whisper','ctc'):tensor=tensor[:,-1,:]
        tensor=tensor.detach().float().cpu().contiguous()
    return output_evidence(tensor.flatten().tolist(),list(tensor.shape))

def execute(root,training,repo,revision):
    root=Path(root).resolve();training=Path(training).resolve()
    base={'schema':'umbra.native.forward.v1','repo':repo,'revision':revision,'inference_verified':False,'research_qualified':False,'weight_training':False,'production_authority':False,'scope':'one bounded offline forward-pass smoke; not accuracy or skill qualification'}
    def result(status,**kw):return {**base,'status':status,**kw}
    busy=(training/'bootstrap.lock',root/'active.lock',root/'experience'/'model-compute.lock',root/'cache-use.lock')
    if any(p.exists() for p in busy):return result('deferred_busy')
    rows=[r for r in catalog(root) if r.get('repo')==repo and r.get('revision')==revision]
    if len(rows)!=1:return result('deferred_identity')
    row=rows[0]
    if row['status']!='candidate':return result('unsupported')
    need=max(3000000000,4*row['total']+2000000000)
    if available_ram()<need:return result('deferred_memory',required_ram=need)
    try:
        if local_api('ps')['models']:return result('deferred_busy')
        with lock(root/'experience'/'model-compute.lock'),lock(root/'cache-use.lock'):
            if (training/'bootstrap.lock').exists() or (root/'active.lock').exists() or local_api('ps')['models']:return result('deferred_busy')
            if available_ram()<need:return result('deferred_memory',required_ram=need)
            folder=root/row['folder']
            r=read_receipt(folder)
            if any(r[k]!=row[k] for k in ('repo','revision','digest','total')):raise ValueError('receipt identity changed')
            start=time.monotonic();evidence=forward(folder,r,row['route'])
            return result('forward_verified',inference_verified=True,weight_sha256=r['digest'],route=row['route'],runtime_seconds=round(time.monotonic()-start,6),output=evidence)
    except FileExistsError:return result('deferred_busy')
    except Exception as e:return result('failed',error_type=type(e).__name__,reason=str(e)[:240])

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--training',type=Path);p.add_argument('--repo');p.add_argument('--revision');p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    if bool(a.repo)!=bool(a.revision):p.error('repo and revision must be supplied together')
    if a.output.exists():p.error('output already exists')
    value=execute(a.root,a.training or a.root.parent/'umbra-train-native-20261124',a.repo,a.revision) if a.repo else {'schema':'umbra.native.forward.catalog.v1','scope':'metadata only','rows':catalog(a.root)}
    with a.output.open('x',encoding='utf8') as f:json.dump(value,f,indent=2,allow_nan=False);f.flush();os.fsync(f.fileno())
    print(json.dumps(value if a.repo else {'count':len(value['rows']),'candidate':sum(r['status']=='candidate' for r in value['rows']),'unsupported':sum(r['status']=='unsupported' for r in value['rows']),'invalid':sum(r['status']=='invalid_metadata' for r in value['rows']),'inference_verified':0},allow_nan=False))
if __name__=='__main__':main()
