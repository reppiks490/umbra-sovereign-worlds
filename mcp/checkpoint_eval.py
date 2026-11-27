"""Read-only evaluation of one v51 FP16 checkpoint in an operator-selected bank.
No weight export, training, remote calls, path arguments from MCP, or model promotion.
"""
import argparse,json,math,stat,sys
from pathlib import Path
import myriad_agent_bank_v51 as base

def validate(a):
    if not isinstance(a,dict) or set(a)-{'agent','features'} or type(a.get('agent')) is not int or not 1<=a['agent']<=base.TARGET:
        raise ValueError('invalid agent')
    if 'features' in a:
        x=a['features']
        if not isinstance(x,list) or len(x)!=32 or any(type(v) not in (int,float) or not math.isfinite(v) or abs(v)>4 for v in x):
            raise ValueError('invalid synthetic features')
    return a

def safe(p):
    s=p.lstat()
    if p.is_symlink() or getattr(s,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',1024):
        raise ValueError('linked bank paths prohibited')
    return s

def evaluate(root,request):
    a=validate(request);root=Path(root).absolute()
    for p in (*reversed(root.parents),root):safe(p)
    folder=root/f"{a['agent']:05d}"
    if not stat.S_ISDIR(safe(folder).st_mode):raise ValueError('invalid checkpoint folder')
    for name,bound in [('weights.fp16',base.WIDTH),('receipt.json',16384)]:
        s=safe(folder/name)
        if not stat.S_ISREG(s.st_mode) or not 0<s.st_size<=bound:raise ValueError('invalid checkpoint file')
    r=base.verify(folder,replay=True)
    result={'schema':'myriad.mcp.checkpoint_evaluation.v1','agent':a['agent'],'parameters':base.PARAMETERS,'replayed':True,'before':r['before'],'after':r['after'],'scope':'v51 synthetic regression only','production_authority':False,'semantic_mastery_certified':False}
    if 'features' in a:
        import torch
        torch.set_num_threads(1)
        with (folder/'weights.fp16').open('rb') as f:raw=f.read(base.WIDTH+1)
        if len(raw)!=base.WIDTH or base.sha(raw)!=r['weight_sha256']:raise ValueError('checkpoint changed')
        model=base.restore(torch,base.model(torch,a['agent']),raw);model.eval()
        with torch.inference_mode():pred=model(torch.tensor([a['features']],dtype=torch.float32)).reshape(-1).tolist()
        if len(pred)!=8 or not all(math.isfinite(v) for v in pred):raise ValueError('invalid inference')
        result['prediction']=pred
    return result

def unique(pairs):
    out={}
    for k,v in pairs:
        if k in out:raise ValueError('duplicate JSON key')
        out[k]=v
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--bank-root',required=True);a=p.parse_args()
    try:
        raw=sys.stdin.buffer.read(8193)
        if not 0<len(raw)<=8192:raise ValueError('request size')
        request=json.loads(raw,object_pairs_hook=unique)
        print(json.dumps(evaluate(Path(a.bank_root),request),allow_nan=False))
    except Exception:
        print('Checkpoint evaluation unavailable or invalid',file=sys.stderr);return 1
    return 0
if __name__=='__main__':sys.exit(main())
