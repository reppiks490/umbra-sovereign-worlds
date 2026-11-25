"""Local ONNX text evidence adapter; no remote model code or arbitrary prompts."""
import argparse, ctypes, hashlib, json, math, re, sys
from pathlib import Path
from polymind_acquire import catalog

def memory_free():
    if sys.platform=='win32':
        class Status(ctypes.Structure):
            _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(x,ctypes.c_ulonglong) for x in ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]
        s=Status(); s.length=ctypes.sizeof(s)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s)): raise RuntimeError('memory unknown')
        return s.available
    return __import__('os').sysconf('SC_AVPHYS_PAGES')*__import__('os').sysconf('SC_PAGE_SIZE')

def infer(root,rid,world):
    if not isinstance(world,dict) or not 1<=len(world)<=16 or any(not isinstance(k,str) or not re.fullmatch('[a-z_]{1,32}',k) or type(v) not in (int,float) or not math.isfinite(v) for k,v in world.items()): raise ValueError('invalid synthetic numeric evidence')
    matches=[b for b in catalog(root) if b['repo']==rid]
    if len(matches)!=1: raise ValueError('model absent or ambiguous')
    b=matches[0]; folder=root/(rid.replace('/','--')+'--'+b['revision'][:12])
    if b['task'] not in ('feature-extraction','sentence-similarity','text-classification','token-classification','text-ranking','question-answering','zero-shot-classification'): raise ValueError('task not implemented for text')
    if memory_free()<b['total_bytes']*4+1024**3: raise RuntimeError('memory admission denied')
    weight=folder/b['weight']; h=hashlib.sha256()
    with weight.open('rb') as f:
        for chunk in iter(lambda:f.read(1024**2),b''): h.update(chunk)
    if h.hexdigest()!=b['weight_sha256']: raise ValueError('model integrity')
    import numpy as np
    import onnxruntime as ort
    from tokenizers import Tokenizer
    token=Tokenizer.from_file(str(folder/'tokenizer.json'))
    token.enable_truncation(max_length=128)
    enc=token.encode('UMBRA synthetic world evidence only: '+json.dumps(world,sort_keys=True,separators=(',',':')))
    opt=ort.SessionOptions(); opt.intra_op_num_threads=1; opt.inter_op_num_threads=1
    sess=ort.InferenceSession(str(weight),sess_options=opt,providers=['CPUExecutionProvider'])
    arrays={'input_ids':enc.ids,'attention_mask':enc.attention_mask,'token_type_ids':enc.type_ids,'position_ids':list(range(len(enc.ids)))}
    inputs={}
    for item in sess.get_inputs():
        if item.name not in arrays or item.type not in ('tensor(int64)','tensor(int32)') or len(item.shape)!=2: raise ValueError('unsupported model inputs')
        values=arrays[item.name]; width=item.shape[1]
        if isinstance(width,int):
            if not 1<=width<=128: raise ValueError('unsupported static context')
            values=values[:width]+[0]*max(0,width-len(values))
        inputs[item.name]=np.asarray([values],dtype=np.int64 if item.type=='tensor(int64)' else np.int32)
    outputs=sess.run(None,inputs)
    if not outputs or len(outputs)>16: raise ValueError('unsupported outputs')
    result=[]
    for value in outputs:
        if not isinstance(value,np.ndarray) or value.size>2_000_000 or not np.issubdtype(value.dtype,np.number) or not np.isfinite(value).all(): raise ValueError('invalid outputs')
        result.append({'shape':list(value.shape),'dtype':str(value.dtype),'sha256':hashlib.sha256(value.tobytes()).hexdigest()})
    return {'schema':'umbra.polymind.inference.v1','model':rid,'revision':b['revision'],'weight_sha256':b['weight_sha256'],'runtime':'onnxruntime','task':b['task'],'outputs':result,'synthetic':True,'inference_verified':True,'research_qualified':False,'production_authority':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--model',required=True);a=p.parse_args()
    try:
        raw=sys.stdin.buffer.read(8193)
        if len(raw)>8192: raise ValueError('input too large')
        print(json.dumps(infer(a.root,a.model,json.loads(raw))))
    except Exception as e:
        print('POLYMIND_INFERENCE_FAILED '+type(e).__name__,file=sys.stderr);sys.exit(1)
